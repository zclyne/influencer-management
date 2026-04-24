from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.enums import DealStatus
from app.repositories.sqlalchemy import (
    CampaignRepository,
    DealRepository,
    InfluencerContactRepository,
    InfluencerPlatformRepository,
    InfluencerRepository,
)


def _seed_campaign_and_influencer(db_session: Session) -> tuple[str, str]:
    campaign = CampaignRepository(db_session).create(name="Spring Launch")
    influencer = InfluencerRepository(db_session).create(
        display_name="Creator One",
        country="US",
        city="New York",
    )
    InfluencerPlatformRepository(db_session).create(
        influencer_id=influencer.id,
        platform="instagram",
        username="creatorone",
        normalized_username="creatorone",
        follower_count=125000,
    )
    InfluencerContactRepository(db_session).create(
        influencer_id=influencer.id,
        email="creator@example.com",
        role="manager",
        is_primary=True,
    )
    db_session.commit()
    return campaign.id, influencer.id


def test_create_duplicate_list_update_and_archive_deal(
    api_client: TestClient,
    db_session: Session,
) -> None:
    campaign_id, influencer_id = _seed_campaign_and_influencer(db_session)

    create_response = api_client.post(
        f"/api/v1/campaigns/{campaign_id}/deals",
        json={
            "influencer_id": influencer_id,
            "status": "APPROVED",
            "labels": ["priority", "priority", "  paid  "],
            "internal_notes": "Good fit",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == DealStatus.APPROVED.value
    assert created["labels"] == ["priority", "paid"]
    assert created["influencer"]["display_name"] == "Creator One"
    assert created["primary_platform"]["follower_count"] == 125000
    assert created["primary_contact"]["email"] == "creator@example.com"

    duplicate_response = api_client.post(
        f"/api/v1/campaigns/{campaign_id}/deals",
        json={"influencer_id": influencer_id},
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["code"] == "deal_conflict"

    list_response = api_client.get(
        f"/api/v1/campaigns/{campaign_id}/deals",
        params={"status": "APPROVED", "platform": "instagram"},
    )
    assert list_response.status_code == 200
    rows = list_response.json()["deals"]
    assert [row["id"] for row in rows] == [created["id"]]

    update_response = api_client.patch(
        f"/api/v1/deals/{created['id']}",
        json={"status": "LOST", "lost_reason": "Budget", "labels": ["later"]},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == DealStatus.LOST.value
    assert updated["lost_reason"] == "Budget"
    assert updated["labels"] == ["later"]

    delete_response = api_client.delete(f"/api/v1/deals/{created['id']}")
    assert delete_response.status_code == 204
    assert DealRepository(db_session).get(created["id"]).archived_at is not None

    default_list_response = api_client.get(f"/api/v1/campaigns/{campaign_id}/deals")
    assert default_list_response.status_code == 200
    assert default_list_response.json()["deals"] == []

    archived_list_response = api_client.get(
        f"/api/v1/campaigns/{campaign_id}/deals",
        params={"include_archived": "true"},
    )
    assert archived_list_response.status_code == 200
    assert archived_list_response.json()["deals"][0]["archived_at"] is not None


def test_bulk_create_and_bulk_update_deals(
    api_client: TestClient,
    db_session: Session,
) -> None:
    campaign = CampaignRepository(db_session).create(name="Spring Launch")
    first = InfluencerRepository(db_session).create(display_name="Creator One")
    second = InfluencerRepository(db_session).create(display_name="Creator Two")
    existing = DealRepository(db_session).create(
        campaign_id=campaign.id,
        influencer_id=first.id,
    )
    db_session.commit()

    bulk_create_response = api_client.post(
        f"/api/v1/campaigns/{campaign.id}/deals/bulk",
        json={"influencer_ids": [first.id, second.id, "missing"]},
    )

    assert bulk_create_response.status_code == 200
    created = bulk_create_response.json()
    assert created["created_count"] == 1
    assert created["skipped_count"] == 1
    assert created["error_count"] == 1
    rows_by_influencer = {row["influencer_id"]: row for row in created["rows"]}
    assert rows_by_influencer[first.id]["status"] == "skipped"
    assert rows_by_influencer[second.id]["status"] == "created"
    assert rows_by_influencer["missing"]["status"] == "error"

    new_deal_id = rows_by_influencer[second.id]["deal_id"]
    bulk_update_response = api_client.patch(
        f"/api/v1/campaigns/{campaign.id}/deals/bulk",
        json={
            "deal_ids": [existing.id, new_deal_id, "missing-deal"],
            "status": "OUTREACHED",
            "labels": ["ready"],
            "label_mode": "add",
            "internal_notes": "Sent first email",
            "notes_mode": "append",
        },
    )

    assert bulk_update_response.status_code == 200
    updated = bulk_update_response.json()
    assert updated["updated_count"] == 2
    assert updated["error_count"] == 1
    refreshed = DealRepository(db_session).get(existing.id)
    assert refreshed.status == DealStatus.OUTREACHED.value
    assert refreshed.labels_json == ["ready"]
    assert refreshed.internal_notes == "Sent first email"


def test_deal_error_paths(api_client: TestClient, db_session: Session) -> None:
    campaign = CampaignRepository(db_session).create(name="Spring Launch")
    db_session.commit()

    missing_campaign_response = api_client.post(
        "/api/v1/campaigns/missing/deals",
        json={"influencer_id": "missing"},
    )
    assert missing_campaign_response.status_code == 404
    assert missing_campaign_response.json()["details"] == {"campaign_id": "missing"}

    missing_influencer_response = api_client.post(
        f"/api/v1/campaigns/{campaign.id}/deals",
        json={"influencer_id": "missing"},
    )
    assert missing_influencer_response.status_code == 404
    assert missing_influencer_response.json()["details"] == {"influencer_id": "missing"}

    missing_deal_response = api_client.get("/api/v1/deals/missing")
    assert missing_deal_response.status_code == 404
    assert missing_deal_response.json()["details"] == {"deal_id": "missing"}
