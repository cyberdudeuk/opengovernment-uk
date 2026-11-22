"""The Crown Dependencies' and Overseas Territories' own public bodies, by jurisdiction and branch of the state.

One record per body, combining every source that names it:
  - the territory's constitution or founding Order in Council on legislation.gov.uk (the establishing clause is quoted and
    must be found in sources/evidence/territory-instruments.json, which carries each order's fingerprint);
  - the body's own or its government's official website, where the page was read and named the body;
  - Wikidata (community-sourced, CC0): legislature, executive and court links, other public bodies, and official websites.
Nothing is inferred from a name alone: a constitutional body needs its clause; any other body needs a Wikidata record whose
class is a public-sector class. Bodies whose website no longer answers are kept and flagged, not dropped.
Writes data/territories.json. --negative proves the checks fail when they should."""
import collections, copy, json, pathlib, re, sys, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]; EV = ROOT / "sources/evidence"
L = "https://www.legislation.gov.uk/"
JCPC = {"title": "Judicial Committee of the Privy Council: final court of appeal for the UK overseas territories and Crown dependencies", "url": "https://www.jcpc.uk/"}
MOJ = {"title": "GOV.UK: the Ministry of Justice manages the UK's constitutional relationship with the Crown Dependencies", "url": "https://www.gov.uk/government/publications/crown-dependencies-jersey-guernsey-and-the-isle-of-man"}
# jurisdiction code -> (name, OT or CD, register id, founding order key or None)
JUR = {
    "JE": ("Jersey", "CD", "wikidata:Q116785235", None), "GG": ("Guernsey", "CD", "wikidata:Q25230", None),
    "GG-ALD": ("Alderney (Bailiwick of Guernsey)", "CD", "wikidata:Q25230", None), "GG-SRK": ("Sark (Bailiwick of Guernsey)", "CD", "wikidata:Q25230", None),
    "IM": ("Isle of Man", "CD", "wikidata:Q9676", None),
    "AI": ("Anguilla", "OT", "wikidata:Q25228", "uksi-1982-334"), "BM": ("Bermuda", "OT", "wikidata:Q23635", "uksi-1968-182"),
    "VG": ("British Virgin Islands", "OT", "wikidata:Q25305", "uksi-2007-1678"), "KY": ("Cayman Islands", "OT", "wikidata:Q5785", "uksi-2009-1379"),
    "FK": ("Falkland Islands", "OT", "wikidata:Q9648", "uksi-2008-2846"), "GI": ("Gibraltar", "OT", "wikidata:Q1410", None),
    "MS": ("Montserrat", "OT", "wikidata:Q13353", "uksi-2010-2474"), "PN": ("Pitcairn Islands", "OT", "wikidata:Q35672", "uksi-2010-244"),
    "SH": ("St Helena", "OT", "wikidata:Q192184", "uksi-2009-1751"), "SH-AC": ("Ascension", "OT", "wikidata:Q192184", "uksi-2009-1751"),
    "SH-TA": ("Tristan da Cunha", "OT", "wikidata:Q192184", "uksi-2009-1751"), "TC": ("Turks and Caicos Islands", "OT", "wikidata:Q18221", "uksi-2011-1681"),
    "GS": ("South Georgia and the South Sandwich Islands", "OT", "wikidata:Q35086", "uksi-1985-449"), "AQ-BAT": ("British Antarctic Territory", "OT", "wikidata:Q165783", "uksi-1989-842"),
    "IO": ("British Indian Ocean Territory", "OT", "wikidata:Q43448", "uksi-1976-893"), "SBA": ("Akrotiri and Dhekelia (Sovereign Base Areas)", "OT", "wikidata:Q37362", "uksi-1960-1369"),
}
JNOTES = {"IO": "A treaty signed in May 2025 would transfer sovereignty over the Chagos Archipelago to Mauritius, with the UK keeping the base on Diego Garcia. It is not in force: the UK's enabling legislation ran out of time in Parliament in 2026. Until it is, this remains a UK Overseas Territory.",
          "GI": "Gibraltar's Constitution Order 2006 is not published on legislation.gov.uk, so its bodies here rest on Wikidata and official websites."}
