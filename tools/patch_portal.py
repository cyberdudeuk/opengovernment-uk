"""Build OpenGovernment UK 0.3.0 from the published 0.2.2 page plus the accountability tree.
Every textual change is an exact replacement that must match once: if the base page changes, this fails loudly."""
import csv, hashlib, json, pathlib, re, subprocess, sys, io
import barcode, qrcode, qrcode.image.svg
from barcode.writer import SVGWriter

ROOT = pathlib.Path(__file__).resolve().parents[1]; TOOLS = ROOT / "tools"; OUT = ROOT / "docs"; OUT.mkdir(exist_ok=True)  # GitHub Pages serves docs/
VER = "0.3.0"
h = (ROOT / "sources" / "opengovernment-uk-0.2.2.html").read_text()
T = json.loads((ROOT / "data" / "tree.json").read_text())

def once(s, old, new, label):
    n = s.count(old)
    if n != 1: sys.exit(f"patch '{label}': expected 1 match, found {n}")
    return s.replace(old, new)

# ---------- compact accountability payload ----------
EI = {}; E = []
for i, e in enumerate(T["edges"]):
    E.append([e["c"], e["p"], e["pt"], e["rel"], e["src"], e["ref"], e["how"], e.get("money") or e.get("control")]); EI[(e["c"], e["p"], e["rel"], e["src"])] = i
ANS = sorted({c["answerable"] for c in T["chains"].values()}); AI = {a: i for i, a in enumerate(ANS)}
CH = {k: [[EI[(s["from"], s["to"], s["rel"], s["src"])] for s in c["path"]], c["root"], AI[c["answerable"]], c["agree"], c["assertions"]] for k, c in T["chains"].items()}
M = {k: [c["money"]["year"], c["money"]["gov_funded"], c["money"]["other_income"], c["money"]["tme"], c["money"]["classification"], c["money"]["purpose"], c["money"]["ombudsman"]] for k, c in T["chains"].items() if c.get("money")}
W = {k: [c["wga"]["status"], c["wga"]["layer"]] for k, c in T["chains"].items() if c.get("wga")}
WO = {k: c["wgao"]["part"] for k, c in T["chains"].items() if c.get("wgao")}
PCS = {k: c["ons"]["sector"].replace("\n", " ") for k, c in T["chains"].items() if c.get("ons") and (c["ons"]["sector"].startswith("Public") and "Pension" not in c["ons"]["sector"] or c["ons"]["sector"] == "Central Bank")}
PW = {k: c["persons_with_control"] for k, c in T["chains"].items() if c.get("persons_with_control")}
PPP = [[p["id"].split(":")[1], p["project"], p["status"], p["sector"], p["authority"], p["authority_text"], p["dept"], re.sub(r"\s*\(.*?\)\s*$", "", p["dept_text"]), p["spv"], p["spv_no"], p["equity"], p.get("equity_withheld", 0), p["capital"], p["pay_2025_26"], p["expiry"], p["balance_sheet_esa"]] for p in T["ppp"]]
# Only disagreements still contested after triangulation are shown; resolved ones keep their reason in data/tree.json (OG-D33)
CF = [[x["id"], [[v["parent"], v["sources"]] for v in x["views"]], x["reason"]] for x in T["conflicts"] if x.get("status") == "contested"]
CF_RESOLVED = sum(1 for x in T["conflicts"] if x.get("status") == "resolved")
UN = [[u["src"], u["text"], u["ref"], u["why"], u["role"]] for u in T["unresolved"]]
SRC = {k: v for k, v in T["sources"].items() if k not in ("base",)}
ACC = {"v": VER, "built": T["built"], "digest": T["digest"], "legend": {"e": "child, parent, parent as written, relation, source, where in source, match method, money or control",
       "ch": "edge indexes to the root, root, answers-to index, sources agreeing, parents asserted", "m": "year, government funded income, other income, total managed expenditure, classification, purpose, ombudsman",
       "ppp": "HMT id, project, status, sector, authority id, authority, department id, department, project company, company number, equity [holder, share], individuals withheld, capital £m, charge 2025-26 £m, end, ESA balance sheet"},
       "src": SRC, "e": E, "ans": ANS, "ch": CH, "m": M, "w": W, "wo": WO, "tf": T["stats"]["trading_funds"], "pcs": PCS, "pw": PW, "ppp": PPP, "cf": CF, "cfr": CF_RESOLVED, "un": UN,
       "nat": json.loads((ROOT / "data" / "body-nations.json").read_text())}  # tools/nations.py: final nation placement per body
