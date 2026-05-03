# Email Context & Linking Plan

## Status

Superseded.

The original plan used local `EmailAccount`, `EmailThreadMetadata`, and `EmailThreadLink`
database tables. That design no longer matches the product direction.

The current Email module is Gmail-backed:

- Gmail threads and messages are fetched live.
- Campaign/Deal mapping is stored in Gmail labels.
- Local persistence is limited to one Gmail OAuth credential secret.
- No local email business tables should be added for MVP.

See `plan/completed/gmail-label-email-module.md` for the implemented design.
