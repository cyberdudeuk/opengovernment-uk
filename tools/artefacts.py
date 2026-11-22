"""Generate the traceable parts of the documentation bundle from one spine:
needs -> requirements -> components -> checks -> outputs, with the documents that describe each.
Writes: documentation/solution/05-requirements-specification.md, 10-data-dictionary.md, ontology.ttl,
knowledge-graph.jsonld, traceability.json, and docs/navigator.html (interactive lineage).
The data dictionary is read from the real files, so it cannot drift from them."""
import collections, csv, json, pathlib, re, sys
import rdflib

ROOT = pathlib.Path(__file__).resolve().parents[1]; SOL = ROOT / "documentation" / "solution"; SOL.mkdir(parents=True, exist_ok=True)
NEEDS = {
    "N1": "Know which public bodies exist, keyed by an authoritative code",
    "N2": "Know who each body answers to, in the end, and on what evidence",
    "N3": "Follow the money: funding, running costs, PFI and contracts",
    "N4": "Know who owns or controls each body",
    "N5": "See how the state has changed, and where it is heading",
    "N6": "Reuse the data safely in other apps and tools, in open standards",
    "N7": "Trust it: sources, method, checks and limits in plain view",
    "N8": "Help improve it: correct, add sources, contribute code",
}
# id: (text, priority, status, needs, components)
REQS = {
    "OG-R01": ("One record per UK public body, keyed by its own register's code", "Must", "Done", ["N1"], ["C-REG"]),
    "OG-R02": ("Safe-fail matching: no wrong joins", "Must", "Done", ["N1", "N7"], ["C-REG", "C-BUILD"]),
    "OG-R04": ("Every join explains its method and evidence", "Must", "Done", ["N7"], ["C-REG", "C-BUILD"]),
    "OG-R05": ("Pan-UK coverage including devolved bodies, Crown Dependencies and Overseas Territories", "Must", "Done", ["N1"], ["C-REG"]),
    "OG-R08": ("Open-standard exports (ORG, DCAT, CSVW, SKOS)", "Must", "Done", ["N6"], ["C-PORTAL"]),
    "OG-R09": ("Feed contract for estate apps", "Must", "Done", ["N6"], ["C-PORTAL"]),
    "OG-R11": ("Refresh on demand, reviewed before publishing", "Must", "Done", ["N7"], ["C-CI"]),
    "OG-R12": ("Charity registers joined", "Should", "Planned", ["N1"], []),
    "OG-R16": ("Assistant that answers from the register", "Should", "Done", ["N1", "N2"], ["C-PORTAL"]),
    "OG-R20": ("Official endorsement and a permanent home", "Must", "Planned", ["N7"], []),
    "OG-R21": ("Who answers for each body, traced to the law and the sponsor", "Must", "Done", ["N2"], ["C-BUILD", "C-PORTAL"]),
    "OG-R22": ("Follow the money: government funding and PFI charges", "Must", "Done", ["N3"], ["C-BUILD", "C-PORTAL"]),
    "OG-R23": ("Ownership: Companies House controllers, GLEIF parents, PFI investors", "Must", "Done", ["N4"], ["C-BUILD", "C-PORTAL"]),
    "OG-R24": ("Trading funds, public corporations and public-private partnerships", "Must", "Done", ["N3", "N4"], ["C-BUILD", "C-PORTAL"]),
    "OG-R25": ("Lineage to a fingerprinted source for every link", "Must", "Done", ["N7"], ["C-FETCH", "C-BUILD"]),
    "OG-R26": ("Single source of truth for the estate's apps", "Must", "In progress", ["N6"], ["C-PORTAL"]),
    "OG-R27": ("Trends since 2012 from the official editions", "Must", "Done", ["N5"], ["C-TRENDS"]),
    "OG-R28": ("The 2020 baseline checked so nothing stale is carried forward", "Must", "Done", ["N5", "N7"], ["C-TRENDS"]),
    "OG-R29": ("Three lenses to 2030, modelled and editable", "Should", "Done", ["N5"], ["C-SCEN"]),
    "OG-R30": ("Back-office classes A and B from the bodies' own descriptions", "Must", "Done", ["N1"], ["C-FUNC"]),
    "OG-R31": ("BODS 0.4 export validated against the official schema", "Must", "Done", ["N4", "N6"], ["C-BODS"]),
    "OG-R32": ("Concordance of every identifier for every body", "Must", "Done", ["N6"], ["C-ART"]),
    "OG-R33": ("Open-source contribution: forms, guide, code of conduct, review in public", "Must", "Done", ["N8"], ["C-REPO"]),
    "OG-R34": ("No personal data; no individual or affiliation named", "Must", "Done", ["N7"], ["C-BUILD", "C-PORTAL", "C-TRENDS"]),
    "OG-R35": ("Question-led information architecture, WCAG 2.2 AA, dashboards and drill-down", "Must", "Planned", ["N1", "N2", "N3", "N5"], []),
    "OG-R36": ("Reference data lineage matched against the National Data Library catalogue", "Should", "Done", ["N6", "N7"], ["C-REF"]),
    "OG-R38": ("Each nation's register: its public bodies by branch of the state, apex from founding legislation", "Must", "Done", ["N1", "N2"], ["C-NAT"]),
    "OG-R39": ("Nation placement from trusted sources only, every piece of evidence shown, disagreements listed", "Must", "Done", ["N1", "N7"], ["C-NATEV"]),
    "OG-R40": ("Nation colours across the portal; ultimate owners split by nation; bodies serving several nations flagged", "Must", "Done", ["N1", "N2"], ["C-NAT", "C-PORTAL"]),
    "OG-R41": ("Own websites and official-language names, linked within the portal and out to the source", "Should", "Done", ["N1"], ["C-NAT"]),
    "OG-R42": ("2020 compilation used as dated evidence, non-personal columns only, not redistributed", "Should", "Done", ["N5", "N7"], ["C-H2020"]),
    "OG-R43": ("Every body classified by purpose, reach and how it is formed, in plain English for any reader", "Must", "Done", ["N1"], ["C-CLASS", "C-NAT"]),
    "OG-R44": ("Only apps with a public portal and repository are named as consumers", "Must", "Done", ["N6", "N7"], ["C-PORTAL"]),
    "OG-R45": ("Every open standard in use listed with status and a deep link", "Must", "Done", ["N6", "N7"], ["C-PORTAL"]),
    "OG-R46": ("Every trading fund and public corporation shown as its own family tree, each body in exactly one place, grouped by owner level and owner", "Must", "Done", ["N1", "N2", "N4"], ["C-CORP", "C-PORTAL"]),
    "OG-R47": ("Department and corporation trees grouped by purpose, activity and type of body, with large groups split again", "Must", "Done", ["N1", "N2"], ["C-CLASS", "C-CORP", "C-PORTAL"]),
    "OG-R48": ("Local government in England shown as it is and as planned under the English Devolution and Community Empowerment Act 2026: strategic authorities, reorganisation areas and their councils, and a timeline, every fact sourced", "Must", "Done", ["N1", "N2", "N5", "N7"], ["C-LG", "C-PORTAL"]),
    "OG-R50": ("One design system for every page: tokens in an open format, one shared stylesheet, self-hosted fonts, WCAG 2.2 AA contrast in light and dark, a published design system page, and a build that stops on any raw value", "Must", "Done", ["N6", "N7"], ["C-DESIGN", "C-PORTAL"]),
    "OG-R49": ("ONS sponsor codes resolve only through the guide's own abbreviation list", "Must", "Done", ["N2", "N7"], ["C-BUILD"]),
    "OG-R37": ("Comparator adoptions: founding legislation, COFOG, movements, interests, parent history", "Should", "Planned", ["N1", "N4", "N5"], []),
}
# id: (name, path, checks, outputs)
COMPONENTS = {
    "C-REG": ("Register spine (0.2.2)", "sources/opengovernment-uk-0.2.2.html", ["CHK-known_answers"], ["docs/concordance.csv"]),
    "C-FETCH": ("Source fetcher and manifest", "tools/fetch.py", ["CHK-hashes"], ["sources/manifest.json"]),
    "C-BUILD": ("Accountability tree builder", "tools/build.py", ["CHK-provenance", "CHK-ends", "CHK-no_persons", "CHK-chain_shape", "CHK-coverage", "CHK-nmd_terminal", "CHK-unresolved_reason", "CHK-digest", "CHK-person_rule_offices", "CHK-ons_codes"], ["data/tree.json", "data/edges.csv", "data/accountable-owner.csv"]),
    "C-PORTAL": ("Portal page builder", "tools/patch_portal.py", ["CHK-footer", "CHK-req_ids", "CHK-self"], ["docs/index.html", "docs/accountability.json", "docs/ppp.csv"]),
    "C-BODS": ("BODS 0.4 exporter", "tools/export_bods.py", ["CHK-bods_schema", "CHK-bods_rules"], ["docs/bods-0.4.json"]),
    "C-TRENDS": ("Public bodies trends and 2020 reconciliation", "tools/trends.py", ["CHK-units", "CHK-reconciled", "CHK-trend_persons"], ["data/public-bodies-trends.json", "data/reconciliation-2020.csv"]),
    "C-SCEN": ("Scenarios to 2030", "tools/scenarios.py", ["CHK-scenarios"], ["data/scenarios-2030.json"]),
    "C-FUNC": ("Back-office classifier", "tools/functions.py", ["CHK-functions"], ["data/back-office.json"]),
    "C-REF": ("Reference data lineage", "tools/refdata.py", [], ["data/reference-data.json", "documentation/reference-data.md"]),
    "C-NAT": ("Nation-by-nation registers", "tools/nations.py", ["CHK-nations"], ["data/nations.json", "docs/nations.html"]),
    "C-NATEV": ("Nation evidence resolver", "tools/nation_evidence.py", ["CHK-natev"], ["data/nation-evidence.json"]),
    "C-H2020": ("2020 historical layer", "tools/historical_2020.py", ["CHK-h2020"], ["data/historical-2020.json"]),
    "C-CLASS": ("Plain-English classifier", "tools/classify.py", ["CHK-classify"], ["data/classification.json"]),
    "C-DESIGN": ("Design system: tokens, stylesheet, shell and guards", "tools/design.py", ["CHK-design"], ["docs/assets/og.css", "docs/assets/tokens.json", "docs/design-system.html"]),
    "C-CORP": ("Trading fund and public corporation trees", "tools/corporations.py", ["CHK-corporations"], ["data/corporations.json"]),
    "C-LG": ("Local government under the 2026 Act", "tools/localgov.py", ["CHK-localgov"], ["data/local-government.json"]),
    "C-ART": ("Documentation generator", "tools/artefacts.py", ["CHK-artefacts"], ["documentation/solution/", "docs/navigator.html"]),
    "C-CI": ("Checks and refresh workflows", ".github/workflows/", ["CHK-lint"], []),
    "C-REPO": ("Contribution model", "CONTRIBUTING.md", [], [".github/ISSUE_TEMPLATE/"]),
}
CHECKS = {
    "CHK-known_answers": "Chains that can be verified independently land on the right department", "CHK-hashes": "Source fingerprints match the files",
    "CHK-provenance": "Every edge names its source and place", "CHK-ends": "Both ends of every edge are register records", "CHK-no_persons": "No personal names",
    "CHK-chain_shape": "Chains are acyclic and end at their stated root", "CHK-coverage": "Every open body has a chain", "CHK-nmd_terminal": "Non-ministerial departments are their own root",
    "CHK-unresolved_reason": "Every unmatched name says why", "CHK-digest": "Published digest matches the content", "CHK-person_rule_offices": "Offices and institutions are not read as people",
    "CHK-footer": "Footer names no individual and no government body", "CHK-req_ids": "Requirement IDs are unique", "CHK-self": "The page checks itself (width, links, chains, wording)",
    "CHK-bods_schema": "BODS output validates against the official schema", "CHK-units": "Every edition records its unit evidence and year", "CHK-reconciled": "The 2020 baseline is fully accounted for",
    "CHK-trend_persons": "No personal fields in trend outputs", "CHK-scenarios": "Scenarios recompute exactly from their assumptions", "CHK-functions": "Back-office known answers",
    "CHK-design": "32 contrast pairs pass in light and dark; every page uses the shared stylesheet with no raw colour, size, radius or breakpoint and no third-party font; negatives caught",
    "CHK-corporations": "Every member in exactly one tree; known answers (Manchester Airport group, Ordnance Survey, Scottish Water); negatives caught",
    "CHK-localgov": "Every fact sourced; 21 areas cover every two-tier county once; 205 councils match MHCLG's count; known answers; negatives caught",
    "CHK-ons_codes": "ONS sponsor codes resolve through the guide's abbreviations; Scottish Water answers to the Scottish Government",
    "CHK-artefacts": "Ontology and knowledge graph parse; every requirement traces to a need", "CHK-lint": "Linter fails on any finding", "CHK-natev": "Nation known answers found; a wrong nation is caught", "CHK-h2020": "Fingerprint matches; no personal field", "CHK-bods_rules": "Open Ownership's checker finds nothing", "CHK-classify": "Purpose and formation known answers; a wrong formation is caught", "CHK-nations": "Nation and branch known answers are found; every nation has an apex for each branch",
}
DOCS = {
    "D01": ("Theory of change", "01-theory-of-change.md", ["N1", "N2", "N3", "N5", "N7"]),
    "D02": ("User research bundle", "02-user-research.md", ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"]),
    "D03": ("Service blueprint and workflows", "03-service-blueprint-and-workflows.md", ["OG-R11", "OG-R25", "OG-R33"]),
    "D04": ("Product requirements document", "04-product-requirements.md", list(REQS)),
    "D05": ("Functional and technical requirements specification", "05-requirements-specification.md", list(REQS)),
    "D06": ("Solution architecture", "06-solution-architecture.md", list(COMPONENTS)),
    "D07": ("High-level design", "07-high-level-design.md", list(COMPONENTS)),
    "D08": ("Low-level design", "08-low-level-design.md", list(COMPONENTS)),
    "D09": ("Glossary and thesaurus", "09-glossary-and-thesaurus.md", []),
    "D10": ("Data dictionary", "10-data-dictionary.md", ["C-BUILD", "C-TRENDS", "C-BODS", "C-ART"]),
    "D11": ("Taxonomies and ontology", "11-taxonomies-and-ontology.md", ["OG-R08", "OG-R31"]),
    "D12": ("Knowledge graph and navigator", "12-knowledge-graph.md", list(REQS)),
}

def ftir():
    rows = ["# Functional and technical requirements specification", "", "Generated by `tools/artefacts.py` from the traceability spine. Each requirement traces to the needs it serves, the components that meet it, and the checks that prove it.", "",
            "| ID | Requirement | Priority | Status | Needs | Components | Checks |", "|---|---|---|---|---|---|---|"]
    for k, (t, p, s, n, c) in REQS.items():
        chks = sorted({x for ci in c for x in COMPONENTS[ci][2]})
        rows.append(f"| {k} | {t} | {p} | {s} | {', '.join(n)} | {', '.join(COMPONENTS[ci][0] for ci in c) or '–'} | {', '.join(chks) or '–'} |")
    rows += ["", "## Technical requirements", "", "| ID | Requirement |", "|---|---|",
             "| T1 | Static site only (GitHub Pages); no server, no sign-in, no cookies |", "| T2 | Python 3.11+; dependencies pinned in requirements.txt; GitHub Actions pinned to commit SHAs |",
             "| T3 | Every build fails closed: a failed check stops publication |", "| T4 | Least privilege: workflows read-only; no secrets in the repository |",
             "| T5 | Output escaped in the page; safe loaders only; no evaluation of input |", "| T6 | Open formats: JSON, CSV with CSVW, JSON-LD (ORG, DCAT, SKOS), BODS 0.4 |",
             "| T7 | Accessibility: WCAG 2.2 AA; works at 320 px and 400% zoom; light and dark |", "| T8 | No personal data in any output; files naming people are fetched, not redistributed |"]
    (SOL / "05-requirements-specification.md").write_text("\n".join(rows) + "\n")

def describe_csv(p):
    with open(p, newline="") as f: r = csv.reader(f); head = next(r); sample = next(r, [])
    return head, sample
def describe_json(p):
    d = json.loads(p.read_text()); return list(d)[:40] if isinstance(d, dict) else (list(d[0])[:40] if d and isinstance(d[0], dict) else [])
DESC = {"id": "Register key: the owning register's code as a CURIE", "name": "Current name", "family": "Kind of register record", "status": "open or closed",
        "child_id": "Body the link starts from", "child_name": "Name of the body the link starts from", "parent_id": "Body it links to", "parent_name": "Name of the body it links to, as the register names it",
        "parent_as_written": "Parent's name exactly as the source wrote it", "relation": "accounts, sponsors, controls, parent or owns",
        "source": "Source key (see sources/manifest.json)", "source_ref": "Where in the source", "match_method": "How the two names were matched", "accountable_owner_id": "Key of the body at the top of the chain",
        "accountable_owner": "Name of the body at the top of the chain", "answerable_to": "Elected body it answers to in the end", "chain": "The chain, each step with relation and source", "sources_agreeing": "Sources naming the same first link",
        "parents_asserted": "Number of first links the sources assert (more than 1 means sources disagree)", "type": "Kind of body as its register states it (for example Executive agency)",
        "wga_2024_25": "Status in the Whole of Government Accounts 2024-25 (for example consolidated), blank if not listed", "government_funded_income_gbp": "Income from government in pounds, from the Public Bodies Directory 2023/24, blank if not stated",
        "total_managed_expenditure_gbp": "Total managed expenditure in pounds, from the Public Bodies Directory 2023/24, blank if not stated", "trading_fund": "True if a trading fund order names it",
        "ukgi_shareholding": "True if UK Government Investments manages the government's shareholding in it",
        "govuk": "GOV.UK organisation code", "govuk_slug": "GOV.UK organisation slug (the end of its www.gov.uk/government/organisations/ address)", "ons_name": "Name as the ONS Public Sector Classification Guide writes it",
        "gss": "ONS Government Statistical Service code (councils and other areas)", "local_authority": "Local authority code (GB-LAE register)", "nhs_ods": "NHS Organisation Data Service code",
        "companies_house": "Companies House company number", "lei": "Legal Entity Identifier (ISO 17442)", "charity_ew": "Charity Commission for England and Wales number", "charity_sc": "Scottish Charity Regulator number (none matched yet)",
        "charity_ni": "Charity Commission for Northern Ireland number (none matched yet)", "wikidata": "Wikidata item (corroborating only)", "dgu": "data.gov.uk publisher slug", "github": "GitHub organisation the body publishes code under",
        "iati_gb_gov": "IATI organisation identifier (international aid reporting)",
        "hmt_project_id": "HM Treasury's project number", "project": "Project name as HM Treasury writes it", "sector": "Sector as HM Treasury writes it", "procuring_authority_id": "Register key of the public body that procured the project",
        "procuring_authority": "Public body that procured the project, as HM Treasury writes it", "department_id": "Register key of the sponsoring department", "department": "Sponsoring department, as HM Treasury writes it",
        "project_company": "The private project company (special purpose vehicle)", "company_number": "Companies House number of the project company", "equity_holders": "Companies holding equity in the project company, each with its share (1.0 = 100%)",
        "individuals_not_named": "Number of individual shareholders left out because they are people", "capital_gbp_m": "Capital value in millions of pounds, as HM Treasury states it",
        "unitary_charge_2025_26_gbp_m": "Unitary charge (the annual payment) for 2025-26 in millions of pounds", "contract_end": "Date the contract ends", "esa_balance_sheet": "Whether the project is on the public balance sheet under ESA 2010, as HM Treasury states it",
        "name_2020": "Name in the 2020 public bodies list", "department_2020": "Department in the 2020 list", "class_2020": "Classification in the 2020 list (for example NDPB)", "register_id": "Register key it was matched to, blank if none",
        "register_status": "open or closed in the register now", "closed": "Date it closed, from GOV.UK", "close_reason": "Why it closed, from GOV.UK (replaced, merged, no_longer_exists and so on)",
        "verdict": "current, replaced (with successor), closed, or for a person", "in_directory_2023_24": "Also listed in the 2023/24 directory",
        "kind": "Kind of body (department, agency, council and so on)", "nations": "Nations it serves: EN, SC, WA, NI, or UK", "parents": "Register keys of the bodies it answers to", "start": "Date it was set up, where a source states it",
        "end": "Date it closed, where it has", "website": "Official website", "btype": "Body type key (see taxonomies.skos.jsonld)", "purpose": "What it is for, grouped by UN COFOG (worked out, not official)",
        "activity": "What it does (worked out from kind, name and description, so a few may be wrong)", "reach": "Whom it serves (worked out)", "org_id": "org-id.guide identifier"}
FILE_DESC = {"docs/ppp.csv": {"status": "Project status as HM Treasury states it (for example In Operation)"}}  # where a column name means something else in one file
CSVS = ["docs/data/register.csv", "docs/concordance.csv", "data/edges.csv", "data/accountable-owner.csv", "docs/ppp.csv", "data/reconciliation-2020.csv"]
def undescribed():  # every column of every CSV must carry a meaning (the dictionary had 51 blanks before this guard)
    return [f"{f}:{h}" for f in CSVS for h in describe_csv(ROOT / f)[0] if not (FILE_DESC.get(f, {}).get(h) or DESC.get(h))]
def dictionary():
    out = ["# Data dictionary", "", "Generated from the files themselves by `tools/artefacts.py`, so it always matches them. The build fails if any column has no meaning written.", ""]
    for f in CSVS:
        head, sample = describe_csv(ROOT / f)
        out += [f"## `{f}`", "", "| Field | Meaning | Example |", "|---|---|---|"] + [f"| `{h}` | {FILE_DESC.get(f, {}).get(h) or DESC.get(h, '')} | {str(sample[i])[:40].replace('|', '/') if i < len(sample) else ''} |" for i, h in enumerate(head)] + [""]
    for f in ["data/tree.json", "data/public-bodies-trends.json", "data/scenarios-2030.json", "data/back-office.json", "docs/accountability.json"]:
        out += [f"## `{f}`", "", "Top-level keys: " + ", ".join(f"`{k}`" for k in describe_json(ROOT / f)), ""]
    out += ["## `docs/bods-0.4.json`", "", "An array of BODS 0.4 statements (entity and relationship). Public-sector detail is in the `publicAccountability` extension; see documentation/bods-public-sector-profile.md.", ""]
    ftm = [json.loads(ln) for ln in (ROOT / "docs/data/register.ftm.json").read_text().splitlines() if ln.strip()]
    model = json.loads((ROOT / "vendor/followthemoney/defaultModel.json").read_text())["schemata"]
    used = collections.defaultdict(lambda: collections.Counter())
    for e in ftm:
        for k in e["properties"]: used[e["schema"]][k] += 1
    out += ["## `docs/data/register.ftm.json`", "", "One FollowTheMoney entity per line. Meanings are FollowTheMoney's own labels, read from its compiled model.", "", "| Schema | Property | Meaning | Entities with it |", "|---|---|---|---|"]
    for sc in sorted(used):
        props = {}
        for anc in model[sc]["schemata"]: props.update(model[anc].get("properties", {}))
        out += [f"| {sc} | `{k}` | {(props[k].get('description') or props[k].get('label', '')).replace('|', '/')} | {n} |" for k, n in sorted(used[sc].items())]
    st = json.loads((ROOT / "docs/data/source-status.json").read_text())
    out += ["", "## `docs/data/source-status.json`", "", "How each source stands at this build (written by `tools/sources_check.py`).", "", "| Field | Meaning |", "|---|---|",
            "| `as_of` | The build's latest read; ages count from it |", "| `sources[].status` | current, stale (read more than twice its change interval before `as_of`) or not read |",
            "| `sources[].frequency_days` | How often the publisher changes the source, in days |", "| `sources[].next_due` | When the source is next expected to change |", "| `sources[].official` | True if published by the body responsible for it |",
            "| `not_read[]` | Parts of sources that could not be read, each with the reason |", "| `counts[]` | Each expected count, its range, and whether it is in range |", "",
            f"Top-level keys: {', '.join(f'`{k}`' for k in st)}", ""]
    (SOL / "10-data-dictionary.md").write_text("\n".join(out))

TTL = """@prefix og: <https://cyberdudeuk.github.io/opengovernment-uk/ontology#> .
@prefix org: <http://www.w3.org/ns/org#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

og: a owl:Ontology ; rdfs:label "OpenGovernment UK ontology" ; dct:license <https://creativecommons.org/licenses/by/4.0/> ;
    rdfs:comment "Public bodies of the UK state, who they answer to, who funds and owns them. Extends W3C ORG; aligned to BODS 0.4 and FollowTheMoney." .

og:PublicBody a owl:Class ; rdfs:subClassOf org:FormalOrganization ; rdfs:label "Public body" ; rdfs:comment "Any body a UK public register lists. FtM: PublicBody; BODS: stateBody." .
og:MinisterialDepartment a owl:Class ; rdfs:subClassOf og:PublicBody ; rdfs:label "Ministerial department" .
og:NonMinisterialDepartment a owl:Class ; rdfs:subClassOf og:PublicBody ; rdfs:label "Non-ministerial department" .
og:ExecutiveAgency a owl:Class ; rdfs:subClassOf og:PublicBody ; rdfs:label "Executive agency" .
og:NDPB a owl:Class ; rdfs:subClassOf og:PublicBody ; rdfs:label "Non-departmental public body" .
og:PublicCorporation a owl:Class ; rdfs:subClassOf og:PublicBody ; rdfs:label "Public corporation" .
og:TradingFund a owl:Class ; rdfs:subClassOf og:PublicBody ; rdfs:label "Trading fund" .
og:LocalAuthority a owl:Class ; rdfs:subClassOf og:PublicBody ; rdfs:label "Local authority" .
og:NHSBody a owl:Class ; rdfs:subClassOf og:PublicBody ; rdfs:label "NHS body" .
og:Legislature a owl:Class ; rdfs:subClassOf org:FormalOrganization ; rdfs:label "Legislature" .
og:ProjectCompany a owl:Class ; rdfs:subClassOf org:FormalOrganization ; rdfs:label "Project company (PFI special purpose vehicle)" .
og:Source a owl:Class ; rdfs:label "Authoritative source" ; rdfs:comment "A file read by the build, with its SHA-256 fingerprint." .

og:accountsTo a owl:ObjectProperty ; rdfs:domain og:PublicBody ; rdfs:range og:PublicBody ; rdfs:label "included in the Estimate and accounts of" ; skos:closeMatch <https://standard.openownership.org/en/0.4.0/standard/reference.html#interesttype> .
og:sponsoredBy a owl:ObjectProperty ; rdfs:domain og:PublicBody ; rdfs:range og:PublicBody ; rdfs:label "sponsored by" .
og:controlledBy a owl:ObjectProperty ; rdfs:label "controlled by (non-institutional unit)" .
og:ownedBy a owl:ObjectProperty ; rdfs:label "owned or controlled by" .
og:answersTo a owl:ObjectProperty ; rdfs:range og:Legislature ; rdfs:label "answers in the end to" .
og:accountableOwner a owl:ObjectProperty ; rdfs:domain og:PublicBody ; rdfs:range og:PublicBody ; rdfs:label "accountable owner" .
og:procuredBy a owl:ObjectProperty ; rdfs:domain og:ProjectCompany ; rdfs:range og:PublicBody ; rdfs:label "contracted by (procuring authority)" .
og:evidence a owl:ObjectProperty ; rdfs:range og:Source ; rdfs:label "evidenced by" .
og:backOfficeClass a owl:DatatypeProperty ; rdfs:range xsd:string ; rdfs:label "back-office class (A or B)" .
og:sha256 a owl:DatatypeProperty ; rdfs:domain og:Source ; rdfs:range xsd:string ; rdfs:label "SHA-256 fingerprint" .

og:Relations a skos:ConceptScheme ; skos:prefLabel "Accountability relations" .
og:rel-accounts a skos:Concept ; skos:inScheme og:Relations ; skos:prefLabel "accounts" ; skos:definition "Included in a department's Supply Estimate and accounts by designation order" .
og:rel-sponsors a skos:Concept ; skos:inScheme og:Relations ; skos:prefLabel "sponsors" ; skos:altLabel "sponsoring department" .
og:rel-controls a skos:Concept ; skos:inScheme og:Relations ; skos:prefLabel "controls" .
og:rel-parent a skos:Concept ; skos:inScheme og:Relations ; skos:prefLabel "parent" ; skos:definition "GOV.UK parent organisation" .
og:rel-owns a skos:Concept ; skos:inScheme og:Relations ; skos:prefLabel "owns" .
og:BackOffice a skos:ConceptScheme ; skos:prefLabel "Back-office classes" .
og:class-A a skos:Concept ; skos:inScheme og:BackOffice ; skos:prefLabel "A: back-office body" ; skos:definition "Exists to run a function for government itself" .
og:class-B a skos:Concept ; skos:inScheme og:BackOffice ; skos:prefLabel "B: back-office line of business" ; skos:definition "A public-facing body that also runs a cross-government back-office service" .
"""
def ontology():
    g = rdflib.Graph(); g.parse(data=TTL, format="turtle")  # fails loudly if malformed
    (SOL / "ontology.ttl").write_text(TTL); return len(g)

def graph():
    base = "https://cyberdudeuk.github.io/opengovernment-uk/trace#"; items = []
    for k, v in NEEDS.items(): items.append({"@id": base + k, "@type": "Need", "name": v})
    for k, (t, p, s, n, c) in REQS.items(): items.append({"@id": base + k, "@type": "Requirement", "name": t, "priority": p, "status": s, "serves": [base + x for x in n], "metBy": [base + x for x in c]})
    for k, (nm, path, chk, outs) in COMPONENTS.items(): items.append({"@id": base + k, "@type": "Component", "name": nm, "path": path, "provenBy": [base + x for x in chk], "produces": outs})
    for k, v in CHECKS.items(): items.append({"@id": base + k, "@type": "Check", "name": v})
    for k, (t, f, about) in DOCS.items(): items.append({"@id": base + k, "@type": "Document", "name": t, "file": "documentation/solution/" + f, "describes": [base + x for x in about]})
    kg = {"@context": {"@vocab": base, "name": "http://schema.org/name", "serves": {"@type": "@id"}, "metBy": {"@type": "@id"}, "provenBy": {"@type": "@id"}, "describes": {"@type": "@id"}}, "@graph": items}
    g = rdflib.Graph(); g.parse(data=json.dumps(kg), format="json-ld")
    (SOL / "knowledge-graph.jsonld").write_text(json.dumps(kg, indent=1)); return len(g), items

def navigator(items):
    data = json.dumps(items).replace("</", "<\\/")
    html = """<!DOCTYPE html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OpenGovernment UK: documentation and traceability</title>
<style>:root{--bg:#f6f2ea;--paper:#fffdf8;--ink:#1c1a17;--muted:#5a544b;--line:#ddd3c3;--hi:#b6391f;--hi2:#f7e3dc;--focus:#1c5bd6}@media(prefers-color-scheme:dark){:root{--bg:#14120f;--paper:#1c1915;--ink:#efe9de;--muted:#b4aa9a;--line:#3a342b;--hi:#ff8a6e;--hi2:#3a1d15;--focus:#8ab4ff}}
*{box-sizing:border-box}body{margin:0;font:16px/1.5 Inter,"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--ink)}header{padding:20px 24px;border-bottom:1px solid var(--line);background:var(--paper)}h1{font:700 1.5rem Georgia,serif;margin:0 0 4px}p{margin:0;color:var(--muted)}
main{padding:16px 24px}.cols{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}@media(max-width:900px){.cols{grid-template-columns:minmax(0,1fr)}}
.col h2{font-size:.8rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:0 0 8px}.node{display:block;width:100%;text-align:left;background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin:0 0 6px;color:var(--ink);font:inherit;font-size:.86rem;cursor:pointer}
.node b{font-family:"IBM Plex Mono",monospace;font-size:.74rem;color:var(--muted);display:block}.node.on{border-color:var(--hi);background:var(--hi2)}.node.dim{opacity:.35}.node:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.status{font-size:.72rem;color:var(--muted)}#detail{margin:14px 0;padding:12px 14px;background:var(--paper);border:1px solid var(--line);border-radius:10px;min-height:3em}a{color:var(--hi)}
footer{padding:16px 24px;color:var(--muted);font-size:.85rem;border-top:1px solid var(--line)}
.start{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin:0 0 18px;padding:0;list-style:none}.start li{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:10px 12px}.start h3{font-size:1.05rem!important;line-height:1.3!important;margin:0 0 4px!important}.sec-h{font-size:1.3rem!important;margin:0 0 10px!important}.col h2{font-size:.8rem!important;line-height:1.4!important;letter-spacing:.05em!important;margin:0 0 8px!important}.start p{margin:0;font-size:.9rem;color:var(--muted)}.start a{font-weight:600}
</style></head><body>
<header><h1>Requirements and design</h1><p>How the portal is built. For how to use it, see <a href="index.html#help">Help and guides</a>. Choose any item to see its lineage: the needs it serves, what meets it, what proves it, and the documents that describe it. Generated from the same spine as the documentation.</p></header>
<main><section aria-labelledby="start-h" class="dv-sign"><h2 id="start-h" class="sec-h">Want to use the data?</h2><p>Connect, harvest, crosswalks, the MCP connector, plugins, test cases, licensing and how to contribute are all in the <a href="developers.html">developer hub</a>.</p></section><h2 class="sec-h">Requirements and traceability</h2><div id="detail" aria-live="polite">Nothing selected.</div><div class="cols" id="cols"></div></main>
<footer>OpenGovernment UK, an open-source public good. <a href="./">Back to the register</a> · <a href="https://github.com/cyberdudeuk/opengovernment-uk/tree/main/documentation/solution">The documents on GitHub</a></footer>
<script id="kg" type="application/json">__DATA__</script>
<script>"use strict";
const I=JSON.parse(document.getElementById("kg").textContent),B=id=>id.split("#")[1],T=["Need","Requirement","Component","Check","Document"],L={Need:"Needs",Requirement:"Requirements",Component:"Components",Check:"Checks",Document:"Documents"};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const E=[];I.forEach(n=>["serves","metBy","provenBy","describes"].forEach(k=>(n[k]||[]).forEach(t=>E.push([B(n["@id"]),B(t)]))));
const nb=id=>new Set(E.filter(e=>e[0]===id||e[1]===id).map(e=>e[0]===id?e[1]:e[0]));
const LY={Need:0,Requirement:1,Component:2,Check:3},TY=Object.fromEntries(I.map(n=>[B(n["@id"]),n["@type"]]));
// Lineage moves one way only: up towards needs, down towards checks; documents attach but are never walked through,
// otherwise a document describing every requirement links everything to everything (D-OG18).
function walk(start,dir){const seen=new Set([start]);let f=[start];while(f.length){const nx=[];f.forEach(x=>nb(x).forEach(y=>{if(seen.has(y))return;const a=LY[TY[x]],b=LY[TY[y]];if(b===undefined)return;if((dir<0&&b<a)||(dir>0&&b>a)){seen.add(y);nx.push(y)}}));f=nx}return seen}
function lineage(id){const t=TY[id];let core;if(t==="Document"){core=new Set([id,...nb(id)])}else{core=new Set([...walk(id,-1),...walk(id,1)])}
if(t!=="Document")[...core].forEach(x=>nb(x).forEach(y=>{if(TY[y]==="Document"&&(x===id||TY[x]==="Requirement"&&t!=="Need"))core.add(y)}));return core}
document.getElementById("cols").innerHTML=T.map(t=>`<section class="col" aria-label="${L[t]}"><h2>${L[t]}</h2>${I.filter(n=>n["@type"]===t).map(n=>`<button class="node" type="button" data-id="${esc(B(n["@id"]))}"><b>${esc(B(n["@id"]))}</b>${esc(n.name)}${n.status?`<div class="status">${esc(n.priority)} · ${esc(n.status)}</div>`:""}</button>`).join("")}</section>`).join("");
document.getElementById("cols").addEventListener("click",e=>{const b=e.target.closest(".node");if(!b)return;const id=b.dataset.id,set=lineage(id),n=I.find(x=>B(x["@id"])===id);
document.querySelectorAll(".node").forEach(x=>{x.classList.toggle("on",set.has(x.dataset.id));x.classList.toggle("dim",!set.has(x.dataset.id))});
document.getElementById("detail").innerHTML=`<b>${esc(id)}</b>: ${esc(n.name)}${n.file?` · <a href="https://github.com/cyberdudeuk/opengovernment-uk/blob/main/${esc(n.file)}">read it</a>`:""}${n.path?` · <span>${esc(n.path)}</span>`:""}. Linked items: ${set.size-1}.`});
</script></body></html>"""
    sys.path.insert(0, str(ROOT / "tools")); import design  # shared design system and page shell (OG-D42)
    (ROOT / "docs" / "navigator.html").write_text(design.wrap_page(html, "docs").replace("__DATA__", data))

LAYER = {"Need": 0, "Requirement": 1, "Component": 2, "Check": 3}
def lineage(items, start):
    """Python mirror of the navigator's rule: walk up to needs and down to checks, never reversing (D-OG18)."""
    typ = {i["@id"].split("#")[1]: i["@type"] for i in items}; nb = {k: set() for k in typ}
    for i in items:
        for key in ("serves", "metBy", "provenBy", "describes"):
            for t in i.get(key, []): a, b = i["@id"].split("#")[1], t.split("#")[1]; nb[a].add(b); nb[b].add(a)
    out = {start}
    for d in (-1, 1):
        f = [start]; seen = {start}
        while f:
            nx = []
            for x in f:
                for y in nb[x]:
                    if y in seen or typ[y] not in LAYER or typ[x] not in LAYER: continue
                    if (LAYER[typ[y]] - LAYER[typ[x]]) * d > 0: seen.add(y); nx.append(y)
            f = nx
        out |= seen
    return {x for x in out if typ[x] != "Document"}

def check(items):
    """Every requirement serves a need; every Done requirement has a component; every component's checks exist."""
    bad = [k for k, v in REQS.items() if not v[3]] + [k for k, v in REQS.items() if v[2] == "Done" and not v[4]]
    bad += [c for k, v in COMPONENTS.items() for c in v[2] if c not in CHECKS] + [x for v in DOCS.values() for x in v[2] if x not in NEEDS and x not in REQS and x not in COMPONENTS]
    if items:
        got = lineage(items, "OG-R38")
        if got != {"OG-R38", "N1", "N2", "C-NAT", "CHK-nations"}: bad.append(f"OG-R38 lineage {sorted(got)}")
        big = [i["@id"].split("#")[1] for i in items if i["@type"] == "Requirement" and len(lineage(items, i["@id"].split("#")[1])) > len(items) // 2]
        if big: bad.append(f"lineage too broad: {big}")
    return bad

if __name__ == "__main__":
    ftir(); dictionary(); n_onto = ontology(); n_kg, items = graph(); navigator(items)
    (SOL / "traceability.json").write_text(json.dumps({"needs": NEEDS, "requirements": REQS, "components": COMPONENTS, "checks": CHECKS, "documents": DOCS}, indent=1))
    nav = (ROOT / "docs/navigator.html").read_text()
    dead = [u for u in re.findall(r'<section aria-labelledby="start-h".*?</section>', nav, re.S) for u in re.findall(r'href="([^"]+)"', u) if not u.startswith("http") and not (ROOT / "docs" / u).exists()]
    bad = check(items) + [f"no meaning for {x}" for x in undescribed()] + [f"start-here links to a file that is not published: {u}" for u in dead] + ([] if 'href="developers.html">developer hub</a>' in nav else ["navigator has lost its signpost to the developer hub"]) + ([] if re.search(r"\.col h2\{font-size:[^;}]+!important", nav) else ["navigator headings lost the override that beats the shared heading sizes (OG-D68)"])
    if "--negative" in sys.argv:
        DESC["_saved"] = DESC.pop("gss"); caught0 = "docs/concordance.csv:gss" in undescribed(); DESC["gss"] = DESC.pop("_saved")
        print("caught undescribed column" if caught0 else "MISSED undescribed column")
        if not caught0: sys.exit(1)
        REQS["OG-RX"] = ("A requirement serving nothing", "Must", "Done", [], []); caught = bool(check(items)); del REQS["OG-RX"]
        print("caught traceability break" if caught else "MISSED traceability break")
        def undirected(items, start):  # the defective rule: any edge, any direction, documents included
            nb = collections.defaultdict(set)
            for i in items:
                for key in ("serves", "metBy", "provenBy", "describes"):
                    for t in i.get(key, []): x, y = i["@id"].split("#")[1], t.split("#")[1]; nb[x].add(y); nb[y].add(x)
            seen, f = {start}, [start]
            for _ in range(4): f = [y for x in f for y in nb[x] if y not in seen and not seen.add(y)]
            return seen
        good = globals()["lineage"]; globals()["lineage"] = undirected
        caught2 = bool(check(items)); globals()["lineage"] = good; print("caught lineage spread" if caught2 else "MISSED lineage spread"); sys.exit(0 if caught and caught2 else 1)
    print(f"ontology triples {n_onto}, knowledge graph triples {n_kg}, items {len(items)}, problems {bad}"); sys.exit(1 if bad else 0)
