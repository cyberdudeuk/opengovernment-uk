"""Funding, grants, schemes and support for people and organisations, and the public bodies that give them.
  schemes   GOV.UK's 'Find funding and support for your business' finder: type of support, sizes, stages, regions;
  grants    GOV.UK's Find a grant service: funder, who can apply, how much, opening and closing dates as published;
  funders   publishers of open grants data in 360Giving, joined to the register by organisation identifier (org-id);
  services  regulators' innovation services (sandboxes, advice offices, front doors), from each regulator's own page.
Sectors (fintech, medtech, regtech, govtech and so on) are worked out from titles and descriptions, so a few may be
wrong. Writes data/funding.json. --negative proves the checks fail when they should."""
import collections, copy, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import design  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]; EV = ROOT / "sources/evidence"
SECTORS = [("fintech", "Fintech and financial services", r"fintech|financial services|payments?\b|open banking|insurtech|\bbank(ing)?\b|investment readiness|access to finance"),
           ("medtech", "Medtech and digital health", r"medtech|medical device|diagnostic|digital health|health ?tech|healthcare|clinical|\bnhs\b|patients?"),
           ("lifesci", "Life sciences and biotech", r"life sciences?|biotech|biomedical|genomic|pharma|engineering biology|bioscience|biological"),
           ("regtech", "Regtech and compliance", r"regtech|regulat(ion|ory|or)|compliance|sandbox"),
           ("govtech", "Govtech and public services", r"govtech|public sector|public services?|local authorit|smart cit|civic"),
           ("ai", "AI, data and digital", r"artificial intelligence|\bai\b|machine learning|\bdata\b|digital|software|cyber|quantum|semiconductor|computing"),
           ("cleantech", "Clean energy and net zero", r"net zero|low carbon|zero emission|clean energy|renewable|energy efficiency|decarboni|electric vehicle|hydrogen|heat pump|climate|charging"),
           ("agritech", "Agriculture, food and land", r"agri|farm|food|fisher|woodland|forest|land manage|rural|horticult"),
           ("creative", "Creative industries and culture", r"creative|film|screen|games?\b|music|arts?\b|heritage|museum|culture|cultural|theatre|design"),
           ("space", "Space", r"\bspace\b|satellite|launch"),
           ("defence", "Defence and security", r"defen[cs]e|security|resilience|dual.use"),
           ("transport", "Transport and mobility", r"transport|mobility|aviation|maritime|rail|road|vehicle|drone|autonomous"),
           ("education", "Education, skills and research", r"education|skills?|training|apprentic|research|university|fellowship|studentship|scholar"),
           ("community", "Community, charity and social", r"communit|charit|voluntary|social enterprise|youth|inclusion|wellbeing|equalit"),
           ("export", "Trade and exporting", r"export|international trade|overseas market|global growth")]
AUDIENCE = {"Private Sector": "businesses", "Non-profit": "non-profits", "Public Sector": "public sector", "Local authority": "local authorities", "Personal / Individual": "individuals"}


def sectors(text):
    t = text.lower(); return [k for k, _, rx in SECTORS if re.search(rx, t)]


GENERIC = {"council", "borough", "city", "county", "district", "metropolitan", "london", "of", "the", "royal", "and", "unitary", "authority"}


def core(s): return set(norm(s).split()) - GENERIC


def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", re.sub(r"^the ", "", s.lower().replace("&", " and ")))).strip()


