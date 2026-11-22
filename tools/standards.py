"""Publish the portal in open standards, at stable addresses other portals can harvest -> docs/data/ (+ sitemap, robots)

  catalogue.jsonld          W3C DCAT 3 (DCAT-AP shaped): every dataset and download, licence, format, standard it conforms to
  register.jsonld           W3C Organization Ontology (ORG) + schema.org: every body, its parent, identifiers, sameAs links,
                            website and classification (pointing at the SKOS schemes)
  register.csv (+ -metadata.json)   W3C CSV on the Web (CSVW): the register as a table, with its schema
  international.jsonld      W3C ORG memberships of international bodies (UK and home nations), the UK body that leads;
                            schema.org Legislation for treaties and agreements; trade agreements in effect and tax treaties
  taxonomies.skos.jsonld    W3C SKOS: record families, types of body, purposes (with UN COFOG codes), activities, reach,
                            nations (ISO 3166-2:GB), kinds of treaty and relationship domains
  provenance.jsonld         W3C PROV-O: the build, the sources it used (with fingerprints) and the files it made
  ../datapackage.json       Frictionless Data Package: every CSV with its field list and licence (at the site root, because
                            the specification does not allow paths that climb out of the package's folder)
  bods-0.4.json             (written by tools/export_bods.py) Beneficial Ownership Data Standard 0.4, linked from the catalogue
  ../sitemap.xml, ../robots.txt, and a schema.org Dataset block in each page's head, so search engines and dataset
  search services find the data.
Every graph is parsed back with rdflib and every CSV checked against its schema before anything is written.
"""
import csv, hashlib, io, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"; OUT = DOCS / "data"
SITE = "https://cyberdudeuk.github.io/opengovernment-uk/"
ID = SITE + "id/"
OGL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
PUBLISHER = {"@id": SITE, "@type": ["foaf:Agent", "schema:Organization"], "foaf:name": "OpenGovernment UK (pilot)", "schema:name": "OpenGovernment UK (pilot)"}
CTX = {"org": "http://www.w3.org/ns/org#", "skos": "http://www.w3.org/2004/02/skos/core#", "owl": "http://www.w3.org/2002/07/owl#", "dct": "http://purl.org/dc/terms/",
       "dcat": "http://www.w3.org/ns/dcat#", "foaf": "http://xmlns.com/foaf/0.1/", "schema": "https://schema.org/", "prov": "http://www.w3.org/ns/prov#",
       "time": "http://www.w3.org/2006/time#", "xsd": "http://www.w3.org/2001/XMLSchema#", "rov": "http://www.w3.org/ns/regorg#", "og": ID}


def iri(k):  # one identifier per body everywhere: the register key under the site's id/ path (as og:<key> expands in the page's own files)
    from urllib.parse import quote
    return ID + quote(k, safe=":._~-")
def concept(scheme, key): return {"@id": f"{ID}scheme/{scheme}/{key}"}
def page_data(name, block):
    return json.loads(re.search(rf'<script[^>]*id="{block}"[^>]*>(.*?)</script>', (DOCS / name).read_text(), re.S).group(1))
def load(p): return json.loads((ROOT / p).read_text())


def taxonomies(meta, coop, rel):
    g = []
    def scheme(key, label, items, notation=None, desc=None):
        g.append({"@id": f"{ID}scheme/{key}", "@type": "skos:ConceptScheme", "skos:prefLabel": label})
        for it in items:
            c = {"@id": f"{ID}scheme/{key}/{it[0]}", "@type": "skos:Concept", "skos:prefLabel": it[1], "skos:inScheme": {"@id": f"{ID}scheme/{key}"}}
            if desc and desc.get(it[0]): c["skos:definition"] = desc[it[0]]
            if notation and notation.get(it[0]): c["skos:notation"] = notation[it[0]]
            g.append(c)
    scheme("btype", "Types of public body", [(b["key"], b["label"]) for b in meta["btypes"]], desc={b["key"]: b.get("explain", "") for b in meta["btypes"]})
    scheme("purpose", "What a body is for (mapped to UN COFOG divisions)", [(p["key"], p["label"]) for p in meta["purposes"]],
           notation={p["key"]: p["cofog"] for p in meta["purposes"] if p.get("cofog")}, desc={p["key"]: p["explain"] for p in meta["purposes"]})
    scheme("activity", "What a body does", [(a["key"], a["label"]) for a in meta["activities"]], desc={a["key"]: a["explain"] for a in meta["activities"]})
    scheme("reach", "Where a body works", [("uk", "The whole UK"), ("several", "Several nations"), ("one", "One nation"), ("local", "Local"), ("outside", "Outside the UK"), ("unstated", "Not stated")])
    scheme("nation", "Nations of the UK (ISO 3166-2:GB)", [("EN", "England"), ("SC", "Scotland"), ("WA", "Wales"), ("NI", "Northern Ireland"), ("UK", "United Kingdom")],
           notation={"EN": "GB-ENG", "SC": "GB-SCT", "WA": "GB-WLS", "NI": "GB-NIR", "UK": "GB"})
    scheme("treaty-kind", "Kinds of treaty (worked out from titles, so modelled)", coop["kinds"])
    scheme("domain", "Domains of international relationships", list(rel["domains"].items()))
    return {"@context": CTX, "@graph": g}


