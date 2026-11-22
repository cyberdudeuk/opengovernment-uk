"""The UK's cooperation with each country: the Commonwealth, trade agreements in effect, tax treaties and the kind of
every treaty -> data/cooperation.json

Official sources only, read into sources/evidence/cooperation-sources.json (--refresh re-reads them):
  the Commonwealth's members   thecommonwealth.org, "Our member countries" (the Commonwealth Secretariat)
  how the UK takes part        GOV.UK, UK Representation in the Commonwealth (Foreign, Commonwealth and Development Office)
  trade agreements in effect   GOV.UK, "UK trade agreements in effect" (Department for Business and Trade)
  tax treaties                 GOV.UK, "Tax treaties" collection (HM Revenue and Customs)
Kinds of treaty (trade, tax, social security and so on) are worked out from each title, so they are modelled and say so.

Names are kept as each source gives them. Each country is placed on the map by exact name or by a recorded alias
(sources/evidence/treaty-partners.json); a name that is neither fails the build. Places that are part of the UK family
(Crown Dependencies and Overseas Territories) are shown as UK territories, never as foreign partners. Former names of the
same state (Swaziland, Zaire) are placed on today's country and marked; states that no longer exist are listed, not drawn.

  python tools/cooperation.py              build and check (offline, from the evidence file)
  python tools/cooperation.py --refresh    re-read the official sources first
  python tools/cooperation.py --negative   prove the checks fail when they should
"""
import collections, hashlib, html, html.parser, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EV = ROOT / "sources/evidence"
SRC = EV / "cooperation-sources.json"
UA = "OpenGovernmentUK/0.4 (https://github.com/cyberdudeuk/opengovernment-uk)"
U = {"cw_members": "https://thecommonwealth.org/our-member-countries",
     "cw_uk": "https://www.gov.uk/world/organisations/uk-representation-in-the-commonwealth",
     "trade": "https://www.gov.uk/guidance/uk-trade-agreements-in-effect",
     "tax": "https://www.gov.uk/government/collections/tax-treaties"}
UK_FAMILY = {"Anguilla", "Bermuda", "British Virgin Islands", "Cayman Islands", "Falkland Islands", "Gibraltar", "Montserrat",
             "Turks and Caicos Islands", "Isle of Man", "Jersey", "Guernsey", "St Helena, Ascension and Tristan da Cunha"}
KINDS = [  # first match wins; worked out from the title (modelled)
    ("trade", "Trade", r"free trade|trade (and|continuity|partnership|cooperation)|economic partnership|trade agreement|association agreement|digital (economy|trade)|customs|\bCPTPP\b|mutual recognition"),
    ("tax", "Tax", r"double taxation|taxes on income|\btax(es|ation)?\b|fiscal evasion"),
    ("social", "Social security and health", r"social security|reciprocal health|health ?care|pension"),
    ("air", "Air services", r"air services|air transport|civil aviation|aviation"),
    ("justice", "Justice, policing and returns", r"extradition|mutual legal assistance|transfer of (sentenced|prisoners)|readmission|police|criminal|crime|drug"),
    ("defence", "Defence and security", r"defen[cs]e|military|classified|status of (forces|their forces)|security of information|armed forces|weapons|disarmament"),
    ("science", "Science, research and space", r"scien|research|technolog|outer space|\bspace\b|innovation"),
    ("investment", "Investment", r"investment"),
    ("environment", "Environment, energy and fisheries", r"climate|environment|energy|nuclear|fisher|marine|whal|pollution|biodiversity"),
    ("culture", "Culture, education and youth", r"cultur|educat|youth|scholar|heritage|sport"),
    ("people", "Visas, migration and mobility", r"visa|migration|mobility|working holiday|asylum"),
    ("diplomatic", "Diplomatic and consular", r"consular|diplomatic|privileges and immunities|headquarters|embass"),
    ("transport", "Shipping, transport and communications", r"shipping|maritime|road|rail|transport|postal|telecommunic|satellite|broadcast"),
    ("borders", "Borders and territory", r"boundar|frontier|delimitation|continental shelf|territor"),
    ("development", "Aid and development", r"development|grant agreement|loan|debt|aid\b")]


def fetch(u):
    return subprocess.run(["curl", "-s", "-L", "-m", "60", "-A", UA, u], capture_output=True, text=True).stdout  # noqa: S603,S607 fixed program, our own URLs


