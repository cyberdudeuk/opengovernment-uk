"""OpenGovernment UK 0.3: the accountability tree of the UK state.

Who answers for each public body, who pays for it, and who owns it, traced edge by edge to the authoritative source.
The UK public-sector equivalent of a corporate tree and ultimate beneficial ownership is built from four kinds of evidence:
  law      the department whose estimate and accounts include the body (Estimates and Accounts Order 2026),
           and designation for Whole of Government Accounts (WGA Order 2026); NI equivalent order 2026
  control  ONS sponsoring entity, controlling unit and parent company (Public Sector Classification Guide, Nov 2026)
  sponsor  Cabinet Office Public Bodies Directory 2023/24 (sponsor, government-funded income, total managed expenditure)
  admin    GOV.UK parent organisations; successors after machinery-of-government changes
  owner    Companies House persons with significant control; GLEIF accounting consolidation parents;
           HM Treasury PFI/PF2 project companies, their procuring authorities and equity holders
Every edge carries its source, the row or part it came from, and how its two ends were matched. Nothing is inferred
silently: anything that cannot be matched to a register record goes to the unresolved queue, never guessed.
Personal names are never reproduced (natural persons with significant control are counted, not named)."""
import collections, datetime, hashlib, json, pathlib, re
import openpyxl
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
S, OUT = ROOT / "sources", ROOT / "data"; OUT.mkdir(exist_ok=True)
MAN = json.loads((S / "manifest.json").read_text())

# ---------- base register (identity spine) ----------
base = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (S / MAN["base"]["file"]).read_text(), re.S).group(1))
FAMS = base["fam"]
R = {}
for r in base["r"]:
    R[r[0]] = {"id": r[0], "name": r[1], "fam": FAMS[r[2]], "type": r[3], "open": bool(r[4]), "parents": r[6], "ids": r[10],
               "ons": {"sector": r[11][0], "esa": r[11][1], "sponsor": r[11][2]}, "pred": r[15], "succ": r[16], "abbr": r[18], "nation": r[5]}
SLUG = {v["ids"]["govuk_slug"]: k for k, v in R.items() if v["ids"].get("govuk_slug")}
CHNO = {v["ids"]["companies_house"]: k for k, v in R.items() if v["ids"].get("companies_house")}

# ---------- name matching (exact after documented cleaning; never fuzzy) ----------
LEGAL = [r"^board of trustees of (the )?", r"^the trustees of (the )?", r"^trustees of (the )?", r"^the board of (the )?", r"^board of (the )?",
         r"^the governors of (the )?", r"^the commissioners for ", r"^commissioners of ", r"^the ", r"\s+(limited|ltd|plc|llp)$", r"\s+\(.*?\)$"]
def norm(s):
    s = (s or "").lower().replace("’", "'").replace("&", " and ").replace("–", "-")
    s = re.sub(r"[.,'`\"]", "", s); s = re.sub(r"[-/]", " ", s); return re.sub(r"\s+", " ", s).strip()
def strip_legal(s):
    s = norm(s)
    for p in LEGAL: s = re.sub(p, "", s).strip()
    return s
IDX, IDX2 = collections.defaultdict(set), collections.defaultdict(set)
for k, v in R.items():
    for nm in {v["name"], v["ids"].get("ons_name") or ""} - {""}:
        IDX[norm(nm)].add(k); IDX2[strip_legal(nm)].add(k)
    if v["abbr"]: IDX[norm(v["abbr"])].add(k)
ALIAS = {"sg": "The Scottish Government", "wg": "Welsh Government", "nie": "Northern Ireland Executive", "department of health": "Department of Health and Social Care",
         "attorney generals office": "Attorney General's Office", "hmt": "HM Treasury", "hm treasury": "HM Treasury"}
def current(k, seen=()):
    """Follow GOV.UK successor links to the open record (machinery-of-government changes)."""
    v = R.get(k)
    if not v or v["open"] or not v["succ"] or k in seen: return k
    nxt = [s for s in v["succ"] if s in R]
    return current(nxt[0], seen + (k,)) if len(nxt) == 1 else k
