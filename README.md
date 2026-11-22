# OpenGovernment UK

One register of the UK state: every public body the official registers know about, **who it answers to, who pays for it and who owns it**, each fact traced to the authoritative source it came from.

**Site:** https://cyberdudeuk.github.io/opengovernment-uk/ · **Status:** pilot, version 0.3.0 · **Licence:** code MIT, data OGL v3.0 (see [LICENCE-DATA.md](LICENCE-DATA.md))

It isn't an official government list and it isn't affiliated with any public body. It is an open-source public good: corrections, sources and code are welcome from everyone (see [Contributing](CONTRIBUTING.md)).

## What it holds

| | |
|---|---|
| Records | 3,477 bodies (2,824 open): departments, agencies, non-departmental bodies, councils, NHS bodies, devolved bodies, public corporations, Crown Dependencies and Overseas Territories |
| Accountability | 2,522 links, each naming its source, where in the source and how the names were matched; 2,581 open bodies (91%) traced to an elected body |
| Money | Government funding and spend (Public Bodies Directory 2023/24); 654 PFI and PF2 contracts with their project companies and investors |
| Ownership | Companies House controllers, GLEIF consolidation parents, ONS parent companies; trading funds and public corporations |
| Open standards | W3C ORG, DCAT 3, CSVW, SKOS; **BODS 0.4** (Beneficial Ownership Data Standard) with a public-sector extension |

## Feeds

All served from the site and rebuilt from the same run:

| File | What it is |
|---|---|
| `accountability.json` | Links, chains, money, PFI, conflicts, unmatched names and the provenance ledger |
| `edges.csv` | Every accountability, sponsorship and ownership link with its source |
| `accountable-owner.csv` | One row per open body: its accountable owner and the chain to it |
| `ppp.csv` | PFI and PF2 contracts |
| `bods-0.4.json` | The same tree as 4,209 BODS 0.4 statements, validated against the official schema |

The register's key is the owning register's own code as a CURIE, for example `government-organisation:D303`. Join your list by GOV.UK slug or code first, never by name. The full contract is `feed-contract.json` in the page's downloads.

## How it is built

```
tools/fetch.py          read every source; write sources/manifest.json with SHA-256 of each file
tools/build.py          join the sources into data/tree.json (exact cleaned names only; anything else goes to a queue)
tools/check.py          13 checks; --negative proves each one fails on a deliberate break
tools/patch_portal.py   build docs/index.html from the 0.2.2 page plus the accountability view
tools/export_bods.py    emit and validate BODS 0.4 (schema vendored in vendor/bods-schema, commit e8cc3fd)
tools/reconcile_peers.py  reconcile peer reference lists from the National Data Library catalogue
tools/refdata.py        reference data lineage, matched against data.gov.uk
tools/trends.py         public bodies 2012-2024 from the official editions; 2020 baseline reconciled with today
tools/functions.py      back-office classes: A (exists for government) and B (back office as one line of business)
tools/scenarios.py      evolution, reform and revolution to 2030 (modelled, assumptions editable)
tools/corporations.py   one family tree per trading fund and public corporation, grouped by owner
tools/design.py         the design system: tokens to one stylesheet, the shared page shell, the design system page and its guards
tools/localgov.py       local government under the English Devolution and Community Empowerment Act 2026 (current and planned)
tools/sameas.py         one record per body: combines records that are the same body seen by different sources
tools/territories.py    the Crown Dependencies' and Overseas Territories' own bodies, branch by branch
tools/international.py  which UK body leads the UK's place in each international body or trading bloc
tools/sqlite_export.py  one SQLite file for Datasette Lite, and org-id.guide identifiers
tools/instruments.py    rules that apply to each body, what it issues, and legislation naming it
tools/relations.py      the UK's memberships, treaties and agreements, linked to the UK bodies that hold them
tools/orgchart.py      interactive org charts: who answers to whom, nations and branches, type and purpose, the UK in the world
tools/funding.py        grants, business support schemes, regulators' innovation services and grant-makers
tools/personas.py       personas and journeys from one source; checks every route the portal offers them
tools/worldmap.py       world map of treaty partners (world-atlas 2.0.2, Equal Earth); every partner placed or recorded as an organisation or former state
tools/websites.py       each body's own website, from one combined table (matched by code; councils in Scotland and Northern Ireland by exact name within that nation's councils, from the official lists, one-to-one or the build fails)
```

Three source files are **not redistributed** here because they name people (the Public Bodies Directory, Companies House controller pages, the PFI register's investors). `fetch.py --private` downloads them; their fingerprints are in `sources/manifest.json`, so a downloaded copy can be checked against the one the build used.

```
pip install -r requirements.txt
python tools/check.py && python tools/check.py --negative
python tools/fetch.py --private && python tools/build.py   # full rebuild
```

## Running it: effort for one person

| Task | When | Effort |
|---|---|---|
| Run the **Refresh** workflow, read the summary, publish if the checks pass | monthly, or when a source changes | about 30 minutes |
| New editions of the sources: ONS guide (roughly monthly), Estimates and Accounts and WGA orders (yearly), Public Bodies Directory and PFI register (yearly) | as published | 1 to 2 hours each to update the URL in `fetch.py` and review changes |
| Clear the queue of names that didn't match (884 today) | per release | open-ended; worth 1 to 2 hours a release |
| Local government facts (sources/evidence/local-government-2026.json): check the government's reorganisation and devolution announcements | when MHCLG announces decisions (every area is due an outcome by early 2027), then at least quarterly | 30 to 60 minutes |
| Territory bodies and websites: re-read the Wikidata and founding-order evidence files, review exclusions | twice a year | 1 to 2 hours |
| Reconciliation decisions (sources/evidence/reconciliation-decisions.json): decide new items from the body's own page or founding law | when the review queue is not empty | 15 minutes per item |
| International bodies (sources/evidence/international-bodies.json): re-check leads after any machinery-of-government change; confirm the 'still to confirm' list | after each change, at least yearly | 30 to 60 minutes |
| Rules, guidance, treaties and agreements: re-run the GOV.UK, legislation.gov.uk and Wikidata reads (scripts in tools/, about 15 minutes of machine time), review the known answers | quarterly | 30 minutes |
| Funding (Find a grant, GOV.UK schemes, 360Giving registry): re-read; grants open and close weekly | monthly, with the Refresh workflow | 20 minutes |
| Feedback via the GitHub issue form | as it comes | minutes each |

Nothing runs on a schedule: there are no paid services, no secrets and no tokens beyond the read-only one GitHub gives each workflow run.

## Documentation

- [Trends since 2012 and three lenses to 2030](documentation/trends-and-futures-2030.md): what the Cabinet Office's own editions show, the November 2020 baseline checked against today, and modelled scenarios
- [The open-government ecosystem](documentation/ecosystem.md): BODS tools, OCDS contracts, FollowTheMoney, OpenCorporates, OpenSanctions, WhatDoTheyKnow, and what to reuse
- [Information architecture and design review](documentation/ia-and-design-review.md): the brief for 0.4
- [Contributing](CONTRIBUTING.md): how to correct, add sources or improve the code
- [Reference data lineage](documentation/reference-data.md): everything this relies on, everything that relies on it, matched against data.gov.uk
- [BODS public-sector profile](documentation/bods-public-sector-profile.md)
- [Defect register](documentation/defect-register.md) and [the case against](documentation/case-against.md)

## Contact

Use the [feedback form](https://github.com/cyberdudeuk/opengovernment-uk/issues/new?template=feedback.yml). Please don't include names, email addresses or phone numbers.
