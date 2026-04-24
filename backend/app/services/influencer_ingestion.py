from sqlalchemy.orm import Session

from app.influencers.ingestion.adapters import UnsupportedImportFileError
from app.influencers.ingestion.normalization import (
    normalize_email,
    normalize_platform,
    normalize_profile_url,
    normalize_username,
)
from app.influencers.ingestion.registry import (
    ImportAdapterRegistry,
    UnsupportedImportSourceError,
)
from app.influencers.ingestion.schemas import (
    CanonicalInfluencerRow,
    ContactCandidate,
    DedupMatch,
    ImportPreviewInput,
    ImportSessionResponse,
    IngestionConfirmRequest,
    IngestionConfirmResponse,
    IngestionPreviewResponse,
    IngestionPreviewRow,
    IngestionRowResult,
    SocialLinkCandidate,
)
from app.repositories.sqlalchemy import ImportSessionRepository, InfluencerRepository
from app.services.deals import DealService
from app.services.dedup import DedupService
from app.services.errors import ServiceError
from app.services.influencer_bulk_writer import BulkInfluencerWriteCommand
from app.services.influencers import InfluencerService


class InfluencerIngestionServiceError(ServiceError):
    code = "ingestion_error"
    status_code = 422


class UnsupportedImportFile(InfluencerIngestionServiceError):
    code = "unsupported_import_file"


class UnsupportedImportSource(InfluencerIngestionServiceError):
    code = "unsupported_import_source"


class ImportSessionNotFound(InfluencerIngestionServiceError):
    code = "not_found"
    status_code = 404


