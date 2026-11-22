# National and supranational comparators: the best of each, adopted here

**Status:** survey, 22 November 2026. Each comparator was read from its owner's own pages; an adoption is marked **done**, **0.4** or **later**.

## The comparators

| Comparator | Owner | What it is | Best feature |
|---|---|---|---|
| **Australian Government Organisations Register (AGOR)** | Department of Finance, Australia | 1,371 bodies, 13 types in 4 broad classes; searchable on directory.gov.au; quarterly CSV snapshots on data.gov.au (CC BY 3.0 AU) | Every body records the legislation it was **established by or under**, its **Government Finance Statistics function and sector**, and whether the Public Service Act applies; **quarterly dashboard** of bodies added and abolished; a **register of movements** |
| **Inventory of Federal Organizations and Interests**, with **GC InfoBase** | Treasury Board Secretariat, Canada | Every federal organisation, plus the **interests** the government holds (mixed and joint enterprises, international organisations), with spending and FTEs by programme | **Interests** as a category: where government owns shares or appoints board members, short of control. A separate **names-and-codes reference list with a concordance** file. Interactive visual stories for citizens |
| **Public sector organisations dataset** | Public Service Commission (Te Kawa Mataaho), New Zealand | Current and historical agencies, with **establishment and disestablishment dates**, agency types, a business number and **Māori names** | History as data, and names in the official second language as standard; a diagram of **how the public sector is organised** across all branches |
| **Federal Hierarchy (SAM.gov)** and **Federal Register agencies API** | GSA and National Archives, USA | Departments, agencies and sub-tiers with parent links | **Parent history** held as data (who an organisation sat under, and when) |
| **allusgov** | CivicActions (civil society, USA) | Consolidates nine US directories into one organisational map | The same method as this register: many official lists, one reconciled graph, every source kept |
| **EU Whoiswho** | Publications Office of the EU | The official directory of EU institutions, bodies and agencies, with archives back to the 1980s | **Snapshots archived over decades**; one directory across every institution. It lists named staff, which this register deliberately does not |
| **COFOG** | UN Statistics Division, OECD, Eurostat | The international Classification of the Functions of Government: 10 divisions, with groups and classes | A **function code** that makes UK bodies comparable with any country's; used by ONS; a UN revision is due to report in 2027 |

## What we adopt

| From | Adoption | Status |
|---|---|---|
| Canada | **Concordance file**: one row per body, every identifier it has in every register (`docs/concordance.csv`) | **done** |
| Australia | **Established by or under**: link each body to its founding Act or Order on legislation.gov.uk (BODS `formedByStatute`) | 0.4 |
| Australia, UN | **Function code**: COFOG division and group for every body, alongside the back-office classes A and B | 0.4 |
| Australia | **Quarterly movements dashboard**: bodies added, abolished and reclassified, with the register of movements as a feed | 0.4 (the data exists in Changes) |
| Canada | **Interests**: bodies where government holds shares or appoints board members without control, from Companies House controllers, PFI equity and UKGI | 0.4 |
| USA | **Parent history over time**: who each body answered to, and when, built from the dated editions and GOV.UK changes | 0.4 |
| New Zealand | **Names in Welsh, Gaelic and Irish** where a body has one; **branches of the state** as the top of the hierarchy (legislature, executive, judiciary) | later |
| EU Whoiswho | **Snapshot archive**: every release kept and downloadable, so any past state can be cited | later |
| allusgov | **Method check**: compare sources and the reconciliation approach, and share findings openly | later |

## What we do differently, on purpose

- **No personal data.** Unlike Whoiswho, AGOR's appointments register and GC InfoBase's people data, this register describes offices and roles, never named people.
- **Accountability chains.** None of the comparators traces each body, source by source, to the elected body it answers to. That stays this register's distinctive contribution.
- **Open by construction.** The code, checks and evidence are public, and corrections come from anyone, with a cited source.

## Sources

- Department of Finance (Australia): *Australian Government Organisations Register*, *Types of Bodies* and *Guide to Fields*; data.gov.au AGOR dataset
- Treasury Board of Canada Secretariat: *Inventory of Federal Organizations and Interests*; *Overview of federal organizations and interests*; Open Government Portal, *GC InfoBase open datasets* and *Government of Canada organization names and codes*
- Te Kawa Mataaho Public Service Commission: *How the public sector is organised*; Digital.govt.nz, *Agency name open dataset*
- GSA *Federal Hierarchy public API*; Federal Register *agencies API*; CivicActions `allusgov`
- Publications Office of the EU: *EU Whoiswho* and archives
- UN Statistics Division: *Classification of the Functions of Government*
