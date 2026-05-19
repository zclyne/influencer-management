from __future__ import annotations

from datetime import UTC
from typing import Generic, TypeVar

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db import models
from app.db.models import utc_now

ModelT = TypeVar("ModelT", bound=models.Base)


class SqlAlchemyRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **values: object) -> ModelT:
        entity = self.model(**values)
        self.db.add(entity)
        self.db.flush()
        return entity

    def get(self, entity_id: str) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def update(self, entity: ModelT, **values: object) -> ModelT:
        for key, value in values.items():
            setattr(entity, key, value)
        self.db.flush()
        return entity

    def archive(self, entity: ModelT) -> ModelT:
        if hasattr(entity, "archived_at"):
            entity.archived_at = utc_now().astimezone(UTC)
        self.db.flush()
        return entity


class BrandRepository(SqlAlchemyRepository[models.Brand]):
    model = models.Brand

    def list(
        self,
        *,
        query: str | None = None,
        include_archived: bool = False,
    ) -> list[models.Brand]:
        stmt = select(models.Brand)
        if query:
            stmt = stmt.where(models.Brand.name.ilike(f"%{query.strip()}%"))
        if not include_archived:
            stmt = stmt.where(models.Brand.archived_at.is_(None))
        stmt = stmt.order_by(models.Brand.name.asc())
        return list(self.db.scalars(stmt))

    def get_active(self, brand_id: str) -> models.Brand | None:
        return self.db.scalar(
            select(models.Brand).where(
                models.Brand.id == brand_id,
                models.Brand.archived_at.is_(None),
            )
        )

    def find_by_name(self, name: str) -> models.Brand | None:
        return self.db.scalar(
            select(models.Brand).where(func.lower(models.Brand.name) == name.strip().lower())
        )

    def campaign_count(self, brand_id: str) -> int:
        return self.db.scalar(
            select(func.count())
            .select_from(models.CampaignBrand)
            .where(models.CampaignBrand.brand_id == brand_id)
        ) or 0

    def campaign_counts(self) -> dict[str, int]:
        rows = self.db.execute(
            select(models.CampaignBrand.brand_id, func.count(models.CampaignBrand.id)).group_by(
                models.CampaignBrand.brand_id
            )
        )
        return {brand_id: count for brand_id, count in rows}


class CampaignRepository(SqlAlchemyRepository[models.Campaign]):
    model = models.Campaign

    def list(
        self,
        *,
        status: str | None = None,
        include_archived: bool = False,
    ) -> list[models.Campaign]:
        stmt = select(models.Campaign)
        if status:
            stmt = stmt.where(models.Campaign.status == status)
        if not include_archived:
            stmt = stmt.where(models.Campaign.archived_at.is_(None))
        stmt = stmt.order_by(models.Campaign.updated_at.desc())
        return list(self.db.scalars(stmt))

    def get_with_brands(self, campaign_id: str) -> models.Campaign | None:
        return self.db.scalar(
            select(models.Campaign)
            .options(
                selectinload(models.Campaign.brand_links).selectinload(
                    models.CampaignBrand.brand
                )
            )
            .where(models.Campaign.id == campaign_id)
        )

    def find_by_name(self, name: str) -> models.Campaign | None:
        return self.db.scalar(
            select(models.Campaign).where(func.lower(models.Campaign.name) == name.strip().lower())
        )


class CampaignBrandRepository(SqlAlchemyRepository[models.CampaignBrand]):
    model = models.CampaignBrand

    def get_by_campaign_brand(self, campaign_id: str, brand_id: str) -> models.CampaignBrand | None:
        return self.db.scalar(
            select(models.CampaignBrand).where(
                models.CampaignBrand.campaign_id == campaign_id,
                models.CampaignBrand.brand_id == brand_id,
            )
        )

    def delete(self, campaign_brand: models.CampaignBrand) -> None:
        self.db.delete(campaign_brand)
        self.db.flush()


