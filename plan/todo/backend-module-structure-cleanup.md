# Backend Module Structure Cleanup Plan

## Status

- New plan.
- This plan captures backend structure issues found after the export, template/outreach, shared enum, and schema package discussions.
- The goal is to make package names match the actual architecture and product boundaries without changing business behavior beyond intentional breaking API/model renames.
- Each fix must be implemented on its own branch, verified, merged back to `main`, and then the next branch must start from the updated `main`.

When all fixes are implemented, verified, merged to `main`, and accepted, move this file to `plan/completed/backend-module-structure-cleanup.md`.

## Current Problems

### 1. Export Is Structurally Top-Level But Product-Scoped To Campaigns

Current state:

- Route file: `backend/app/api/routes/exports.py`
- Schema package: `backend/app/exports/schemas.py`
- Service file: `backend/app/services/exports.py`
- Effective endpoint: `GET /api/v1/campaigns/{campaign_id}/export.csv`

The API path is already campaign-scoped, which is correct.
The problem is package and route naming: `exports` looks like a top-level business module, but export is a Campaign Workspace sub-feature.

Expected direction:

- Keep export as a campaign contextual action.
- Do not introduce a top-level export workspace or business domain.
- Move export code under campaign-oriented naming.

### 2. Outreach Module Is Actually Mostly Template Management

Current state:

- Route file: `backend/app/api/routes/outreach.py`
- Schema package: `backend/app/outreach/schemas.py`
- Service file: `backend/app/services/outreach.py`
- DB model: `OutreachTemplate`
- Table: `outreach_templates`
- Template CRUD endpoints: `/api/v1/outreach/templates`

This makes `Template` look like an outreach-only concept.
That is wrong for Desktop IRM because templates can later support outreach emails, contract drafts, reports, summaries, briefs, and other reusable documents.

Expected direction:

- Template CRUD belongs to a generic Template module.
- Outreach draft generation is a use case that consumes templates.
- Sent/outreach state actions belong to Deal or communication workflow, not Template CRUD.
- No compatibility layer is needed; this app is still early-stage.

### 3. `domain` Package Overstates The Architecture

Current state:

- `backend/app/domain/enums.py` contains shared enum definitions.
- There are no domain models, aggregates, value objects, or domain services under `domain`.

The project currently uses a horizontal layered architecture:

```text
API handler -> Service -> Repository -> SQLAlchemy model/database
```

The package name `domain` implies a DDD-style layer that does not exist.
For the current architecture, shared enums should be named directly and plainly.

Expected direction:

- Replace `app.domain.enums` with `app.enums`.
- Remove the empty/misleading `app/domain` package.
- Keep enums outside `schemas` because SQLAlchemy models and services also depend on them.

### 4. Module Packages Containing Only `schemas.py` Are Misleading

Current state:

Many package names look like domain modules but contain only Pydantic schemas:

```text
backend/app/brands/schemas.py
backend/app/campaigns/schemas.py
backend/app/compensation/schemas.py
backend/app/deals/schemas.py
backend/app/deliverables/schemas.py
backend/app/email_context/schemas.py
backend/app/exports/schemas.py
backend/app/files/schemas.py
backend/app/jobs/schemas.py
backend/app/outreach/schemas.py
```

This suggests module-oriented or DDD-style organization, but implementation is actually horizontally layered.

Expected direction:

- Create one schemas package:

```text
backend/app/schemas/
  __init__.py
  common.py
  brands.py
  campaign_exports.py
  campaigns.py
  compensation.py
  deals.py
  deliverables.py
  email_context.py
  files.py
  influencer_ingestion.py
  influencers.py
  jobs.py
  templates.py
```

- Move `backend/app/api/schemas.py` into `backend/app/schemas/common.py` or `backend/app/schemas/errors.py`.
- Remove schema-only packages after imports are updated.
- Keep packages that contain real implementation code, for example `backend/app/influencers/ingestion/`, because it contains adapters, normalization, and registry code.