class InfluencerIngestionService:
    def __init__(
        self,
        db: Session,
        adapter_registry: ImportAdapterRegistry | None = None,
    ) -> None:
        self.db = db
        self.adapter_registry = adapter_registry or ImportAdapterRegistry()
        self.import_sessions = ImportSessionRepository(db)
        self.influencers = InfluencerService(db)
        self.influencer_repo = InfluencerRepository(db)
        self.dedup = DedupService(db)
        self.deals = DealService(db)

    def preview_import(self, input: ImportPreviewInput) -> IngestionPreviewResponse:
        try:
            adapter = self.adapter_registry.get(input.source_type)
            rows = adapter.parse(input)
        except UnsupportedImportSourceError as exc:
            raise UnsupportedImportSource(
                str(exc),
                details={"source_type": input.source_type.value},
            ) from exc
        except UnsupportedImportFileError as exc:
            raise UnsupportedImportFile(
                str(exc),
                details={"source_type": input.source_type.value},
            ) from exc
        if not rows:
            raise UnsupportedImportFile(
                "Import source contains no importable rows.",
                details={"source_type": input.source_type.value},
            )
        preview_rows = [
            self._preview_row(self._canonicalize_row(row)) for row in rows
        ]
        return IngestionPreviewResponse(
            source_type=input.source_type.value,
            row_count=len(preview_rows),
            rows=preview_rows,
        )

    def confirm_import(self, payload: IngestionConfirmRequest) -> IngestionConfirmResponse:
        row_results: list[IngestionRowResult] = []
        processed_influencer_ids: set[str] = set()
        imported_count = 0
        skipped_count = 0
        conflict_count = 0
        created_deals = 0

        for confirm_row in payload.rows:
            row = self._canonicalize_row(confirm_row.row)
            if confirm_row.action == "skip":
                skipped_count += 1
                row_results.append(
                    IngestionRowResult(
                        source_row_number=row.source_row_number,
                        action=confirm_row.action,
                        status="skipped",
                    )
                )
                continue

            match = self.dedup.match(row)
            invalid_result = self._invalid_result(row, confirm_row.action, match)
            if invalid_result:
                skipped_count += 1
                row_results.append(invalid_result)
                continue

            conflict_result = self._conflict_result(
                row,
                confirm_row.action,
                match,
                confirm_row.existing_influencer_id,
                processed_influencer_ids,
            )
            if conflict_result:
                conflict_count += 1
                row_results.append(conflict_result)
                continue

            command_action = confirm_row.action
            command_existing_influencer_id = confirm_row.existing_influencer_id
            if (
                confirm_row.action == "create"
                and match.status == "high_confidence"
                and match.influencer_id in processed_influencer_ids
            ):
                command_action = "merge"
                command_existing_influencer_id = match.influencer_id

            command = BulkInfluencerWriteCommand(
                row=row,
                action=command_action,
                existing_influencer_id=command_existing_influencer_id,
            )
            write_result = self.influencers.bulk_create_or_update([command]).rows[0]
            if write_result.status == "failed":
                skipped_count += 1
                row_results.append(
                    IngestionRowResult(
                        source_row_number=row.source_row_number,
                        action=confirm_row.action,
                        status="failed",
                        errors=write_result.errors,
                        warnings=write_result.warnings,
                    )
                )
                continue

            imported_count += 1
            result_status = "created" if write_result.status == "created" else "merged"
            if write_result.influencer_id:
                processed_influencer_ids.add(write_result.influencer_id)
            warnings = list(write_result.warnings)
            deal_id = None
            if payload.target_campaign_id and write_result.influencer_id:
                deal, created = self.deals.create_if_missing(
                    payload.target_campaign_id,
                    write_result.influencer_id,
                )
                deal_id = deal.id
                if created:
                    created_deals += 1
                else:
                    warnings.append("Campaign deal already exists; skipped deal creation.")
            row_results.append(
                IngestionRowResult(
                    source_row_number=row.source_row_number,
                    action=confirm_row.action,
                    status=result_status,
                    influencer_id=write_result.influencer_id,
                    deal_id=deal_id,
                    warnings=warnings,
                )
            )

        session = self.import_sessions.create(
            source_type=payload.source_type.value,
            file_name=payload.file_name,
            file_hash=payload.file_hash,
            row_count=len(payload.rows),
            imported_count=imported_count,
            skipped_count=skipped_count,
            conflict_count=conflict_count,
            target_campaign_id=payload.target_campaign_id,
        )
        self.db.commit()
        return IngestionConfirmResponse(
            import_session_id=session.id,
            row_count=len(payload.rows),
            imported_count=imported_count,
            skipped_count=skipped_count,
            conflict_count=conflict_count,
            created_deals=created_deals,
            rows=row_results,
        )

    def get_session(self, import_session_id: str) -> ImportSessionResponse:
        session = self.import_sessions.get(import_session_id)
        if not session:
            raise ImportSessionNotFound(
                "Import session not found.",
                details={"import_session_id": import_session_id},
            )
        return ImportSessionResponse(
            id=session.id,
            source_type=session.source_type,
            file_name=session.file_name,
            file_hash=session.file_hash,
            row_count=session.row_count,
            imported_count=session.imported_count,
            skipped_count=session.skipped_count,
            conflict_count=session.conflict_count,
            target_campaign_id=session.target_campaign_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def _preview_row(self, row: CanonicalInfluencerRow) -> IngestionPreviewRow:
        match = self.dedup.match(row)
        if match.status == "invalid":
            status = "invalid"
        elif match.status == "high_confidence":
            status = "matched_existing"
        elif match.status == "possible":
            status = "possible_duplicate"
        else:
            status = "new"
        return IngestionPreviewRow(row=row, status=status, dedup=match)

    def _invalid_result(
        self,
        row: CanonicalInfluencerRow,
        action: str,
        match: DedupMatch,
    ) -> IngestionRowResult | None:
        if match.status != "invalid":
            return None
        return IngestionRowResult(
            source_row_number=row.source_row_number,
            action=action,  # type: ignore[arg-type]
            status="invalid",
            errors=row.parse_errors or ["Row is invalid."],
            warnings=row.warnings,
        )

    def _conflict_result(
        self,
        row: CanonicalInfluencerRow,
        action: str,
        match: DedupMatch,
        existing_influencer_id: str | None,
        processed_influencer_ids: set[str],
    ) -> IngestionRowResult | None:
        if action == "create" and match.status in {"high_confidence", "possible"}:
            if (
                match.status == "high_confidence"
                and match.influencer_id in processed_influencer_ids
            ):
                return None
            return IngestionRowResult(
                source_row_number=row.source_row_number,
                action=action,  # type: ignore[arg-type]
                status="conflict",
                influencer_id=match.influencer_id,
                errors=[f"Create action conflicts with dedup match: {match.reason}."],
                warnings=row.warnings,
            )
        if action == "merge":
            if not existing_influencer_id:
                return IngestionRowResult(
                    source_row_number=row.source_row_number,
                    action=action,  # type: ignore[arg-type]
                    status="failed",
                    errors=["Merge action requires existing_influencer_id."],
                    warnings=row.warnings,
                )
            if not self.influencer_repo.get(existing_influencer_id):
                return IngestionRowResult(
                    source_row_number=row.source_row_number,
                    action=action,  # type: ignore[arg-type]
                    status="failed",
                    errors=["Existing influencer not found."],
                    warnings=row.warnings,
                )
            if match.status == "high_confidence" and match.influencer_id != existing_influencer_id:
                return IngestionRowResult(
                    source_row_number=row.source_row_number,
                    action=action,  # type: ignore[arg-type]
                    status="conflict",
                    influencer_id=match.influencer_id,
                    errors=["Merge target conflicts with high-confidence dedup match."],
                    warnings=row.warnings,
                )
        return None

    def _canonicalize_row(self, row: CanonicalInfluencerRow) -> CanonicalInfluencerRow:
        platform = normalize_platform(row.platform)
        normalized_profile_url = normalize_profile_url(
            row.normalized_profile_url or row.profile_url
        )
        normalized_username = normalize_username(
            platform,
            row.normalized_username or row.username or row.profile_url,
        )
        contacts = [
            ContactCandidate(email=email, source=contact.source)
            for contact in row.contacts
            if (email := normalize_email(contact.email))
        ]
        social_links = []
        for link in row.social_links:
            link_platform = normalize_platform(link.platform)
            normalized_url = normalize_profile_url(link.profile_url)
            if not link_platform or not normalized_url:
                continue
            social_links.append(
                SocialLinkCandidate(
                    platform=link_platform,
                    profile_url=normalized_url,
                    username=normalize_username(link_platform, link.username or normalized_url),
                )
            )
        updates = {
            "platform": platform,
            "normalized_profile_url": normalized_profile_url,
            "normalized_username": normalized_username,
            "contacts": contacts,
            "social_links": social_links,
        }
        parse_errors = list(row.parse_errors)
        if not (row.display_name or row.username):
            parse_errors.append("Missing display name.")
        if not platform:
            parse_errors.append("Missing or invalid platform.")
        if not normalized_profile_url:
            parse_errors.append("Missing or invalid profile URL.")
        updates["parse_errors"] = list(dict.fromkeys(parse_errors))
        return row.model_copy(update=updates)