acc_json = json.dumps(ACC, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

# ---------- data block edits ----------
m = re.search(r'(<script[^>]*id="data"[^>]*>)(.*?)(</script>)', h, re.S); D = json.loads(m.group(2))
D["v"] = VER; D["built"] = T["built"]
chk = subprocess.run([sys.executable, str(TOOLS / "check.py")], capture_output=True, text=True)  # noqa: S603 fixed interpreter and script path, no input
neg = subprocess.run([sys.executable, str(TOOLS / "check.py"), "--negative"], capture_output=True, text=True)  # noqa: S603
if chk.returncode or neg.returncode: sys.exit("accountability checks failed; nothing written\n" + chk.stdout + neg.stdout)
for line in chk.stdout.splitlines():
    st, rest = line.split(" ", 1); name, doc = rest.split(" — ", 1)
    D["checks"].append({"id": "AT-" + name[2:], "name": doc.strip(), "problems": [], "pass": st == "pass"})
    D["vacc"].append({"id": "AT-" + name[2:], "caught": ("caught " + name) in neg.stdout})
for k, v in SRC.items():
    if k not in D["src"]: D["src"][k] = {"name": v["name"], "url": v["url"], "owner": v["owner"], "licence": v["licence"], "read": v["retrieved"]}
D["nr"].append({"source": "Scottish Government national public bodies directory (gov.scot)", "why": "the site refuses automated reads; Scottish bodies come from ONS and GOV.UK instead"})
D["nr"].append({"source": "UK Government Investments portfolio", "why": "published only as prose in its annual report; government shareholdings show through Companies House controllers instead"})
c = D["contract"]; c["version"] = "1.1.0"
c["files"] += ["accountability.json", "edges.csv", "accountable-owner.csv", "ppp.csv"]
c["fields"].update({"accountable_owner": "the key of the body at the top of the chain (accountable-owner.csv)", "answers_to": "the elected body it answers to in the end", "edges": "child, parent, relation, source, where in the source, match method"})
c["change"] += " 1.1.0 (additive): accountability, money and ownership files."
for x in c["consumers"]:
    x["app"] = x["app"].replace("AIM OCDO PMO portal", "AIM Government Data Directorate PMO portal")
    if x["app"] == "DAM Policy and CDA portals":
        x.update(app="DAM Policy returns: SharePoint reference list and Dataverse", holds_now="data/reference-organisations.csv (308 in-scope bodies), DAM Reference Organisations list, dam_Organisation table",
                 reads="id, name, accountable_owner, answers_to, wga, ids.govuk_slug", status="adopting (0.3.0)", note="the reference list is regenerated from this feed; local columns keep only scope decisions")
c["consumers"] += [
    {"app": "CDA register and CDA Estate Command Dashboard", "holds_now": "publishing-body names and WGA status per return", "reads": "id, accountable_owner, wga (accountability.json)", "status": "proposed"},
    {"app": "DAM Insight", "holds_now": "organisation names on returns", "reads": "id, name, accountable_owner", "status": "proposed"},
    {"app": "Social Care Legacy Exit portal", "holds_now": "council and NHS body names", "reads": "id, ids.local_authority, ids.nhs_ods, answers_to", "status": "proposed"},
    {"app": "Portfolio portal (Government Data Directorate)", "holds_now": "departments and bodies in its portfolio", "reads": "id, name, accountable_owner", "status": "proposed"},
    {"app": "dcat-ap-uk", "holds_now": "publisher URIs", "reads": "id as dct:publisher, state.jsonld", "status": "proposed"}]
data_json = json.dumps(D, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
h = h[:m.start(2)] + data_json + h[m.end(2):]
mf = re.search(r'(<script[^>]*id="files"[^>]*>)(.*?)(</script>)', h, re.S); F = json.loads(mf.group(2))
F["feed-contract.json"] = json.dumps(c, indent=1, ensure_ascii=False)  # D-OG6: the download is regenerated from the same contract as the page
h = h[:mf.start(2)] + json.dumps(F, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + h[mf.end(2):]

# ---------- page edits ----------
files_end = re.search(r'<script[^>]*id="files"[^>]*>.*?</script>', h, re.S).end()
h = h[:files_end] + f'\n<script id="tree" type="application/json">{acc_json}</script>' + h[files_end:]
h = once(h, "  <!-- DATA -->", (TOOLS / "tree-view.html").read_text() + "  <!-- DATA -->", "view")
h = once(h, "</style>", (TOOLS / "tree-view.css").read_text() + "</style>", "css") if h.count("</style>") == 1 else h.replace("</style>", (TOOLS / "tree-view.css").read_text() + "</style>", 1)
ICONS = '<symbol id="i-crown" viewBox="0 0 24 24"><path d="M3 8l4.5 4L12 5l4.5 7L21 8l-2 11H5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></symbol><symbol id="i-coin" viewBox="0 0 24 24"><ellipse cx="12" cy="7" rx="7" ry="3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M5 7v10c0 1.7 3.1 3 7 3s7-1.3 7-3V7M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>'
h = once(h, '<symbol id="i-tree"', ICONS + '<symbol id="i-tree"', "icons")
js = (TOOLS / "tree-view.js").read_text()
# Top-level names added by this release must not redeclare the base page's (OG-D31: "NAT" collided and stopped the page).
_decl = lambda t: set(re.findall(r"^(?:const|let|function)\s+([A-Za-z_$][\w$]*)", t, re.M))
_clash = _decl(js) & _decl(re.sub(r"<script id=\"tree\".*?</script>", "", h, flags=re.S))
if _clash: sys.exit(f"top-level names redeclared: {sorted(_clash)}")
h = once(h, "// ---- start ----", js + "\n// ---- start ----", "js")
h = once(h, "home(); explore(); setupRegister(); renderRegister(); reconcile(); changes(); dataView(); quality(); help(); product(); ask();\nroute(); selfChecks();",
         "home(); explore(); setupRegister(); renderRegister(); reconcile(); changes(); whoAnswers(); dataView(); quality(); help(); product(); ask();\nroute(); selfChecks(); treeSelfChecks();", "start")
h = once(h, "const G = [[", "const G = [...TREE_TERMS, [", "glossary")
h = once(h, "const DEFECTS = [[", (TOOLS / "tree-defects.js").read_text() + "const DEFECTS = [...TREE_DEFECTS, [", "defects")  # D-OG7: must precede DEFECTS (temporal dead zone)
h = once(h, '$("#relList").innerHTML = `<li><b>0.2.2</b>', '$("#relList").innerHTML = `<li><b>0.3.0</b>, 22 November 2026: who answers for each body. Accountability, money and ownership from the Estimates and Accounts Orders (UK and Northern Ireland), the Whole of Government Accounts order and annex, ONS, the Public Bodies Directory, Companies House controllers, GLEIF and HM Treasury\'s PFI register, every link traced to a fingerprinted source; trading funds, public corporations and PPPs; the register becomes the single source for the DAM returns ecosystem.</li><li><b>0.2.2</b>', "release")
h = once(h, 'const SUGG = ["Which bodies does the Ministry of Defence have under it?",', 'const SUGG = ["Who does the Met Office answer to in the end?", "Which PFI contracts does the Department of Health and Social Care pay for?", "Which bodies does the Ministry of Defence have under it?",', "suggest")
WHO = '{name:"who_answers", description:"For one exact record id: the chain of bodies it answers to, each step with its source and where in the source; who it answers to in the end; its government funding, Whole of Government Accounts status and PFI contracts.", inputSchema:{type:"object", properties:{id:{type:"string"}}, required:["id"]}, execute: ({id}) => { if (!ACC.ch[id]) throw new Error("no accountability data for that id"); used.add(id); const c = CHAIN(id); const pp = ACC.ppp.filter(p => p[4] === id || p[6] === id); return {body: BY[id].name, chain: c.path.map(e => ({to: BY[e.p] ? BY[e.p].name : e.p, relation: RELNAME[e.rel], source: SRC(e.src).name, where: e.ref})), answers_to: c.ans, government_funding: ACC.m[id] ? {year: ACC.m[id][0], gov_funded_gbp: ACC.m[id][1], tme_gbp: ACC.m[id][3]} : null, wga: ACC.w[id] ? ACC.w[id][0] : null, pfi: pp.length ? {contracts: pp.length, capital_gbp_m: Math.round(pp.reduce((s, p) => s + (p[12] || 0), 0)), charges_2025_26_gbp_m: Math.round(pp.reduce((s, p) => s + (p[13] || 0), 0))} : null}; }},\n                     '
h = once(h, '{name:"count", description:"Count open or all records', WHO + '{name:"count", description:"Count open or all records', "ask tool")
h = once(h, "Families in the register: ${D.fam.join(\", \")}.", "Families in the register: ${D.fam.join(\", \")}. For who a body answers to, who funds it or who owns it, find its id with search_register and then call who_answers; quote the sources it gives.", "ask prompt")
h = once(h, 'function fallback(q, out, used){ const rs = searchRecords(q, 8); rs.forEach(r => used.add(r.id)); $(".ans", out).innerHTML = rs.length ? `These records match your question. Open one to see its identifiers, parents and lineage.`',
         'function fallback(q, out, used){ const rs = searchRecords(q, 8); rs.forEach(r => used.add(r.id)); if (rs.length && /who (answers|owns|funds|pays|sponsors)|answer to|accountab|ultimate|owner|PFI|fund/i.test(q) && ACC.ch[rs[0].id]) { $(".ans", out).innerHTML = chainHTML(rs[0].id) + factsHTML(rs[0].id); return; } $(".ans", out).innerHTML = rs.length ? `These records match your question. Open one to see its identifiers, parents and lineage.`', "fallback")
h = once(h, '["ask","Ask a question","Answers drawn only from the register.","ask"]', '["crown","Who answers","Trace any body to whoever answers for it, with the money and the owners.","tree"],["ask","Ask a question","Answers drawn only from the register.","ask"]', "home tile")
h = once(h, '<a class="btn ghost" href="#register"><svg aria-hidden="true"><use href="#i-list"/></svg>Search the register</a>', '<a class="btn ghost" href="#register"><svg aria-hidden="true"><use href="#i-list"/></svg>Search the register</a><a class="btn ghost" href="#tree"><svg aria-hidden="true"><use href="#i-crown"/></svg>Who answers</a><a class="btn ghost" href="nations.html"><svg aria-hidden="true"><use href="#i-list"/></svg>Nation by nation</a><a class="btn ghost" href="navigator.html"><svg aria-hidden="true"><use href="#i-list"/></svg>Documentation</a>', "hero")
h = once(h, '["Next","ANA, GovCRM, MEASR and the MoG canon read the feed","must"]', '["Now","DAM returns reference list and Dataverse read the feed","must"],["Next","ANA, GovCRM, MEASR, the CDA register and the MoG canon read the feed","must"],["Next","Resolve the names left for a person, starting with classes of body in the Orders","must"],["Later","Scottish Government directory and UKGI portfolio when they can be read","should"]', "roadmap")
h = once(h, 'const REQS = [', 'const REQS = [["OG-R21","Who answers for each body, traced to the law and the sponsor","Must","Done","Estimates and Accounts Orders, PBD, ONS; checks AT-chain_shape, AT-known_answers"],["OG-R22","Follow the money: government funding and PFI charges","Must","Done","PBD 2023/24; HMT PFI register 2025"],["OG-R23","Ownership: Companies House controllers, GLEIF parents, PFI investors","Must","Done","No natural person named; check AT-no_persons"],["OG-R24","Trading funds, public corporations and public-private partnerships","Must","Done","legislation.gov.uk orders; ONS sectors; 654 contracts"],["OG-R25","Lineage to a fingerprinted source for every link","Must","Done","Provenance ledger; check AT-hashes, AT-digest"],["OG-R26","Single source of truth for the estate\'s apps","Must","In progress","DAM returns adopting; others proposed"],["OG-R38","Each nation\'s register: its public bodies by branch of the state, with each branch\'s apex from its founding legislation","Must","Done","nations.html; checks for known answers and apexes"],', "reqs")
h = once(h, '["OG-R11","Daily refresh that proposes changes as pull requests","Must","In progress"', '["OG-R11","Refresh on demand: a manual workflow rebuilds and checks everything, reviewed before publishing (no schedule to maintain)","Must","Done"', "R11 matches operation")
_ids = re.findall(r'\["(OG-R\d+)",', re.search(r'const REQS = (\[\[.*?\]\]);', h, re.S).group(1))
if len(_ids) != len(set(_ids)): sys.exit(f"duplicate requirement ids: {sorted(i for i in set(_ids) if _ids.count(i) > 1)}")  # D-OG15
# footer and identity
h = once(h, "<h3>Transparency</h3><p>Built by the Data Management Lead, Office of the Chief Data Officer, with Claude (an AI assistant) doing the harvesting, matching and page build under a person's direction.", "<h3>Transparency</h3><p>An open-source public good, built in the open and open to everyone's contributions: corrections, sources and code are all welcome through GitHub. AI (Claude) helps with harvesting, matching and building; every change is checked and reviewed in public.", "footer: no affiliation, no individual")  # D-OG9, D-OG14  # D-OG9: the footer names no employer or government body
h = once(h, "It isn't an official list of government, and no body named here has endorsed it.", "It isn't an official government list, it isn't affiliated with any public body, and no body named here has endorsed it.", "footer disclaimer")
_foot = re.search(r'<footer class="colo".*?</footer>', h, re.S).group(0); _foot = re.sub(r"<svg.*?</svg>", "", _foot, flags=re.S)
_aff = re.findall(r"Directorate|Data Management|Cabinet Office|Department for|Ministry|DSIT|DCMS|\bGDS\b|Government Digital Service|Civil Service|HM Government|Crown copyright", _foot)
if _aff: sys.exit(f"footer names an affiliation: {_aff}")
_NAMES = {'fcd2b45b8eda145e', 'd24e913a4107af87'}  # D-OG14: fingerprints of an individual's name, so the check needs no name in the code
_ind = [w for w in re.findall(r"[A-Za-z]+", re.sub(r"<[^>]+>", " ", _foot)) if hashlib.sha256(w.lower().encode()).hexdigest()[:16] in _NAMES] + re.findall(r"Data Management Lead|a person's direction", _foot)
if _ind: sys.exit(f"footer names an individual: {_ind}")
h = once(h, 'Version <span class="mono">0.2.2</span>', f'Version <span class="mono">{VER}</span>', "version")
bc = io.BytesIO(); barcode.get("code128", f"OGUK-{VER}", writer=SVGWriter()).write(bc, {"module_height": 9.0, "font_size": 6, "text_distance": 3, "quiet_zone": 2}); bsvg = bc.getvalue().decode()
bsvg = bsvg[bsvg.index("<svg"):]
mbc = re.search(r'<span class="bc">(<svg.*?</svg>)</span>', h, re.S); h = h[:mbc.start(1)] + bsvg.replace("<svg ", '<svg aria-hidden="true" ', 1) + h[mbc.end(1):]
h = h.replace('"dct:modified": "2026-11-14"', '"dct:modified": "2026-11-22"', 1)
h = once(h, '{"@type": "dcat:Distribution", "dct:title": "Machinery of government changes"', '{"@type": "dcat:Distribution", "dct:title": "Who answers: accountability, money and ownership", "dcat:mediaType": "application/json", "dcat:downloadURL": "accountability.json"}, {"@type": "dcat:Distribution", "dct:title": "Accountability links (CSV)", "dcat:mediaType": "text/csv", "dcat:downloadURL": "edges.csv"}, {"@type": "dcat:Distribution", "dct:title": "Accountable owner of each body (CSV)", "dcat:mediaType": "text/csv", "dcat:downloadURL": "accountable-owner.csv"}, {"@type": "dcat:Distribution", "dct:title": "Public bodies by nation and branch of the state", "dcat:mediaType": "application/json", "dcat:downloadURL": "nations.json"}, {"@type": "dcat:Distribution", "dct:title": "Identifier concordance (CSV)", "dcat:mediaType": "text/csv", "dcat:downloadURL": "concordance.csv"}, {"@type": "dcat:Distribution", "dct:title": "PFI and PF2 contracts (CSV)", "dcat:mediaType": "text/csv", "dcat:downloadURL": "ppp.csv"}, {"@type": "dcat:Distribution", "dct:title": "Machinery of government changes"', "dcat")

# repository release: internal material stays in the repository (standing rule), contact via the GitHub issue form, QR to the site
h = once(h, '<div class="card" id="s-defects">', '<div class="card" id="s-defects" hidden>', "defects internal")
h = once(h, '$("#introTabs").innerHTML = T.map(', '$("#introTabs").innerHTML = T.filter(x => x[0] !== "The case against").map(', "case against tab")
h = once(h, '$("#introPanels").innerHTML = T.map(', '$("#introPanels").innerHTML = T.filter(x => x[0] !== "The case against").map(', "case against panel")
h = once(h, 'if (!(db && myId)) { out.textContent = "Sending isn\'t available in this view."; return; }', 'if (!(db && myId)) { out.innerHTML = \'Sending isn\\\'t available here. Please use the <a href="https://github.com/cyberdudeuk/opengovernment-uk/issues/new?template=feedback.yml" rel="noopener" target="_blank">feedback form on GitHub</a>, without names, email addresses or phone numbers.\'; return; }', "feedback fallback")
qi = io.BytesIO(); qrcode.make("https://cyberdudeuk.github.io/opengovernment-uk/", image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2).save(qi); qsvg = qi.getvalue().decode(); qsvg = qsvg[qsvg.index("<svg"):].replace("<svg ", '<svg role="img" aria-label="QR code: https://cyberdudeuk.github.io/opengovernment-uk/" width="22mm" height="22mm" ', 1)
mq = re.search(r'<span class="qr">(<svg.*?</svg>)</span>', h, re.S); h = h[:mq.start(1)] + qsvg + h[mq.end(1):]
h = once(h, 'Version <span class="mono">{VER}</span>'.replace("{VER}", VER), 'Version <span class="mono">' + VER + '</span>. Source and issues: <a href="https://github.com/cyberdudeuk/opengovernment-uk" rel="noopener" target="_blank">github.com/cyberdudeuk/opengovernment-uk</a>', "repo link")
for bad in ("Office of the Chief Data Officer", "OCDO "):
    if bad in h: sys.exit(f"forbidden wording still present: {bad!r}")
if re.search(r"[\w.+-]+@(?!media)[\w-]+\.(?:gov|org|com|uk|net)\b", h): sys.exit("an email address is present")
(OUT / "index.html").write_text(h)
# served feed files (same content the page offers as downloads)
(OUT / "accountability.json").write_text(json.dumps(ACC, ensure_ascii=False, separators=(",", ":")))
for f in ("edges.csv", "accountable-owner.csv"): (OUT / f).write_text((ROOT / "data" / f).read_text())
with open(OUT / "ppp.csv", "w", newline="") as f:  # same columns as the page's own download
    w = csv.writer(f); w.writerow(["hmt_project_id", "project", "status", "sector", "procuring_authority_id", "procuring_authority", "department_id", "department", "project_company", "company_number", "equity_holders", "individuals_not_named", "capital_gbp_m", "unitary_charge_2025_26_gbp_m", "contract_end", "esa_balance_sheet"])
    for p in PPP: w.writerow([p[0], p[1], p[2], p[3], p[4] or "", p[5], p[6] or "", p[7], p[8], p[9], "; ".join(f"{a} {b}" for a, b in p[10]), p[11], p[12], p[13], p[14], p[15]])
print(VER, "index.html", len(h), "accountability.json", len(acc_json), "sha", hashlib.sha256(h.encode()).hexdigest()[:16])
