from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.domain.enums import ImportSourceType

IngestionRowStatus = Literal[
    "pending",
    "matched_existing",
    "possible_duplicate",
    "new",
    "invalid",
    "skipped",
    "imported",
]

IngestionConfirmAction = Literal["create", "merge", "skip"]
IngestionResultStatus = Literal["created", "merged", "skipped", "conflict", "invalid", "failed"]


class ContactCandidate(BaseModel):
    email: str
    source: str = "import"


class SocialLinkCandidate(BaseModel):
    platform: str
    profile_url: str
    username: str | None = None


class CanonicalInfluencerRow(BaseModel):
    source_type: str
    source_row_number: int
    raw_row_json: dict[str, Any]
    display_name: str | None = None
    full_name: str | None = None
    gender: str | None = None
    country: str | None = None
    city: str | None = None
    bio: str | None = None
    platform: str | None = None
    username: str | None = None
    normalized_username: str | None = None
    profile_url: str | None = None
    normalized_profile_url: str | None = None
    follower_count: int | None = None
    engagement_rate: Decimal | None = None
    follower_credibility: Decimal | None = None
    notable_follower_rate: Decimal | None = None
    avg_likes: int | None = None
    avg_views: int | None = None
    avg_comments: int | None = None
    avg_reels_plays: int | None = None
    total_likes: int | None = None
    total_posts_or_videos: int | None = None
    total_views: int | None = None
    raw_metrics_json: dict[str, Any] | None = None
    age_gender_json: dict[str, Any] | None = None
    top_countries_json: list[dict[str, Any]] | None = None
    top_cities_json: list[dict[str, Any]] | None = None
    top_interests_json: list[dict[str, Any]] | None = None
    contacts: list[ContactCandidate] = Field(default_factory=list)
    social_links: list[SocialLinkCandidate] = Field(default_factory=list)
    parse_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DedupMatch(BaseModel):
    status: Literal["high_confidence", "possible", "new", "invalid"]
    influencer_id: str | None = None
    reason: str | None = None


class ImportPreviewInput(BaseModel):
    source_type: ImportSourceType
    file_name: str | None = None
    content: bytes


class IngestionPreviewRow(BaseModel):
    row: CanonicalInfluencerRow
    status: IngestionRowStatus
    dedup: DedupMatch


class IngestionPreviewResponse(BaseModel):
    source_type: str
    row_count: int
    rows: list[IngestionPreviewRow]
    fatal_errors: list[str] = Field(default_factory=list)


class IngestionConfirmRow(BaseModel):
    row: CanonicalInfluencerRow
    action: IngestionConfirmAction
    existing_influencer_id: str | None = None


class IngestionConfirmRequest(BaseModel):
    source_type: ImportSourceType
    rows: list[IngestionConfirmRow] = Field(default_factory=list)
    file_name: str | None = None
    file_hash: str | None = None
    target_campaign_id: str | None = None


class IngestionRowResult(BaseModel):
    source_row_number: int
    action: IngestionConfirmAction
    status: IngestionResultStatus
    influencer_id: str | None = None
    deal_id: str | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class IngestionConfirmResponse(BaseModel):
    import_session_id: str
    row_count: int
    imported_count: int
    skipped_count: int
    conflict_count: int
    created_deals: int
    rows: list[IngestionRowResult] = Field(default_factory=list)


class ImportSessionResponse(BaseModel):
    id: str
    source_type: str
    file_name: str | None = None
    file_hash: str | None = None
    row_count: int
    imported_count: int
    skipped_count: int
    conflict_count: int
    target_campaign_id: str | None = None
    created_at: datetime
    updated_at: datetime
