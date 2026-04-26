from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.errors import ERROR_RESPONSES, service_error_response
from app.db.session import get_db
from app.schemas.influencers import (
    InfluencerContactCreateRequest,
    InfluencerContactListResponse,
    InfluencerContactResponse,
    InfluencerContactUpdateRequest,
    InfluencerCreateRequest,
    InfluencerDealListResponse,
    InfluencerListResponse,
    InfluencerPlatformCreateRequest,
    InfluencerPlatformListResponse,
    InfluencerPlatformResponse,
    InfluencerPlatformUpdateRequest,
    InfluencerResponse,
    InfluencerUpdateRequest,
    ManualInfluencerInput,
    ManualInfluencerResponse,
)
from app.services.influencers import InfluencerService, InfluencerServiceError

router = APIRouter(prefix="/influencers", tags=["influencers"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=InfluencerResponse,
    responses=ERROR_RESPONSES,
)
def create_influencer(
    payload: InfluencerCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> InfluencerResponse | JSONResponse:
    try:
        return InfluencerService(db).create_influencer(payload)
    except InfluencerServiceError as exc:
        return service_error_response(exc)


@router.get("", response_model=InfluencerListResponse, responses=ERROR_RESPONSES)
def list_influencers(
    db: Annotated[Session, Depends(get_db)],
    query: str | None = None,
    platform: str | None = None,
    country: str | None = None,
    city: str | None = None,
    include_archived: bool = False,
) -> InfluencerListResponse:
    return InfluencerService(db).list_influencers(
        query=query,
        platform=platform,
        country=country,
        city=city,
        include_archived=include_archived,
    )


@router.get("/{influencer_id}", response_model=InfluencerResponse, responses=ERROR_RESPONSES)
def get_influencer(
    influencer_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> InfluencerResponse | JSONResponse:
    try:
        return InfluencerService(db).get_influencer(influencer_id)
    except InfluencerServiceError as exc:
        return service_error_response(exc)


@router.patch("/{influencer_id}", response_model=InfluencerResponse, responses=ERROR_RESPONSES)
def update_influencer(
    influencer_id: str,
    payload: InfluencerUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> InfluencerResponse | JSONResponse:
    try:
        return InfluencerService(db).update_influencer(influencer_id, payload)
    except InfluencerServiceError as exc:
        return service_error_response(exc)


@router.delete(
    "/{influencer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def archive_influencer(
    influencer_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        InfluencerService(db).archive_influencer(influencer_id)
    except InfluencerServiceError as exc:
        return service_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{influencer_id}/platforms",
    response_model=InfluencerPlatformListResponse,
    responses=ERROR_RESPONSES,
)
def list_platforms(
    influencer_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> InfluencerPlatformListResponse | JSONResponse:
    try:
        return InfluencerService(db).list_platforms(influencer_id)
    except InfluencerServiceError as exc:
        return service_error_response(exc)


@router.post(
    "/{influencer_id}/platforms",
    status_code=status.HTTP_201_CREATED,
    response_model=InfluencerPlatformResponse,
    responses=ERROR_RESPONSES,
)
def create_platform(
    influencer_id: str,
    payload: InfluencerPlatformCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> InfluencerPlatformResponse | JSONResponse:
    try:
        return InfluencerService(db).create_platform(influencer_id, payload)
    except InfluencerServiceError as exc:
        return service_error_response(exc)


@router.patch(
    "/{influencer_id}/platforms/{platform_id}",
    response_model=InfluencerPlatformResponse,
    responses=ERROR_RESPONSES,
)
def update_platform(
    influencer_id: str,
    platform_id: str,
    payload: InfluencerPlatformUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> InfluencerPlatformResponse | JSONResponse:
    try:
        return InfluencerService(db).update_platform(influencer_id, platform_id, payload)
    except InfluencerServiceError as exc:
        return service_error_response(exc)


@router.delete(
    "/{influencer_id}/platforms/{platform_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def delete_platform(
    influencer_id: str,
    platform_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        InfluencerService(db).delete_platform(influencer_id, platform_id)
    except InfluencerServiceError as exc:
        return service_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{influencer_id}/contacts",
    response_model=InfluencerContactListResponse,
    responses=ERROR_RESPONSES,
)
def list_contacts(
    influencer_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> InfluencerContactListResponse | JSONResponse:
    try:
        return InfluencerService(db).list_contacts(influencer_id)
    except InfluencerServiceError as exc:
        return service_error_response(exc)


@router.post(
    "/{influencer_id}/contacts",
    status_code=status.HTTP_201_CREATED,
    response_model=InfluencerContactResponse,
    responses=ERROR_RESPONSES,
)
def create_contact(
    influencer_id: str,
    payload: InfluencerContactCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> InfluencerContactResponse | JSONResponse:
    try:
        return InfluencerService(db).create_contact(influencer_id, payload)
    except InfluencerServiceError as exc:
        return service_error_response(exc)


@router.patch(
    "/{influencer_id}/contacts/{contact_id}",
    response_model=InfluencerContactResponse,
    responses=ERROR_RESPONSES,
)
def update_contact(
    influencer_id: str,
    contact_id: str,
    payload: InfluencerContactUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> InfluencerContactResponse | JSONResponse:
    try:
        return InfluencerService(db).update_contact(influencer_id, contact_id, payload)
    except InfluencerServiceError as exc:
        return service_error_response(exc)


@router.delete(
    "/{influencer_id}/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses=ERROR_RESPONSES,
)
def delete_contact(
    influencer_id: str,
    contact_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response | JSONResponse:
    try:
        InfluencerService(db).delete_contact(influencer_id, contact_id)
    except InfluencerServiceError as exc:
        return service_error_response(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{influencer_id}/deals",
    response_model=InfluencerDealListResponse,
    responses=ERROR_RESPONSES,
)
def list_deals(
    influencer_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> InfluencerDealListResponse | JSONResponse:
    try:
        return InfluencerService(db).list_deals(influencer_id)
    except InfluencerServiceError as exc:
        return service_error_response(exc)


@router.post(
    "/manual",
    status_code=status.HTTP_201_CREATED,
    response_model=ManualInfluencerResponse,
    responses=ERROR_RESPONSES,
)
def create_manual_influencer(
    payload: ManualInfluencerInput,
    db: Annotated[Session, Depends(get_db)],
    merge_if_matched: bool = False,
) -> ManualInfluencerResponse | JSONResponse:
    try:
        influencer = InfluencerService(db).manual_create(
            payload,
            merge_if_matched=merge_if_matched,
        )
    except InfluencerServiceError as exc:
        return service_error_response(exc)
    return ManualInfluencerResponse(
        id=influencer.id,
        display_name=influencer.display_name,
        platform_count=len(influencer.platforms),
        contact_count=len(influencer.contacts),
    )
