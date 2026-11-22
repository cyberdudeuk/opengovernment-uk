"""Local government in England under the English Devolution and Community Empowerment Act 2026: current and planned.

Reads the hand-transcribed facts in sources/evidence/local-government-2026.json (every fact carries its sources) and
joins them to the register:
  - each reorganisation area -> its county council, district councils (ONS district-to-county lookup, by GSS code)
    and the neighbouring unitary councils the area's own name includes (ONS district names, by GSS code);
  - each strategic authority -> its register record by exact name (open records first), or flagged as missing.
Fails closed if the ONS lookup's fingerprint changes, a fact has no source, a status is unknown, or a two-tier county
in the ONS lookup is not in exactly one area. Writes data/local-government.json. --negative proves the checks bite."""
import collections, copy, hashlib, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]; EV = ROOT / "sources/evidence"
LOOKUP_SHA = "af375fc83aa779e61d5957184798c00671362e892fd9c236143de80b7dfbb249"
TIERS = {"foundation-single", "foundation-combined", "mayoral", "mayoral-established"}
DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


def load():
    raw = (EV / "ons-lad-cty-dec-2024-en.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != LOOKUP_SHA: sys.exit("localgov: ONS district-to-county lookup changed; review it and update LOOKUP_SHA")
    cty = [f["attributes"] for f in json.loads(raw)["features"]]
    lad = {f["attributes"]["LAD24NM"]: f["attributes"]["LAD24CD"] for f in json.loads((EV / "ons-lad-dec-2024-uk.json").read_text())["features"]}
    facts = json.loads((EV / "local-government-2026.json").read_text())
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    return cty, lad, facts, D


def build():
    cty, lad, F, D = load()
    R = {r[0]: r for r in D["r"]}
    gss = {}
    for r in D["r"]:
        g = r[10].get("gss")
        if g and (g not in gss or (r[4] and not R[gss[g]][4])): gss[g] = r[0]
    byname = collections.defaultdict(list)
    for r in D["r"]: byname[r[1].lower()].append(r[0])

    def one(name):
        hits = byname.get(name.lower(), []); op = [h for h in hits if R[h][4]]
        return (op or hits or [None])[0]
    county_code = {x["CTY24NM"]: x["CTY24CD"] for x in cty}
    districts = collections.defaultdict(list)
    for x in cty: districts[x["CTY24NM"]].append(x["LAD24CD"])
    areas, council_area, missing = [], {}, []
    for a in F["reorganisation"]["areas"]:
        ids = []
        for c in a["counties"]:
            cc = gss.get(county_code.get(c, "")); (ids.append(cc) if cc else missing.append(f"{a['area']}: county council {c}"))
            for d in districts.get(c, []):
                x = gss.get(d); (ids.append(x) if x else missing.append(f"{a['area']}: district {d}"))
        for u in a["unitaries"]:
            x = gss.get(lad.get(u, "")); (ids.append(x) if x else missing.append(f"{a['area']}: unitary {u}"))
        b = dict(a, councils=ids); areas.append(b)
        for i in ids: council_area.setdefault(i, []).append(len(areas) - 1)
    sas = []
    for s in F["strategic_authorities"]:
        i = one(s["name"]); sas.append(dict(s, id=i, in_register=bool(i)))
    asof = F["as_of"]
    TL = [  # (date, what, sources): every event comes from the facts file's sources
        ("2025-12", "Ministers ask 63 councils about postponing their May 2026 elections; first mayoral elections in four priority areas moved to May 2028", ["dpp-funds", "hansard-dpp"]),
        ("2026-04-29", "The English Devolution and Community Empowerment Act becomes law", ["assent"]),
        ("2026-05", "Council elections: 107 go ahead and 29 are postponed; East Surrey and West Surrey councils elected", ["postpone-2026", "review-launch"]),
        ("2026-05-21", "Government sets out commencement: the supplementary vote returns for mayors and police and crime commissioners", ["sv"]),
        ("2026-09-07", "Reorganisation review launched; decisions for Essex, Hampshire, Norfolk and Suffolk withdrawn", ["review-launch", "review-letter"]),
        ("2026-10-29", "Five areas get 'minded to' decisions; July decisions for nine areas withdrawn; 15 areas under review", ["five-counties", "withdrawn-9", "review-6"]),
        ("2027-04-01", "East Surrey and West Surrey councils take over", ["five-counties"]),
        ("2027-05", "Elections to existing councils in the other 20 areas; first mayors elected in Cumbria and in Cheshire and Warrington", ["withdrawn-9", "ifg-dpp"]),
        ("2028-05", "Elections to the new (shadow) councils; first mayors in Sussex and Brighton, Hampshire and the Solent, Greater Essex, and Norfolk and Suffolk", ["withdrawn-9", "dpp-funds"]),
        ("2029-04-01", "New single councils take over in the 20 remaining areas, if confirmed", ["withdrawn-9", "oxford"]),
    ]
    timeline = [{"date": d, "what": w, "src": s, "when": "done" if d <= asof else "planned"} for d, w, s in TL]
    out = {"timeline": timeline, "meta": {"as_of": F["as_of"], "about": F["about"], "built_from": ["sources/evidence/local-government-2026.json", "sources/evidence/ons-lad-cty-dec-2024-en.json (ONS, sha " + LOOKUP_SHA[:12] + ")", "sources/evidence/ons-lad-dec-2024-uk.json"],
                    "counts": {"areas": len(areas), "councils_in_areas": len(council_area), "strategic_authorities": len(sas),
                               "sa_current": sum(s["status"] == "current" for s in sas), "sa_planned": sum(s["status"] == "planned" for s in sas),
                               "sa_not_in_register": sum(not s["in_register"] for s in sas),
                               "by_status": dict(collections.Counter(a["status"] for a in areas))}},
           "sources": F["sources"], "act": F["act"], "strategic_authorities": sas,
           "reorganisation": {k: v for k, v in F["reorganisation"].items() if k != "areas"} | {"areas": areas},
           "council_area": council_area, "missing": missing,
           "two_tier_counties": sorted({x["CTY24NM"] for x in cty if x["LAD24CD"].startswith("E07")})}
    return out, R


def check(out, R):
    e = []
    srcs = set(out["sources"])

    def need(obj, where):
        s = obj.get("src")
        if not s or any(k not in srcs for k in s): e.append(f"no valid source: {where}")
    for t in out["timeline"]: need(t, t["what"][:40])
    if [t["date"] for t in out["timeline"]] != sorted(t["date"] for t in out["timeline"]): e.append("timeline out of order")
    need(out["act"]["royal_assent"], "royal assent"); need(out["act"]["competences"], "competences")
    for t in out["act"]["tiers"]: need(t, t["key"])
    for c in out["act"]["changes"]: need(c, c["key"])
    for s in out["strategic_authorities"]:
        need(s, s["name"])
        if s["tier"] not in TIERS: e.append(f"unknown tier: {s['name']}")
        if s["status"] not in ("current", "planned"): e.append(f"unknown status: {s['name']}")
        if s["status"] == "planned" and not DATE.match(s.get("first_mayor", "")): e.append(f"planned mayoral authority without a first election date: {s['name']}")
        if s["id"] and not R[s["id"]][4]: e.append(f"strategic authority matched to a closed record: {s['name']}")
    st = out["reorganisation"]["statuses"]
    for a in out["reorganisation"]["areas"]:
        need(a, a["area"])
        if a["status"] not in st: e.append(f"unknown status: {a['area']}")
        for k in ("existing_elections", "shadow_election", "vesting"):
            if a.get(k) and not DATE.match(a[k]): e.append(f"bad date {k}: {a['area']}")
        if a["status"] in ("decided", "minded-to") and not a.get("new_councils"): e.append(f"decision without a number of new councils: {a['area']}")
        if not a["councils"]: e.append(f"no councils joined: {a['area']}")
    covered = sorted(c for a in out["reorganisation"]["areas"] for c in a["counties"])
    if covered != out["two_tier_counties"]: e.append(f"areas don't cover each two-tier county exactly once: {set(covered) ^ set(out['two_tier_counties'])}")
    if len(out["reorganisation"]["areas"]) != 21: e.append("expected 21 reorganisation areas (MHCLG)")
    if len(out["council_area"]) != 205: e.append(f"expected 205 councils: MHCLG's 204 in 21 areas (18 December 2025) plus West Berkshire in the Oxfordshire proposal; got {len(out['council_area'])}")
    dup = [k for k, v in out["council_area"].items() if len(v) > 1]
    if dup: e.append(f"councils in more than one area: {dup[:3]}")
    if out["missing"]: e.append(f"councils not found in the register: {out['missing'][:3]}")
    name = {k: r[1] for k, r in R.items()}
    A = out["reorganisation"]["areas"]

    def area_of(n):
        i = next((k for k, v in name.items() if v == n and R[k][4]), None)
        return A[out["council_area"][i][0]] if i in out["council_area"] else None
    known = [("Surrey Heath Borough Council", lambda a: a and a["status"] == "decided" and a["vesting"] == "2027-04-01"),
             ("Gedling Borough Council", lambda a: a and a["area"] == "Nottinghamshire and Nottingham" and a["status"] == "review"),
             ("Oxford City Council", lambda a: a and a["status"] == "minded-to" and a["new_councils"] == 3),
             ("West Berkshire Council", lambda a: a and a["area"].startswith("Oxfordshire")),
             ("Cheltenham Borough Council", lambda a: a and a["area"] == "Gloucestershire"),
             ("Manchester City Council", lambda a: a is None)]
    for n, ok in known:
        if not any(v == n for v in name.values()): e.append(f"known answer not found: {n}"); continue
        if not ok(area_of(n)): e.append(f"known answer wrong: {n}")
    gm = next((s for s in out["strategic_authorities"] if s["name"] == "Greater Manchester Combined Authority"), None)
    if not gm or not gm["in_register"] or gm["tier"] != "mayoral": e.append("known answer wrong: Greater Manchester Combined Authority is a mayoral strategic authority in the register")
    return e


def main():
    out, R = build()
    if "--negative" in sys.argv:
        br = []
        o = copy.deepcopy(out); o["reorganisation"]["areas"][0]["src"] = []; br.append(o)
        o = copy.deepcopy(out); o["reorganisation"]["areas"].pop(); br.append(o)
        o = copy.deepcopy(out); o["reorganisation"]["areas"][1]["status"] = "agreed"; br.append(o)
        o = copy.deepcopy(out); o["strategic_authorities"][-1]["first_mayor"] = ""; br.append(o)
        o = copy.deepcopy(out); k = next(iter(o["council_area"])); o["council_area"][k] = [0, 1]; br.append(o)
        o = copy.deepcopy(out); o["reorganisation"]["areas"][0]["vesting"] = "April 2027"; br.append(o)
        missed = sum(1 for o in br if not check(o, R))
        if missed: sys.exit(f"localgov negative: {missed} breaker(s) not caught")
        print(f"localgov negative: all {len(br)} breakers caught"); return
    e = check(out, R)
    if e: sys.exit("localgov: " + "; ".join(e))
    (ROOT / "data/local-government.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("localgov:", out["meta"]["counts"])


if __name__ == "__main__":
    main()
