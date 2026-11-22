"""Fetch every authoritative source the accountability tree is built from, and write sources/manifest.json:
URL, owner, licence, retrieved time and SHA-256 for each file, so every value in the build traces back to bytes on disk.
Network calls: GOV.UK Organisations API, legislation.gov.uk, ONS, GOV.UK assets, GLEIF API, Companies House public pages.
Files that were staged from earlier reads (the 0.2.2 register, the CDA register's WGA annex) are recorded as staged."""
import hashlib, html, json, pathlib, re, sys, time, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
S = ROOT / "sources"
UA = {"User-Agent": "OpenGovernment-UK-build/0.3 (+public good register; contact via GitHub issue form)"}
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def get(url, binary=False, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                b = r.read(); return b if binary else b.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    raise RuntimeError("failed: " + url)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

SOURCES = {
  "govuk": {"file": "govuk-organisations.json", "name": "GOV.UK Organisations API", "url": "https://www.gov.uk/api/organisations", "owner": "Government Digital Service", "licence": "OGL v3.0", "asserts": "administrative parent (parent_organisations), status, closure reason and successors"},
  "ons": {"file": "pscgnov2026.xlsx", "name": "ONS Public Sector Classification Guide, November 2026 (issued 20 November 2026)", "url": "https://www.ons.gov.uk/file?uri=/methodology/classificationsandstandards/economicstatisticsclassifications/introductiontoeconomicstatisticsclassifications/pscgnov2026.xlsx", "owner": "Office for National Statistics", "licence": "OGL v3.0", "asserts": "public sector control: sector, sponsoring entity, parent company and subsidiaries"},
  "eao": {"file": "eao2026.xml", "name": "The Government Resources and Accounts Act 2000 (Estimates and Accounts) Order 2026, S.I. 2026/216, Schedule", "url": "https://www.legislation.gov.uk/uksi/2026/216/made", "owner": "HM Treasury (legislation.gov.uk)", "licence": "OGL v3.0", "asserts": "legal financial accountability: the department whose estimate and accounts include the body (2026-27)"},
  "wgao": {"file": "wga-order-2026.xml", "name": "The Whole of Government Accounts (Designation of Bodies) Order 2026, S.I. 2026/66, Schedule", "url": "https://www.legislation.gov.uk/uksi/2026/66/made", "owner": "HM Treasury (legislation.gov.uk)", "licence": "OGL v3.0", "asserts": "legal designation to supply information for Whole of Government Accounts 2025-26"},
  "wga": {"file": "cda-register-2026-10-15.json", "name": "HM Treasury Whole of Government Accounts 2024-25, Annexes 1 to 3 (as transcribed in the CDA register, read 21 September 2026)", "url": "https://www.gov.uk/government/collections/whole-of-government-accounts", "owner": "HM Treasury", "licence": "OGL v3.0", "asserts": "consolidation status in the audited accounts of the UK public sector", "staged": True},
  "pbd": {"file": "pbd2324.xlsx", "name": "Cabinet Office Public Bodies Directory 2023/24 (published 29 May 2025)", "url": "https://assets.publishing.service.gov.uk/media/697897e25da1fd4ddea98bda/2025-05-29_Public_Bodies_Directory_2023_24.xlsx", "owner": "Cabinet Office Public Bodies Team", "licence": "OGL v3.0", "asserts": "sponsoring department, direct sponsor, government-funded income and total managed expenditure"},
  "gleif": {"file": "gleif-level2.json", "name": "GLEIF Level 2 relationship records (API)", "url": "https://api.gleif.org/api/v1/lei-records", "owner": "Global Legal Entity Identifier Foundation", "licence": "CC0", "asserts": "accounting consolidation: direct and ultimate parent, or the reason none is reported"},
  "ch": {"file": "companies-house-psc.json", "name": "Companies House register: persons with significant control (public pages)", "url": "https://find-and-update.company-information.service.gov.uk/", "owner": "Companies House", "licence": "OGL v3.0", "asserts": "legal ownership and control: who holds shares, votes or the right to appoint directors"},
  "eao-ni": {"file": "ni-eao-2026.xml", "name": "Estimates and Accounts (Designation of Bodies) Order (Northern Ireland) 2026, S.R. 2026/49", "url": "https://www.legislation.gov.uk/nisr/2026/49/made/data.xml", "owner": "Department of Finance (Northern Ireland)", "licence": "OGL v3.0", "asserts": "legal financial accountability for Northern Ireland bodies"},
  "pfi": {"file": "pfi-2025.ods", "name": "HM Treasury: Current PFI and PF2 projects as at 31 March 2025", "url": "https://assets.publishing.service.gov.uk/media/69c14bc7d588c92c483e4ba3/Current-PFI-PF2-projects-as-at-31-March-2025-OFFICIAL.ods", "owner": "HM Treasury / National Infrastructure and Service Transformation Authority", "licence": "OGL v3.0", "asserts": "public-private partnerships: authority, project company, investors, charges"},
  "tf": {"file": "tf-feed.xml", "name": "legislation.gov.uk: trading fund orders", "url": "https://www.legislation.gov.uk/all/data.feed?title=Trading%20Fund%20Order", "owner": "legislation.gov.uk (The National Archives)", "licence": "OGL v3.0", "asserts": "which operations are financed as trading funds"},
  "base": {"file": "opengovernment-uk-0.2.2.html", "name": "OpenGovernment UK 0.2.2 (built 14 November 2026)", "url": "https://claude.ai/artifact/63VSpapuNHqrds1LrFuwpb", "owner": "OpenGovernment UK pilot", "licence": "OGL v3.0", "asserts": "the identity spine: one record per body with its own register's code, and joins to ONS, NHS ODS, planning, GLEIF, Companies House, Wikidata", "staged": True},
}

NOT_REDISTRIBUTED = {"pbd", "pfi", "ch", "eao-ni"}  # D-OG10: pbd, pfi, ch name people; D-OG11: eao-ni carries legislation.gov.uk effect ids ("key-" + 32 hex) that GitHub push protection reads as an API key

def fetch_file(k):
    b = get(SOURCES[k]["url"], binary=True)
    if not b: raise RuntimeError("no content: " + SOURCES[k]["url"])
    (S / SOURCES[k]["file"]).write_bytes(b); return len(b)

def base_records():
    h = (S / SOURCES["base"]["file"]).read_text()
    return json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', h, re.S).group(1))["r"]

def fetch_govuk():
    out, page = [], 1
    while True:
        d = json.loads(get(f"https://www.gov.uk/api/organisations?page={page}"))
        out += d["results"]
        if page >= d.get("pages", 1): break
        page += 1; time.sleep(0.15)
    (S / SOURCES["govuk"]["file"]).write_text(json.dumps(out))
    return len(out)

def fetch_gleif(recs):
    leis = sorted({r[10]["lei"] for r in recs if r[10].get("lei")})
    out = {}
    for lei in leis:
        row = {}
        for rel in ("direct", "ultimate"):
            p = get(f"https://api.gleif.org/api/v1/lei-records/{lei}/{rel}-parent")
            if p:
                a = json.loads(p)["data"]; row[rel] = {"lei": a["id"], "name": a["attributes"]["entity"]["legalName"]["name"]}
            else:
                e = get(f"https://api.gleif.org/api/v1/lei-records/{lei}/{rel}-parent-reporting-exception")
                row[rel] = {"exception": json.loads(e)["data"]["attributes"].get("reason") if e else None}
            time.sleep(0.12)
        out[lei] = row
    (S / SOURCES["gleif"]["file"]).write_text(json.dumps(out, indent=0))
    return len(out)

def fetch_psc(recs):
    out = {}
    for r in recs:
        no = r[10].get("companies_house")
        if not no: continue
        t = get(f"https://find-and-update.company-information.service.gov.uk/company/{no}/persons-with-significant-control")
        pscs = []
        if t:
            for blk in re.split(r'<div class="appointment-\d+">', t)[1:]:
                # D-OG1: the name sits in a nested <span><b>; read the whole psc-name span and strip tags
                nm = re.search(r'<span id="psc-name-\d+">(.*?)</span>\s*</span>', blk, re.S)
                if not nm: continue
                nm_text = re.sub(r"<[^>]+>|\s+", " ", nm.group(1)).strip()
                st = re.search(r'id="psc-status-tag-\d+"[^>]*>(.*?)<', blk)
                ceased = bool(st and "ceased" in st.group(1).lower()) or bool(re.search(r'Ceased on', blk))
                nat = [html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x))).strip() for x in re.findall(r'id="psc-noc-[^"]*"[^>]*>(.*?)</', blk, re.S)]
                kind = re.search(r'id="psc-legal-form-\d+"[^>]*>(.*?)</dd>', blk, re.S)
                pscs.append({"name": html.unescape(nm_text), "ceased": ceased, "control": nat, "legal_form": html.unescape(re.sub(r"<[^>]+>|\s+", " ", kind.group(1))).strip() if kind else ""})
            if not pscs and re.search(r"no persons with significant control|There are no", t, re.I): pscs = []
        out[no] = {"pscs": pscs, "page": f"https://find-and-update.company-information.service.gov.uk/company/{no}/persons-with-significant-control"}
        time.sleep(0.6)
    (S / SOURCES["ch"]["file"]).write_text(json.dumps(out, indent=0))
    return len(out)

