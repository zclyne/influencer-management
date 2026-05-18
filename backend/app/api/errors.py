from typing import Any, Protocol

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import ApiErrorResponse


class SupportsApiError(Protocol):
    code: str
    message: str
    status_code: int
    details: dict[str, object] | None


ERROR_RESPONSES = {
    400: {"model": ApiErrorResponse},
    404: {"model": ApiErrorResponse},
    409: {"model": ApiErrorResponse},
    422: {"model": ApiErrorResponse},
}


def api_error_payload(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    return ApiErrorResponse(
        code=code,
        message=message,
        details=details or {},
        request_id=request_id,
    ).model_dump()


def service_error_response(error: SupportsApiError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=api_error_payload(
            code=error.code,
            message=error.message,
            details=error.details,
        ),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = []
    for error in exc.errors():
        cleaned = dict(error)
        if isinstance(cleaned.get("ctx"), dict):
            cleaned["ctx"] = {
                key: str(value) for key, value in cleaned["ctx"].items()
            }
        errors.append(cleaned)
    return JSONResponse(
        status_code=422,
        content=api_error_payload(
            code="validation_error",
            message="Request validation failed.",
            details=jsonable_encoder(
                {"errors": errors, "path": str(request.url.path)}
            ),
        ),
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    detail = exc.detail
    message = detail if isinstance(detail, str) else exc.__class__.__name__
    details: dict[str, Any] = {"path": str(request.url.path)}
    if not isinstance(detail, str) and detail is not None:
        details["detail"] = jsonable_encoder(detail)

    if exc.status_code == 404:
        code = "not_found"
    elif exc.status_code >= 500:
        code = "server_error"
    else:
        code = "request_error"

    return JSONResponse(
        status_code=exc.status_code,
        content=api_error_payload(
            code=code,
            message=message or "Request failed.",
            details=details,
        ),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=api_error_payload(
            code="server_error",
            message="Internal server error.",
            details={"path": str(request.url.path)},
        ),
    )
