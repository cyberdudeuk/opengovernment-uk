"""Per-nation registers: every public body associated with each UK nation, broken down by
branch of the state (legislature, executive, judiciary) and tier.
Nation comes from the register's own stated code, else from where the accountability chain ends
(a devolved legislature). Nothing is inferred from names. Writes data/nations.json and docs/nations.html."""
import collections, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
NATIONS = {"EN": "England", "SC": "Scotland", "WA": "Wales", "NI": "Northern Ireland",
           "UK": "UK-wide (stated)", "GB": "UK Government, extent not stated", "OT": "Overseas Territories", "CD": "Crown Dependencies"}
FROM_ROOT = {"the Scottish Parliament": "SC", "the Senedd": "WA", "the Northern Ireland Assembly": "NI"}
# Explicit names only: the bare word "parliamentary" also matches boundary commissions and panels that sit in the executive (D-OG16).
LEGIS_NAME = re.compile(r"^(houses? of parliament|house of commons|house of lords( commission)?|scottish parliament|senedd|welsh parliament|national assembly for wales|northern ireland assembly)\b|scottish parliamentary corporate body|independent parliamentary standards authority|commonwealth parliamentary association|parliamentary and health service ombudsman|^(senedd|assembly) commission|electoral commission|national audit office|audit scotland|audit wales|wales audit office|northern ireland audit office", re.I)
L = "https://www.legislation.gov.uk/"
# Apex of each branch, from the founding legislation (each link checked against the Act's text on legislation.gov.uk, 22 Nov 2026).
# These are stated, not register records: the register does not yet hold the legislatures or Scotland's supreme courts.
UK_APEX = {"legislature": [("UK Parliament: House of Commons and House of Lords", "No founding Act; the Parliament Act 1911 sets relations between the Houses", L + "ukpga/Geo5/1-2/13/section/1")],
           "executive": [("UK Government: the Prime Minister and ministers of the Crown", "No founding Act; ministers act under the Crown and statute", "")],
           "judiciary": [("Supreme Court of the United Kingdom", "Constitutional Reform Act 2005, s.23", L + "ukpga/2005/4/section/23")]}
EW_COURTS = ("Senior Courts of England and Wales: Court of Appeal, High Court and Crown Court", "Senior Courts Act 1981, s.1", L + "ukpga/1981/54/section/1")
APEX = {"EN": {"legislature": [("No devolved legislature: the UK Parliament legislates for England", "", "")], "executive": [("No devolved government: the UK Government governs England", "", "")], "judiciary": [EW_COURTS]},
        "SC": {"legislature": [("Scottish Parliament", "Scotland Act 1998, s.1", L + "ukpga/1998/46/section/1")],
               "executive": [("Scottish Government (the Scottish Administration)", "Scotland Act 1998, s.44", L + "ukpga/1998/46/section/44")],
               "judiciary": [("Court of Session", "Court of Session Act 1988, s.1", L + "ukpga/1988/36/section/1"), ("The Lord President, Head of the Scottish Judiciary", "Judiciary and Courts (Scotland) Act 2008, s.2", L + "asp/2008/6/section/2")]},
        "WA": {"legislature": [("Senedd Cymru (Welsh Parliament)", "Government of Wales Act 2006, s.1; renamed by the Senedd and Elections (Wales) Act 2020, s.2", L + "ukpga/2006/32/section/1")],
               "executive": [("Welsh Government", "Government of Wales Act 2006, s.45", L + "ukpga/2006/32/section/45")],
               "judiciary": [("Shared with England: " + EW_COURTS[0], EW_COURTS[1], EW_COURTS[2])]},
        "NI": {"legislature": [("Northern Ireland Assembly", "Northern Ireland Act 1998, Part IV", L + "ukpga/1998/47/part/IV")],
               "executive": [("Northern Ireland Executive (the Executive Committee)", "Northern Ireland Act 1998, s.20", L + "ukpga/1998/47/section/20")],
               "judiciary": [("Court of Judicature of Northern Ireland: Court of Appeal, High Court and Crown Court", "Judicature (Northern Ireland) Act 1978, s.1", L + "ukpga/1978/23/section/1")]},
        "GB": UK_APEX}
