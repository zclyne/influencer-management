from typing import Any

from sqlalchemy.orm import Session

from app.campaigns.schemas import (
    BrandSummary,
    CampaignBrandResponse,
    CampaignBrandUpdateRequest,
    CampaignCreateRequest,
    CampaignListResponse,
    CampaignResponse,
    CampaignUpdateRequest,
)
from app.db import models
from app.enums import CampaignStatus
from app.repositories.sqlalchemy import BrandRepository, CampaignBrandRepository, CampaignRepository
from app.services.errors import ServiceError


class CampaignServiceError(ServiceError):
    code = "campaign_error"
    status_code = 422


class CampaignNotFound(CampaignServiceError):
    code = "not_found"
    status_code = 404


class CampaignBrandConflict(CampaignServiceError):
    code = "campaign_brand_conflict"
    status_code = 409


class BrandNotFound(CampaignServiceError):
    code = "not_found"
    status_code = 404


class CampaignService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.campaigns = CampaignRepository(db)
        self.brands = BrandRepository(db)
        self.campaign_brands = CampaignBrandRepository(db)

    def create_campaign(self, payload: CampaignCreateRequest) -> CampaignResponse:
        campaign = self.campaigns.create(
            name=payload.name,
            brief=payload.brief,
            budget=payload.budget,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=payload.status.value,
            notes=payload.notes,
        )
        self.db.commit()
        return self._campaign_response(campaign)

    def list_campaigns(
        self,
        *,
        status: CampaignStatus | None = None,
        include_archived: bool = False,
    ) -> CampaignListResponse:
        campaigns = self.campaigns.list(
            status=status.value if status else None,
            include_archived=include_archived,
        )
        return CampaignListResponse(
            campaigns=[self._campaign_response(campaign) for campaign in campaigns]
        )

    def get_campaign(self, campaign_id: str) -> CampaignResponse:
        campaign = self.campaigns.get_with_brands(campaign_id)
        if not campaign:
            raise CampaignNotFound(
                "Campaign not found.",
                details={"campaign_id": campaign_id},
            )
        return self._campaign_response(campaign)

    def update_campaign(
        self, campaign_id: str, payload: CampaignUpdateRequest
    ) -> CampaignResponse:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise CampaignNotFound(
                "Campaign not found.",
                details={"campaign_id": campaign_id},
            )
        values = self._campaign_update_values(payload)
        if values:
            campaign = self.campaigns.update(campaign, **values)
            self.db.commit()
        return self.get_campaign(campaign.id)

    def archive_campaign(self, campaign_id: str) -> None:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise CampaignNotFound(
                "Campaign not found.",
                details={"campaign_id": campaign_id},
            )
        self.campaigns.archive(campaign)
        self.db.commit()

    def add_brand(
        self,
        campaign_id: str,
        *,
        brand_id: str,
        role: str | None = None,
        notes: str | None = None,
    ) -> CampaignBrandResponse:
        campaign = self._require_campaign(campaign_id)
        brand = self.brands.get(brand_id)
        if not brand:
            raise BrandNotFound("Brand not found.", details={"brand_id": brand_id})
        existing = self.campaign_brands.get_by_campaign_brand(campaign_id, brand_id)
        if existing:
            raise CampaignBrandConflict(
                "Brand is already linked to this campaign.",
                details={"campaign_id": campaign_id, "brand_id": brand_id},
            )
        link = self.campaign_brands.create(
            campaign_id=campaign_id,
            brand_id=brand_id,
            role=role,
            notes=notes,
        )
        link.brand = brand
        self.db.expire(campaign, ["brand_links"])
        self.db.commit()
        return self._campaign_brand_response(link)

    def update_brand_link(
        self,
        campaign_id: str,
        brand_id: str,
        payload: CampaignBrandUpdateRequest,
    ) -> CampaignBrandResponse:
        self._require_campaign(campaign_id)
        link = self.campaign_brands.get_by_campaign_brand(campaign_id, brand_id)
        if not link:
            raise CampaignNotFound(
                "Campaign brand link not found.",
                details={"campaign_id": campaign_id, "brand_id": brand_id},
            )
        values = payload.model_dump(exclude_unset=True)
        if values:
            link = self.campaign_brands.update(link, **values)
            self.db.commit()
        return self._campaign_brand_response(link)

    def remove_brand(self, campaign_id: str, brand_id: str) -> None:
        campaign = self._require_campaign(campaign_id)
        link = self.campaign_brands.get_by_campaign_brand(campaign_id, brand_id)
        if not link:
            raise CampaignNotFound(
                "Campaign brand link not found.",
                details={"campaign_id": campaign_id, "brand_id": brand_id},
            )
        self.campaign_brands.delete(link)
        self.db.expire(campaign, ["brand_links"])
        self.db.commit()

    def _require_campaign(self, campaign_id: str) -> models.Campaign:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise CampaignNotFound(
                "Campaign not found.",
                details={"campaign_id": campaign_id},
            )
        return campaign

    def _campaign_update_values(self, payload: CampaignUpdateRequest) -> dict[str, Any]:
        values = payload.model_dump(exclude_unset=True)
        status = values.get("status")
        if isinstance(status, CampaignStatus):
            values["status"] = status.value
        return values

    def _campaign_response(self, campaign: models.Campaign) -> CampaignResponse:
        brand_links = sorted(
            campaign.brand_links,
            key=lambda link: link.created_at,
        )
        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            brief=campaign.brief,
            budget=campaign.budget,
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            status=CampaignStatus(campaign.status),
            notes=campaign.notes,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            archived_at=campaign.archived_at,
            brands=[self._campaign_brand_response(link) for link in brand_links],
        )

    def _campaign_brand_response(
        self, campaign_brand: models.CampaignBrand
    ) -> CampaignBrandResponse:
        return CampaignBrandResponse(
            id=campaign_brand.id,
            brand=BrandSummary(
                id=campaign_brand.brand.id,
                name=campaign_brand.brand.name,
                website=campaign_brand.brand.website,
                notes=campaign_brand.brand.notes,
            ),
            role=campaign_brand.role,
            notes=campaign_brand.notes,
            created_at=campaign_brand.created_at,
            updated_at=campaign_brand.updated_at,
        )