## Target Backend Structure

After this cleanup, backend structure should read as a clear horizontal architecture:

```text
backend/app/
  api/
    routes/
  core/
  db/
  enums.py
  repositories/
  schemas/
  services/
  storage/
  tasks/
```

Allowed implementation packages:

- `backend/app/influencers/ingestion/` may stay because it contains source adapters and normalization, not only schemas.
- Infrastructure packages such as `storage` and `tasks` may stay because they represent implementation boundaries.

Avoid adding package names that imply a domain module unless that package contains meaningful module-local implementation beyond schemas.

## Branch Plan

Each branch must start from current `main`.
After verification, merge the branch back into `main` before starting the next branch.

Recommended order reduces conflicts.

### Branch 1: Campaign Export Boundary

Branch name:

```bash
refactor/campaign-export-boundary
```

Scope:

- Rename `backend/app/services/exports.py` to `backend/app/services/campaign_exports.py`.
- Move `CampaignExportFilters` from `app.exports.schemas` to `app.schemas.campaign_exports` if the schemas package already exists, or temporarily to a campaign export schema file that Branch 4 will consolidate.
- Rename route file from `api/routes/exports.py` to `api/routes/campaign_exports.py`, or fold the endpoint into `api/routes/campaigns.py` if that stays readable.
- Keep effective API path: `GET /api/v1/campaigns/{campaign_id}/export.csv`.
- Change OpenAPI tag from `exports` to `campaigns` or `campaign exports`.
- Rename tests from export-as-module naming to campaign-export naming.
- Remove `backend/app/exports/` when no longer used.

Out of scope:

- Do not add export history UI.
- Do not introduce top-level `/exports`.
- Do not change CSV content unless tests expose an existing bug.

Verification:

```bash
cd backend
uv run pytest backend/tests/test_exports.py
uv run pytest
uv run ruff check .
```

Done criteria:

- No `app.exports` imports remain.
- No top-level export module package remains.
- Campaign export endpoint behavior stays covered by tests.
- Endpoint remains under `/api/v1/campaigns/{campaign_id}/export.csv`.

### Branch 2: Generic Templates Instead Of Outreach Templates

Branch name:

```bash
refactor/templates-module
```

Scope:

- Rename `OutreachTemplate` model to `Template`.
- Rename table `outreach_templates` to `templates` through an Alembic migration.
- Add a generic template type/category field if needed for product clarity, for example:
  - `OUTREACH_EMAIL`
  - `CONTRACT`
  - `REPORT`
  - `BRIEF`
  - `OTHER`
- Replace `/api/v1/outreach/templates` CRUD endpoints with `/api/v1/templates`.
- Rename schema classes from `OutreachTemplate*` to `Template*`.
- Rename repository from `OutreachTemplateRepository` to `TemplateRepository`.
- Rename service responsibilities:
  - `TemplateService` owns template CRUD and template validation.
  - A narrower outreach draft service may keep outreach-specific rendering and sent actions if needed.
- Keep deal/campaign outreach draft endpoints only if they remain meaningful as workflow actions:
  - `POST /api/v1/deals/{deal_id}/outreach-drafts`
  - `POST /api/v1/campaigns/{campaign_id}/outreach-drafts/bulk`
  - `POST /api/v1/deals/{deal_id}/outreach-sent`
- Ensure those endpoints consume generic template records instead of outreach-owned template records.

Out of scope:

- Do not implement contract draft generator.
- Do not add report rendering.
- Do not create compatibility aliases for old `/outreach/templates` endpoints.

Verification:

```bash
cd backend
uv run alembic upgrade head
uv run pytest backend/tests/test_outreach.py
uv run pytest
uv run ruff check .
```

Done criteria:

- Template CRUD is available under `/api/v1/templates`.
- No template CRUD endpoint remains under `/api/v1/outreach/templates`.
- No `OutreachTemplate` model/repository/schema names remain unless referring to historical migrations.
- Outreach draft generation uses generic templates.
- Contract draft concepts remain deferred.

