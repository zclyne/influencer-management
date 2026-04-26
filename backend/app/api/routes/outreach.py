from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiErrorResponse
from app.schemas.outreach import (
    BulkOutreachDraftRequest,
    BulkOutreachDraftResponse,
    OutreachDraftRequest,
    OutreachDraftResponse,
)
from app.services.outreach import OutreachService, OutreachServiceError

router = APIRouter(tags=["outreach"])


def _http_error_response(error: OutreachServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=ApiErrorResponse(
            code=error.code,
            message=error.message,
            details=error.details,
            request_id=None,
        ).model_dump(),
    )


ERROR_RESPONSES = {404: {"model": ApiErrorResponse}, 422: {"model": ApiErrorResponse}}


@router.post(
    "/deals/{deal_id}/outreach-drafts",
    response_model=OutreachDraftResponse,
    responses=ERROR_RESPONSES,
)
def render_deal_draft(
    deal_id: str,
    payload: OutreachDraftRequest,
    db: Annotated[Session, Depends(get_db)],
) -> OutreachDraftResponse | JSONResponse:
    try:
        return OutreachService(db).render_deal_draft(deal_id, payload)
    except OutreachServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/campaigns/{campaign_id}/outreach-drafts/bulk",
    response_model=BulkOutreachDraftResponse,
    responses=ERROR_RESPONSES,
)
def render_campaign_drafts(
    campaign_id: str,
    payload: BulkOutreachDraftRequest,
    db: Annotated[Session, Depends(get_db)],
) -> BulkOutreachDraftResponse | JSONResponse:
    try:
        return OutreachService(db).render_campaign_drafts(campaign_id, payload)
    except OutreachServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/deals/{deal_id}/outreach-sent",
    response_model=OutreachDraftResponse,
    responses=ERROR_RESPONSES,
)
def confirm_sent(
    deal_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> OutreachDraftResponse | JSONResponse:
    try:
        return OutreachService(db).confirm_sent(deal_id)
    except OutreachServiceError as exc:
        return _http_error_response(exc)
