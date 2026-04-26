from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Campaign, CampaignBrand
from app.enums import CampaignStatus
from app.repositories.sqlalchemy import BrandRepository, CampaignRepository


def test_campaign_crud_and_archive(api_client: TestClient, db_session: Session) -> None:
    create_response = api_client.post(
        "/api/v1/campaigns",
        json={
            "name": "  Spring Launch  ",
            "brief": "Creator launch",
            "budget": "1200.50",
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
            "notes": "Initial notes",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Spring Launch"
    assert created["status"] == CampaignStatus.PLANNING.value
    assert created["budget"] == "1200.50"
    assert created["brands"] == []

    campaign_id = created["id"]
    patch_response = api_client.patch(
        f"/api/v1/campaigns/{campaign_id}",
        json={"status": "ACTIVE", "notes": "Updated"},
    )

    assert patch_response.status_code == 200
    patched = patch_response.json()
    assert patched["status"] == CampaignStatus.ACTIVE.value
    assert patched["notes"] == "Updated"
    assert patched["brief"] == "Creator launch"

    list_response = api_client.get("/api/v1/campaigns", params={"status": "ACTIVE"})
    assert list_response.status_code == 200
    assert [campaign["id"] for campaign in list_response.json()["campaigns"]] == [campaign_id]

    delete_response = api_client.delete(f"/api/v1/campaigns/{campaign_id}")
    assert delete_response.status_code == 204

    default_list_response = api_client.get("/api/v1/campaigns")
    assert default_list_response.status_code == 200
    assert default_list_response.json()["campaigns"] == []

    archived_list_response = api_client.get(
        "/api/v1/campaigns",
        params={"include_archived": "true"},
    )
    assert archived_list_response.status_code == 200
    archived_campaigns = archived_list_response.json()["campaigns"]
    assert len(archived_campaigns) == 1
    assert archived_campaigns[0]["id"] == campaign_id
    assert archived_campaigns[0]["archived_at"] is not None

    archived = db_session.get(Campaign, campaign_id)
    assert archived is not None
    assert archived.archived_at is not None


def test_campaign_validation_and_not_found_errors(api_client: TestClient) -> None:
    blank_response = api_client.post("/api/v1/campaigns", json={"name": "   "})
    assert blank_response.status_code == 422

    invalid_status_response = api_client.patch(
        "/api/v1/campaigns/missing",
        json={"status": "LAUNCHED"},
    )
    assert invalid_status_response.status_code == 422

    missing_response = api_client.get("/api/v1/campaigns/missing")
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == "not_found"
    assert missing_response.json()["details"] == {"campaign_id": "missing"}


def test_campaign_brand_link_lifecycle(
    api_client: TestClient,
    db_session: Session,
) -> None:
    campaign = CampaignRepository(db_session).create(name="Spring Launch")
    brand = BrandRepository(db_session).create(
        name="TCL",
        website="https://www.tcl.com",
        notes="Brand notes",
    )
    db_session.commit()

    add_response = api_client.post(
        f"/api/v1/campaigns/{campaign.id}/brands",
        json={"brand_id": brand.id, "role": "primary", "notes": "Launch owner"},
    )

    assert add_response.status_code == 201
    added = add_response.json()
    assert added["brand"]["id"] == brand.id
    assert added["brand"]["name"] == "TCL"
    assert added["role"] == "primary"
    assert added["notes"] == "Launch owner"

    duplicate_response = api_client.post(
        f"/api/v1/campaigns/{campaign.id}/brands",
        json={"brand_id": brand.id},
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["code"] == "campaign_brand_conflict"

    detail_response = api_client.get(f"/api/v1/campaigns/{campaign.id}")
    assert detail_response.status_code == 200
    brands = detail_response.json()["brands"]
    assert len(brands) == 1
    assert brands[0]["brand"]["website"] == "https://www.tcl.com"

    update_response = api_client.patch(
        f"/api/v1/campaigns/{campaign.id}/brands/{brand.id}",
        json={"notes": "Updated link notes"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["role"] == "primary"
    assert updated["notes"] == "Updated link notes"

    remove_response = api_client.delete(f"/api/v1/campaigns/{campaign.id}/brands/{brand.id}")
    assert remove_response.status_code == 204
    assert db_session.scalar(select(CampaignBrand)) is None

    unlinked_detail_response = api_client.get(f"/api/v1/campaigns/{campaign.id}")
    assert unlinked_detail_response.status_code == 200
    assert unlinked_detail_response.json()["brands"] == []


def test_campaign_brand_link_errors(api_client: TestClient, db_session: Session) -> None:
    campaign = CampaignRepository(db_session).create(name="Spring Launch")
    db_session.commit()

    missing_brand_response = api_client.post(
        f"/api/v1/campaigns/{campaign.id}/brands",
        json={"brand_id": "missing-brand"},
    )
    assert missing_brand_response.status_code == 404
    assert missing_brand_response.json()["details"] == {"brand_id": "missing-brand"}

    missing_campaign_response = api_client.post(
        "/api/v1/campaigns/missing-campaign/brands",
        json={"brand_id": "missing-brand"},
    )
    assert missing_campaign_response.status_code == 404
    assert missing_campaign_response.json()["details"] == {"campaign_id": "missing-campaign"}
