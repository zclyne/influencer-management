# Campaign Workspace Detail Actions

## Summary

Fix the Campaign Workspace page so it presents campaign-level information and actions separately from deal-level table actions.

## Implemented Scope

- Show campaign status, budget, date range, brands, updated time, brief, and notes in the workspace header.
- Add campaign edit and delete actions.
- Redirect to Campaign list after deleting a campaign.
- Move "Add influencers from library" into the Deals table area so the action is clearly tied to deal creation.
- Keep the existing bulk deal creation API and campaign export behavior.

## Verification

- Run frontend typecheck and production build.
- Run focused backend campaign/deal tests if backend contract behavior is touched.
