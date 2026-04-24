from sqlalchemy.orm import Session

from app.db import models
from app.domain.enums import DealStatus
from app.repositories.sqlalchemy import DealRepository


class DealService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.deals = DealRepository(db)

    def create_if_missing(self, campaign_id: str, influencer_id: str) -> tuple[models.Deal, bool]:
        existing = self.deals.get_by_campaign_influencer(campaign_id, influencer_id)
        if existing:
            return existing, False
        return (
            self.deals.create(
                campaign_id=campaign_id,
                influencer_id=influencer_id,
                status=DealStatus.DRAFT.value,
            ),
            True,
        )

    def exists(self, campaign_id: str, influencer_id: str) -> bool:
        return self.deals.get_by_campaign_influencer(campaign_id, influencer_id) is not None