def build():
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    SA = json.loads((ROOT / "data/same-as.json").read_text())["groups"]; canon = {m: c for c, g in SA.items() for m in g["members"]}
    R = {r[0]: r for r in D["r"]}; slug = {r[10]["govuk_slug"]: canon.get(r[0], r[0]) for r in D["r"] if r[10].get("govuk_slug")}
    byname = collections.defaultdict(set)
    for r in D["r"]:
        if r[4]: byname[norm(r[1])].add(canon.get(r[0], r[0]))
    closed = collections.defaultdict(set)
    for r in D["r"]:
        if not r[4]: closed[norm(r[1])].add(r[0])
    one = lambda n: (lambda s: next(iter(s)) if len(s) == 1 else "")(byname.get(norm(n)) or closed.get(norm(n), set()))  # open record first; a closed one when the source still names it
    S = json.loads((EV / "govuk-business-support.json").read_text())["schemes"]
    schemes = [{"title": s["title"], "url": s["url"], "desc": s["desc"], "types": s["types"], "sizes": s["sizes"], "stages": s["stages"], "regions": s["regions"],
                "sectors": sectors(s["title"] + " " + s["desc"]), "by": [slug[g] for g in s["givers"] if g in slug], "updated": s["updated"]} for s in S if "error" not in s]
    G = json.loads((EV / "find-a-grant.json").read_text())["grants"]
    grants = []
    for g in G:
        fo = re.sub(r"\s+", " ", g.get("funding organisation", "")).strip()
        parts = [p.strip() for p in fo.split(",") if p.strip()]
        fid = next((x for x in [one(p) for p in reversed(parts)] + [one(fo), one(re.sub(r"\s*\(.*?\)", "", fo))] if x), "")
        bad = lambda d: bool(d) and d < "1900"
        grants.append({"title": g["title"], "url": g["url"], "desc": g.get("desc", ""), "funder": fo, "by": [fid] if fid else [], "location": g.get("location", ""),
                       "who": [AUDIENCE.get(w.strip(), w.strip()) for w in g.get("who can apply", "").split(",") if w.strip()], "amount": g.get("how much you can get", ""), "total": g.get("total size of grant scheme", ""),
                       "opens": g.get("opening date", ""), "closes": g.get("closing date", ""), "date_flag": "an opening or closing date is given wrongly at source" if bad(g.get("opening date")) or bad(g.get("closing date")) else "",
                       "sectors": sectors(g["title"] + " " + g.get("desc", ""))})
    P = json.loads((EV / "360giving-publishers.json").read_text())["publishers"]
    la = {r[0].split(":")[1]: r[0] for r in D["r"] if r[0].startswith("local-authority:")}
    ch = {str(r[10]["charity_ew"]): canon.get(r[0], r[0]) for r in D["r"] if r[10].get("charity_ew")}
    co = {str(r[10]["companies_house"]): canon.get(r[0], r[0]) for r in D["r"] if r[10].get("companies_house")}
    funders = []
    for p in P:
        oid = p["org_id"]; rid = ""
        if oid.startswith("GB-GOR-") and "government-organisation:" + oid[7:] in R: rid = canon.get("government-organisation:" + oid[7:], "government-organisation:" + oid[7:])
        elif oid.startswith("GB-LAE-") and oid[7:] in la: rid = la[oid[7:]]
        elif oid.startswith("GB-CHC-"): rid = ch.get(oid[7:], "")
        elif oid.startswith("GB-COH-"): rid = co.get(oid[7:], "")
        funders.append({"name": p["name"], "org_id": oid, "website": p["website"], "datasets": p["datasets"], "last": p["last_published"], "id": rid,
                        "grantnav": f"https://grantnav.threesixtygiving.org/org/{oid}" if oid else ""})
    I = json.loads((EV / "innovation-services.json").read_text())["services"]  # noqa: E741
    return {"read": "2026-11-22", "sectors": {k: v for k, v, _ in SECTORS}, "schemes": schemes, "grants": grants, "funders": funders, "services": I}, R


def check(o, R):
    e = []
    for x in o["schemes"] + o["grants"]:
        if any(b not in R for b in x["by"]): e.append(f"unknown giver on {x['title'][:40]}")
    for f in o["funders"]:
        if f["id"] and f["id"] not in R: e.append(f"unknown funder id {f['id']}")
        if f["id"].startswith("local-authority:") and not core(R[f["id"]][1]) & core(f["name"]): e.append(f"council org-id joins a different council: {f['name']} -> {R[f['id']][1]}")
    for s in o["services"]:
        if s["body"] not in R or not s["url"].startswith("https://"): e.append(f"service {s['name']}: bad body or link")
    byt = {g["title"]: g for g in o["grants"]}
    if not any(g["by"] for g in o["grants"]): e.append("no grant joined to its funder")
    if not any("fintech" in s["sectors"] for s in o["services"]): e.append("known answer wrong: no fintech innovation service")
    if not any(g["date_flag"] for g in o["grants"]) and any(g["opens"] < "1900" for g in o["grants"] if g["opens"]): e.append("an impossible date was not flagged")
    return e + ([] if byt else ["no grants"])


def main():
    o, R = build()
    if "--negative" in sys.argv:
        cases = []
        x = copy.deepcopy(o); x["grants"][0]["by"] = ["government-organisation:NOPE"]; cases.append(x)
        x = copy.deepcopy(o); x["services"][0]["body"] = "nope"; cases.append(x)
        x = copy.deepcopy(o); f = next(f for f in x["funders"] if f["id"].startswith("local-authority:")) if any(f["id"].startswith("local-authority:") for f in x["funders"]) else None
        if f: f["id"] = next(k for k in R if k.startswith("local-authority:") and not core(R[k][1]) & core(f["name"]))
        cases.append(x)
        if not all(check(c, R) for c in cases): sys.exit("funding negative: a breaker was not caught")
        print(f"funding negative: all {len(cases)} breakers caught"); return
    e = check(o, R)
    if e: sys.exit("funding: " + "; ".join(e[:6]))
    (ROOT / "data/funding.json").write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":")))
    ids = {i for x in o["schemes"] + o["grants"] for i in x["by"]} | {s["body"] for s in o["services"]} | {f["id"] for f in o["funders"] if f["id"]}
    page = dict(o, names={i: R[i][1] + ("" if R[i][4] else " (closed)") for i in sorted(ids)})  # sorted: a set's order changes between runs (OG-D61)
    data = json.dumps(page, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    (ROOT / "docs/funding.html").write_text(design.wrap_page((ROOT / "tools/funding-page.html").read_text(), "funding").replace("__DATA__", data))
    C = collections.Counter
    print("funding:", len(o["schemes"]), "schemes;", len(o["grants"]), "grants,", sum(1 for g in o["grants"] if g["by"]), "joined to their funder;", len(o["funders"]), "360Giving funders,",
          sum(1 for f in o["funders"] if f["id"]), "in the register;", len(o["services"]), "innovation services;", dict(C(s for x in o["schemes"] + o["grants"] for s in x["sectors"]).most_common(8)))


if __name__ == "__main__":
    main()