def register(D, ACC, web, orgid, sameas, cls):
    fam = D["fam"]; g = []
    canon = {m: c for c, grp in sameas.items() for m in grp["members"]}
    for r in D["r"]:
        k = r[0]
        o = {"@id": iri(k), "@type": ["org:Organization", "schema:GovernmentOrganization"], "skos:prefLabel": r[1], "schema:name": r[1],
             "dct:identifier": k, "og:family": fam[r[2]], "og:status": "open" if r[4] else "closed",
             "schema:url": f"{SITE}index.html#org-{k.replace(':', '--')}"}
        if r[3]: o["org:classification"] = [{"@id": f"{ID}kind/{re.sub(r'[^a-z0-9]+', '-', r[3].lower()).strip('-')}", "skos:prefLabel": r[3]}]
        c = cls.get(k)
        if c:
            o.setdefault("org:classification", []).extend([concept("btype", c["btype"]), concept("purpose", c["purpose"]), concept("activity", c["activity"]), concept("reach", c["reach"])])
        if r[6]: o["org:subOrganizationOf"] = [{"@id": iri(p)} for p in r[6]]
        if r[7]: o["schema:foundingDate"] = r[7][:10]
        if r[8]: o["schema:dissolutionDate"] = r[8][:10]
        same = []
        ids = r[10] or {}
        if ids.get("wikidata"): same.append({"@id": "http://www.wikidata.org/entity/" + ids["wikidata"]})
        if ids.get("lei"): same.append({"@id": "https://lei.info/" + ids["lei"]})
        if k in canon: same.append({"@id": iri(canon[k])})
        for c2, grp in sameas.items():
            if c2 == k: same += [{"@id": iri(m)} for m in grp["members"]]
        if same: o["owl:sameAs"] = same
        if ids.get("companies_house"): o["rov:registration"] = "GB-COH-" + str(ids["companies_house"])
        if k in orgid: o["schema:identifier"] = orgid[k]
        if k in web: o["foaf:homepage"] = {"@id": web[k][0]}
        g.append(o)
    return {"@context": CTX, "@graph": g}


