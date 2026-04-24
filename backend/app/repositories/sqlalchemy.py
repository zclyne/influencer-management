from datetime import UTC
from typing import Generic, TypeVar

from sqlalchemy import Select, func, select
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

    def find_by_display_name(self, display_name: str, limit: int = 5) -> list[models.Influencer]:
        stmt: Select[tuple[models.Influencer]] = (
            select(models.Influencer)
            .where(func.lower(models.Influencer.display_name) == display_name.lower())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))


class InfluencerPlatformRepository(SqlAlchemyRepository[models.InfluencerPlatform]):
    model = models.InfluencerPlatform

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
        clauses = [
            models.InfluencerPlatform.influencer_id == influencer_id,
            models.InfluencerPlatform.platform == platform,
        ]
        if normalized_profile_url:
            clauses.append(
                models.InfluencerPlatform.normalized_profile_url == normalized_profile_url
            )
        elif normalized_username:
            clauses.append(models.InfluencerPlatform.normalized_username == normalized_username)
        else:
            return None
        return self.db.scalar(select(models.InfluencerPlatform).where(*clauses))


class InfluencerAudienceSnapshotRepository(
    SqlAlchemyRepository[models.InfluencerAudienceSnapshot]
):
    model = models.InfluencerAudienceSnapshot


class InfluencerContactRepository(SqlAlchemyRepository[models.InfluencerContact]):
    model = models.InfluencerContact

    def find_by_email(self, email: str) -> list[models.InfluencerContact]:
        return list(
            self.db.scalars(
                select(models.InfluencerContact).where(models.InfluencerContact.email == email)
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


class DeliverableRepository(SqlAlchemyRepository[models.Deliverable]):
    model = models.Deliverable


class CompensationItemRepository(SqlAlchemyRepository[models.CompensationItem]):
    model = models.CompensationItem


class EmailThreadLinkRepository(SqlAlchemyRepository[models.EmailThreadLink]):
    model = models.EmailThreadLink


class ImportSessionRepository(SqlAlchemyRepository[models.ImportSession]):
    model = models.ImportSession


class StoredFileRepository(SqlAlchemyRepository[models.StoredFile]):
    model = models.StoredFile
