# Frontend AGENTS.md

## Scope

These instructions apply to the `frontend/` workspace.

The frontend is the desktop workbench UI for Desktop IRM. It should follow the product
boundaries in the root `AGENTS.md` and the current Penpot design direction.

## Technology Choices

Use this stack for frontend implementation:

- Vue 3.
- Vite.
- Electron.
- TypeScript.
- Vue Router for page routing.
- Ant Design Vue for framework UI primitives.
- OpenAPI-generated typed API client plus module-level composables.

Do not build a custom UI component system for common controls that Ant Design Vue already
covers.

Ant Design Vue is the default UI implementation layer for the entire frontend. Prefer its
components before writing custom UI. Custom components should compose Ant Design Vue
primitives for product-specific behavior; they should not replace Ant Design Vue tables,
forms, modals, drawers, upload controls, selects, buttons, tabs, tags, pagination,
notifications, or layout primitives.

## Product Navigation

Primary navigation should contain:

- `Campaigns`
- `Influencers`
- `Brands`
- `Email`
- `Templates`

Do not add top-level `Imports` or `Exports` navigation.

Product boundaries:

- Import belongs under Influencers.
- Campaign export belongs under Campaigns as `Export view`.
- Email is a placeholder-only page until the standalone email workflow is redesigned.
- Influencer Detail is a standalone page.
- Deal profile links must reuse the same Influencer Detail page.

## Route Model

Use Vue Router.

Expected route shape:

- `/campaigns`
- `/campaigns/:campaignId`
- `/campaigns/:campaignId/deals/:dealId`
- `/influencers`
- `/influencers/import`
- `/influencers/:influencerId`
- `/brands`
- `/templates`
- `/email`

The `/email` route should render a placeholder only.

## Code Structure

Prefer this high-level structure:

```text
src/
  app/
  api/
  shared/
  modules/
    campaigns/
    influencers/
    brands/
    templates/
    email/
```

Responsibilities:

- `app/`: router, layout shell, navigation, providers.
- `api/`: generated client, request wrapper, API error normalization.
- `shared/`: reusable UI wrappers, table helpers, status/platform badges, confirm helpers.
- `modules/*`: feature screens, feature composables, and module-specific components.

Do not let page components construct backend URLs directly. API calls should go through the
API layer and module composables.

## UI Conventions

Use Ant Design Vue primitives for:

- tables.
- forms.
- modals and popconfirms.
- drawers.
- upload.
- selects.
- buttons.
- tags.
- notifications.

Default to Ant Design Vue for any other common workbench UI primitive as well. Only write
custom UI when Ant Design Vue cannot reasonably express the behavior, and keep that custom
code narrowly scoped to the product-specific interaction.

Tables:

- Use framework table behavior for sorting, filtering, pagination, and selection.
- Use `rowSelection` for multi-select actions.
- Use a rightmost actions column for row actions.
- Every row that can be deleted should expose a row-level `Delete` action.
- Bulk deletion should use `Delete selected`.
- Destructive actions must show confirmation or provide undo. Do not silently delete.
- Use clickable primary entity cells for detail navigation; do not make full rows ambiguously
  clickable.

Layouts:

- Use a route-driven app shell with sidebar, top toolbar, and content outlet.
- Keep the top toolbar global. Do not put page-specific create, import, export, search, or
  delete actions in the top toolbar.
- Put page-specific actions in the page header or table toolbar.
- Use drawer only for side context such as quick deal review.
- Use full pages for standalone detail workflows such as Influencer Detail and Deal Detail.

## Module Rules

Campaigns:

- Campaign Workspace is the main operating surface.
- Deals are campaign rows.
- Add creators to campaigns via `Add from library`.
- Adding an influencer to a campaign creates a Deal.
- Do not add a campaign-level import action.
- Use `Export view` for campaign-scoped export.

Influencers:

- Influencer Library is table-first.
- Clicking a creator name navigates to Influencer Detail.
- Do not add a side profile preview that competes with the detail page.
- Influencer and Deal screens must support multi-platform creators.
- Import Wizard lives under `/influencers/import`.

Import Wizard:

- Upload should collapse into a compact uploaded-file status row after a file is selected.
- Use the main page area for preview review.
- Preview is the table surface; do not duplicate it as a separate workflow stage.
- Preview rows can be removed before confirm.
- Confirm writes only valid canonical influencer rows.

Email:

- Keep the standalone Email page as a placeholder.
- Deal and Influencer detail pages may reserve space for future email context.
- Do not build thread timelines, candidate queues, or standalone email workflows until the
  email UX is redesigned.

Templates:

- Templates are reusable docs, not outreach-only.
- Leave room for outreach templates, contract templates, report templates, briefs, and
  summaries.

## API And State

Use backend OpenAPI as the frontend contract.

API conventions:

- Backend base URL comes from `VITE_API_BASE_URL`, defaulting to `http://localhost:8000`.
- All backend calls use `/api/v1`.
- Keep the shared API error shape visible to users through clear messages.

State conventions:

- Use module composables for loading, error, selection, and mutation refresh behavior.
- Keep cross-module state small and explicit.
- Prefer route params over opaque global selection state for detail pages.

## Verification

Run from `frontend/` after frontend code changes:

```bash
bun run typecheck
bun run build
```

Docs-only changes do not require tests.