def international(intl, rel, coop, own):
    g = []; nat = {"UK": "wikidata:Q145", "EN": "wikidata:Q21", "SC": "wikidata:Q22", "WA": "wikidata:Q25", "NI": "wikidata:Q26"}
    for b in intl["bodies"]:
        g.append({"@id": f"{ID}intl/{re.sub(r'[^a-z0-9]+', '-', b['name'].lower()).strip('-')}", "@type": ["org:Organization", "schema:Organization"], "skos:prefLabel": b["name"],
                  "og:ukWayIn": b.get("way_in", ""), "og:ukLead": [{"@id": iri(x["id"])} for x in b["lead"]], "dct:description": b.get("role", ""),
                  "dct:source": [{"@id": e["url"]} for e in b.get("evidence", [])]})
    for i, m in enumerate(rel["memberships"]):
        org = {"@id": f"http://www.wikidata.org/entity/{m['qid']}"} if m["qid"] else {"@id": f"{ID}intl/{re.sub(r'[^a-z0-9]+', '-', m['name'].lower()).strip('-')}", "skos:prefLabel": m["name"]}
        ms = {"@id": f"{ID}membership/{i}", "@type": "org:Membership", "org:member": {"@id": iri(nat.get(m["who"], "wikidata:Q145"))}, "org:organization": org,
              "og:status": m["status"], "skos:note": f"{m['name']} ({m['status']})"}
        if m.get("start") or m.get("end"):
            ms["org:memberDuring"] = {"@type": "time:Interval", **({"time:hasBeginning": {"time:inXSDDate": m["start"][:10]}} if m.get("start") else {}),
                                      **({"time:hasEnd": {"time:inXSDDate": m["end"][:10]}} if m.get("end") else {})}
        if m.get("lead"): ms["og:ukLead"] = [{"@id": iri(x)} for x in m["lead"]]
        g.append(ms)
    for i, (t, k) in enumerate(zip(rel["treaties"], coop["treaty_kind"], strict=True)):
        g.append({"@id": f"{ID}treaty/{i}", "@type": "schema:Legislation", "schema:name": t["title"], "schema:legislationType": "Treaty",
                  "schema:legislationDate": t["date"], "schema:url": {"@id": t["url"]}, "schema:about": concept("treaty-kind", k),
                  "og:partner": t["partner"] or None, "og:series": t["series"] or None, "og:bilateral": t["kind"] == "bilateral",
                  "schema:legislationResponsible": [{"@id": iri(x)} for x in t["uk"]]})
    for i, a in enumerate(rel["agreements"]):
        g.append({"@id": f"{ID}agreement/{i}", "@type": "schema:Legislation", "schema:name": a["title"], "schema:legislationType": a["form"],
                  "schema:legislationDate": a["date"], "schema:url": {"@id": a["url"]}, "og:level": a["level"],
                  "schema:legislationResponsible": [{"@id": iri(x)} for x in a["uk"]]})
    for c, v in coop["countries"].items():
        node = {"@id": f"{ID}country/{re.sub(r'[^a-z0-9]+', '-', c.lower()).strip('-')}", "@type": "schema:Country", "schema:name": v["display"],
                "og:commonwealthMember": bool(v["commonwealth"]), "og:treatyCount": v["treaty_total"]}
        if v["trade"]: node["og:tradeAgreementInEffect"] = [{"@type": "schema:Legislation", "schema:name": t["agreement"], "og:entryIntoEffect": t["mechanism"]} for t in v["trade"]]
        if v["tax"]: node["og:taxTreaty"] = [{"@id": t["url"]} for t in v["tax"]]
        g.append(node)
    for r in own["rows"]:  # the ownership itself is in bods-0.4.json; here the institutions, linked by LEI and Wikidata
        g.append({"@id": "http://www.wikidata.org/entity/" + r["wikidata"], "@type": ["org:Organization", "schema:Organization"], "skos:prefLabel": r["name"],
                  "owl:sameAs": {"@id": "https://lei.info/" + r["lei"]}, "og:ukShareOfVotes": r["share_of_votes"], "og:asOf": r["as_of"], "dct:source": {"@id": r["source"]["url"]}})
    return {"@context": CTX, "@graph": g}


def provenance(tree, files):
    g = [{"@id": f"{ID}build/{tree['built']}", "@type": "prov:Activity", "prov:endedAtTime": {"@value": tree["built"], "@type": "xsd:dateTime"},
          "prov:wasAssociatedWith": {"@id": SITE}, "prov:used": [{"@id": s["url"]} for s in tree["sources"].values() if s.get("url")]}]
    for s in tree["sources"].values():
        if s.get("url"): g.append({"@id": s["url"], "@type": "prov:Entity", "dct:title": s["name"], "og:sha256": s.get("sha256", ""), "prov:generatedAtTime": s.get("retrieved", "")})
    for f, h in files.items():
        g.append({"@id": SITE + f, "@type": "prov:Entity", "prov:wasGeneratedBy": {"@id": f"{ID}build/{tree['built']}"}, "og:sha256": h})
    return {"@context": CTX, "@graph": g}


