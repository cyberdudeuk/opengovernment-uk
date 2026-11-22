"""The UK and the world: a section of its own -> docs/world.html

International bodies and who speaks for the UK in each (tools/international.py), memberships, treaties and agreements
(tools/relations.py), cooperation by country, the Commonwealth, trade agreements in effect and tax treaties
(tools/cooperation.py), the treaty map (tools/worldmap.py), the UK's shares and votes in international financial
institutions (tools/intl_ownership.py, also in BODS) and the open-standard files (tools/standards.py).
One page, one tab bar, so nothing needs a long scroll; the chosen tab, country, kind and shading are kept in the address.

  python tools/world.py             build and check
  python tools/world.py --negative  prove the checks fail when they should
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = (ROOT / "tools/world-page.html").read_text()
STD = [  # file, standard, what it holds, the standard's own page
    ("data/catalogue.jsonld", "W3C DCAT 3 (DCAT-AP shaped)", "The catalogue of every dataset and download: start here", "https://www.w3.org/TR/vocab-dcat-3/"),
    ("data/international.jsonld", "W3C Organization Ontology and schema.org", "Memberships (org:Membership, with the UK body that leads), treaties and agreements (schema:Legislation), countries with trade agreements and tax treaties", "https://www.w3.org/TR/vocab-org/"),
    ("bods-0.4.json", "Beneficial Ownership Data Standard 0.4", "Ownership and control: every public body, and the UK's shares and votes in international financial institutions", "https://standard.openownership.org/en/0.4.0/"),
    ("data/register.jsonld", "W3C Organization Ontology and schema.org", "Every public body, its parent, codes, links to Wikidata and LEI, website and classification", "https://www.w3.org/TR/vocab-org/"),
    ("data/register.csv", "W3C CSV on the Web", "The register as a table, described by register.csv-metadata.json", "https://www.w3.org/TR/tabular-data-primer/"),
    ("data/taxonomies.skos.jsonld", "W3C SKOS", "Types of body, purposes (UN COFOG), activities, reach, nations (ISO 3166-2:GB), kinds of treaty", "https://www.w3.org/TR/skos-reference/"),
    ("data/provenance.jsonld", "W3C PROV-O", "Which sources each build used, with fingerprints, and the files it made", "https://www.w3.org/TR/prov-o/"),
    ("datapackage.json", "Frictionless Data Package", "Every CSV with its fields and licence", "https://specs.frictionlessdata.io/data-package/"),
    ("sitemap.xml", "Sitemaps protocol", "Every page and file, for search engines and harvesters", "https://www.sitemaps.org/protocol.html")]


def rel_payload():
    """The UK's memberships, treaties and agreements (tools/relations.py), with UK body names resolved, for the nations page."""
    p = ROOT / "data/relations.json"
    if not p.exists(): return None
    o = json.loads(p.read_text())
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    nm = {r[0]: r[1] for r in D["r"]}
    uk = lambda ids: [[i, nm.get(i, i)] for i in ids]
    cp = ROOT / "data/cooperation.json"; coop = json.loads(cp.read_text()) if cp.exists() else None
    return {"read": o["read"], "domains": o["domains"],
            "m": [[m["who"], m["name"], m["status"], m["start"][:4], (m["end"] or "")[:4], m["domain"], uk(m["lead"]), m["site"], m.get("official") or (f"https://www.wikidata.org/wiki/{m['qid']}" if m["qid"] else "")] for m in o["memberships"]],
            "t": [[t["title"], t["url"], t["date"], t["partner"], t["kind"], t["series"], t["domain"], uk(t["uk"]), k] for t, k in zip(o["treaties"], coop["treaty_kind"] if coop else [""] * len(o["treaties"]), strict=True)],
            "a": [[a["title"], a["url"], a["date"], a["form"], a["level"], a["domain"], uk(a["uk"])] for a in o["agreements"]],
            "geo": json.loads((ROOT / "data/worldmap.json").read_text()) if (ROOT / "data/worldmap.json").exists() else None,
            "coop": {k: v for k, v in coop.items() if k != "treaty_kind"} if coop else None}



def build():
    rel = rel_payload()
    intl = json.loads((ROOT / "data/international.json").read_text())
    own = json.loads((ROOT / "data/intl-ownership.json").read_text())
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    nm = {r[0]: r[1] for r in D["r"]}
    leads = sorted({i for r in own["rows"] for i in r.get("uk_lead", [])})
    C = rel["coop"]["countries"]
    stats = [[len(intl["bodies"]), "international bodies with a named UK lead"], [len(rel["m"]), "memberships"], [len(rel["t"]), "treaties"],
             [len(rel["a"]), "memoranda and agreements"], [sum(1 for v in C.values() if v["trade"]), "countries with a trade agreement in effect"],
             [sum(1 for v in C.values() if v["tax"]), "countries with a tax treaty"], [rel["coop"]["commonwealth"]["members"], "Commonwealth members"],
             [len(own["rows"]), "financial institutions where the UK holds shares"]]
    return {"rel": rel, "intl": intl, "own": own, "leads": [[i, nm.get(i, i)] for i in leads], "std": STD, "stats": stats}


def check(p):
    e = []
    if not p["rel"] or len(p["rel"]["t"]) < 1000: e.append("treaties missing")
    if p["stats"][6][0] != 56: e.append("known answer: 56 Commonwealth members")
    if not any(r["short"] == "IBRD" for r in p["own"]["rows"]): e.append("known answer: the UK's IBRD holding")
    if ".hidden=" in PAGE and "#world [hidden]" not in PAGE: e.append("elements hidden by script would still show (OG-D59)")
    for f, *_ in p["std"]:
        if not (ROOT / "docs" / f).exists(): e.append(f"standard file not published: {f}")
    return e


def main():
    p = build()
    if "--negative" in sys.argv:
        bad = json.loads(json.dumps(p)); bad["std"].append(["data/missing.jsonld", "", "", ""]); bad["stats"][6][0] = 55
        if not check(bad): sys.exit("world negative: not caught")
        print("world negative: breakers caught"); return
    e = check(p)
    if e: sys.exit("world: " + "; ".join(e))
    sys.path.insert(0, str(ROOT / "tools")); import design  # noqa: E402
    (ROOT / "docs/world.html").write_text(design.wrap_page(PAGE, "world").replace("__DATA__", json.dumps(p, ensure_ascii=False).replace("</", "<\\/")))
    print("world:", {k: v for v, k in p["stats"]})


if __name__ == "__main__":
    main()
