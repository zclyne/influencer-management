import base64
from datetime import UTC, datetime, timedelta
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Base
from app.enums import DealStatus
from app.repositories.sqlalchemy import CampaignRepository, DealRepository, InfluencerRepository
from app.schemas.email_context import (
    EmailParticipant,
    EmailThreadBatchRequest,
    EmailThreadLinkRequest,
)
from app.services.email_context import (
    EmailContextService,
    EmailDraftFile,
    EmailProviderError,
    EmailReconnectRequired,
    GmailConnector,
    GmailCredential,
    GmailCredentialStore,
)


class FakeGmailConnector:
    def __init__(self) -> None:
        self.labels: list[dict[str, Any]] = [
            {"id": "INBOX", "name": "INBOX", "type": "system"},
            {"id": "UNREAD", "name": "UNREAD", "type": "system"},
        ]
        self.modified: list[dict[str, Any]] = []
        self.created_drafts: list[dict[str, Any]] = []
        self.updated_drafts: list[dict[str, Any]] = []
        self.sent_drafts: list[str] = []
        self.deleted_drafts: list[str] = []
        self.list_thread_calls: list[dict[str, Any]] = []
        self.thread_label_ids: dict[str, list[str]] = {"thread-1": ["INBOX", "UNREAD"]}

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
        current = set(self.thread_label_ids.get(thread_id, ["INBOX"]))
        current.update(add_label_ids or [])
        current.difference_update(remove_label_ids or [])
        self.thread_label_ids[thread_id] = sorted(current)
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
        self.list_thread_calls.append(
            {
                "label_ids": label_ids,
                "query": query,
                "page_token": page_token,
                "page_size": page_size,
            }
        )
        return {
            "threads": [
                self.get_thread(access_token, "thread-1", metadata_only=True),
            ],
            "nextPageToken": None,
            "resultSizeEstimate": 1,
        }

    def get_thread(
        self, access_token: str, thread_id: str, *, metadata_only: bool = False
    ) -> dict[str, Any]:
        label_ids = self.thread_label_ids.get(thread_id, ["INBOX"])
        return {
            "id": thread_id,
            "snippet": "Latest reply",
            "messages": [
                {
                    "id": "msg-1",
                    "labelIds": label_ids,
                    "internalDate": "1770000000000",
                    "snippet": "Latest reply",
                    "payload": {
                        "mimeType": "text/plain",
                        "headers": [
                            {"name": "Subject", "value": "Campaign details"},
                            {"name": "Message-ID", "value": "<msg-1@example.com>"},
                            {"name": "References", "value": "<root@example.com>"},
                            {"name": "From", "value": "Creator <creator@example.com>"},
                            {
                                "name": "To",
                                "value": "Agency <agency@example.com>, Other <other@example.com>",
                            },
                            {"name": "Cc", "value": "Second <second@example.com>"},
                            {"name": "Date", "value": "Fri, 1 May 2026 12:00:00 +0000"},
                        ],
                        "body": {"data": "SGVsbG8"},
                    },
                }
            ],
        }

    def create_draft(
        self,
        access_token: str,
        *,
        raw_message: str,
        thread_id: str,
    ) -> dict[str, Any]:
        self.created_drafts.append({"raw": raw_message, "thread_id": thread_id})
        return {"id": "draft-1", "message": {"id": "draft-message-1", "threadId": thread_id}}

    def update_draft(
        self, access_token: str, draft_id: str, *, raw_message: str, thread_id: str
    ) -> dict[str, Any]:
        self.updated_drafts.append(
            {"draft_id": draft_id, "raw": raw_message, "thread_id": thread_id}
        )
        return {"id": draft_id, "message": {"id": "draft-message-2", "threadId": thread_id}}

    def send_draft(self, access_token: str, draft_id: str) -> dict[str, Any]:
        self.sent_drafts.append(draft_id)
        return {"id": "sent-message-1", "threadId": "thread-1"}

    def delete_draft(self, access_token: str, draft_id: str) -> None:
        self.deleted_drafts.append(draft_id)


