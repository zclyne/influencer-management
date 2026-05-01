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

6. Do not design a full standalone Email page yet.
   Email context is important to the product, but the current UI direction is not ready. Keep only a placeholder in navigation/design until the workflow is rethought.

7. Influencer and Deal screens must show multi-platform creators.
   A creator can have Instagram, TikTok, YouTube, Threads, and other platform identities. Do not design these screens as if each influencer only has one platform.

8. Influencer detail is a standalone page.
   Clicking an influencer in the Influencer Library should navigate to the Influencer Detail page. Deal screens that link to an influencer profile must reuse the same Influencer Detail page, not a separate deal-specific profile view.

9. Tables need standard deletion affordances.
   Data tables should use framework table row selection for multi-select deletion and a rightmost actions column for single-row delete. Do not design custom deletion controls outside the table unless the table component cannot support the interaction.
   Destructive table actions should open a confirmation modal or provide an undo window; do not imply immediate silent deletion.

10. Import Wizard should not duplicate preview as both a stage and a panel.
    The preview result table is the preview surface. Do not add a separate top-level `Preview result` stage/card that repeats the same state.

11. Import Wizard should optimize for preview review after upload.
    The upload control should collapse to a compact file status row after a file is selected. Use the main page area for the preview table, row decisions, filters, row removal, and confirm actions.

12. Campaigns need a list page before the workspace page.
    `/campaigns` should show a Campaign List page for browsing, creating, deleting, and opening campaigns. The campaign workspace/pipeline belongs to `/campaigns/:campaignId`.

13. Top bar must stay global.
    The top bar should contain page-independent workspace controls or status only. Page-specific actions such as `New campaign`, `New brand`, `New template`, `Import CSV`, `Add from library`, search inputs, and export actions belong inside the page header or table toolbar.

14. Detail pages need an obvious return path.
    Campaign Detail should make it easy to return to Campaign List, and similar detail pages should make parent navigation explicit. Prefer framework breadcrumbs, such as Campaign List -> Campaign Detail, instead of relying only on browser back behavior.

15. Campaign Detail should not embed a dedicated Email area.
    Campaign-scoped email review should reuse the standalone Email page. Campaign pages should provide a page action linking to Email with a campaign URL parameter. The Email page defaults to all email, and future implementation can filter to a campaign when a campaign parameter is present.

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
  - Contains global influencer library, manual add, platform/contact editing, and Modash import.
  - Import should appear as a sub-tab/action inside this section, not as a standalone sidebar item.

- `Brands`
  - Subtitle: `Clients and briefs`
  - Optional but reasonable because Brand CRUD now exists and Campaign can link multiple Brands.
  - If the product feels too crowded, Brand management can be nested in Campaign creation/settings instead.

- `Email`
  - Subtitle: `Thread context`
  - Placeholder only for now.
  - Do not design the full Email page until the email workflow is revisited.

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
- Keep the top toolbar global; do not place page-specific primary actions in it.
- Keep interaction states easy to map to Vue components and API state.
- Avoid designing bespoke controls that would require a custom component system before the product workflow is validated.
- Keep dense table interactions practical: stable row height, selectable rows, sortable columns, simple filter chips, and a right-side detail drawer.
- Use table row selection for bulk delete and a fixed/rightmost actions column for per-row delete.
- Use clickable primary entity cells for navigation to detail pages, rather than making an entire row ambiguously clickable.
- Do not use a side preview on Influencer Library that competes with the standalone Influencer Detail page.
- Use breadcrumb navigation on standalone detail pages so users can return to the parent list or workspace directly.
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
- Add a Campaign List page before Campaign Workspace.
- Campaign List should use a framework table with row selection, row delete, bulk delete, and campaign-name navigation into Campaign Workspace.
- Page-specific actions must live inside the content area or table toolbar, not the global top bar.
- Add an Influencer Library screen state with:
  - `Library`
  - `Import CSV`
  - `Add manually`
  - multi-platform platform display and editing.