JUDIC_NAME = re.compile(r"\b(court|courts|tribunal|tribunals|judicial|judiciary|judges|sheriff principal|lord chief justice)\b", re.I)
COURT_ADMIN = re.compile(r"courts? (and|&) tribunals? service|courts service|tribunals service|judicial appointments|judicial office|judicial college|judicial conduct", re.I)

def court_administration_branch(name: str) -> tuple[str, str]:
    """Contested case: bodies that run or appoint to the courts but do not judge (HM Courts & Tribunals Service,
    Scottish Courts and Tribunals Service, Judicial Appointments Commission ...). Constitutionally they sit in the
    executive or are independent statutory bodies; functionally they serve the judiciary.
    Default chosen: count them under the judiciary, tier 'court administration and appointments', so a reader
    looking at a nation's justice system sees them; the tier label keeps them distinct from courts themselves."""
    return "judiciary", "Court administration and appointments"

def tier_of(t: str, fam: str, answerable: str) -> str:
    if fam == "Local authority" or t in {"Local Government", "Non-metropolitan district", "Unitary authority", "Metropolitan district", "London borough", "County council", "Combined authority"}:
        return "Local government"
    if fam == "NHS body" or "NHS" in answerable or t in {"NHS trust", "Integrated care board", "Health board", "Local health board", "Special health authority", "Health and social care trust", "Care trust", "Commissioning support unit", "NHS England region"}:
        return "Health service"
    if t in {"Ministerial department", "Non-ministerial department", "Devolved government", "UK nation"}:
        return "Government departments"
    if t in {"Public Non-Financial Corporations", "Public corporation"} or t.startswith("Public Other financial") or t in {"Public Financial Auxiliaries", "Public Pension Funds"}:
        return "Public corporations and financial bodies"
    return "Arm's-length bodies and other central bodies"

def branch_of(name: str, t: str, fam: str, answerable: str) -> tuple[str, str]:
    if COURT_ADMIN.search(name): return court_administration_branch(name)
    if t in {"Court", "Tribunal"} or JUDIC_NAME.search(name): return "judiciary", "Courts and tribunals"
    if LEGIS_NAME.search(name) or answerable == "Parliament directly (not a ministerial body)": return "legislature", "Legislatures and their bodies"
    return "executive", tier_of(t, fam, answerable)

def nations_of(code: str, answerable: str) -> tuple[list[str], str]:
    if code:
        found = [c for c in ("EN", "SC", "WA", "NI", "OT", "CD", "UK") if c in code]
        if found: return found, "stated by the register"
    if answerable in FROM_ROOT: return [FROM_ROOT[answerable]], "answers to that nation's legislature"
    if answerable.startswith("Parliament"): return ["GB"], "answers to the UK Parliament; extent not stated"
    return [], ""

def load():
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    chains = json.loads((ROOT / "data/tree.json").read_text())["chains"]
    ev = json.loads((ROOT / "data/nation-evidence.json").read_text())["bodies"]  # tools/nation_evidence.py
    return D, chains, ev

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nation_evidence as NE  # noqa: E402  council matching and ONS Welsh names, shared so the two never drift

LANGS_FOR = {"WA": ["cy"], "SC": ["gd", "sco"], "NI": ["ga", "sco"], "UK": ["cy", "gd", "ga", "sco"], "GB": ["cy", "gd", "ga", "sco"]}
def names_and_sites():
    """Official websites (Wikidata P856, current statements only), official names (P1448, and ONS Welsh names for
    councils), and community labels (Wikidata labels, shown as community translations, dropped when they just repeat
    the English name)."""
    w = json.loads((ROOT / "sources/evidence/wikidata-websites-names.json").read_text())
    site = {}
    for q, u in w["website"]: site.setdefault(q, u)
    off, lab = collections.defaultdict(dict), collections.defaultdict(dict)
    for q, lang, n in w["official_name"]: off[q].setdefault(lang, n)
    for q, lang, n in w["label"]: lab[q].setdefault(lang, n)
    return site, off, lab, NE.lad_index()
def to_hash(i): return "org-" + re.sub(r"[^A-Za-z0-9-]", "", i.replace(":", "--"))  # mirrors the portal's toHash

BASIS = {"chain": "answers to that nation's legislature", "ons-sponsor": "ONS records its sponsor", "own-site": "its own GOV.UK page says so",
         "register": "stated by the register", "ons-gss": "ONS local authority code", "statute": "the Act that founded it", "wikidata": "Wikidata jurisdiction",
         "pb-2020": "2020 public bodies compilation", "companies": "where it is registered"}

