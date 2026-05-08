from sqlalchemy.orm import Session

from app.db import models
from app.enums import ContactRole, ImportSourceType
from app.influencers.ingestion.normalization import (
    normalize_email,
    normalize_platform,
    normalize_profile_url,
    normalize_username,
)
from app.repositories.sqlalchemy import (
    DealRepository,
    InfluencerContactRepository,
    InfluencerPlatformRepository,
    InfluencerRepository,
)
from app.schemas.influencer_ingestion import CanonicalInfluencerRow, ContactCandidate
from app.schemas.influencers import (
    InfluencerContactCreateRequest,
    InfluencerContactListResponse,
    InfluencerContactResponse,
    InfluencerContactUpdateRequest,
    InfluencerCreateRequest,
    InfluencerDealListResponse,
    InfluencerDealSummary,
    InfluencerListItem,
    InfluencerListResponse,
    InfluencerPlatformCreateRequest,
    InfluencerPlatformListResponse,
    InfluencerPlatformResponse,
    InfluencerPlatformSummary,
    InfluencerPlatformUpdateRequest,
    InfluencerResponse,
    InfluencerUpdateRequest,
    ManualInfluencerInput,
    ManualInfluencerPlatformInput,
)
from app.services.deals import DealService
from app.services.dedup import DedupService
from app.services.errors import ServiceError
from app.services.influencer_bulk_writer import (
    BulkInfluencerWriteCommand,
    BulkInfluencerWriteResult,
    InfluencerBulkWriter,
)
from app.services.tags import TagValidationError, clean_tag_value, clean_tags


class InfluencerServiceError(ServiceError):
    code = "influencer_error"


class InfluencerNotFound(InfluencerServiceError):
    code = "not_found"
    status_code = 404


class InfluencerPlatformNotFound(InfluencerServiceError):
    code = "not_found"
    status_code = 404


class InfluencerContactNotFound(InfluencerServiceError):
    code = "not_found"
    status_code = 404


class InfluencerValidationError(InfluencerServiceError):
    code = "invalid_influencer"
    status_code = 422


class InfluencerPlatformConflict(InfluencerServiceError):
    code = "platform_conflict"
    status_code = 409