### Branch 3: Shared Enums Without A Fake Domain Package

Branch name:

```bash
refactor/shared-enums
```

Scope:

- Move `backend/app/domain/enums.py` to `backend/app/enums.py`.
- Update all imports from `app.domain.enums` to `app.enums`.
- Delete `backend/app/domain/__init__.py` once no imports remain.
- Keep enum definitions unchanged unless Branch 2 adds a new `TemplateType`.
- Remove stale `__pycache__` directories if they are accidentally tracked; otherwise ignore local bytecode.

Out of scope:

- Do not introduce domain models.
- Do not split enums by feature unless the codebase has a concrete need.
- Do not move enums into schemas.

Verification:

```bash
cd backend
uv run pytest
uv run ruff check .
```

Done criteria:

- No `app.domain.enums` imports remain.
- No `backend/app/domain/` source package remains.
- DB models, services, schemas, and tests import shared enums from `app.enums`.

### Branch 4: Consolidated Schemas Package

Branch name:

```bash
refactor/schemas-package
```

Scope:

- Create `backend/app/schemas/`.
- Move Pydantic API/request/response schemas into domain-named files under `app.schemas`.
- Move common API error schema out of `app/api/schemas.py` into `app/schemas/common.py` or `app/schemas/errors.py`.
- Update route and service imports to use `app.schemas.*`.
- Move influencer ingestion Pydantic schemas from `app/influencers/ingestion/schemas.py` to `app/schemas/influencer_ingestion.py`.
- Keep ingestion adapter, normalization, and registry code in `app/influencers/ingestion/`.
- Delete schema-only packages that become empty:
  - `app/brands`
  - `app/campaigns`
  - `app/compensation`
  - `app/deals`
  - `app/deliverables`
  - `app/email_context`
  - `app/files`
  - `app/jobs`
  - any remaining `app/exports` or `app/outreach` schema-only package after earlier branches

Out of scope:

- Do not change API behavior.
- Do not rename fields unless required by Branch 2 template changes.
- Do not introduce generated API clients in this branch.

Verification:

```bash
cd backend
uv run pytest
uv run ruff check .
```

Done criteria:

- Public Pydantic schemas live under `app.schemas`.
- No package exists solely to contain `schemas.py`.
- Route/service imports clearly express horizontal layering.
- Existing backend tests pass.

## Required Documentation Updates

Update these files as part of the relevant branch:

- `AGENTS.md`
- affected completed plan files if they describe old module names as current truth
- OpenAPI export helper references if imports move
- backend tests with renamed endpoint/module expectations

When all branches are merged:

- Update this plan status.
- Move this plan from `plan/todo/` to `plan/completed/`.
- Confirm `plan/todo/` only contains genuinely unfinished work.

## Cross-Branch Merge Rules

- Do not stack all fixes in one branch.
- Do not start Branch 2 from Branch 1 before Branch 1 is merged to `main`.
- Resolve conflicts by preserving the newest product boundary decisions:
  - export is campaign-scoped.
  - templates are generic.
  - no fake domain package.
  - schemas are centralized.
- Because the app is early-stage, do not add compatibility endpoints, alias imports, or duplicate model names unless a temporary alias is strictly required inside one migration file.

## Final Verification

After Branch 4 is merged to `main`, run:

```bash
cd backend
uv run alembic upgrade head
uv run pytest
uv run ruff check .
```

If frontend navigation is touched as part of related cleanup, also run:

```bash
cd frontend
bun run typecheck
bun run build
```

## Done Criteria

- Export code is structurally campaign-owned.
- Template CRUD is generic and not hidden under outreach.
- Shared enums are exposed through `app.enums`.
- Pydantic schemas are centralized under `app.schemas`.
- Schema-only pseudo-module packages are removed.
- No compatibility layer remains for old structural names or old template routes.
- All backend tests and lint checks pass.
- This plan is moved to `plan/completed/` after implementation and verification.
