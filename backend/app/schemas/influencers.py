from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.enums import ContactRole


class ManualInfluencerPlatformInput(BaseModel):
    platform: str = Field(min_length=1, max_length=64)
    username: str = Field(min_length=1, max_length=255)
    follower_count: int | None = None

    @model_validator(mode="after")
    def validate_platform_username(self) -> "ManualInfluencerPlatformInput":
        self.platform = self.platform.strip()
        self.username = self.username.strip()
        if not self.platform:
            raise ValueError("Platform cannot be blank.")
        if not self.username:
            raise ValueError("Platform username cannot be blank.")
        return self


class ManualInfluencerInput(BaseModel):
    display_name: str
    full_name: str | None = None
    platforms: list[ManualInfluencerPlatformInput] = Field(default_factory=list)
    country: str | None = None
    city: str | None = None
    bio: str | None = None
    emails: list[str] = Field(default_factory=list)
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    target_campaign_id: str | None = None

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Influencer display name cannot be blank.")
        return stripped


class InfluencerPlatformCreateRequest(BaseModel):
    platform: str = Field(min_length=1, max_length=64)
    username: str | None = Field(default=None, max_length=255)
    profile_url: str | None = Field(default=None, max_length=1024)
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
    bio: str | None = None


class InfluencerPlatformUpdateRequest(BaseModel):
    platform: str | None = Field(default=None, min_length=1, max_length=64)
    username: str | None = Field(default=None, max_length=255)
    profile_url: str | None = Field(default=None, max_length=1024)
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
    bio: str | None = None


class InfluencerContactCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: str | None = Field(default=None, max_length=255)
    role: ContactRole = ContactRole.UNKNOWN
    is_primary: bool = False
    source: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class InfluencerContactUpdateRequest(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=320)
    name: str | None = Field(default=None, max_length=255)
    role: ContactRole | None = None
    is_primary: bool | None = None
    source: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class InfluencerCreateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=64)
    country: str | None = Field(default=None, max_length=128)
    city: str | None = Field(default=None, max_length=128)
    bio: str | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    platforms: list[InfluencerPlatformCreateRequest] = Field(default_factory=list)
    contacts: list[InfluencerContactCreateRequest] = Field(default_factory=list)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Influencer display name cannot be blank.")
        return stripped


class InfluencerUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=64)
    country: str | None = Field(default=None, max_length=128)
    city: str | None = Field(default=None, max_length=128)
    bio: str | None = None
    notes: str | None = None
    tags: list[str] | None = None

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Influencer display name cannot be blank.")
        return stripped


class InfluencerPlatformResponse(BaseModel):
    id: str
    influencer_id: str
    platform: str
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
    bio: str | None = None
    created_at: datetime
    updated_at: datetime


class InfluencerPlatformSummary(BaseModel):
    id: str
    platform: str
    username: str | None = None
    profile_url: str | None = None
    follower_count: int | None = None
    engagement_rate: Decimal | None = None
    is_primary: bool = False


class InfluencerContactResponse(BaseModel):
    id: str
    influencer_id: str
    name: str | None = None
    email: str
    role: ContactRole
    is_primary: bool
    source: str | None = None
    notes: str | None = None
    conflict_influencer_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class InfluencerDealSummary(BaseModel):
    id: str
    campaign_id: str
    campaign_name: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None


class InfluencerListItem(BaseModel):
    id: str
    display_name: str
    full_name: str | None = None
    country: str | None = None
    city: str | None = None
    primary_platform: InfluencerPlatformResponse | None = None
    platforms: list[InfluencerPlatformSummary] = Field(default_factory=list)
    follower_count: int | None = None
    primary_contact: InfluencerContactResponse | None = None
    recent_deal_count: int
    tags: list[str] = Field(default_factory=list)
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class InfluencerResponse(BaseModel):
    id: str
    display_name: str
    full_name: str | None = None
    gender: str | None = None
    country: str | None = None
    city: str | None = None
    bio: str | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    platforms: list[InfluencerPlatformResponse] = Field(default_factory=list)
    contacts: list[InfluencerContactResponse] = Field(default_factory=list)
    deals: list[InfluencerDealSummary] = Field(default_factory=list)


class InfluencerListResponse(BaseModel):
    influencers: list[InfluencerListItem]


class InfluencerPlatformListResponse(BaseModel):
    platforms: list[InfluencerPlatformResponse]


class InfluencerContactListResponse(BaseModel):
    contacts: list[InfluencerContactResponse]


class InfluencerDealListResponse(BaseModel):
    deals: list[InfluencerDealSummary]


class ManualInfluencerResponse(BaseModel):
    id: str
    display_name: str
    platform_count: int
    contact_count: int