class InfluencerRepository(SqlAlchemyRepository[models.Influencer]):
    model = models.Influencer

    def list(
        self,
        *,
        query: str | None = None,
        platform: str | None = None,
        country: str | None = None,
        city: str | None = None,
        include_archived: bool = False,
    ) -> list[models.Influencer]:
        stmt = select(models.Influencer).options(
            selectinload(models.Influencer.platforms),
            selectinload(models.Influencer.contacts),
            selectinload(models.Influencer.deals),
        )
        if query:
            like_query = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    models.Influencer.display_name.ilike(like_query),
                    models.Influencer.full_name.ilike(like_query),
                )
            )
        if platform:
            stmt = stmt.join(models.InfluencerPlatform).where(
                models.InfluencerPlatform.platform == platform
            )
        if country:
            stmt = stmt.where(models.Influencer.country.ilike(country.strip()))
        if city:
            stmt = stmt.where(models.Influencer.city.ilike(city.strip()))
        if not include_archived:
            stmt = stmt.where(models.Influencer.archived_at.is_(None))
        stmt = stmt.order_by(models.Influencer.updated_at.desc()).distinct()
        return list(self.db.scalars(stmt))

    def get_profile(self, influencer_id: str) -> models.Influencer | None:
        return self.db.scalar(
            select(models.Influencer)
            .options(
                selectinload(models.Influencer.platforms),
                selectinload(models.Influencer.contacts),
                selectinload(models.Influencer.deals).selectinload(models.Deal.campaign),
            )
            .where(models.Influencer.id == influencer_id)
        )

    def get_active(self, influencer_id: str) -> models.Influencer | None:
        return self.db.scalar(
            select(models.Influencer).where(
                models.Influencer.id == influencer_id,
                models.Influencer.archived_at.is_(None),
            )
        )

    def find_by_display_name(self, display_name: str, limit: int = 5) -> list[models.Influencer]:
        stmt: Select[tuple[models.Influencer]] = (
            select(models.Influencer)
            .where(func.lower(models.Influencer.display_name) == display_name.lower())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))


class InfluencerPlatformRepository(SqlAlchemyRepository[models.InfluencerPlatform]):
    model = models.InfluencerPlatform

    def list_for_influencer(self, influencer_id: str) -> list[models.InfluencerPlatform]:
        return list(
            self.db.scalars(
                select(models.InfluencerPlatform)
                .where(models.InfluencerPlatform.influencer_id == influencer_id)
                .order_by(models.InfluencerPlatform.created_at.asc())
            )
        )

    def get_for_influencer(
        self, influencer_id: str, platform_id: str
    ) -> models.InfluencerPlatform | None:
        return self.db.scalar(
            select(models.InfluencerPlatform).where(
                models.InfluencerPlatform.id == platform_id,
                models.InfluencerPlatform.influencer_id == influencer_id,
            )
        )

    def find_by_normalized_profile_url(
        self, normalized_profile_url: str | None
    ) -> models.InfluencerPlatform | None:
        if not normalized_profile_url:
            return None
        return self.db.scalar(
            select(models.InfluencerPlatform).where(
                models.InfluencerPlatform.normalized_profile_url == normalized_profile_url
            )
        )

    def find_by_platform_username(
        self, platform: str | None, normalized_username: str | None
    ) -> models.InfluencerPlatform | None:
        if not platform or not normalized_username:
            return None
        return self.db.scalar(
            select(models.InfluencerPlatform).where(
                models.InfluencerPlatform.platform == platform,
                models.InfluencerPlatform.normalized_username == normalized_username,
            )
        )

    def find_for_influencer(
        self,
        influencer_id: str,
        platform: str,
        normalized_profile_url: str | None,
        normalized_username: str | None,
    ) -> models.InfluencerPlatform | None:
        identity_clauses = []
        if normalized_profile_url:
            identity_clauses.append(
                models.InfluencerPlatform.normalized_profile_url == normalized_profile_url
            )
        if normalized_username:
            identity_clauses.append(
                models.InfluencerPlatform.normalized_username == normalized_username
            )
        if not identity_clauses:
            return None

        clauses = [
            models.InfluencerPlatform.influencer_id == influencer_id,
            models.InfluencerPlatform.platform == platform,
            or_(*identity_clauses),
        ]
        return self.db.scalar(select(models.InfluencerPlatform).where(*clauses))

    def delete(self, platform: models.InfluencerPlatform) -> None:
        self.db.delete(platform)
        self.db.flush()