SA, SA_NAMES = {}, {}
_WP = ROOT / "data/websites.json"
WEB = json.loads(_WP.read_text()) if _WP.exists() else {}
JTIER = "The jurisdictions themselves"


def add_territories(out):
    """The Crown Dependencies' and Overseas Territories' own bodies (tools/territories.py), grouped by jurisdiction within each branch."""
    tp = ROOT / "data/territories.json"
    if not tp.exists(): return
    T = json.loads(tp.read_text())
    for g in ("OT", "CD"):  # the jurisdiction records themselves head each family tree
        ex = out[g]["branches"]["executive"]
        for tier in list(ex):
            if tier != JTIER: ex[JTIER] += ex.pop(tier)
    FKB = {"legislature": "territory", "judiciary": "judicial"}
    for b in T["bodies"]:
        s0 = b["srcs"][0]
        out[b["group"]]["branches"][b["branch"]][b["jurisdiction"]].append({
            "id": b["id"], "name": b["name"], "type": b["type"], "basis": {"founding order": "founding order", "official": "official website", "Wikidata": "Wikidata"}[s0["kind"]],
            "why": "; ".join(s["title"] for s in b["srcs"]), "url": s0["url"], "p": b["parent"], "answers_to": "", "h": "", "web": b["web"], "gov": "", "names": [], "nations": [],
            "pk": b["pk"], "rk": b["geography"], "fk": FKB.get(b["branch"], "unknown") if b["tk"] != "territory" else "territory", "ak": b["ak"], "tk": b["tk"],
            "j": b["jurisdiction"], "srcs": b["srcs"], "formerly": b.get("formerly"), "also": []})
    jm = T["meta"]["jurisdictions"]
    for g in ("OT", "CD"):
        out[g]["apex"] = {"judiciary": [{"name": "Judicial Committee of the Privy Council (final court of appeal)", "basis": "jcpc.uk", "url": "https://www.jcpc.uk/"}]}
        if g == "CD": out[g]["apex"]["executive"] = [{"name": "The Crown, through the Privy Council; the Ministry of Justice manages the UK's relationship", "basis": "GOV.UK", "url": "https://www.gov.uk/government/publications/crown-dependencies-jersey-guernsey-and-the-isle-of-man"}]
        out[g]["notes"] = [{"j": v["name"], "note": v["note"], "sources": v["note_sources"]} for v in jm.values() if v["group"] == g and v["note"]]
        out[g]["coverage"] = {"excluded": T["meta"]["excluded"], "blocked": T["meta"].get("blocked", ""), "not_covered": T["meta"]["not_covered"]}


