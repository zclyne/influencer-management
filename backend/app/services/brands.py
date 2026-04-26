from sqlalchemy.orm import Session

from app.db import models
from app.repositories.sqlalchemy import BrandRepository
from app.schemas.brands import (
    BrandCreateRequest,
    BrandListResponse,
    BrandResponse,
    BrandUpdateRequest,
)
from app.services.errors import ServiceError


class BrandServiceError(ServiceError):
    code = "brand_error"


class BrandNotFound(BrandServiceError):
    code = "not_found"
    status_code = 404


class BrandConflict(BrandServiceError):
    code = "brand_conflict"
    status_code = 409


class BrandService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.brands = BrandRepository(db)

    def create_brand(self, payload: BrandCreateRequest) -> BrandResponse:
        self._ensure_name_available(payload.name)
        brand = self.brands.create(
            name=payload.name,
            website=payload.website,
            notes=payload.notes,
        )
        self.db.commit()
        return self._brand_response(brand)

    def list_brands(
        self,
        *,
        query: str | None = None,
        include_archived: bool = False,
    ) -> BrandListResponse:
        campaign_counts = self.brands.campaign_counts()
        return BrandListResponse(
            brands=[
                self._brand_response(brand, campaign_count=campaign_counts.get(brand.id, 0))
                for brand in self.brands.list(query=query, include_archived=include_archived)
            ]
        )

    def get_brand(self, brand_id: str) -> BrandResponse:
        brand = self.brands.get(brand_id)
        if not brand:
            raise BrandNotFound("Brand not found.", details={"brand_id": brand_id})
        return self._brand_response(
            brand,
            campaign_count=self.brands.campaign_count(brand.id),
        )

    def update_brand(self, brand_id: str, payload: BrandUpdateRequest) -> BrandResponse:
        brand = self.brands.get(brand_id)
        if not brand:
            raise BrandNotFound("Brand not found.", details={"brand_id": brand_id})
        values = payload.model_dump(exclude_unset=True)
        name = values.get("name")
        if isinstance(name, str) and name.lower() != brand.name.lower():
            self._ensure_name_available(name, exclude_brand_id=brand.id)
        if values:
            brand = self.brands.update(brand, **values)
            self.db.commit()
        return self.get_brand(brand.id)

    def archive_brand(self, brand_id: str) -> None:
        brand = self.brands.get(brand_id)
        if not brand:
            raise BrandNotFound("Brand not found.", details={"brand_id": brand_id})
        self.brands.archive(brand)
        self.db.commit()

    def _ensure_name_available(
        self,
        name: str,
        *,
        exclude_brand_id: str | None = None,
    ) -> None:
        existing = self.brands.find_by_name(name)
        if existing and existing.id != exclude_brand_id:
            raise BrandConflict(
                "Brand name already exists.",
                details={"brand_id": existing.id, "name": name},
            )

    def _brand_response(
        self,
        brand: models.Brand,
        *,
        campaign_count: int | None = None,
    ) -> BrandResponse:
        return BrandResponse(
            id=brand.id,
            name=brand.name,
            website=brand.website,
            notes=brand.notes,
            archived_at=brand.archived_at,
            created_at=brand.created_at,
            updated_at=brand.updated_at,
            campaign_count=campaign_count,
        )
