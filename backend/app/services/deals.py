from collections import Counter
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.db import models
from app.db.models import utc_now
from app.enums import (
    CompensationItemStatus,
    CompensationItemType,
    DealStatus,
    DeliverableStatus,
)
from app.repositories.sqlalchemy import CampaignRepository, DealRepository, InfluencerRepository
from app.schemas.deals import (
    CompensationSummary,
    DealBulkCreateRequest,
    DealBulkCreateResponse,
    DealBulkCreateRowResult,
    DealBulkUpdateRequest,
    DealBulkUpdateResponse,
    DealBulkUpdateRowResult,
    DealCreateRequest,
    DealDetailResponse,
    DealListResponse,
    DealPipelineRow,
    DealUpdateRequest,
    DeliverableSummary,
    EmailThreadSummary,
    InfluencerSummary,
    PrimaryContactSummary,
    PrimaryPlatformSummary,
)


class DealServiceError(Exception):
    code = "deal_error"
    status_code = 422

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class DealNotFound(DealServiceError):
    code = "not_found"
    status_code = 404


class CampaignNotFound(DealServiceError):
    code = "not_found"
    status_code = 404


class InfluencerNotFound(DealServiceError):
    code = "not_found"
    status_code = 404


class DealConflict(DealServiceError):
    code = "deal_conflict"
    status_code = 409