def match(name, prefer_open=True):
    """Return (id, method) or (None, reason). Exact cleaned names only; ambiguity is reported, not resolved."""
    if not name: return None, "blank"
    n = norm(name); n = norm(ALIAS.get(n, name)) if n in ALIAS else n
    for idx, how in ((IDX, "name, cleaned"), (IDX2, "name without legal form")):
        hits = idx.get(n if idx is IDX else strip_legal(n if n not in ALIAS else ALIAS[n]), set())
        if prefer_open and len(hits) > 1:
            op = {h for h in hits if R[h]["open"]}
            if len(op) == 1: hits = op
            elif len(op) > 1:
                gov = {h for h in op if h.startswith("government-organisation:")}
                if len(gov) == 1: hits = gov
        if len(hits) == 1:
            h = next(iter(hits)); c = current(h)
            return c, how + ("; followed GOV.UK successor" if c != h else "")
        if len(hits) > 1: return None, f"ambiguous: {len(hits)} records share this name"
    return None, "no register record with this name"

LA_STOP = {"council","city","borough","metropolitan","county","district","london","of","the","royal","and","mbc","cc","dc","bc","lbc"}
def la_key(s): return " ".join(w for w in norm(s).split() if w not in LA_STOP)
LAIDX = collections.defaultdict(set)
for k, v in R.items():
    if v["fam"] == "Local authority" and v["open"]: LAIDX[la_key(v["name"])].add(k)
def match_la(name):
    """Procuring authorities in HM Treasury's PFI data are often written as a place ('Barnsley'). Accept only a unique open council."""
    hits = LAIDX.get(la_key(name), set())
    return (next(iter(hits)), "council short name (unique among open local authorities)") if len(hits) == 1 else (None, "no unique council for this place name")

PERSON = re.compile(r"^(?:mr|mrs|ms|miss|dr|sir|dame|lady|professor|prof)\b|^lord\s+(?!chancellor|advocate|president|privy|high|lieutenant|chief)", re.I)  # D-OG4, shared with tools/check.py
CORP = re.compile(r"\b(limited|limted|ltd|plc|llp|lp|group|holdings|ventures|enterprises|capital|partners|fund|investments|infrastructure|company|co)\b", re.I)
def is_person(n): return bool(PERSON.match(n or "")) and not CORP.search(n or "")  # D-OG5: companies named after people stay visible; bare names are withheld
EDGES, UNRES = [], []
def edge(child, parent_id, parent_text, rel, src, ref, how, **extra):
    if not child: return
    e = {"c": child, "p": parent_id, "pt": parent_text, "rel": rel, "src": src, "ref": ref, "how": how}
    e.update({k: v for k, v in extra.items() if v not in (None, "", [])}); EDGES.append(e)
def unresolved(src, text, ref, why, role):
    UNRES.append({"src": src, "text": text, "ref": ref, "why": why, "role": role})

# ---------- law: Estimates and Accounts Order 2026 (and NI 2026) ----------
def designation(file, src):
    x = (S / file).read_text(); n = 0
    for part in re.findall(r"<Part[^>]*>(.*?)</Part>", x, re.S):
        dept = re.sub(r"<[^>]+>", "", re.search(r"<Title>(.*?)</Title>", part, re.S).group(1)).strip()
        did, dhow = match(dept)
        if not did: unresolved(src, dept, "Schedule part title", dhow, "department")
        for item in re.findall(r"<ListItem[^>]*>(.*?)</ListItem>", part, re.S):
            body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", item)).strip(); n += 1
            bid, bhow = match(body)
            if not bid: unresolved(src, body, f"Schedule, part: {dept}", bhow, "body"); continue
            edge(bid, did, dept, "accounts", src, f"Schedule, part: {dept}", f"body: {bhow}; department: {dhow}")
    return n
N_EAO = designation(MAN["eao"]["file"], "eao")
N_NI = designation("ni-eao-2026.xml", "eao-ni")