def build(D, chains, ev):
    site, off, lab, lad = names_and_sites()
    cp = ROOT / "data/classification.json"  # tools/classify.py (it reads body-nations.json, which this writes: run nations, classify, nations)
    CL = json.loads(cp.read_text())["bodies"] if cp.exists() else {}
    out = {k: {"name": v, "branches": {"legislature": collections.defaultdict(list), "executive": collections.defaultdict(list), "judiciary": collections.defaultdict(list)}} for k, v in NATIONS.items()}
    unplaced = 0
    sa = json.loads((ROOT / "data/same-as.json").read_text())["groups"] if (ROOT / "data/same-as.json").exists() else {}  # tools/sameas.py: one record per body
    SA.clear(); SA.update({c: g["members"] for c, g in sa.items()}); SA_NAMES.clear(); SA_NAMES.update({k: n for g in sa.values() for k, n in g["names"].items()})
    folded = {m for g in sa.values() for m in g["members"]}
    for r in D["r"]:
        if not r[4] or r[0] in folded: continue  # open bodies only, once each (a folded record's sources show on its main record)
        ans = (chains.get(r[0]) or {}).get("answerable", "")
        e = ev.get(r[0]) or {}
        if e.get("nations"): codes, basis, why, url = e["nations"], BASIS[e["basis"]], e.get("why", ""), e.get("url", "")
        else:
            codes, basis = nations_of("", ans); why, url = basis, ""
        if not codes: unplaced += 1; continue
        br, tier = branch_of(r[1], r[3], D["fam"][r[2]], ans)
        path = (chains.get(r[0]) or {}).get("path") or []
        parent = path[0]["to"] if path else ""
        q, ids = r[10].get("wikidata"), r[10]
        langs = sorted({lg for c in codes for lg in LANGS_FOR.get(c, [])})
        nm = []
        ck = NE.council_key(r[1])
        if ck and ck in lad and lad[ck][2] and "cy" in langs: nm.append({"lang": "cy", "name": lad[ck][2], "src": "official (ONS)"})
        for lg in langs:
            if any(x["lang"] == lg for x in nm): continue
            if q and lg in off.get(q, {}) and NE.clean(off[q][lg]) == NE.clean(r[1]): continue
            if q and lg in off.get(q, {}): nm.append({"lang": lg, "name": off[q][lg], "src": "official name (Wikidata)"})
            elif q and lg in lab.get(q, {}) and NE.clean(lab[q][lg]) != NE.clean(r[1]): nm.append({"lang": lg, "name": lab[q][lg], "src": "community translation (Wikidata)"})
        govuk = f"https://www.gov.uk/government/organisations/{ids['govuk_slug']}" if ids.get("govuk_slug") else ""
        web = WEB.get(r[0], ["", ""])[0]  # tools/websites.py: the one combined website table every list uses
        if web.rstrip("/") == govuk.rstrip("/"): web = ""
        multi = [c for c in codes if c in ("EN", "SC", "WA", "NI")]
        for c in codes: out[c]["branches"][br][tier].append({"id": r[0], "name": r[1], "type": r[3], "basis": basis, "why": why, "url": url, "p": parent, "answers_to": ans,
                                                             "h": to_hash(r[0]), "web": web, "gov": govuk, "names": nm, "nations": codes if (len(multi) > 1 or "UK" in codes) else [],
                                                             "pk": (CL.get(r[0]) or {}).get("purpose", "unknown"), "rk": (CL.get(r[0]) or {}).get("reach_label", ""), "fk": (CL.get(r[0]) or {}).get("formed", "unknown"),
                                                             "ak": (CL.get(r[0]) or {}).get("activity", "unknown"), "tk": (CL.get(r[0]) or {}).get("btype", "central"), "also": [{"id": m, "name": SA_NAMES.get(m, m)} for m in SA.get(r[0], [])]})
    for c, n in out.items():
        n["apex"] = {br: [{"name": a, "basis": b, "url": u} for a, b, u in v] for br, v in APEX.get(c, {}).items()}
    add_territories(out)
    for c, n in out.items():
        n["uk_apex"] = {br: [{"name": a, "basis": b, "url": u} for a, b, u in v] for br, v in UK_APEX.items()} if c in ("EN", "SC", "WA", "NI") else {}
        for br in n["branches"]:
            n["branches"][br] = {k: sorted(v, key=lambda x: x["name"]) for k, v in sorted(n["branches"][br].items(), key=lambda kv: (kv[0] != JTIER, kv[0]))}
        n["counts"] = {br: sum(len(v) for v in n["branches"][br].values()) for br in n["branches"]}
    return out, unplaced

def check(out, unplaced, D):
    """Known answers, no double-counting within a nation, every open body placed or counted as unplaced."""
    p = []
    def where(name):
        return {(c, br) for c, n in out.items() for br, tiers in n["branches"].items() for v in tiers.values() for x in v if x["name"] == name}
    # Known answers must be FOUND: a known answer that silently matches nothing proves nothing (D-OG17).
    for name, want in [("The Scottish Government", ("SC", "executive")), ("Scottish Parliamentary Corporate Body", ("SC", "legislature")),
                       ("Northern Ireland Assembly Commission", ("NI", "legislature")), ("Welsh Government", ("WA", "executive")),
                       ("Scottish Courts and Tribunals Service", ("SC", "judiciary")), ("Supreme Court of the United Kingdom", ("UK", "judiciary")), ("HM Land Registry", ("WA", "executive")), ("Estyn", ("WA", "executive")),
                       ("Aberdeen City Council", ("SC", "executive")),
                       ("Houses of Parliament", ("GB", "legislature")), ("Parliamentary Boundary Commission for England", ("EN", "executive"))]:
        if want not in where(name): p.append(f"{name}: expected {want}, got {sorted(where(name))}")
    for c in ("EN", "SC", "WA", "NI", "GB"):
        for br in ("legislature", "executive", "judiciary"):
            if not out[c]["apex"].get(br): p.append(f"{c}: no apex for {br}")
            for a in out[c]["apex"].get(br, []):
                if a["url"] and not a["url"].startswith("https://www.legislation.gov.uk/"): p.append(f"{c}: apex link not to legislation.gov.uk")
    for c, n in out.items():
        ids = [x["id"] for tiers in n["branches"].values() for v in tiers.values() for x in v]
        if len(ids) != len(set(ids)): p.append(f"{c}: a body appears twice")
    placed = {x["id"] for n in out.values() for tiers in n["branches"].values() for v in tiers.values() for x in v}
    folded = {m for ms in SA.values() for m in ms}
    reg_placed = {i for i in placed if not i.startswith("terr:")}  # territory bodies come from their own sources, not the register
    if len(reg_placed) + unplaced + len(folded) != sum(1 for r in D["r"] if r[4]): p.append("open bodies not all accounted for (placed + unplaced + folded duplicates)")
    if folded & reg_placed: p.append("a folded duplicate is still listed separately")
    return p

