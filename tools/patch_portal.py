"""Build OpenGovernment UK 0.3.0 from the published 0.2.2 page plus the accountability tree.
Every textual change is an exact replacement that must match once: if the base page changes, this fails loudly."""
import collections, csv, hashlib, json, pathlib, re, subprocess, sys, io
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
_CL = json.loads((ROOT / "data" / "classification.json").read_text())  # tools/classify.py: purpose, activity and type of body (purpose and activity MODELLED)
ACC["cl"] = {k: [v["purpose"], v["activity"], v["btype"], v["reach"]] for k, v in _CL["bodies"].items()}
_SA = json.loads((ROOT / "data" / "same-as.json").read_text())  # tools/sameas.py: one record per body
ACC["orgid"] = json.loads((ROOT / "data" / "org-id.json").read_text())  # tools/sqlite_export.py: org-id.guide identifiers (GB-COH, GB-CHC)
_INS = json.loads((ROOT / "data" / "instruments.json").read_text())  # tools/instruments.py: rules that apply, what each body issues, legislation naming it
ACC["ins"] = _INS["bodies"]; ACC["insr"] = _INS["rules"]
_REL = json.loads((ROOT / "data" / "relations.json").read_text())  # tools/relations.py: treaties and agreements by UK body
_RB = collections.defaultdict(list)
for _x in _REL["treaties"]:
    for _u in _x["uk"]: _RB[_u].append([_x["title"], _x["url"], _x["date"], "treaty"])
for _x in _REL["agreements"]:
    for _u in _x["uk"]: _RB[_u].append([_x["title"], _x["url"], _x["date"], _x["form"]])
ACC["relb"] = {k: {"n": len(v), "top": sorted(v, key=lambda z: z[2], reverse=True)[:6]} for k, v in _RB.items()}
ACC["web"] = json.loads((ROOT / "data" / "websites.json").read_text())  # tools/websites.py: id -> [own website, source]
ACC["sa"] = {c: g["members"] for c, g in _SA["groups"].items()}; ACC["sar"] = {c: g["rules"] for c, g in _SA["groups"].items()}
ACC["clm"] = {"purpose": {x["key"]: [x["label"], x["explain"]] for x in _CL["meta"]["purposes"]}, "activity": {x["key"]: [x["label"], x["explain"]] for x in _CL["meta"]["activities"]},
              "btype": {x["key"]: [x["label"], x["explain"]] for x in _CL["meta"]["btypes"]},
              "reach": {"local": ["A local area", "Works in one council area or a few."], "one": ["One nation", "Works across one of England, Scotland, Wales or Northern Ireland."], "several": ["Several nations", "Works in two or three of the four nations."], "uk": ["The whole UK", "Works across all four nations."], "outside": ["Outside the UK", "A territory or Crown Dependency, or one of its bodies."], "unstated": ["Not stated", "The sources don't say where it works yet."]}}