# WGA designation (attribute)
WGAO = {}
x = (S / MAN["wgao"]["file"]).read_text()
for sec in re.findall(r"<Part[^>]*>(.*?)</Part>", x, re.S) or [x]:
    t = re.search(r"<Title>(.*?)</Title>", sec, re.S); t = re.sub(r"<[^>]+>", "", t.group(1)).strip() if t else "Schedule"
    for item in re.findall(r"<ListItem[^>]*>(.*?)</ListItem>", sec, re.S):
        body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", item)).strip()
        bid, how = match(body)
        if bid: WGAO[bid] = {"part": t, "listed_as": body}
        else: unresolved("wgao", body, t, how, "body")
# WGA 2024-25 annex status (attribute)
WGA = {}
for w in json.loads((S / MAN["wga"]["file"]).read_text())["wga"]:
    bid, how = match(w["name"])
    if bid: WGA.setdefault(bid, {"status": w["status"], "layer": w["layer"], "annex": w["annex"], "row": w["row"], "listed_as": w["name"]})

# ---------- control: ONS Public Sector Classification Guide ----------
wb = openpyxl.load_workbook(S / MAN["ons"]["file"], read_only=True)
def sheet(name, first):
    rows = list(wb[name].iter_rows(values_only=True)); h = next(i for i, r in enumerate(rows) if r and r[0] == first)
    return rows[h], [r for r in rows[h + 1:] if r and r[0]]
_, ONSROWS = sheet("Organisation|Institutional Unit", "Name")
ONSBY = {}
for i, r in enumerate(ONSROWS, 1):
    name, sector, esa, _, classified, parentco, subs, sponsor = r[:8]
    if sector and str(sector).strip() == "Not in the Public Sector": continue
    bid, how = match(name)
    ref = f"Organisation sheet, row {i}"
    if not bid: unresolved("ons", name, ref, how, "body"); continue
    ONSBY[bid] = {"sector": str(sector or "").strip(), "esa": esa, "classified": str(classified)[:10] if classified else ""}
    if sponsor and str(sponsor).strip().lower() not in ("local authorities",):
        pid, phow = match(str(sponsor))
        if pid and pid != bid: edge(bid, pid, sponsor, "sponsors", "ons", ref, f"body: {how}; sponsor: {phow}")
        elif not pid: unresolved("ons", sponsor, ref + " (sponsoring entity)", phow, "sponsor")
    if parentco:
        pid, phow = match(str(parentco))
        if pid and pid != bid: edge(bid, pid, parentco, "owns", "ons", ref + " (parent company)", f"body: {how}; parent: {phow}")
        elif not pid: unresolved("ons", parentco, ref + " (parent company)", phow, "parent")
_, NIU = sheet("Non-Institutional Units", "Non-Institutional Unit name")
for i, r in enumerate(NIU, 1):
    bid, how = match(r[0]); pid, phow = match(r[1]); ref = f"Non-institutional units sheet, row {i}"
    if bid and pid and bid != pid: edge(bid, pid, r[1], "controls", "ons", ref, f"body: {how}; controlling unit: {phow}")
    elif not bid: unresolved("ons", r[0], ref, how, "body")

# ---------- sponsor and money: Public Bodies Directory 2023/24 ----------
wb2 = openpyxl.load_workbook(S / MAN["pbd"]["file"], read_only=True, data_only=True)
ws = wb2["Data"]; ws.reset_dimensions(); rows = list(ws.iter_rows(values_only=True))
h = next(i for i, r in enumerate(rows) if r and r[0] == "overall_financial_year"); H = rows[h]
MONEY = {}
for i, r in enumerate(rows[h + 1:], 1):
    if not r or not r[1]: continue
    d = dict(zip(H, r, strict=False)); ref = f"Data sheet, row {i} ({d.get('overall_copbt_uid')})"
    bid, how = match(d["overall_alb_name"])
    if not bid: unresolved("pbd", d["overall_alb_name"], ref, how, "body"); continue
    sp = d.get("overall_direct_sponsor") if d.get("overall_direct_sponsor") not in (None, "N/A") else d["overall_parent_department"]
    pid, phow = match(sp)
    num = lambda k, d=d: float(d[k]) if isinstance(d.get(k), (int, float)) else None
    MONEY[bid] = {"year": d["overall_financial_year"], "gov_funded": num("finance_budget_govt_income"), "other_income": num("finance_budget_other_income"),
                  "tme": num("finance_spend_tme"), "grants": num("finance_spend_grants"), "classification": d.get("overall_classification"),
                  "purpose": d.get("overall_primary_purpose"), "ombudsman": d.get("accountability_ombudsman"), "framework": d.get("accountability_framework_doc_year"),
                  "staff_fte": num("staffing_fte_inpost"), "uid": d.get("overall_copbt_uid")}
    if pid and pid != bid: edge(bid, pid, sp, "sponsors", "pbd", ref, f"body: {how}; sponsor: {phow}", money=MONEY[bid]["gov_funded"])
    elif not pid: unresolved("pbd", sp, ref + " (sponsor)", phow, "sponsor")