PAGE = (pathlib.Path(__file__).resolve().parent / "nations-page.html").read_text()

if __name__ == "__main__":
    D, chains, ev = load(); out, unplaced = build(D, chains, ev)
    _orig = branch_of
    if "--negative" in sys.argv:  # break the judiciary rule: the known answers must catch it
        globals()["branch_of"] = lambda n, t, f, a: ("executive", "x")
        bad, _ = build(D, chains, ev); ok = bool(check(bad, _, D)); print("caught branch break" if ok else "MISSED branch break")
        globals()["branch_of"] = _orig; out2, u2 = build(D, chains, ev); out2["SC"]["apex"]["judiciary"] = []
        ok2 = bool(check(out2, u2, D)); print("caught missing apex" if ok2 else "MISSED missing apex"); sys.exit(0 if ok and ok2 else 1)
    probs = check(out, unplaced, D)
    def hidden_guard(page):  # OG-D59: a label hidden by script still shows if page CSS sets its display
        return [] if ".hidden=" not in page or "label[hidden]{display:none}" in page else ["filter labels are hidden by script but the page CSS would still show them (add label[hidden]{display:none})"]
    if hidden_guard(".hidden=tab label{display:grid}") == []: probs.append("OG-D59 guard failed its negative")
    probs += hidden_guard(PAGE)
    ISO = {"EN": "GB-ENG", "SC": "GB-SCT", "WA": "GB-WLS", "NI": "GB-NIR", "UK": "GB"}  # ISO 3166-2:GB (and 3166-1 for the UK)
    for c, nn in out.items(): nn["iso"] = ISO.get(c)
    final = {x["id"]: x.get("nations") or [c] for c, n in out.items() for t in n["branches"].values() for v in t.values() for x in v}
    (ROOT / "data/body-nations.json").write_text(json.dumps(final, separators=(",", ":")))  # final placement, read by the portal
    for f in ("data/nations.json", "docs/nations.json"): (ROOT / f).write_text(json.dumps({"nations": out, "unplaced_open_bodies": unplaced}, indent=1))
    evd = json.loads((ROOT / "data/nation-evidence.json").read_text())
    placed = {x["id"] for n in out.values() for t in n["branches"].values() for v in t.values() for x in v}
    unl = sorted(({"id": r[0], "name": r[1], "type": r[3].replace("\n", " ")} for r in D["r"] if r[4] and r[0] not in placed), key=lambda x: x["name"])
    meta = json.loads((ROOT / "data/classification.json").read_text())["meta"] if (ROOT / "data/classification.json").exists() else {}
    payload = {"meta": meta, "nations": out, "conflicts": [c for c in evd["conflicts"] if c.get("status") == "contested"], "resolved": sum(1 for c in evd["conflicts"] if c.get("status") == "resolved"), "unplaced": unl,
               "rel": None, "intl": None}  # the UK and the world now has its own page (tools/world.py)
    sys.path.insert(0, str(ROOT / "tools")); import design  # shared design system and page shell (OG-D42)
    (ROOT / "docs/nations.html").write_text(design.wrap_page(PAGE, "nations", drawer=True).replace("__DATA__", json.dumps(payload).replace("</", "<\\/")).replace("__UNPLACED__", str(unplaced)))
    for k, n in out.items(): print(f"{k:3} {n['name']:36} {n['counts']}")
    print("unplaced", unplaced, "problems", probs); sys.exit(1 if probs else 0)