JNOTE_SRC = {"IO": [{"title": "GOV.UK: UK/Mauritius Agreement concerning the Chagos Archipelago including Diego Garcia (May 2025)", "url": "https://www.gov.uk/government/publications/ukmauritius-agreement-concerning-the-chagos-archipelago-including-diego-garcia-cs-mauritius-no12025"},
                    {"title": "Chatham House, January 2026: Lords debate on ratification delayed", "url": "https://www.chathamhouse.org/2026/01/uk-ratification-chagos-archipelago-treaty-will-not-violate-international-law"}]}
# Constitutional and apex bodies: (jurisdiction, name, branch, kind, clause that must appear in the order's evidence or None, Wikidata ids, formerly, official evidence key)
C = [
    ("AI", "House of Assembly", "legislature", "legislature", "House of Assembly for Anguilla", ["Q4763974"], None, None),
    ("AI", "Executive Council", "executive", "government", "Executive Council in and for Anguilla", ["Q107770622"], None, None),
    ("AI", "Governor of Anguilla", "executive", "crown", "Governor of Anguilla", [], None, None),
    ("AI", "Eastern Caribbean Supreme Court (High Court and Court of Appeal)", "judiciary", "court", None, ["Q3001122"], None, "ecsc"),
    ("BM", "Parliament of Bermuda", "legislature", "legislature", "Legislature for Bermuda", ["Q7138929"], None, None),
    ("BM", "Cabinet", "executive", "government", "Executive Council for Bermuda", ["Q107979988"], "Executive Council (the 1968 order's name)", None),
    ("BM", "Governor of Bermuda", "executive", "crown", "Governor and Commander-in-Chief of Bermuda", [], None, None),
    ("BM", "Supreme Court of Bermuda", "judiciary", "court", "Supreme Court for Bermuda", ["Q113006163"], None, None),
    ("BM", "Court of Appeal for Bermuda", "judiciary", "court", "Court of Appeal for Bermuda", [], None, None),
    ("BM", "Public Service Commission", "executive", "commission", "Public Service Commission for Bermuda", [], None, None),
    ("VG", "House of Assembly", "legislature", "legislature", "Her Majesty and a House of Assembly", ["Q5914704"], None, None),
    ("VG", "Cabinet", "executive", "government", "Cabinet in and for the Virgin Islands", ["Q16825166"], None, None),
    ("VG", "Governor of the Virgin Islands", "executive", "crown", "Governor of the Virgin Islands", [], None, None),
    ("VG", "Eastern Caribbean Supreme Court (High Court and Court of Appeal)", "judiciary", "court", None, ["Q3001122"], None, "ecsc"),
    ("VG", "Director of Public Prosecutions", "executive", "office", "Director of Public Prosecutions", [], None, None),
    ("VG", "Auditor General", "executive", "office", "Auditor General", [], None, None),
    ("VG", "Complaints Commissioner", "executive", "office", "Complaints Commissioner", [], None, None),
    ("KY", "Parliament of the Cayman Islands", "legislature", "legislature", "Her Majesty and a Legislative Assembly", ["Q3625554"], "Legislative Assembly (the 2009 order's name; renamed Parliament)", None),
    ("KY", "Cabinet", "executive", "government", "Cabinet in and for the Cayman Islands", [], None, None),
    ("KY", "Governor of the Cayman Islands", "executive", "crown", "Governor of the Cayman Islands", [], None, None),
    ("KY", "Grand Court", "judiciary", "court", "Grand Court", [], None, None),
    ("KY", "Court of Appeal", "judiciary", "court", "Court of Appeal", [], None, None),
    ("KY", "Director of Public Prosecutions", "executive", "office", "Director of Public Prosecutions", [], None, None),
    ("KY", "Auditor General", "executive", "office", "Auditor General", [], None, None),
    ("KY", "Public Accounts Committee", "legislature", "committee", "Public Accounts Committee", [], None, None),
    ("FK", "Legislative Assembly", "legislature", "legislature", "Legislative Assembly for the Falkland Islands", ["Q3365321"], None, None),
    ("FK", "Executive Council", "executive", "government", "Executive Council", ["Q5419832"], None, None),
    ("FK", "Governor of the Falkland Islands", "executive", "crown", "Governor of the Falkland Islands", [], None, None),
    ("FK", "Supreme Court", "judiciary", "court", "Supreme Court", ["Q133255547"], None, None),
    ("FK", "Court of Appeal", "judiciary", "court", "Court of Appeal", [], None, None),
    ("FK", "Public Accounts Committee", "legislature", "committee", "Public Accounts Committee", [], None, None),
    ("MS", "Legislative Assembly", "legislature", "legislature", "Legislature", ["Q21029427"], None, None),
    ("MS", "Cabinet", "executive", "government", "Cabinet in and for Montserrat", ["Q109849522"], None, None),
    ("MS", "Governor of Montserrat", "executive", "crown", "Governor of Montserrat", [], None, None),
    ("MS", "National Advisory Council", "executive", "commission", "National Advisory Council for Montserrat", [], None, None),
    ("MS", "Electoral Commission", "executive", "commission", "Electoral Commission for Montserrat", [], None, None),
    ("MS", "Public Service Commission", "executive", "commission", "Public Service Commission for Montserrat", [], None, None),
    ("MS", "Auditor-General", "executive", "office", "Auditor-General for Montserrat", [], None, None),
    ("MS", "Complaints Commission", "executive", "office", "Complaints Commission for Montserrat", [], None, None),
    ("MS", "Director of Public Prosecutions", "executive", "office", "Director of Public Prosecutions for Montserrat", [], None, None),
    ("MS", "Eastern Caribbean Supreme Court (High Court and Court of Appeal)", "judiciary", "court", None, ["Q3001122"], None, "ecsc"),
    ("PN", "Island Council", "legislature", "legislature", "Island Council for Pitcairn", ["Q6083065"], None, None),
    ("PN", "Governor of Pitcairn", "executive", "crown", "Governor of Pitcairn", [], None, None),
    ("PN", "Supreme Court", "judiciary", "court", "Supreme Court for Pitcairn", ["Q7645015"], None, None),
    ("PN", "Court of Appeal", "judiciary", "court", "Court of Appeal for Pitcairn", [], None, None),
    ("SH", "Legislative Council", "legislature", "legislature", "Legislature for St Helena", ["Q6518247"], None, None),
    ("SH", "Executive Council", "executive", "government", "Executive Council for St Helena", [], None, None),
    ("SH", "Governor of St Helena", "executive", "crown", "Governor of St Helena", [], None, None),
    ("SH", "Supreme Court", "judiciary", "court", "Supreme Court for St Helena", [], None, None),
    ("SH", "Court of Appeal", "judiciary", "court", "Court of Appeal for St Helena", [], None, None),
    ("SH", "Judicial Service Commission", "judiciary", "commission", "Judicial Service Commission for St Helena", [], None, None),
    ("SH", "Chief Auditor", "executive", "office", "Chief Auditor for St Helena", [], None, None),
    ("SH-AC", "Island Council", "legislature", "legislature", "Island Council for Ascension", ["Q4803835"], None, None),
    ("SH-AC", "Administrator of Ascension", "executive", "crown", "Administrator of Ascension", [], None, None),
    ("SH-AC", "Ascension Judicial Service Commission", "judiciary", "commission", "Ascension Judicial Service Commission", [], None, None),
    ("SH-TA", "Island Council", "legislature", "legislature", "Island Council for Tristan", ["Q7844151"], None, None),
    ("SH-TA", "Administrator of Tristan da Cunha", "executive", "crown", "Administrator of Tristan", [], None, None),
    ("TC", "Parliament of the Turks and Caicos Islands", "legislature", "legislature", "Her Majesty and a Parliament", ["Q7855481"], None, None),
    ("TC", "Cabinet", "executive", "government", "Cabinet for the Turks and Caicos Islands", ["Q5015586"], None, None),
    ("TC", "Governor of the Turks and Caicos Islands", "executive", "crown", "Governor of the Turks and Caicos Islands", [], None, None),
    ("TC", "Supreme Court", "judiciary", "court", "Supreme Court", [], None, None),
    ("TC", "Court of Appeal", "judiciary", "court", "Court of Appeal", [], None, None),
    ("TC", "Judicial Service Commission", "judiciary", "commission", "Judicial Service Commission", [], None, None),
    ("TC", "Public Service Commission", "executive", "commission", "Public Service Commission", [], None, None),
    ("TC", "Police and Defence Service Commission", "executive", "commission", "Police and Defence Service Commission", [], None, None),
    ("TC", "Public Accounts Committee", "legislature", "committee", "Public Accounts Committee", [], None, None),
    ("GS", "Commissioner for South Georgia and the South Sandwich Islands", "executive", "crown", "Commissioner for the Territories", [], None, None),
    ("GS", "Supreme Court", "judiciary", "court", "Supreme Court", [], None, None),
    ("AQ-BAT", "Commissioner for the British Antarctic Territory", "executive", "crown", "Commissioner for the Territory", [], None, None),
    ("IO", "Commissioner for the British Indian Ocean Territory", "executive", "crown", "Commissioner for the Territory", [], None, None),
    ("SBA", "Administrator of the Sovereign Base Areas", "executive", "crown", "Administrator of the Sovereign Base Areas", [], None, None),
    # Gibraltar and the Crown Dependencies: no UK founding order; Wikidata's own legislature, executive and court links, and official pages
    ("GI", "Parliament of Gibraltar", "legislature", "legislature", None, ["Q128852"], None, "wd-legis"),
    ("GI", "Government of Gibraltar", "executive", "government", None, ["Q128986", "Q107803249"], None, "wd"),
    ("GI", "Courts of Gibraltar", "judiciary", "court", None, ["Q169857"], None, "wd"),
    ("JE", "States Assembly", "legislature", "legislature", None, ["Q946944"], None, "wd-legis"),
    ("JE", "Government of Jersey (Council of Ministers)", "executive", "government", None, ["Q61747417", "Q5060027"], None, "je-gov"),
    ("JE", "Royal Court of Jersey", "judiciary", "court", None, ["Q111950877", "Q5178728"], None, "wd"),
    ("JE", "Court of Appeal of Jersey", "judiciary", "court", None, ["Q141255105"], None, "wd"),
    ("GG", "States of Guernsey (States of Deliberation)", "legislature", "legislature", None, ["Q1368324"], None, "gg-parliament"),
    ("GG", "Policy & Resources Committee", "executive", "government", None, ["Q27958235"], None, "wd"),
    ("GG", "Royal Court of Guernsey", "judiciary", "court", None, ["Q21995547"], None, "gg-courts"),
    ("GG-ALD", "States of Alderney", "legislature", "legislature", None, ["Q7604031"], None, "wd-legis"),
    ("GG-SRK", "Chief Pleas", "legislature", "legislature", None, ["Q9189683"], None, "wd-legis"),
    ("IM", "Tynwald", "legislature", "legislature", None, ["Q827704"], None, "wd-legis"),
    ("IM", "House of Keys", "legislature", "legislature", None, ["Q1516957"], None, "wd"),
    ("IM", "Legislative Council", "legislature", "legislature", None, ["Q679687"], None, "wd"),
    ("IM", "Isle of Man Government (Council of Ministers)", "executive", "government", None, ["Q3112593", "Q2993842"], None, "wd"),
    ("IM", "High Court of Justice of the Isle of Man", "judiciary", "court", None, [], None, "im-courts"),
    ("IM", "Staff of Government Division (appeal court)", "judiciary", "court", None, [], None, "im-courts"),
]
OFFICIAL = {  # pages read on 22 November 2026; each named the body (see sources/evidence/territory-official-pages.json)
    "je-gov": ("Government of Jersey: Council of Ministers", "https://www.gov.je/Government/Pages/default.aspx"),
    "gg-parliament": ("States of Guernsey: States of Deliberation", "https://www.gov.gg/parliament"),
    "gg-courts": ("Royal Court of Guernsey", "https://www.guernseyroyalcourt.gg/"),
    "im-courts": ("Isle of Man Courts of Justice: High Court, Deemsters, Staff of Government Division", "https://www.courts.im/"),
    "ecsc": ("Eastern Caribbean Supreme Court; The Anguilla, Montserrat and Virgin Islands (Supreme Court) Order 2000", L + "uksi/2000/3060/contents/made"),
}
KIND = {"legislature": ("legislature", "Parliament or assembly"), "committee": ("legislature", "Parliament or assembly"), "government": ("department", "Government department"),
        "crown": ("territory", "The Crown's representative"), "court": ("court", "Court or tribunal"), "commission": ("ndpb", "Arm's-length public body"), "office": ("ndpb", "Arm's-length public body")}
