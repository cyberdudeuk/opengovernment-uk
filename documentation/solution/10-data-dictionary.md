# Data dictionary

Generated from the files themselves by `tools/artefacts.py`, so it always matches them.

## `docs/concordance.csv`

| Field | Meaning | Example |
|---|---|---|
| `id` | Register key: the owning register's code as a CURIE | government-organisation:OT1025 |
| `name` | Current name | Academy for Justice Commissioning |
| `family` | Kind of register record | GOV.UK organisation |
| `status` | open or closed | closed |
| `govuk` |  | OT1025 |
| `govuk_slug` |  | academy-for-justice-commissioning |
| `ons_name` |  |  |
| `gss` |  |  |
| `local_authority` |  |  |
| `nhs_ods` |  |  |
| `companies_house` |  |  |
| `lei` |  |  |
| `charity_ew` |  |  |
| `charity_sc` |  |  |
| `charity_ni` |  |  |
| `wikidata` |  |  |
| `dgu` |  |  |
| `github` |  |  |
| `iati_gb_gov` |  |  |

## `data/edges.csv`

| Field | Meaning | Example |
|---|---|---|
| `child_id` | Body the link starts from | government-organisation:PB523 |
| `child_name` |  | Administration of Radioactive Substances |
| `parent_id` | Body it links to | government-organisation:D12 |
| `parent_name` |  | Department of Health and Social Care |
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
| `type` |  | Other |
| `accountable_owner_id` | Key of the body at the top of the chain | government-organisation:D18 |
| `accountable_owner` |  | Ministry of Justice |
| `answerable_to` |  | Parliament, through the Secretary of Sta |
| `chain` | The chain, each step with relation and source | Academy for Social Justice > Ministry of |
| `sources_agreeing` | Sources naming the same first link | 1 |
| `parents_asserted` |  | 1 |
| `wga_2024_25` |  |  |
| `government_funded_income_gbp` |  |  |
| `total_managed_expenditure_gbp` |  |  |
| `trading_fund` |  | False |
| `ukgi_shareholding` |  | False |

## `docs/ppp.csv`

| Field | Meaning | Example |
|---|---|---|
| `hmt_project_id` |  | 7 |
| `project` |  | Two Schools Project (Jo Richardson Commu |
| `status` | open or closed | In Operation |
| `sector` |  | Schools (Non-BSF) |
| `procuring_authority_id` |  | local-authority:BDG |
| `procuring_authority` |  | Barking and Dagenham London Borough Coun |
| `department_id` |  | government-organisation:D6 |
| `department` |  | Department for Education |
| `project_company` |  | BY EDUCATION (BARKING) |
| `company_number` |  | 04949258 |
| `equity_holders` |  |  |
| `individuals_not_named` |  | 0 |
| `capital_gbp_m` |  | 47.3 |
| `unitary_charge_2025_26_gbp_m` |  | 7.96 |
| `contract_end` |  | 2030-08-31 |
| `esa_balance_sheet` |  | No Data Provided |

## `data/reconciliation-2020.csv`

| Field | Meaning | Example |
|---|---|---|
| `name_2020` |  | Advisory Committee on Animal Feeding stu |
| `department_2020` |  | Food Standards Agency |
| `class_2020` |  | NDPB |
| `register_id` |  |  |
| `register_status` |  |  |
| `closed` |  |  |
| `close_reason` |  |  |
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

Top-level keys: `v`, `built`, `digest`, `legend`, `src`, `e`, `ans`, `ch`, `m`, `w`, `wo`, `tf`, `pcs`, `pw`, `ppp`, `cf`, `cfr`, `un`, `nat`, `cl`, `orgid`, `ins`, `insr`, `relb`, `web`, `sa`, `sar`, `clm`, `vol`, `lg`, `corp`

## `docs/bods-0.4.json`

An array of BODS 0.4 statements (entity and relationship). Public-sector detail is in the `publicAccountability` extension; see documentation/bods-public-sector-profile.md.
