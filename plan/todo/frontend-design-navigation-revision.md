# Frontend Design Navigation Revision Plan

## Status

- New plan.
- Current Figma file exists: https://www.figma.com/design/10bTfKv9JQHy3DoBed8B8L
- The current Figma direction is broadly acceptable, but the left sidebar information architecture needs correction before the design is treated as implementation-ready.
- Current frontend code also still exposes `Imports` and `Exports` as independent workbench navigation concepts through the initial scaffold.

When this design revision is implemented in Figma and reflected in frontend code, move this file to `plan/completed/frontend-design-navigation-revision.md`.

## User Feedback To Capture

1. `Import` is not a top-level product module.
   It is an Influencer sub-flow because import is one way to create/update global influencer data.

2. `Templates` is not only for outreach.
   Templates can later include outreach templates, contract templates, summary/report templates, brief snippets, and other reusable content. The current sidebar subtitle is too narrow.

3. `Exports` is unclear as a top-level feature.
   The code has an export module because the product requires campaign pipeline CSV export, but that does not mean users need an `Exports` workspace in the primary sidebar.

4. In this product context, export is a Campaign sub-feature.
   It should be designed and implemented as part of Campaign Workspace, not as an independent module.

5. Frontend design should be easy to implement with existing frameworks.
   The design should avoid custom component systems or bespoke complex widgets when mature framework components can do the job.

## Product Interpretation

The product remains campaign-first:

- `Campaigns` is the daily operating workspace.
- `Deals` are rows inside a campaign pipeline.
- `Influencers` is the global reusable library.
- `Import/Ingestion` belongs under `Influencers`.
- `Export` is a contextual action on a campaign pipeline or filtered table view.
- `Export` belongs under Campaigns as a Campaign Workspace capability.
- `Templates` is a reusable resource area, not only an outreach feature.
- The design should map cleanly to existing frontend framework components instead of requiring a large custom UI system.

## Proposed Sidebar Information Architecture

Primary sidebar should use:

- `Campaigns`
  - Subtitle: `Pipeline workspace`
  - Default first screen.
  - Includes campaign list, pipeline table, filters, bulk actions, and export current view.

- `Influencers`
  - Subtitle: `Library and import`
  - Contains global influencer library, manual add, platform/contact editing, duplicate review, and Modash import.
  - Import should appear as a sub-tab/action inside this section, not as a standalone sidebar item.

- `Brands`
  - Subtitle: `Clients and briefs`
  - Optional but reasonable because Brand CRUD now exists and Campaign can link multiple Brands.
  - If the product feels too crowded, Brand management can be nested in Campaign creation/settings instead.

- `Email`
  - Subtitle: `Thread context`
  - Handles manual link/unlink, contact matching, and thread candidates.

- `Templates`
  - Subtitle: `Reusable docs`
  - Covers outreach templates now.
  - Leaves room for contract templates and summary/report templates later.
  - Do not label it as `Outreach drafts`.

Do not use `Exports` as a primary sidebar item for MVP.

## Framework-First Design Principle

The frontend should start from existing framework capabilities and mature UI/component patterns.

Design implications:

- Prefer conventional data-table behavior over custom spreadsheet-like controls unless the workflow truly requires it.
- Prefer framework-ready layouts: sidebar shell, top toolbar, tabs, drawers, modals, forms, tables, dropdown filters, toasts, and empty states.
- Keep interaction states easy to map to Vue components and API state.
- Avoid designing bespoke controls that would require a custom component system before the product workflow is validated.
- Keep dense table interactions practical: stable row height, selectable rows, sortable columns, simple filter chips, and a right-side detail drawer.
- Treat advanced table capabilities as incremental enhancements, not first-pass requirements.

Suitable implementation directions:

- Vue 3 component composition.
- Existing table/form/drawer/modal patterns from a mature UI framework.
- OpenAPI-aligned API client types.
- Feature folders that match product modules: campaigns, influencers, deals, email context, templates.

The Figma design should therefore communicate layout, hierarchy, states, and workflows without forcing pixel-perfect custom components that are expensive to build.

## Export UX Decision

The backend `exports` module exists for a valid reason: product docs require campaign pipeline export to CSV / Google Sheets-compatible format for agency handoff to clients, finance, or internal teams.

However, export is not a standalone workspace in the current product model.
It is a Campaign sub-feature.

UI placement:

- Campaign Workspace toolbar: `Export view`.
- Pipeline selection toolbar: `Export selected`.
- Campaign detail menu: `Export campaign CSV`.
- Optional future Campaign subpage: `Export history`, only if persisted export history becomes useful.
- Future reporting area can introduce report templates or dashboards if that scope becomes clear.

Design copy should make this obvious:

- Use `Export view` for the button.
- Avoid `Exports` as a main nav label.
- If an export history screen is added later, call it `Export history` under Campaigns or Settings, not a top-level module.

## Figma Revision Scope

Update the existing Figma file:

- Replace sidebar `Imports` with an Influencers sub-flow.
- Replace sidebar `Templates / Outreach drafts` subtitle with `Templates / Reusable docs`.
- Remove `Exports` from primary sidebar.
- Add `Export view` in Campaign Workspace toolbar and selection actions.
- Add an Influencer Library screen state with:
  - `Library`
  - `Import CSV`
  - `Add manually`
  - `Duplicate review` or `Import sessions`, if useful.
- Add Import Wizard as a nested Influencers view, visually connected to the library.
- Add a short annotation near Campaign export explaining that export is campaign-contextual.
- Keep all designed controls implementable with existing UI framework primitives.

Keep the current visual direction:

- Dense campaign table.
- Right-side Deal detail drawer.
- Neutral local-first desktop palette.
- Sidebar width and workbench structure.
- Framework-friendly components instead of custom one-off widgets.

## Frontend Code Revision Scope

Later code change should update:

- `frontend/src/app/navigation.ts`
- `frontend/src/App.vue`
- `frontend/src/influencers/InfluencerLibrary.vue`
- `frontend/src/ingestion/ImportWizard.vue`
- any future templates/export surfaces.

Expected code behavior:

- Remove top-level `imports` navigation item.
- Remove top-level `exports` navigation item.
- Keep import flow reachable from:
  - Influencer Library action.
  - Campaign Workspace `Import creators` action with target campaign preselected.
- Rename Templates subtitle to avoid outreach-only wording.
- Keep campaign export as an action, not a route.
- Treat export API integration as Campaign Workspace behavior.
- Use existing framework table, drawer, form, modal, dropdown, tab, and notification primitives wherever possible.

## Open Questions

- Should `Brands` be top-level navigation or only appear inside Campaign setup?
- Should `Templates` be top-level now, or should it wait until more than outreach templates exist?
- Should import sessions/history be visible under Influencers, or only after a user imports?
- Should export history be stored and visible, or should MVP only download generated CSV immediately?
- Which UI framework should be standardized for the Vue frontend before implementing the revised design?

## Done Criteria

- Figma sidebar no longer shows `Imports` as a top-level item.
- Figma sidebar no longer shows `Exports` as a top-level item.
- Templates subtitle is broader than outreach.
- Import Wizard is visually nested under Influencers.
- Campaign export is shown as a contextual action.
- Export is treated as a Campaign sub-feature in both design and code.
- Design can be implemented with existing Vue/UI framework primitives without building a large custom component library first.
- Frontend code navigation matches the revised Figma design.
- `bun run typecheck` and `bun run build` pass after code changes.
