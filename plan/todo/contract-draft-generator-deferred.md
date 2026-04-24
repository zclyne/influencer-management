# Contract Draft Generator Deferred Plan

## Status

- Deferred by Notion docs.
- Not part of MVP implementation.
- No ContractDraft table should be created now.

Move this file to `plan/completed/contract-draft-generator-deferred.md` only if the deferred module is intentionally implemented or explicitly closed as out of scope.

## Notion Sources

- Contract Draft Generator doc: deferred, future design placeholder.
- Product doc: contracts remain external for MVP.
- Data model doc: do not add ContractDraft table in MVP.

## Goal

Keep the future contract module boundary explicit so current MVP work does not accidentally bake contract state into Deal or Compensation.

## Current Decision

Do not implement in MVP:

- ContractDraft table.
- Contract template management.
- Google Docs copy/update.
- PDF generation.
- Electronic signature flow.
- Contract status in Deal state machine.

## Future Scope

If reactivated later, the module may support:

- Contract template metadata.
- Template variables.
- Deal-based render context.
- Variable preview and missing-field warnings.
- Draft Google Doc or local document generation.
- Link generated draft back to Deal.

## Future API Sketch

Do not implement now.

Potential future endpoints:

- `GET /api/v1/contract-templates`
- `POST /api/v1/contract-templates`
- `POST /api/v1/deals/{deal_id}/contract-drafts/preview`
- `POST /api/v1/deals/{deal_id}/contract-drafts`
- `GET /api/v1/deals/{deal_id}/contract-drafts`

## Future Render Context

Potential variables:

- brand names.
- campaign name and dates.
- influencer display name.
- primary contact email.
- deliverables summary/table.
- compensation summary/table.

## Guardrails For Current Work

- Do not add contract status to `DealStatus`.
- Do not add contract fields to Deal unless a separate approved plan exists.
- Keep deliverables and compensation data clean enough to feed a future renderer.
- Keep local file management generic enough to store future generated docs.

## Done Criteria For Now

- No implementation work is done for this module during MVP.
- Other modules do not introduce contract-specific shortcuts.
