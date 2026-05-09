from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import CompensationItemStatus, CompensationItemType
from app.repositories.sqlalchemy import (
    CampaignRepository,
    CompensationItemRepository,
    DealRepository,
    InfluencerRepository,
)


def _seed_deal(db_session: Session, *, campaign_name: str = "Spring Launch") -> str:
    campaign = CampaignRepository(db_session).create(name=campaign_name)
    influencer = InfluencerRepository(db_session).create(display_name="Creator One")
    deal = DealRepository(db_session).create(
        campaign_id=campaign.id,
        influencer_id=influencer.id,
    )
    db_session.commit()
    return deal.id


def test_compensation_item_lifecycle_and_summary(
    api_client: TestClient,
    db_session: Session,
) -> None:
    deal_id = _seed_deal(db_session)

    cash_response = api_client.post(
        f"/api/v1/deals/{deal_id}/compensation-items",
        json={
            "type": "CASH_STIPEND",
            "description": "Creator fee",
            "amount": "1000.00",
            "status": "PROMISED",
        },
    )
    assert cash_response.status_code == 201
    cash = cash_response.json()
    assert cash["currency"] == "USD"
    assert cash["amount"] == "1000.00"

    gift_response = api_client.post(
        f"/api/v1/deals/{deal_id}/compensation-items",
        json={
            "type": "PRODUCT_GIFT",
            "description": "Product gift",
        },
    )
    assert gift_response.status_code == 201
    gift = gift_response.json()
    assert gift["amount"] is None

    list_response = api_client.get(f"/api/v1/deals/{deal_id}/compensation-items")
    assert list_response.status_code == 200
    assert len(list_response.json()["compensation_items"]) == 2

    complete_response = api_client.patch(
        f"/api/v1/deals/{deal_id}/compensation-items/{cash['id']}",
        json={"status": "COMPLETED"},
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["completed_at"] is not None

    CompensationItemRepository(db_session).create(
        deal_id=deal_id,
        type=CompensationItemType.FLIGHT_REIMBURSEMENT.value,
        amount=Decimal("200.00"),
        currency="USD",
        status=CompensationItemStatus.CANCELLED.value,
    )
    db_session.commit()

    detail_response = api_client.get(f"/api/v1/deals/{deal_id}")
    assert detail_response.status_code == 200
    summary = detail_response.json()["compensation"]
    assert summary["active_item_count"] == 2
    assert summary["completed_item_count"] == 1
    assert summary["cash_totals"] == {"USD": "1000.00"}
    assert summary["reimbursement_totals"] == {}
    assert summary["non_cash_descriptions"] == ["Product gift"]
    assert summary["label"] == "$1,000 cash + Product gift"

    delete_response = api_client.delete(
        f"/api/v1/deals/{deal_id}/compensation-items/{gift['id']}"
    )
    assert delete_response.status_code == 204
    assert CompensationItemRepository(db_session).get(gift["id"]) is None


def test_compensation_validation_and_wrong_deal_errors(
    api_client: TestClient,
    db_session: Session,
) -> None:
    deal_id = _seed_deal(db_session)
    other_deal_id = _seed_deal(db_session, campaign_name="Summer Launch")
    item = CompensationItemRepository(db_session).create(
        deal_id=deal_id,
        type=CompensationItemType.PRODUCT_GIFT.value,
        description="Gift",
    )
    db_session.commit()

    negative_response = api_client.post(
        f"/api/v1/deals/{deal_id}/compensation-items",
        json={"amount": "-1.00"},
    )
    assert negative_response.status_code == 422

    missing_deal_response = api_client.post(
        "/api/v1/deals/missing/compensation-items",
        json={"description": "Gift"},
    )
    assert missing_deal_response.status_code == 404
    assert missing_deal_response.json()["details"] == {"deal_id": "missing"}

    wrong_deal_response = api_client.patch(
        f"/api/v1/deals/{other_deal_id}/compensation-items/{item.id}",
        json={"status": "COMPLETED"},
    )
    assert wrong_deal_response.status_code == 404
    assert wrong_deal_response.json()["details"] == {
        "deal_id": other_deal_id,
        "item_id": item.id,
    }


def test_archived_deal_rejects_compensation_mutation(
    api_client: TestClient,
    db_session: Session,
) -> None:
    deal_id = _seed_deal(db_session)
    api_client.delete(f"/api/v1/deals/{deal_id}")

    create_response = api_client.post(
        f"/api/v1/deals/{deal_id}/compensation-items",
        json={"description": "Gift"},
    )
    assert create_response.status_code == 409
    assert create_response.json()["code"] == "archived_deal"
