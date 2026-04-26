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


def _create_outreach_deal(db_session: Session, *, status: DealStatus = DealStatus.APPROVED):
    campaign = CampaignRepository(db_session).create(name="Spring Launch")
    influencer = InfluencerRepository(db_session).create(display_name="Creator")
    InfluencerContactRepository(db_session).create(
        influencer_id=influencer.id,
        name="Pat",
        email="creator@example.com",
        is_primary=True,
    )
    InfluencerPlatformRepository(db_session).create(
        influencer_id=influencer.id,
        platform="instagram",
        profile_url="https://instagram.com/creator",
    )
    deal = DealRepository(db_session).create(
        campaign_id=campaign.id,
        influencer_id=influencer.id,
        status=status.value,
    )
    db_session.commit()
    return campaign, deal


def _create_template(api_client: TestClient) -> str:
    response = api_client.post(
        "/api/v1/templates",
        json={
            "name": "Invite",
            "subject_template": "Partnership with {{ campaign.name }}",
            "body_template": "Hi {{ contact.name }}, invite for {{ influencer.display_name }}.",
        },
    )
    assert response.status_code == 201
    assert response.json()["type"] == "OUTREACH_EMAIL"
    return response.json()["id"]


def test_template_crud_and_single_draft(
    api_client: TestClient,
    db_session: Session,
) -> None:
    _, deal = _create_outreach_deal(db_session)
    template_id = _create_template(api_client)

    draft_response = api_client.post(
        f"/api/v1/deals/{deal.id}/outreach-drafts",
        json={"template_id": template_id},
    )

    assert draft_response.status_code == 200
    draft = draft_response.json()
    assert draft["subject"] == "Partnership with Spring Launch"
    assert draft["body"] == "Hi Pat, invite for Creator."
    assert draft["to_email"] == "creator@example.com"

    patch_response = api_client.patch(
        f"/api/v1/templates/{template_id}",
        json={"description": "Updated"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["description"] == "Updated"

    delete_response = api_client.delete(f"/api/v1/templates/{template_id}")
    assert delete_response.status_code == 204
    assert api_client.get("/api/v1/templates").json()["templates"] == []


def test_unknown_template_variable_returns_validation_error(
    api_client: TestClient,
    db_session: Session,
) -> None:
    _, deal = _create_outreach_deal(db_session)
    template_response = api_client.post(
        "/api/v1/templates",
        json={
            "name": "Bad",
            "subject_template": "{{ unknown.value }}",
            "body_template": "Body",
        },
    )

    response = api_client.post(
        f"/api/v1/deals/{deal.id}/outreach-drafts",
        json={"template_id": template_response.json()["id"]},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "template_render_error"
    assert response.json()["details"] == {"unknown_variables": ["unknown.value"]}


def test_outreach_draft_rejects_non_outreach_template(
    api_client: TestClient,
    db_session: Session,
) -> None:
    _, deal = _create_outreach_deal(db_session)
    template_response = api_client.post(
        "/api/v1/templates",
        json={
            "type": "REPORT",
            "name": "Report",
            "subject_template": "Report",
            "body_template": "Body",
        },
    )

    response = api_client.post(
        f"/api/v1/deals/{deal.id}/outreach-drafts",
        json={"template_id": template_response.json()["id"]},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "template_render_error"
    assert response.json()["details"]["template_type"] == "REPORT"


def test_bulk_draft_returns_missing_contact_warning(
    api_client: TestClient,
    db_session: Session,
) -> None:
    campaign = CampaignRepository(db_session).create(name="Bulk")
    influencer = InfluencerRepository(db_session).create(display_name="No Contact")
    deal = DealRepository(db_session).create(
        campaign_id=campaign.id,
        influencer_id=influencer.id,
        status=DealStatus.DRAFT.value,
    )
    db_session.commit()
    template_id = _create_template(api_client)

    response = api_client.post(
        f"/api/v1/campaigns/{campaign.id}/outreach-drafts/bulk",
        json={"template_id": template_id, "deal_ids": [deal.id]},
    )

    assert response.status_code == 200
    assert response.json()["drafts"][0]["warnings"] == [
        "No primary contact email is available.",
        "No platform profile is available.",
    ]


def test_confirm_sent_updates_only_early_statuses(
    api_client: TestClient,
    db_session: Session,
) -> None:
    _, approved = _create_outreach_deal(db_session, status=DealStatus.APPROVED)
    _, active = _create_outreach_deal(db_session, status=DealStatus.ACTIVE)

    approved_response = api_client.post(f"/api/v1/deals/{approved.id}/outreach-sent")
    active_response = api_client.post(f"/api/v1/deals/{active.id}/outreach-sent")

    assert approved_response.status_code == 200
    assert active_response.status_code == 200
    assert db_session.get(type(approved), approved.id).status == DealStatus.OUTREACHED.value
    assert db_session.get(type(active), active.id).status == DealStatus.ACTIVE.value
