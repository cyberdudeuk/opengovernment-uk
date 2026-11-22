# 21 · A public body controlled by law: designation into a department's accounts

## What this tests
Control that comes from the law rather than from shares: a UK public body is designated, by an Estimates and Accounts
Order, into a government department's Supply Estimate and accounts. Interest type `controlByLegalFramework`.

## Shape (BODS v0.4)
- 2 `recordType: entity`: the department (`stateBody`, subtype `governmentDepartment`) and the body (`stateBody`)
- 1 `recordType: relationship`, one interest: `controlByLegalFramework`, `direct`, `beneficialOwnershipOrControl: false`,
  with `details` naming the designation
- `source.type: officialRegister`, with the designation order and its fingerprint in `source.description`

## Conformance expectations
- Adapters MUST keep `controlByLegalFramework` (do not collapse it to `otherInfluenceOrControl`).
- Sink adapters mapping to FollowTheMoney SHOULD emit `Control` with `controlType: state` (the published BODS-to-FtM
  mapping does this when the interested party is a state or state body).
- No percentage is stated; a query engine MUST NOT assign one.
