from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import models
from app.domain.enums import DealStatus
from app.repositories.sqlalchemy import (
    CampaignRepository,
    DealRepository,
    EmailThreadMetadataRepository,
    InfluencerContactRepository,
    InfluencerRepository,
)


def _create_deal(db_session: Session, *, email: str = "creator@example.com") -> models.Deal:
    campaign = CampaignRepository(db_session).create(name="Launch")
    influencer = InfluencerRepository(db_session).create(display_name="Creator")
    InfluencerContactRepository(db_session).create(
        influencer_id=influencer.id,
        email=email,
        is_primary=True,
    )
    deal = DealRepository(db_session).create(
        campaign_id=campaign.id,
        influencer_id=influencer.id,
        status=DealStatus.OUTREACHED.value,
    )
    db_session.commit()
    return deal


def test_match_unique_known_contact_returns_influencer_and_deal_candidates(
    api_client: TestClient,
    db_session: Session,
) -> None:
    deal = _create_deal(db_session)

    response = api_client.post(
        "/api/v1/email/threads/match",
        json={
            "provider": "gmail",
            "external_thread_id": "thread-1",
            "message_count": 2,
            "participants": [{"email": "creator@example.com"}],
        },
    )

    assert response.status_code == 200
    candidates = response.json()["candidates"]
    assert {candidate["type"] for candidate in candidates} == {
        "inferred_from_contact",
        "deal_candidate",
    }
    deal_candidate = next(candidate for candidate in candidates if candidate["deal_id"] == deal.id)
    assert deal_candidate["suggested_status"] == DealStatus.RESPONDED.value


def test_match_shared_email_returns_conflicts(
    api_client: TestClient,
    db_session: Session,
) -> None:
    first = InfluencerRepository(db_session).create(display_name="First")
    second = InfluencerRepository(db_session).create(display_name="Second")
    InfluencerContactRepository(db_session).create(influencer_id=first.id, email="mgr@example.com")
    InfluencerContactRepository(db_session).create(influencer_id=second.id, email="mgr@example.com")
    db_session.commit()

    response = api_client.post(
        "/api/v1/email/threads/match",
        json={
            "provider": "gmail",
            "external_thread_id": "thread-2",
            "participants": [{"email": "mgr@example.com"}],
        },
    )

    assert response.status_code == 200
    candidates = response.json()["candidates"]
    assert [candidate["type"] for candidate in candidates] == ["conflict", "conflict"]


def test_manual_link_inheritance_and_scoped_lists(
    api_client: TestClient,
    db_session: Session,
) -> None:
    deal = _create_deal(db_session)
    EmailThreadMetadataRepository(db_session).create(
        provider="gmail",
        external_thread_id="thread-3",
        subject="Launch",
        participants_json=[{"email": "creator@example.com"}],
        message_count=1,
    )
    db_session.commit()

    create_response = api_client.post(
        "/api/v1/email/thread-links",
        json={"provider": "gmail", "external_thread_id": "thread-3", "deal_id": deal.id},
    )

    assert create_response.status_code == 201
    link_id = create_response.json()["id"]

    match_response = api_client.post(
        "/api/v1/email/threads/match",
        json={"provider": "gmail", "external_thread_id": "thread-3"},
    )
    assert match_response.status_code == 200
    assert match_response.json()["candidates"][0]["type"] == "inherited_from_thread"

    deal_threads = api_client.get(f"/api/v1/deals/{deal.id}/email-threads")
    assert deal_threads.status_code == 200
    assert deal_threads.json()["threads"][0]["thread"]["subject"] == "Launch"

    delete_response = api_client.delete(f"/api/v1/email/thread-links/{link_id}")
    assert delete_response.status_code == 204
    assert api_client.get(f"/api/v1/deals/{deal.id}/email-threads").json()["threads"] == []


def test_deal_link_validates_influencer_consistency(
    api_client: TestClient,
    db_session: Session,
) -> None:
    deal = _create_deal(db_session)
    other = InfluencerRepository(db_session).create(display_name="Other")
    db_session.commit()

    response = api_client.post(
        "/api/v1/email/thread-links",
        json={
            "provider": "gmail",
            "external_thread_id": "thread-4",
            "deal_id": deal.id,
            "influencer_id": other.id,
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_email_context_link"
