# Defect register

Internal record, kept in the repository rather than on the portal. Every defect has a guard: a check, a test or a build rule that fails if it comes back.

| ID | What went wrong | Fix and guard |
|---|---|---|
| OR-D1 | Curly and straight apostrophes matched differently (first pilot) | Folding normalises them; check OG-02 includes a case |
| OR-D2 | At 320 pixels every view was wider than the screen (first pilot) | Grids use minmax with min(100%); the page check below measures it |
| OG-D1 | NHS ODS role codes were guessed and returned councils and support units | Codes read from the ODS roles list; the harvest fails if a role returns the wrong description |
| OG-D2 | The Northern Ireland training board borrowed the Great Britain board's Wikidata item when its "(NI)" was stripped | Nation brackets are never stripped for Wikidata lookups, and evidence can't override an explicit nation conflict (OG-04) |
| OG-D3 | Two checks passed their own deliberate breaks (OG-04 looked at any evidence, OG-08 accepted an empty list) | Both rewritten; every check now fails its break |
| OG-D4 | "HM Courts Service" joined "The Court Service", a predecessor body, because HM was ignored | HM is a significant word; the pair goes to a person |
| OG-D5 | The data.gov.uk API caps each page at 25 publishers, so the new harvester kept 25 of 1,045 | Page until a page is empty; the harvest refuses a list under 500 |
| OG-UX-01 | In the first pilot's review, the whole panel looked selected, so you couldn't tell which answer was chosen | Each answer is its own option with a tick, a fill and a Selected label; the choice is also stated in words |
| OG-D6 | Companies House pages nest the name of a person with significant control inside a second element, so the first reader found none | The reader takes the nested text; 45 of 59 companies now show their controller |
| OG-D7 | An office of state (“Lord Chancellor's Department”) was treated as a person's name and withheld | The person rule excludes offices of state; check D-OG4 tests both directions |
| OG-D8 | Companies named after a founder (“Sir … Enterprises Ltd”) were treated as people | A company legal form keeps the name; a bare title and name is still withheld |
| OG-D9 | Non-ministerial departments climbed to the ministry GOV.UK lists as their parent | A non-ministerial department is its own root; check D-OG3 |
| OG-D10 | The footer named the former office | It now names the Government Data Directorate; a check fails the build on the old name |
| D-039 | Choice labels containing brackets broke the SharePoint schema parser (DAM returns) | Quoted-item pattern; regression test |
| OG-D11 | Feed contract download disagreed with the page | Regenerated from the same contract object (D-OG6) |
| OG-D12 | A page constant was read before it was defined, so the page stopped (temporal dead zone) | Definition moved before first use (D-OG7) |
| OG-D13 | Phone-width masthead clipped the title; a long select scrolled the page sideways | Labels visually hidden under 520 px; grid column minmax(0,1fr); selfcheck 'no sideways scrolling' |
| OG-D14 | Footer named an employer | Neutral authorship line; the build fails if the footer names a government body (D-OG9) |
| OG-D15 | Raw sources that name people were candidates for a public repository | Not redistributed; fetched by the pipeline; the hash check requires them to be declared (D-OG10) |
| OG-D16 | GitHub push protection read a legislation.gov.uk effect identifier ("key-" + 32 hex characters) in the Northern Ireland order as a Mailgun API key | The file is fetched, not committed; its fingerprint stays in the manifest (D-OG11). Push protection is left on |
