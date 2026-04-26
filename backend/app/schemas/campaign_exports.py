from pydantic import BaseModel, Field

from app.enums import DealStatus


class CampaignExportFilters(BaseModel):
    status: DealStatus | None = None
    platform: str | None = None
    lost_reason: str | None = None
    include_archived: bool = False
    deal_ids: list[str] = Field(default_factory=list)
