# The open-government ecosystem: what to reuse, link or learn from

**Purpose:** make the anatomy of the UK state as transparent as possible for everyone: public servants, journalists, researchers, civil society and the wider economy. Reuse open work before building, link rather than copy, and respect every licence.

**Status:** survey, 22 November 2026. Recommendations are ranked by value for effort, with the effort it takes one maintainer to keep each one running.

## Recommended now

| What | Who | Why it matters here | How we use it | Licence | Effort |
|---|---|---|---|---|---|
| **BODS 0.4** (`data-standard`) | Open Ownership | The UK government's adopted standard for ownership data; models states and state bodies | Already used: `docs/bods-0.4.json` validates against the official schema, with a public-sector extension | Apache 2.0 | Done; re-validate per release |
| **bods-dagre** visualisation library | Open Ownership | Draws BODS 0.4 ownership and control graphs automatically | Render each body's accountability and ownership chain from our BODS file: the horizontal and vertical lineage views | open source (npm `@openownership/bods-dagre`) | Low: a library in the page |
| **lib-cove-bods** data review | Open Ownership / Open Data Services | The official validator and data-quality checks for BODS | Add to CI next to our schema validation, so our output passes the standard's own checks | open source | Low |
| **Find a Tender and Contracts Finder (OCDS)** | Cabinet Office | Every public contract notice, as Open Contracting data | Join buyers to bodies on GOV.UK codes (`GB-GOR` scheme, e.g. Cabinet Office `D2`): contracts and spend per body, PFI linked to procurement | OGL v3.0 | Medium: a monthly fetch |
| **WhatDoTheyKnow authorities dataset** | mySociety | A crowdsourced list of UK public authorities (FOI) | Reconcile record by record as a peer list; link each body to its FOI page; learn from its contributor model | check the dataset page | Low |
| **FollowTheMoney (FtM)** | OpenSanctions / OCCRP | The data model used by journalists' tools (Aleph, OpenSanctions); has `PublicBody`, `Ownership`, `Payment`, `Contract` | Export the register as FtM so investigative tools can load it directly | MIT | Low: one exporter |

## Link, don't copy

| What | Why not copy | How we link |
|---|---|---|
| **OpenCorporates** | Data is ODbL share-alike, and free API keys exclude government departments | Link each company number to its OpenCorporates page (already done); no data copied |
| **OpenSanctions** | Bulk data is CC BY-NC 4.0, free for non-commercial use; commercial and compliance use needs a licence. It also holds personal data (PEPs) | Describe how users can screen the register's PFI project companies and investors themselves; publish nothing from it |
| **Wikidata** | Already used for identifiers | Keep contributing corrections back |

## Worth adopting later

- **bodsdata** (Open Ownership analysis tools): notebook and Datasette patterns for analysts. A Datasette build of our files would give researchers SQL access for free.
- **bodspipelines / bods-gleif-pipeline**: their GLEIF-to-BODS pipeline could replace our own GLEIF reading. It runs on AWS, though, so it isn't free to operate; reuse the mapping, not the infrastructure.
- **360Giving** (GrantNav): grants by public bodies, for "who funds whom" beyond grant-in-aid.
- **Parliament APIs** (committees, written answers): link each body to scrutiny of it.
- **legislation.gov.uk**: link each body to the Act or Order that created it (`formedByStatute`).

## What this means for the design of the portal

- **Different people come with different questions.** Journalists follow money and ownership. Researchers want bulk files and SQL. Civil society wants accountability and FOI. Public servants want reference data and APIs. Businesses want contracts and buyers. Journeys and entry points should be built around these questions (see the review of information architecture).
- **Contribution is the sustainability model.** WhatDoTheyKnow, OpenCorporates and Wikidata all rely on corrections from users. Every page should invite a sourced correction, and the queue of unmatched names is the obvious first task for volunteers.
- **Interoperate with what people already use.** BODS for ownership, OCDS for contracts, FtM for investigations, Datasette for SQL.

## Sources

- Open Ownership GitHub organisation and publications (BODS visualisation library, analysis tools, pipelines)
- OpenSanctions documentation (entity structure, licensing and non-commercial use)
- OpenCorporates API reference and terms of use
- GOV.UK *Open contracting* transparency page; Find a Tender API documentation; Open Contracting Partnership data registry
- mySociety, *WhatDoTheyKnow Authorities Dataset*
