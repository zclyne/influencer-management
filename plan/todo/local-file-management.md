# Local File Management Plan

## Status

- `StoredFile` model and repository exist.
- No file storage service, app data path policy, upload/import/export integration, or cleanup behavior exists.

When this module is implemented and verified, move this file to `plan/completed/local-file-management.md`.

## Notion Sources

- Technical overview: frontend chooses files, backend processes file contents.
- Backend doc: local file management should cover source files, export CSV, receipts, email attachments, generated docs.
- Data model doc: `StoredFile` stores managed local file references.

## Goal

Define and implement a safe local-first file reference layer for files the backend manages.

## Scope

In scope:

- App data directory resolution.
- Store file metadata in `StoredFile`.
- Copy/import selected files into app-managed storage when needed.
- Generate and register export files.
- Support receipt file references later.
- Detect missing files and return clear errors.

Out of scope:

- Cloud sync.
- File versioning.
- Full attachment preview.
- Electron packaging storage policy. Keep room for later.

## Backend API

MVP internal service first. Public APIs can be added when a feature needs them.

Potential endpoints:

- `GET /api/v1/files/{file_id}`
- `GET /api/v1/files/{file_id}/download`
- `DELETE /api/v1/files/{file_id}`

For desktop file selection, frontend should pass file bytes or a user-approved local path only through explicit endpoints. Do not let arbitrary backend paths be read without validation.

## Backend Design

Add:

- `backend/app/storage/files.py`
- `backend/app/services/files.py`
- optional `backend/app/api/routes/files.py`
- tests in `backend/tests/test_files.py`

Storage layout:

```plain text
APP_DATA_DIR/
  imports/
  exports/
  receipts/
  email_attachments/
  generated/
  logs/
```

Service rules:

- All managed files live under `APP_DATA_DIR`.
- Generate stable internal filenames using ids/checksums, not user-provided names.
- Preserve original name in DB.
- Store checksum and size.
- Never trust path traversal input.
- A missing file should not crash unrelated object reads; return file status where needed.

## StoredFile Kinds

Initial kinds:

- `import_source`
- `campaign_export`
- `receipt`
- `email_attachment`
- `generated_document`

## Integration Points

Influencer ingestion:

- Later, store original source CSV as `import_source` if user wants import history with file recovery.

Export:

- Async exports should create `campaign_export`.

Compensation:

- `receipt_file_id` points to `receipt`.

Email:

- future attachment cache uses `email_attachment`.

Contract:

- future generated docs use `generated_document`.

## Frontend Work

Electron:

- file picker for imports and receipts.
- save dialog for exports.
- clear error when a managed file is missing.

Do not let frontend bypass backend business parsing rules.

## Tests

Backend:

- Store file metadata.
- Reject path traversal.
- Compute checksum and size.
- Download existing managed file.
- Missing file returns clear error.
- Delete removes file or marks metadata unavailable, based on chosen behavior.

## Done Criteria

- Files managed by backend have consistent metadata and storage paths.
- Export and future receipt/import flows have a common file foundation.
- Storage path handling is safe for local desktop use.
- `uv run pytest` and `uv run ruff check .` pass.
