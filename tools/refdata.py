"""Reference data lineage for OpenGovernment UK, matched against the National Data Library catalogue (data.gov.uk).
Upstream: every reference dataset or codelist the register and its accountability layer read.
Downstream: every app or dataset in this estate that reads the register (from the feed contract).
For each, the catalogue is searched and the best candidates are scored by title similarity. A score is a lead for a person
to confirm, never a confirmed match: the output says so on every row."""
import datetime, json, pathlib, re, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
API = "https://www.data.gov.uk/api/action/package_search"
UA = {"User-Agent": "OpenGovernment-UK-build/0.3 (+public good register)"}
# id, name, owner, role (what OGUK uses it for), kind (register | codelist | legislation | dataset | identifier scheme), url, catalogue query
UP = [
 ("govuk-orgs", "GOV.UK Organisations API", "Government Digital Service", "identity spine: names, types, parents, successors", "register", "https://www.gov.uk/api/organisations", "government organisations GOV.UK"),
 ("ons-pscg", "Public Sector Classification Guide", "Office for National Statistics", "sector, ESA code, sponsor, parent company, controlling unit", "register", "https://www.ons.gov.uk/methodology/classificationsandstandards/economicstatisticsclassifications/introductiontoeconomicstatisticsclassifications", "public sector classification guide"),
 ("esa2010", "ESA 2010 institutional sector codes", "Eurostat / ONS", "sector codes on every ONS-classified body", "codelist", "https://ec.europa.eu/eurostat/web/esa-2010", "ESA 2010 sector classification"),
 ("eao", "Estimates and Accounts Order 2026 (S.I. 2026/216)", "HM Treasury (legislation.gov.uk)", "legal accounting boundary: which department answers for a body's money", "legislation", "https://www.legislation.gov.uk/uksi/2026/216/made", "estimates and accounts designation of bodies"),
 ("eao-ni", "Estimates and Accounts Order (NI) 2026 (S.R. 2026/49)", "Department of Finance NI (legislation.gov.uk)", "the same for Northern Ireland bodies", "legislation", "https://www.legislation.gov.uk/nisr/2026/49/made", "Northern Ireland estimates accounts designation"),
 ("wgao", "Whole of Government Accounts (Designation of Bodies) Order 2026", "HM Treasury (legislation.gov.uk)", "which bodies supply data to WGA", "legislation", "https://www.legislation.gov.uk/uksi/2026/66/made", "whole of government accounts"),
 ("wga", "Whole of Government Accounts 2024-25, Annexes 1-3", "HM Treasury", "WGA consolidation status per body", "dataset", "https://www.gov.uk/government/collections/whole-of-government-accounts", "whole of government accounts annex"),
 ("pbd", "Public Bodies Directory 2023/24", "Cabinet Office", "sponsor, government funding, spend, classification", "dataset", "https://www.gov.uk/government/collections/public-bodies", "public bodies"),
 ("pfi", "Current PFI and PF2 projects (31 March 2025)", "HM Treasury / NISTA", "public-private partnerships: authority, project company, investors, charges", "dataset", "https://www.gov.uk/government/publications/pfi-and-pfi2-projects-2025-summary-data", "PFI PF2 projects"),
 ("tf", "Trading Fund Orders", "legislation.gov.uk", "which operations are trading funds", "legislation", "https://www.legislation.gov.uk/all?title=Trading%20Fund%20Order", "trading fund"),
 ("ch", "Companies House register and persons with significant control", "Companies House", "company numbers; who controls government companies", "register", "https://find-and-update.company-information.service.gov.uk/", "companies house persons with significant control"),
 ("gleif", "Global LEI Index, Level 1 and Level 2", "GLEIF (ISO 17442)", "legal entity identifiers; consolidation parents", "register", "https://www.gleif.org/en/lei-data/gleif-golden-copy", "legal entity identifier"),
 ("nhs-ods", "NHS Organisation Data Service", "NHS England", "codes for NHS bodies", "register", "https://digital.nhs.uk/services/organisation-data-service", "NHS organisation data service"),
 ("la-codes", "Local authority codes (GSS / ONS geography)", "Office for National Statistics", "codes for councils; GSS codes", "codelist", "https://geoportal.statistics.gov.uk/", "local authority district codes"),
 ("charities", "Charity registers (England and Wales, Scotland, Northern Ireland)", "Charity Commission, OSCR, CCNI", "charity numbers of bodies that are charities", "register", "https://register-of-charities.charitycommission.gov.uk/", "register of charities"),
 ("wikidata", "Wikidata", "Wikimedia Foundation", "corroboration and cross-identifiers", "register", "https://www.wikidata.org/", None),
 ("dgu-publishers", "data.gov.uk publishers", "National Data Library / GDS", "link from each body to its published datasets", "register", "https://www.data.gov.uk/api/action/organization_list", "data.gov.uk publishers organisations"),
 ("iso3166", "ISO 3166-2:GB subdivision codes", "ISO / ONS", "nation codes (GB-ENG, GB-SCT, GB-WLS, GB-NIR)", "codelist", "https://www.iso.org/obp/ui/#iso:code:3166:GB", "country nation codes"),
 ("org-id", "org-id.guide identifier schemes", "Open Data Services", "identifier prefixes in the BODS export (GB-COH, GB-CHC …)", "identifier scheme", "https://org-id.guide/", None),
 ("bods", "Beneficial Ownership Data Standard 0.4 codelists", "Open Ownership", "entityType and interestType codes in the BODS export", "codelist", "https://standard.openownership.org/", None),
 ("govs", "Government Functional Standards (GovS 001-015)", "Cabinet Office", "back-office function flags (0.4)", "codelist", "https://www.gov.uk/government/collections/functional-standards", "functional standards"),
]
contract = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "docs" / "index.html").read_text(), re.S).group(1).replace("<\\/", "</"))["contract"]
DOWN = [(re.sub(r"[^a-z0-9]+", "-", c["app"].lower()).strip("-"), c["app"], c["holds_now"], c["reads"], c["status"]) for c in contract["consumers"]]

