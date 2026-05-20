import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiErrorResponse
from app.schemas.email_context import (
    EmailDraftSendResponse,
    EmailParticipant,
    EmailReplyDraftResponse,
    EmailThreadBatchRequest,
    EmailThreadBatchResponse,
    EmailThreadLinkRequest,
    EmailThreadLinkResponse,
    GmailAuthStartResponse,
    GmailAuthStatusResponse,
    GmailLabelListResponse,
    GmailThreadDetailResponse,
    GmailThreadListResponse,
)
from app.services.email_context import EmailContextService, EmailContextServiceError, EmailDraftFile

router = APIRouter(prefix="/email", tags=["email"])


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


ERROR_RESPONSES = {
    401: {"model": ApiErrorResponse},
    404: {"model": ApiErrorResponse},
    422: {"model": ApiErrorResponse},
    502: {"model": ApiErrorResponse},
}


@router.get("/auth/status", response_model=GmailAuthStatusResponse, responses=ERROR_RESPONSES)
def auth_status(db: Annotated[Session, Depends(get_db)]) -> GmailAuthStatusResponse | JSONResponse:
    try:
        return EmailContextService(db).auth_status()
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.post("/auth/start", response_model=GmailAuthStartResponse, responses=ERROR_RESPONSES)
def start_auth(db: Annotated[Session, Depends(get_db)]) -> GmailAuthStartResponse | JSONResponse:
    try:
        return EmailContextService(db).start_auth()
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.get("/auth/callback", response_model=None, responses=ERROR_RESPONSES)
def auth_callback(
    db: Annotated[Session, Depends(get_db)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse | JSONResponse:
    service = EmailContextService(db)
    frontend_url = service.settings.gmail_frontend_redirect_uri
    if error:
        return RedirectResponse(
            url=f"{frontend_url}?gmailError={error}",
            status_code=status.HTTP_302_FOUND,
        )
    if not code:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ApiErrorResponse(
                code="missing_oauth_code",
                message="Google OAuth callback did not include a code.",
                details={},
                request_id=None,
            ).model_dump(),
        )
    try:
        service.complete_auth(code, state)
        return RedirectResponse(
            url=f"{frontend_url}?gmailConnected=1",
            status_code=status.HTTP_302_FOUND,
        )
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/auth/disconnect",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def disconnect(db: Annotated[Session, Depends(get_db)]) -> Response | JSONResponse:
    try:
        EmailContextService(db).disconnect()
    except EmailContextServiceError as exc:
        return _http_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/labels", response_model=GmailLabelListResponse, responses=ERROR_RESPONSES)
def list_labels(db: Annotated[Session, Depends(get_db)]) -> GmailLabelListResponse | JSONResponse:
    try:
        return EmailContextService(db).list_labels()
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.get("/threads", response_model=GmailThreadListResponse, responses=ERROR_RESPONSES)
def list_threads(
    db: Annotated[Session, Depends(get_db)],
    campaign_id: str | None = None,
    deal_id: str | None = None,
    q: str | None = None,
    label: str | None = None,
    view: str | None = None,
    page_token: str | None = None,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> GmailThreadListResponse | JSONResponse:
    try:
        return EmailContextService(db).list_threads(
            campaign_id=campaign_id,
            deal_id=deal_id,
            query=q,
            label=label,
            view=view,
            page_token=page_token,
            page_size=page_size,
        )
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.post("/threads/batch", response_model=EmailThreadBatchResponse, responses=ERROR_RESPONSES)
def batch_threads(
    payload: EmailThreadBatchRequest,
    db: Annotated[Session, Depends(get_db)],
) -> EmailThreadBatchResponse | JSONResponse:
    try:
        return EmailContextService(db).batch_threads(payload)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.get(
    "/threads/{thread_id}",
    response_model=GmailThreadDetailResponse,
    responses=ERROR_RESPONSES,
)
def get_thread(
    thread_id: str,
    db: Annotated[Session, Depends(get_db)],
    mark_read: bool = True,
) -> GmailThreadDetailResponse | JSONResponse:
    try:
        return EmailContextService(db).get_thread(thread_id, mark_read=mark_read)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/threads/{thread_id}/links",
    response_model=EmailThreadLinkResponse,
    responses=ERROR_RESPONSES,
)
def link_thread(
    thread_id: str,
    payload: EmailThreadLinkRequest,
    db: Annotated[Session, Depends(get_db)],
) -> EmailThreadLinkResponse | JSONResponse:
    try:
        return EmailContextService(db).link_thread(thread_id, payload)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.delete(
    "/threads/{thread_id}/links",
    response_model=EmailThreadLinkResponse,
    responses=ERROR_RESPONSES,
)
def unlink_thread(
    thread_id: str,
    db: Annotated[Session, Depends(get_db)],
    campaign_id: str | None = None,
    deal_id: str | None = None,
) -> EmailThreadLinkResponse | JSONResponse:
    try:
        return EmailContextService(db).unlink_thread(
            thread_id,
            campaign_id=campaign_id,
            deal_id=deal_id,
        )
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/threads/{thread_id}/draft-replies",
    response_model=EmailReplyDraftResponse,
    responses=ERROR_RESPONSES,
)
async def save_reply_draft(
    thread_id: str,
    db: Annotated[Session, Depends(get_db)],
    draft_id: Annotated[str | None, Form()] = None,
    reply_mode: Annotated[str, Form()] = "reply",
    anchor_message_id: Annotated[str | None, Form()] = None,
    to: Annotated[str, Form()] = "[]",
    cc: Annotated[str, Form()] = "[]",
    bcc: Annotated[str, Form()] = "[]",
    subject: Annotated[str | None, Form()] = None,
    body_html: Annotated[str | None, Form()] = None,
    body_text: Annotated[str | None, Form()] = None,
    inline_image_cids: Annotated[list[str] | None, Form()] = None,
    inline_images: Annotated[list[UploadFile] | None, File()] = None,
    attachments: Annotated[list[UploadFile] | None, File()] = None,
) -> EmailReplyDraftResponse | JSONResponse:
    try:
        return EmailContextService(db).save_reply_draft(
            thread_id,
            draft_id=draft_id,
            reply_mode=reply_mode,
            anchor_message_id=anchor_message_id,
            to=_participants_from_json(to),
            cc=_participants_from_json(cc),
            bcc=_participants_from_json(bcc),
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            inline_images=await _draft_files(inline_images or [], cids=inline_image_cids or []),
            attachments=await _draft_files(attachments or []),
        )
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/drafts/{draft_id}/send",
    response_model=EmailDraftSendResponse,
    responses=ERROR_RESPONSES,
)
def send_draft(
    draft_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> EmailDraftSendResponse | JSONResponse:
    try:
        return EmailContextService(db).send_draft(draft_id)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)


@router.delete(
    "/drafts/{draft_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def delete_draft(draft_id: str, db: Annotated[Session, Depends(get_db)]) -> Response | JSONResponse:
    try:
        EmailContextService(db).delete_draft(draft_id)
    except EmailContextServiceError as exc:
        return _http_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _participants_from_json(value: str) -> list[EmailParticipant]:
    try:
        payload = json.loads(value or "[]")
    except json.JSONDecodeError as exc:
        raise EmailContextServiceError("Recipient payload is not valid JSON.") from exc
    if not isinstance(payload, list):
        raise EmailContextServiceError("Recipient payload must be a list.")
    return [EmailParticipant.model_validate(item) for item in payload]


async def _draft_files(
    files: list[UploadFile],
    *,
    cids: list[str] | None = None,
) -> list[EmailDraftFile]:
    cids = cids or []
    output: list[EmailDraftFile] = []
    for index, file in enumerate(files):
        output.append(
            EmailDraftFile(
                filename=file.filename or "attachment",
                content_type=file.content_type or "application/octet-stream",
                content=await file.read(),
                cid=cids[index] if index < len(cids) else None,
            )
        )
    return output
