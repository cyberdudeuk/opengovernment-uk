# Theory of change

**Problem.** No single public place says which bodies make up the UK state, who each one answers to, what it costs and who owns it. The facts exist, but in over a dozen official sources that use different names, codes and dates. Anyone tracing accountability (a journalist, a researcher, a public servant, a citizen) has to rebuild the picture by hand, and gets a different answer each time.

| Inputs | Activities | Outputs | Outcomes | Impact |
|---|---|---|---|---|
| Official open sources (GOV.UK, Estimates and Accounts Orders, ONS classification, Public Bodies directory, Companies House, GLEIF, PFI register, Wikidata, IATI) | Fetch with fingerprints; match names safely; trace each body to the elected body it answers to; check everything; publish in open standards | 3,477 records, 2,522 evidenced links, 2,824 chains, BODS 0.4 statements, trends since 2012, concordance, open feeds | People find who answers for a body in seconds, with the source; apps reuse one register instead of keeping copies; gaps and conflicts are visible and get corrected | A state that is easier to see, scrutinise and simplify: bodies kept only while they serve a purpose, and public money traceable to accountability |

**Assumptions, each with how it is tested**

| Assumption | Test | Status |
|---|---|---|
| The official sources are enough to establish most chains | Share of open bodies with a chain that ends at an elected body | 2,581 of 2,824 (91%); 243 not established, listed with reasons |
| Safe-fail matching avoids wrong joins | Known-answer checks and the conflicts view | Passing; 85 conflicts shown, not resolved silently |
| People will contribute corrections | Issues raised through the forms | Not yet tested: the register is newly public |
| Reusers want open standards rather than a bespoke format | Downloads and requests by format | Not yet measured; no analytics are collected by design |

**What would show this is wrong.** If contributors don't come forward, the register goes stale at the rate the sources change, because one maintainer can't keep up alone. If the official sources start publishing machine-readable accountability themselves, the register should shrink to a reconciliation layer, or retire.
