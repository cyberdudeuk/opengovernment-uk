# Data dictionary

Generated from the files themselves by `tools/artefacts.py`, so it always matches them. The build fails if any column has no meaning written.

## `docs/data/register.csv`

| Field | Meaning | Example |
|---|---|---|
| `id` | Register key: the owning register's code as a CURIE | government-organisation:OT1025 |
| `name` | Current name | Academy for Justice Commissioning |
| `family` | Kind of register record | GOV.UK organisation |
| `kind` | Kind of body (department, agency, council and so on) | Other |
| `status` | open or closed | closed |
| `nations` | Nations it serves: EN, SC, WA, NI, or UK |  |
| `parents` | Register keys of the bodies it answers to |  |
| `start` | Date it was set up, where a source states it |  |
| `end` | Date it closed, where it has |  |
| `website` | Official website |  |
| `btype` | Body type key (see taxonomies.skos.jsonld) |  |
| `purpose` | What it is for, grouped by UN COFOG (worked out, not official) |  |
| `activity` | What it does (worked out from kind, name and description, so a few may be wrong) |  |
| `reach` | Whom it serves (worked out) |  |
| `wikidata` | Wikidata item (corroborating only) |  |
| `lei` | Legal Entity Identifier (ISO 17442) |  |
| `companies_house` | Companies House company number |  |
| `org_id` | org-id.guide identifier |  |

## `docs/concordance.csv`

| Field | Meaning | Example |
|---|---|---|
| `id` | Register key: the owning register's code as a CURIE | government-organisation:OT1025 |
| `name` | Current name | Academy for Justice Commissioning |
| `family` | Kind of register record | GOV.UK organisation |
| `status` | open or closed | closed |
| `govuk` | GOV.UK organisation code | OT1025 |
| `govuk_slug` | GOV.UK organisation slug (the end of its www.gov.uk/government/organisations/ address) | academy-for-justice-commissioning |
| `ons_name` | Name as the ONS Public Sector Classification Guide writes it |  |
| `gss` | ONS Government Statistical Service code (councils and other areas) |  |
| `local_authority` | Local authority code (GB-LAE register) |  |
| `nhs_ods` | NHS Organisation Data Service code |  |
| `companies_house` | Companies House company number |  |
| `lei` | Legal Entity Identifier (ISO 17442) |  |
| `charity_ew` | Charity Commission for England and Wales number |  |
| `charity_sc` | Scottish Charity Regulator number (none matched yet) |  |
| `charity_ni` | Charity Commission for Northern Ireland number (none matched yet) |  |
| `wikidata` | Wikidata item (corroborating only) |  |
| `dgu` | data.gov.uk publisher slug |  |
| `github` | GitHub organisation the body publishes code under |  |
| `iati_gb_gov` | IATI organisation identifier (international aid reporting) |  |

## `data/edges.csv`

| Field | Meaning | Example |
|---|---|---|
| `child_id` | Body the link starts from | government-organisation:PB523 |
| `child_name` | Name of the body the link starts from | Administration of Radioactive Substances |
| `parent_id` | Body it links to | government-organisation:D12 |
| `parent_name` | Name of the body it links to, as the register names it | Department of Health and Social Care |
| `parent_as_written` | Parent's name exactly as the source wrote it | Department of Health and Social Care |
| `relation` | accounts, sponsors, controls, parent or owns | accounts |
| `source` | Source key (see sources/manifest.json) | eao |
| `source_ref` | Where in the source | Schedule, part: Department of Health and |
| `match_method` | How the two names were matched | body: name, cleaned; department: name, c |

## `data/accountable-owner.csv`

| Field | Meaning | Example |
|---|---|---|
| `id` | Register key: the owning register's code as a CURIE | government-organisation:OT1276 |
| `name` | Current name | Academy for Social Justice |
| `family` | Kind of register record | GOV.UK organisation |
| `type` | Kind of body as its register states it (for example Executive agency) | Other |
| `accountable_owner_id` | Key of the body at the top of the chain | government-organisation:D18 |
| `accountable_owner` | Name of the body at the top of the chain | Ministry of Justice |
| `answerable_to` | Elected body it answers to in the end | Parliament, through the Secretary of Sta |
| `chain` | The chain, each step with relation and source | Academy for Social Justice > Ministry of |
| `sources_agreeing` | Sources naming the same first link | 1 |
| `parents_asserted` | Number of first links the sources assert (more than 1 means sources disagree) | 1 |
| `wga_2024_25` | Status in the Whole of Government Accounts 2024-25 (for example consolidated), blank if not listed |  |
| `government_funded_income_gbp` | Income from government in pounds, from the Public Bodies Directory 2023/24, blank if not stated |  |
| `total_managed_expenditure_gbp` | Total managed expenditure in pounds, from the Public Bodies Directory 2023/24, blank if not stated |  |
| `trading_fund` | True if a trading fund order names it | False |
| `ukgi_shareholding` | True if UK Government Investments manages the government's shareholding in it | False |