class DealService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.campaigns = CampaignRepository(db)
        self.influencers = InfluencerRepository(db)
        self.deals = DealRepository(db)

    def create_if_missing(self, campaign_id: str, influencer_id: str) -> tuple[models.Deal, bool]:
        existing = self.deals.get_by_campaign_influencer(campaign_id, influencer_id)
        if existing:
            return existing, False
        return (
            self.deals.create(
                campaign_id=campaign_id,
                influencer_id=influencer_id,
                status=DealStatus.DRAFT.value,
            ),
            True,
        )

    def exists(self, campaign_id: str, influencer_id: str) -> bool:
        return self.deals.get_by_campaign_influencer(campaign_id, influencer_id) is not None

    def create_deal(self, campaign_id: str, payload: DealCreateRequest) -> DealDetailResponse:
        self._require_campaign(campaign_id)
        influencer = self.influencers.get(payload.influencer_id)
        if not influencer or influencer.archived_at is not None:
            raise InfluencerNotFound(
                "Influencer not found.",
                details={"influencer_id": payload.influencer_id},
            )
        existing = self.deals.get_by_campaign_influencer(campaign_id, payload.influencer_id)
        if existing:
            raise DealConflict(
                "Influencer already has a deal in this campaign.",
                details={
                    "campaign_id": campaign_id,
                    "influencer_id": payload.influencer_id,
                    "deal_id": existing.id,
                },
            )
        deal = self.deals.create(
            campaign_id=campaign_id,
            influencer_id=payload.influencer_id,
            status=payload.status.value,
            lost_reason=payload.lost_reason,
            labels_json=_clean_labels(payload.labels),
            internal_notes=payload.internal_notes,
        )
        self.db.commit()
        return self.get_deal(deal.id)

    def list_campaign_deals(
        self,
        campaign_id: str,
        *,
        status: DealStatus | None = None,
        platform: str | None = None,
        lost_reason: str | None = None,
        has_email_thread: bool | None = None,
        include_archived: bool = False,
        sort: str = "updated_at",
        limit: int | None = None,
        offset: int = 0,
    ) -> DealListResponse:
        self._require_campaign(campaign_id)
        deals = self.deals.list_for_campaign(
            campaign_id,
            status=status.value if status else None,
            platform=platform,
            lost_reason=lost_reason,
            has_email_thread=has_email_thread,
            include_archived=include_archived,
        )
        rows = [self._pipeline_row(deal) for deal in deals]
        rows = self._sort_rows(rows, sort)
        if offset:
            rows = rows[offset:]
        if limit is not None:
            rows = rows[:limit]
        return DealListResponse(deals=rows)

    def get_deal(self, deal_id: str) -> DealDetailResponse:
        deal = self.deals.get_detail(deal_id)
        if not deal:
            raise DealNotFound("Deal not found.", details={"deal_id": deal_id})
        row = self._pipeline_row(deal)
        return DealDetailResponse(
            **row.model_dump(),
            created_at=deal.created_at,
            source_list_status=deal.source_list_status,
        )

    def update_deal(self, deal_id: str, payload: DealUpdateRequest) -> DealDetailResponse:
        deal = self._require_deal(deal_id)
        values = self._deal_update_values(payload)
        if values:
            self.deals.update(deal, **values)
            self.db.commit()
        return self.get_deal(deal_id)

    def archive_deal(self, deal_id: str) -> None:
        deal = self._require_deal(deal_id)
        self.deals.archive(deal)
        self.db.commit()

    def bulk_create_deals(
        self, campaign_id: str, payload: DealBulkCreateRequest
    ) -> DealBulkCreateResponse:
        self._require_campaign(campaign_id)
        rows: list[DealBulkCreateRowResult] = []
        created_count = skipped_count = conflict_count = error_count = 0
        for influencer_id in payload.influencer_ids:
            influencer = self.influencers.get(influencer_id)
            if not influencer or influencer.archived_at is not None:
                error_count += 1
                rows.append(
                    DealBulkCreateRowResult(
                        influencer_id=influencer_id,
                        status="error",
                        errors=["Influencer not found."],
                    )
                )
                continue
            existing = self.deals.get_by_campaign_influencer(campaign_id, influencer_id)
            if existing:
                if payload.skip_existing:
                    skipped_count += 1
                    rows.append(
                        DealBulkCreateRowResult(
                            influencer_id=influencer_id,
                            deal_id=existing.id,
                            status="skipped",
                        )
                    )
                else:
                    conflict_count += 1
                    rows.append(
                        DealBulkCreateRowResult(
                            influencer_id=influencer_id,
                            deal_id=existing.id,
                            status="conflict",
                            errors=["Influencer already has a deal in this campaign."],
                        )
                    )
                continue
            deal = self.deals.create(
                campaign_id=campaign_id,
                influencer_id=influencer_id,
                status=DealStatus.DRAFT.value,
            )
            created_count += 1
            rows.append(
                DealBulkCreateRowResult(
                    influencer_id=influencer_id,
                    deal_id=deal.id,
                    status="created",
                )
            )
        self.db.commit()
        return DealBulkCreateResponse(
            created_count=created_count,
            skipped_count=skipped_count,
            conflict_count=conflict_count,
            error_count=error_count,
            rows=rows,
        )

    def bulk_update_deals(
        self, campaign_id: str, payload: DealBulkUpdateRequest
    ) -> DealBulkUpdateResponse:
        self._require_campaign(campaign_id)
        deals_by_id = {deal.id: deal for deal in self.deals.list_by_ids(payload.deal_ids)}
        rows: list[DealBulkUpdateRowResult] = []
        updated_count = error_count = 0
        for deal_id in payload.deal_ids:
            deal = deals_by_id.get(deal_id)
            if not deal:
                error_count += 1
                rows.append(
                    DealBulkUpdateRowResult(
                        deal_id=deal_id,
                        status="error",
                        errors=["Deal not found."],
                    )
                )
                continue
            if deal.campaign_id != campaign_id:
                error_count += 1
                rows.append(
                    DealBulkUpdateRowResult(
                        deal_id=deal_id,
                        status="error",
                        errors=["Deal does not belong to this campaign."],
                    )
                )
                continue
            values = self._bulk_update_values(deal, payload)
            if values:
                self.deals.update(deal, **values)
            updated_count += 1
            rows.append(DealBulkUpdateRowResult(deal_id=deal_id, status="updated"))
        self.db.commit()
        return DealBulkUpdateResponse(
            updated_count=updated_count,
            error_count=error_count,
            rows=rows,
        )

    def _require_campaign(self, campaign_id: str) -> models.Campaign:
        campaign = self.campaigns.get(campaign_id)
        if not campaign or campaign.archived_at is not None:
            raise CampaignNotFound(
                "Campaign not found.",
                details={"campaign_id": campaign_id},
            )
        return campaign

    def _require_deal(self, deal_id: str) -> models.Deal:
        deal = self.deals.get(deal_id)
        if not deal:
            raise DealNotFound("Deal not found.", details={"deal_id": deal_id})
        return deal

    def _deal_update_values(self, payload: DealUpdateRequest) -> dict[str, Any]:
        values = payload.model_dump(exclude_unset=True)
        if isinstance(values.get("status"), DealStatus):
            values["status"] = values["status"].value
        if "labels" in values:
            values["labels_json"] = _clean_labels(values.pop("labels") or [])
        return values

    def _bulk_update_values(
        self, deal: models.Deal, payload: DealBulkUpdateRequest
    ) -> dict[str, Any]:
        values: dict[str, Any] = {}
        if payload.status is not None:
            values["status"] = payload.status.value
        if "lost_reason" in payload.model_fields_set:
            values["lost_reason"] = payload.lost_reason
        if payload.labels is not None:
            values["labels_json"] = _apply_label_update(
                deal.labels_json or [],
                payload.labels,
                payload.label_mode,
            )
        if payload.internal_notes is not None:
            values["internal_notes"] = (
                _append_note(deal.internal_notes, payload.internal_notes)
                if payload.notes_mode == "append"
                else payload.internal_notes
            )
        return values

    def _pipeline_row(self, deal: models.Deal) -> DealPipelineRow:
        deliverables = _deliverable_summary(deal.deliverables)
        compensation = _compensation_summary(deal.compensation_items)
        email_threads = _email_thread_summary(deal.email_thread_links)
        return DealPipelineRow(
            id=deal.id,
            campaign_id=deal.campaign_id,
            status=DealStatus(deal.status),
            lost_reason=deal.lost_reason,
            labels=deal.labels_json or [],
            internal_notes=deal.internal_notes,
            influencer=InfluencerSummary(
                id=deal.influencer.id,
                display_name=deal.influencer.display_name,
                country=deal.influencer.country,
                city=deal.influencer.city,
            ),
            primary_platform=_primary_platform(deal.influencer.platforms),
            platforms=_platform_summaries(deal.influencer.platforms),
            primary_contact=_primary_contact(deal.influencer.contacts),
            deliverables=deliverables,
            compensation=compensation,
            email_threads=email_threads,
            completion_suggested=_completion_suggested(
                deal.deliverables, deal.compensation_items
            ),
            updated_at=deal.updated_at,
            archived_at=deal.archived_at,
        )

    def _sort_rows(self, rows: list[DealPipelineRow], sort: str) -> list[DealPipelineRow]:
        reverse = True
        key_name = sort
        if sort.startswith("-"):
            key_name = sort[1:]
        elif sort.startswith("+"):
            key_name = sort[1:]
            reverse = False
        if key_name == "follower_count":
            return sorted(
                rows,
                key=lambda row: (
                    row.primary_platform.follower_count
                    if row.primary_platform and row.primary_platform.follower_count is not None
                    else -1
                ),
                reverse=reverse,
            )
        if key_name == "status":
            return sorted(rows, key=lambda row: row.status.value, reverse=reverse)
        if key_name == "due_date":
            return sorted(
                rows,
                key=lambda row: row.deliverables.next_due_date or date.max,
                reverse=False if sort == "due_date" else reverse,
            )
        return sorted(rows, key=lambda row: row.updated_at, reverse=reverse)


