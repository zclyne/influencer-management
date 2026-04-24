from typing import Any, Protocol

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.schemas import ApiErrorResponse


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
    return JSONResponse(
        status_code=422,
        content=api_error_payload(
            code="validation_error",
            message="Request validation failed.",
            details=jsonable_encoder(
                {"errors": exc.errors(), "path": str(request.url.path)}
            ),
        ),
    )
