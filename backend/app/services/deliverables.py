from typing import Any

from sqlalchemy.orm import Session

from app.db import models
from app.enums import DeliverableStatus
from app.repositories.sqlalchemy import DealRepository, DeliverableRepository
from app.schemas.deliverables import (
    DeliverableCreateRequest,
    DeliverableListResponse,
    DeliverableResponse,
    DeliverableUpdateRequest,
)
from app.services.deals import DealNotFound, DealServiceError


class DeliverableNotFound(DealServiceError):
    code = "not_found"
    status_code = 404


class ArchivedDealMutation(DealServiceError):
    code = "archived_deal"
    status_code = 409


class DeliverableService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.deals = DealRepository(db)
        self.deliverables = DeliverableRepository(db)

    def list_for_deal(self, deal_id: str) -> DeliverableListResponse:
        self._require_deal(deal_id)
        return DeliverableListResponse(
            deliverables=[
                self._response(deliverable)
                for deliverable in self.deliverables.list_for_deal(deal_id)
            ]
        )

    def create(
        self, deal_id: str, payload: DeliverableCreateRequest
    ) -> DeliverableResponse:
        self._require_mutable_deal(deal_id)
        deliverable = self.deliverables.create(
            deal_id=deal_id,
            type=payload.type.strip(),
            quantity=payload.quantity,
            due_date=payload.due_date,
            status=payload.status.value,
            published_url=payload.published_url,
            notes=payload.notes,
        )
        self.db.commit()
        return self._response(deliverable)

    def update(
        self,
        deal_id: str,
        deliverable_id: str,
        payload: DeliverableUpdateRequest,
    ) -> DeliverableResponse:
        self._require_mutable_deal(deal_id)
        deliverable = self.deliverables.get_for_deal(deal_id, deliverable_id)
        if not deliverable:
            raise DeliverableNotFound(
                "Deliverable not found.",
                details={"deal_id": deal_id, "deliverable_id": deliverable_id},
            )
        values = self._update_values(payload)
        if values:
            deliverable = self.deliverables.update(deliverable, **values)
            self.db.commit()
        return self._response(deliverable)

    def delete(self, deal_id: str, deliverable_id: str) -> None:
        self._require_mutable_deal(deal_id)
        deliverable = self.deliverables.get_for_deal(deal_id, deliverable_id)
        if not deliverable:
            raise DeliverableNotFound(
                "Deliverable not found.",
                details={"deal_id": deal_id, "deliverable_id": deliverable_id},
            )
        self.deliverables.delete(deliverable)
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

    def _update_values(self, payload: DeliverableUpdateRequest) -> dict[str, Any]:
        values = payload.model_dump(exclude_unset=True)
        if isinstance(values.get("status"), DeliverableStatus):
            values["status"] = values["status"].value
        if "type" in values and values["type"] is not None:
            values["type"] = values["type"].strip()
        return values

    def _response(self, deliverable: models.Deliverable) -> DeliverableResponse:
        return DeliverableResponse(
            id=deliverable.id,
            deal_id=deliverable.deal_id,
            type=deliverable.type,
            quantity=deliverable.quantity,
            due_date=deliverable.due_date,
            status=DeliverableStatus(deliverable.status),
            published_url=deliverable.published_url,
            notes=deliverable.notes,
            created_at=deliverable.created_at,
            updated_at=deliverable.updated_at,
        )
