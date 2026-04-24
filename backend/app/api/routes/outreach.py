from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.schemas import ApiErrorResponse
from app.db.session import get_db
from app.outreach.schemas import (
    BulkOutreachDraftRequest,
    BulkOutreachDraftResponse,
    OutreachDraftRequest,
    OutreachDraftResponse,
    OutreachTemplateCreateRequest,
    OutreachTemplateListResponse,
    OutreachTemplateResponse,
    OutreachTemplateUpdateRequest,
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


@router.get(
    "/outreach/templates",
    response_model=OutreachTemplateListResponse,
    responses=ERROR_RESPONSES,
)
def list_templates(
    db: Annotated[Session, Depends(get_db)],
    include_archived: bool = False,
) -> OutreachTemplateListResponse | JSONResponse:
    try:
        return OutreachService(db).list_templates(include_archived=include_archived)
    except OutreachServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/outreach/templates",
    status_code=status.HTTP_201_CREATED,
    response_model=OutreachTemplateResponse,
    responses=ERROR_RESPONSES,
)
def create_template(
    payload: OutreachTemplateCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> OutreachTemplateResponse | JSONResponse:
    try:
        return OutreachService(db).create_template(payload)
    except OutreachServiceError as exc:
        return _http_error_response(exc)


@router.get(
    "/outreach/templates/{template_id}",
    response_model=OutreachTemplateResponse,
    responses=ERROR_RESPONSES,
)
def get_template(
    template_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> OutreachTemplateResponse | JSONResponse:
    try:
        return OutreachService(db).get_template(template_id)
    except OutreachServiceError as exc:
        return _http_error_response(exc)


@router.patch(
    "/outreach/templates/{template_id}",
    response_model=OutreachTemplateResponse,
    responses=ERROR_RESPONSES,
)
def update_template(
    template_id: str,
    payload: OutreachTemplateUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> OutreachTemplateResponse | JSONResponse:
    try:
        return OutreachService(db).update_template(template_id, payload)
    except OutreachServiceError as exc:
        return _http_error_response(exc)


@router.delete(
    "/outreach/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def archive_template(
    template_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        OutreachService(db).archive_template(template_id)
    except OutreachServiceError as exc:
        return _http_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