# Facts and figures: every number below is counted from the published data at build time (classification facets are modelled)
def _volumetrics():
    C = collections.Counter
    sa = json.loads((ROOT / "data/same-as.json").read_text())["groups"]; folded = {m for g in sa.values() for m in g["members"]}
    reg = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))["r"]
    opn = [r for r in reg if r[4] and r[0] not in folded]
    cl = _CL["bodies"]; web = json.loads((ROOT / "data/websites.json").read_text())
    lab = lambda facet, k: ACC["clm"][facet].get(k, [k])[0]
    facet = lambda f, i: C(lab(f, cl[r[0]][f]) for r in opn if r[0] in cl).most_common()
    ids = C(k for r in opn for k in r[10] if k not in ("ons_name", "govuk"))
    natc = C(c for r in opn for c in (ACC["nat"].get(r[0]) or ["unstated"]))
    ter = json.loads((ROOT / "data/territories.json").read_text())["bodies"]
    natc.update(b["group"] for b in ter)  # the territories' own bodies count with their group
    intl = json.loads((ROOT / "data/international.json").read_text())
    nat = json.loads((ROOT / "data/nations.json").read_text())["nations"]
    corp = json.loads((ROOT / "data/corporations.json").read_text())["trees"]
    dec = json.loads((ROOT / "sources/evidence/reconciliation-decisions.json").read_text())
    bods = json.loads((ROOT / "docs/bods-0.4.json").read_text())
    own = sum(1 for r in opn if r[0] in web and web[r[0]][1] != "GOV.UK page"); gov = sum(1 for r in opn if r[0] in web and web[r[0]][1] == "GOV.UK page")
    return {"records": len(reg), "open": len(opn), "folded": len(folded), "groups": len(sa),
            "type": facet("btype", 0), "purpose": facet("purpose", 0), "activity": facet("activity", 0), "reach": facet("reach", 0),
            "nation": natc.most_common(), "ids": ids.most_common(),
            "web": {"own": own, "govuk": gov, "none": len(opn) - own - gov},
            "branches": {k: v["counts"] for k, v in nat.items()},
            "territories": {"bodies": len(ter), "jurisdictions": len({b["j"] for b in ter}), "constitutional": sum(1 for b in ter if b.get("constitutional")), "by_branch": C(b["branch"] for b in ter).most_common()},
            "intl": {"bodies": len(intl["bodies"]), "leads": len({x["id"] for b in intl["bodies"] for x in b["lead"]}), "to_confirm": len(intl["to_confirm"])},
            "corp": {"trees": len(corp), "by_kind": C(t["kind"] for t in corp).most_common()},
            "recon": {"names": len(dec["names"]), "chains": len(dec["chains"]), "left": 0},
            "bods": {"statements": len(bods), "by_type": C(x.get("recordType", "?") for x in bods).most_common()}}

