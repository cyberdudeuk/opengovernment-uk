# 20 · A state holding shares and votes in an international body

## What this tests
A state as the interested party: the United Kingdom (`entityType.type: state`) holds a shareholding and voting rights
in the International Bank for Reconstruction and Development (`legalEntity`, identified by its LEI). The figures are
the bank's own published share of subscriptions and share of votes.

## Shape (BODS v0.4)
- 2 `recordType: entity`: the United Kingdom (`state`, jurisdiction GB) and the bank (`legalEntity`, XI-LEI)
- 1 `recordType: relationship` with two interests, both `direct` and `beneficialOwnershipOrControl: false`:
  `shareholding` (share of subscriptions, exact) and `votingRights` (share of votes, exact)
- a namespaced extension, `publicAccountability`, says the state is a member and shareholder

## Conformance expectations
- Adapters MUST keep both interests (do not merge them because they describe one holding).
- Adapters MUST NOT treat the state as a beneficial owner (`beneficialOwnershipOrControl` stays false) nor drop it
  for not being a person: BODS represents state ownership by design.
- Sink adapters SHOULD map the state to a public-body type (for FollowTheMoney, `PublicBody`). FollowTheMoney only lets
  an `Ownership` point at an `Asset`, so a converter needs a rule for an intergovernmental body (this portal uses a
  `Membership` and states the share in its description).
- Query engines asked "who holds the bank" MUST return the state with the stated shares, and MUST NOT add shares across
  sources or invent a total.
