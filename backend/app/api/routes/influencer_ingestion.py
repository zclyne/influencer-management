from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.enums import ImportSourceType
from app.influencers.ingestion.schemas import (
    ApiErrorResponse,
    ImportPreviewInput,
    ImportSessionResponse,
    IngestionConfirmRequest,
    IngestionConfirmResponse,
    IngestionPreviewResponse,
)
from app.services.influencer_ingestion import (
    InfluencerIngestionService,
    InfluencerIngestionServiceError,
)

router = APIRouter(prefix="/influencers/imports", tags=["influencer-ingestion"])


def _error_payload(error: InfluencerIngestionServiceError) -> dict[str, object]:
    return ApiErrorResponse(
        code=error.code,
        message=error.message,
        details=error.details,
        request_id=None,
    ).model_dump()


def _http_error_response(error: InfluencerIngestionServiceError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content=_error_payload(error))


ERROR_RESPONSES = {
    404: {"model": ApiErrorResponse},
    422: {"model": ApiErrorResponse},
}


@router.post("/modash/preview", response_model=IngestionPreviewResponse, responses=ERROR_RESPONSES)
async def preview_modash_import(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
) -> IngestionPreviewResponse | JSONResponse:
    content = await file.read()
    try:
        return InfluencerIngestionService(db).preview_import(
            ImportPreviewInput(
                source_type=ImportSourceType.MODASH_CSV,
                file_name=file.filename,
                content=content,
            )
        )
    except InfluencerIngestionServiceError as exc:
        return _http_error_response(exc)


@router.post(
    "/confirm",
    response_model=IngestionConfirmResponse,
    responses=ERROR_RESPONSES,
)
def confirm_import(
    payload: IngestionConfirmRequest,
    db: Annotated[Session, Depends(get_db)],
) -> IngestionConfirmResponse | JSONResponse:
    try:
        return InfluencerIngestionService(db).confirm_import(payload)
    except InfluencerIngestionServiceError as exc:
        return _http_error_response(exc)


@router.get(
    "/sessions/{import_session_id}",
    response_model=ImportSessionResponse,
    responses=ERROR_RESPONSES,
)
def get_import_session(
    import_session_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> ImportSessionResponse | JSONResponse:
    try:
        return InfluencerIngestionService(db).get_session(import_session_id)
    except InfluencerIngestionServiceError as exc:
        return _http_error_response(exc)