class Rows(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.rows, self.row, self.cell = [], None, None
    def handle_starttag(self, t, a):
        if t == "tr": self.row = []
        if t in ("td", "th") and self.row is not None: self.cell = ""
    def handle_endtag(self, t):
        if t in ("td", "th") and self.cell is not None: self.row.append(re.sub(r"\s+", " ", self.cell).strip()); self.cell = None
        if t == "tr" and self.row: self.rows.append(self.row); self.row = None
    def handle_data(self, d):
        if self.cell is not None: self.cell += d


def refresh():
    c = fetch(U["cw_members"]); seen, cw = set(), []
    for slug, name in re.findall(r'href="/our-member-countries/([a-z0-9-]+)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{3,60})<', c):
        if slug not in seen: seen.add(slug); cw.append({"name": html.unescape(name.strip()), "url": "https://thecommonwealth.org/our-member-countries/" + slug})
    uk = json.loads(fetch(U["cw_uk"].replace("https://www.gov.uk/", "https://www.gov.uk/api/content/")))
    p = Rows(); p.feed(json.loads(fetch(U["trade"].replace("https://www.gov.uk/", "https://www.gov.uk/api/content/")))["details"]["body"])
    trade = [{"country": r[0], "agreement": r[1], "mechanism": r[2], "uk_trade_2025_gbp_m": r[3]} for r in p.rows if len(r) == 4 and r[0] != "Country"]
    tx = json.loads(fetch(U["tax"].replace("https://www.gov.uk/", "https://www.gov.uk/api/content/")))
    tax = []
    for d in tx["links"]["documents"]:
        t = d["title"]
        m = re.match(r"(.+?):? tax treaties$", t) or re.search(r"between the UK and (?:the )?(.+?)(?: for the exchange|:)", t) or re.match(r"Tax Information Exchange Agreement: (.+?) -", t)
        if m: tax.append({"country": m.group(1).strip(), "title": t, "url": "https://www.gov.uk" + d["base_path"], "kind": "tax treaties" if "tax treaties" in t else "exchange of tax information"})
    out = {"read": "2026-11-22", "urls": U, "commonwealth": {"members": cw, "uk_role": {"title": uk["title"], "description": uk["description"], "url": U["cw_uk"]}},
           "trade": trade, "tax": tax}
    out["sha256"] = hashlib.sha256(json.dumps(out, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    SRC.write_text(json.dumps(out, ensure_ascii=False, indent=0))


def kind(title):
    for k, _, p in KINDS:
        if re.search(p, title, re.I): return k
    return "other"


def build():
    S = json.loads(SRC.read_text()); P = json.loads((EV / "treaty-partners.json").read_text())
    wm = json.loads((ROOT / "data/worldmap.json").read_text()); known = set(wm["shapes"]) | set(wm["dots"])
    rel = json.loads((ROOT / "data/relations.json").read_text())
    alias, former, uk_fam, gone = P["aliases"], P.get("former_names", {}), P.get("uk_family_names", {}), set(P.get("former_states", []))
    problems = []
    def place(name, src):
        if name in UK_FAMILY or name in uk_fam: return ("uk", uk_fam.get(name, name))
        if name in gone: return ("gone", name)
        if name in former: return ("country", former[name])
        if name in known: return ("country", name)
        if name in alias and len(alias[name]) == 1: return ("country", alias[name][0])
        problems.append(f"{src}: {name!r} is not placed (add it to treaty-partners.json)"); return (None, None)
    C = collections.defaultdict(lambda: {"names": set(), "cw": None, "cw_name": "", "trade_name": "", "trade": [], "tax": [], "treaties": collections.Counter(), "former": set()})
    uk_terr = collections.defaultdict(list); gone_l = []
    for m in S["commonwealth"]["members"]:
        k, c = place(m["name"], "Commonwealth")
        if k == "country": C[c]["cw"] = m["url"]; C[c]["names"].add(m["name"]); C[c]["cw_name"] = m["name"]
    for t in S["trade"]:
        k, c = place(t["country"], "trade agreements")
        if k == "country": C[c]["trade_name"] = C[c]["trade_name"] or t["country"]; C[c]["trade"].append({"agreement": t["agreement"], "mechanism": t["mechanism"], "uk_trade_2025_gbp_m": t["uk_trade_2025_gbp_m"]}); C[c]["names"].add(t["country"])
        elif k == "uk": uk_terr[c].append({"what": t["agreement"], "url": U["trade"]})
    for t in S["tax"]:
        k, c = place(t["country"], "tax treaties")
        if k == "country":
            C[c]["tax"].append({"title": t["title"], "url": t["url"], "kind": t["kind"]}); C[c]["names"].add(t["country"])
            if t["country"] in former: C[c]["former"].add(t["country"])
        elif k == "uk": uk_terr[c].append({"what": t["title"], "url": t["url"]})
        elif k == "gone": gone_l.append({"name": c, "what": t["title"], "url": t["url"]})
    kinds = [kind(t["title"]) for t in rel["treaties"]]
    for t, kd in zip(rel["treaties"], kinds, strict=True):
        for c in wm["place"].get(t["partner"], []): C[c]["treaties"][kd] += 1
    ABBR = [(r"\bDem\. Rep\.", "Democratic Republic of the"), (r"\bRep\.", "Republic"), (r"\bIs\.", "Islands"), (r"\bSt\. Vin\. and Gren\.", "St Vincent and the Grenadines"),
            (r"\bHerz\.", "Herzegovina"), (r"\bBarb\.", "Barbuda"), (r"\bSt\.", "St"), (r"\bCent\. Afr\.", "Central African"), (r"\bEq\.", "Equatorial"), (r"\bS\. Sudan", "South Sudan")]
    def display(c, v):  # the Commonwealth's name, then the trade list's, then the map's own name spelt out; never a former name
        if v["cw_name"]: return v["cw_name"]
        if v["trade_name"]: return v["trade_name"]
        n = c
        for a, b in ABBR: n = re.sub(a, b, n)
        return n.replace("Congo Congo", "Congo").replace("of the Congo", "of the Congo")
    countries = {c: {"display": display(c, v), "names": sorted(v["names"]), "commonwealth": v["cw"], "trade": v["trade"], "tax": v["tax"], "former_names": sorted(v["former"]),
                     "treaties": dict(v["treaties"]), "treaty_total": sum(v["treaties"].values())} for c, v in sorted(C.items())}
    reg = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    cw_bodies = sorted([[r[0], r[1]] for r in reg["r"] if r[4] and re.search(r"\bCommonwealth\b", r[1]) and not re.search(r"Foreign, Commonwealth", r[1])], key=lambda x: x[1])
    return {"read": S["read"], "sources": S["urls"], "kinds": [[k, label] for k, label, _ in KINDS] + [["other", "Other or not worked out"]],
            "treaty_kind": kinds, "countries": countries, "uk_territories": dict(uk_terr), "former_states": gone_l,
            "commonwealth": {"members": len(S["commonwealth"]["members"]), "uk_role": S["commonwealth"]["uk_role"], "uk_bodies": cw_bodies},
            "note": "Map boundaries and names are Natural Earth's and imply no view by this portal on the status of any territory."}, problems


def check(out, problems):
    e = list(problems)
    C = out["countries"]
    for c in ["Canada", "India", "Australia", "South Africa", "Jamaica"]:  # known Commonwealth members
        if not C.get(c, {}).get("commonwealth"): e.append(f"known answer: {c} should be a Commonwealth member")
    for c in ["United States of America", "France", "Japan"]:  # known non-members
        if C.get(c, {}).get("commonwealth"): e.append(f"known answer: {c} is not a Commonwealth member")
    if out["commonwealth"]["members"] != 56: e.append(f"the Commonwealth has {out['commonwealth']['members']} members in the source, expected 56 (check the source)")
    if not any("Free Trade Agreement" in t["agreement"] for t in C.get("Australia", {}).get("trade", [])): e.append("known answer: the UK-Australia Free Trade Agreement is in effect")
    if not C.get("United States of America", {}).get("tax"): e.append("known answer: the UK has a tax treaty with the USA")
    if any(t in C for t in UK_FAMILY): e.append("a Crown Dependency or Overseas Territory is listed as a foreign partner")
    if C.get("Dem. Rep. Congo", {}).get("display") == "Zaire": e.append("a former name is shown as a country's name")
    if C.get("United States of America", {}).get("display") != "United States of America": e.append("known answer: the USA's display name")
    if "voluntary association" not in out["commonwealth"]["uk_role"]["description"]: e.append("the Commonwealth's description is not the official wording")
    if sum(1 for k in out["treaty_kind"] if k != "other") < len(out["treaty_kind"]) * .5: e.append("fewer than half the treaties have a kind; the patterns need review")
    return e


def main():
    if "--refresh" in sys.argv: refresh()
    out, problems = build()
    if "--negative" in sys.argv:
        bad = json.loads(json.dumps(out)); bad["countries"]["France"] = {"commonwealth": "x"}; bad["countries"]["Gibraltar"] = {}
        caught = [bool(check(bad, [])), bool(check(out, ["tax treaties: 'Atlantis' is not placed"]))]
        if not all(caught): sys.exit(f"cooperation negative: {caught.count(False)} not caught")
        print("cooperation negative: all breakers caught"); return
    e = check(out, problems)
    if e: sys.exit("cooperation: " + "; ".join(e))
    (ROOT / "data/cooperation.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    C = out["countries"]
    print(f"cooperation: {len(C)} countries; Commonwealth {sum(1 for v in C.values() if v['commonwealth'])}; trade agreements in effect with {sum(1 for v in C.values() if v['trade'])}; "
          f"tax treaties with {sum(1 for v in C.values() if v['tax'])}; UK territories {len(out['uk_territories'])}; former states {len(out['former_states'])}; "
          f"treaty kinds {dict(collections.Counter(out['treaty_kind']).most_common())}")


if __name__ == "__main__":
    main()
