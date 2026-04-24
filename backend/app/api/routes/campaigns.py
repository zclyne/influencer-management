from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.campaigns.schemas import (
    ApiErrorResponse,
    CampaignBrandLinkRequest,
    CampaignBrandResponse,
    CampaignBrandUpdateRequest,
    CampaignCreateRequest,
    CampaignListResponse,
    CampaignResponse,
    CampaignUpdateRequest,
)
from app.db.session import get_db
from app.domain.enums import CampaignStatus
from app.services.campaigns import CampaignService, CampaignServiceError

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _error_payload(error: CampaignServiceError) -> dict[str, object]:
    return ApiErrorResponse(
        code=error.code,
        message=error.message,
        details=error.details,
        request_id=None,
    ).model_dump()


def _http_error_response(error: CampaignServiceError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content=_error_payload(error))


ERROR_RESPONSES = {
    404: {"model": ApiErrorResponse},
    409: {"model": ApiErrorResponse},
    422: {"model": ApiErrorResponse},
}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CampaignResponse,
    responses=ERROR_RESPONSES,
)
def create_campaign(
    payload: CampaignCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CampaignResponse | JSONResponse:
    try:
        return CampaignService(db).create_campaign(payload)
    except CampaignServiceError as exc:
        return _http_error_response(exc)


@router.get("", response_model=CampaignListResponse, responses=ERROR_RESPONSES)
def list_campaigns(
    db: Annotated[Session, Depends(get_db)],
    status: CampaignStatus | None = None,
    include_archived: bool = False,
) -> CampaignListResponse | JSONResponse:
    try:
        return CampaignService(db).list_campaigns(
            status=status,
            include_archived=include_archived,
        )
    except CampaignServiceError as exc:
        return _http_error_response(exc)


@router.get("/{campaign_id}", response_model=CampaignResponse, responses=ERROR_RESPONSES)
def get_campaign(
    campaign_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> CampaignResponse | JSONResponse:
    try:
        return CampaignService(db).get_campaign(campaign_id)
    except CampaignServiceError as exc:
        return _http_error_response(exc)


@router.patch("/{campaign_id}", response_model=CampaignResponse, responses=ERROR_RESPONSES)
def update_campaign(
    campaign_id: str,
    payload: CampaignUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CampaignResponse | JSONResponse:
    try:
        return CampaignService(db).update_campaign(campaign_id, payload)
    except CampaignServiceError as exc:
        return _http_error_response(exc)


@router.delete(
    "/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def archive_campaign(
    campaign_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        CampaignService(db).archive_campaign(campaign_id)
    except CampaignServiceError as exc:
        return _http_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{campaign_id}/brands",
    status_code=status.HTTP_201_CREATED,
    response_model=CampaignBrandResponse,
    responses=ERROR_RESPONSES,
)
def add_campaign_brand(
    campaign_id: str,
    payload: CampaignBrandLinkRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CampaignBrandResponse | JSONResponse:
    try:
        return CampaignService(db).add_brand(
            campaign_id,
            brand_id=payload.brand_id,
            role=payload.role,
            notes=payload.notes,
        )
    except CampaignServiceError as exc:
        return _http_error_response(exc)


@router.patch(
    "/{campaign_id}/brands/{brand_id}",
    response_model=CampaignBrandResponse,
    responses=ERROR_RESPONSES,
)
def update_campaign_brand(
    campaign_id: str,
    brand_id: str,
    payload: CampaignBrandUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CampaignBrandResponse | JSONResponse:
    try:
        return CampaignService(db).update_brand_link(
            campaign_id,
            brand_id,
            payload,
        )
    except CampaignServiceError as exc:
        return _http_error_response(exc)


@router.delete(
    "/{campaign_id}/brands/{brand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def remove_campaign_brand(
    campaign_id: str,
    brand_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        CampaignService(db).remove_brand(campaign_id, brand_id)
    except CampaignServiceError as exc:
        return _http_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