_LG = json.loads((ROOT / "data" / "local-government.json").read_text())
ACC["vol"] = _volumetrics()  # tools/localgov.py: English Devolution Act 2026, current and planned
ACC["lg"] = {k: v for k, v in _LG.items() if k not in ("two_tier_counties", "missing")}
ACC["corp"] = json.loads((ROOT / "data" / "corporations.json").read_text())  # tools/corporations.py: one family tree per trading fund or public corporation
acc_json = json.dumps(ACC, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

# ---------- data block edits ----------
m = re.search(r'(<script[^>]*id="data"[^>]*>)(.*?)(</script>)', h, re.S); D = json.loads(m.group(2))
D["v"] = VER; D["built"] = T["built"]
_DEC = json.loads((ROOT / "sources/evidence/reconciliation-decisions.json").read_text())["names"]  # decided name matches leave the queue
_DONE = {(d["id"], d["ons"]) for d in _DEC}
if not all(d.get("evidence") for d in _DEC): sys.exit("a name decision has no evidence")
D["q"] = [x for x in D["q"] if (x["id"], x["ons"]) not in _DONE]
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
c["consumers"] += [{"app": "dcat-ap-uk", "holds_now": "publisher URIs", "reads": "id as dct:publisher, state.jsonld", "status": "proposed"}]
# Only apps with a live public portal AND a public repository are listed (checked 22 Nov 2026 against the account's repo
# list and each portal's address). Internal apps are not named on a public site (OG-D34).
PUBLIC_APPS = {
    "GitHub Repos Asset Catalogue": ("https://cyberdudeuk.github.io/github-repos-asset-catalogue/", "https://github.com/cyberdudeuk/github-repos-asset-catalogue"),
    "dcat-ap-uk": ("https://cyberdudeuk.github.io/dcat-ap-uk/", "https://github.com/cyberdudeuk/dcat-ap-uk"),
}
c["consumers"] = [dict(x, portal=PUBLIC_APPS[x["app"]][0], repo=PUBLIC_APPS[x["app"]][1]) for x in c["consumers"] if x["app"] in PUBLIC_APPS]
if {x["app"] for x in c["consumers"]} != set(PUBLIC_APPS): sys.exit(f"public consumer missing: {set(PUBLIC_APPS) - {x['app'] for x in c['consumers']}}")
data_json = json.dumps(D, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
h = h[:m.start(2)] + data_json + h[m.end(2):]
mf = re.search(r'(<script[^>]*id="files"[^>]*>)(.*?)(</script>)', h, re.S); F = json.loads(mf.group(2))
F["feed-contract.json"] = json.dumps(c, indent=1, ensure_ascii=False)  # D-OG6: the download is regenerated from the same contract as the page
h = h[:mf.start(2)] + json.dumps(F, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + h[mf.end(2):]

# ---------- page edits ----------
STD_OLD = 'const std = [["W3C Organization Ontology (ORG)","Records, sub-organisation links and identifiers in state.jsonld"],["W3C DCAT 3","The catalogue record"],["W3C CSVW","CSV metadata"],["W3C SKOS","Families and sectors"],["CURIE (W3C)","Every key, such as government-organisation:D303"],["ISO 17442 (LEI)","Legal entity identifiers, checked by their check digits (OG-06)"],["Open Government Licence 3.0","All files"],["GOV.UK guidance: Publish reference data for use across government","Owner and steward, one system of record, persistent identifiers, JSON first, versioned changes"],["WCAG 2.2 AA","This page: keyboard, contrast, focus, reduced motion"],["GDS Service Standard and Technology Code of Practice","Open code, open standards, reuse before building"]];'
STD_NEW = 'const std = [["Beneficial Ownership Data Standard (BODS) 0.4", "bods-0.4.json: every body, link and owner as BODS statements; checked against the official schema and Open Ownership\'s own checker (lib-cove-bods) on every build", "Followed", "https://standard.openownership.org/en/0.4.0/"], ["W3C Organization Ontology (ORG)", "state.jsonld: bodies, parent and sub-organisation links, identifiers; the ontology (ontology.ttl) extends it", "Followed", "https://www.w3.org/TR/vocab-org/"], ["W3C DCAT 3", "The catalogue record for the National Data Library and data.gov.uk, with every download listed", "Followed", "https://www.w3.org/TR/vocab-dcat-3/"], ["W3C CSV on the Web (CSVW)", "Column names, types and keys for the CSV files", "Followed", "https://www.w3.org/TR/tabular-metadata/"], ["W3C SKOS", "Families, sectors, accountability relations and back-office classes as concept schemes", "Followed", "https://www.w3.org/TR/skos-reference/"], ["W3C OWL 2 and RDF Turtle", "ontology.ttl, parsed on every build", "Followed", "https://www.w3.org/TR/owl2-overview/"], ["W3C JSON-LD 1.1", "state.jsonld, the catalogue and the documentation knowledge graph", "Followed", "https://www.w3.org/TR/json-ld11/"], ["W3C CURIE", "Every key, such as government-organisation:D303", "Followed", "https://www.w3.org/TR/curie/"], ["org-id.guide identifier schemes", "GB-GOVUK, GB-COH, GB-CHC, GB-SC, GB-NIC, GB-NHS and XI-LEI in the BODS file", "Followed", "https://org-id.guide/"], ["ISO 17442 Legal Entity Identifier (LEI)", "LEIs checked by their check digits", "Followed", "https://www.gleif.org/en/about-lei/iso-17442-the-lei-code-structure"], ["ISO 3166-2:GB", "Nation codes GB-ENG, GB-SCT, GB-WLS and GB-NIR alongside the short codes EN, SC, WA and NI in nations.json", "Followed", ""], ["ONS Geography codes (GSS)", "Councils placed in their nation by the code ONS gives them (E, S, W or N)", "Followed", "https://geoportal.statistics.gov.uk/"], ["UN Classification of the Functions of Government (COFOG)", "What each body does, in ten plain-English groups mapped to COFOG divisions (worked out, not official)", "Partly followed", "https://unstats.un.org/unsd/classifications/Family/Detail/4"], ["European System of Accounts (ESA 2010) sectors", "ONS sector and code for each classified body", "Followed", "https://ec.europa.eu/eurostat/web/esa-2010"], ["IETF BCP 47 language tags", "Names in Welsh (cy), Scottish Gaelic (gd), Irish (ga) and Scots (sco) marked so screen readers say them correctly", "Followed", "https://www.rfc-editor.org/info/bcp47"], ["legislation.gov.uk URIs", "Links to the Acts that set up each nation\'s parliament, government and courts, and to founding Acts", "Followed", "https://www.legislation.gov.uk/developer/uris"], ["Wikidata identifiers", "Links to Wikidata, used as corroborating evidence only", "Followed", "https://www.wikidata.org/wiki/Wikidata:Main_Page"], ["WCAG 2.2 AA", "Every page: keyboard use, contrast, focus, language of parts, reduced motion", "Followed", "https://www.w3.org/TR/WCAG22/"], ["W3C Design Tokens Format (Community Group draft)", "tokens.json: every colour, type size, space, corner, shadow, motion and breakpoint, reusable by other apps; og.css is generated from it", "Followed", "https://tr.designtokens.org/format/"], ["SIL Open Font License 1.1", "Atkinson Hyperlegible Next and IBM Plex Mono, served from this site (no third-party font requests)", "Followed", "https://openfontlicense.org/"], ["GDS Service Standard, point 12: make new source code open", "All code public on GitHub", "Followed", "https://www.gov.uk/service-manual/service-standard/point-12-make-new-source-code-open"], ["GDS Service Standard, point 13: use common standards, components and patterns", "Open standards above; reuse of BODS, ORG and DCAT rather than new formats", "Followed", "https://www.gov.uk/service-manual/service-standard/point-13-use-common-standards-components-patterns"], ["Technology Code of Practice: be open and use open source", "Open code, open data and open contribution", "Followed", "https://www.gov.uk/guidance/be-open-and-use-open-source"], ["Technology Code of Practice: make use of open standards", "Open formats only; no proprietary file formats", "Followed", "https://www.gov.uk/guidance/make-use-of-open-standards"], ["Licences: MIT (code), CC BY 4.0 (documentation), Open Government Licence 3.0 (data)", "Each file carries the licence for its kind", "Followed", "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"], ["Open Contracting Data Standard (OCDS)", "Joining public contracts from Find a Tender to the bodies that buy", "Planned", "https://standard.open-contracting.org/latest/en/"], ["FollowTheMoney", "An export that investigative tools can load directly", "Planned", "https://followthemoney.tech/"], ["360Giving", "Grants made by public bodies, to show who funds whom", "Planned", "https://standard.threesixtygiving.org/"]];'  # OG-D35: the list now names every standard in use, its status and a deep link

files_end = re.search(r'<script[^>]*id="files"[^>]*>.*?</script>', h, re.S).end()
h = h[:files_end] + f'\n<script id="tree" type="application/json">{acc_json}</script>' + h[files_end:]
h = once(h, STD_OLD, STD_NEW, "standards list")
h = once(h, '$("#stdRows").innerHTML = std.map(s => `<tr><td>${esc(s[0])}</td><td>${esc(s[1])}</td></tr>`).join("");',
         '$("#stdRows").innerHTML = std.map(s => `<tr><td>${s[3] ? `<a href="${esc(s[3])}" rel="noopener">${esc(s[0])}</a>` : esc(s[0])}</td><td>${esc(s[1])}</td><td>${esc(s[2])}</td></tr>`).join("");', "standards rows")
h = once(h, '<th scope="col">Standard</th><th scope="col">Where it applies</th></tr>', '<th scope="col">Standard</th><th scope="col">Where it applies</th><th scope="col">Status</th></tr>', "standards head")
h = once(h, '<div class="card" id="s-mog">', (TOOLS / "localgov-view.html").read_text() + '<div class="card" id="s-mog">', "localgov")  # most important first: what is changing now
h = once(h, '<option value="fam">Family</option><option value="nat">Nation</option><option value="sec">ONS sector</option></select>', '<option value="btype">Type of body</option><option value="purpose">What it is for</option><option value="activity">What it does</option><option value="nation">Nation</option><option value="reach">Geography</option><option value="fam">Source family</option><option value="sec">ONS sector</option></select>', "register group options")
h = once(h, '<th scope="col"><button class="sortbtn" data-sort="fam">Family and kind</button></th><th scope="col">Nation</th>', '<th scope="col"><button class="sortbtn" data-sort="fam">Type</button></th><th scope="col">What it is for and does</th><th scope="col">Nation and geography</th>', "register columns")
h = h.replace('const g = {fam:r => r.fam, nat:r => (r.nat.map(n => NAT[n]).join(", ") || "Not stated"), sec:r => r.ons.sector || "Not classified by ONS"}[FILTER.group];', "const g = REG_GROUP[FILTER.group];")
h = once(h, 'const gf = FILTER.group ? {fam:r => r.fam, nat:r => (r.nat.map(n => NAT[n]).join(", ") || "Not stated"), sec:r => r.ons.sector || "Not classified by ONS"}[FILTER.group] : null;', "const gf = FILTER.group ? REG_GROUP[FILTER.group] : null;", "register group fn")
h = once(h, 'head = `<tr><th colspan="5" scope="colgroup"', 'head = `<tr><th colspan="6" scope="colgroup"', "register group colspan")
h = once(h, '${r.web ? `<dt>Website</dt><dd><a href="${esc(r.web)}" rel="noopener" target="_blank">${esc(r.web)}</a></dd>` : ""}', '${profWeb(r)}', "profile website from the one combined table")
h = once(h, '$("#exIntro").textContent = `${D.q.length} pairs need someone who knows the bodies.', '$("#exIntro").textContent = D.q.length === 0 ? "Nothing is left for a person. Every pair was decided from the body\'s own page, its founding law or an official archive record, and each decision is kept with its evidence in sources/evidence/reconciliation-decisions.json." : `${D.q.length} pairs need someone who knows the bodies.', "empty review queue says why")
h = once(h, '</td><td>${esc(r.fam)}<br><span class="muted">${esc(r.kind)}</span></td><td>${esc(r.nat.map(x => NAT[x]).join(", ") || "Not stated")}</td>', '${siteLink(r.id)}${regAlso(r.id)}</td><td>${regType(r)}</td><td>${regWhat(r.id)}</td><td>${regWhere(r.id)}</td>', "register row cells")
h = once(h, "function filtered(){ return R.filter(r => matches(r, FILTER.q)", "function filtered(){ return R.filter(r => !SA_FOLDED.has(r.id) && matches(r, FILTER.q)", "register: one record per body")
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
if "sr-only" in js and ".sr-only{" not in h: sys.exit("OG-D40: screen-reader-only text used but .sr-only is not defined, so it would show on screen")
h = once(h, "home(); explore(); setupRegister(); renderRegister(); reconcile(); changes(); dataView(); quality(); help(); product(); ask();\nroute(); selfChecks();",
         "home(); explore(); setupRegister(); renderRegister(); reconcile(); changes(); whoAnswers(); dataView(); quality(); help(); product(); ask(); figures();\nroute(); selfChecks(); treeSelfChecks();", "start")
h = once(h, '<div class="card" id="s-files"><h2>Download the register</h2>', '<div class="card" id="s-query"><span class="eyebrow">Query it yourself</span><h2>Ask the data your own questions</h2><p>Every table in one SQLite file: bodies with their type, purpose, activity, nations, website and identifiers; who answers to whom; the accountable owner; public-private partnerships; the concordance of codes; the territories\' own bodies; and the UK in international bodies. Open it in <a href="https://lite.datasette.io/?url=https://cyberdudeuk.github.io/opengovernment-uk/opengovernment-uk.db" rel="noopener" target="_blank">Datasette Lite<span class="sr-only"> (opens in a new tab)</span></a> to filter, facet and run SQL in your browser, with nothing to install, or <a href="opengovernment-uk.db" download>download the file</a> for any SQLite tool. The approach follows Open Ownership\'s own data analysis tools.</p></div>\n   <div class="card" id="s-files"><h2>Download the register</h2>', "query panel")
h = once(h, '<div class="stats" id="homeStats" aria-label="The register in numbers"></div>', '<div class="stats" id="homeStats" aria-label="The register in numbers"></div>\n   <div class="card" id="s-figures"><span class="eyebrow">Facts and figures</span><h2>The state in numbers</h2><p class="muted" id="figLede"></p><div class="stats" id="figStats" aria-label="Facts and figures"></div><div class="figgrid" id="figBars"></div></div>', "facts and figures panel")
h = once(h, "const G = [[", "const G = [...TREE_TERMS, [", "glossary")
h = once(h, "const DEFECTS = [[", (TOOLS / "tree-defects.js").read_text() + "const DEFECTS = [...TREE_DEFECTS, [", "defects")  # D-OG7: must precede DEFECTS (temporal dead zone)
h = once(h, '$("#relList").innerHTML = `<li><b>0.2.2</b>', '$("#relList").innerHTML = `<li><b>0.3.0</b>, 22 November 2026: who answers for each body. Accountability, money and ownership from the Estimates and Accounts Orders (UK and Northern Ireland), the Whole of Government Accounts order and annex, ONS, the Public Bodies Directory, Companies House controllers, GLEIF and HM Treasury\'s PFI register, every link traced to a fingerprinted source; trading funds, public corporations and PPPs; the register becomes the single source for any app that reuses it.</li><li><b>0.2.2</b>', "release")
h = once(h, 'const SUGG = ["Which bodies does the Ministry of Defence have under it?",', 'const SUGG = ["Who does the Met Office answer to in the end?", "Which PFI contracts does the Department of Health and Social Care pay for?", "Which bodies does the Ministry of Defence have under it?",', "suggest")
WHO = '{name:"who_answers", description:"For one exact record id: the chain of bodies it answers to, each step with its source and where in the source; who it answers to in the end; its government funding, Whole of Government Accounts status and PFI contracts.", inputSchema:{type:"object", properties:{id:{type:"string"}}, required:["id"]}, execute: ({id}) => { if (!ACC.ch[id]) throw new Error("no accountability data for that id"); used.add(id); const c = CHAIN(id); const pp = ACC.ppp.filter(p => p[4] === id || p[6] === id); return {body: BY[id].name, chain: c.path.map(e => ({to: BY[e.p] ? BY[e.p].name : e.p, relation: RELNAME[e.rel], source: SRC(e.src).name, where: e.ref})), answers_to: c.ans, government_funding: ACC.m[id] ? {year: ACC.m[id][0], gov_funded_gbp: ACC.m[id][1], tme_gbp: ACC.m[id][3]} : null, wga: ACC.w[id] ? ACC.w[id][0] : null, pfi: pp.length ? {contracts: pp.length, capital_gbp_m: Math.round(pp.reduce((s, p) => s + (p[12] || 0), 0)), charges_2025_26_gbp_m: Math.round(pp.reduce((s, p) => s + (p[13] || 0), 0))} : null}; }},\n                     '
h = once(h, '{name:"count", description:"Count open or all records', WHO + '{name:"count", description:"Count open or all records', "ask tool")
h = once(h, "Families in the register: ${D.fam.join(\", \")}.", "Families in the register: ${D.fam.join(\", \")}. For who a body answers to, who funds it or who owns it, find its id with search_register and then call who_answers; quote the sources it gives.", "ask prompt")
h = once(h, 'function fallback(q, out, used){ const rs = searchRecords(q, 8); rs.forEach(r => used.add(r.id)); $(".ans", out).innerHTML = rs.length ? `These records match your question. Open one to see its identifiers, parents and lineage.`',
         'function fallback(q, out, used){ const rs = searchRecords(q, 8); rs.forEach(r => used.add(r.id)); if (rs.length && /who (answers|owns|funds|pays|sponsors)|answer to|accountab|ultimate|owner|PFI|fund/i.test(q) && ACC.ch[rs[0].id]) { $(".ans", out).innerHTML = chainHTML(rs[0].id) + factsHTML(rs[0].id); return; } $(".ans", out).innerHTML = rs.length ? `These records match your question. Open one to see its identifiers, parents and lineage.`', "fallback")
h = once(h, '["ask","Ask a question","Answers drawn only from the register.","ask"]', '["crown","Who answers","Trace any body to whoever answers for it, with the money and the owners.","tree"],["ask","Ask a question","Answers drawn only from the register.","ask"]', "home tile")
h = once(h, '<a class="btn ghost" href="#register"><svg aria-hidden="true"><use href="#i-list"/></svg>Search the register</a>', '<a class="btn ghost" href="#register"><svg aria-hidden="true"><use href="#i-list"/></svg>Search the register</a><a class="btn ghost" href="#tree"><svg aria-hidden="true"><use href="#i-crown"/></svg>Who answers</a><a class="btn ghost" href="nations.html"><svg aria-hidden="true"><use href="#i-list"/></svg>Nation by nation</a><a class="btn ghost" href="navigator.html"><svg aria-hidden="true"><use href="#i-list"/></svg>Documentation</a>', "hero")
h = once(h, '["Next","ANA, GovCRM, MEASR and the MoG canon read the feed","must"]', '["Now","Public apps read the feed: the GitHub Repos Asset Catalogue and dcat-ap-uk","must"],["Next","Any other open project can reuse the feed: tell us and we will list it once it has a public site and repository","should"],["Next","Resolve the names left for a person, starting with classes of body in the Orders","must"],["Later","Scottish Government directory and UKGI portfolio when they can be read","should"]', "roadmap")
h = once(h, 'const REQS = [', 'const REQS = [["OG-R21","Who answers for each body, traced to the law and the sponsor","Must","Done","Estimates and Accounts Orders, PBD, ONS; checks AT-chain_shape, AT-known_answers"],["OG-R22","Follow the money: government funding and PFI charges","Must","Done","PBD 2023/24; HMT PFI register 2025"],["OG-R23","Ownership: Companies House controllers, GLEIF parents, PFI investors","Must","Done","No natural person named; check AT-no_persons"],["OG-R24","Trading funds, public corporations and public-private partnerships","Must","Done","legislation.gov.uk orders; ONS sectors; 654 contracts"],["OG-R25","Lineage to a fingerprinted source for every link","Must","Done","Provenance ledger; check AT-hashes, AT-digest"],["OG-R26","Single source of truth for the estate\'s apps","Must","In progress","Two public apps reuse it; others welcome"],["OG-R38","Each nation\'s register: its public bodies by branch of the state, with each branch\'s apex from its founding legislation","Must","Done","nations.html; checks for known answers and apexes"],', "reqs")
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
# ---------- design system (OG-D42): shared tokens and stylesheet, self-hosted fonts, tokenised page CSS ----------
sys.path.insert(0, str(TOOLS)); import design  # noqa: E402
h = re.sub(r'<link rel="preconnect" href="https://fonts\.(?:googleapis|gstatic)\.com"[^>]*>\s*', "", h)
h = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\s*', "", h)
h = h.replace("background:#fff;color:#000}", "background:var(--og-bg);color:var(--og-ink)}", 1).replace("footer .codes svg{background:#fff", "footer .codes svg{background:white", 1)  # codes stay on white so they scan
h = re.sub(r"<style>(.*?)</style>", lambda m: "<style>" + design.layer(design.tokenise(m.group(1))) + "</style>", h, flags=re.S)
h = re.sub(r'style="([^"]*)"', lambda m: 'style="' + design.tokenise(m.group(1)) + '"', h)
h = once(h, "</head>", '<link rel="stylesheet" href="assets/og.css">\n</head>', "design stylesheet")
h = h.replace("Fonts: Fraunces, Inter and IBM Plex Mono, from Google Fonts.", 'Fonts: Atkinson Hyperlegible Next and IBM Plex Mono (SIL Open Font License), served from this site. <a href="design-system.html">Design system</a>.')
if "fonts.googleapis" in h or "Fraunces" in h.split("<script")[0]: sys.exit("OG-D42: a third-party font is still referenced")
(OUT / "index.html").write_text(h)
# served feed files (same content the page offers as downloads)
(OUT / "accountability.json").write_text(json.dumps(ACC, ensure_ascii=False, separators=(",", ":")))
for f in ("edges.csv", "accountable-owner.csv"): (OUT / f).write_text((ROOT / "data" / f).read_text())
with open(OUT / "ppp.csv", "w", newline="") as f:  # same columns as the page's own download
    w = csv.writer(f); w.writerow(["hmt_project_id", "project", "status", "sector", "procuring_authority_id", "procuring_authority", "department_id", "department", "project_company", "company_number", "equity_holders", "individuals_not_named", "capital_gbp_m", "unitary_charge_2025_26_gbp_m", "contract_end", "esa_balance_sheet"])
    for p in PPP: w.writerow([p[0], p[1], p[2], p[3], p[4] or "", p[5], p[6] or "", p[7], p[8], p[9], "; ".join(f"{a} {b}" for a, b in p[10]), p[11], p[12], p[13], p[14], p[15]])
print(VER, "index.html", len(h), "accountability.json", len(acc_json), "sha", hashlib.sha256(h.encode()).hexdigest()[:16])
