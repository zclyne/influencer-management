from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.schemas import ApiErrorResponse
from app.db.session import get_db
from app.email_context.schemas import (
    EmailThreadLinkCreateRequest,
    EmailThreadLinkListResponse,
    EmailThreadLinkResponse,
    EmailThreadLinkUpdateRequest,
    EmailThreadListResponse,
    EmailThreadMatchRequest,
    EmailThreadMatchResponse,
    EmailThreadMetadataResponse,
    ScopedEmailThreadListResponse,
)
from app.services.email_context import EmailContextService, EmailContextServiceError

router = APIRouter(tags=["email"])


def _http_error_response(error: EmailContextServiceError) -> JSONResponse:
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


@router.get("/email/threads", response_model=EmailThreadListResponse, responses=ERROR_RESPONSES)
def list_threads(
    db: Annotated[Session, Depends(get_db)],
    provider: str | None = None,
) -> EmailThreadListResponse | JSONResponse:
    try:
        return EmailContextService(db).list_threads(provider=provider)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.get(
    "/email/threads/{provider}/{external_thread_id}",
    response_model=EmailThreadMetadataResponse,
    responses=ERROR_RESPONSES,
)
def get_thread(
    provider: str,
    external_thread_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> EmailThreadMetadataResponse | JSONResponse:
    try:
        return EmailContextService(db).get_thread(provider, external_thread_id)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/email/threads/match",
    response_model=EmailThreadMatchResponse,
    responses=ERROR_RESPONSES,
)
def match_thread(
    payload: EmailThreadMatchRequest,
    db: Annotated[Session, Depends(get_db)],
) -> EmailThreadMatchResponse | JSONResponse:
    try:
        return EmailContextService(db).match_thread(payload)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.get(
    "/email/thread-links",
    response_model=EmailThreadLinkListResponse,
    responses=ERROR_RESPONSES,
)
def list_links(
    db: Annotated[Session, Depends(get_db)],
    provider: str | None = None,
    external_thread_id: str | None = None,
    deal_id: str | None = None,
    influencer_id: str | None = None,
) -> EmailThreadLinkListResponse | JSONResponse:
    try:
        return EmailContextService(db).list_links(
            provider=provider,
            external_thread_id=external_thread_id,
            deal_id=deal_id,
            influencer_id=influencer_id,
        )
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/email/thread-links",
    status_code=status.HTTP_201_CREATED,
    response_model=EmailThreadLinkResponse,
    responses=ERROR_RESPONSES,
)
def create_link(
    payload: EmailThreadLinkCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> EmailThreadLinkResponse | JSONResponse:
    try:
        return EmailContextService(db).create_link(payload)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.patch(
    "/email/thread-links/{link_id}",
    response_model=EmailThreadLinkResponse,
    responses=ERROR_RESPONSES,
)
def update_link(
    link_id: str,
    payload: EmailThreadLinkUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> EmailThreadLinkResponse | JSONResponse:
    try:
        return EmailContextService(db).update_link(link_id, payload)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.delete(
    "/email/thread-links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def delete_link(
    link_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        EmailContextService(db).delete_link(link_id)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/deals/{deal_id}/email-threads",
    response_model=ScopedEmailThreadListResponse,
    responses=ERROR_RESPONSES,
)
def list_deal_threads(
    deal_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> ScopedEmailThreadListResponse | JSONResponse:
    try:
        return EmailContextService(db).list_deal_threads(deal_id)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.get(
    "/influencers/{influencer_id}/email-threads",
    response_model=ScopedEmailThreadListResponse,
    responses=ERROR_RESPONSES,
)
def list_influencer_threads(
    influencer_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> ScopedEmailThreadListResponse | JSONResponse:
    try:
        return EmailContextService(db).list_influencer_threads(influencer_id)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)