ACT = {"legislature": "legislate", "committee": "inspect", "government": "policy", "crown": "policy", "court": "judge", "commission": "regulate", "office": "inspect"}


def wd_kind(cls, name):
    c = " ".join(cls).lower()
    if re.search(r"legislat|parliament", c): return "legislature", "legislature", "legislate"
    if re.search(r"court|judiciary", c): return "judiciary", "court", "judge"
    if re.search(r"parish|municipal|local", c): return "executive", "council", "services"
    if re.search(r"ministry|department|government service|executive branch|^government$", c) or re.match(r"(Ministry|Department) ", name): return "executive", "department", "policy" if re.match(r"Ministry", name) else "services"
    if re.search(r"central bank|monetary|regulat|financial services|commission|data protection|aviation authority", c) or re.search(r"Commission|Authority|Regulat", name): return "executive", "ndpb", "regulate"
    if re.search(r"postal|post office|state-owned", c): return "executive", "corporation", "trade"
    if re.search(r"police|fire|hospital|disaster|health", c): return "executive", "agency", "services"
    if re.search(r"museum|archive", c): return "executive", "agency", "collections"
    if re.search(r"registr", c + name.lower()): return "executive", "agency", "records"
    return "executive", "agency", "services"


def confirmed(w):
    """A Wikidata-only body counts as current when its own website answers at the recorded address, or redirects to a site carrying its own name."""
    if w.get("site_status") != 200: return False
    if re.search(r"error|not found|404|page cannot|does not exist|no longer|request rejected|access denied", w.get("site_title") or "", re.I): return False  # a retired address answering with an error page, or a site that refused the check: fail closed
    if w.get("site_confirms"): return True
    host = urllib.parse.urlparse(w.get("site_final") or "").netloc.lower()
    toks = [t for t in re.findall(r"[a-z]+", w["name"].lower()) if len(t) >= 5 and t not in ("saint", "islands", "island", "government", "department")]
    return any(t in host for t in toks)


