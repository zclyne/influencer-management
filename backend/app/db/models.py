import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON as SAJSON
from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.domain.enums import (
    CampaignStatus,
    CompensationItemStatus,
    CompensationItemType,
    ContactRole,
    DealStatus,
    DeliverableStatus,
    EmailLinkType,
)


def uuid_str() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class ArchiveMixin:
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Brand(TimestampMixin, ArchiveMixin, Base):
    __tablename__ = "brands"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    campaign_links: Mapped[list["CampaignBrand"]] = relationship(
        back_populates="brand", cascade="all, delete-orphan"
    )


class Campaign(TimestampMixin, ArchiveMixin, Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=CampaignStatus.PLANNING.value)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    brand_links: Mapped[list["CampaignBrand"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    deals: Mapped[list["Deal"]] = relationship(back_populates="campaign")


class CampaignBrand(TimestampMixin, Base):
    __tablename__ = "campaign_brands"
    __table_args__ = (UniqueConstraint("campaign_id", "brand_id", name="uq_campaign_brand"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), nullable=False)
    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    campaign: Mapped[Campaign] = relationship(back_populates="brand_links")
    brand: Mapped[Brand] = relationship(back_populates="campaign_links")


class Influencer(TimestampMixin, ArchiveMixin, Base):
    __tablename__ = "influencers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    platforms: Mapped[list["InfluencerPlatform"]] = relationship(
        back_populates="influencer", cascade="all, delete-orphan"
    )
    contacts: Mapped[list["InfluencerContact"]] = relationship(
        back_populates="influencer", cascade="all, delete-orphan"
    )
    deals: Mapped[list["Deal"]] = relationship(back_populates="influencer")


class InfluencerPlatform(TimestampMixin, Base):
    __tablename__ = "influencer_platforms"
    __table_args__ = (
        UniqueConstraint("platform", "normalized_profile_url", name="uq_platform_profile_url"),
        Index("ix_influencer_platform_influencer_id", "influencer_id"),
        Index("ix_influencer_platform_username", "platform", "normalized_username"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    influencer_id: Mapped[str] = mapped_column(ForeignKey("influencers.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    normalized_profile_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    follower_count: Mapped[int | None] = mapped_column(nullable=True)
    engagement_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), nullable=True)
    follower_credibility: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), nullable=True)
    notable_follower_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), nullable=True)
    avg_likes: Mapped[int | None] = mapped_column(nullable=True)
    avg_views: Mapped[int | None] = mapped_column(nullable=True)
    avg_comments: Mapped[int | None] = mapped_column(nullable=True)
    avg_reels_plays: Mapped[int | None] = mapped_column(nullable=True)
    total_likes: Mapped[int | None] = mapped_column(nullable=True)
    total_posts_or_videos: Mapped[int | None] = mapped_column(nullable=True)
    total_views: Mapped[int | None] = mapped_column(nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_metrics_json: Mapped[dict[str, Any] | None] = mapped_column(SAJSON, nullable=True)
    last_imported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    influencer: Mapped[Influencer] = relationship(back_populates="platforms")
    audience_snapshots: Mapped[list["InfluencerAudienceSnapshot"]] = relationship(
        back_populates="platform", cascade="all, delete-orphan"
    )


class InfluencerAudienceSnapshot(Base):
    __tablename__ = "influencer_audience_snapshots"
    __table_args__ = (Index("ix_audience_snapshot_platform_id", "influencer_platform_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    influencer_platform_id: Mapped[str] = mapped_column(
        ForeignKey("influencer_platforms.id"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    age_gender_json: Mapped[dict[str, Any] | None] = mapped_column(SAJSON, nullable=True)
    top_countries_json: Mapped[list[dict[str, Any]] | None] = mapped_column(SAJSON, nullable=True)
    top_cities_json: Mapped[list[dict[str, Any]] | None] = mapped_column(SAJSON, nullable=True)
    top_interests_json: Mapped[list[dict[str, Any]] | None] = mapped_column(SAJSON, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    platform: Mapped[InfluencerPlatform] = relationship(back_populates="audience_snapshots")


class InfluencerContact(TimestampMixin, Base):
    __tablename__ = "influencer_contacts"
    __table_args__ = (
        Index("ix_influencer_contact_email", "email"),
        Index("ix_influencer_contact_influencer_id", "influencer_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    influencer_id: Mapped[str] = mapped_column(ForeignKey("influencers.id"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default=ContactRole.UNKNOWN.value)
    is_primary: Mapped[bool] = mapped_column(default=False)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    influencer: Mapped[Influencer] = relationship(back_populates="contacts")


class Deal(TimestampMixin, ArchiveMixin, Base):
    __tablename__ = "deals"
    __table_args__ = (
        UniqueConstraint("campaign_id", "influencer_id", name="uq_campaign_influencer_deal"),
        Index("ix_deal_campaign_status", "campaign_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), nullable=False)
    influencer_id: Mapped[str] = mapped_column(ForeignKey("influencers.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=DealStatus.DRAFT.value)
    lost_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    labels_json: Mapped[list[str] | None] = mapped_column(SAJSON, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_list_status: Mapped[str | None] = mapped_column(String(128), nullable=True)

    campaign: Mapped[Campaign] = relationship(back_populates="deals")
    influencer: Mapped[Influencer] = relationship(back_populates="deals")
    deliverables: Mapped[list["Deliverable"]] = relationship(
        back_populates="deal", cascade="all, delete-orphan"
    )
    compensation_items: Mapped[list["CompensationItem"]] = relationship(
        back_populates="deal", cascade="all, delete-orphan"
    )
    email_thread_links: Mapped[list["EmailThreadLink"]] = relationship(back_populates="deal")


class Deliverable(TimestampMixin, Base):
    __tablename__ = "deliverables"
    __table_args__ = (Index("ix_deliverable_deal_id", "deal_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    deal_id: Mapped[str] = mapped_column(ForeignKey("deals.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(default=1)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=DeliverableStatus.TODO.value)
    published_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    deal: Mapped[Deal] = relationship(back_populates="deliverables")


class CompensationItem(TimestampMixin, Base):
    __tablename__ = "compensation_items"
    __table_args__ = (Index("ix_compensation_item_deal_id", "deal_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    deal_id: Mapped[str] = mapped_column(ForeignKey("deals.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(64), default=CompensationItemType.OTHER.value)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    recipient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=CompensationItemStatus.PLANNED.value)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    receipt_file_id: Mapped[str | None] = mapped_column(
        ForeignKey("stored_files.id"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    deal: Mapped[Deal] = relationship(back_populates="compensation_items")
    receipt_file: Mapped["StoredFile | None"] = relationship()


class EmailThreadLink(TimestampMixin, Base):
    __tablename__ = "email_thread_links"
    __table_args__ = (
        Index("ix_email_thread_external_thread", "provider", "external_thread_id"),
        Index("ix_email_thread_deal_id", "deal_id"),
        Index("ix_email_thread_contact_id", "contact_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    external_thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    influencer_id: Mapped[str | None] = mapped_column(ForeignKey("influencers.id"), nullable=True)
    campaign_id: Mapped[str | None] = mapped_column(ForeignKey("campaigns.id"), nullable=True)
    deal_id: Mapped[str | None] = mapped_column(ForeignKey("deals.id"), nullable=True)
    contact_id: Mapped[str | None] = mapped_column(
        ForeignKey("influencer_contacts.id"), nullable=True
    )
    link_type: Mapped[str] = mapped_column(String(64), default=EmailLinkType.MANUAL.value)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    linked_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    deal: Mapped[Deal | None] = relationship(back_populates="email_thread_links")


class ImportSession(TimestampMixin, Base):
    __tablename__ = "import_sessions"
    __table_args__ = (Index("ix_import_session_source", "source_type", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    row_count: Mapped[int] = mapped_column(default=0)
    imported_count: Mapped[int] = mapped_column(default=0)
    skipped_count: Mapped[int] = mapped_column(default=0)
    conflict_count: Mapped[int] = mapped_column(default=0)
    target_campaign_id: Mapped[str | None] = mapped_column(
        ForeignKey("campaigns.id"), nullable=True
    )


class StoredFile(TimestampMixin, Base):
    __tablename__ = "stored_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
