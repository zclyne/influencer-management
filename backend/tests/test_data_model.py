import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.enums import CompensationItemType
from app.repositories.sqlalchemy import (
    BrandRepository,
    CampaignBrandRepository,
    CampaignRepository,
    CompensationItemRepository,
    DealRepository,
    InfluencerPlatformRepository,
    InfluencerRepository,
)


def test_campaign_brand_and_deal_uniqueness(db_session: Session) -> None:
    brand = BrandRepository(db_session).create(name="TCL")
    campaign = CampaignRepository(db_session).create(name="Launch campaign")
    CampaignBrandRepository(db_session).create(campaign_id=campaign.id, brand_id=brand.id)
    influencer = InfluencerRepository(db_session).create(display_name="Creator")
    DealRepository(db_session).create(campaign_id=campaign.id, influencer_id=influencer.id)

    with pytest.raises(IntegrityError):
        DealRepository(db_session).create(campaign_id=campaign.id, influencer_id=influencer.id)
        db_session.flush()


def test_platform_lookup_and_nullable_compensation_amount(db_session: Session) -> None:
    influencer = InfluencerRepository(db_session).create(display_name="Creator")
    platform = InfluencerPlatformRepository(db_session).create(
        influencer_id=influencer.id,
        platform="instagram",
        username="creator",
        normalized_username="creator",
        profile_url="https://instagram.com/creator",
        normalized_profile_url="https://instagram.com/creator",
    )
    assert (
        InfluencerPlatformRepository(db_session)
        .find_by_normalized_profile_url("https://instagram.com/creator")
        .id
        == platform.id
    )

    campaign = CampaignRepository(db_session).create(name="Campaign")
    deal = DealRepository(db_session).create(campaign_id=campaign.id, influencer_id=influencer.id)
    item = CompensationItemRepository(db_session).create(
        deal_id=deal.id,
        type=CompensationItemType.PRODUCT_GIFT.value,
        description="Sample product",
        amount=None,
    )
    assert item.amount is None

