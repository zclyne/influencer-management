from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.api.schemas import ApiErrorResponse
from app.db.session import get_db
from app.enums import DealStatus
from app.schemas.campaign_exports import CampaignExportFilters
from app.services.campaign_exports import CampaignExportService, ExportServiceError

router = APIRouter(tags=["campaign exports"])


def _http_error_response(error: ExportServiceError) -> JSONResponse:
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
    "/campaigns/{campaign_id}/export.csv",
    response_model=None,
    responses=ERROR_RESPONSES,
)
def export_campaign_csv(
    campaign_id: str,
    db: Annotated[Session, Depends(get_db)],
    status: DealStatus | None = None,
    platform: str | None = None,
    lost_reason: str | None = None,
    include_archived: bool = False,
) -> Response | JSONResponse:
    try:
        csv_body = CampaignExportService(db).export_campaign_csv(
            campaign_id,
            CampaignExportFilters(
                status=status,
                platform=platform,
                lost_reason=lost_reason,
                include_archived=include_archived,
            ),
        )
    except ExportServiceError as exc:
        return _http_error_response(exc)
    return Response(
        content=csv_body.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="campaign-{campaign_id}.csv"'},
    )
