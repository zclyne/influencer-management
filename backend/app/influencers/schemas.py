from pydantic import BaseModel, Field


class ManualInfluencerInput(BaseModel):
    display_name: str
    full_name: str | None = None
    platform: str | None = None
    username: str | None = None
    profile_url: str | None = None
    follower_count: int | None = None
    country: str | None = None
    city: str | None = None
    bio: str | None = None
    emails: list[str] = Field(default_factory=list)
    notes: str | None = None
    target_campaign_id: str | None = None
