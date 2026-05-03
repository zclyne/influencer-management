from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Base
from app.enums import DealStatus
from app.repositories.sqlalchemy import CampaignRepository, DealRepository, InfluencerRepository
from app.schemas.email_context import EmailThreadLinkRequest
from app.services.email_context import (
    EmailContextService,
    GmailCredential,
    GmailCredentialStore,
)


class FakeGmailConnector:
    def __init__(self) -> None:
        self.labels: list[dict[str, Any]] = [
            {"id": "INBOX", "name": "INBOX", "type": "system"},
        ]
        self.modified: list[dict[str, Any]] = []

    def authorization_url(self, state: str) -> str:
        return f"https://accounts.google.com/o/oauth2/v2/auth?state={state}"

    def exchange_code(self, code: str) -> GmailCredential:
        return GmailCredential(
            email="agency@example.com",
            google_subject="google-subject",
            refresh_token=f"refresh-{code}",
            access_token="access-token",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        )

    def refresh_access_token(self, credential: GmailCredential) -> GmailCredential:
        return credential

    def list_labels(self, access_token: str) -> list[dict[str, Any]]:
        return self.labels

    def create_label(self, access_token: str, name: str) -> dict[str, Any]:
        label = {"id": f"label-{len(self.labels)}", "name": name, "type": "user"}
        self.labels.append(label)
        return label

    def modify_thread(
        self,
        access_token: str,
        thread_id: str,
        *,
        add_label_ids: list[str] | None = None,
        remove_label_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        self.modified.append(
            {
                "thread_id": thread_id,
                "add": add_label_ids or [],
                "remove": remove_label_ids or [],
            }
        )
        return {}

    def list_threads(
        self,
        access_token: str,
        *,
        label_ids: list[str],
        query: str | None,
        page_token: str | None,
        page_size: int,
    ) -> dict[str, Any]:
        return {
            "threads": [
                self.get_thread(access_token, "thread-1", metadata_only=True),
            ],
            "nextPageToken": None,
        }

    def get_thread(
        self, access_token: str, thread_id: str, *, metadata_only: bool = False
    ) -> dict[str, Any]:
        crm_label_ids = [
            str(label["id"])
            for label in self.labels
            if str(label["name"]).startswith("DesktopIRM/")
        ]
        return {
            "id": thread_id,
            "snippet": "Latest reply",
            "messages": [
                {
                    "id": "msg-1",
                    "labelIds": ["INBOX", *crm_label_ids],
                    "internalDate": "1770000000000",
                    "snippet": "Latest reply",
                    "payload": {
                        "mimeType": "text/plain",
                        "headers": [
                            {"name": "Subject", "value": "Campaign details"},
                            {"name": "From", "value": "Creator <creator@example.com>"},
                            {"name": "To", "value": "Agency <agency@example.com>"},
                            {"name": "Date", "value": "Fri, 1 May 2026 12:00:00 +0000"},
                        ],
                        "body": {"data": "SGVsbG8"},
                    },
                }
            ],
        }


def _store(tmp_path: Path) -> GmailCredentialStore:
    store = GmailCredentialStore(
        tmp_path / "gmail_oauth.json.enc",
        tmp_path / "gmail_oauth.key",
    )
    store.write(
        GmailCredential(
            email="agency@example.com",
            google_subject="google-subject",
            refresh_token="refresh-token",
            access_token="access-token",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        )
    )
    return store


def _create_deal(db_session: Session) -> tuple[str, str]:
    campaign = CampaignRepository(db_session).create(name="Launch")
    influencer = InfluencerRepository(db_session).create(display_name="Creator")
    deal = DealRepository(db_session).create(
        campaign_id=campaign.id,
        influencer_id=influencer.id,
        status=DealStatus.OUTREACHED.value,
    )
    db_session.commit()
    return campaign.id, deal.id


def test_email_tables_are_not_part_of_local_metadata() -> None:
    assert "email_accounts" not in Base.metadata.tables
    assert "email_thread_metadata" not in Base.metadata.tables
    assert "email_thread_links" not in Base.metadata.tables


def test_credential_store_persists_single_encrypted_gmail_secret(tmp_path: Path) -> None:
    store = _store(tmp_path)

    raw_secret = (tmp_path / "gmail_oauth.json.enc").read_text()
    assert "refresh-token" not in raw_secret

    loaded = store.read()
    assert loaded is not None
    assert loaded.email == "agency@example.com"
    assert loaded.refresh_token == "refresh-token"


def test_link_deal_applies_campaign_and_deal_gmail_labels(
    db_session: Session,
    tmp_path: Path,
) -> None:
    campaign_id, deal_id = _create_deal(db_session)
    connector = FakeGmailConnector()
    service = EmailContextService(
        db_session,
        connector=connector,  # type: ignore[arg-type]
        credential_store=_store(tmp_path),
    )

    response = service.link_thread(
        "thread-1",
        EmailThreadLinkRequest(campaign_id=campaign_id, deal_id=deal_id),
    )

    assert {link.type for link in response.links} == {"campaign", "deal"}
    assert connector.modified[-1]["thread_id"] == "thread-1"
    assert len(connector.modified[-1]["add"]) == 2


def test_campaign_filter_uses_existing_gmail_label(
    db_session: Session,
    tmp_path: Path,
) -> None:
    campaign_id, _ = _create_deal(db_session)
    connector = FakeGmailConnector()
    connector.labels.append(
        {
            "id": "campaign-label",
            "name": f"DesktopIRM/Campaigns/{campaign_id}",
            "type": "user",
        }
    )
    service = EmailContextService(
        db_session,
        connector=connector,  # type: ignore[arg-type]
        credential_store=_store(tmp_path),
    )

    response = service.list_threads(campaign_id=campaign_id)

    assert response.threads[0].id == "thread-1"
    assert response.threads[0].crm_links[0].campaign_id == campaign_id