# ---------- admin: GOV.UK parent organisations (fresh read) ----------
GOVUK = {o["details"]["slug"]: o for o in json.loads((S / MAN["govuk"]["file"]).read_text())}
for slug, o in GOVUK.items():
    cid = SLUG.get(slug)
    if not cid: unresolved("govuk", o["title"], "GOV.UK API record " + slug, "not in the 0.2.2 spine (new since 14 November)", "body"); continue
    for p in o.get("parent_organisations") or []:
        ps = p["id"].rstrip("/").split("/")[-1]; pid = SLUG.get(ps)
        if pid: edge(cid, current(pid), p.get("title") or ps, "parent", "govuk", "parent_organisations of " + slug, "GOV.UK slug")

# ---------- owner: Companies House PSC, GLEIF, ONS parent company (above), PFI ----------
PSC = json.loads((S / MAN["ch"]["file"]).read_text()); PERSONS = collections.Counter()
SOS = re.compile(r"secretary of state (?:for|representing (?:the )?department for)\s+(.*)", re.I)
for no, v in PSC.items():
    cid = CHNO.get(no)
    for p in v["pscs"]:
        if p["ceased"]: continue
        nm = p["name"]; ref = v["page"]
        if is_person(nm): PERSONS[cid] += 1; continue
        target = nm
        m = SOS.search(nm)
        if m: target = re.sub(r"^the\s+", "", m.group(1), flags=re.I)
        if re.search(r"treasury|chancellor of the exchequer", nm, re.I): target = "HM Treasury"
        pid, how = match(target)
        if not pid: pid, how = match("Department for " + target) if m else (None, how)
        if pid and pid != cid: edge(cid, pid, nm, "owns", "ch", ref, f"company number; holder: {how}", control="; ".join(p["control"]))
        elif not pid: unresolved("ch", nm, ref, how, "holder")
GLEIF = json.loads((S / MAN["gleif"]["file"]).read_text()); LEI = {v["ids"]["lei"]: k for k, v in R.items() if v["ids"].get("lei")}
GLEIFX = collections.Counter()
for lei, v in GLEIF.items():
    cid = LEI.get(lei)
    for rel in ("direct", "ultimate"):
        x = v.get(rel) or {}
        if x.get("lei"):
            pid = LEI.get(x["lei"])
            if pid and pid != cid: edge(cid, pid, x["name"], "owns", "gleif", f"LEI {lei}, {rel} accounting consolidation parent", "LEI")
            elif not pid: unresolved("gleif", x["name"], f"LEI {lei} {rel} parent {x['lei']}", "parent LEI not in the register", "parent")
        elif rel == "ultimate": GLEIFX[x.get("exception") or "none given"] += 1