EXCLUDE_CLS = re.compile(r"hospital", re.I)  # Wikidata doesn't say whether a hospital is public or private


def norm(s): return re.sub(r"[^a-z0-9]+", " ", re.sub(r"^the ", "", s.lower())).strip()


def build():
    sys.path.insert(0, str(ROOT / "tools")); import classify
    ins = json.loads((EV / "territory-instruments.json").read_text())["orders"]
    wd = json.loads((EV / "territory-wikidata.json").read_text())["bodies"]
    off = {k: v for k, v in json.loads((EV / "territory-official-pages.json").read_text()).items() if k != "about"}
    BT = {k: lab for k, lab, _ in classify.BTYPES}; BT.update({"legislature": "Parliament or assembly", "territory": "The Crown's representative"})
    bodies, used_wd, problems = [], set(), []
    for j, name, br, kind, clause, qids, formerly, offk in C:
        jn, grp, reg, order = JUR[j]
        srcs = []
        if clause:
            o = ins.get(order)
            hit = next((c for c in (o or {}).get("clauses", []) if clause in c), None)
            if not hit: problems.append(f"clause not found: {j} {name}: {clause!r}"); continue
            srcs.append({"kind": "founding order", "title": o["title"], "url": o["url"], "quote": hit[:180], "read_as": o["read_as"]})
        if offk in OFFICIAL:
            t, u = OFFICIAL[offk]
            if offk in off and not any(off[offk]["found"].values()): problems.append(f"official page doesn't name the body: {offk}")
            srcs.append({"kind": "official", "title": t, "url": u})
        site = ""
        for q in qids:
            w = wd.get(q)
            srcs.append({"kind": "Wikidata", "title": (w or {}).get("name") or q, "url": "https://www.wikidata.org/wiki/" + q, "note": "its legislature (P194)" if offk == "wd-legis" else ""})
            used_wd.add(q)
            if w and w.get("site") and w.get("site_status") == 200 and not site: site = w["site"]
        if offk in ("wd", "wd-legis") and not qids: problems.append(f"no source: {name}")
        if not srcs: problems.append(f"no source: {j} {name}")
        bt, _ = KIND[kind]
        bodies.append({"j": j, "name": name, "branch": br, "tk": bt, "type": BT[bt], "ak": ACT[kind], "formerly": formerly, "web": site, "srcs": srcs, "constitutional": bool(clause)})
    # every other public body Wikidata records in the jurisdiction (not already one of the above)
    excluded = collections.Counter()
    for q, w in wd.items():
        if q in used_wd: continue
        if EXCLUDE_CLS.search(" ".join(w["classes"])): excluded["hospitals (public or private not stated)"] += 1; continue
        if not confirmed(w): excluded["no website confirming it is current" if not w.get("site") else "website gone, moved or blocked"] += 1; continue
        for j in w["jurisdictions"] or []:
            if j not in JUR: continue
            br, bt, ak = wd_kind(w["classes"], w["name"])
            bodies.append({"j": j, "name": w["name"], "branch": br, "tk": bt, "type": BT.get(bt, bt), "ak": ak, "formerly": None,
                           "web": w.get("site_final") or w["site"], "web_flag": "",
                           "srcs": [{"kind": "Wikidata", "title": w["name"], "url": "https://www.wikidata.org/wiki/" + q, "note": ", ".join(w["classes"])}], "constitutional": False})
    # one record per body: same jurisdiction and same name -> combine sources
    by = collections.OrderedDict()
    for b in bodies:
        k = (b["j"], norm(b["name"]))
        if k in by:
            a = by[k]; a["srcs"] += [s for s in b["srcs"] if s["url"] not in {x["url"] for x in a["srcs"]}]; a["web"] = a["web"] or b["web"]
        else: by[k] = b
    out = []
    for b in by.values():
        jn, grp, reg, order = JUR[b["j"]]
        pk, _ = classify.purpose(b["name"], b["type"], " ".join(s.get("note", "") for s in b["srcs"]))
        if b["branch"] == "judiciary": pk = "safety"
        if b["branch"] == "legislature" or b["tk"] == "territory": pk = "govt"
        b.update({"jurisdiction": jn, "group": grp, "parent": reg, "pk": pk, "geography": "Outside the UK: " + jn,
                  "uk_links": [JCPC] + ([MOJ] if grp == "CD" else []), "id": "terr:" + b["j"].lower() + ":" + norm(b["name"]).replace(" ", "-")[:60]})
        out.append(b)
    build.excluded = dict(excluded)
    return out, problems


