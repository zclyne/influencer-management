from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiErrorResponse
from app.schemas.templates import (
    TemplateCreateRequest,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdateRequest,
)
from app.services.templates import TemplateService, TemplateServiceError

router = APIRouter(tags=["templates"])


def _http_error_response(error: TemplateServiceError) -> JSONResponse:
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
    "/templates",
    response_model=TemplateListResponse,
    responses=ERROR_RESPONSES,
)
def list_templates(
    db: Annotated[Session, Depends(get_db)],
    include_archived: bool = False,
) -> TemplateListResponse | JSONResponse:
    try:
        return TemplateService(db).list_templates(include_archived=include_archived)
    except TemplateServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/templates",
    status_code=status.HTTP_201_CREATED,
    response_model=TemplateResponse,
    responses=ERROR_RESPONSES,
)
def create_template(
    payload: TemplateCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TemplateResponse | JSONResponse:
    try:
        return TemplateService(db).create_template(payload)
    except TemplateServiceError as exc:
        return _http_error_response(exc)


@router.get(
    "/templates/{template_id}",
    response_model=TemplateResponse,
    responses=ERROR_RESPONSES,
)
def get_template(
    template_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> TemplateResponse | JSONResponse:
    try:
        return TemplateService(db).get_template(template_id)
    except TemplateServiceError as exc:
        return _http_error_response(exc)


@router.patch(
    "/templates/{template_id}",
    response_model=TemplateResponse,
    responses=ERROR_RESPONSES,
)
def update_template(
    template_id: str,
    payload: TemplateUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TemplateResponse | JSONResponse:
    try:
        return TemplateService(db).update_template(template_id, payload)
    except TemplateServiceError as exc:
        return _http_error_response(exc)


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def archive_template(
    template_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        TemplateService(db).archive_template(template_id)
    except TemplateServiceError as exc:
        return _http_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
