# BODS public-sector profile (draft)

**Status:** draft for discussion. The output (`docs/bods-0.4.json`) validates against the official BODS 0.4 schema (vendored at commit e8cc3fd).

## Why BODS rather than a new standard

The Beneficial Ownership Data Standard is the UK government's adopted open standard for ownership data, and version 0.4 already models the state:

- entity types `state` and `stateBody`, with subtypes `governmentDepartment` and `stateAgency`
- interest type `controlByLegalFramework` ("control of an entity gained through a legal framework … created by governments and legislators to establish and guide agencies and entities linked to the state")
- a `formedByStatute` property on entities

What it lacks is the public sector's own relations: answering to Parliament through an Estimate, sponsorship, funding, consolidation in the Whole of Government Accounts, regulation and inspection. Those travel in a namespaced extension so that standard BODS tools still read the file.

## Mapping

| Register relation | Source | BODS interest type | Extension `publicAccountability.relation` |
|---|---|---|---|
| Included in a department's Estimate and accounts | Estimates and Accounts Orders (UK, NI) | `controlByLegalFramework` | `accounts` |
| Sponsored by | Public Bodies Directory, ONS | `otherInfluenceOrControl` | `sponsors` |
| Controlled by (non-institutional unit) | ONS | `otherInfluenceOrControl` | `controls` |
| GOV.UK parent organisation | GOV.UK | `otherInfluenceOrControl` | `parent` |
| Owned or controlled by | Companies House controllers | `shareholding`, `votingRights`, `appointmentOfBoard` with share ranges | `owns` |
| Parent company | ONS | `shareholding` (share not published) | `owns` |
| Accounting consolidation parent | GLEIF Level 2 | `otherInfluenceOrControl` | `owns` |

Entity statements carry `publicAccountability.answersTo` (the elected body at the end of the chain), `accountableOwner`, `sourcesAgreeing`, WGA status, government funding and a trading-fund flag.

## Identifiers

org-id.guide schemes where they exist: `GB-GOVUK`, `GB-GOV` (IATI, FCDO list), `GB-COH`, `GB-CHC`, `GB-SC`, `GB-NIC`, `GB-NHS`, `GB-LAE`, `XI-LEI`, plus the register key under `OGUK`.

## Proposed additions for a public-sector profile

1. Relation codes for `accounts`, `sponsors`, `funds` (grant-in-aid), `designatedForWGA`, `regulates`, `inspects`, `answersToLegislature`.
2. `branchOfState`: legislature, executive, judiciary.
3. `formedByStatute.uri`: a legislation.gov.uk link, not only a name and date.
4. Money on relationships: amount, year and source, so funding flows sit beside control.

## Links to neighbouring standards

| Standard | How it connects |
|---|---|
| OCDS (Open Contracting) | PFI contracts: buyer = procuring authority, supplier = project company; investors are BODS relationships of the supplier |
| 360Giving | Grant-in-aid from department to body |
| W3C ORG | `org:subOrganizationOf` for the register's parent links (`state.jsonld`) |
| DCAT 3 | The catalogue record for every feed |
| ISO 17442 (LEI) | Legal entity identifiers, GLEIF parents |
| ESA 2010 | ONS sector codes |
| IATI organisation identifiers | `GB-GOV-n` codes for UK government organisations |

People are never statements in this profile: offices are described by role, and natural persons with control are counted, not named.
