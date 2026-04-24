from sqlalchemy.orm import Session

from app.db import models
from app.domain.enums import ImportSourceType
from app.influencers.ingestion.normalization import (
    normalize_email,
    normalize_platform,
    normalize_profile_url,
    normalize_username,
)
from app.influencers.ingestion.schemas import CanonicalInfluencerRow, ContactCandidate
from app.influencers.schemas import ManualInfluencerInput
from app.repositories.sqlalchemy import InfluencerRepository
from app.services.deals import DealService
from app.services.dedup import DedupService
from app.services.influencer_bulk_writer import (
    BulkInfluencerWriteCommand,
    BulkInfluencerWriteResult,
    InfluencerBulkWriter,
)


class InfluencerService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.influencers = InfluencerRepository(db)
        self.dedup = DedupService(db)
        self.bulk_writer = InfluencerBulkWriter(db)
        self.deals = DealService(db)

    def manual_create(
        self, payload: ManualInfluencerInput, merge_if_matched: bool = False
    ) -> models.Influencer:
        row = self._manual_payload_to_row(payload)
        match = self.dedup.match(row)
        action = "merge" if merge_if_matched and match.influencer_id else "create"
        existing_influencer_id = match.influencer_id if action == "merge" else None
        result = self.bulk_create_or_update(
            [
                BulkInfluencerWriteCommand(
                    row=row,
                    action=action,
                    existing_influencer_id=existing_influencer_id,
                )
            ]
        )
        write_result = result.rows[0]
        if not write_result.influencer_id:
            raise ValueError("; ".join(write_result.errors) or "Failed to create influencer.")
        influencer = self.influencers.get(write_result.influencer_id)
        if influencer is None:
            raise ValueError("Created influencer not found.")
        if payload.target_campaign_id:
            self.deals.create_if_missing(payload.target_campaign_id, influencer.id)
        self.db.commit()
        self.db.refresh(influencer)
        return influencer

    def bulk_create_or_update(
        self, commands: list[BulkInfluencerWriteCommand]
    ) -> BulkInfluencerWriteResult:
        return self.bulk_writer.write(commands)

    def _manual_payload_to_row(self, payload: ManualInfluencerInput) -> CanonicalInfluencerRow:
        platform = normalize_platform(payload.platform)
        normalized_profile_url = normalize_profile_url(payload.profile_url)
        normalized_username = normalize_username(platform, payload.username or payload.profile_url)
        normalized_emails = [
            normalized for email in payload.emails if (normalized := normalize_email(email))
        ]
        return CanonicalInfluencerRow(
            source_type=ImportSourceType.MANUAL.value,
            source_row_number=1,
            raw_row_json=payload.model_dump(),
            display_name=payload.display_name,
            full_name=payload.full_name,
            country=payload.country,
            city=payload.city,
            bio=payload.bio,
            platform=platform,
            username=payload.username,
            normalized_username=normalized_username,
            profile_url=payload.profile_url,
            normalized_profile_url=normalized_profile_url,
            follower_count=payload.follower_count,
            contacts=[
                ContactCandidate(email=email, source="manual")
                for email in normalized_emails
            ],
        )