class InfluencerAudienceSnapshotRepository(
    SqlAlchemyRepository[models.InfluencerAudienceSnapshot]
):
    model = models.InfluencerAudienceSnapshot


class InfluencerContactRepository(SqlAlchemyRepository[models.InfluencerContact]):
    model = models.InfluencerContact

    def list_for_influencer(self, influencer_id: str) -> list[models.InfluencerContact]:
        return list(
            self.db.scalars(
                select(models.InfluencerContact)
                .where(models.InfluencerContact.influencer_id == influencer_id)
                .order_by(
                    models.InfluencerContact.is_primary.desc(),
                    models.InfluencerContact.created_at.asc(),
                )
            )
        )

    def get_for_influencer(
        self, influencer_id: str, contact_id: str
    ) -> models.InfluencerContact | None:
        return self.db.scalar(
            select(models.InfluencerContact).where(
                models.InfluencerContact.id == contact_id,
                models.InfluencerContact.influencer_id == influencer_id,
            )
        )

    def find_by_email(self, email: str) -> list[models.InfluencerContact]:
        return list(
            self.db.scalars(
                select(models.InfluencerContact).where(
                    func.lower(models.InfluencerContact.email) == email.lower()
                )
            )
        )

    def find_for_influencer(
        self, influencer_id: str, email: str
    ) -> models.InfluencerContact | None:
        return self.db.scalar(
            select(models.InfluencerContact).where(
                models.InfluencerContact.influencer_id == influencer_id,
                models.InfluencerContact.email == email,
            )
        )

    def clear_primary(self, influencer_id: str, exclude_contact_id: str | None = None) -> None:
        contacts = self.list_for_influencer(influencer_id)
        for contact in contacts:
            if contact.id != exclude_contact_id:
                contact.is_primary = False
        self.db.flush()

    def delete(self, contact: models.InfluencerContact) -> None:
        self.db.delete(contact)
        self.db.flush()


