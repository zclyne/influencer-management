# Detail Pages Consistency Review

## Summary

Review and align all current detail/workspace pages: Campaign Workspace, Deal Detail, and Influencer Detail.

## Implemented Scope

- Campaign Workspace deal rows now navigate to Deal Detail instead of Influencer Detail when clicking the creator name.
- Campaign Workspace deal actions distinguish quick drawer review from full Deal Detail navigation.
- Deal Detail exposes top-level actions for opening the campaign, opening the influencer, and editing the deal.
- Deal Detail summary shows status, campaign, lost reason, labels, next action, created time, and updated time.
- Influencer Detail contact conflict copy clarifies that the same email appears on other influencers.
- Influencer Detail action ordering is aligned with other detail pages by putting edit before delete.

## Verification

- Run frontend typecheck and production build.
- Run focused backend campaign, deal, and influencer tests to confirm existing API contracts remain stable.