def _clean_labels(labels: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for label in labels:
        normalized = label.strip()
        if normalized and normalized not in seen:
            cleaned.append(normalized)
            seen.add(normalized)
    return cleaned


def _apply_label_update(
    current: list[str], labels: list[str], mode: str
) -> list[str]:
    cleaned = _clean_labels(labels)
    if mode == "add":
        return _clean_labels([*current, *cleaned])
    if mode == "remove":
        remove = set(cleaned)
        return [label for label in current if label not in remove]
    return cleaned


def _append_note(current: str | None, addition: str) -> str:
    if not current:
        return addition
    if not addition:
        return current
    return f"{current}\n{addition}"


def _primary_platform(
    platforms: list[models.InfluencerPlatform],
) -> PrimaryPlatformSummary | None:
    if not platforms:
        return None
    platform = sorted(
        platforms,
        key=lambda item: (item.follower_count or 0, item.created_at),
        reverse=True,
    )[0]
    return PrimaryPlatformSummary(
        platform=platform.platform,
        username=platform.username,
        profile_url=platform.profile_url,
        follower_count=platform.follower_count,
    )


def _platform_summaries(
    platforms: list[models.InfluencerPlatform],
) -> list[PrimaryPlatformSummary]:
    return [
        PrimaryPlatformSummary(
            platform=platform.platform,
            username=platform.username,
            profile_url=platform.profile_url,
            follower_count=platform.follower_count,
        )
        for platform in sorted(
            platforms,
            key=lambda item: (item.follower_count or 0, item.created_at),
            reverse=True,
        )
    ]


def _primary_contact(
    contacts: list[models.InfluencerContact],
) -> PrimaryContactSummary | None:
    if not contacts:
        return None
    contact = sorted(contacts, key=lambda item: (not item.is_primary, item.created_at))[0]
    return PrimaryContactSummary(
        id=contact.id,
        name=contact.name,
        email=contact.email,
        role=contact.role,
        is_primary=contact.is_primary,
    )


def _deliverable_summary(deliverables: list[models.Deliverable]) -> DeliverableSummary:
    active = [
        item for item in deliverables if item.status != DeliverableStatus.CANCELLED.value
    ]
    completed_statuses = {
        DeliverableStatus.POSTED.value,
        DeliverableStatus.COMPLETED.value,
    }
    completed_count = sum(1 for item in active if item.status in completed_statuses)
    due_dates = [
        item.due_date
        for item in active
        if item.due_date and item.status not in completed_statuses
    ]
    published_url_count = sum(1 for item in active if item.published_url)
    label = _deliverable_label(active)
    return DeliverableSummary(
        total_count=len(active),
        completed_count=completed_count,
        next_due_date=min(due_dates) if due_dates else None,
        published_url_count=published_url_count,
        label=label,
    )


def _deliverable_label(deliverables: list[models.Deliverable]) -> str | None:
    if not deliverables:
        return None
    quantities = Counter[str]()
    for item in deliverables:
        quantities[item.type] += item.quantity
    parts = [
        f"{quantity} {_pluralize(label, quantity)}"
        for label, quantity in sorted(quantities.items())
    ]
    posted_count = sum(
        1
        for item in deliverables
        if item.status in {DeliverableStatus.POSTED.value, DeliverableStatus.COMPLETED.value}
    )
    if posted_count:
        parts.append(f"{posted_count} posted")
    return ", ".join(parts)


def _pluralize(label: str, quantity: int) -> str:
    if quantity == 1 or label.endswith("s"):
        return label
    return f"{label}s"


def _compensation_summary(
    items: list[models.CompensationItem],
) -> CompensationSummary:
    active = [item for item in items if item.status != CompensationItemStatus.CANCELLED.value]
    cash_totals: dict[str, Decimal] = {}
    reimbursement_totals: dict[str, Decimal] = {}
    non_cash_descriptions: list[str] = []
    for item in active:
        if item.amount is None:
            non_cash_descriptions.append(item.description or _humanize_type(item.type))
            continue
        currency = item.currency or "USD"
        if item.type == CompensationItemType.CASH_STIPEND.value:
            cash_totals[currency] = cash_totals.get(currency, Decimal("0")) + item.amount
        elif _is_reimbursement(item.type):
            reimbursement_totals[currency] = (
                reimbursement_totals.get(currency, Decimal("0")) + item.amount
            )
        else:
            non_cash_descriptions.append(item.description or _humanize_type(item.type))
    return CompensationSummary(
        active_item_count=len(active),
        completed_item_count=sum(
            1 for item in active if item.status == CompensationItemStatus.COMPLETED.value
        ),
        cash_totals=cash_totals,
        reimbursement_totals=reimbursement_totals,
        non_cash_descriptions=non_cash_descriptions,
        label=_compensation_label(cash_totals, reimbursement_totals, non_cash_descriptions),
    )


def _is_reimbursement(item_type: str) -> bool:
    return (
        item_type.endswith("_REIMBURSEMENT")
        or item_type == CompensationItemType.MEAL_OR_PER_DIEM.value
    )


def _compensation_label(
    cash_totals: dict[str, Decimal],
    reimbursement_totals: dict[str, Decimal],
    non_cash_descriptions: list[str],
) -> str | None:
    parts: list[str] = []
    for currency, amount in sorted(cash_totals.items()):
        parts.append(f"{_format_money(amount, currency)} cash")
    for currency, amount in sorted(reimbursement_totals.items()):
        parts.append(f"{_format_money(amount, currency)} reimbursements")
    parts.extend(non_cash_descriptions[:2])
    return " + ".join(parts) if parts else None


def _format_money(amount: Decimal, currency: str) -> str:
    if currency == "USD":
        return f"${amount:,.0f}" if amount == amount.to_integral() else f"${amount:,.2f}"
    rendered = f"{amount:,.0f}" if amount == amount.to_integral() else f"{amount:,.2f}"
    return f"{rendered} {currency}"


def _humanize_type(item_type: str) -> str:
    return item_type.lower().replace("_", " ")


def _email_thread_summary(
    links: list[models.EmailThreadLink],
) -> EmailThreadSummary:
    if not links:
        return EmailThreadSummary()
    last_activity = max(link.updated_at or link.created_at for link in links)
    return EmailThreadSummary(thread_count=len(links), last_activity_at=last_activity)


def _completion_suggested(
    deliverables: list[models.Deliverable],
    compensation_items: list[models.CompensationItem],
) -> bool:
    active_deliverables = [
        item for item in deliverables if item.status != DeliverableStatus.CANCELLED.value
    ]
    active_compensation = [
        item
        for item in compensation_items
        if item.status != CompensationItemStatus.CANCELLED.value
    ]
    if not active_deliverables and not active_compensation:
        return False
    deliverables_done = all(
        item.status in {DeliverableStatus.POSTED.value, DeliverableStatus.COMPLETED.value}
        for item in active_deliverables
    )
    compensation_done = all(
        item.status == CompensationItemStatus.COMPLETED.value for item in active_compensation
    )
    return deliverables_done and compensation_done


def mark_completed_at_if_needed(values: dict[str, Any]) -> dict[str, Any]:
    if (
        values.get("status") == CompensationItemStatus.COMPLETED.value
        and values.get("completed_at") is None
    ):
        values["completed_at"] = utc_now()
    return values
