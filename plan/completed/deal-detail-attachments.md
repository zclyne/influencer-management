# Deal Detail Attachments Plan

Implement Deal-scoped attachments for the standalone Deal Detail page.

## Summary

- Attachments belong to a Deal only.
- Store uploaded files in backend-managed local storage using `StoredFile`.
- Track Deal-to-file ownership through `DealAttachment`.
- Reuse the existing file download endpoint for downloads.

## Backend

- Add `StoredFileKind.DEAL_ATTACHMENT`.
- Add `deal_attachments` table with `deal_id` and `file_id`.
- Add deal-scoped endpoints:
  - `GET /api/v1/deals/{deal_id}/attachments`
  - `POST /api/v1/deals/{deal_id}/attachments`
  - `DELETE /api/v1/deals/{deal_id}/attachments/{attachment_id}`
- Keep upload/delete blocked for archived Deals.

## Frontend

- Load attachments on Deal Detail.
- Replace the placeholder attachment card with upload, list, download, and delete controls.
- Keep v1 metadata read-only: original name, size, MIME type, uploaded time, and exists status.

## Done Criteria

- Backend tests cover upload, list, download, delete, missing Deal, wrong Deal, and archived Deal writes.
- Frontend typecheck and build pass.