if __name__ == "__main__":
    recs = base_records()
    counts = {}
    if "--offline" not in sys.argv:
        counts["govuk"] = fetch_govuk(); counts["gleif"] = fetch_gleif(recs); counts["ch"] = fetch_psc(recs)
        for k in ("pbd", "pfi", "eao-ni", "tf"): counts[k] = fetch_file(k)
    elif "--private" in sys.argv:  # offline build in CI: fetch only what the repository doesn't hold
        counts["pbd"] = fetch_file("pbd"); counts["pfi"] = fetch_file("pfi"); counts["eao-ni"] = fetch_file("eao-ni"); counts["ch"] = fetch_psc(recs)
    man = {}
    for k, s in SOURCES.items():
        p = S / s["file"]
        if not p.exists(): sys.exit(f"missing source file {p}: the build fails closed")
        man[k] = dict(s, redistributed=k not in NOT_REDISTRIBUTED, sha256=sha(p), bytes=p.stat().st_size, retrieved=(json.loads((S / "manifest.json").read_text()).get(k, {}).get("retrieved", NOW) if (S / "manifest.json").exists() and "--offline" in sys.argv else NOW) if not s.get("staged") else ("2026-11-14T18:32:29Z" if k == "base" else "2026-09-21"))
    (S / "manifest.json").write_text(json.dumps(man, indent=1))
    print("fetched", counts, "manifest", len(man))