def words(s): return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in {"the", "and", "for", "data", "dataset", "list", "register", "codes", "with"}}
def search(q):
    u = API + "?" + urllib.parse.urlencode({"q": q, "rows": 8})
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40) as r: d = json.load(r)
    return d["result"]["count"], d["result"]["results"]
out = {"built": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "catalogue": "https://www.data.gov.uk (National Data Library search directory), CKAN package_search",
       "note": "score = share of the reference item's name words found in the catalogue title; a lead for a person to confirm, not a confirmed match", "upstream": [], "downstream": []}
for i, name, owner, role, kind, url, q in UP:
    row = {"id": i, "name": name, "owner": owner, "used_for": role, "kind": kind, "url": url, "catalogue_query": q, "catalogue_hits": 0, "candidates": []}
    if q:
        n, res = search(q); row["catalogue_hits"] = n; W = words(q)
        for p in res:
            t = p.get("title", ""); sc = round(len(W & words(t)) / max(1, len(W)), 2)
            row["candidates"].append({"title": t, "publisher": (p.get("organization") or {}).get("title"), "url": "https://www.data.gov.uk/dataset/" + p.get("id", ""), "modified": (p.get("metadata_modified") or "")[:10], "score": sc})
        row["candidates"].sort(key=lambda c: -c["score"]); row["candidates"] = row["candidates"][:4]
        row["best"] = row["candidates"][0]["score"] if row["candidates"] else 0
        time.sleep(0.4)
    else: row["best"] = None; row["catalogue_note"] = "not a UK government dataset; not expected in the catalogue"
    out["upstream"].append(row)
for i, app, holds, reads, status in DOWN:
    out["downstream"].append({"id": i, "app": app, "holds_now": holds, "reads": reads, "status": status})
# peer reference datasets: other lists of public bodies or their codes, to reconcile record by record
PEERS = ["organisation identifier government", "public bodies list", "government organisations register", "local authority register codes", "arm's length bodies", "public sector organisations"]
out["peers"] = []
seen = set()
for q in PEERS:
    n, res = search(q)
    for p in res[:6]:
        if p["id"] in seen: continue
        seen.add(p["id"]); fmts = sorted({(r.get("format") or "").upper() for r in p.get("resources", []) if r.get("format")})
        out["peers"].append({"query": q, "title": p.get("title"), "publisher": (p.get("organization") or {}).get("title"), "url": "https://www.data.gov.uk/dataset/" + p["id"], "modified": (p.get("metadata_modified") or "")[:10], "formats": fmts,
                             "resources": [r.get("url") for r in p.get("resources", []) if (r.get("format") or "").upper() in ("CSV", "JSON", "XLSX", "XLS", "ODS")][:3]})
    time.sleep(0.4)
# Is OpenGovernment UK's own feed in the catalogue yet? (it should be, once published)
n, res = search("OpenGovernment UK register of the UK state"); out["self_in_catalogue"] = [r.get("title") for r in res if "opengovernment" in r.get("title", "").lower()]
(ROOT / "data" / "reference-data.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
md = ["# Reference data lineage", "", f"Built {out['built']} against {out['catalogue']}.", "", "> " + out["note"] + ".", "", "## Upstream: what OpenGovernment UK relies on", "",
      "| Reference data | Owner | Used for | Kind | Catalogue hits | Best candidate in the catalogue | Score |", "|---|---|---|---|---:|---|---:|"]
for r in out["upstream"]:
    c = r["candidates"][0] if r["candidates"] else None
    md.append(f"| [{r['name']}]({r['url']}) | {r['owner']} | {r['used_for']} | {r['kind']} | {r['catalogue_hits']} | " + (f"[{c['title']}]({c['url']}) ({c['publisher']}, {c['modified']})" if c else (r.get("catalogue_note") or "none")) + f" | {'' if r['best'] is None else r['best']} |")
md += ["", "## Downstream: what relies on OpenGovernment UK", "", "| App or dataset | Holds today | Reads from the register | Status |", "|---|---|---|---|"]
md += [f"| {d['app']} | {d['holds_now']} | `{d['reads']}` | {d['status']} |" for d in out["downstream"]]
md += ["", "## Peer reference datasets in the catalogue", "", "Other lists of public bodies or their codes. Each is a candidate to reconcile record by record.", "", "| Dataset | Publisher | Updated | Formats |", "|---|---|---|---|"]
md += [f"| [{x['title']}]({x['url']}) | {x['publisher']} | {x['modified']} | {', '.join(x['formats'])} |" for x in out["peers"]]
md += ["", "## Gaps", "", "- OpenGovernment UK itself is " + ("listed: " + ", ".join(out["self_in_catalogue"]) if out["self_in_catalogue"] else "not yet in the catalogue. Registering it (DCAT record already in the page) is a release task.") + "",
       "- Scores below 0.5 mean no clear catalogue entry for that reference data: either it isn't catalogued or it is catalogued under another name. Each needs a person to look."]
(ROOT / "documentation").mkdir(exist_ok=True); (ROOT / "documentation" / "reference-data.md").write_text("\n".join(md) + "\n")
for r in out["upstream"]: print(f"{r['id']:15} hits {r['catalogue_hits']:>5} best {r['best']}  {(r['candidates'][0]['title'][:70] if r['candidates'] else '')}")
print("downstream", len(out["downstream"]), "self", out["self_in_catalogue"])