class RefreshFailingGmailConnector(FakeGmailConnector):
    def refresh_access_token(self, credential: GmailCredential) -> GmailCredential:
        raise EmailProviderError("Google OAuth request failed.")


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
        status=DealStatus.ACTIVE.value,
    )
    db_session.commit()
    return campaign.id, deal.id


def _decoded_message(raw: str):
    padding = "=" * (-len(raw) % 4)
    data = base64.urlsafe_b64decode(f"{raw}{padding}".encode("ascii"))
    return BytesParser(policy=policy.default).parsebytes(data)


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


def test_auth_status_marks_gmail_reconnect_required_when_refresh_fails(
    db_session: Session,
    tmp_path: Path,
) -> None:
    service = EmailContextService(
        db_session,
        connector=RefreshFailingGmailConnector(),  # type: ignore[arg-type]
        credential_store=_store(tmp_path),
    )

    response = service.auth_status()

    assert response.connected is True
    assert response.email == "agency@example.com"
    assert response.reconnect_required is True


def test_email_operations_request_reconnect_when_gmail_refresh_fails(
    db_session: Session,
    tmp_path: Path,
) -> None:
    service = EmailContextService(
        db_session,
        connector=RefreshFailingGmailConnector(),  # type: ignore[arg-type]
        credential_store=_store(tmp_path),
    )

    try:
        service.list_labels()
    except EmailReconnectRequired as exc:
        assert exc.status_code == 401
        assert exc.code == "email_reconnect_required"
        assert exc.details == {"email": "agency@example.com"}
    else:
        raise AssertionError("Expected EmailReconnectRequired.")


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
    campaign_link = next(link for link in response.links if link.type == "campaign")
    assert campaign_link.campaign_id == campaign_id
    assert campaign_link.campaign_name == "Launch"
    campaign_prefix = "CreatorFlow/Campaigns/"
    campaign_label = next(
        label for label in connector.labels if str(label["name"]).startswith(campaign_prefix)
    )
    assert campaign_label["name"] == "CreatorFlow/Campaigns/Launch"
    assert connector.modified[0]["thread_id"] == "thread-1"
    assert len(connector.modified[0]["add"]) == 2


def test_campaign_filter_uses_existing_gmail_label(
    db_session: Session,
    tmp_path: Path,
) -> None:
    campaign_id, _ = _create_deal(db_session)
    connector = FakeGmailConnector()
    connector.labels.append(
        {
            "id": "campaign-label",
            "name": "CreatorFlow/Campaigns/Launch",
            "type": "user",
        }
    )
    connector.thread_label_ids["thread-1"] = ["INBOX", "campaign-label"]
    service = EmailContextService(
        db_session,
        connector=connector,  # type: ignore[arg-type]
        credential_store=_store(tmp_path),
    )

    response = service.list_threads(campaign_id=campaign_id)

    assert response.threads[0].id == "thread-1"
    assert response.threads[0].crm_links[0].campaign_id == campaign_id
    assert response.threads[0].crm_links[0].campaign_name == "Launch"
    assert response.result_size_estimate == 1
    assert connector.list_thread_calls[-1]["label_ids"] == ["campaign-label"]
    assert connector.list_thread_calls[-1]["query"] == "in:inbox category:primary"


def test_email_view_maps_to_gmail_search_query(
    db_session: Session,
    tmp_path: Path,
) -> None:
    _create_deal(db_session)
    connector = FakeGmailConnector()
    connector.thread_label_ids["thread-1"] = ["CATEGORY_PROMOTIONS"]
    service = EmailContextService(
        db_session,
        connector=connector,  # type: ignore[arg-type]
        credential_store=_store(tmp_path),
    )

    response = service.list_threads(view="promotions")

    assert response.threads[0].id == "thread-1"
    assert connector.list_thread_calls[-1]["label_ids"] == []
    assert connector.list_thread_calls[-1]["query"] == "in:inbox category:promotions"


