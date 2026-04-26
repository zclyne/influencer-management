from decimal import Decimal

from sqlalchemy.orm import Session

from app.db import models
from app.enums import DealStatus, EmailLinkType
from app.repositories.sqlalchemy import (
    CampaignRepository,
    DealRepository,
    EmailThreadLinkRepository,
    EmailThreadMetadataRepository,
    InfluencerContactRepository,
    InfluencerRepository,
)
from app.schemas.email_context import (
    EmailParticipant,
    EmailThreadCandidate,
    EmailThreadLinkCreateRequest,
    EmailThreadLinkListResponse,
    EmailThreadLinkResponse,
    EmailThreadLinkUpdateRequest,
    EmailThreadListResponse,
    EmailThreadMatchRequest,
    EmailThreadMatchResponse,
    EmailThreadMetadataResponse,
    ScopedEmailThreadListResponse,
    ScopedEmailThreadResponse,
)


class EmailContextServiceError(Exception):
    code = "email_context_error"
    status_code = 422

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class EmailContextNotFound(EmailContextServiceError):
    code = "not_found"
    status_code = 404


class EmailContextValidationError(EmailContextServiceError):
    code = "invalid_email_context_link"
    status_code = 422


class EmailContextService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.links = EmailThreadLinkRepository(db)
        self.thread_metadata = EmailThreadMetadataRepository(db)
        self.contacts = InfluencerContactRepository(db)
        self.influencers = InfluencerRepository(db)
        self.campaigns = CampaignRepository(db)
        self.deals = DealRepository(db)

    def list_threads(self, *, provider: str | None = None) -> EmailThreadListResponse:
        return EmailThreadListResponse(
            threads=[
                self._thread_response(thread)
                for thread in self.thread_metadata.list(provider=provider)
            ]
        )

    def get_thread(self, provider: str, external_thread_id: str) -> EmailThreadMetadataResponse:
        thread = self.thread_metadata.get_by_thread(provider, external_thread_id)
        if not thread:
            raise EmailContextNotFound(
                "Email thread not found.",
                details={"provider": provider, "external_thread_id": external_thread_id},
            )
        return self._thread_response(thread)

    def match_thread(self, payload: EmailThreadMatchRequest) -> EmailThreadMatchResponse:
        inherited = self.links.list_manual_for_thread(
            payload.provider, payload.external_thread_id
        )
        if inherited:
            return EmailThreadMatchResponse(
                provider=payload.provider,
                external_thread_id=payload.external_thread_id,
                candidates=[
                    EmailThreadCandidate(
                        type=EmailLinkType.INHERITED_FROM_THREAD.value,
                        confidence=Decimal("1.000"),
                        influencer_id=link.influencer_id,
                        campaign_id=link.campaign_id,
                        deal_id=link.deal_id,
                        contact_id=link.contact_id,
                        link_id=link.id,
                        reason="Thread already has a manual link.",
                    )
                    for link in inherited
                ],
            )

        participants = payload.participants or self._participants_from_metadata(
            payload.provider, payload.external_thread_id
        )
        contacts_by_influencer: dict[str, list[models.InfluencerContact]] = {}
        for participant in participants:
            for contact in self.contacts.find_by_email(participant.email):
                contacts_by_influencer.setdefault(contact.influencer_id, []).append(contact)

        candidates: list[EmailThreadCandidate] = []
        if len(contacts_by_influencer) > 1:
            for influencer_id, contacts in contacts_by_influencer.items():
                candidates.append(
                    EmailThreadCandidate(
                        type="conflict",
                        confidence=Decimal("0.500"),
                        influencer_id=influencer_id,
                        contact_id=contacts[0].id,
                        reason="Participant email matches contacts on multiple influencers.",
                    )
                )
            return EmailThreadMatchResponse(
                provider=payload.provider,
                external_thread_id=payload.external_thread_id,
                candidates=candidates,
            )

        if len(contacts_by_influencer) == 1:
            influencer_id, contacts = next(iter(contacts_by_influencer.items()))
            contact = contacts[0]
            candidates.append(
                EmailThreadCandidate(
                    type=EmailLinkType.INFERRED_FROM_CONTACT.value,
                    confidence=Decimal("0.950"),
                    influencer_id=influencer_id,
                    contact_id=contact.id,
                    reason="Participant email matches a known influencer contact.",
                )
            )
            for deal in self.deals.list_for_influencer(influencer_id):
                candidates.append(
                    EmailThreadCandidate(
                        type="deal_candidate",
                        confidence=Decimal("0.850"),
                        influencer_id=influencer_id,
                        campaign_id=deal.campaign_id,
                        deal_id=deal.id,
                        contact_id=contact.id,
                        reason="Known contact belongs to an influencer with this deal.",
                        suggested_status=self._status_hint(
                            deal, message_count=payload.message_count
                        ),
                    )
                )
        return EmailThreadMatchResponse(
            provider=payload.provider,
            external_thread_id=payload.external_thread_id,
            candidates=candidates,
        )

    def list_links(
        self,
        *,
        provider: str | None = None,
        external_thread_id: str | None = None,
        deal_id: str | None = None,
        influencer_id: str | None = None,
    ) -> EmailThreadLinkListResponse:
        return EmailThreadLinkListResponse(
            links=[
                self._link_response(link)
                for link in self.links.list(
                    provider=provider,
                    external_thread_id=external_thread_id,
                    deal_id=deal_id,
                    influencer_id=influencer_id,
                )
            ]
        )

    def create_link(self, payload: EmailThreadLinkCreateRequest) -> EmailThreadLinkResponse:
        values = self._validated_link_values(payload.model_dump())
        link = self.links.create(
            provider=payload.provider,
            external_thread_id=payload.external_thread_id,
            external_message_id=payload.external_message_id,
            link_type=EmailLinkType.MANUAL.value,
            confidence=Decimal("1.000"),
            **values,
        )
        self.db.commit()
        return self._link_response(link)

    def update_link(
        self, link_id: str, payload: EmailThreadLinkUpdateRequest
    ) -> EmailThreadLinkResponse:
        link = self._require_link(link_id)
        values = self._validated_link_values(
            payload.model_dump(exclude_unset=True),
            existing=link,
        )
        if values:
            link = self.links.update(link, **values)
            self.db.commit()
        return self._link_response(link)

    def delete_link(self, link_id: str) -> None:
        link = self._require_link(link_id)
        self.links.delete(link)
        self.db.commit()

    def list_deal_threads(self, deal_id: str) -> ScopedEmailThreadListResponse:
        if not self.deals.get(deal_id):
            raise EmailContextNotFound("Deal not found.", details={"deal_id": deal_id})
        return self._scoped_threads(self.links.list(deal_id=deal_id))

    def list_influencer_threads(self, influencer_id: str) -> ScopedEmailThreadListResponse:
        if not self.influencers.get(influencer_id):
            raise EmailContextNotFound(
                "Influencer not found.", details={"influencer_id": influencer_id}
            )
        return self._scoped_threads(self.links.list(influencer_id=influencer_id))

    def _validated_link_values(
        self,
        values: dict[str, object],
        *,
        existing: models.EmailThreadLink | None = None,
    ) -> dict[str, object]:
        merged = {
            "influencer_id": existing.influencer_id if existing else None,
            "campaign_id": existing.campaign_id if existing else None,
            "deal_id": existing.deal_id if existing else None,
            "contact_id": existing.contact_id if existing else None,
            "linked_by": existing.linked_by if existing else None,
        }
        merged.update({key: value for key, value in values.items() if key in merged})
        deal_id = merged.get("deal_id")
        if deal_id:
            deal = self.deals.get(str(deal_id))
            if not deal:
                raise EmailContextNotFound("Deal not found.", details={"deal_id": deal_id})
            if merged.get("campaign_id") and merged["campaign_id"] != deal.campaign_id:
                raise EmailContextValidationError(
                    "Deal does not belong to the provided campaign.",
                    details={"deal_id": deal.id, "campaign_id": merged["campaign_id"]},
                )
            if merged.get("influencer_id") and merged["influencer_id"] != deal.influencer_id:
                raise EmailContextValidationError(
                    "Deal does not belong to the provided influencer.",
                    details={"deal_id": deal.id, "influencer_id": merged["influencer_id"]},
                )
            merged["campaign_id"] = deal.campaign_id
            merged["influencer_id"] = deal.influencer_id
        if merged.get("campaign_id") and not self.campaigns.get(str(merged["campaign_id"])):
            raise EmailContextNotFound(
                "Campaign not found.", details={"campaign_id": merged["campaign_id"]}
            )
        if merged.get("influencer_id") and not self.influencers.get(str(merged["influencer_id"])):
            raise EmailContextNotFound(
                "Influencer not found.", details={"influencer_id": merged["influencer_id"]}
            )
        if merged.get("contact_id"):
            contact = self.contacts.get(str(merged["contact_id"]))
            if not contact:
                raise EmailContextNotFound(
                    "Influencer contact not found.", details={"contact_id": merged["contact_id"]}
                )
            if merged.get("influencer_id") and contact.influencer_id != merged["influencer_id"]:
                raise EmailContextValidationError(
                    "Contact does not belong to the linked influencer.",
                    details={
                        "contact_id": contact.id,
                        "influencer_id": merged["influencer_id"],
                    },
                )
        target_keys = ("influencer_id", "campaign_id", "deal_id", "contact_id")
        if not any(merged.get(key) for key in target_keys):
            raise EmailContextValidationError(
                "Email thread link must target an influencer, campaign, deal, or contact."
            )
        return merged

    def _participants_from_metadata(
        self, provider: str, external_thread_id: str
    ) -> list[EmailParticipant]:
        thread = self.thread_metadata.get_by_thread(provider, external_thread_id)
        if not thread:
            return []
        return [
            EmailParticipant(email=str(item.get("email", "")), name=item.get("name"))
            for item in thread.participants_json or []
            if item.get("email")
        ]

    def _status_hint(self, deal: models.Deal, *, message_count: int | None) -> str | None:
        if deal.status == DealStatus.OUTREACHED.value and (message_count or 0) > 1:
            return DealStatus.RESPONDED.value
        return None

    def _require_link(self, link_id: str) -> models.EmailThreadLink:
        link = self.links.get(link_id)
        if not link:
            raise EmailContextNotFound("Email thread link not found.", details={"link_id": link_id})
        return link

    def _scoped_threads(
        self, links: list[models.EmailThreadLink]
    ) -> ScopedEmailThreadListResponse:
        return ScopedEmailThreadListResponse(
            threads=[
                ScopedEmailThreadResponse(
                    link=self._link_response(link),
                    thread=self._optional_thread_response(
                        link.provider, link.external_thread_id
                    ),
                )
                for link in links
            ]
        )

    def _optional_thread_response(
        self, provider: str, external_thread_id: str
    ) -> EmailThreadMetadataResponse | None:
        thread = self.thread_metadata.get_by_thread(provider, external_thread_id)
        return self._thread_response(thread) if thread else None

    def _thread_response(self, thread: models.EmailThreadMetadata) -> EmailThreadMetadataResponse:
        return EmailThreadMetadataResponse(
            id=thread.id,
            provider=thread.provider,
            external_thread_id=thread.external_thread_id,
            account_id=thread.account_id,
            subject=thread.subject,
            participants=[
                EmailParticipant(email=str(item.get("email", "")), name=item.get("name"))
                for item in thread.participants_json or []
                if item.get("email")
            ],
            last_message_at=thread.last_message_at,
            snippet=thread.snippet,
            message_count=thread.message_count,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
        )

    def _link_response(self, link: models.EmailThreadLink) -> EmailThreadLinkResponse:
        return EmailThreadLinkResponse(
            id=link.id,
            provider=link.provider,
            external_thread_id=link.external_thread_id,
            external_message_id=link.external_message_id,
            influencer_id=link.influencer_id,
            campaign_id=link.campaign_id,
            deal_id=link.deal_id,
            contact_id=link.contact_id,
            link_type=EmailLinkType(link.link_type),
            confidence=link.confidence,
            linked_by=link.linked_by,
            created_at=link.created_at,
            updated_at=link.updated_at,
        )