class InfluencerService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.influencers = InfluencerRepository(db)
        self.platforms = InfluencerPlatformRepository(db)
        self.contacts = InfluencerContactRepository(db)
        self.deal_repo = DealRepository(db)
        self.dedup = DedupService(db)
        self.bulk_writer = InfluencerBulkWriter(db)
        self.deals = DealService(db)

    def manual_create(
        self, payload: ManualInfluencerInput, merge_if_matched: bool = False
    ) -> models.Influencer:
        self._validate_manual_platforms(payload.platforms)
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
        influencer_updates: dict[str, object | None] = {}
        if payload.notes is not None:
            influencer_updates["notes"] = payload.notes
        tags = self._clean_tags(payload.tags)
        if tags:
            influencer_updates["tags_json"] = tags
        if influencer_updates:
            self.influencers.update(influencer, **influencer_updates)
        for platform_payload in payload.platforms:
            self._create_or_update_manual_platform(influencer.id, platform_payload)
        if payload.target_campaign_id:
            self.deals.create_if_missing(payload.target_campaign_id, influencer.id)
        self.db.commit()
        self.db.refresh(influencer)
        return influencer

    def create_influencer(self, payload: InfluencerCreateRequest) -> InfluencerResponse:
        influencer = self.influencers.create(
            display_name=payload.display_name,
            full_name=payload.full_name,
            gender=payload.gender,
            country=payload.country,
            city=payload.city,
            bio=payload.bio,
            notes=payload.notes,
            tags_json=self._clean_tags(payload.tags) or None,
        )
        for platform_payload in payload.platforms:
            self._create_platform(influencer.id, platform_payload)
        for contact_payload in payload.contacts:
            self._create_contact(influencer.id, contact_payload)
        self.db.commit()
        return self.get_influencer(influencer.id)

    def list_influencers(
        self,
        *,
        query: str | None = None,
        platform: str | None = None,
        country: str | None = None,
        city: str | None = None,
        tag: str | None = None,
        include_archived: bool = False,
    ) -> InfluencerListResponse:
        normalized_platform = normalize_platform(platform)
        normalized_tag = self._normalize_tag_filter(tag)
        influencers = self.influencers.list(
            query=query,
            platform=normalized_platform,
            country=country,
            city=city,
            include_archived=include_archived,
        )
        if normalized_tag:
            normalized_tag_key = normalized_tag.casefold()
            influencers = [
                influencer
                for influencer in influencers
                if normalized_tag_key in {tag.casefold() for tag in self._tags(influencer)}
            ]
        return InfluencerListResponse(
            influencers=[self._influencer_list_item(influencer) for influencer in influencers]
        )

    def get_influencer(self, influencer_id: str) -> InfluencerResponse:
        influencer = self.influencers.get_profile(influencer_id)
        if not influencer:
            raise InfluencerNotFound(
                "Influencer not found.",
                details={"influencer_id": influencer_id},
            )
        return self._influencer_response(influencer)

    def update_influencer(
        self,
        influencer_id: str,
        payload: InfluencerUpdateRequest,
    ) -> InfluencerResponse:
        influencer = self.influencers.get(influencer_id)
        if not influencer:
            raise InfluencerNotFound(
                "Influencer not found.",
                details={"influencer_id": influencer_id},
            )
        values = payload.model_dump(exclude_unset=True)
        if "tags" in values:
            values["tags_json"] = self._clean_tags(values.pop("tags")) or None
        if values:
            self.influencers.update(influencer, **values)
            self.db.commit()
        return self.get_influencer(influencer.id)

    def archive_influencer(self, influencer_id: str) -> None:
        influencer = self.influencers.get(influencer_id)
        if not influencer:
            raise InfluencerNotFound(
                "Influencer not found.",
                details={"influencer_id": influencer_id},
            )
        self.influencers.archive(influencer)
        self.db.commit()

    def list_platforms(self, influencer_id: str) -> InfluencerPlatformListResponse:
        self._require_influencer(influencer_id)
        return InfluencerPlatformListResponse(
            platforms=[
                self._platform_response(platform)
                for platform in self.platforms.list_for_influencer(influencer_id)
            ]
        )

    def create_platform(
        self,
        influencer_id: str,
        payload: InfluencerPlatformCreateRequest,
    ) -> InfluencerPlatformResponse:
        self._require_influencer(influencer_id)
        platform = self._create_platform(influencer_id, payload)
        self.db.commit()
        return self._platform_response(platform)

    def update_platform(
        self,
        influencer_id: str,
        platform_id: str,
        payload: InfluencerPlatformUpdateRequest,
    ) -> InfluencerPlatformResponse:
        self._require_influencer(influencer_id)
        platform = self.platforms.get_for_influencer(influencer_id, platform_id)
        if not platform:
            raise InfluencerPlatformNotFound(
                "Influencer platform not found.",
                details={"influencer_id": influencer_id, "platform_id": platform_id},
            )
        values = payload.model_dump(exclude_unset=True)
        if values:
            values = self._platform_values(
                platform=values.get("platform", platform.platform),
                username=values.get("username", platform.username),
                profile_url=values.get("profile_url", platform.profile_url),
                values=values,
            )
            self._ensure_platform_available(
                values["platform"],
                values.get("normalized_profile_url"),
                values.get("normalized_username"),
                exclude_platform_id=platform.id,
            )
            platform = self.platforms.update(platform, **values)
            self.db.commit()
        return self._platform_response(platform)

    def delete_platform(self, influencer_id: str, platform_id: str) -> None:
        self._require_influencer(influencer_id)
        platform = self.platforms.get_for_influencer(influencer_id, platform_id)
        if not platform:
            raise InfluencerPlatformNotFound(
                "Influencer platform not found.",
                details={"influencer_id": influencer_id, "platform_id": platform_id},
            )
        self.platforms.delete(platform)
        self.db.commit()

    def list_contacts(self, influencer_id: str) -> InfluencerContactListResponse:
        self._require_influencer(influencer_id)
        return InfluencerContactListResponse(
            contacts=[
                self._contact_response(contact)
                for contact in self.contacts.list_for_influencer(influencer_id)
            ]
        )

    def create_contact(
        self,
        influencer_id: str,
        payload: InfluencerContactCreateRequest,
    ) -> InfluencerContactResponse:
        self._require_influencer(influencer_id)
        contact = self._create_contact(influencer_id, payload)
        self.db.commit()
        return self._contact_response(contact)

    def update_contact(
        self,
        influencer_id: str,
        contact_id: str,
        payload: InfluencerContactUpdateRequest,
    ) -> InfluencerContactResponse:
        self._require_influencer(influencer_id)
        contact = self.contacts.get_for_influencer(influencer_id, contact_id)
        if not contact:
            raise InfluencerContactNotFound(
                "Influencer contact not found.",
                details={"influencer_id": influencer_id, "contact_id": contact_id},
            )
        values = payload.model_dump(exclude_unset=True)
        if "email" in values:
            email = normalize_email(values["email"])
            if not email:
                raise InfluencerValidationError(
                    "Contact email is invalid.",
                    details={"email": values["email"]},
                )
            values["email"] = email
        role = values.get("role")
        if isinstance(role, ContactRole):
            values["role"] = role.value
        if values.get("is_primary") is True:
            self.contacts.clear_primary(influencer_id, exclude_contact_id=contact.id)
        if values:
            contact = self.contacts.update(contact, **values)
            self.db.commit()
        return self._contact_response(contact)

    def delete_contact(self, influencer_id: str, contact_id: str) -> None:
        self._require_influencer(influencer_id)
        contact = self.contacts.get_for_influencer(influencer_id, contact_id)
        if not contact:
            raise InfluencerContactNotFound(
                "Influencer contact not found.",
                details={"influencer_id": influencer_id, "contact_id": contact_id},
            )
        self.contacts.delete(contact)
        self.db.commit()

    def list_deals(self, influencer_id: str) -> InfluencerDealListResponse:
        self._require_influencer(influencer_id)
        return InfluencerDealListResponse(
            deals=[
                self._deal_summary(deal)
                for deal in self.deal_repo.list_for_influencer(influencer_id)
            ]
        )

    def bulk_create_or_update(
        self, commands: list[BulkInfluencerWriteCommand]
    ) -> BulkInfluencerWriteResult:
        return self.bulk_writer.write(commands)

    def _normalize_tag_filter(self, tag: str | None) -> str | None:
        if tag is None:
            return None
        normalized = " ".join(tag.strip().split())
        if not normalized:
            return None
        return self._clean_tag(normalized)

    def _clean_tags(self, tags: list[str] | None) -> list[str]:
        try:
            return clean_tags(tags, entity_name="Influencer")
        except TagValidationError as exc:
            raise InfluencerValidationError(exc.message, details=exc.details) from exc

    def _clean_tag(self, tag: str) -> str:
        try:
            return clean_tag_value(tag, entity_name="Influencer")
        except TagValidationError as exc:
            raise InfluencerValidationError(exc.message, details=exc.details) from exc

    def _tags(self, influencer: models.Influencer) -> list[str]:
        return list(influencer.tags_json or [])

    def _require_influencer(self, influencer_id: str) -> models.Influencer:
        influencer = self.influencers.get(influencer_id)
        if not influencer:
            raise InfluencerNotFound(
                "Influencer not found.",
                details={"influencer_id": influencer_id},
            )
        return influencer

    def _create_platform(
        self,
        influencer_id: str,
        payload: InfluencerPlatformCreateRequest,
    ) -> models.InfluencerPlatform:
        values = self._platform_values(
            platform=payload.platform,
            username=payload.username,
            profile_url=payload.profile_url,
            values=payload.model_dump(exclude={"platform", "username", "profile_url"}),
        )
        self._ensure_platform_available(
            values["platform"],
            values.get("normalized_profile_url"),
            values.get("normalized_username"),
        )
        return self.platforms.create(influencer_id=influencer_id, **values)

    def _platform_values(
        self,
        *,
        platform: str | None,
        username: str | None,
        profile_url: str | None,
        values: dict[str, object],
    ) -> dict[str, object]:
        normalized_platform = normalize_platform(platform)
        normalized_profile_url = normalize_profile_url(profile_url)
        normalized_username = normalize_username(
            normalized_platform,
            username or normalized_profile_url,
        )
        if not normalized_platform:
            raise InfluencerValidationError(
                "Platform is required.",
                details={"platform": platform},
            )
        if not normalized_profile_url and not normalized_username:
            raise InfluencerValidationError(
                "Platform requires a profile URL or username.",
                details={"platform": normalized_platform},
            )
        return {
            **values,
            "platform": normalized_platform,
            "username": username,
            "normalized_username": normalized_username,
            "profile_url": profile_url or normalized_profile_url,
            "normalized_profile_url": normalized_profile_url,
        }

    def _ensure_platform_available(
        self,
        platform: str,
        normalized_profile_url: str | None,
        normalized_username: str | None,
        *,
        exclude_platform_id: str | None = None,
    ) -> None:
        existing_by_url = self.platforms.find_by_normalized_profile_url(normalized_profile_url)
        if existing_by_url and existing_by_url.id != exclude_platform_id:
            raise InfluencerPlatformConflict(
                "Platform profile URL is already linked to an influencer.",
                details={
                    "platform_id": existing_by_url.id,
                    "influencer_id": existing_by_url.influencer_id,
                    "normalized_profile_url": normalized_profile_url,
                },
            )
        existing_by_username = self.platforms.find_by_platform_username(
            platform,
            normalized_username,
        )
        if existing_by_username and existing_by_username.id != exclude_platform_id:
            raise InfluencerPlatformConflict(
                "Platform username is already linked to an influencer.",
                details={
                    "platform_id": existing_by_username.id,
                    "influencer_id": existing_by_username.influencer_id,
                    "platform": platform,
                    "normalized_username": normalized_username,
                },
            )

    def _create_contact(
        self,
        influencer_id: str,
        payload: InfluencerContactCreateRequest,
    ) -> models.InfluencerContact:
        email = normalize_email(payload.email)
        if not email:
            raise InfluencerValidationError(
                "Contact email is invalid.",
                details={"email": payload.email},
            )
        if payload.is_primary:
            self.contacts.clear_primary(influencer_id)
        return self.contacts.create(
            influencer_id=influencer_id,
            name=payload.name,
            email=email,
            role=payload.role.value,
            is_primary=payload.is_primary,
            source=payload.source,
            notes=payload.notes,
        )

    def _manual_payload_to_row(self, payload: ManualInfluencerInput) -> CanonicalInfluencerRow:
        primary_platform = (
            self._manual_platform_values(payload.platforms[0]) if payload.platforms else {}
        )
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
            platform=primary_platform.get("platform"),
            username=primary_platform.get("username"),
            normalized_username=primary_platform.get("normalized_username"),
            profile_url=primary_platform.get("profile_url"),
            normalized_profile_url=primary_platform.get("normalized_profile_url"),
            follower_count=primary_platform.get("follower_count"),
            contacts=[
                ContactCandidate(email=email, source="manual")
                for email in normalized_emails
            ],
        )

    def _manual_platform_values(
        self,
        payload: ManualInfluencerPlatformInput,
    ) -> dict[str, object]:
        platform = normalize_platform(payload.platform)
        username = payload.username.strip()
        normalized_username = normalize_username(platform, username)
        if not platform or not normalized_username:
            raise InfluencerValidationError(
                "Manual platform requires a platform and username.",
                details={"platform": payload.platform, "username": payload.username},
            )
        if any(char.isspace() for char in normalized_username):
            raise InfluencerValidationError(
                "Manual platform username cannot contain whitespace.",
                details={"platform": payload.platform, "username": payload.username},
            )
        profile_url = self._profile_url_for_platform(platform, normalized_username)
        return {
            "platform": platform,
            "username": username.removeprefix("@").strip(),
            "normalized_username": normalized_username,
            "profile_url": profile_url,
            "normalized_profile_url": normalize_profile_url(profile_url),
            "follower_count": payload.follower_count,
        }

    def _validate_manual_platforms(
        self,
        platforms: list[ManualInfluencerPlatformInput],
    ) -> None:
        seen = set()
        for platform_payload in platforms:
            values = self._manual_platform_values(platform_payload)
            key = (values["platform"], values["normalized_username"])
            if key in seen:
                raise InfluencerValidationError(
                    "Duplicate manual platform username.",
                    details={
                        "platform": values["platform"],
                        "username": values["normalized_username"],
                    },
                )
            seen.add(key)

    def _profile_url_for_platform(self, platform: str, normalized_username: str) -> str | None:
        if platform == "instagram":
            return f"https://instagram.com/{normalized_username}"
        if platform == "tiktok":
            return f"https://tiktok.com/@{normalized_username}"
        if platform == "youtube":
            return f"https://youtube.com/@{normalized_username}"
        if platform == "x":
            return f"https://x.com/{normalized_username}"
        if platform == "twitch":
            return f"https://twitch.tv/{normalized_username}"
        return None

    def _create_or_update_manual_platform(
        self,
        influencer_id: str,
        payload: ManualInfluencerPlatformInput,
    ) -> models.InfluencerPlatform:
        values = self._manual_platform_values(payload)
        platform = str(values["platform"])
        normalized_profile_url = values.get("normalized_profile_url")
        normalized_username = values.get("normalized_username")
        existing = self.platforms.find_for_influencer(
            influencer_id,
            platform,
            normalized_profile_url if isinstance(normalized_profile_url, str) else None,
            normalized_username if isinstance(normalized_username, str) else None,
        )
        if existing:
            updates = {
                key: value
                for key, value in values.items()
                if value is not None and getattr(existing, key) != value
            }
            return self.platforms.update(existing, **updates) if updates else existing

        self._ensure_platform_available(
            platform,
            normalized_profile_url if isinstance(normalized_profile_url, str) else None,
            normalized_username if isinstance(normalized_username, str) else None,
        )
        return self.platforms.create(influencer_id=influencer_id, **values)

    def _influencer_response(self, influencer: models.Influencer) -> InfluencerResponse:
        return InfluencerResponse(
            id=influencer.id,
            display_name=influencer.display_name,
            full_name=influencer.full_name,
            gender=influencer.gender,
            country=influencer.country,
            city=influencer.city,
            bio=influencer.bio,
            notes=influencer.notes,
            tags=self._tags(influencer),
            archived_at=influencer.archived_at,
            created_at=influencer.created_at,
            updated_at=influencer.updated_at,
            platforms=[
                self._platform_response(platform)
                for platform in sorted(influencer.platforms, key=lambda item: item.created_at)
            ],
            contacts=[
                self._contact_response(contact)
                for contact in sorted(
                    influencer.contacts,
                    key=lambda item: (not item.is_primary, item.created_at),
                )
            ],
            deals=[
                self._deal_summary(deal)
                for deal in sorted(influencer.deals, key=lambda item: item.updated_at, reverse=True)
            ],
        )

    def _influencer_list_item(self, influencer: models.Influencer) -> InfluencerListItem:
        primary_platform = self._primary_platform(influencer.platforms)
        primary_contact = self._primary_contact(influencer.contacts)
        sorted_platforms = self._sorted_platforms(influencer.platforms)
        return InfluencerListItem(
            id=influencer.id,
            display_name=influencer.display_name,
            full_name=influencer.full_name,
            country=influencer.country,
            city=influencer.city,
            primary_platform=(
                self._platform_response(primary_platform) if primary_platform else None
            ),
            platforms=[
                self._platform_summary(platform, is_primary=platform.id == primary_platform.id)
                for platform in sorted_platforms
            ]
            if primary_platform
            else [],
            follower_count=primary_platform.follower_count if primary_platform else None,
            primary_contact=self._contact_response(primary_contact) if primary_contact else None,
            recent_deal_count=len([deal for deal in influencer.deals if not deal.archived_at]),
            tags=self._tags(influencer),
            archived_at=influencer.archived_at,
            created_at=influencer.created_at,
            updated_at=influencer.updated_at,
        )

    def _primary_platform(
        self,
        platforms: list[models.InfluencerPlatform],
    ) -> models.InfluencerPlatform | None:
        if not platforms:
            return None
        return self._sorted_platforms(platforms)[0]

    def _sorted_platforms(
        self,
        platforms: list[models.InfluencerPlatform],
    ) -> list[models.InfluencerPlatform]:
        return sorted(
            platforms,
            key=lambda item: (item.follower_count or 0, item.created_at),
            reverse=True,
        )

    def _primary_contact(
        self,
        contacts: list[models.InfluencerContact],
    ) -> models.InfluencerContact | None:
        if not contacts:
            return None
        return sorted(contacts, key=lambda item: (not item.is_primary, item.created_at))[0]

    def _platform_response(
        self,
        platform: models.InfluencerPlatform,
    ) -> InfluencerPlatformResponse:
        return InfluencerPlatformResponse(
            id=platform.id,
            influencer_id=platform.influencer_id,
            platform=platform.platform,
            username=platform.username,
            normalized_username=platform.normalized_username,
            profile_url=platform.profile_url,
            normalized_profile_url=platform.normalized_profile_url,
            follower_count=platform.follower_count,
            engagement_rate=platform.engagement_rate,
            follower_credibility=platform.follower_credibility,
            notable_follower_rate=platform.notable_follower_rate,
            avg_likes=platform.avg_likes,
            avg_views=platform.avg_views,
            avg_comments=platform.avg_comments,
            avg_reels_plays=platform.avg_reels_plays,
            total_likes=platform.total_likes,
            total_posts_or_videos=platform.total_posts_or_videos,
            total_views=platform.total_views,
            bio=platform.bio,
            created_at=platform.created_at,
            updated_at=platform.updated_at,
        )

    def _platform_summary(
        self,
        platform: models.InfluencerPlatform,
        *,
        is_primary: bool,
    ) -> InfluencerPlatformSummary:
        return InfluencerPlatformSummary(
            id=platform.id,
            platform=platform.platform,
            username=platform.username,
            profile_url=platform.profile_url,
            follower_count=platform.follower_count,
            engagement_rate=platform.engagement_rate,
            is_primary=is_primary,
        )

    def _contact_response(self, contact: models.InfluencerContact) -> InfluencerContactResponse:
        conflict_influencer_ids = sorted(
            {
                match.influencer_id
                for match in self.contacts.find_by_email(contact.email)
                if match.influencer_id != contact.influencer_id
            }
        )
        return InfluencerContactResponse(
            id=contact.id,
            influencer_id=contact.influencer_id,
            name=contact.name,
            email=contact.email,
            role=ContactRole(contact.role),
            is_primary=contact.is_primary,
            source=contact.source,
            notes=contact.notes,
            conflict_influencer_ids=conflict_influencer_ids,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
        )

    def _deal_summary(self, deal: models.Deal) -> InfluencerDealSummary:
        return InfluencerDealSummary(
            id=deal.id,
            campaign_id=deal.campaign_id,
            campaign_name=deal.campaign.name if deal.campaign else None,
            status=deal.status,
            created_at=deal.created_at,
            updated_at=deal.updated_at,
            archived_at=deal.archived_at,
        )
