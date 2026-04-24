from dataclasses import dataclass, field
from datetime import UTC
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.db import models
from app.db.models import utc_now
from app.influencers.ingestion.normalization import normalize_profile_url, normalize_username
from app.influencers.ingestion.schemas import CanonicalInfluencerRow, ContactCandidate
from app.repositories.sqlalchemy import (
    InfluencerAudienceSnapshotRepository,
    InfluencerContactRepository,
    InfluencerPlatformRepository,
    InfluencerRepository,
)

BulkWriteAction = Literal["create", "merge"]
BulkWriteStatus = Literal["created", "merged", "failed"]


@dataclass
class BulkInfluencerWriteCommand:
    row: CanonicalInfluencerRow
    action: BulkWriteAction
    existing_influencer_id: str | None = None


@dataclass
class BulkInfluencerWriteRowResult:
    source_row_number: int
    action: BulkWriteAction
    status: BulkWriteStatus
    influencer_id: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class BulkInfluencerWriteResult:
    rows: list[BulkInfluencerWriteRowResult] = field(default_factory=list)


class InfluencerBulkWriter:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.influencers = InfluencerRepository(db)
        self.platforms = InfluencerPlatformRepository(db)
        self.contacts = InfluencerContactRepository(db)
        self.snapshots = InfluencerAudienceSnapshotRepository(db)

    def write(self, commands: list[BulkInfluencerWriteCommand]) -> BulkInfluencerWriteResult:
        results = []
        for command in commands:
            try:
                influencer = self._write_one(command)
            except ValueError as exc:
                results.append(
                    BulkInfluencerWriteRowResult(
                        source_row_number=command.row.source_row_number,
                        action=command.action,
                        status="failed",
                        errors=[str(exc)],
                    )
                )
                continue
            results.append(
                BulkInfluencerWriteRowResult(
                    source_row_number=command.row.source_row_number,
                    action=command.action,
                    status="created" if command.action == "create" else "merged",
                    influencer_id=influencer.id,
                    warnings=list(command.row.warnings),
                )
            )
        self.db.flush()
        return BulkInfluencerWriteResult(rows=results)

    def _write_one(self, command: BulkInfluencerWriteCommand) -> models.Influencer:
        if command.action == "merge":
            if not command.existing_influencer_id:
                raise ValueError("Merge action requires existing_influencer_id.")
            influencer = self.influencers.get(command.existing_influencer_id)
            if not influencer:
                raise ValueError("Existing influencer not found.")
            self._merge_influencer(influencer, command.row)
        else:
            influencer = self._create_influencer(command.row)
        primary_platform = self._create_or_update_platform(influencer.id, command.row)
        self._add_social_platforms(influencer.id, command.row)
        self._add_audience_snapshot(primary_platform, command.row)
        self._add_contacts(influencer.id, command.row.contacts)
        return influencer

    def _create_influencer(self, row: CanonicalInfluencerRow) -> models.Influencer:
        return self.influencers.create(
            display_name=row.display_name or row.username or "Unknown creator",
            full_name=row.full_name,
            gender=row.gender,
            country=row.country,
            city=row.city,
            bio=row.bio,
            notes=None,
        )

    def _merge_influencer(
        self, influencer: models.Influencer, row: CanonicalInfluencerRow
    ) -> None:
        updates = {
            "full_name": row.full_name,
            "gender": row.gender,
            "country": row.country,
            "city": row.city,
            "bio": row.bio,
        }
        for key, value in updates.items():
            if value and not getattr(influencer, key):
                setattr(influencer, key, value)
        self.db.flush()

    def _add_social_platforms(
        self, influencer_id: str, row: CanonicalInfluencerRow
    ) -> list[models.InfluencerPlatform]:
        platforms = []
        for link in row.social_links:
            if link.profile_url == row.normalized_profile_url:
                continue
            platform = self._create_or_update_platform(
                influencer_id,
                CanonicalInfluencerRow(
                    source_type=row.source_type,
                    source_row_number=row.source_row_number,
                    raw_row_json=row.raw_row_json,
                    display_name=row.display_name,
                    platform=link.platform,
                    username=link.username,
                    normalized_username=normalize_username(link.platform, link.username),
                    profile_url=link.profile_url,
                    normalized_profile_url=normalize_profile_url(link.profile_url),
                ),
            )
            if platform:
                platforms.append(platform)
        return platforms

    def _add_audience_snapshot(
        self, platform: models.InfluencerPlatform | None, row: CanonicalInfluencerRow
    ) -> None:
        if platform and (
            row.age_gender_json
            or row.top_countries_json
            or row.top_cities_json
            or row.top_interests_json
        ):
            self.snapshots.create(
                influencer_platform_id=platform.id,
                source=row.source_type,
                age_gender_json=self._json_safe(row.age_gender_json),
                top_countries_json=self._json_safe(row.top_countries_json),
                top_cities_json=self._json_safe(row.top_cities_json),
                top_interests_json=self._json_safe(row.top_interests_json),
                captured_at=utc_now().astimezone(UTC),
            )

    def _add_contacts(
        self, influencer_id: str, contacts: list[ContactCandidate]
    ) -> list[models.InfluencerContact]:
        created_contacts = []
        for contact in contacts:
            if not self.contacts.find_for_influencer(influencer_id, contact.email):
                created_contacts.append(
                    self.contacts.create(
                        influencer_id=influencer_id,
                        email=contact.email,
                        source=contact.source,
                        is_primary=False,
                    )
                )
        self.db.flush()
        return created_contacts

    def _create_or_update_platform(
        self, influencer_id: str, row: CanonicalInfluencerRow
    ) -> models.InfluencerPlatform | None:
        if not row.platform and not row.normalized_profile_url:
            return None
        platform = row.platform or "unknown"
        existing = self.platforms.find_for_influencer(
            influencer_id,
            platform,
            row.normalized_profile_url,
            row.normalized_username,
        )
        values = {
            "username": row.username,
            "normalized_username": row.normalized_username,
            "profile_url": row.profile_url or row.normalized_profile_url,
            "normalized_profile_url": row.normalized_profile_url,
            "follower_count": row.follower_count,
            "engagement_rate": row.engagement_rate,
            "follower_credibility": row.follower_credibility,
            "notable_follower_rate": row.notable_follower_rate,
            "avg_likes": row.avg_likes,
            "avg_views": row.avg_views,
            "avg_comments": row.avg_comments,
            "avg_reels_plays": row.avg_reels_plays,
            "total_likes": row.total_likes,
            "total_posts_or_videos": row.total_posts_or_videos,
            "total_views": row.total_views,
            "bio": row.bio,
            "raw_metrics_json": self._json_safe(row.raw_metrics_json),
            "last_imported_at": utc_now().astimezone(UTC),
        }
        if existing:
            for key, value in values.items():
                if value is not None and not getattr(existing, key):
                    setattr(existing, key, value)
            self.db.flush()
            return existing
        return self.platforms.create(influencer_id=influencer_id, platform=platform, **values)

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, list):
            return [self._json_safe(item) for item in value]
        if isinstance(value, dict):
            return {key: self._json_safe(item) for key, item in value.items()}
        return value
