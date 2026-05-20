from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from email.utils import formataddr, getaddresses, parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import bleach
import httpx
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials as GoogleCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.repositories.sqlalchemy import CampaignRepository, DealRepository
from app.schemas.email_context import (
    EmailCrmLink,
    EmailDraftSendResponse,
    EmailParticipant,
    EmailReplyDraftResponse,
    EmailThreadBatchRequest,
    EmailThreadBatchResponse,
    EmailThreadLinkRequest,
    EmailThreadLinkResponse,
    GmailAuthStartResponse,
    GmailAuthStatusResponse,
    GmailLabelListResponse,
    GmailLabelResponse,
    GmailMessageResponse,
    GmailThreadDetailResponse,
    GmailThreadListResponse,
    GmailThreadSummary,
)

GMAIL_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GMAIL_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GMAIL_SCOPES = [
    "openid",
    "email",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]
CRM_LABEL_ROOT = "CreatorFlow"
EMAIL_VIEW_QUERIES = {
    "primary": "in:inbox category:primary",
    "promotions": "in:inbox category:promotions",
    "social": "in:inbox category:social",
    "updates": "in:inbox category:updates",
    "forums": "in:inbox category:forums",
    "starred": "is:starred",
    "deleted": "in:trash",
    "spam": "in:spam",
}
MAX_DRAFT_UPLOAD_BYTES = 24 * 1024 * 1024
ALLOWED_REPLY_HTML_TAGS = set(bleach.sanitizer.ALLOWED_TAGS).union(
    {
        "p",
        "br",
        "div",
        "span",
        "strong",
        "em",
        "u",
        "ul",
        "ol",
        "li",
        "blockquote",
        "pre",
        "code",
        "a",
        "img",
    }
)
ALLOWED_REPLY_HTML_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
}


class EmailContextServiceError(Exception):
    code = "email_error"
    status_code = 422

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EmailNotConfigured(EmailContextServiceError):
    code = "email_not_configured"


class EmailNotConnected(EmailContextServiceError):
    code = "email_not_connected"
    status_code = 401


class EmailReconnectRequired(EmailNotConnected):
    code = "email_reconnect_required"


class EmailNotFound(EmailContextServiceError):
    code = "not_found"
    status_code = 404


class EmailProviderError(EmailContextServiceError):
    code = "email_provider_error"
    status_code = 502


@dataclass
class GmailCredential:
    email: str
    google_subject: str | None
    refresh_token: str
    access_token: str | None
    expires_at: datetime | None
    scopes: list[str]


@dataclass(frozen=True)
class EmailDraftFile:
    filename: str
    content_type: str
    content: bytes
    cid: str | None = None


