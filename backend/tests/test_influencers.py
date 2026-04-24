from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Influencer
from app.repositories.sqlalchemy import CampaignRepository, DealRepository


def test_influencer_crud_profile_search_and_archive(
    api_client: TestClient,
    db_session: Session,
) -> None:
    create_response = api_client.post(
        "/api/v1/influencers",
        json={
            "display_name": "  Creator One  ",
            "full_name": "Creator One",
            "country": "US",
            "city": "New York",
            "bio": "Bio",
            "notes": "Global notes",
            "platforms": [
                {
                    "platform": "IG",
                    "username": "@CreatorOne",
                    "profile_url": "instagram.com/creatorone?utm_source=test",
                    "follower_count": 1000,
                }
            ],
            "contacts": [
                {
                    "email": "CREATOR@EXAMPLE.COM",
                    "name": "Manager",
                    "role": "manager",
                    "is_primary": True,
                }
            ],
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["display_name"] == "Creator One"
    assert created["platforms"][0]["platform"] == "instagram"
    assert created["platforms"][0]["normalized_username"] == "creatorone"
    assert created["platforms"][0]["normalized_profile_url"] == "https://instagram.com/creatorone"
    assert created["contacts"][0]["email"] == "creator@example.com"
    assert created["contacts"][0]["is_primary"] is True

    influencer_id = created["id"]
    patch_response = api_client.patch(
        f"/api/v1/influencers/{influencer_id}",
        json={"city": "Brooklyn", "notes": "Updated notes"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["city"] == "Brooklyn"
    assert patch_response.json()["notes"] == "Updated notes"

    list_response = api_client.get(
        "/api/v1/influencers",
        params={"query": "creator", "platform": "instagram", "country": "US"},
    )
    assert list_response.status_code == 200
    rows = list_response.json()["influencers"]
    assert [row["id"] for row in rows] == [influencer_id]
    assert rows[0]["primary_platform"]["platform"] == "instagram"
    assert rows[0]["primary_contact"]["email"] == "creator@example.com"

    campaign = CampaignRepository(db_session).create(name="Campaign")
    DealRepository(db_session).create(campaign_id=campaign.id, influencer_id=influencer_id)
    db_session.commit()

    detail_response = api_client.get(f"/api/v1/influencers/{influencer_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["deals"][0]["campaign_name"] == "Campaign"

    delete_response = api_client.delete(f"/api/v1/influencers/{influencer_id}")
    assert delete_response.status_code == 204

    default_list_response = api_client.get("/api/v1/influencers")
    assert default_list_response.status_code == 200
    assert default_list_response.json()["influencers"] == []

    archived_list_response = api_client.get(
        "/api/v1/influencers",
        params={"include_archived": "true"},
    )
    assert archived_list_response.status_code == 200
    assert archived_list_response.json()["influencers"][0]["archived_at"] is not None

    archived = db_session.get(Influencer, influencer_id)
    assert archived is not None
    assert archived.archived_at is not None


def test_platform_lifecycle_and_duplicate_conflict(api_client: TestClient) -> None:
    first = api_client.post("/api/v1/influencers", json={"display_name": "Creator One"}).json()
    second = api_client.post("/api/v1/influencers", json={"display_name": "Creator Two"}).json()

    create_platform_response = api_client.post(
        f"/api/v1/influencers/{first['id']}/platforms",
        json={
            "platform": "Instagram",
            "username": "@CreatorOne",
            "profile_url": "https://www.instagram.com/creatorone/",
            "follower_count": 2000,
        },
    )
    assert create_platform_response.status_code == 201
    platform = create_platform_response.json()
    assert platform["platform"] == "instagram"
    assert platform["normalized_profile_url"] == "https://instagram.com/creatorone"

    duplicate_response = api_client.post(
        f"/api/v1/influencers/{second['id']}/platforms",
        json={
            "platform": "instagram",
            "username": "creatorone",
            "profile_url": "https://instagram.com/creatorone?utm_campaign=x",
        },
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["code"] == "platform_conflict"

    update_response = api_client.patch(
        f"/api/v1/influencers/{first['id']}/platforms/{platform['id']}",
        json={"username": "@creator_one", "follower_count": 3000},
    )
    assert update_response.status_code == 200
    assert update_response.json()["normalized_username"] == "creator_one"
    assert update_response.json()["follower_count"] == 3000

    list_response = api_client.get(f"/api/v1/influencers/{first['id']}/platforms")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["platforms"]] == [platform["id"]]

    delete_response = api_client.delete(
        f"/api/v1/influencers/{first['id']}/platforms/{platform['id']}"
    )
    assert delete_response.status_code == 204
    assert api_client.get(f"/api/v1/influencers/{first['id']}/platforms").json() == {
        "platforms": []
    }


def test_contact_lifecycle_normalization_and_conflict_metadata(
    api_client: TestClient,
) -> None:
    first = api_client.post("/api/v1/influencers", json={"display_name": "Creator One"}).json()
    second = api_client.post("/api/v1/influencers", json={"display_name": "Creator Two"}).json()

    first_contact_response = api_client.post(
        f"/api/v1/influencers/{first['id']}/contacts",
        json={"email": "MANAGER@EXAMPLE.COM", "role": "manager", "is_primary": True},
    )
    assert first_contact_response.status_code == 201
    first_contact = first_contact_response.json()
    assert first_contact["email"] == "manager@example.com"

    second_contact_response = api_client.post(
        f"/api/v1/influencers/{second['id']}/contacts",
        json={"email": "manager@example.com", "role": "agency"},
    )
    assert second_contact_response.status_code == 201
    assert second_contact_response.json()["conflict_influencer_ids"] == [first["id"]]

    update_response = api_client.patch(
        f"/api/v1/influencers/{first['id']}/contacts/{first_contact['id']}",
        json={"name": "Lead manager", "email": "LEAD@EXAMPLE.COM"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Lead manager"
    assert update_response.json()["email"] == "lead@example.com"

    list_response = api_client.get(f"/api/v1/influencers/{first['id']}/contacts")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["contacts"]] == [first_contact["id"]]

    delete_response = api_client.delete(
        f"/api/v1/influencers/{first['id']}/contacts/{first_contact['id']}"
    )
    assert delete_response.status_code == 204
    assert api_client.get(f"/api/v1/influencers/{first['id']}/contacts").json() == {
        "contacts": []
    }
