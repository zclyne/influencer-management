from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.enums import DealStatus
from app.schemas.compensation import (
    CompensationItemCreateRequest,
    CompensationItemListResponse,
    CompensationItemResponse,
    CompensationItemUpdateRequest,
)
from app.schemas.deals import (
    ApiErrorResponse,
    DealBulkCreateRequest,
    DealBulkCreateResponse,
    DealBulkUpdateRequest,
    DealBulkUpdateResponse,
    DealCreateRequest,
    DealDetailResponse,
    DealListResponse,
    DealUpdateRequest,
)
from app.schemas.deliverables import (
    DeliverableCreateRequest,
    DeliverableListResponse,
    DeliverableResponse,
    DeliverableUpdateRequest,
)
from app.services.compensation import CompensationItemService
from app.services.deals import DealService, DealServiceError
from app.services.deliverables import DeliverableService

router = APIRouter(tags=["deals"])


def _error_payload(error: DealServiceError) -> dict[str, object]:
    return ApiErrorResponse(
        code=error.code,
        message=error.message,
        details=error.details,
        request_id=None,
    ).model_dump()


def _http_error_response(error: DealServiceError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content=_error_payload(error))


ERROR_RESPONSES = {
    404: {"model": ApiErrorResponse},
    409: {"model": ApiErrorResponse},
    422: {"model": ApiErrorResponse},
}


@router.get(
    "/campaigns/{campaign_id}/deals",
    response_model=DealListResponse,
    responses=ERROR_RESPONSES,
)
def list_campaign_deals(
    campaign_id: str,
    db: Annotated[Session, Depends(get_db)],
    status: DealStatus | None = None,
    platform: str | None = None,
    lost_reason: str | None = None,
    has_email_thread: bool | None = None,
    include_archived: bool = False,
    sort: str = "updated_at",
    limit: int | None = None,
    offset: int = 0,
) -> DealListResponse | JSONResponse:
    try:
        return DealService(db).list_campaign_deals(
            campaign_id,
            status=status,
            platform=platform,
            lost_reason=lost_reason,
            has_email_thread=has_email_thread,
            include_archived=include_archived,
            sort=sort,
            limit=limit,
            offset=offset,
        )
    except DealServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/campaigns/{campaign_id}/deals",
    status_code=status.HTTP_201_CREATED,
    response_model=DealDetailResponse,
    responses=ERROR_RESPONSES,
)
def create_deal(
    campaign_id: str,
    payload: DealCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> DealDetailResponse | JSONResponse:
    try:
        return DealService(db).create_deal(campaign_id, payload)
    except DealServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/campaigns/{campaign_id}/deals/bulk",
    response_model=DealBulkCreateResponse,
    responses=ERROR_RESPONSES,
)
def bulk_create_deals(
    campaign_id: str,
    payload: DealBulkCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> DealBulkCreateResponse | JSONResponse:
    try:
        return DealService(db).bulk_create_deals(campaign_id, payload)
    except DealServiceError as exc:
        return _http_error_response(exc)


@router.patch(
    "/campaigns/{campaign_id}/deals/bulk",
    response_model=DealBulkUpdateResponse,
    responses=ERROR_RESPONSES,
)
def bulk_update_deals(
    campaign_id: str,
    payload: DealBulkUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> DealBulkUpdateResponse | JSONResponse:
    try:
        return DealService(db).bulk_update_deals(campaign_id, payload)
    except DealServiceError as exc:
        return _http_error_response(exc)


@router.get(
    "/deals/{deal_id}",
    response_model=DealDetailResponse,
    responses=ERROR_RESPONSES,
)
def get_deal(
    deal_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> DealDetailResponse | JSONResponse:
    try:
        return DealService(db).get_deal(deal_id)
    except DealServiceError as exc:
        return _http_error_response(exc)


@router.patch(
    "/deals/{deal_id}",
    response_model=DealDetailResponse,
    responses=ERROR_RESPONSES,
)
def update_deal(
    deal_id: str,
    payload: DealUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> DealDetailResponse | JSONResponse:
    try:
        return DealService(db).update_deal(deal_id, payload)
    except DealServiceError as exc:
        return _http_error_response(exc)


@router.delete(
    "/deals/{deal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def archive_deal(
    deal_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        DealService(db).archive_deal(deal_id)
    except DealServiceError as exc:
        return _http_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/deals/{deal_id}/deliverables",
    response_model=DeliverableListResponse,
    responses=ERROR_RESPONSES,
)
def list_deliverables(
    deal_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> DeliverableListResponse | JSONResponse:
    try:
        return DeliverableService(db).list_for_deal(deal_id)
    except DealServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/deals/{deal_id}/deliverables",
    status_code=status.HTTP_201_CREATED,
    response_model=DeliverableResponse,
    responses=ERROR_RESPONSES,
)
def create_deliverable(
    deal_id: str,
    payload: DeliverableCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> DeliverableResponse | JSONResponse:
    try:
        return DeliverableService(db).create(deal_id, payload)
    except DealServiceError as exc:
        return _http_error_response(exc)


@router.patch(
    "/deals/{deal_id}/deliverables/{deliverable_id}",
    response_model=DeliverableResponse,
    responses=ERROR_RESPONSES,
)
def update_deliverable(
    deal_id: str,
    deliverable_id: str,
    payload: DeliverableUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> DeliverableResponse | JSONResponse:
    try:
        return DeliverableService(db).update(deal_id, deliverable_id, payload)
    except DealServiceError as exc:
        return _http_error_response(exc)


@router.delete(
    "/deals/{deal_id}/deliverables/{deliverable_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def delete_deliverable(
    deal_id: str,
    deliverable_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        DeliverableService(db).delete(deal_id, deliverable_id)
    except DealServiceError as exc:
        return _http_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/deals/{deal_id}/compensation-items",
    response_model=CompensationItemListResponse,
    responses=ERROR_RESPONSES,
)
def list_compensation_items(
    deal_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> CompensationItemListResponse | JSONResponse:
    try:
        return CompensationItemService(db).list_for_deal(deal_id)
    except DealServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/deals/{deal_id}/compensation-items",
    status_code=status.HTTP_201_CREATED,
    response_model=CompensationItemResponse,
    responses=ERROR_RESPONSES,
)
def create_compensation_item(
    deal_id: str,
    payload: CompensationItemCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CompensationItemResponse | JSONResponse:
    try:
        return CompensationItemService(db).create(deal_id, payload)
    except DealServiceError as exc:
        return _http_error_response(exc)


@router.patch(
    "/deals/{deal_id}/compensation-items/{item_id}",
    response_model=CompensationItemResponse,
    responses=ERROR_RESPONSES,
)
def update_compensation_item(
    deal_id: str,
    item_id: str,
    payload: CompensationItemUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CompensationItemResponse | JSONResponse:
    try:
        return CompensationItemService(db).update(deal_id, item_id, payload)
    except DealServiceError as exc:
        return _http_error_response(exc)


@router.delete(
    "/deals/{deal_id}/compensation-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def delete_compensation_item(
    deal_id: str,
    item_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        CompensationItemService(db).delete(deal_id, item_id)
    except DealServiceError as exc:
        return _http_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