pfi = pd.read_excel(S / "pfi-2025.ods", engine="odf", header=0)
PPP = []
for _, r in pfi[pfi["Unique HMT Project ID"].notna()].iterrows():
    eq = [[str(r[f"Equity Holder ({i})"]), (float(r[f"Equity Holding ({i})"]) if str(r[f"Equity Holding ({i})"]).replace('.', '', 1).isdigit() else str(r[f"Equity Holding ({i})"]))]
          for i in range(1, 8) if str(r[f"Equity Holder ({i})"]) not in ("nan", "", "No Data Provided")]
    withheld = sum(1 for h, _ in eq if is_person(h)); eq = [x for x in eq if not is_person(x[0])]
    auth, ahow = match(str(r["Procuring Authority"]))
    if not auth and str(r["Procuring authority type"]).strip().lower() == "local": auth, ahow = match_la(str(r["Procuring Authority"]))
    dept, dhow = match(re.sub(r"\s*\(.*?\)\s*$", "", str(r["Department"])))
    pay = r.get("2025-26 (£M)"); pay = float(pay) if isinstance(pay, (int, float)) and pay == pay else None
    spv_no = str(r["SPV Company Number"]).strip(); spv_no = spv_no.zfill(8) if spv_no.isdigit() else spv_no
    node = {"id": f"pfi:{int(r['Unique HMT Project ID'])}", "project": str(r["Project Name"]).strip(), "status": str(r["Project Status"]), "sector": str(r["Sector"]),
            "authority": auth, "authority_text": str(r["Procuring Authority"]), "authority_type": str(r["Procuring authority type"]), "dept": dept, "dept_text": str(r["Department"]),
            "spv": str(r["SPV Name"]).strip() if str(r["SPV Name"]) != "nan" else "", "spv_no": spv_no if spv_no not in ("nan", "No Data Provided") else "",
            "equity": eq, "equity_withheld": withheld, "capital": float(r["Capital Value (£m)"]) if isinstance(r["Capital Value (£m)"], (int, float)) and r["Capital Value (£m)"] == r["Capital Value (£m)"] else None,
            "pay_2025_26": pay, "expiry": str(r["Contract expiry date"])[:10], "balance_sheet_esa": str(r["On / Off balance sheet under ESA"]),
            "ref": f"Current PFI PF2 projects at 31 March 2025, project {int(r['Unique HMT Project ID'])}"}
    if not auth: unresolved("pfi", node["authority_text"], node["ref"], ahow, "procuring authority")
    PPP.append(node)

UKGI = []  # D-OG2: UKGI publishes no structured portfolio list; its control shows through Companies House records instead

# ---------- trading funds (ONS information text and legislation titles) ----------
TF = set()
for r in ONSROWS:
    if r[8] and re.search(r"\btrading fund\b", str(r[8]), re.I) and str(r[1]).strip() != "Not in the Public Sector":
        bid, _ = match(r[0]);  TF.add(bid) if bid else None
tf_titles = sorted(set(re.findall(r"<title>The ([^<]*?) Trading Fund Order \d{4}</title>", (S / "tf-feed.xml").read_text())))
for t in tf_titles:
    bid, _ = match(t)
    if bid and R[bid]["open"]: TF.add(bid)

# ---------- chains: the accountable owner of every open body ----------
PREC = [("accounts", "eao"), ("accounts", "eao-ni"), ("sponsors", "pbd"), ("sponsors", "ons"), ("controls", "ons"), ("parent", "govuk"), ("owns", "ch"), ("owns", "ons"), ("owns", "gleif")]
ACC = {("accounts", "eao"), ("accounts", "eao-ni"), ("sponsors", "pbd"), ("sponsors", "ons"), ("controls", "ons"), ("parent", "govuk")}
BYC = collections.defaultdict(list)
for e in EDGES:
    if e["p"] and e["p"] != e["c"]: BYC[e["c"]].append(e)
def best(cid):
    es = BYC.get(cid, [])
    for rel, src in PREC:
        for e in es:
            if e["rel"] == rel and e["src"] == src: return e
    return None
TERMINAL_TYPES = {"Ministerial department", "Devolved government", "Executive office"}
def chain(cid):
    path, seen, cur = [], {cid}, cid
    while True:
        v = R[cur]
        if cur != cid and v["type"] in TERMINAL_TYPES: break
        if v["type"] == "Non-ministerial department": break  # D-OG3: answers to Parliament itself; a GOV.UK parent is its minister, not an owner
        e = best(cur)
        if not e or e["p"] in seen: break
        path.append({"from": cur, "to": e["p"], "rel": e["rel"], "src": e["src"], "ref": e["ref"]}); seen.add(e["p"]); cur = e["p"]
        if len(path) > 8: break
    root = R[cur]
    return path, cur, root