def test_email_view_combines_gmail_view_query_with_user_search(
    db_session: Session,
    tmp_path: Path,
) -> None:
    _create_deal(db_session)
    connector = FakeGmailConnector()
    service = EmailContextService(
        db_session,
        connector=connector,  # type: ignore[arg-type]
        credential_store=_store(tmp_path),
    )

    response = service.list_threads(view="primary", query="from:creator@example.com")

    assert response.threads[0].id == "thread-1"
    assert connector.list_thread_calls[-1]["label_ids"] == []
    assert (
        connector.list_thread_calls[-1]["query"]
        == "in:inbox category:primary from:creator@example.com"
    )


def test_batch_thread_actions_update_gmail_labels(
    db_session: Session,
    tmp_path: Path,
) -> None:
    _create_deal(db_session)
    connector = FakeGmailConnector()
    service = EmailContextService(
        db_session,
        connector=connector,  # type: ignore[arg-type]
        credential_store=_store(tmp_path),
    )

    read_response = service.batch_threads(
        EmailThreadBatchRequest(thread_ids=["thread-1"], action="mark_read")
    )
    unread_response = service.batch_threads(
        EmailThreadBatchRequest(thread_ids=["thread-1"], action="mark_unread")
    )
    delete_response = service.batch_threads(
        EmailThreadBatchRequest(thread_ids=["thread-1"], action="delete")
    )

    assert read_response.updated_count == 1
    assert unread_response.updated_count == 1
    assert delete_response.updated_count == 1
    assert connector.modified[-3:] == [
        {"thread_id": "thread-1", "add": [], "remove": ["UNREAD"]},
        {"thread_id": "thread-1", "add": ["UNREAD"], "remove": []},
        {"thread_id": "thread-1", "add": ["TRASH"], "remove": ["INBOX"]},
    ]


def test_get_thread_marks_unread_thread_as_read(
    db_session: Session,
    tmp_path: Path,
) -> None:
    _create_deal(db_session)
    connector = FakeGmailConnector()
    service = EmailContextService(
        db_session,
        connector=connector,  # type: ignore[arg-type]
        credential_store=_store(tmp_path),
    )

    response = service.get_thread("thread-1")

    assert response.unread is False
    assert "UNREAD" not in connector.thread_label_ids["thread-1"]
    assert connector.modified[-1] == {
        "thread_id": "thread-1",
        "add": [],
        "remove": ["UNREAD"],
    }


def test_get_thread_can_skip_marking_unread_thread_as_read(
    db_session: Session,
    tmp_path: Path,
) -> None:
    _create_deal(db_session)
    connector = FakeGmailConnector()
    service = EmailContextService(
        db_session,
        connector=connector,  # type: ignore[arg-type]
        credential_store=_store(tmp_path),
    )

    response = service.get_thread("thread-1", mark_read=False)

    assert response.unread is True
    assert "UNREAD" in connector.thread_label_ids["thread-1"]
    assert connector.modified == []


def test_reply_draft_create_builds_threaded_mime_and_recipients(
    db_session: Session,
    tmp_path: Path,
) -> None:
    _create_deal(db_session)
    connector = FakeGmailConnector()
    service = EmailContextService(
        db_session,
        connector=connector,  # type: ignore[arg-type]
        credential_store=_store(tmp_path),
    )

    response = service.save_reply_draft(
        "thread-1",
        draft_id=None,
        reply_mode="reply_all",
        anchor_message_id=None,
        to=[],
        cc=[],
        bcc=[],
        subject=None,
        body_html=(
            '<p>Hello <strong>there</strong><script>alert("x")</script>'
            '<img src="cid:inline-1"></p>'
        ),
        body_text="Hello there",
        inline_images=[
            EmailDraftFile(
                filename="inline.png",
                content_type="image/png",
                content=b"inline-image",
                cid="inline-1",
            )
        ],
        attachments=[
            EmailDraftFile(
                filename="brief.pdf",
                content_type="application/pdf",
                content=b"attachment",
            )
        ],
    )

    assert response.draft_id == "draft-1"
    assert response.subject == "Re: Campaign details"
    assert [participant.email for participant in response.to] == ["creator@example.com"]
    assert {participant.email for participant in response.cc} == {
        "other@example.com",
        "second@example.com",
    }
    assert connector.created_drafts[0]["thread_id"] == "thread-1"
    message = _decoded_message(connector.created_drafts[0]["raw"])
    assert message["Subject"] == "Re: Campaign details"
    assert message["In-Reply-To"] == "<msg-1@example.com>"
    assert message["References"] == "<root@example.com> <msg-1@example.com>"
    assert "agency@example.com" not in message["To"]
    assert any(part.get_content_type() == "text/html" for part in message.walk())
    assert any(part.get("Content-ID") == "<inline-1>" for part in message.walk())
    assert any(part.get_filename() == "brief.pdf" for part in message.walk())
    html_part = next(part for part in message.walk() if part.get_content_type() == "text/html")
    assert "<script>" not in html_part.get_content()