class GmailCredentialStore:
    def __init__(self, credential_file: Path, key_file: Path) -> None:
        self.credential_file = credential_file
        self.key_file = key_file

    def read(self) -> GmailCredential | None:
        if not self.credential_file.exists():
            return None
        payload = json.loads(self._decrypt(self.credential_file.read_text()))
        expires_at = (
            datetime.fromisoformat(payload["expires_at"])
            if payload.get("expires_at")
            else None
        )
        return GmailCredential(
            email=payload["email"],
            google_subject=payload.get("google_subject"),
            refresh_token=payload["refresh_token"],
            access_token=payload.get("access_token"),
            expires_at=expires_at,
            scopes=list(payload.get("scopes") or []),
        )

    def write(self, credential: GmailCredential) -> None:
        self.credential_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "email": credential.email,
            "google_subject": credential.google_subject,
            "refresh_token": credential.refresh_token,
            "access_token": credential.access_token,
            "expires_at": credential.expires_at.isoformat() if credential.expires_at else None,
            "scopes": credential.scopes,
        }
        self.credential_file.write_text(self._encrypt(json.dumps(payload)))
        os.chmod(self.credential_file, 0o600)

    def delete(self) -> None:
        if self.credential_file.exists():
            self.credential_file.unlink()

    def write_auth_state(self, state: str) -> None:
        state_file = self._state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(state)
        os.chmod(state_file, 0o600)

    def consume_auth_state(self, state: str | None) -> None:
        state_file = self._state_file()
        expected = state_file.read_text() if state_file.exists() else None
        if state_file.exists():
            state_file.unlink()
        if not state or not expected or not hmac.compare_digest(state, expected):
            raise EmailContextServiceError("Gmail OAuth state is invalid or expired.")

    def _state_file(self) -> Path:
        return self.credential_file.with_suffix(".state")

    def _key(self) -> bytes:
        if self.key_file.exists():
            return base64.urlsafe_b64decode(self.key_file.read_text().encode("ascii"))
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        key = secrets.token_bytes(32)
        self.key_file.write_text(base64.urlsafe_b64encode(key).decode("ascii"))
        os.chmod(self.key_file, 0o600)
        return key

    def _encrypt(self, plaintext: str) -> str:
        key = self._key()
        nonce = secrets.token_bytes(16)
        plaintext_bytes = plaintext.encode("utf-8")
        ciphertext = _xor_stream(plaintext_bytes, key, nonce)
        mac = hmac.new(key, b"v1" + nonce + ciphertext, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(b"v1" + nonce + mac + ciphertext).decode("ascii")

    def _decrypt(self, encoded: str) -> str:
        key = self._key()
        data = base64.urlsafe_b64decode(encoded.encode("ascii"))
        if data[:2] != b"v1":
            raise EmailContextServiceError("Unsupported Gmail credential secret format.")
        nonce = data[2:18]
        mac = data[18:50]
        ciphertext = data[50:]
        expected = hmac.new(key, b"v1" + nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected):
            raise EmailContextServiceError("Gmail credential secret could not be verified.")
        return _xor_stream(ciphertext, key, nonce).decode("utf-8")


def _xor_stream(data: bytes, key: bytes, nonce: bytes) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < len(data):
        block = hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
        output.extend(block)
        counter += 1
    return bytes(value ^ output[index] for index, value in enumerate(data))


class GmailConnector:
    def __init__(self, settings: Settings, credential_store: GmailCredentialStore) -> None:
        self.settings = settings
        self.credential_store = credential_store

    def authorization_url(self, state: str) -> str:
        self._require_oauth_config()
        return f"{GMAIL_AUTH_URL}?{urlencode({
            'client_id': self.settings.gmail_client_id,
            'redirect_uri': self.settings.gmail_redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(GMAIL_SCOPES),
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state,
        })}"

    def exchange_code(self, code: str) -> GmailCredential:
        self._require_oauth_config()
        token = self._post_form(
            GMAIL_TOKEN_URL,
            {
                "code": code,
                "client_id": self.settings.gmail_client_id,
                "client_secret": self.settings.gmail_client_secret,
                "redirect_uri": self.settings.gmail_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        access_token = str(token["access_token"])
        userinfo = self._get_json(GMAIL_USERINFO_URL, access_token)
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            existing = self.credential_store.read()
            refresh_token = existing.refresh_token if existing else None
        if not refresh_token:
            raise EmailProviderError("Google did not return a refresh token.")
        credential = GmailCredential(
            email=str(userinfo["email"]),
            google_subject=str(userinfo.get("sub")) if userinfo.get("sub") else None,
            refresh_token=str(refresh_token),
            access_token=access_token,
            expires_at=_expires_at(token),
            scopes=str(token.get("scope", "")).split(),
        )
        self.credential_store.write(credential)
        return credential

    def refresh_access_token(self, credential: GmailCredential) -> GmailCredential:
        if credential.access_token and credential.expires_at:
            expires_at = _google_expiry(credential.expires_at)
            if expires_at and expires_at > datetime.now(UTC) + timedelta(seconds=60):
                return credential
        self._require_oauth_config()
        google_credential = self._google_credential(credential)
        try:
            google_credential.refresh(GoogleAuthRequest())
        except Exception as exc:
            raise EmailProviderError("Google OAuth request failed.") from exc
        refreshed = GmailCredential(
            email=credential.email,
            google_subject=credential.google_subject,
            refresh_token=credential.refresh_token,
            access_token=google_credential.token,
            expires_at=_google_expiry(google_credential.expiry),
            scopes=list(google_credential.scopes or credential.scopes),
        )
        self.credential_store.write(refreshed)
        return refreshed

    def list_labels(self, access_token: str) -> list[dict[str, Any]]:
        try:
            payload = self._service(access_token).users().labels().list(userId="me").execute()
        except HttpError as exc:
            raise EmailProviderError("Gmail API request failed.") from exc
        return list(payload.get("labels") or [])

    def list_threads(
        self,
        access_token: str,
        *,
        label_ids: list[str],
        query: str | None,
        page_token: str | None,
        page_size: int,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"maxResults": page_size}
        if query:
            params["q"] = query
        if page_token:
            params["pageToken"] = page_token
        if label_ids:
            params["labelIds"] = label_ids
        try:
            response = (
                self._service(access_token)
                .users()
                .threads()
                .list(userId="me", **params)
                .execute()
            )
        except HttpError as exc:
            raise EmailProviderError("Gmail API request failed.") from exc
        threads = [
            self.get_thread(access_token, str(item["id"]), metadata_only=True)
            for item in response.get("threads") or []
        ]
        return {
            "threads": threads,
            "nextPageToken": response.get("nextPageToken"),
            "resultSizeEstimate": response.get("resultSizeEstimate"),
        }

    def get_thread(
        self, access_token: str, thread_id: str, *, metadata_only: bool = False
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "format": "metadata" if metadata_only else "full",
            "metadataHeaders": ["From", "To", "Cc", "Subject", "Date"],
        }
        try:
            return dict(
                self._service(access_token)
                .users()
                .threads()
                .get(userId="me", id=thread_id, **params)
                .execute()
            )
        except HttpError as exc:
            raise EmailProviderError("Gmail API request failed.") from exc

    def create_label(self, access_token: str, name: str) -> dict[str, Any]:
        try:
            return dict(
                self._service(access_token)
                .users()
                .labels()
                .create(
                    userId="me",
                    body={
                        "name": name,
                        "labelListVisibility": "labelShow",
                        "messageListVisibility": "show",
                    },
                )
                .execute()
            )
        except HttpError as exc:
            raise EmailProviderError("Gmail API request failed.") from exc

    def modify_thread(
        self,
        access_token: str,
        thread_id: str,
        *,
        add_label_ids: list[str] | None = None,
        remove_label_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        try:
            return dict(
                self._service(access_token)
                .users()
                .threads()
                .modify(
                    userId="me",
                    id=thread_id,
                    body={
                        "addLabelIds": add_label_ids or [],
                        "removeLabelIds": remove_label_ids or [],
                    },
                )
                .execute()
            )
        except HttpError as exc:
            raise EmailProviderError("Gmail API request failed.") from exc

    def create_draft(
        self,
        access_token: str,
        *,
        raw_message: str,
        thread_id: str,
    ) -> dict[str, Any]:
        try:
            return dict(
                self._service(access_token)
                .users()
                .drafts()
                .create(
                    userId="me",
                    body={"message": {"raw": raw_message, "threadId": thread_id}},
                )
                .execute()
            )
        except HttpError as exc:
            raise EmailProviderError("Gmail API request failed.") from exc

    def update_draft(
        self,
        access_token: str,
        draft_id: str,
        *,
        raw_message: str,
        thread_id: str,
    ) -> dict[str, Any]:
        try:
            return dict(
                self._service(access_token)
                .users()
                .drafts()
                .update(
                    userId="me",
                    id=draft_id,
                    body={"id": draft_id, "message": {"raw": raw_message, "threadId": thread_id}},
                )
                .execute()
            )
        except HttpError as exc:
            raise EmailProviderError("Gmail API request failed.") from exc

    def send_draft(self, access_token: str, draft_id: str) -> dict[str, Any]:
        try:
            return dict(
                self._service(access_token)
                .users()
                .drafts()
                .send(userId="me", body={"id": draft_id})
                .execute()
            )
        except HttpError as exc:
            raise EmailProviderError("Gmail API request failed.") from exc

    def delete_draft(self, access_token: str, draft_id: str) -> None:
        try:
            (
                self._service(access_token)
                .users()
                .drafts()
                .delete(userId="me", id=draft_id)
                .execute()
            )
        except HttpError as exc:
            raise EmailProviderError("Gmail API request failed.") from exc

    def _google_credential(self, credential: GmailCredential) -> GoogleCredentials:
        return GoogleCredentials(
            token=credential.access_token,
            refresh_token=credential.refresh_token,
            token_uri=GMAIL_TOKEN_URL,
            client_id=self.settings.gmail_client_id,
            client_secret=self.settings.gmail_client_secret,
            scopes=credential.scopes or GMAIL_SCOPES,
            expiry=_google_client_expiry(credential.expires_at),
        )

    def _service(self, access_token: str):
        credential = GoogleCredentials(token=access_token, scopes=GMAIL_SCOPES)
        return build("gmail", "v1", credentials=credential, cache_discovery=False)

    def _require_oauth_config(self) -> None:
        if not self.settings.gmail_client_id or not self.settings.gmail_client_secret:
            raise EmailNotConfigured(
                "Gmail OAuth is not configured.",
                details={"required": ["GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET"]},
            )

    def _post_form(self, url: str, data: dict[str, object]) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=20) as client:
                response = client.post(url, data=data)
                response.raise_for_status()
                return dict(response.json())
        except httpx.HTTPError as exc:
            raise EmailProviderError("Google OAuth request failed.") from exc

    def _get_json(
        self,
        url: str,
        access_token: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=20) as client:
                response = client.get(url, headers=_auth_headers(access_token), params=params)
                response.raise_for_status()
                return dict(response.json())
        except httpx.HTTPError as exc:
            raise EmailProviderError("Google API request failed.") from exc


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _combine_gmail_queries(*queries: str | None) -> str | None:
    combined = " ".join(query.strip() for query in queries if query and query.strip())
    return combined or None


class EmailContextService:
    def __init__(
        self,
        db: Session,
        *,
        settings: Settings | None = None,
        connector: GmailConnector | None = None,
        credential_store: GmailCredentialStore | None = None,
    ) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.credential_store = credential_store or GmailCredentialStore(
            self.settings.gmail_credential_file,
            self.settings.gmail_credential_key_file,
        )
        self.connector = connector or GmailConnector(self.settings, self.credential_store)
        self.campaigns = CampaignRepository(db)
        self.deals = DealRepository(db)

    def auth_status(self) -> GmailAuthStatusResponse:
        credential = self.credential_store.read()
        if not credential:
            return GmailAuthStatusResponse(connected=False)
        try:
            credential = self.connector.refresh_access_token(credential)
        except EmailProviderError:
            return GmailAuthStatusResponse(
                connected=True,
                email=credential.email,
                google_subject=credential.google_subject,
                scopes=credential.scopes,
                expires_at=credential.expires_at,
                reconnect_required=True,
            )
        return GmailAuthStatusResponse(
            connected=True,
            email=credential.email,
            google_subject=credential.google_subject,
            scopes=credential.scopes,
            expires_at=credential.expires_at,
        )

    def start_auth(self) -> GmailAuthStartResponse:
        state = secrets.token_urlsafe(24)
        self.credential_store.write_auth_state(state)
        return GmailAuthStartResponse(authorization_url=self.connector.authorization_url(state))

    def complete_auth(self, code: str, state: str | None) -> GmailAuthStatusResponse:
        self.credential_store.consume_auth_state(state)
        credential = self.connector.exchange_code(code)
        return GmailAuthStatusResponse(
            connected=True,
            email=credential.email,
            google_subject=credential.google_subject,
            scopes=credential.scopes,
            expires_at=credential.expires_at,
        )

    def disconnect(self) -> None:
        self.credential_store.delete()

    def list_labels(self) -> GmailLabelListResponse:
        labels = self._labels()
        return GmailLabelListResponse(labels=[_label_response(label) for label in labels])

    def list_threads(
        self,
        *,
        campaign_id: str | None = None,
        deal_id: str | None = None,
        query: str | None = None,
        label: str | None = None,
        view: str | None = None,
        page_token: str | None = None,
        page_size: int = 20,
    ) -> GmailThreadListResponse:
        credential = self._credential()
        labels = self._labels(credential)
        view_query = self._view_query(view or "primary")
        label_ids = self._filter_label_ids(
            labels,
            campaign_id=campaign_id,
            deal_id=deal_id,
            label=label,
        )
        if label_ids is None:
            return GmailThreadListResponse(threads=[])
        payload = self.connector.list_threads(
            credential.access_token or "",
            label_ids=label_ids,
            query=_combine_gmail_queries(view_query, query),
            page_token=page_token,
            page_size=max(1, min(page_size, 50)),
        )
        return GmailThreadListResponse(
            threads=[self._thread_summary(thread, labels) for thread in payload["threads"]],
            next_page_token=payload.get("nextPageToken"),
            result_size_estimate=payload.get("resultSizeEstimate"),
        )

    def batch_threads(self, payload: EmailThreadBatchRequest) -> EmailThreadBatchResponse:
        thread_ids = list(dict.fromkeys(payload.thread_ids))
        if not thread_ids:
            raise EmailContextServiceError("At least one thread_id is required.")
        add_label_ids: list[str] = []
        remove_label_ids: list[str] = []
        if payload.action == "mark_read":
            remove_label_ids = ["UNREAD"]
        elif payload.action == "mark_unread":
            add_label_ids = ["UNREAD"]
        elif payload.action == "delete":
            add_label_ids = ["TRASH"]
            remove_label_ids = ["INBOX"]
        else:
            raise EmailContextServiceError(
                "Unsupported email batch action.",
                details={"action": payload.action},
            )
        credential = self._credential()
        for thread_id in thread_ids:
            self.connector.modify_thread(
                credential.access_token or "",
                thread_id,
                add_label_ids=add_label_ids,
                remove_label_ids=remove_label_ids,
            )
        return EmailThreadBatchResponse(
            thread_ids=thread_ids,
            action=payload.action,
            updated_count=len(thread_ids),
        )

    def get_thread(self, thread_id: str, *, mark_read: bool = True) -> GmailThreadDetailResponse:
        credential = self._credential()
        labels = self._labels(credential)
        thread = self.connector.get_thread(credential.access_token or "", thread_id)
        summary = self._thread_summary(thread, labels)
        if mark_read and summary.unread:
            self.connector.modify_thread(
                credential.access_token or "",
                thread_id,
                remove_label_ids=["UNREAD"],
            )
            _remove_thread_label(thread, "UNREAD")
            summary = self._thread_summary(thread, labels)
        return GmailThreadDetailResponse(
            **summary.model_dump(),
            messages=[_message_response(message) for message in thread.get("messages") or []],
        )

    def link_thread(
        self,
        thread_id: str,
        payload: EmailThreadLinkRequest,
    ) -> EmailThreadLinkResponse:
        if not payload.campaign_id and not payload.deal_id:
            raise EmailContextServiceError("A campaign_id or deal_id is required.")
        credential = self._credential()
        labels = self._labels(credential)
        add_label_ids: list[str] = []
        if payload.campaign_id:
            self._require_campaign(payload.campaign_id)
            campaign_label = self._ensure_label(labels, self._campaign_label(payload.campaign_id))
            add_label_ids.append(str(campaign_label["id"]))
        if payload.deal_id:
            deal = self._require_deal(payload.deal_id)
            if payload.campaign_id and payload.campaign_id != deal.campaign_id:
                raise EmailContextServiceError(
                    "Deal does not belong to the selected campaign.",
                    details={"campaign_id": payload.campaign_id, "deal_id": payload.deal_id},
                )
            campaign_label = self._ensure_label(labels, self._campaign_label(deal.campaign_id))
            deal_label = self._ensure_label(labels, self._deal_label(deal.id))
            add_label_ids.extend([str(campaign_label["id"]), str(deal_label["id"])])
        self.connector.modify_thread(
            credential.access_token or "",
            thread_id,
            add_label_ids=sorted(set(add_label_ids)),
        )
        return self._link_response(thread_id)

    def unlink_thread(
        self,
        thread_id: str,
        *,
        campaign_id: str | None = None,
        deal_id: str | None = None,
    ) -> EmailThreadLinkResponse:
        if not campaign_id and not deal_id:
            raise EmailContextServiceError("A campaign_id or deal_id is required.")
        credential = self._credential()
        labels = self._labels(credential)
        remove_label_ids: list[str] = []
        if deal_id:
            deal = self._require_deal(deal_id)
            deal_label = self._find_label(labels, self._deal_label(deal.id))
            if deal_label:
                remove_label_ids.append(str(deal_label["id"]))
        if campaign_id:
            self._require_campaign(campaign_id)
            campaign_label = self._find_label(labels, self._campaign_label(campaign_id))
            if campaign_label:
                remove_label_ids.append(str(campaign_label["id"]))
            for deal in self.deals.list_for_campaign(campaign_id):
                deal_label = self._find_label(labels, self._deal_label(deal.id))
                if deal_label:
                    remove_label_ids.append(str(deal_label["id"]))
        if remove_label_ids:
            self.connector.modify_thread(
                credential.access_token or "",
                thread_id,
                remove_label_ids=sorted(set(remove_label_ids)),
            )
        return self._link_response(thread_id)

    def save_reply_draft(
        self,
        thread_id: str,
        *,
        draft_id: str | None,
        reply_mode: str,
        anchor_message_id: str | None,
        to: list[EmailParticipant],
        cc: list[EmailParticipant],
        bcc: list[EmailParticipant],
        subject: str | None,
        body_html: str | None,
        body_text: str | None,
        inline_images: list[EmailDraftFile] | None = None,
        attachments: list[EmailDraftFile] | None = None,
    ) -> EmailReplyDraftResponse:
        if reply_mode not in {"reply", "reply_all"}:
            raise EmailContextServiceError(
                "Unsupported reply mode.",
                details={"reply_mode": reply_mode, "supported": ["reply", "reply_all"]},
            )
        credential = self._credential()
        thread = self.connector.get_thread(credential.access_token or "", thread_id)
        messages = _non_draft_messages(thread)
        anchor = _find_anchor_message(messages, anchor_message_id)
        if not anchor:
            raise EmailNotFound("Reply anchor message not found.", details={"thread_id": thread_id})
        anchor_headers = _headers(anchor)
        resolved_to, resolved_cc = _reply_recipients(
            anchor_headers,
            reply_mode=reply_mode,
            account_email=credential.email,
        )
        final_to = _dedupe_participants(to) or resolved_to
        final_cc = _dedupe_participants(cc) or (resolved_cc if reply_mode == "reply_all" else [])
        final_bcc = _dedupe_participants(bcc)
        if not final_to:
            raise EmailContextServiceError("At least one reply recipient is required.")
        final_subject = _reply_subject(subject or anchor_headers.get("subject") or "")
        all_files = [*(inline_images or []), *(attachments or [])]
        total_bytes = sum(len(item.content) for item in all_files)
        if total_bytes > MAX_DRAFT_UPLOAD_BYTES:
            raise EmailContextServiceError(
                "Reply draft attachments are too large.",
                details={"max_bytes": MAX_DRAFT_UPLOAD_BYTES, "actual_bytes": total_bytes},
            )
        raw_message = _build_reply_mime(
            from_participant=EmailParticipant(email=credential.email),
            to=final_to,
            cc=final_cc,
            bcc=final_bcc,
            subject=final_subject,
            body_html=body_html,
            body_text=body_text,
            in_reply_to=anchor_headers.get("message-id"),
            references=_reply_references(anchor_headers),
            inline_images=inline_images or [],
            attachments=attachments or [],
        )
        if draft_id:
            draft = self.connector.update_draft(
                credential.access_token or "",
                draft_id,
                raw_message=raw_message,
                thread_id=thread_id,
            )
        else:
            draft = self.connector.create_draft(
                credential.access_token or "",
                raw_message=raw_message,
                thread_id=thread_id,
            )
        draft_message = draft.get("message") or {}
        return EmailReplyDraftResponse(
            draft_id=str(draft.get("id") or draft_id or ""),
            message_id=str(draft_message["id"]) if draft_message.get("id") else None,
            thread_id=thread_id,
            to=final_to,
            cc=final_cc,
            bcc=final_bcc,
            subject=final_subject,
        )

    def send_draft(self, draft_id: str) -> EmailDraftSendResponse:
        credential = self._credential()
        message = self.connector.send_draft(credential.access_token or "", draft_id)
        return EmailDraftSendResponse(
            draft_id=draft_id,
            message_id=str(message["id"]) if message.get("id") else None,
            thread_id=str(message["threadId"]) if message.get("threadId") else None,
        )

    def delete_draft(self, draft_id: str) -> None:
        credential = self._credential()
        self.connector.delete_draft(credential.access_token or "", draft_id)

    def _link_response(self, thread_id: str) -> EmailThreadLinkResponse:
        detail = self.get_thread(thread_id)
        return EmailThreadLinkResponse(thread_id=thread_id, links=detail.crm_links)

    def _credential(self) -> GmailCredential:
        credential = self.credential_store.read()
        if not credential:
            raise EmailNotConnected("Gmail is not connected.")
        try:
            return self.connector.refresh_access_token(credential)
        except EmailProviderError as exc:
            raise EmailReconnectRequired(
                "Gmail authorization expired or failed. Sign in with Google again.",
                details={"email": credential.email},
            ) from exc

    def _labels(self, credential: GmailCredential | None = None) -> list[dict[str, Any]]:
        credential = credential or self._credential()
        return self.connector.list_labels(credential.access_token or "")

    def _filter_label_ids(
        self,
        labels: list[dict[str, Any]],
        *,
        campaign_id: str | None,
        deal_id: str | None,
        label: str | None,
    ) -> list[str] | None:
        filter_label_ids: list[str] = []
        if deal_id:
            self._require_deal(deal_id)
            deal_label = self._find_label(labels, self._deal_label(deal_id))
            if not deal_label:
                return None
            filter_label_ids.append(str(deal_label["id"]))
        elif campaign_id:
            self._require_campaign(campaign_id)
            campaign_label = self._find_label(labels, self._campaign_label(campaign_id))
            if not campaign_label:
                return None
            filter_label_ids.append(str(campaign_label["id"]))
        elif label:
            requested = self._find_label(labels, label)
            if not requested:
                return None
            filter_label_ids.append(str(requested["id"]))
        return sorted(set(filter_label_ids))

    def _view_query(self, view: str) -> str:
        normalized = view.strip().lower()
        if normalized not in EMAIL_VIEW_QUERIES:
            raise EmailContextServiceError(
                "Unsupported email view.",
                details={"view": view, "supported": list(EMAIL_VIEW_QUERIES)},
            )
        return EMAIL_VIEW_QUERIES[normalized]

    def _thread_summary(
        self,
        thread: dict[str, Any],
        labels: list[dict[str, Any]],
    ) -> GmailThreadSummary:
        messages = list(thread.get("messages") or [])
        label_lookup = {str(label["id"]): label for label in labels}
        label_ids = sorted({item for message in messages for item in message.get("labelIds") or []})
        first_headers = _headers(messages[0]) if messages else {}
        last_message = messages[-1] if messages else {}
        crm_links = [
            link
            for label_id in label_ids
            if label_id in label_lookup
            for link in [self._crm_link(label_lookup[label_id])]
            if link is not None
        ]
        return GmailThreadSummary(
            id=str(thread["id"]),
            subject=first_headers.get("subject"),
            snippet=thread.get("snippet") or last_message.get("snippet"),
            unread="UNREAD" in label_ids,
            participants=_participants_from_messages(messages),
            last_message_at=_message_datetime(last_message),
            message_count=len(messages),
            labels=[
                _label_response(label_lookup[label_id])
                for label_id in label_ids
                if label_id in label_lookup
            ],
            crm_links=crm_links,
        )

    def _ensure_label(self, labels: list[dict[str, Any]], name: str) -> dict[str, Any]:
        existing = self._find_label(labels, name)
        if existing:
            return existing
        credential = self._credential()
        created = self.connector.create_label(credential.access_token or "", name)
        labels.append(created)
        return created

    def _find_label(self, labels: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
        for label in labels:
            if label.get("name") == name or label.get("id") == name:
                return label
        return None

    def _campaign_label(self, campaign_id: str) -> str:
        campaign = self._require_campaign(campaign_id)
        return f"{CRM_LABEL_ROOT}/Campaigns/{campaign.name}"

    def _deal_label(self, deal_id: str) -> str:
        return f"{CRM_LABEL_ROOT}/Deals/{deal_id}"

    def _require_campaign(self, campaign_id: str):
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise EmailNotFound("Campaign not found.", details={"campaign_id": campaign_id})
        return campaign

    def _require_deal(self, deal_id: str):
        deal = self.deals.get_detail(deal_id)
        if not deal:
            raise EmailNotFound("Deal not found.", details={"deal_id": deal_id})
        return deal

    def _crm_link(self, label: dict[str, Any]) -> EmailCrmLink | None:
        label_id = str(label["id"])
        name = str(label.get("name", ""))
        campaign_prefix = f"{CRM_LABEL_ROOT}/Campaigns/"
        deal_prefix = f"{CRM_LABEL_ROOT}/Deals/"
        if name.startswith(campaign_prefix):
            label_value = name.removeprefix(campaign_prefix)
            campaign = self.campaigns.get(label_value) or self.campaigns.find_by_name(label_value)
            return EmailCrmLink(
                type="campaign",
                label_id=label_id,
                label_name=name,
                campaign_id=campaign.id if campaign else None,
                campaign_name=campaign.name if campaign else label_value,
            )
        if name.startswith(deal_prefix):
            deal_id = name.removeprefix(deal_prefix)
            deal = self.deals.get_detail(deal_id)
            return EmailCrmLink(
                type="deal",
                label_id=label_id,
                label_name=name,
                campaign_id=deal.campaign_id if deal else None,
                campaign_name=deal.campaign.name if deal and deal.campaign else None,
                deal_id=deal_id,
                deal_influencer_name=(
                    deal.influencer.display_name if deal and deal.influencer else None
                ),
            )
        return None


def _expires_at(token: dict[str, Any]) -> datetime | None:
    expires_in = token.get("expires_in")
    if not expires_in:
        return None
    return datetime.now(UTC) + timedelta(seconds=int(expires_in))


def _google_client_expiry(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def _google_expiry(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo:
        return value.astimezone(UTC)
    return value.replace(tzinfo=UTC)


def _label_response(label: dict[str, Any]) -> GmailLabelResponse:
    return GmailLabelResponse(
        id=str(label["id"]),
        name=str(label["name"]),
        type=str(label.get("type")) if label.get("type") else None,
    )


def _remove_thread_label(thread: dict[str, Any], label_id: str) -> None:
    for message in thread.get("messages") or []:
        label_ids = [item for item in message.get("labelIds") or [] if item != label_id]
        message["labelIds"] = label_ids


def _headers(message: dict[str, Any]) -> dict[str, str]:
    headers = message.get("payload", {}).get("headers") or []
    return {str(item.get("name", "")).lower(): str(item.get("value", "")) for item in headers}


def _participants_from_messages(messages: list[dict[str, Any]]) -> list[EmailParticipant]:
    seen: set[str] = set()
    participants: list[EmailParticipant] = []
    for message in messages:
        headers = _headers(message)
        for header in ("from", "to", "cc"):
            for name, email in getaddresses([headers.get(header, "")]):
                if not email or email.lower() in seen:
                    continue
                seen.add(email.lower())
                participants.append(EmailParticipant(name=name or None, email=email))
    return participants


def _message_response(message: dict[str, Any]) -> GmailMessageResponse:
    headers = _headers(message)
    senders = _participants(headers.get("from"))
    sender = senders[0] if senders else None
    body = _message_body(message.get("payload") or {})
    return GmailMessageResponse(
        id=str(message["id"]),
        rfc_message_id=headers.get("message-id"),
        references=headers.get("references"),
        sender=sender,
        to=_participants(headers.get("to")),
        cc=_participants(headers.get("cc")),
        sent_at=_message_datetime(message),
        snippet=message.get("snippet"),
        body_text=body.get("text"),
        body_html=body.get("html"),
    )


def _participants(value: str | None) -> list[EmailParticipant]:
    return [
        EmailParticipant(name=name or None, email=email)
        for name, email in getaddresses([value or ""])
        if email
    ]


def _dedupe_participants(participants: list[EmailParticipant]) -> list[EmailParticipant]:
    seen: set[str] = set()
    deduped: list[EmailParticipant] = []
    for participant in participants:
        email = (participant.email or "").strip()
        if not email or email.lower() in seen:
            continue
        seen.add(email.lower())
        deduped.append(EmailParticipant(name=participant.name, email=email))
    return deduped


def _non_draft_messages(thread: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        message
        for message in thread.get("messages") or []
        if "DRAFT" not in set(message.get("labelIds") or [])
    ]


def _find_anchor_message(
    messages: list[dict[str, Any]],
    anchor_message_id: str | None,
) -> dict[str, Any] | None:
    if anchor_message_id:
        return next(
            (message for message in messages if str(message.get("id")) == anchor_message_id),
            None,
        )
    return messages[-1] if messages else None


def _reply_recipients(
    headers: dict[str, str],
    *,
    reply_mode: str,
    account_email: str,
) -> tuple[list[EmailParticipant], list[EmailParticipant]]:
    excluded = {account_email.lower()}
    sender = _participants(headers.get("reply-to") or headers.get("from"))
    to = _exclude_participants(sender, excluded)
    if reply_mode != "reply_all":
        return to, []
    cc_candidates = [*sender, *_participants(headers.get("to")), *_participants(headers.get("cc"))]
    recipients = _exclude_participants(cc_candidates, excluded)
    return recipients[:1] or recipients, recipients[1:]


def _exclude_participants(
    participants: list[EmailParticipant],
    excluded: set[str],
) -> list[EmailParticipant]:
    return [
        participant
        for participant in _dedupe_participants(participants)
        if participant.email and participant.email.lower() not in excluded
    ]


def _reply_subject(subject: str) -> str:
    stripped = subject.strip()
    if not stripped:
        return "Re:"
    return stripped if stripped.lower().startswith("re:") else f"Re: {stripped}"


def _reply_references(headers: dict[str, str]) -> str | None:
    references = headers.get("references", "").strip()
    message_id = headers.get("message-id", "").strip()
    if references and message_id and message_id not in references:
        return f"{references} {message_id}"
    return references or message_id or None


def _format_address(participant: EmailParticipant) -> str:
    email = participant.email or ""
    return formataddr((participant.name or "", email)) if participant.name else email


def _set_reply_headers(
    message: EmailMessage,
    *,
    from_participant: EmailParticipant,
    to: list[EmailParticipant],
    cc: list[EmailParticipant],
    bcc: list[EmailParticipant],
    subject: str,
    in_reply_to: str | None,
    references: str | None,
) -> None:
    message["From"] = _format_address(from_participant)
    message["To"] = ", ".join(_format_address(participant) for participant in to)
    if cc:
        message["Cc"] = ", ".join(_format_address(participant) for participant in cc)
    if bcc:
        message["Bcc"] = ", ".join(_format_address(participant) for participant in bcc)
    message["Subject"] = subject
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
    if references:
        message["References"] = references


def _build_reply_mime(
    *,
    from_participant: EmailParticipant,
    to: list[EmailParticipant],
    cc: list[EmailParticipant],
    bcc: list[EmailParticipant],
    subject: str,
    body_html: str | None,
    body_text: str | None,
    in_reply_to: str | None,
    references: str | None,
    inline_images: list[EmailDraftFile],
    attachments: list[EmailDraftFile],
) -> str:
    text = body_text or _plain_text_from_html(body_html or "")
    html = _sanitize_reply_html(body_html or text.replace("\n", "<br>"))

    alternative = EmailMessage()
    alternative.set_content(text or " ")
    alternative.add_alternative(html or " ", subtype="html")

    body_part: EmailMessage = alternative
    if inline_images:
        related = EmailMessage()
        related.make_related()
        related.attach(alternative)
        for image in inline_images:
            maintype, subtype = _content_type_parts(image.content_type)
            part = EmailMessage()
            part.set_content(image.content, maintype=maintype, subtype=subtype)
            part.add_header("Content-ID", f"<{image.cid}>")
            part.add_header("Content-Disposition", "inline", filename=image.filename)
            related.attach(part)
        body_part = related

    if attachments:
        root = EmailMessage()
        _set_reply_headers(
            root,
            from_participant=from_participant,
            to=to,
            cc=cc,
            bcc=bcc,
            subject=subject,
            in_reply_to=in_reply_to,
            references=references,
        )
        root.make_mixed()
        root.attach(body_part)
        for attachment in attachments:
            maintype, subtype = _content_type_parts(attachment.content_type)
            root.add_attachment(
                attachment.content,
                maintype=maintype,
                subtype=subtype,
                filename=attachment.filename,
            )
        message = root
    else:
        message = body_part
        _set_reply_headers(
            message,
            from_participant=from_participant,
            to=to,
            cc=cc,
            bcc=bcc,
            subject=subject,
            in_reply_to=in_reply_to,
            references=references,
        )
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")


def _content_type_parts(content_type: str | None) -> tuple[str, str]:
    if content_type and "/" in content_type:
        maintype, subtype = content_type.split("/", 1)
        return maintype or "application", subtype or "octet-stream"
    return "application", "octet-stream"


def _sanitize_reply_html(html: str) -> str:
    return bleach.clean(
        html,
        tags=ALLOWED_REPLY_HTML_TAGS,
        attributes=ALLOWED_REPLY_HTML_ATTRIBUTES,
        protocols=["http", "https", "mailto", "cid"],
        strip=True,
    )


def _plain_text_from_html(html: str) -> str:
    stripped = bleach.clean(html, tags=[], strip=True)
    return stripped.replace("\xa0", " ").strip()


def _message_datetime(message: dict[str, Any]) -> datetime | None:
    headers = _headers(message)
    if headers.get("date"):
        try:
            parsed = parsedate_to_datetime(headers["date"])
            return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except (TypeError, ValueError):
            pass
    internal_date = message.get("internalDate")
    if internal_date:
        return datetime.fromtimestamp(int(internal_date) / 1000, tz=UTC)
    return None


def _message_body(payload: dict[str, Any]) -> dict[str, str | None]:
    found: dict[str, str | None] = {"text": None, "html": None}

    def walk(part: dict[str, Any]) -> None:
        mime_type = part.get("mimeType")
        data = part.get("body", {}).get("data")
        if data and mime_type in {"text/plain", "text/html"}:
            decoded = _decode_body(str(data))
            if mime_type == "text/plain" and found["text"] is None:
                found["text"] = decoded
            if mime_type == "text/html" and found["html"] is None:
                found["html"] = decoded
        for child in part.get("parts") or []:
            walk(child)

    walk(payload)
    return found


def _decode_body(data: str) -> str:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}".encode("ascii")).decode(
        "utf-8",
        errors="replace",
    )