class DealRepository(SqlAlchemyRepository[models.Deal]):
    model = models.Deal

    def get_by_campaign_influencer(
        self, campaign_id: str, influencer_id: str
    ) -> models.Deal | None:
        return self.db.scalar(
            select(models.Deal).where(
                models.Deal.campaign_id == campaign_id,
                models.Deal.influencer_id == influencer_id,
            )
        )

    def list_for_influencer(self, influencer_id: str) -> list[models.Deal]:
        return list(
            self.db.scalars(
                select(models.Deal)
                .options(selectinload(models.Deal.campaign))
                .where(models.Deal.influencer_id == influencer_id)
                .order_by(models.Deal.updated_at.desc())
            )
        )

    def list_for_campaign(
        self,
        campaign_id: str,
        *,
        status: str | None = None,
        platform: str | None = None,
        lost_reason: str | None = None,
        include_archived: bool = False,
    ) -> list[models.Deal]:
        stmt = (
            select(models.Deal)
            .options(
                selectinload(models.Deal.influencer).selectinload(
                    models.Influencer.platforms
                ),
                selectinload(models.Deal.influencer).selectinload(models.Influencer.contacts),
                selectinload(models.Deal.deliverables),
                selectinload(models.Deal.compensation_items),
            )
            .where(models.Deal.campaign_id == campaign_id)
        )
        if status:
            stmt = stmt.where(models.Deal.status == status)
        if platform:
            stmt = stmt.where(
                models.Deal.influencer.has(
                    models.Influencer.platforms.any(
                        models.InfluencerPlatform.platform == platform
                    )
                )
            )
        if lost_reason:
            stmt = stmt.where(models.Deal.lost_reason == lost_reason)
        if not include_archived:
            stmt = stmt.where(models.Deal.archived_at.is_(None))
        stmt = stmt.order_by(models.Deal.updated_at.desc())
        return list(self.db.scalars(stmt))

    def list_for_campaign_with_graph(
        self,
        campaign_id: str,
        *,
        status: str | None = None,
        platform: str | None = None,
        lost_reason: str | None = None,
        include_archived: bool = False,
        deal_ids: list[str] | None = None,
    ) -> list[models.Deal]:
        stmt = (
            select(models.Deal)
            .options(
                selectinload(models.Deal.campaign)
                .selectinload(models.Campaign.brand_links)
                .selectinload(models.CampaignBrand.brand),
                selectinload(models.Deal.influencer).selectinload(
                    models.Influencer.platforms
                ),
                selectinload(models.Deal.influencer).selectinload(models.Influencer.contacts),
                selectinload(models.Deal.deliverables),
                selectinload(models.Deal.compensation_items),
            )
            .where(models.Deal.campaign_id == campaign_id)
        )
        if status:
            stmt = stmt.where(models.Deal.status == status)
        if platform:
            stmt = stmt.where(
                models.Deal.influencer.has(
                    models.Influencer.platforms.any(
                        models.InfluencerPlatform.platform == platform
                    )
                )
            )
        if lost_reason:
            stmt = stmt.where(models.Deal.lost_reason == lost_reason)
        if not include_archived:
            stmt = stmt.where(models.Deal.archived_at.is_(None))
        if deal_ids:
            stmt = stmt.where(models.Deal.id.in_(deal_ids))
        stmt = stmt.order_by(models.Deal.updated_at.desc())
        return list(self.db.scalars(stmt))

    def get_detail(self, deal_id: str) -> models.Deal | None:
        return self.db.scalar(
            select(models.Deal)
            .options(
                selectinload(models.Deal.campaign)
                .selectinload(models.Campaign.brand_links)
                .selectinload(models.CampaignBrand.brand),
                selectinload(models.Deal.influencer).selectinload(
                    models.Influencer.platforms
                ),
                selectinload(models.Deal.influencer).selectinload(models.Influencer.contacts),
                selectinload(models.Deal.deliverables),
                selectinload(models.Deal.compensation_items),
            )
            .where(models.Deal.id == deal_id)
        )

    def list_by_ids(self, ids: list[str]) -> list[models.Deal]:
        if not ids:
            return []
        return list(
            self.db.scalars(
                select(models.Deal)
                .options(
                    selectinload(models.Deal.influencer).selectinload(
                        models.Influencer.platforms
                    ),
                    selectinload(models.Deal.influencer).selectinload(
                        models.Influencer.contacts
                    ),
                    selectinload(models.Deal.deliverables),
                    selectinload(models.Deal.compensation_items),
                )
                .where(models.Deal.id.in_(ids))
            )
        )


class DeliverableRepository(SqlAlchemyRepository[models.Deliverable]):
    model = models.Deliverable

    def list_for_deal(self, deal_id: str) -> list[models.Deliverable]:
        return list(
            self.db.scalars(
                select(models.Deliverable)
                .where(models.Deliverable.deal_id == deal_id)
                .order_by(models.Deliverable.due_date.asc(), models.Deliverable.created_at.asc())
            )
        )

    def get_for_deal(self, deal_id: str, deliverable_id: str) -> models.Deliverable | None:
        return self.db.scalar(
            select(models.Deliverable).where(
                models.Deliverable.id == deliverable_id,
                models.Deliverable.deal_id == deal_id,
            )
        )

    def delete(self, deliverable: models.Deliverable) -> None:
        self.db.delete(deliverable)
        self.db.flush()