def check(out, problems):
    e = list(problems)
    ids = collections.Counter(b["id"] for b in out)
    if any(v > 1 for v in ids.values()): e.append(f"duplicate records: {[k for k, v in ids.items() if v > 1][:3]}")
    if any(not b["srcs"] for b in out): e.append("a body with no source")
    for j in JUR:
        if j in ("GG-ALD", "GG-SRK", "SH-AC", "SH-TA", "AQ-BAT", "IO", "GS", "SBA"): continue
        brs = {b["branch"] for b in out if b["j"] == j}
        if not {"legislature", "executive", "judiciary"} <= brs: e.append(f"{JUR[j][0]}: missing a branch ({sorted(brs)})")
    def has(j, n, br): return any(b["j"] == j and b["name"] == n and b["branch"] == br for b in out)
    for j, n, br in [("KY", "Grand Court", "judiciary"), ("BM", "Cabinet", "executive"), ("IM", "Tynwald", "legislature"), ("JE", "Royal Court of Jersey", "judiciary"), ("TC", "Parliament of the Turks and Caicos Islands", "legislature")]:
        if not has(j, n, br): e.append(f"known answer missing: {n} ({j}, {br})")
    if any(b["name"] == "Department of Community, Culture and Leisure" for b in out): e.append("a retired department shown as current (its address answers with an error page)")
    hs = [b for b in out if b["j"] == "IM" and "Health and Social Care" in b["name"]]
    if len(hs) > 1: e.append("the same body appears twice (Isle of Man Department of Health and Social Care)")
    return e


