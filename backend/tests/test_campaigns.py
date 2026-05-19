import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Campaign, CampaignBrand
from app.enums import CampaignStatus, StoredFileKind
from app.repositories.sqlalchemy import (
    BrandRepository,
    CampaignAttachmentRepository,
    CampaignRepository,
)


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
            "tags": ["  launch  ", "Launch", "paid/approved"],
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Spring Launch"
    assert created["status"] == CampaignStatus.PLANNING.value
    assert created["budget"] == "1200.50"
    assert created["brands"] == []
    assert created["tags"] == ["launch", "paid/approved"]

    campaign_id = created["id"]
    patch_response = api_client.patch(
        f"/api/v1/campaigns/{campaign_id}",
        json={"status": "ACTIVE", "notes": "Updated", "tags": ["priority", "seasonal"]},
    )

    assert patch_response.status_code == 200
    patched = patch_response.json()
    assert patched["status"] == CampaignStatus.ACTIVE.value
    assert patched["notes"] == "Updated"
    assert patched["brief"] == "Creator launch"
    assert patched["tags"] == ["priority", "seasonal"]

    list_response = api_client.get("/api/v1/campaigns", params={"status": "ACTIVE"})
    assert list_response.status_code == 200
    assert [campaign["id"] for campaign in list_response.json()["campaigns"]] == [campaign_id]

    tag_list_response = api_client.get("/api/v1/campaigns", params={"tag": " Seasonal "})
    assert tag_list_response.status_code == 200
    assert [campaign["id"] for campaign in tag_list_response.json()["campaigns"]] == [campaign_id]

    invalid_tags_response = api_client.patch(
        f"/api/v1/campaigns/{campaign_id}",
        json={"tags": ["needs, comma"]},
    )
    assert invalid_tags_response.status_code == 422
    assert invalid_tags_response.json()["code"] == "invalid_campaign"

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


def test_campaign_name_must_be_unique(
    api_client: TestClient,
    db_session: Session,
) -> None:
    existing = CampaignRepository(db_session).create(name="Spring Launch")
    other = CampaignRepository(db_session).create(name="Summer Launch")
    db_session.commit()

    duplicate_create_response = api_client.post(
        "/api/v1/campaigns",
        json={"name": " spring launch "},
    )
    assert duplicate_create_response.status_code == 409
    assert duplicate_create_response.json()["code"] == "campaign_name_conflict"

    duplicate_update_response = api_client.patch(
        f"/api/v1/campaigns/{other.id}",
        json={"name": "SPRING LAUNCH"},
    )
    assert duplicate_update_response.status_code == 409
    assert duplicate_update_response.json()["code"] == "campaign_name_conflict"

    same_name_update_response = api_client.patch(
        f"/api/v1/campaigns/{existing.id}",
        json={"name": "Spring Launch"},
    )
    assert same_name_update_response.status_code == 200


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


def test_campaign_attachment_upload_list_download_and_delete(
    api_client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    os.environ["LOCAL_STORAGE_DIR"] = str(tmp_path)
    get_settings.cache_clear()
    campaign = CampaignRepository(db_session).create(name="Spring Launch")
    db_session.commit()

    upload_response = api_client.post(
        f"/api/v1/campaigns/{campaign.id}/attachments",
        files={"file": ("../brief.txt", b"campaign brief", "text/plain")},
    )

    assert upload_response.status_code == 201
    uploaded = upload_response.json()
    assert uploaded["campaign_id"] == campaign.id
    assert uploaded["file"]["kind"] == StoredFileKind.CAMPAIGN_ATTACHMENT.value
    assert uploaded["file"]["original_name"] == "brief.txt"
    assert uploaded["file"]["size_bytes"] == len(b"campaign brief")
    assert uploaded["file"]["exists"] is True

    list_response = api_client.get(f"/api/v1/campaigns/{campaign.id}/attachments")
    assert list_response.status_code == 200
    attachments = list_response.json()["attachments"]
    assert [attachment["id"] for attachment in attachments] == [uploaded["id"]]

    download_response = api_client.get(f"/api/v1/files/{uploaded['file']['id']}/download")
    assert download_response.status_code == 200
    assert download_response.content == b"campaign brief"

    delete_response = api_client.delete(
        f"/api/v1/campaigns/{campaign.id}/attachments/{uploaded['id']}"
    )
    assert delete_response.status_code == 204
    assert CampaignAttachmentRepository(db_session).list_for_campaign(campaign.id) == []

    deleted_file_response = api_client.get(f"/api/v1/files/{uploaded['file']['id']}")
    assert deleted_file_response.status_code == 404


def test_campaign_attachment_list_is_empty_when_campaign_has_no_attachments(
    api_client: TestClient,
    db_session: Session,
) -> None:
    campaign = CampaignRepository(db_session).create(name="Spring Launch")
    db_session.commit()

    response = api_client.get(f"/api/v1/campaigns/{campaign.id}/attachments")

    assert response.status_code == 200
    assert response.json() == {"attachments": []}


def test_campaign_attachment_is_campaign_scoped_and_archived_campaigns_are_read_only(
    api_client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    os.environ["LOCAL_STORAGE_DIR"] = str(tmp_path)
    get_settings.cache_clear()
    first_campaign = CampaignRepository(db_session).create(name="Spring Launch")
    second_campaign = CampaignRepository(db_session).create(name="Summer Launch")
    db_session.commit()

    upload_response = api_client.post(
        f"/api/v1/campaigns/{first_campaign.id}/attachments",
        files={"file": ("references.pdf", b"pdf", "application/pdf")},
    )
    assert upload_response.status_code == 201
    attachment_id = upload_response.json()["id"]

    wrong_campaign_delete_response = api_client.delete(
        f"/api/v1/campaigns/{second_campaign.id}/attachments/{attachment_id}"
    )
    assert wrong_campaign_delete_response.status_code == 404

    archived_response = api_client.delete(f"/api/v1/campaigns/{first_campaign.id}")
    assert archived_response.status_code == 204

    archived_list_response = api_client.get(
        f"/api/v1/campaigns/{first_campaign.id}/attachments"
    )
    assert archived_list_response.status_code == 200
    assert len(archived_list_response.json()["attachments"]) == 1

    archived_upload_response = api_client.post(
        f"/api/v1/campaigns/{first_campaign.id}/attachments",
        files={"file": ("after-archive.txt", b"blocked", "text/plain")},
    )
    assert archived_upload_response.status_code == 422
    assert archived_upload_response.json()["code"] == "archived_campaign"

    archived_delete_response = api_client.delete(
        f"/api/v1/campaigns/{first_campaign.id}/attachments/{attachment_id}"
    )
    assert archived_delete_response.status_code == 422
    assert archived_delete_response.json()["code"] == "archived_campaign"
