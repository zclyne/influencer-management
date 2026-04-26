from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.errors import ERROR_RESPONSES, service_error_response
from app.db.session import get_db
from app.schemas.brands import (
    BrandCreateRequest,
    BrandListResponse,
    BrandResponse,
    BrandUpdateRequest,
)
from app.services.brands import BrandService, BrandServiceError

router = APIRouter(prefix="/brands", tags=["brands"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=BrandResponse,
    responses=ERROR_RESPONSES,
)
def create_brand(
    payload: BrandCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> BrandResponse | JSONResponse:
    try:
        return BrandService(db).create_brand(payload)
    except BrandServiceError as exc:
        return service_error_response(exc)


@router.get("", response_model=BrandListResponse, responses=ERROR_RESPONSES)
def list_brands(
    db: Annotated[Session, Depends(get_db)],
    query: str | None = None,
    include_archived: bool = False,
) -> BrandListResponse:
    return BrandService(db).list_brands(query=query, include_archived=include_archived)


@router.get("/{brand_id}", response_model=BrandResponse, responses=ERROR_RESPONSES)
def get_brand(
    brand_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> BrandResponse | JSONResponse:
    try:
        return BrandService(db).get_brand(brand_id)
    except BrandServiceError as exc:
        return service_error_response(exc)


@router.patch("/{brand_id}", response_model=BrandResponse, responses=ERROR_RESPONSES)
def update_brand(
    brand_id: str,
    payload: BrandUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> BrandResponse | JSONResponse:
    try:
        return BrandService(db).update_brand(brand_id, payload)
    except BrandServiceError as exc:
        return service_error_response(exc)


@router.delete(
    "/{brand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def archive_brand(
    brand_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        BrandService(db).archive_brand(brand_id)
    except BrandServiceError as exc:
        return service_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
