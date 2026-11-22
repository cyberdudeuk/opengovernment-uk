# Low-level design

## Chain tracing (build.py)
1. For each open body, collect candidate first links from each source, keeping the source's own wording of the parent.
2. Match the parent by exact cleaned name, then by name with legal forms removed, then by the council short-name rule (PFI only), then by following GOV.UK successors. Nothing fuzzier.
3. Choose the first link by precedence: EAO, then PBD, then ONS, then GOV.UK, then ownership. Disagreement between sources is recorded as a conflict, never overwritten.
4. Climb until a root: a ministerial or non-ministerial department (non-ministerial departments are terminal), an elected council, a devolved legislature or NHS governance.
5. Reject anything the person rule flags (titles, honorifics) unless it is an office of state, a company or an institution.
6. Write the chain with each step's relation, source key and source location; write a digest of the content.

## Back-office classes (functions.py)
- **A:** the body's name marks it as internal to government (for example a government profession or shared services).
- **B:** the description has a service phrase and a back-office word, and no advice wording.
- Otherwise none. Advisory bodies are excluded by design.

## Trends (trends.py)
Units pinned per edition by an anchor body; HMT GDP deflator, chained into forecast years; like-for-like on bodies present in both years, excluding changes over threefold; 2015 counts only (financial year uncertain).

## Failure behaviour
Every tool exits non-zero on a failed check; CI stops before publication. Negative tests prove each check fails when it should.
