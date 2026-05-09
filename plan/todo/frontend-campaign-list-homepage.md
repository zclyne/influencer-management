# Frontend Campaign List Homepage Plan

## Status

- New plan.
- This plan covers the frontend homepage only: `/campaigns` as the Campaign List page.
- Move this file to `plan/completed/` only after the homepage is implemented, verified, and accepted.

## Design Sources

- Product source of truth: Notion CreatorFlow docs.
- Frontend constraints: `frontend/AGENTS.md`.
- Visual direction: Penpot `Campaign List Page`.
- Current backend API:
  - `GET /api/v1/campaigns`
  - `POST /api/v1/campaigns`
  - `DELETE /api/v1/campaigns/{campaign_id}`

## Product Intent

The homepage is the Campaign List page.

It lets users:

- browse campaigns.
- create a campaign.
- search/filter campaigns.
- archive campaigns through delete actions.
- open a campaign workspace.

It must not become the campaign workspace itself.

Campaign-specific operations belong inside `/campaigns/:campaignId`, including:

- campaign deal pipeline.
- `Add from library`.
- `Export view`.
- deal drawer/detail workflows.

## Technical Direction

Use the frontend stack and conventions in `frontend/AGENTS.md`:

- Vue 3.
- TypeScript.
- Vue Router.
- Ant Design Vue.
- OpenAPI-generated or schema-aligned API client.
- Module composables for data loading and mutations.

Ant Design Vue should be used wherever possible. Do not build custom replacements for:

- table.
- form.
- modal.
- popconfirm.
- input/search.
- button.
- tags.
- pagination.
- notification/message.

Custom components may compose Ant Design Vue primitives for product-specific structure.

## Route And Navigation

Add route behavior:

- `/campaigns` renders Campaign List.
- `/campaigns/:campaignId` renders Campaign Workspace.

Sidebar:

- `Campaigns` links to `/campaigns`.
- Do not add `Imports` or `Exports` sidebar items.

Top bar:

- Top bar remains global only.
- Do not put `New campaign`, search, delete, import, or export actions in the top bar.

## Campaign List UI

Implement the page using Ant Design Vue:

- Page title: `Campaign list`.
- Description: open campaigns to manage deals, add influencers from the library, and use campaign-scoped export.
- Summary cards should only use data available from current campaign list response:
  - total active/unarchived campaigns.
  - planning/draft count.
  - active count.
  - archived count only when archived campaigns are included.

Do not mock unavailable metrics such as:

- active deal count.
- pending review count.
- spend planned.

Campaign table:

- Use Ant Design Vue `Table`.
- Use `rowSelection` for multi-select.
- Use columns:
  - Campaign.
  - Brands.
  - Status.
  - Budget.
  - Updated.
  - Actions.
- Campaign name is a link to `/campaigns/:campaignId`.
- Do not make the entire row ambiguously clickable.
- Actions column includes `Delete`.
- Toolbar includes:
  - search input.
  - status filter.
  - include archived toggle/filter.
  - `Delete selected`.
  - `New campaign`.

Delete behavior:

- Existing backend delete archives a campaign.
- Label user-facing confirmation as archive/delete consistently.
- Destructive actions must use Ant Design Vue confirmation.
- Bulk delete should run archive requests for selected rows and report failures clearly.

Create campaign:

- `New campaign` opens an Ant Design Vue modal/form.
- Form fields:
  - name.
  - status.
  - budget.
  - start date.
  - end date.
  - brief.
  - notes.
- Brand linking can be deferred unless the existing frontend already has a brand selector ready.
- On success, close modal, refresh list, and navigate to the new campaign workspace or keep the user on list with the new row visible.
  - Default: navigate to the new campaign workspace.

## API And State

Add campaign list API support if missing:

- `listCampaigns({ status, includeArchived })`
- `createCampaign(payload)`
- `archiveCampaign(campaignId)`

Use a module composable, for example `useCampaigns`, to own:

- list loading.
- list error.
- create mutation state.
- archive mutation state.
- selected row keys.
- search text.
- status filter.
- include archived filter.
- refresh after mutation.

The page should not construct raw URLs directly.

## Refactor Boundaries

Current frontend mixes campaign list and workspace behavior in `CampaignWorkspace.vue`.

Separate responsibilities:

- Campaign List page owns campaign browsing and campaign creation.
- Campaign Workspace page owns selected campaign pipeline and campaign-scoped actions.

Remove campaign-level import behavior from workspace.

Campaign Workspace should eventually expose:

- `Add from library`.
- `Export view`.
- deal table.
- deal drawer/detail link.

## Acceptance Criteria

- `/campaigns` shows the Campaign List page.
- `/campaigns/:campaignId` is reserved for Campaign Workspace.
- Top bar contains only global workspace/status/settings content.
- Page-specific create/search/delete controls are inside page content or table toolbar.
- Campaign table uses Ant Design Vue Table.
- New campaign uses Ant Design Vue Modal/Form.
- Delete and bulk delete use confirmation.
- Campaign name opens the workspace route.
- No top-level Imports or Exports navigation appears.
- No mocked deal/pending/spend metrics appear on Campaign List.
- `bun run typecheck` passes.
- `bun run build` passes.

