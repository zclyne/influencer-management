import csv
from io import StringIO

from sqlalchemy.orm import Session

from app.db import models
from app.enums import CompensationItemType
from app.repositories.sqlalchemy import CampaignRepository, DealRepository
from app.schemas.campaign_exports import CampaignExportFilters

EXPORT_COLUMNS = [
    "campaign_name",
    "brand_names",
    "deal_status",
    "lost_reason",
    "influencer_display_name",
    "influencer_country",
    "influencer_city",
    "primary_platform",
    "primary_profile_url",
    "follower_count",
    "primary_contact_email",
    "deliverables_summary",
    "compensation_summary",
    "cash_total",
    "reimbursement_total",
    "internal_notes",
    "updated_at",
]

REIMBURSEMENT_TYPES = {
    CompensationItemType.FLIGHT_REIMBURSEMENT.value,
    CompensationItemType.HOTEL_REIMBURSEMENT.value,
    CompensationItemType.LOCAL_TRANSPORT_REIMBURSEMENT.value,
    CompensationItemType.MEAL_OR_PER_DIEM.value,
}


class ExportServiceError(Exception):
    code = "export_error"
    status_code = 422

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ExportCampaignNotFound(ExportServiceError):
    code = "not_found"
    status_code = 404


class CampaignExportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.campaigns = CampaignRepository(db)
        self.deals = DealRepository(db)

    def export_campaign_csv(self, campaign_id: str, filters: CampaignExportFilters) -> str:
        campaign = self.campaigns.get_with_brands(campaign_id)
        if not campaign:
            raise ExportCampaignNotFound(
                "Campaign not found.", details={"campaign_id": campaign_id}
            )
        deals = self.deals.list_for_campaign_with_graph(
            campaign_id,
            status=filters.status.value if filters.status else None,
            platform=filters.platform,
            lost_reason=filters.lost_reason,
            include_archived=filters.include_archived,
            deal_ids=filters.deal_ids or None,
        )
        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=EXPORT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for deal in deals:
            writer.writerow(self._row(campaign, deal))
        return buffer.getvalue()

    def _row(self, campaign: models.Campaign, deal: models.Deal) -> dict[str, object]:
        platform = self._primary_platform(deal.influencer.platforms)
        contact = self._primary_contact(deal.influencer.contacts)
        cash_total = sum(
            float(item.amount or 0)
            for item in deal.compensation_items
            if item.type == CompensationItemType.CASH_STIPEND.value
        )
        reimbursement_total = sum(
            float(item.amount or 0)
            for item in deal.compensation_items
            if item.type in REIMBURSEMENT_TYPES
        )
        return {
            "campaign_name": campaign.name,
            "brand_names": "; ".join(link.brand.name for link in campaign.brand_links),
            "deal_status": deal.status,
            "lost_reason": deal.lost_reason or "",
            "influencer_display_name": deal.influencer.display_name,
            "influencer_country": deal.influencer.country or "",
            "influencer_city": deal.influencer.city or "",
            "primary_platform": platform.platform if platform else "",
            "primary_profile_url": platform.profile_url if platform else "",
            "follower_count": (
                platform.follower_count if platform and platform.follower_count else ""
            ),
            "primary_contact_email": contact.email if contact else "",
            "deliverables_summary": self._deliverables_summary(deal.deliverables),
            "compensation_summary": self._compensation_summary(deal.compensation_items),
            "cash_total": f"{cash_total:.2f}",
            "reimbursement_total": f"{reimbursement_total:.2f}",
            "internal_notes": deal.internal_notes or "",
            "updated_at": deal.updated_at.isoformat(),
        }

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
                amount = f" {item.amount:.2f} {item.currency or ''}".rstrip()
            description = f": {item.description}" if item.description else ""
            parts.append(f"{item.type}{amount}{description}")
        return "; ".join(parts)
