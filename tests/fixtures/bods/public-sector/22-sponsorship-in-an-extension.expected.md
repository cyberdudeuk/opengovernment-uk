# 22 · Sponsorship carried in a namespaced extension, not as ownership

## What this tests
A department sponsors an arm's-length body: it answers for it to Parliament but does not own it. The relationship uses
the weakest fitting interest (`otherInfluenceOrControl`) and puts the public-sector meaning in a namespaced extension
(`publicAccountability`: relation `sponsors`, how the match was made, the source's own wording).

## Shape (BODS v0.4)
- 2 `recordType: entity` (`stateBody`)
- 1 `recordType: relationship`, one interest: `otherInfluenceOrControl`, `beneficialOwnershipOrControl: false`
- `publicAccountability` extension on the relationship

## Conformance expectations
- Validators MUST accept the extension (BODS allows additional properties) and adapters SHOULD carry it through.
- Adapters MUST NOT promote sponsorship to ownership or to a beneficial interest.
- Query engines following "who owns" MUST NOT traverse this link; "who answers for" MAY.
