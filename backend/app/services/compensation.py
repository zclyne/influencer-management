from typing import Any

from sqlalchemy.orm import Session

from app.compensation.schemas import (
    CompensationItemCreateRequest,
    CompensationItemListResponse,
    CompensationItemResponse,
    CompensationItemUpdateRequest,
)
from app.db import models
from app.domain.enums import CompensationItemStatus, CompensationItemType
from app.repositories.sqlalchemy import CompensationItemRepository, DealRepository
from app.services.deals import DealNotFound, DealServiceError, mark_completed_at_if_needed
from app.services.deliverables import ArchivedDealMutation


class CompensationItemNotFound(DealServiceError):
    code = "not_found"
    status_code = 404


class CompensationItemService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.deals = DealRepository(db)
        self.items = CompensationItemRepository(db)

    def list_for_deal(self, deal_id: str) -> CompensationItemListResponse:
        self._require_deal(deal_id)
        return CompensationItemListResponse(
            compensation_items=[
                self._response(item) for item in self.items.list_for_deal(deal_id)
            ]
        )

    def create(
        self, deal_id: str, payload: CompensationItemCreateRequest
    ) -> CompensationItemResponse:
        self._require_mutable_deal(deal_id)
        values = payload.model_dump()
        values["type"] = payload.type.value
        values["status"] = payload.status.value
        if values.get("amount") is not None and not values.get("currency"):
            values["currency"] = "USD"
        values = mark_completed_at_if_needed(values)
        item = self.items.create(deal_id=deal_id, **values)
        self.db.commit()
        return self._response(item)

    def update(
        self,
        deal_id: str,
        item_id: str,
        payload: CompensationItemUpdateRequest,
    ) -> CompensationItemResponse:
        self._require_mutable_deal(deal_id)
        item = self.items.get_for_deal(deal_id, item_id)
        if not item:
            raise CompensationItemNotFound(
                "Compensation item not found.",
                details={"deal_id": deal_id, "item_id": item_id},
            )
        values = self._update_values(item, payload)
        if values:
            item = self.items.update(item, **values)
            self.db.commit()
        return self._response(item)

    def delete(self, deal_id: str, item_id: str) -> None:
        self._require_mutable_deal(deal_id)
        item = self.items.get_for_deal(deal_id, item_id)
        if not item:
            raise CompensationItemNotFound(
                "Compensation item not found.",
                details={"deal_id": deal_id, "item_id": item_id},
            )
        self.items.delete(item)
        self.db.commit()

    def _require_deal(self, deal_id: str) -> models.Deal:
        deal = self.deals.get(deal_id)
        if not deal:
            raise DealNotFound("Deal not found.", details={"deal_id": deal_id})
        return deal

    def _require_mutable_deal(self, deal_id: str) -> models.Deal:
        deal = self._require_deal(deal_id)
        if deal.archived_at is not None:
            raise ArchivedDealMutation(
                "Archived deals cannot be modified.",
                details={"deal_id": deal_id},
            )
        return deal

    def _update_values(
        self,
        item: models.CompensationItem,
        payload: CompensationItemUpdateRequest,
    ) -> dict[str, Any]:
        values = payload.model_dump(exclude_unset=True)
        if isinstance(values.get("type"), CompensationItemType):
            values["type"] = values["type"].value
        if isinstance(values.get("status"), CompensationItemStatus):
            values["status"] = values["status"].value
        if values.get("amount") is not None and not values.get("currency") and not item.currency:
            values["currency"] = "USD"
        return mark_completed_at_if_needed(values)

    def _response(self, item: models.CompensationItem) -> CompensationItemResponse:
        return CompensationItemResponse(
            id=item.id,
            deal_id=item.deal_id,
            type=CompensationItemType(item.type),
            description=item.description,
            amount=item.amount,
            currency=item.currency,
            recipient_name=item.recipient_name,
            status=CompensationItemStatus(item.status),
            due_date=item.due_date,
            completed_at=item.completed_at,
            receipt_file_id=item.receipt_file_id,
            notes=item.notes,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
