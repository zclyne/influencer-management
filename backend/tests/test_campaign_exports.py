import csv
from io import StringIO

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import CompensationItemType, DealStatus
from app.repositories.sqlalchemy import (
    BrandRepository,
    CampaignBrandRepository,
    CampaignRepository,
    CompensationItemRepository,
    DealRepository,
    InfluencerContactRepository,
    InfluencerPlatformRepository,
    InfluencerRepository,
)


def test_campaign_export_with_no_deals(api_client: TestClient, db_session: Session) -> None:
    campaign = CampaignRepository(db_session).create(name="Empty Campaign")
    db_session.commit()

    response = api_client.get(f"/api/v1/campaigns/{campaign.id}/export.csv")

    assert response.status_code == 200
    rows = list(csv.reader(StringIO(response.text)))
    assert rows[0][:3] == ["campaign_name", "brand_names", "deal_status"]
    assert len(rows) == 1


def test_campaign_export_includes_deal_summaries_and_filters(
    api_client: TestClient,
    db_session: Session,
) -> None:
    campaign = CampaignRepository(db_session).create(name="Launch Élite")
    brand = BrandRepository(db_session).create(name="TCL")
    CampaignBrandRepository(db_session).create(campaign_id=campaign.id, brand_id=brand.id)
    influencer = InfluencerRepository(db_session).create(
        display_name="Créateur",
        country="France",
        city="Paris",
    )
    InfluencerPlatformRepository(db_session).create(
        influencer_id=influencer.id,
        platform="instagram",
        username="createur",
        profile_url="https://instagram.com/createur",
        follower_count=12000,
    )
    InfluencerContactRepository(db_session).create(
        influencer_id=influencer.id,
        email="creator@example.com",
        is_primary=True,
    )
    deal = DealRepository(db_session).create(
        campaign_id=campaign.id,
        influencer_id=influencer.id,
        status=DealStatus.ACTIVE.value,
        internal_notes="VIP",
    )
    CompensationItemRepository(db_session).create(
        deal_id=deal.id,
        type=CompensationItemType.CASH_STIPEND.value,
        description="Fee",
        amount=500,
        currency="USD",
    )
    db_session.commit()

    response = api_client.get(
        f"/api/v1/campaigns/{campaign.id}/export.csv",
        params={"status": DealStatus.ACTIVE.value, "platform": "instagram"},
    )

    assert response.status_code == 200
    rows = list(csv.DictReader(StringIO(response.text)))
    assert len(rows) == 1
    assert rows[0]["campaign_name"] == "Launch Élite"
    assert rows[0]["brand_names"] == "TCL"
    assert rows[0]["influencer_display_name"] == "Créateur"
    assert rows[0]["primary_contact_email"] == "creator@example.com"
    assert rows[0]["cash_total"] == "500.00"
    assert rows[0]["internal_notes"] == "VIP"


def test_campaign_export_unknown_campaign_returns_404(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/campaigns/missing/export.csv")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
