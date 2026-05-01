# Deal Detail Page Plan

## Summary

Implement `/campaigns/:campaignId/deals/:dealId` as the standalone full-page Deal Detail workflow.
The Penpot page `Deal Detail Page Shell` contains the current v2 design direction.

## Design Direction

- Use breadcrumb navigation: `Campaigns / {campaign name} / {influencer name} deal`.
- Keep this page as a full detail page, separate from the Campaign Workspace review drawer.
- Show a header with status, campaign context, next action, `Open campaign`, and deal-specific actions.
- Include an influencer summary card with multi-platform badges, primary contact, and `Open influencer`.
- Include Deal summary and Contact summary cards.
- Manage Deal-owned objects through Ant Design Vue tables:
  - Deliverables.
  - Compensation items.
  - Files and internal notes.
- Keep email as a lightweight placeholder only:
  - show linked-thread count/manual-link state when available.
  - provide `Open email` entrypoint.
  - do not build email timelines, candidate queues, or full email workflow here.

## Implementation Notes

- Replace the current placeholder route component with a real Deal Detail page component.
- Load deal detail through `GET /api/v1/deals/{deal_id}`.
- Load deliverables through `GET /api/v1/deals/{deal_id}/deliverables`.
- Load compensation through `GET /api/v1/deals/{deal_id}/compensation-items`.
- Keep mutation flows Ant Design Vue based: tables, modals, forms, popconfirms, tags, alerts.
- Do not add compensation shortcuts directly to Deal; use CompensationItem APIs.
- Do not auto-mutate Deal status from email context.

## Done Criteria

- Deal Detail page matches the Penpot v2 layout.
- Page supports easy navigation back to the Campaign Workspace.
- Multi-platform creator display is visible.
- Deliverables and compensation are table-first and backed by existing APIs.
- Email remains placeholder-only.
- `bun run typecheck` and `bun run build` pass.
