from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.api.schemas import ApiErrorResponse
from app.db.session import get_db
from app.files.schemas import StoredFileResponse
from app.services.files import FileService, FileServiceError

router = APIRouter(prefix="/files", tags=["files"])


def _http_error_response(error: FileServiceError) -> JSONResponse:
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


@router.get("/{file_id}", response_model=StoredFileResponse, responses=ERROR_RESPONSES)
def get_file(
    file_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> StoredFileResponse | JSONResponse:
    try:
        return FileService(db).get_file(file_id)
    except FileServiceError as exc:
        return _http_error_response(exc)


@router.get("/{file_id}/download", response_model=None, responses=ERROR_RESPONSES)
def download_file(
    file_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse | JSONResponse:
    service = FileService(db)
    try:
        file = service.get_file(file_id)
        path = service.resolve_download_path(file_id)
    except FileServiceError as exc:
        return _http_error_response(exc)
    return FileResponse(path, media_type=file.mime_type, filename=file.original_name)


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def delete_file(
    file_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        FileService(db).delete_file(file_id)
    except FileServiceError as exc:
        return _http_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