def main():
    out, problems = build()
    if "--negative" in sys.argv:
        caught = []
        o = copy.deepcopy(out); o.append(copy.deepcopy(o[0])); caught.append(bool(check(o, [])))
        o = [b for b in copy.deepcopy(out) if not (b["j"] == "KY" and b["branch"] == "judiciary")]; caught.append(bool(check(o, [])))
        caught.append(bool(check(out, ["clause not found: test"])))
        o = copy.deepcopy(out); o[0]["srcs"] = []; caught.append(bool(check(o, [])))
        if not all(caught): sys.exit(f"territories negative: {caught.count(False)} not caught")
        print(f"territories negative: all {len(caught)} breakers caught"); return
    e = check(out, problems)
    if e: sys.exit("territories: " + "; ".join(e))
    meta = {"rule": __doc__.split("\n\n")[1].strip(), "jurisdictions": {k: {"name": v[0], "group": v[1], "register_id": v[2], "order": v[3], "note": JNOTES.get(k, ""), "note_sources": JNOTE_SRC.get(k, [])} for k, v in JUR.items()},
            "counts": dict(collections.Counter((b["group"], b["branch"]) for b in out).items()) and {f"{g}:{br}": n for (g, br), n in collections.Counter((b["group"], b["branch"]) for b in out).items()},
            "constitutional": sum(b["constitutional"] for b in out), "total": len(out), "excluded": build.excluded,
            "blocked": "The Isle of Man Government's website refused automated checks, so its departments known only from Wikidata are left out until they can be confirmed another way; the site was not retried with a disguised request.",
            "not_covered": "Local government below the jurisdiction (parishes, parish commissioners, douzaines) is shown only where the body's own website confirms it; hospitals are left out because the sources don't say whether each is public or private."}
    (ROOT / "data/territories.json").write_text(json.dumps({"meta": meta, "bodies": out}, ensure_ascii=False, indent=1))
    print("territories:", meta["total"], "bodies;", meta["constitutional"], "from founding orders;", meta["counts"])


if __name__ == "__main__":
    main()
