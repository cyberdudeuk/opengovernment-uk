# Working with Open Ownership: what each side could reuse

Status: assessment, 22 November 2026. No arrangement exists yet; nothing here implies endorsement by Open Ownership.
Contact routes are public ones only: Open Ownership's website and the issue trackers of its open-source repositories.

## Why this matters

Open Ownership develops the Beneficial Ownership Data Standard (BODS), which the UK government lists as an open standard
for beneficial ownership information ([GOV.UK, open standards for government: BODS](https://www.gov.uk/government/publications/open-standards-for-government/collect-use-and-exchange-beneficial-ownership-information)).
Open Ownership recommends that companies declare ownership and control by states, and its standard can represent states
and state bodies ([Open Ownership, state-owned enterprises and beneficial ownership disclosures](https://openownership.org/blogs/state-owned-enterprises-and-beneficial-ownership-disclosures);
[BODS 0.4, representing state-owned enterprises](https://standard.openownership.org/en/0.4.0/standard/modelling/repr-state-owned-enterprises.html)).
This portal publishes the UK state's own side of that picture in BODS 0.4: who owns or controls each public body, and the UK's
shares and votes in international financial institutions. The two pieces of work meet at the state.

## What Open Ownership could reuse from this portal

| What | Where | Why it helps them | Confidence |
|---|---|---|---|
| A validated BODS 0.4 dataset of a whole state's public bodies (4,210 statements: 1,694 entities, 2,516 relationships), checked with Open Ownership's own `libcovebods` (no schema errors, no rule findings) | `docs/bods-0.4.json` | A worked public-sector example for their state-owned enterprise guidance; a candidate source for their BODS data analysis tools, which republish national datasets (including the UK's own beneficial-ownership register) | Measured on every build |
| The state as interested party: the United Kingdom as a `state` entity holding shareholding and voting-rights interests in five international financial institutions (IBRD, IDA, IFC, MIGA, AIIB), each identified by its LEI | `docs/bods-0.4.json`, `world.html#tab=own` | A clear case for modelling guidance: a state owning part of an intergovernmental body, with figures from each institution's own table | From official sources, re-read on refresh |
| A public-sector profile: sponsorship, designation into a department's accounts (`controlByLegalFramework`) and accountability chains, carried in a namespaced extension (`publicAccountability`) rather than stretched into ownership | `docs/bods-0.4.json`, `documentation/bods-public-sector-profile.md` | Evidence for whether the standard needs a codelist entry or extension for public accountability | Our proposal; theirs to judge |
| A concordance of codes for each body: GOV.UK, ONS, Companies House, charity numbers, NHS ODS, LEI, Wikidata, GSS and org-id | `docs/concordance.csv`, `docs/data/register.csv` | Lets them recognise UK public bodies when they appear as owners or controllers in company data, by code rather than by name | Each code from its own register |
| Linked data: every body under one HTTP identifier, in the W3C Organization Ontology, with `owl:sameAs` links to Wikidata and LEI | `docs/data/register.jsonld` | Open Ownership publishes an RDF mapping of BODS 0.4; aligning identifiers would let both graphs join | Parsed on every build |

## What this portal could reuse from Open Ownership

| What | Gain for the portal | Effort here |
|---|---|---|
| Their BODS data analysis tools (a catalogue of BODS datasets with Datasette and bulk formats) as a place to list this portal's BODS file | Reach and free hosting for analysis, with nothing extra to run (fits the one-person rule) | About an hour to ask; then nothing, if they pull the published address |
| Their republished UK beneficial-ownership data in BODS | Find companies whose owners or controllers are UK public bodies, by joining on Companies House numbers and the concordance; fills gaps in the public corporation family trees | About a day to build a join and its checks; minutes a quarter after. Person statements must be dropped on read, because this portal never publishes people's names |
| Their visualisation library for ownership diagrams | Draw the trading-fund and public-corporation trees as standard ownership diagrams instead of maintaining our own drawing code | About half a day; small upkeep when the library changes |
| Their data review tool and `libcovebods` (already used in CI) | Independent validation; already in place | None |
| Their state-owned enterprise guidance | A ready-made basis for the public-sector profile, so the portal follows rather than invents | Reading time only |

## A possible arrangement, in three steps

1. **Listing (start here).** Ask, through Open Ownership's public channels, whether the portal's BODS file can be listed in
   their data analysis tools as a public-sector source. Nothing changes on either side except a link. Effort: about an hour.
2. **Shared reconciliation.** Agree that public bodies appearing as owners or controllers in their UK company data are
   matched to this register by code (Companies House number, LEI, GOV.UK code), and publish the matches openly. Each side
   keeps its own data; the join lives in the open. Effort: about a day here; their effort is theirs to judge.
3. **Standard feedback.** Raise the public-sector profile and the state-as-shareholder-of-an-intergovernmental-body case on
   the standard's public issue tracker, with this dataset as the worked example.

## Risks and how they are handled

| Risk | Response |
|---|---|
| Joining with company data brings in people's names | Read only entity and relationship statements whose parties are entities; drop person statements on read; the build's no-personal-names check already fails on any name |
| Sponsorship or accountability read as ownership | Kept in the namespaced `publicAccountability` extension; only real ownership (shares, votes, designation by law) uses BODS interest types |
| Version mismatch: GOV.UK's guidance cites BODS 0.3; this portal publishes 0.4 | State the version on every file; offer a 0.3 view only if a user needs one |
| Implied endorsement | This page says plainly that no arrangement exists; the portal names no affiliation |
| Upkeep for one person | Each step is designed to need no running service: published files at stable addresses, pulled by whoever reuses them |

## Effort to run (one-person band)

Step 1: about an hour once. Step 2: about a day to build, then 15 minutes a quarter. Step 3: an hour per issue raised.
Nothing here adds a server, a schedule or a paid service.
