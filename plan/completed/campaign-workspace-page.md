# Campaign Workspace Page Plan

## Summary

Implement `/campaigns/:campaignId` as the campaign operating workspace, backed by real Campaign,
Deal, Influencer Library, bulk deal, and export APIs.

## Implementation

- Use Ant Design Vue primitives for breadcrumb, cards, table, filters, modal, drawer, tags,
  popconfirm, and messages.
- Load campaign metadata, campaign deals, and add-from-library influencer candidates through the
  frontend API layer and module composables.
- Show deal summary cards, deal table filters, row selection, row delete, bulk status update,
  add from library, open email, and export view.
- Use a wide deal review drawer with multi-platform creator display and links to full deal detail
  and influencer detail.
- Keep Campaign Workspace free of embedded email panels; route campaign email review to
  `/email?campaignId=<campaign_id>`.

## Done Criteria

- Campaign Workspace loads real campaign and deal data.
- Deal table supports filters, selection, bulk update, row delete, and drawer review.
- Add from library bulk-creates campaign deals from existing influencers.
- Export view downloads campaign CSV with current deal filters.
- Typecheck and build pass.
