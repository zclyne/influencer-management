# Table Action Column Fixed

## Summary

Make action columns behave consistently across frontend tables.

## Implemented Scope

- Add `fixed: 'right'` to every table column named `Actions`.
- Ensure list pages without horizontal table scroll have `scroll.x` so fixed action columns work correctly.
- Keep existing row actions and table behavior unchanged.

## Verification

- Run frontend typecheck and production build.
