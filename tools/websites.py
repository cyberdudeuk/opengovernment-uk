"""Every listed body's own website, from one table that combines the sources (first match wins, in this order):
  1. the official council register (planning.data.gov.uk local-authority dataset), for councils in England, and the
     official council lists for Scotland (mygov.scot) and Northern Ireland (nidirect), matched by exact name within
     that nation's councils;
  2. Wikidata's official website (P856) for the body's Wikidata item, or for the item carrying the body's exact
     NHS Organisation Data Service ID, council GSS code, LEI or Companies House number (matched on the code, never on the name);
  3. the website the register itself records, when it isn't a GOV.UK organisation page;
  4. the body's GOV.UK organisation page, for bodies whose home on the web is GOV.UK.
A folded duplicate (tools/sameas.py) shares its main record's website. Writes data/websites.json: id -> [url, source]."""
import collections, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]; EV = ROOT / "sources/evidence"
SAFE = re.compile(r"^https?://[^\s\"'<>]+$")


def build():
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    la = json.loads((EV / "la-websites.json").read_text())["websites"]
    wd = {q: u for q, u in json.loads((EV / "wikidata-websites-names.json").read_text())["website"]}
    bc = json.loads((EV / "wikidata-websites-by-code.json").read_text())
    sa = json.loads((ROOT / "data/same-as.json").read_text())["groups"]
    nat = json.loads((ROOT / "data/body-nations.json").read_text())
    nm = lambda x: re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", re.sub(r"^the ", "", x.lower().replace("&", " and ")))).strip()
    dev, DEV_MISS = {}, []
    DEVF = json.loads((EV / "devolved-council-websites.json").read_text())
    live = {r[0] for r in D["r"] if r[4]}
    for code, rows in DEVF["councils"].items():
        pool = {}
        for r in D["r"]:
            if r[4] and (nat.get(r[0]) or []) == [code]: pool.setdefault(nm(r[1]), []).append(r[0])
        for x in rows:
            ids = pool.get(nm(x["name"]), [])
            dec = DEVF.get("decisions", {}).get(x["name"])
            if dec and not ids and dec["id"] in live: ids = [dec["id"]]
            if len(ids) == 1 and x["website"]: dev[ids[0]] = (x["website"], "official council list (" + ("mygov.scot" if code == "SC" else "nidirect") + ")")
            else: DEV_MISS.append(x["name"])
    build.dev_missing = DEV_MISS
    out = {}
    for r in D["r"]:
        if not r[4]: continue
        i, ids = r[0], r[10]
        cand = []
        if i.startswith("local-authority:") and i.split(":")[1] in la: cand.append((la[i.split(":")[1]]["website"], "council register (planning.data.gov.uk)"))
        if i in dev: cand.append(dev[i])
        if ids.get("wikidata") in wd: cand.append((wd[ids["wikidata"]], "Wikidata"))
        if ids.get("nhs_ods") in bc["ods"]: cand.append((bc["ods"][ids["nhs_ods"]], "Wikidata (by ODS code)"))
        for key, src in (("gss", "gss"), ("lei", "lei"), ("companies_house", "ch")):
            if ids.get(key) in bc[src]: cand.append((bc[src][ids[key]], f"Wikidata (by {src.upper()} code)"))
        if r[9] and "gov.uk/government/organisations" not in r[9]: cand.append((r[9], "register"))
        if ids.get("govuk_slug"): cand.append(("https://www.gov.uk/government/organisations/" + ids["govuk_slug"], "GOV.UK page"))
        for u, src in cand:
            if SAFE.match(u or ""): out[i] = [u, src]; break
    for c, g in sa.items():  # one record per body: share the best website across the group
        best = next((out[k] for k in [c, *g["members"]] if k in out), None)
        if best:
            for k in [c, *g["members"]]: out.setdefault(k, best)
    return out, D


def check(out, D):
    e = []
    byname = {r[1]: r[0] for r in D["r"] if r[4]}
    for name, want in [("Manchester City Council", "manchester.gov.uk"), ("Met Office", "metoffice.gov.uk"), ("Birmingham City Council", "birmingham.gov.uk"), ("National Library of Wales", "library.wales"), ("Aberdeen City Council", "aberdeencity.gov.uk"), ("Belfast City Council", "belfastcity.gov.uk")]:
        i = byname.get(name)
        if not i or i not in out or want not in out[i][0]: e.append(f"known answer wrong: {name} -> {(out.get(i) or ['none'])[0]}")
    if any(not SAFE.match(u) for u, _ in out.values()): e.append("an unsafe or malformed address")
    if getattr(build, "dev_missing", []): e.append(f"official council list entries with no single register match: {build.dev_missing}")
    return e


def main():
    out, D = build()
    if "--negative" in sys.argv:
        o = dict(out); o["x"] = ["javascript:alert(1)", "test"]
        bad = dict(out); bad.pop(next(r[0] for r in D["r"] if r[1] == "Met Office"), None)
        miss = build.dev_missing; build.dev_missing = ["Glasgow City Council"]
        ok = bool(check(o, D)) and bool(check(bad, D)) and bool(check(out, D))
        build.dev_missing = miss
        if not ok: sys.exit("websites negative: not caught")
        print("websites negative: three breakers caught"); return
    e = check(out, D)
    if e: sys.exit("websites: " + "; ".join(e))
    (ROOT / "data/websites.json").write_text(json.dumps(out, separators=(",", ":")))
    n_open = sum(1 for r in D["r"] if r[4])
    print("websites:", len(out), "of", n_open, "open records;", dict(collections.Counter(s for _, s in out.values())))


if __name__ == "__main__":
    main()