class CompensationItemRepository(SqlAlchemyRepository[models.CompensationItem]):
    model = models.CompensationItem

    def list_for_deal(self, deal_id: str) -> list[models.CompensationItem]:
        return list(
            self.db.scalars(
                select(models.CompensationItem)
                .where(models.CompensationItem.deal_id == deal_id)
                .order_by(
                    models.CompensationItem.due_date.asc(),
                    models.CompensationItem.created_at.asc(),
                )
            )
        )

    def get_for_deal(
        self, deal_id: str, item_id: str
    ) -> models.CompensationItem | None:
        return self.db.scalar(
            select(models.CompensationItem).where(
                models.CompensationItem.id == item_id,
                models.CompensationItem.deal_id == deal_id,
            )
        )

    def delete(self, item: models.CompensationItem) -> None:
        self.db.delete(item)
        self.db.flush()


class ImportSessionRepository(SqlAlchemyRepository[models.ImportSession]):
    model = models.ImportSession


class StoredFileRepository(SqlAlchemyRepository[models.StoredFile]):
    model = models.StoredFile

    def delete(self, stored_file: models.StoredFile) -> None:
        self.db.delete(stored_file)
        self.db.flush()


class DealAttachmentRepository(SqlAlchemyRepository[models.DealAttachment]):
    model = models.DealAttachment

    def list_for_deal(self, deal_id: str) -> list[models.DealAttachment]:
        return list(
            self.db.scalars(
                select(models.DealAttachment)
                .options(selectinload(models.DealAttachment.file))
                .where(models.DealAttachment.deal_id == deal_id)
                .order_by(models.DealAttachment.created_at.desc())
            )
        )

    def get_for_deal(self, deal_id: str, attachment_id: str) -> models.DealAttachment | None:
        return self.db.scalar(
            select(models.DealAttachment)
            .options(selectinload(models.DealAttachment.file))
            .where(
                models.DealAttachment.id == attachment_id,
                models.DealAttachment.deal_id == deal_id,
            )
        )

    def delete(self, attachment: models.DealAttachment) -> None:
        self.db.delete(attachment)
        self.db.flush()


class CampaignAttachmentRepository(SqlAlchemyRepository[models.CampaignAttachment]):
    model = models.CampaignAttachment

    def list_for_campaign(self, campaign_id: str) -> list[models.CampaignAttachment]:
        return list(
            self.db.scalars(
                select(models.CampaignAttachment)
                .options(selectinload(models.CampaignAttachment.file))
                .where(models.CampaignAttachment.campaign_id == campaign_id)
                .order_by(models.CampaignAttachment.created_at.desc())
            )
        )

    def get_for_campaign(
        self, campaign_id: str, attachment_id: str
    ) -> models.CampaignAttachment | None:
        return self.db.scalar(
            select(models.CampaignAttachment)
            .options(selectinload(models.CampaignAttachment.file))
            .where(
                models.CampaignAttachment.id == attachment_id,
                models.CampaignAttachment.campaign_id == campaign_id,
            )
        )

    def delete(self, attachment: models.CampaignAttachment) -> None:
        self.db.delete(attachment)
        self.db.flush()


class JobRecordRepository(SqlAlchemyRepository[models.JobRecord]):
    model = models.JobRecord

    def list(self, *, status: str | None = None, type: str | None = None) -> list[models.JobRecord]:
        stmt = select(models.JobRecord).order_by(models.JobRecord.created_at.desc())
        if status:
            stmt = stmt.where(models.JobRecord.status == status)
        if type:
            stmt = stmt.where(models.JobRecord.type == type)
        return list(self.db.scalars(stmt))


class TemplateRepository(SqlAlchemyRepository[models.Template]):
    model = models.Template

    def list(self, *, include_archived: bool = False) -> list[models.Template]:
        stmt = select(models.Template).order_by(models.Template.updated_at.desc())
        if not include_archived:
            stmt = stmt.where(models.Template.is_archived.is_(False))
        return list(self.db.scalars(stmt))

    def archive(self, entity: models.Template) -> models.Template:
        entity.is_archived = True
        self.db.flush()
        return entity

    def delete_archived(self) -> int:
        result = self.db.execute(
            delete(models.Template).where(models.Template.is_archived.is_(True))
        )
        self.db.flush()
        return result.rowcount or 0