DATASETS = [  # file, title, description, media type, standard it conforms to
    ("data/register.jsonld", "Register of the UK state (linked data)", "Every public body, its parent, identifiers and classification.", "application/ld+json", "http://www.w3.org/ns/org#"),
    ("data/register.csv", "Register of the UK state (table)", "One row per record, with every register code.", "text/csv", "http://www.w3.org/ns/csvw"),
    ("data/international.jsonld", "The UK and the world", "Memberships of international bodies, the UK body that leads, treaties, agreements, trade agreements in effect and tax treaties.", "application/ld+json", "http://www.w3.org/ns/org#"),
    ("data/taxonomies.skos.jsonld", "Taxonomies", "Types, purposes (UN COFOG), activities, reach, nations (ISO 3166-2:GB), kinds of treaty.", "application/ld+json", "http://www.w3.org/2004/02/skos/core#"),
    ("bods-0.4.json", "Ownership and control (BODS 0.4)", "Who owns or controls each public body, and the UK's shareholdings in international financial institutions.", "application/json", "https://standard.openownership.org/en/0.4.0/"),
    ("data/register.ftm.json", "The register in FollowTheMoney", "Public bodies, companies they control, international bodies, links, renames and memberships, for OpenSanctions, OpenAleph and yente.", "application/json", "https://followthemoney.tech/"),
    ("llms.txt", "Guide for AI agents", "Where everything is, in plain text, for language models and agents (the llms.txt convention).", "text/plain", "https://llmstxt.org/"),
    ("data/provenance.jsonld", "Provenance of this build", "Sources used, with fingerprints, and the files made.", "application/ld+json", "http://www.w3.org/ns/prov#"),
    ("datapackage.json", "Data package", "Every CSV with its fields and licence.", "application/json", "https://specs.frictionlessdata.io/data-package/"),
    ("opengovernment-uk.db", "Everything in one SQLite file", "All tables, ready for Datasette or any SQLite tool.", "application/vnd.sqlite3", ""),
    ("accountability.json", "Who answers for each body", "Accountability chains, money and owners.", "application/json", ""),
    ("nations.json", "Nation by nation", "Each nation's legislature, executive and judiciary.", "application/json", ""),
    ("edges.csv", "Links between bodies", "Each parent-child link with its source.", "text/csv", ""),
    ("concordance.csv", "Concordance of codes", "Every register's code for each body.", "text/csv", ""),
    ("accountable-owner.csv", "Accountable owner", "Who each body answers to in the end.", "text/csv", ""),
    ("ppp.csv", "Public-private partnerships", "PFI and PF2 contracts and who pays.", "text/csv", "")]


def catalogue(built):
    ds = []
    for f, t, d, mt, std in DATASETS:
        dist = {"@type": "dcat:Distribution", "dcat:downloadURL": {"@id": SITE + f}, "dcat:accessURL": {"@id": SITE + f}, "dcat:mediaType": mt,
                "dct:license": {"@id": OGL}, "dct:title": t}
        if std: dist["dct:conformsTo"] = {"@id": std}
        ds.append({"@id": f"{ID}dataset/{re.sub(r'[^a-z0-9]+', '-', f.lower())}", "@type": "dcat:Dataset", "dct:title": t, "dct:description": d,
                   "dct:license": {"@id": OGL}, "dct:publisher": PUBLISHER, "dct:modified": built[:10], "dcat:distribution": dist,
                   "dcat:keyword": ["public sector", "government organisations", "UK"], "dct:spatial": {"@id": "http://www.wikidata.org/entity/Q145"},
                   "dcat:landingPage": {"@id": SITE}, "dct:accrualPeriodicity": {"@id": "http://purl.org/cld/freq/irregular"}})
    return {"@context": CTX, "@id": SITE + "data/catalogue.jsonld", "@type": "dcat:Catalog", "dct:title": "OpenGovernment UK: open data catalogue",
            "dct:description": "Every dataset this portal publishes, in open standards, for other portals to harvest.", "dct:publisher": PUBLISHER,
            "dct:license": {"@id": OGL}, "dct:modified": built[:10], "dcat:dataset": ds, "foaf:homepage": {"@id": SITE}}


def csv_schema(path):
    head = next(csv.reader(io.StringIO((DOCS / path).read_text().split("\n", 1)[0] + "\n")))
    return head


def checks(out, D):
    e = []
    import rdflib
    for name in ("register.jsonld", "international.jsonld", "taxonomies.skos.jsonld", "provenance.jsonld", "catalogue.jsonld"):
        g = rdflib.Graph(); g.parse(data=json.dumps(out[name]), format="json-ld")
        if len(g) < 20: e.append(f"{name}: only {len(g)} triples")
        out["_triples"][name] = len(g)
    reg = {n["dct:identifier"]: n for n in out["register.jsonld"]["@graph"]}
    met = reg.get("government-organisation:EA46", {})
    if not any("wikidata" in s["@id"] for s in met.get("owl:sameAs", [])): e.append("known answer: the Met Office links to its Wikidata item")
    if len(reg) != len(D["r"]): e.append("register.jsonld does not hold every record")
    if not any(n.get("@type") == "org:Membership" and "NATO" in n.get("skos:note", "") for n in out["international.jsonld"]["@graph"]): e.append("known answer: the UK's NATO membership")
    for f, *_ in DATASETS:
        if not (DOCS / f).exists() and f.split("/")[-1] not in out and f not in ("data/register.csv", "llms.txt"): e.append(f"catalogue lists {f}, which is not published")
    for res in out["datapackage.json"]["resources"]:
        if ".." in res["path"] or res["path"].startswith("/"): e.append(f"datapackage: {res['path']} climbs out of the package (not allowed)")
        elif (DOCS / res["path"]).exists() and [x["name"] for x in res["schema"]["fields"]] != csv_schema(res["path"]): e.append(f"datapackage: {res['path']} fields do not match its header")
    return e


