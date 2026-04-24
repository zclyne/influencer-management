# Frontend Desktop Workbench Plan

## Status

- Frontend is a minimal Vue/Electron placeholder.
- No routing, state management, generated API client, Campaign Workspace, Influencer Library, Deal Detail, or import wizard UI exists.

When this module is implemented and verified, move this file to `plan/completed/frontend-workbench.md`.

## Notion Sources

- Frontend doc: Vue.js + Electron, HTTP API through FastAPI, OpenAPI-based client.
- Product doc: primary UI is Campaign Workspace, not a landing page.
- Technical overview: frontend owns interaction, table workflow, file selection, notifications, and user confirmation.

## Goal

Build the actual Desktop IRM workbench UI around Campaign Workspace and supporting library/detail flows.

## Scope

In scope:

- Electron + Vue app shell.
- Routing.
- API client layer.
- Campaign Workspace.
- Influencer Library.
- Deal Detail drawer/page.
- Influencer Ingestion Wizard.
- Error and loading states.

Out of scope:

- Marketing landing page.
- Full packaging/update strategy.
- Client portal.
- Complex design system.

## Architecture

Add:

- router.
- typed API client.
- shared layout.
- feature directories matching backend domains.

Suggested structure:

```plain text
frontend/src/
  api/
  app/
  campaigns/
  influencers/
  deals/
  ingestion/
  email-context/
  shared/
```

API:

- Use generated or schema-aligned TypeScript types from FastAPI OpenAPI.
- Keep all requests under configured `VITE_API_BASE_URL`.
- Frontend never talks to SQLite directly.

## First Screens

Default screen should be the usable campaign pipeline workspace, not a promotional landing page.

Initial navigation:

- Campaigns.
- Influencers.
- Imports.
- Settings later.

Campaign Workspace:

- campaign list/select.
- deal table.
- status filter.
- add influencer.
- import into campaign.
- open deal detail.
- export current view once export exists.

Influencer Library:

- search/list.
- profile detail.
- platform/contact management once backend exists.

Ingestion Wizard:

- select Modash CSV.
- call source-specific preview.
- display row-level errors/warnings/conflicts.
- user chooses create/merge/skip.
- confirm import.

Deal Detail:

- status.
- notes/labels/lost reason.
- contacts.
- deliverables.
- compensation.
- email context.

## State Management

Start simple:

- Vue Query or equivalent request cache if introduced.
- Otherwise feature-local composables for API calls.
- Avoid global store until state is shared across multiple screens.

## Error Handling

Use backend error shape once standardized:

- code.
- message.
- details.
- request_id.

UI must show row-level import and bulk operation errors, not only global failure.

## Styling

Use practical desktop workbench layout:

- dense tables.
- side drawer/detail panel.
- stable column widths.
- no marketing hero.

Avoid duplicating backend business rules. Frontend can validate obvious format issues, but backend remains final authority.

## Tests

Frontend:

- API client contract smoke tests once generated types exist.
- Component tests for ingestion preview table.
- Campaign Workspace load/error/empty states.
- Deal detail edit flows.

Manual:

- Run dev server.
- Verify Electron shell loads configured API base.
- Verify import preview and confirm against backend test CSV once screens exist.

## Done Criteria

- The first screen is a usable Desktop IRM workspace.
- Core navigation and API client exist.
- Campaign Workspace and Ingestion Wizard can call real backend endpoints.
- Frontend does not duplicate final normalization, dedup, or status rules.
- `bun run build` or the project equivalent passes.
