from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import DeliverableStatus
from app.repositories.sqlalchemy import (
    CampaignRepository,
    DealRepository,
    DeliverableRepository,
    InfluencerRepository,
)


def _seed_deal(db_session: Session) -> str:
    campaign = CampaignRepository(db_session).create(name="Spring Launch")
    influencer = InfluencerRepository(db_session).create(display_name="Creator One")
    deal = DealRepository(db_session).create(
        campaign_id=campaign.id,
        influencer_id=influencer.id,
    )
    db_session.commit()
    return deal.id


def test_deliverable_lifecycle_and_deal_summary(
    api_client: TestClient,
    db_session: Session,
) -> None:
    deal_id = _seed_deal(db_session)

    create_response = api_client.post(
        f"/api/v1/deals/{deal_id}/deliverables",
        json={"type": "video", "quantity": 2, "due_date": "2026-05-10"},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["type"] == "video"
    assert created["quantity"] == 2
    assert created["status"] == DeliverableStatus.TODO.value

    list_response = api_client.get(f"/api/v1/deals/{deal_id}/deliverables")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["deliverables"]] == [created["id"]]

    update_response = api_client.patch(
        f"/api/v1/deals/{deal_id}/deliverables/{created['id']}",
        json={
            "status": "POSTED",
            "published_url": "https://example.com/post",
            "notes": "Live",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == DeliverableStatus.POSTED.value
    assert updated["published_url"] == "https://example.com/post"

    detail_response = api_client.get(f"/api/v1/deals/{deal_id}")
    assert detail_response.status_code == 200
    summary = detail_response.json()["deliverables"]
    assert summary["total_count"] == 1
    assert summary["completed_count"] == 1
    assert summary["published_url_count"] == 1
    assert summary["label"] == "2 videos, 1 posted"

    delete_response = api_client.delete(
        f"/api/v1/deals/{deal_id}/deliverables/{created['id']}"
    )
    assert delete_response.status_code == 204
    assert DeliverableRepository(db_session).get(created["id"]) is None


def test_deliverable_validation_and_wrong_deal_errors(
    api_client: TestClient,
    db_session: Session,
) -> None:
    deal_id = _seed_deal(db_session)
    other_deal_id = _seed_deal(db_session)
    deliverable = DeliverableRepository(db_session).create(
        deal_id=deal_id,
        type="story",
        quantity=1,
    )
    db_session.commit()

    invalid_quantity_response = api_client.post(
        f"/api/v1/deals/{deal_id}/deliverables",
        json={"type": "video", "quantity": 0},
    )
    assert invalid_quantity_response.status_code == 422

    missing_deal_response = api_client.post(
        "/api/v1/deals/missing-deal/deliverables",
        json={"type": "video"},
    )
    assert missing_deal_response.status_code == 404
    assert missing_deal_response.json()["details"] == {"deal_id": "missing-deal"}

    wrong_deal_response = api_client.patch(
        f"/api/v1/deals/{other_deal_id}/deliverables/{deliverable.id}",
        json={"status": "COMPLETED"},
    )
    assert wrong_deal_response.status_code == 404
    assert wrong_deal_response.json()["details"] == {
        "deal_id": other_deal_id,
        "deliverable_id": deliverable.id,
    }


def test_archived_deal_rejects_deliverable_mutation(
    api_client: TestClient,
    db_session: Session,
) -> None:
    deal_id = _seed_deal(db_session)
    api_client.delete(f"/api/v1/deals/{deal_id}")

    create_response = api_client.post(
        f"/api/v1/deals/{deal_id}/deliverables",
        json={"type": "video"},
    )
    assert create_response.status_code == 409
    assert create_response.json()["code"] == "archived_deal"