def test_reply_draft_update_send_and_delete(
    db_session: Session,
    tmp_path: Path,
) -> None:
    _create_deal(db_session)
    connector = FakeGmailConnector()
    service = EmailContextService(
        db_session,
        connector=connector,  # type: ignore[arg-type]
        credential_store=_store(tmp_path),
    )

    update_response = service.save_reply_draft(
        "thread-1",
        draft_id="draft-1",
        reply_mode="reply",
        anchor_message_id="msg-1",
        to=[EmailParticipant(email="creator@example.com", name="Creator")],
        cc=[],
        bcc=[],
        subject="Re: Campaign details",
        body_html="<p>Updated</p>",
        body_text="Updated",
    )
    send_response = service.send_draft("draft-1")
    service.delete_draft("draft-2")

    assert update_response.message_id == "draft-message-2"
    assert connector.updated_drafts[0]["draft_id"] == "draft-1"
    assert send_response.message_id == "sent-message-1"
    assert connector.sent_drafts == ["draft-1"]
    assert connector.deleted_drafts == ["draft-2"]


class FakeGoogleRequest:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def execute(self) -> dict[str, Any]:
        return self.payload


class FakeGoogleThreads:
    def __init__(self) -> None:
        self.list_kwargs: dict[str, Any] | None = None
        self.get_kwargs: list[dict[str, Any]] = []

    def list(self, **kwargs: Any) -> FakeGoogleRequest:
        self.list_kwargs = kwargs
        return FakeGoogleRequest(
            {
                "threads": [{"id": "thread-1"}],
                "nextPageToken": "next-token",
                "resultSizeEstimate": 42,
            }
        )

    def get(self, **kwargs: Any) -> FakeGoogleRequest:
        self.get_kwargs.append(kwargs)
        return FakeGoogleRequest(
            {
                "id": kwargs["id"],
                "snippet": "Latest reply",
                "messages": [
                    {
                        "id": "msg-1",
                        "payload": {
                            "headers": [
                                {"name": "Subject", "value": "Campaign details"},
                            ],
                        },
                    }
                ],
            }
        )


class FakeGoogleUsers:
    def __init__(self, threads: FakeGoogleThreads) -> None:
        self._threads = threads

    def threads(self) -> FakeGoogleThreads:
        return self._threads


class FakeGoogleService:
    def __init__(self, threads: FakeGoogleThreads) -> None:
        self._users = FakeGoogleUsers(threads)

    def users(self) -> FakeGoogleUsers:
        return self._users


class FakeSettings:
    gmail_client_id = "client-id"
    gmail_client_secret = "client-secret"


def test_gmail_connector_uses_google_client_thread_pagination(tmp_path: Path) -> None:
    threads = FakeGoogleThreads()
    connector = GmailConnector(settings=FakeSettings(), credential_store=_store(tmp_path))  # type: ignore[arg-type]
    connector._service = lambda access_token: FakeGoogleService(threads)  # type: ignore[method-assign]

    response = connector.list_threads(
        "access-token",
        label_ids=["Label_1"],
        query="from:creator@example.com",
        page_token="page-token",
        page_size=25,
    )

    assert threads.list_kwargs == {
        "userId": "me",
        "maxResults": 25,
        "q": "from:creator@example.com",
        "pageToken": "page-token",
        "labelIds": ["Label_1"],
    }
    assert threads.get_kwargs[0]["format"] == "metadata"
    assert response["nextPageToken"] == "next-token"
    assert response["resultSizeEstimate"] == 42