## `docs/ppp.csv`

| Field | Meaning | Example |
|---|---|---|
| `hmt_project_id` | HM Treasury's project number | 7 |
| `project` | Project name as HM Treasury writes it | Two Schools Project (Jo Richardson Commu |
| `status` | Project status as HM Treasury states it (for example In Operation) | In Operation |
| `sector` | Sector as HM Treasury writes it | Schools (Non-BSF) |
| `procuring_authority_id` | Register key of the public body that procured the project | local-authority:BDG |
| `procuring_authority` | Public body that procured the project, as HM Treasury writes it | Barking and Dagenham London Borough Coun |
| `department_id` | Register key of the sponsoring department | government-organisation:D6 |
| `department` | Sponsoring department, as HM Treasury writes it | Department for Education |
| `project_company` | The private project company (special purpose vehicle) | BY EDUCATION (BARKING) |
| `company_number` | Companies House number of the project company | 04949258 |
| `equity_holders` | Companies holding equity in the project company, each with its share (1.0 = 100%) |  |
| `individuals_not_named` | Number of individual shareholders left out because they are people | 0 |
| `capital_gbp_m` | Capital value in millions of pounds, as HM Treasury states it | 47.3 |
| `unitary_charge_2025_26_gbp_m` | Unitary charge (the annual payment) for 2025-26 in millions of pounds | 7.96 |
| `contract_end` | Date the contract ends | 2030-08-31 |
| `esa_balance_sheet` | Whether the project is on the public balance sheet under ESA 2010, as HM Treasury states it | No Data Provided |

## `data/reconciliation-2020.csv`

| Field | Meaning | Example |
|---|---|---|
| `name_2020` | Name in the 2020 public bodies list | Advisory Committee on Animal Feeding stu |
| `department_2020` | Department in the 2020 list | Food Standards Agency |
| `class_2020` | Classification in the 2020 list (for example NDPB) | NDPB |
| `register_id` | Register key it was matched to, blank if none |  |
| `register_status` | open or closed in the register now |  |
| `closed` | Date it closed, from GOV.UK |  |
| `close_reason` | Why it closed, from GOV.UK (replaced, merged, no_longer_exists and so on) |  |
| `in_directory_2023_24` | Also listed in the 2023/24 directory | False |
| `verdict` | current, replaced (with successor), closed, or for a person | not matched: for a person |

## `data/tree.json`

Top-level keys: `v`, `built`, `sources`, `stats`, `rels`, `edges`, `chains`, `conflicts`, `unresolved`, `ppp`, `digest`

## `data/public-bodies-trends.json`

Top-level keys: `editions`, `deflator_source`, `deflator`

## `data/scenarios-2030.json`

Top-level keys: `modelled`, `prices`, `baseline`, `known`, `lenses`

## `data/back-office.json`

Top-level keys: `source`, `functions`, `bodies`

## `docs/accountability.json`

Top-level keys: `v`, `built`, `digest`, `legend`, `src`, `e`, `ans`, `ch`, `m`, `w`, `wo`, `tf`, `pcs`, `pw`, `ppp`, `cf`, `cfr`, `un`, `nat`, `cl`, `orgid`, `ins`, `insr`, `relb`, `fund`, `personas`, `web`, `sa`, `sar`, `clm`, `vol`, `lg`, `corp`, `news`

## `docs/bods-0.4.json`

An array of BODS 0.4 statements (entity and relationship). Public-sector detail is in the `publicAccountability` extension; see documentation/bods-public-sector-profile.md.

## `docs/data/register.ftm.json`

One FollowTheMoney entity per line. Meanings are FollowTheMoney's own labels, read from its compiled model.

| Schema | Property | Meaning | Entities with it |
|---|---|---|---|
| Company | `classification` | Classification as provided by the data source or inferred based on other provided data; prefer `sector` if relevant | 58 |
| Company | `country` | An association between the entity and a country that is not covered by a more specific property (e.g. `jurisdiction`, `birthCountry`, `mainCountry`) | 59 |
| Company | `dissolutionDate` | The date the legal entity was dissolved, if applicable | 1 |
| Company | `incorporationDate` | The date the legal entity was incorporated | 30 |
| Company | `leiCode` | Legal Entity Identifier | 51 |
| Company | `name` | The primary name of the entity | 59 |
| Company | `publisher` | Publishing source | 59 |
| Company | `publisherUrl` | Publishing source URL | 59 |
| Company | `registrationNumber` | Company registration number | 59 |
| Company | `sourceUrl` | A deep link to a source website for the profile | 59 |
| Company | `status` | A short string describing how 'active' (broadly defined) an entity is | 59 |
| Company | `website` | Website address | 23 |
| Company | `wikidataId` | Wikidata ID | 15 |
| Control | `controlType` | The mechanism through which control is exercised | 322 |
| Control | `controlled` | The entity being controlled | 2504 |
| Control | `controller` | The entity exercising control | 2504 |
| Control | `publisher` | Publishing source | 2504 |
| Control | `publisherUrl` | Publishing source URL | 2504 |
| Control | `role` | Role | 2504 |
| Control | `sourceUrl` | A deep link to a source website for the profile | 2504 |
| Control | `summary` | Summary | 2504 |
| Membership | `description` | Description | 5 |
| Membership | `endDate` | The date of expiry of a document, or on which a relationship, sanctioned status, occupation, etc. ended | 5 |
| Membership | `member` | Member | 74 |
| Membership | `organization` | Organization | 74 |
| Membership | `publisher` | Publishing source | 74 |
| Membership | `publisherUrl` | Publishing source URL | 74 |
| Membership | `role` | Role | 74 |
| Membership | `sourceUrl` | A deep link to a source website for the profile | 5 |
| Membership | `startDate` | The date of issue of a document, or on which a relationship, sanctioned status, occupation, etc. started | 32 |
| Membership | `status` | Status | 69 |
| Membership | `summary` | Summary | 5 |
| Organization | `leiCode` | Legal Entity Identifier | 5 |
| Organization | `name` | The primary name of the entity | 74 |
| Organization | `publisher` | Publishing source | 74 |
| Organization | `publisherUrl` | Publishing source URL | 74 |
| Organization | `sourceUrl` | A deep link to a source website for the profile | 5 |
| Organization | `website` | Website address | 42 |
| Organization | `wikidataId` | Wikidata ID | 57 |
| Ownership | `asset` | Asset | 7 |
| Ownership | `owner` | Owner | 7 |
| Ownership | `publisher` | Publishing source | 7 |
| Ownership | `publisherUrl` | Publishing source URL | 7 |
| Ownership | `role` | Role | 7 |
| Ownership | `sourceUrl` | A deep link to a source website for the profile | 7 |
| Ownership | `summary` | Summary | 7 |
| PublicBody | `classification` | Classification as provided by the data source or inferred based on other provided data; prefer `sector` if relevant | 2766 |
| PublicBody | `country` | An association between the entity and a country that is not covered by a more specific property (e.g. `jurisdiction`, `birthCountry`, `mainCountry`) | 3418 |
| PublicBody | `dissolutionDate` | The date the legal entity was dissolved, if applicable | 227 |
| PublicBody | `incorporationDate` | The date the legal entity was incorporated | 830 |
| PublicBody | `leiCode` | Legal Entity Identifier | 255 |
| PublicBody | `name` | The primary name of the entity | 3418 |
| PublicBody | `publisher` | Publishing source | 3418 |
| PublicBody | `publisherUrl` | Publishing source URL | 3418 |
| PublicBody | `sourceUrl` | A deep link to a source website for the profile | 3418 |
| PublicBody | `status` | A short string describing how 'active' (broadly defined) an entity is | 3418 |
| PublicBody | `website` | Website address | 1295 |
| PublicBody | `wikidataId` | Wikidata ID | 1098 |
| Succession | `date` | Date associated with an Interval that isn't explicitly its `startDate` or `endDate` (prefer those when available) | 143 |
| Succession | `predecessor` | Predecessor | 272 |
| Succession | `publisher` | Publishing source | 272 |
| Succession | `publisherUrl` | Publishing source URL | 272 |
| Succession | `role` | Role | 272 |
| Succession | `successor` | Successor | 272 |

## `docs/data/source-status.json`

How each source stands at this build (written by `tools/sources_check.py`).

| Field | Meaning |
|---|---|
| `as_of` | The build's latest read; ages count from it |
| `sources[].status` | current, stale (read more than twice its change interval before `as_of`) or not read |
| `sources[].frequency_days` | How often the publisher changes the source, in days |
| `sources[].next_due` | When the source is next expected to change |
| `sources[].official` | True if published by the body responsible for it |
| `not_read[]` | Parts of sources that could not be read, each with the reason |
| `counts[]` | Each expected count, its range, and whether it is in range |

Top-level keys: `about`, `as_of`, `sources`, `not_read`, `counts`
