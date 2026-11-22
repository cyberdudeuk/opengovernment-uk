# Reference data lineage

Built 2026-11-22T04:24:15Z against https://www.data.gov.uk (National Data Library search directory), CKAN package_search.

> score = share of the reference item's name words found in the catalogue title; a lead for a person to confirm, not a confirmed match.

## Upstream: what OpenGovernment UK relies on

| Reference data | Owner | Used for | Kind | Catalogue hits | Best candidate in the catalogue | Score |
|---|---|---|---|---:|---|---:|
| [GOV.UK Organisations API](https://www.gov.uk/api/organisations) | Government Digital Service | identity spine: names, types, parents, successors | register | 22488 | [IATI Organisation Identifier for UK government organisations](https://www.data.gov.uk/dataset/3daf2e08-170e-4aa0-850b-bde231a2031a) (Foreign, Commonwealth and Development Office (FCDO), 2023-12-06) | 0.67 |
| [Public Sector Classification Guide](https://www.ons.gov.uk/methodology/classificationsandstandards/economicstatisticsclassifications/introductiontoeconomicstatisticsclassifications) | Office for National Statistics | sector, ESA code, sponsor, parent company, controlling unit | register | 173 | [National Accounts Sector Classification](https://www.data.gov.uk/dataset/04e8b6c8-2afb-4eec-ae3b-b7c016f1d2f0) (Office for National Statistics, 2026-07-08) | 0.5 |
| [ESA 2010 institutional sector codes](https://ec.europa.eu/eurostat/web/esa-2010) | Eurostat / ONS | sector codes on every ONS-classified body | codelist | 7 | [town_centre_classification](https://www.data.gov.uk/dataset/15b5de65-8028-4e9f-9bb8-3eee11d99f9a) (Colchester Borough Council, 2016-02-10) | 0.25 |
| [Estimates and Accounts Order 2026 (S.I. 2026/216)](https://www.legislation.gov.uk/uksi/2026/216/made) | HM Treasury (legislation.gov.uk) | legal accounting boundary: which department answers for a body's money | legislation | 645 | [Environmental Accounts](https://www.data.gov.uk/dataset/f099c07d-501f-4ced-a952-91edfb42cd7b) (Office for National Statistics, 2026-07-08) | 0.25 |
| [Estimates and Accounts Order (NI) 2026 (S.R. 2026/49)](https://www.legislation.gov.uk/nisr/2026/49/made) | Department of Finance NI (legislation.gov.uk) | the same for Northern Ireland bodies | legislation | 175 | [Mid-year population estimates - Northern Ireland](https://www.data.gov.uk/dataset/0f17c4ca-63ae-4cdc-9704-d2754d731893) (OpenDataNI, 2025-09-23) | 0.6 |
| [Whole of Government Accounts (Designation of Bodies) Order 2026](https://www.legislation.gov.uk/uksi/2026/66/made) | HM Treasury (legislation.gov.uk) | which bodies supply data to WGA | legislation | 845 | [Sub-regional Government Accounts (experimental)](https://www.data.gov.uk/dataset/9a7c52ac-00a0-47de-b8a7-c8c7440f771c) (Office for National Statistics, 2026-07-08) | 0.67 |
| [Whole of Government Accounts 2024-25, Annexes 1-3](https://www.gov.uk/government/collections/whole-of-government-accounts) | HM Treasury | WGA consolidation status per body | dataset | 28 | [Directory of London Businesses](https://www.data.gov.uk/dataset/bf2d8d1b-2aaa-4b6e-a10e-4fae572a1230) (Greater London Authority, 2026-09-25) | 0.0 |
| [Public Bodies Directory 2023/24](https://www.gov.uk/government/collections/public-bodies) | Cabinet Office | sponsor, government funding, spend, classification | dataset | 551 | [Public Bodies 2014](https://www.data.gov.uk/dataset/d942fd6c-3e88-4c1b-8d5d-c51128e8e00a) (Cabinet Office, 2015-04-02) | 1.0 |
| [Current PFI and PF2 projects (31 March 2025)](https://www.gov.uk/government/publications/pfi-and-pfi2-projects-2025-summary-data) | HM Treasury / NISTA | public-private partnerships: authority, project company, investors, charges | dataset | 6203 | [Private Finance Initiative (PFI) Data](https://www.data.gov.uk/dataset/ade9b626-885e-4a70-a438-d0b6f991e922) (HM Treasury, 2026-07-08) | 0.33 |
| [Trading Fund Orders](https://www.legislation.gov.uk/all?title=Trading%20Fund%20Order) | legislation.gov.uk | which operations are trading funds | legislation | 34 | [Bradford Council trade union facility time](https://www.data.gov.uk/dataset/5968ae05-4fe7-4133-b859-9d49e0e532a7) (City of Bradford Metropolitan District Council, 2018-11-07) | 0.0 |
| [Companies House register and persons with significant control](https://find-and-update.company-information.service.gov.uk/) | Companies House | company numbers; who controls government companies | register | 38 | [People with significant control (PSC)](https://www.data.gov.uk/dataset/ef221487-73b6-49a4-9fdc-cd87eda50bbc) (Companies House, 2026-07-08) | 0.4 |
| [Global LEI Index, Level 1 and Level 2](https://www.gleif.org/en/lei-data/gleif-golden-copy) | GLEIF (ISO 17442) | legal entity identifiers; consolidation parents | register | 173 | [Defra electronic legal deposit](https://www.data.gov.uk/dataset/28bec91d-6e1c-4c06-bd8b-f70428497e37) (Department for Environment, Food and Rural Affairs, 2025-04-21) | 0.33 |
| [NHS Organisation Data Service](https://digital.nhs.uk/services/organisation-data-service) | NHS England | codes for NHS bodies | register | 1181 | [Details of NHS organisations in England from Organisation Data Service](https://www.data.gov.uk/dataset/afcd5cb3-9598-4485-8156-475260fef9aa) (NHS Digital, 2017-10-19) | 1.0 |
| [Local authority codes (GSS / ONS geography)](https://geoportal.statistics.gov.uk/) | Office for National Statistics | codes for councils; GSS codes | codelist | 2246 | [Former Local Authority Districts](https://www.data.gov.uk/dataset/7c90716d-4f73-410b-b68b-aa1942f53ee8) (Ministry of Housing, Communities and Local Government, 2017-01-20) | 0.67 |
| [Charity registers (England and Wales, Scotland, Northern Ireland)](https://register-of-charities.charitycommission.gov.uk/) | Charity Commission, OSCR, CCNI | charity numbers of bodies that are charities | register | 2018 | [Register of Charities](https://www.data.gov.uk/dataset/4e5deb54-0485-4cc5-84a3-a72f0d8d3ef3) (OpenDataNI, 2026-07-08) | 1.0 |
| [Wikidata](https://www.wikidata.org/) | Wikimedia Foundation | corroboration and cross-identifiers | register | 0 | not a UK government dataset; not expected in the catalogue |  |
| [data.gov.uk publishers](https://www.data.gov.uk/api/action/organization_list) | National Data Library / GDS | link from each body to its published datasets | register | 11841 | [Data Requests at data.gov.uk](https://www.data.gov.uk/dataset/c79fb418-898c-406d-b1a7-7b4aaeff521d) (Cabinet Office, 2026-07-08) | 0.33 |
| [ISO 3166-2:GB subdivision codes](https://www.iso.org/obp/ui/#iso:code:3166:GB) | ISO / ONS | nation codes (GB-ENG, GB-SCT, GB-WLS, GB-NIR) | codelist | 2290 | [Countries (December 2015) Names and Codes in the UK](https://www.data.gov.uk/dataset/095c0f3a-dfba-45bc-9108-85b9e7493b5d) (Office for National Statistics, 2025-08-11) | 0.0 |
| [org-id.guide identifier schemes](https://org-id.guide/) | Open Data Services | identifier prefixes in the BODS export (GB-COH, GB-CHC …) | identifier scheme | 0 | not a UK government dataset; not expected in the catalogue |  |
| [Beneficial Ownership Data Standard 0.4 codelists](https://standard.openownership.org/) | Open Ownership | entityType and interestType codes in the BODS export | codelist | 0 | not a UK government dataset; not expected in the catalogue |  |
| [Government Functional Standards (GovS 001-015)](https://www.gov.uk/government/collections/functional-standards) | Cabinet Office | back-office function flags (0.4) | codelist | 41 | [National Occupational Standards (NOS) database](https://www.data.gov.uk/dataset/b4053024-bbf7-4d64-a5b9-739890da5d01) (UK Commission for Employment and Skills, 2016-02-10) | 0.5 |

## Downstream: what relies on OpenGovernment UK

| App or dataset | Holds today | Reads from the register | Status |
|---|---|---|---|
| ANA: Anatomy of Government | its own anatomy of departments and arm's-length bodies | `id, name, family, parents, ids.govuk_slug` | proposed |
| GovCRM | party-data.js (organisations as parties) | `id as party key; name; parents` | proposed |
| MEASR data asset register | uk-gov-orgs.json (1,176 organisations), org-resolution.json | `id, name, ids.govuk_slug, joins` | proposed |
| MoG Navigator and the MoG canon | mog-canon.json | `mog-changes.json as its change log; superseding links` | proposed |
| Cadastre | derived organisation feeds | `id, name, family, nations` | proposed |
| AIM Government Data Directorate PMO portal | org-chart.js | `id, name, parents` | proposed |
| GitHub Repos Asset Catalogue | organisation names and GOV.UK slugs per GitHub account | `ids.github, ids.govuk_slug` | proposed |
| Government Technology Intelligence | organisation-level scores | `id, name, family` | proposed |
| DAM Policy returns: SharePoint reference list and Dataverse | data/reference-organisations.csv (308 in-scope bodies), DAM Reference Organisations list, dam_Organisation table | `id, name, accountable_owner, answers_to, wga, ids.govuk_slug` | adopting (0.3.0) |
| Data Interoperability Atlas | estate owners by GOV.UK slug | `ids.govuk_slug, id` | proposed |
| CDA register and CDA Estate Command Dashboard | publishing-body names and WGA status per return | `id, accountable_owner, wga (accountability.json)` | proposed |
| DAM Insight | organisation names on returns | `id, name, accountable_owner` | proposed |
| Social Care Legacy Exit portal | council and NHS body names | `id, ids.local_authority, ids.nhs_ods, answers_to` | proposed |
| Portfolio portal (Government Data Directorate) | departments and bodies in its portfolio | `id, name, accountable_owner` | proposed |
| dcat-ap-uk | publisher URIs | `id as dct:publisher, state.jsonld` | proposed |

## Peer reference datasets in the catalogue

Other lists of public bodies or their codes. Each is a candidate to reconcile record by record.

| Dataset | Publisher | Updated | Formats |
|---|---|---|---|
| [IATI Organisation Identifier for UK government organisations](https://www.data.gov.uk/dataset/3daf2e08-170e-4aa0-850b-bde231a2031a) | Foreign, Commonwealth and Development Office (FCDO) | 2023-12-06 | ODS |
| [Organisation Structure - Local Government Transparency Code](https://www.data.gov.uk/dataset/e6e68c42-bec8-4733-a0ec-52ce0a0d9db8) | North Lincolnshire Council | 2018-04-19 | CSV |
| [Identified Residential Areas](https://www.data.gov.uk/dataset/41d0b2f0-24ac-4142-88ad-0ec6b5fcf38b) | City of London | 2024-04-27 |  |
| [Company identifiers (URIs)](https://www.data.gov.uk/dataset/5a33338a-e142-4f05-9458-ca7283f410b3) | Companies House | 2022-05-30 | CSV, HTML, JSON, PDF, RDF, XML |
| [Marine Management Organisation (MMO) Government Procurement Card spend - transactions over £500](https://www.data.gov.uk/dataset/ccca8ab2-b329-4c8c-b47d-634cd0cd97a5) | Department for Environment, Food and Rural Affairs | 2014-07-21 | CSV |
| [Grants to voluntary, community and social enterprise organisations - Local Government Transparency Code](https://www.data.gov.uk/dataset/cf725d50-6535-4f8b-bc98-5ab01aa866a7) | North Lincolnshire Council | 2018-04-19 | CSV |
| [IPS research publications list](https://www.data.gov.uk/dataset/3f336752-6b0a-483a-a8e4-a2637e720abe) | Identity & Passport Service | 2014-05-10 | HTML |
| [APHA Staff Publication List 2025](https://www.data.gov.uk/dataset/64ba25ae-70a5-473e-bd09-9f84b9c5cceb) | Animal and Plant Health Agency | 2026-03-11 | PDF |
| [APHA Staff Publications List 2024](https://www.data.gov.uk/dataset/a9fa31e5-b99a-4b92-af8d-c635302d32fe) | Animal and Plant Health Agency | 2025-07-08 | PDF |
| [APHA Staff Publications List 2023](https://www.data.gov.uk/dataset/b5d8b099-0d46-4b43-85bd-e926070319fc) | Animal and Plant Health Agency | 2025-07-08 | PDF |
| [Locally Listed Assets (SDC) (Public)](https://www.data.gov.uk/dataset/f8fb64dc-2ae9-4210-bc58-47d9e77998e6) | Sevenoaks District Council | 2026-09-18 | ARCGIS GEOSERVICES REST API, CSV, GEOJSON, HTML, KML, ZIP |
| [APHA Staff Publications List 2014](https://www.data.gov.uk/dataset/5b937732-c088-43ed-805d-efa1dc60dd01) | Animal and Plant Health Agency | 2016-03-24 | CSV |
| [Government Grants Register](https://www.data.gov.uk/dataset/3e9a7045-8f37-4490-b6b5-0f38a4a74e16) | Cabinet Office | 2017-01-20 | CSV, PDF |
| [Marine Management Organisation Evidence Project Register](https://www.data.gov.uk/dataset/03c5b260-19d8-45e9-a7dd-fc4e09df017e) | Marine Management Organisation | 2016-04-21 | CSV, HTML |
| [Marine Management Organisation Master Data Register](https://www.data.gov.uk/dataset/f71fb9f5-d440-40fc-9f63-f4eda2d45d4d) | Marine Management Organisation | 2016-04-20 | CSV, HTML |
| [Department of Finance Information Asset Register](https://www.data.gov.uk/dataset/ea9bf56e-a73c-4e91-a0d6-1c9e68dd54eb) | OpenDataNI | 2026-07-08 |  |
| [Local Authority Eng Register](https://www.data.gov.uk/dataset/05d3b10a-6670-4643-9c53-7efc98775c8d) | Ministry of Housing, Communities and Local Government | 2026-07-08 |  |
| [Local authority sct register](https://www.data.gov.uk/dataset/e138a2a5-a9c3-4bd7-a1de-c2ce40915d30) | Scottish Government | 2026-07-08 |  |
| [Local Authority Data Registers](https://www.data.gov.uk/dataset/58428e98-a61a-4879-b935-8441307b3761) | Food Standards Agency | 2026-06-26 | .CSV, CSV |
| [Local Authority Districts (April 1991) Names and Codes in EW](https://www.data.gov.uk/dataset/805500be-aa02-4a0e-8368-fb52d8d5047b) | Office for National Statistics | 2024-11-24 | ARCGIS GEOSERVICES REST API, CSV, GEOJSON, HTML, KML, ZIP |
| [Local Authority Land](https://www.data.gov.uk/dataset/5e6994be-d539-448f-b325-f689c2e0f198) | London Borough of Camden | 2026-09-25 |  |
| [Local Authority Districts (December 2016) Names and Codes in the UK](https://www.data.gov.uk/dataset/724cb887-c270-4e36-8fbf-edbed4524b01) | Office for National Statistics | 2024-11-24 | ARCGIS GEOSERVICES REST API, CSV, GEOJSON, HTML, KML, ZIP |
| [Tax Arrangements of public sector employees – data from DCMS arm’s length bodies](https://www.data.gov.uk/dataset/5be500b0-b0e8-4a21-8e9f-fab453ca5479) | Department for Digital, Culture, Media and Sport | 2013-12-04 | XLS |
| [Official Development Assistance (ODA) Arms Length Bodies and Soft Power Programmes](https://www.data.gov.uk/dataset/98df2329-432d-4c3a-9c98-863392ea0401) | Foreign and Commonwealth Office | 2026-07-08 |  |
| [Ministry of Justice - Arms Length Body - GPC transactions of £500 and above](https://www.data.gov.uk/dataset/0bbd58e0-df93-425d-9251-d000e9bc948e) | Ministry of Justice | 2014-01-10 | CSV |
| [Greening Government data for DCLG and Arms' Length Bodies [also DfE]](https://www.data.gov.uk/dataset/bb4e8c6f-8bc8-4d54-93cb-a7a7bd343370) | Ministry of Housing, Communities and Local Government | 2013-12-19 |  |
| [Spend over £25,000 in the Ministry of Justice Arms-Length Bodies](https://www.data.gov.uk/dataset/e62c7888-5b44-46a5-a888-65bd0660b9a7) | Ministry of Justice | 2013-08-12 | CSV/ZIP, ZIP |
| [Spend over £25,000 in the Department for Transport and its arms-length bodies](https://www.data.gov.uk/dataset/804be0c6-ae01-4899-bbb9-2317dff1a4f9) | Department for Transport | 2026-10-29 | .CSV, CSV, XLS, XLX |
| [Public Sector Productivity Estimates: Total Public Sector](https://www.data.gov.uk/dataset/72409bf9-8e9e-4098-932f-73a0dcbc0297) | Office for National Statistics | 2026-07-08 |  |
| [Grants to third sector organisations](https://www.data.gov.uk/dataset/89d360d8-a6ec-438c-86e9-d78bb30a190e) | Data Mill North | 2026-09-25 | DOC, PDF |
| [Public Sector Finances](https://www.data.gov.uk/dataset/ee59f8e5-5103-43d4-8c32-dce0a5978a09) | Office for National Statistics | 2026-07-08 | HTML, HTMLHTML |
| [Public Sector Statistics](https://www.data.gov.uk/dataset/546d00b0-f44a-4ea6-bf77-7dad9f64abd9) | Office for National Statistics | 2026-07-08 | HTML |
| [Public Sector Employment](https://www.data.gov.uk/dataset/a7affd12-23e9-49cc-b2e9-da7052faaf62) | Office for National Statistics | 2026-07-08 | HTML |
| [Public Sector Finances](https://www.data.gov.uk/dataset/b1e67a88-db41-4fbd-ae7c-f502276e1ef1) | HM Treasury | 2026-07-08 |  |

## Gaps

- OpenGovernment UK itself is not yet in the catalogue. Registering it (DCAT record already in the page) is a release task.
- Scores below 0.5 mean no clear catalogue entry for that reference data: either it isn't catalogued or it is catalogued under another name. Each needs a person to look.