- Add an Influencer Detail page that is reached from Influencer Library row clicks and Deal profile links.
- Add Import Wizard as a nested Influencers view, visually connected to the library.
- In Import Wizard, keep preview as the main result panel, not as a duplicated top workflow card.
- In Import Wizard, do not keep upload and preview as large side-by-side panels after upload; use a compact uploaded-file row and dedicate the page to preview review.
- Add a short annotation near Campaign export explaining that export is campaign-contextual.
- Add breadcrumbs to detail page designs, including Campaign Detail back to Campaign List and shared Influencer Detail back to the originating library/workspace where route context is known.
- Remove any dedicated email panel/section from Campaign Detail designs. Add a Campaign page action such as `Open email` or `View email` that routes to `/email?campaignId=<campaign_id>` instead.
- Keep the Email page as a placeholder design, but document that it will default to all email and can later filter by URL campaign parameter.
- Keep all designed controls implementable with existing UI framework primitives.
- Keep Email as a placeholder only.

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
- Rename Templates subtitle to avoid outreach-only wording.
- Keep campaign export as an action, not a route.
- Treat export API integration as Campaign Workspace behavior.
- Keep Campaign List focused on campaign selection and management; do not put campaign-specific export there.
- Keep page-specific create/search/import/export actions out of the global top bar.
- Detail pages should use Ant Design Vue `Breadcrumb` or an equivalent framework breadcrumb near the page header for parent navigation.
- Campaign detail/workspace should link to `/email?campaignId=<campaign_id>` for campaign email context instead of embedding a campaign email area.
- The Email route should tolerate no parameter by showing all email, and tolerate `campaignId` by filtering to campaign-related email when the Email workflow is implemented.
- In Campaign Workspace, add creators by selecting from the existing Influencer Library; adding an influencer to a campaign creates a Deal.
- Do not add a Campaign-level import action.
- In data tables, include row selection and a rightmost delete action column.
- Influencer Library row primary link navigates to the shared Influencer Detail page.
- Influencer Library should be table-first; avoid a right-side profile preview because the profile is a standalone page.
- Delete and bulk delete actions must show confirmation or undo behavior in implementation.
- Use existing framework table, drawer, form, modal, dropdown, tab, and notification primitives wherever possible.

## Open Questions

- Should `Brands` be top-level navigation or only appear inside Campaign setup?
- Should `Templates` be top-level now, or should it wait until more than outreach templates exist?
- Should import sessions/history be visible under Influencers, or only after a user imports?
- Should export history be stored and visible, or should MVP only download generated CSV immediately?
- What is the correct standalone Email workflow beyond deal/influencer email context placeholders?
- Which UI framework should be standardized for the Vue frontend before implementing the revised design?

## Done Criteria

- Figma sidebar no longer shows `Imports` as a top-level item.
- Figma sidebar no longer shows `Exports` as a top-level item.
- Templates subtitle is broader than outreach.
- Import Wizard is visually nested under Influencers.
- Campaign export is shown as a contextual action.
- Campaign List exists separately from Campaign Workspace.
- Top bar contains only global workspace/status controls; page actions are inside page content.
- Export is treated as a Campaign sub-feature in both design and code.
- Email page remains a placeholder, not a full workflow screen.
- Detail pages include obvious breadcrumb/back navigation to their parent list/workspace.
- Campaign Detail does not include an embedded email panel and instead links to the Email page with campaign route context.
- Influencer and Deal screens show creators with multiple platforms.
- Influencer Detail exists as a standalone page and is reused by Deal profile links.
- Tables expose single-row delete and multi-select delete via framework table primitives.
- Import Wizard does not duplicate preview in both the workflow header and the main preview table.
- Import Wizard uses most of the page for preview results after upload.
- Design can be implemented with existing Vue/UI framework primitives without building a large custom component library first.
- Frontend code navigation matches the revised Figma design.
- `bun run typecheck` and `bun run build` pass after code changes.
