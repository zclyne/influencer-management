from sqlalchemy.orm import Session

from app.repositories.sqlalchemy import (
    InfluencerContactRepository,
    InfluencerPlatformRepository,
    InfluencerRepository,
)
from app.schemas.influencer_ingestion import CanonicalInfluencerRow, DedupMatch


class DedupService:
    def __init__(self, db: Session) -> None:
        self.platforms = InfluencerPlatformRepository(db)
        self.contacts = InfluencerContactRepository(db)
        self.influencers = InfluencerRepository(db)

    def match(self, row: CanonicalInfluencerRow) -> DedupMatch:
        if row.parse_errors:
            return DedupMatch(status="invalid", reason="row_has_parse_errors")

        platform_match = self.platforms.find_by_normalized_profile_url(row.normalized_profile_url)
        if platform_match:
            return DedupMatch(
                status="high_confidence",
                influencer_id=platform_match.influencer_id,
                reason="profile_url",
            )

        if row.platform and row.normalized_username:
            username_match = self.platforms.find_by_platform_username(
                row.platform, row.normalized_username
            )
            if username_match:
                return DedupMatch(
                    status="high_confidence",
                    influencer_id=username_match.influencer_id,
                    reason="platform_username",
                )

        matched_influencer_ids: set[str] = set()
        for contact in row.contacts:
            matched_influencer_ids.update(
                existing.influencer_id for existing in self.contacts.find_by_email(contact.email)
            )
        if len(matched_influencer_ids) == 1:
            return DedupMatch(
                status="high_confidence",
                influencer_id=next(iter(matched_influencer_ids)),
                reason="email",
            )
        if len(matched_influencer_ids) > 1:
            return DedupMatch(status="possible", reason="email_used_by_multiple_influencers")

        if row.display_name and self.influencers.find_by_display_name(row.display_name, limit=1):
            return DedupMatch(status="possible", reason="display_name")

        return DedupMatch(status="new", reason="no_match")
