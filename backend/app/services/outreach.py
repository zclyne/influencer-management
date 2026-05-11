import re
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db import models
from app.enums import CompensationItemType, DealStatus, TemplateType
from app.repositories.sqlalchemy import (
    CampaignRepository,
    DealRepository,
    TemplateRepository,
)
from app.schemas.outreach import (
    BulkOutreachDraftRequest,
    BulkOutreachDraftResponse,
    OutreachDraftRequest,
    OutreachDraftResponse,
)

VARIABLE_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*}}")
LATER_STATUSES = {
    DealStatus.ACTIVE.value,
    DealStatus.COMPLETED.value,
    DealStatus.LOST.value,
}


class OutreachServiceError(Exception):
    code = "outreach_error"
    status_code = 422

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class OutreachNotFound(OutreachServiceError):
    code = "not_found"
    status_code = 404


class TemplateRenderError(OutreachServiceError):
    code = "template_render_error"
    status_code = 422


@dataclass(frozen=True)
class RenderContext:
    values: dict[str, str]
    warnings: list[str]


class OutreachService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.templates = TemplateRepository(db)
        self.deals = DealRepository(db)
        self.campaigns = CampaignRepository(db)

    def render_deal_draft(
        self, deal_id: str, payload: OutreachDraftRequest
    ) -> OutreachDraftResponse:
        template = self._require_template(payload.template_id)
        deal = self._require_deal(deal_id)
        return self._render_draft(deal, template)

    def render_campaign_drafts(
        self, campaign_id: str, payload: BulkOutreachDraftRequest
    ) -> BulkOutreachDraftResponse:
        if not self.campaigns.get(campaign_id):
            raise OutreachNotFound("Campaign not found.", details={"campaign_id": campaign_id})
        template = self._require_template(payload.template_id)
        deals = self.deals.list_for_campaign_with_graph(
            campaign_id, deal_ids=payload.deal_ids or None
        )
        return BulkOutreachDraftResponse(
            drafts=[self._render_draft(deal, template) for deal in deals]
        )

    def confirm_sent(self, deal_id: str) -> OutreachDraftResponse:
        deal = self._require_deal(deal_id)
        if deal.status not in LATER_STATUSES:
            self.deals.update(deal, status=DealStatus.ACTIVE.value)
            self.db.commit()
        return OutreachDraftResponse(
            deal_id=deal.id,
            template_id="",
            subject="",
            body="",
            to_email=self._primary_contact(deal.influencer.contacts).email
            if self._primary_contact(deal.influencer.contacts)
            else None,
            warnings=[],
        )

    def _render_draft(
        self, deal: models.Deal, template: models.Template
    ) -> OutreachDraftResponse:
        context = self._build_context(deal)
        subject = self._render_template(template.subject_template, context.values)
        body = self._render_template(template.body_template, context.values)
        contact = self._primary_contact(deal.influencer.contacts)
        return OutreachDraftResponse(
            deal_id=deal.id,
            template_id=template.id,
            subject=subject,
            body=body,
            to_email=contact.email if contact else None,
            warnings=context.warnings,
        )

    def _render_template(self, template: str, values: dict[str, str]) -> str:
        rendered_variables = {match.group(1) for match in VARIABLE_RE.finditer(template)}
        unknown = sorted(rendered_variables - values.keys())
        if unknown:
            raise TemplateRenderError(
                "Template contains unknown variables.", details={"unknown_variables": unknown}
            )

        def replace(match: re.Match[str]) -> str:
            return values[match.group(1)]

        return VARIABLE_RE.sub(replace, template)

    def _build_context(self, deal: models.Deal) -> RenderContext:
        campaign = deal.campaign
        influencer = deal.influencer
        platform = self._primary_platform(influencer.platforms)
        contact = self._primary_contact(influencer.contacts)
        warnings: list[str] = []
        if not contact:
            warnings.append("No primary contact email is available.")
        if not platform:
            warnings.append("No platform profile is available.")
        values = {
            "campaign.name": campaign.name if campaign else "",
            "campaign.start_date": campaign.start_date.isoformat()
            if campaign and campaign.start_date
            else "",
            "campaign.end_date": campaign.end_date.isoformat()
            if campaign and campaign.end_date
            else "",
            "campaign.brand_names": "; ".join(link.brand.name for link in campaign.brand_links)
            if campaign
            else "",
            "influencer.display_name": influencer.display_name,
            "influencer.full_name": influencer.full_name or "",
            "contact.name": contact.name if contact and contact.name else "",
            "contact.email": contact.email if contact else "",
            "primary_platform.platform": platform.platform if platform else "",
            "primary_platform.url": (
                platform.profile_url if platform and platform.profile_url else ""
            ),
            "deal.internal_notes": deal.internal_notes or "",
            "deliverables.summary": self._deliverables_summary(deal.deliverables),
            "compensation.summary": self._compensation_summary(deal.compensation_items),
        }
        return RenderContext(values=values, warnings=warnings)

    def _require_template(self, template_id: str) -> models.Template:
        template = self.templates.get(template_id)
        if not template:
            raise OutreachNotFound(
                "Template not found.", details={"template_id": template_id}
            )
        if template.type != TemplateType.OUTREACH_EMAIL.value:
            raise TemplateRenderError(
                "Template is not an outreach email template.",
                details={"template_id": template_id, "template_type": template.type},
            )
        return template

    def _require_deal(self, deal_id: str) -> models.Deal:
        deal = self.deals.get_detail(deal_id)
        if not deal:
            raise OutreachNotFound("Deal not found.", details={"deal_id": deal_id})
        return deal

    def _primary_platform(
        self, platforms: list[models.InfluencerPlatform]
    ) -> models.InfluencerPlatform | None:
        if not platforms:
            return None
        return sorted(platforms, key=lambda item: item.follower_count or 0, reverse=True)[0]

    def _primary_contact(
        self, contacts: list[models.InfluencerContact]
    ) -> models.InfluencerContact | None:
        if not contacts:
            return None
        return sorted(contacts, key=lambda item: (not item.is_primary, item.created_at))[0]

    def _deliverables_summary(self, deliverables: list[models.Deliverable]) -> str:
        return "; ".join(
            f"{item.quantity}x {item.type} ({item.status})" for item in deliverables
        )

    def _compensation_summary(self, items: list[models.CompensationItem]) -> str:
        parts: list[str] = []
        for item in items:
            amount = ""
            if item.amount is not None:
                amount = f" {Decimal(item.amount):.2f} {item.currency or ''}".rstrip()
            label = item.description or item.type
            if item.type == CompensationItemType.CASH_STIPEND.value:
                label = f"cash stipend{amount}"
            elif amount:
                label = f"{label}{amount}"
            parts.append(label)
        return "; ".join(parts)
