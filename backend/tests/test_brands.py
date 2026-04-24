from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Brand
from app.repositories.sqlalchemy import CampaignRepository


def test_brand_crud_search_and_archive(api_client: TestClient, db_session: Session) -> None:
    create_response = api_client.post(
        "/api/v1/brands",
        json={
            "name": "  TCL  ",
            "website": "https://www.tcl.com",
            "notes": "Brand notes",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "TCL"
    assert created["website"] == "https://www.tcl.com"
    assert created["campaign_count"] is None

    brand_id = created["id"]
    patch_response = api_client.patch(
        f"/api/v1/brands/{brand_id}",
        json={"notes": "Updated notes"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["notes"] == "Updated notes"

    search_response = api_client.get("/api/v1/brands", params={"query": "tc"})
    assert search_response.status_code == 200
    assert [brand["id"] for brand in search_response.json()["brands"]] == [brand_id]

    delete_response = api_client.delete(f"/api/v1/brands/{brand_id}")
    assert delete_response.status_code == 204

    default_list_response = api_client.get("/api/v1/brands")
    assert default_list_response.status_code == 200
    assert default_list_response.json()["brands"] == []

    archived_list_response = api_client.get(
        "/api/v1/brands",
        params={"include_archived": "true"},
    )
    assert archived_list_response.status_code == 200
    archived = archived_list_response.json()["brands"][0]
    assert archived["id"] == brand_id
    assert archived["archived_at"] is not None

    archived_brand = db_session.get(Brand, brand_id)
    assert archived_brand is not None
    assert archived_brand.archived_at is not None


def test_brand_errors_and_campaign_link(api_client: TestClient, db_session: Session) -> None:
    first_response = api_client.post("/api/v1/brands", json={"name": "TCL"})
    assert first_response.status_code == 201

    duplicate_response = api_client.post("/api/v1/brands", json={"name": " tcl "})
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["code"] == "brand_conflict"

    missing_response = api_client.get("/api/v1/brands/missing")
    assert missing_response.status_code == 404
    assert missing_response.json()["details"] == {"brand_id": "missing"}

    campaign = CampaignRepository(db_session).create(name="Launch")
    db_session.commit()
    link_response = api_client.post(
        f"/api/v1/campaigns/{campaign.id}/brands",
        json={"brand_id": first_response.json()["id"]},
    )
    assert link_response.status_code == 201

    detail_response = api_client.get(f"/api/v1/brands/{first_response.json()['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["campaign_count"] == 1