def answerable(root):
    t = root["type"]
    if t == "Ministerial department": return "Parliament, through the Secretary of State or minister in charge"
    if t == "Non-ministerial department": return "Parliament, through its sponsoring minister"
    if t == "Devolved government": return {"SC": "the Scottish Parliament", "WA": "the Senedd", "NI": "the Northern Ireland Assembly"}.get(root.get("nation", ""), "its devolved legislature")
    if root["fam"] == "Local authority": return "its elected council"
    if re.search(r"parliament|national audit office|electoral commission|parliamentary|ipsa|house of commons|house of lords", root["name"], re.I) and root.get("nation", "") not in ("SC", "WA", "NI"): return "Parliament directly (not a ministerial body)"
    sec = (ONSBY.get(root["id"]) or {}).get("sector") or root["ons"]["sector"]
    if sec.startswith("Local Government"): return "local government (a council or group of councils)"
    if root["ons"]["sponsor"] in ("SG",) or root.get("nation") == "SC": return "the Scottish Parliament"
    if root["ons"]["sponsor"] in ("WG",) or root.get("nation") == "WA": return "the Senedd"
    if root.get("nation") == "NI": return "the Northern Ireland Assembly"
    if root["fam"] == "NHS body": return "NHS governance in its nation"
    return "not established from the sources"
CHAINS, CONFLICTS = {}, []
for cid, v in R.items():
    if not v["open"]: continue
    # every open body gets a chain, so a body with no evidence is visible as a gap rather than missing
    path, root_id, root = chain(cid)
    parents = collections.defaultdict(set)
    for e in BYC.get(cid, []):
        if (e["rel"], e["src"]) in ACC: parents[e["p"]].add(e["src"])
    agree = max((len(s) for s in parents.values()), default=0)
    if len(parents) > 1:
        CONFLICTS.append({"id": cid, "views": [{"parent": p, "sources": sorted(s)} for p, s in sorted(parents.items(), key=lambda kv: -len(kv[1]))]})
    CHAINS[cid] = {"path": path, "root": root_id, "answerable": answerable(root), "agree": agree, "assertions": len(parents),
                   "wgao": WGAO.get(cid), "wga": WGA.get(cid), "money": MONEY.get(cid), "ons": ONSBY.get(cid), "persons_with_control": PERSONS.get(cid, 0),
                   "trading_fund": cid in TF, "ukgi": cid in UKGI}

# PFI money rolled up to the procuring authority and the department
PFIBY = collections.defaultdict(lambda: {"projects": 0, "capital": 0.0, "pay_2025_26": 0.0})
for p in PPP:
    for k in (p["authority"], p["dept"]):
        if k:
            a = PFIBY[k]; a["projects"] += 1; a["capital"] += p["capital"] or 0; a["pay_2025_26"] += p["pay_2025_26"] or 0
for k, a in PFIBY.items():
    if k in CHAINS: CHAINS[k]["pfi"] = {kk: round(vv, 1) if isinstance(vv, float) else vv for kk, vv in a.items()}