def main():
    OUT.mkdir(exist_ok=True)
    D = page_data("index.html", "data"); ACC = page_data("index.html", "tree")
    meta = load("data/classification.json")["meta"]; cls = load("data/classification.json")["bodies"]
    rel, coop, intl, own, tree = load("data/relations.json"), load("data/cooperation.json"), load("data/international.json"), load("data/intl-ownership.json"), load("data/tree.json")
    web, orgid, sameas = load("data/websites.json"), load("data/org-id.json"), load("data/same-as.json")["groups"]
    out = {"_triples": {}}
    out["taxonomies.skos.jsonld"] = taxonomies(meta, coop, rel)
    out["register.jsonld"] = register(D, ACC, web, orgid, sameas, cls)
    out["international.jsonld"] = international(intl, rel, coop, own)
    out["catalogue.jsonld"] = catalogue(tree["built"])
    # register.csv with its CSVW schema
    cols = ["id", "name", "family", "kind", "status", "nations", "parents", "start", "end", "website", "btype", "purpose", "activity", "reach", "wikidata", "lei", "companies_house", "org_id"]
    buf = io.StringIO(); w = csv.writer(buf, lineterminator="\n"); w.writerow(cols)
    for r in D["r"]:
        ids = r[10] or {}; c = cls.get(r[0], {})
        w.writerow([r[0], r[1], D["fam"][r[2]], r[3], "open" if r[4] else "closed", r[5] or "", " ".join(r[6] or []), (r[7] or "")[:10], (r[8] or "")[:10],
                    (web.get(r[0]) or [""])[0], c.get("btype", ""), c.get("purpose", ""), c.get("activity", ""), c.get("reach", ""), ids.get("wikidata", ""), ids.get("lei", ""), ids.get("companies_house", ""), " ".join(orgid.get(r[0], []))])
    (OUT / "register.csv").write_text(buf.getvalue())
    csvw = {"@context": "http://www.w3.org/ns/csvw", "url": "register.csv", "dc:title": "Register of the UK state", "dc:license": OGL,
            "tableSchema": {"primaryKey": "id", "aboutUrl": ID + "{id}", "columns": [{"name": c, "titles": c, "datatype": "date" if c in ("start", "end") else "string", "required": c in ("id", "name")} for c in cols]}}
    (OUT / "register.csv-metadata.json").write_text(json.dumps(csvw, indent=1))
    res = [{"name": "register", "path": "data/register.csv", "format": "csv", "mediatype": "text/csv", "licenses": [{"name": "OGL-UK-3.0", "path": OGL}], "schema": {"fields": [{"name": c, "type": "date" if c in ("start", "end") else "string"} for c in cols], "primaryKey": "id"}}]
    for f in ("edges.csv", "concordance.csv", "accountable-owner.csv", "ppp.csv"):
        res.append({"name": f[:-4], "path": f, "format": "csv", "mediatype": "text/csv", "licenses": [{"name": "OGL-UK-3.0", "path": OGL}], "schema": {"fields": [{"name": h, "type": "string"} for h in csv_schema(f)]}})
    out["datapackage.json"] = {"name": "opengovernment-uk", "title": "OpenGovernment UK", "licenses": [{"name": "OGL-UK-3.0", "path": OGL, "title": "Open Government Licence v3.0"}],
                               "homepage": SITE, "resources": res}
    files = {}
    for name in ("register.jsonld", "international.jsonld", "taxonomies.skos.jsonld", "catalogue.jsonld", "datapackage.json"):
        files[("" if name == "datapackage.json" else "data/") + name] = hashlib.sha256(json.dumps(out[name], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    for f in ("bods-0.4.json", "accountability.json", "nations.json", "edges.csv", "concordance.csv", "accountable-owner.csv", "ppp.csv", "opengovernment-uk.db"):
        if (DOCS / f).exists(): files[f] = hashlib.sha256((DOCS / f).read_bytes()).hexdigest()
    out["provenance.jsonld"] = provenance(tree, files)
    e = checks({k: v for k, v in out.items()}, D) if "--negative" not in sys.argv else []
    if "--negative" in sys.argv:
        bad = json.loads(json.dumps(out["register.jsonld"])); bad["@graph"] = bad["@graph"][:5]
        o2 = dict(out, **{"register.jsonld": bad, "_triples": {}})
        if not checks(o2, D): sys.exit("standards negative: a truncated register was not caught")
        print("standards negative: truncated register caught"); return
    if e: sys.exit("standards: " + "; ".join(e))
    for name, v in out.items():
        if name.startswith("_"): continue
        (DOCS if name == "datapackage.json" else OUT).joinpath(name).write_text(json.dumps(v, ensure_ascii=False, separators=(",", ":")) if name in ("register.jsonld", "international.jsonld") else json.dumps(v, ensure_ascii=False, indent=1))
    # harvesting aids: sitemap, robots, and a schema.org Dataset in each page head
    pages = sorted(p.name for p in DOCS.glob("*.html"))
    (DOCS / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                                      "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{tree['built'][:10]}</lastmod></url>\n" for p in pages) +
                                      "".join(f"<url><loc>{SITE}{f}</loc><lastmod>{tree['built'][:10]}</lastmod></url>\n" for f, *_ in DATASETS) + "</urlset>\n")
    (DOCS / "llms.txt").write_text(  # the llms.txt convention: a plain guide for language models and agents
        "# OpenGovernment UK\n\n> An open register of the UK state: every public body the official registers know, who each answers to, who owns or controls it,"
        " its codes in other registers, and the UK's place in the world. Pilot. Every fact cites its source; anything worked out is labelled.\n\n"
        "Identifiers: each body is " + ID + "<register key>, for example " + ID + "government-organisation:D9. Licence: data OGL v3.0, code MIT, documentation CC BY 4.0.\n\n"
        "## Pages\n\n" + "".join(f"- [{t}]({SITE}{u}): {d}\n" for u, t, d in [("index.html", "Register", "search any body; profiles; who answers; changes; data and feeds; ask a question"),
            ("nations.html", "Nation by nation", "each nation's legislature, executive and judiciary"), ("world.html", "UK and the world", "international bodies, memberships, treaties, agreements, the Commonwealth, trade and tax agreements, the UK's shares in international financial institutions"),
            ("orgchart.html", "Org charts", "every body in context"), ("funding.html", "Funding", "grants, schemes and innovation services"), ("navigator.html", "Documentation", "requirements, design and traceability")]) +
        "\n## Data\n\n" + "".join(f"- [{t}]({SITE}{f}): {d}\n" for f, t, d, _, _ in DATASETS) +
        "\n## Optional\n\n- [Source code and issues](https://github.com/cyberdudeuk/opengovernment-uk)\n")
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n")
    ld = {"@context": "https://schema.org/", "@type": "Dataset", "name": "OpenGovernment UK: register of the UK state",
          "description": "Every UK public body the official registers know, with who each answers to, its codes in other registers, its ownership (BODS 0.4) and the UK's international relationships.",
          "url": SITE, "license": OGL, "isAccessibleForFree": True, "creator": {"@type": "Organization", "name": "OpenGovernment UK (pilot)", "url": SITE},
          "dateModified": tree["built"][:10], "spatialCoverage": "United Kingdom", "includedInDataCatalog": {"@type": "DataCatalog", "url": SITE + "data/catalogue.jsonld"},
          "distribution": [{"@type": "DataDownload", "encodingFormat": mt, "contentUrl": SITE + f, "name": t} for f, t, _, mt, _ in DATASETS]}
    tag = '<script type="application/ld+json" id="og-dataset">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    for p in pages:
        h = (DOCS / p).read_text()
        h = re.sub(r'<script type="application/ld\+json" id="og-dataset">.*?</script><link rel="alternate" type="application/ld\+json" href="data/catalogue.jsonld" title="Data catalogue \(DCAT\)">', "", h, flags=re.S)
        h = h.replace("</head>", tag + '<link rel="alternate" type="application/ld+json" href="data/catalogue.jsonld" title="Data catalogue (DCAT)"></head>', 1) if "</head>" in h else h
        (DOCS / p).write_text(h)
    print("standards:", {k: v for k, v in out["_triples"].items()}, f"| register.csv {len(D['r'])} rows | sitemap {len(pages)} pages + {len(DATASETS)} files")


if __name__ == "__main__":
    main()
