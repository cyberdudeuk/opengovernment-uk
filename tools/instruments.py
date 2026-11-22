"""Legislation, rules, standards and guidance for every body, in three layers, each labelled by how it is known:
  issues     what the body publishes on GOV.UK as issuer: counts by type, and its latest statutory instruments,
             statutory guidance, regulation, standards and treaties (sources/evidence/govuk-instruments.json);
  named_in   legislation whose title contains the body's exact name (sources/evidence/legislation-titles.json);
  applies    cross-cutting laws and rulebooks that apply by rule, from each instrument's own scope statement matched
             to the body's type and nation (sources/evidence/applicability-rules.json).
Writes data/instruments.json. --negative proves the checks fail when they should."""
import collections, copy, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]; EV = ROOT / "sources/evidence"
SAFE = re.compile(r"^https://(www\.)?(gov\.uk|legislation\.gov\.uk|gov\.scot|gov\.wales|finance-ni\.gov\.uk|assets\.publishing\.service\.gov\.uk)/")
FINDER = {"guidance": "https://www.gov.uk/search/guidance-and-regulation?organisations[]={s}", "policy": "https://www.gov.uk/search/policy-papers-and-consultations?organisations[]={s}"}


def load():
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    return (D, json.loads((EV / "govuk-instruments.json").read_text())["orgs"], json.loads((EV / "legislation-titles.json").read_text())["bodies"],
            json.loads((EV / "applicability-rules.json").read_text()), json.loads((ROOT / "data/classification.json").read_text())["bodies"],
            json.loads((ROOT / "data/body-nations.json").read_text()), json.loads((ROOT / "data/same-as.json").read_text())["groups"])


_IDS = {}


def matches(when, r, cl, nat):
    if "has_id" in when: return bool(r[10].get(when["has_id"]))
    if "ids" in when: return r[0] in when["ids"]
    if "ids_file" in when:
        f = when["ids_file"]
        if f not in _IDS: _IDS[f] = {e["id"] for e in json.loads((ROOT / f).read_text())["entries"] if e["id"]}
        return r[0] in _IDS[f]
    if "name_has" in when and when["name_has"].lower() not in r[1].lower(): return False
    if cl.get("btype") not in when["btype"]: return False
    if "family" in when and r[0].split(":")[0] not in when["family"]: return False
    ns = nat or ["none"]
    return set(ns) <= set(when["nation"]) if when.get("only") else bool(set(ns) & set(when["nation"]))


def build():
    D, G, L, A, CL, NAT, SA = load()
    folded = {m for g in SA.values() for m in g["members"]}
    out = {}
    for r in D["r"]:
        if not r[4] or r[0] in folded: continue
        i, rec = r[0], {}
        g = G.get(i)
        if g and (g.get("counts") or g.get("binding")):
            rec["issues"] = {"counts": g["counts"], "binding": g.get("binding", []), "finder": {k: v.format(s=g["slug"]) for k, v in FINDER.items()}}
        lt = L.get(i, {})
        if lt.get("items"): rec["named_in"] = lt["items"] + ([{"more": lt["more"]}] if lt.get("more") else [])
        ap = [x["id"] for x in A["rules"] if matches(x["when"], r, CL.get(i, {}), NAT.get(i))]
        if ap: rec["applies"] = ap
        if rec: out[i] = rec
    rules = {x["id"]: {k: x[k] for k in ("title", "kind", "issuer", "url", "scope", "scope_url")} | {"likely": bool(x.get("likely"))} for x in A["rules"]}
    return {"read": A["read"], "rules": rules, "to_confirm": A["to_confirm"], "bodies": out}, D


def check(o, D):
    e = []
    R = {r[0]: r for r in D["r"]}
    for k, x in o["rules"].items():
        if not SAFE.match(x["url"]) or not SAFE.match(x["scope_url"]): e.append(f"rule {k}: source not official")
        if x["issuer"] and (x["issuer"] not in R or not R[x["issuer"]][4]): e.append(f"rule {k}: issuer is not an open register record")
    for i, b in o["bodies"].items():
        for it in b.get("named_in", []):
            if "url" in it and not it["url"].startswith("https://www.legislation.gov.uk/"): e.append(f"{i}: legislation link not on legislation.gov.uk")
        for it in b.get("issues", {}).get("binding", []):
            if not SAFE.match(it["url"]): e.append(f"{i}: GOV.UK item not official")
        if any(a not in o["rules"] for a in b.get("applies", [])): e.append(f"{i}: unknown rule")
    byname = {r[1]: r[0] for r in D["r"] if r[4]}
    def has(name, rule): return rule in o["bodies"].get(byname.get(name, ""), {}).get("applies", [])
    for name, rule, want in [("Greater Glasgow and Clyde", "foisa-nhs", True), ("Glasgow City Council", "foisa-councils", True), ("Glasgow City Council", "foi-lg", False), ("Arts Council England", "public-appointments", True), ("HM Treasury", "mpm", True), ("Manchester City Council", "lg-transparency", True), ("Manchester City Council", "mpm", False), ("Welsh Government", "mwpm", True), ("HM Treasury", "spfm", False)]:
        if has(name, rule) != want: e.append(f"known answer wrong: {name} {rule} should be {want}")
    if not any("British Museum Act" in it.get("title", "") for it in o["bodies"].get(byname.get("British Museum", byname.get("The British Museum", "")), {}).get("named_in", [])):
        e.append("known answer wrong: British Museum Act not found")
    return e


def main():
    o, D = build()
    if "--negative" in sys.argv:
        cases = []
        x = copy.deepcopy(o); x["rules"]["mpm"]["url"] = "https://example.com/mpm"; cases.append(x)
        x = copy.deepcopy(o); k = next(iter(x["bodies"])); x["bodies"][k]["applies"] = ["invented"]; cases.append(x)
        x = copy.deepcopy(o); [b.get("applies", []).remove("mpm") for b in x["bodies"].values() if "mpm" in b.get("applies", [])]; cases.append(x)
        if not all(check(c, D) for c in cases): sys.exit("instruments negative: a breaker was not caught")
        print(f"instruments negative: all {len(cases)} breakers caught"); return
    e = check(o, D)
    if e: sys.exit("instruments: " + "; ".join(e[:8]))
    (ROOT / "data/instruments.json").write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":")))
    B = o["bodies"]; c = collections.Counter(a for b in B.values() for a in b.get("applies", []))
    print(f"instruments: {len(B)} bodies; issuing on GOV.UK {sum(1 for b in B.values() if 'issues' in b)}; named in legislation {sum(1 for b in B.values() if 'named_in' in b)}; rules {dict(c)}")


if __name__ == "__main__":
    main()