# ---------- write ----------
def sha(o): return hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()
srcs = {k: {kk: v[kk] for kk in ("name", "url", "owner", "licence", "asserts", "retrieved", "sha256")} for k, v in MAN.items()}
srcs["eao-ni"] = {"name": "Government Resources and Accounts Act (Northern Ireland) 2001 (Estimates and Accounts) (Designation of Bodies) Order 2026, S.R. 2026/49", "url": "https://www.legislation.gov.uk/nisr/2026/49/made", "owner": "Department of Finance (Northern Ireland)", "licence": "OGL v3.0", "asserts": "legal financial accountability for Northern Ireland bodies (2026-27)", "retrieved": datetime.date.today().isoformat(), "sha256": hashlib.sha256((S / "ni-eao-2026.xml").read_bytes()).hexdigest()}
srcs["pfi"] = {"name": "HM Treasury: Current PFI and PF2 projects as at 31 March 2025", "url": "https://www.gov.uk/government/publications/pfi-and-pfi2-projects-2025-summary-data", "owner": "HM Treasury / National Infrastructure and Service Transformation Authority", "licence": "OGL v3.0", "asserts": "public-private partnerships: project company, procuring authority, department, equity holders, capital value and annual unitary charges", "retrieved": datetime.date.today().isoformat(), "sha256": hashlib.sha256((S / "pfi-2025.ods").read_bytes()).hexdigest()}
srcs["tf"] = {"name": "legislation.gov.uk: trading fund orders under the Government Trading Funds Act 1973", "url": "https://www.legislation.gov.uk/all?title=Trading%20Fund%20Order", "owner": "legislation.gov.uk (The National Archives)", "licence": "OGL v3.0", "asserts": "which operations are financed as trading funds", "retrieved": datetime.date.today().isoformat(), "sha256": hashlib.sha256((S / "tf-feed.xml").read_bytes()).hexdigest()}
stats = {"records": len(R), "open": sum(v["open"] for v in R.values()), "edges": len(EDGES), "edges_by": dict(collections.Counter(f'{e["rel"]}:{e["src"]}' for e in EDGES)),
         "chains": len(CHAINS), "roots": dict(collections.Counter(c["answerable"] for c in CHAINS.values()).most_common()), "conflicts": len(CONFLICTS),
         "unresolved": len(UNRES), "unresolved_by": dict(collections.Counter(u["src"] for u in UNRES)), "eao_bodies": N_EAO, "ni_bodies": N_NI, "wgao": len(WGAO), "wga": len(WGA),
         "ons_matched": len(ONSBY), "pbd_matched": len(MONEY), "ppp_projects": len(PPP), "ppp_authorities_matched": sum(1 for p in PPP if p["authority"]),
         "trading_funds": sorted(TF), "ukgi": UKGI, "gleif_exceptions": dict(GLEIFX), "persons_with_control_withheld": sum(PERSONS.values())}
TREE = {"v": "0.3.0", "built": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "sources": srcs, "stats": stats,
        "rels": {"accounts": "Included in this department's estimate and accounts (law)", "sponsors": "Sponsored by", "controls": "Controlled by (not an institutional unit)",
                 "parent": "GOV.UK parent organisation", "owns": "Owned or controlled by"},
        "edges": EDGES, "chains": CHAINS, "conflicts": CONFLICTS, "unresolved": UNRES, "ppp": PPP}
TREE["digest"] = sha({k: TREE[k] for k in ("edges", "chains", "conflicts", "unresolved", "ppp")})
(OUT / "tree.json").write_text(json.dumps(TREE, ensure_ascii=False))
with open(OUT / "edges.csv", "w") as f:
    f.write("child_id,child_name,parent_id,parent_name,parent_as_written,relation,source,source_ref,match_method\n")
    import csv; w = csv.writer(f)
    for e in EDGES: w.writerow([e["c"], R[e["c"]]["name"], e["p"] or "", R[e["p"]]["name"] if e["p"] in R else "", e["pt"], e["rel"], e["src"], e["ref"], e["how"]])
with open(OUT / "accountable-owner.csv", "w") as f:
    import csv; w = csv.writer(f); w.writerow(["id", "name", "family", "type", "accountable_owner_id", "accountable_owner", "answerable_to", "chain", "sources_agreeing", "parents_asserted", "wga_2024_25", "government_funded_income_gbp", "total_managed_expenditure_gbp", "trading_fund", "ukgi_shareholding"])
    for k, c in CHAINS.items():
        w.writerow([k, R[k]["name"], R[k]["fam"], R[k]["type"], c["root"], R[c["root"]]["name"], c["answerable"], " > ".join([R[k]["name"]] + [R[s["to"]]["name"] + f' [{s["rel"]}:{s["src"]}]' for s in c["path"]]),
                    c["agree"], c["assertions"], (c["wga"] or {}).get("status", ""), (c["money"] or {}).get("gov_funded") or "", (c["money"] or {}).get("tme") or "", c["trading_fund"], c["ukgi"]])
print(json.dumps(stats, indent=1)[:2500])
