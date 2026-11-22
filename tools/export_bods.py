"""Emit the accountability tree as Beneficial Ownership Data Standard (BODS) 0.4 statements, validated against the
official schema, with the public-sector relation carried in a namespaced extension (publicAccountability).
Mapping rationale is in docs/bods-public-sector-profile.md; every statement cites its source file and fingerprint."""
import hashlib, json, pathlib, re, sys
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = pathlib.Path(__file__).resolve().parents[1]; OUT = ROOT / "docs"; OUT.mkdir(exist_ok=True)
BODS = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "vendor" / "bods-schema")  # official BODS 0.4 schema, pinned commit e8cc3fd
T = json.loads((ROOT / "data" / "tree.json").read_text())
BASE = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources" / "opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
FAM = BASE["fam"]; REG = {r[0]: r for r in BASE["r"]}
PUB = {"publicationDate": T["built"][:10], "bodsVersion": "0.4", "license": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
       "publisher": {"name": "OpenGovernment UK (pilot)", "url": "https://cyberdudeuk.github.io/opengovernment-uk/"}}  # OG-D72: the portal itself, never a private link
# org-id.guide schemes where one exists; the register's own CURIE otherwise
SCHEME = {"govuk_slug": ("GB-GOVUK", "GOV.UK organisation"), "companies_house": ("GB-COH", "Companies House"), "charity_ew": ("GB-CHC", "Charity Commission for England and Wales"),
          "charity_sc": ("GB-SC", "Scottish Charity Regulator"), "charity_ni": ("GB-NIC", "Charity Commission for Northern Ireland"), "lei": ("XI-LEI", "Global Legal Entity Identifier"),
          "nhs_ods": ("GB-NHS", "NHS Organisation Data Service"), "local_authority": ("GB-LAE", "Local authority code"), "wikidata": ("XI-WIKIDATA", "Wikidata")}
def sid(*parts): return "oguk-" + hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:48]
def rid(k): return "oguk-" + hashlib.sha256(k.encode()).hexdigest()[:24]
def etype(r):
    fam, kind = FAM[r[2]], r[3]
    if fam == "Nation or state": return {"type": "state"}
    if kind in ("Ministerial department", "Non-ministerial department", "Devolved government"): return {"type": "stateBody", "subtype": "governmentDepartment", "details": kind}
    if r[10].get("companies_house"): return {"type": "registeredEntity", "details": kind or fam}
    return {"type": "stateBody", "subtype": "stateAgency" if fam != "Local authority" else "other", "details": kind or fam}
JUR = {"EN": ("England", "GB-ENG"), "SC": ("Scotland", "GB-SCT"), "WA": ("Wales", "GB-WLS"), "NI": ("Northern Ireland", "GB-NIR")}
def src(e):
    s = T["sources"][e["src"]]; return {"type": ["officialRegister"], "description": f'{s["name"]}; {e["ref"]}; sha256 {s["sha256"]}', "url": s["url"], "retrievedAt": s["retrieved"]}
PSC = [(r"ownership-of-shares-(\d+)-to-(\d+)", "shareholding"), (r"voting-rights-(\d+)-to-(\d+)", "votingRights"), (r"right-to-appoint-and-remove-directors", "appointmentOfBoard"), (r"significant-influence-or-control", "otherInfluenceOrControl")]
def interests(e):
    base = {"directOrIndirect": "direct", "beneficialOwnershipOrControl": False}
    if e["rel"] == "accounts": return [dict(base, type="controlByLegalFramework", details="Included in this department's Supply Estimate and accounts by designation order")]
    if e["rel"] == "owns" and e["src"] == "ch" and e.get("control"):
        out = []
        for c in e["control"].split("; "):
            for pat, t in PSC:
                m = re.search(pat, c)
                if m:
                    i = dict(base, type=t, details=c)
                    if m.groups(): i["share"] = {"minimum": float(m.group(1)), "maximum": float(m.group(2)), "exclusiveMinimum": False, "exclusiveMaximum": False}
                    out.append(i); break
        return out or [dict(base, type="otherInfluenceOrControl", details=e["control"])]
    if e["rel"] == "owns" and e["src"] == "ons": return [dict(base, type="shareholding", details="ONS: parent company (share not published)")]
    if e["rel"] == "owns": return [dict(base, type="otherInfluenceOrControl", details="GLEIF: accounting consolidation parent")]
    return [dict(base, type="otherInfluenceOrControl", details={"sponsors": "Sponsorship", "controls": "ONS: controlling unit of a non-institutional unit", "parent": "GOV.UK parent organisation", "decided": "Oversight by this parent, decided from the body's own record where the sources disagreed"}[e["rel"]])]
IATI = {r["register_id"]: r["iati_id"] for r in json.loads((ROOT / "data" / "peer-iati.json").read_text())["rows"] if r["register_id"]}  # FCDO list, exact matches only
ids_needed = {e["c"] for e in T["edges"] if e["p"]} | {e["p"] for e in T["edges"] if e["p"]}
S = []
for k in sorted(ids_needed):
    r = REG[k]; nat = (r[5] or "")[:2]
    rd = {"isComponent": False, "entityType": etype(r), "name": r[1],
          "identifiers": [{"id": k, "schemeName": "OpenGovernment UK register key"}] + [{"id": str(v), "scheme": SCHEME[f][0], "schemeName": SCHEME[f][1]} for f, v in r[10].items() if f in SCHEME and v and not isinstance(v, list)] + ([{"id": IATI[k], "scheme": "GB-GOV", "schemeName": "UK government IATI organisation identifier (FCDO)"}] if k in IATI else [])}
    if nat in JUR: rd["jurisdiction"] = {"name": JUR[nat][0], "code": JUR[nat][1]}
    elif nat in ("UK", ""): rd["jurisdiction"] = {"name": "United Kingdom", "code": "GB"}
    if r[7]: rd["foundingDate"] = r[7][:10]
    if r[8]: rd["dissolutionDate"] = r[8][:10]
    if r[9]: rd["uri"] = r[9]
    c = T["chains"].get(k)
    st = {"statementId": sid("e", k, T["digest"]), "statementDate": T["built"][:10], "recordId": rid(k), "declarationSubject": rid(k), "recordType": "entity", "recordStatus": "new", "recordDetails": rd,
          "publicationDetails": PUB, "source": {"type": ["officialRegister"], "description": "OpenGovernment UK register record, joined from GOV.UK, ONS and other registers"}}
    if c: st["publicAccountability"] = {"answersTo": c["answerable"], "accountableOwner": rid(c["root"]) if c["root"] != k else None, "sourcesAgreeing": c["agree"],
                                        "wga2024_25": (c.get("wga") or {}).get("status"), "governmentFundedIncomeGBP": (c.get("money") or {}).get("gov_funded"), "tradingFund": c["trading_fund"] or None}
    S.append(st)
for i, e in enumerate(T["edges"]):
    if not e["p"] or e["p"] == e["c"]: continue
    S.append({"statementId": sid("r", i, e["c"], e["p"], e["rel"], e["src"], T["digest"]), "statementDate": T["built"][:10], "recordId": rid(f'{e["c"]}|{e["p"]}|{e["rel"]}|{e["src"]}|{e["ref"]}'),
              "recordType": "relationship", "recordStatus": "new", "declarationSubject": rid(e["c"]),
              "recordDetails": {"isComponent": False, "subject": rid(e["c"]), "interestedParty": rid(e["p"]), "interests": interests(e)},
              "publicationDetails": PUB, "source": src(e),
              "publicAccountability": {"relation": e["rel"], "relationLabel": T["rels"][e["rel"]], "asWritten": e["pt"], "matchMethod": e["how"], "sourceKey": e["src"]}})
# The UK state's holdings in international financial institutions (tools/intl_ownership.py): real ownership, from each
# institution's own published table. The UK is a 'state' entity; each institution a 'legalEntity' with its LEI.
IO = json.loads((ROOT / "data" / "intl-ownership.json").read_text())
UK = IO["holder"]
if UK not in ids_needed:
    S.append({"statementId": sid("e", UK, T["digest"]), "statementDate": T["built"][:10], "recordId": rid(UK), "declarationSubject": rid(UK), "recordType": "entity", "recordStatus": "new",
              "recordDetails": {"isComponent": False, "entityType": {"type": "state"}, "name": "United Kingdom", "jurisdiction": {"name": "United Kingdom", "code": "GB"},
                                "identifiers": [{"id": UK, "schemeName": "OpenGovernment UK register key"}, {"id": "Q145", "scheme": "XI-WIKIDATA", "schemeName": "Wikidata"}]},
              "publicationDetails": PUB, "source": {"type": ["officialRegister"], "description": "OpenGovernment UK register record"}})
MON = {m: i + 1 for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}
def iso(d):
    m = re.fullmatch(r"(\d{1,2})-(\w{3})-(\d{4})", d) or None
    if m: return f"{m.group(3)}-{MON[m.group(2)[:3]]:02d}-{int(m.group(1)):02d}"
    m = re.fullmatch(r"(\w{3})\w*\.? (\d{1,2}), (\d{4})", d.strip())
    return f"{m.group(3)}-{MON[m.group(1)[:3]]:02d}-{int(m.group(2)):02d}"
for r in IO["rows"]:
    k = "lei:" + r["lei"]; asof = iso(r["as_of"])
    S.append({"statementId": sid("e", k, asof), "statementDate": asof, "recordId": rid(k), "declarationSubject": rid(k), "recordType": "entity", "recordStatus": "new",
              "recordDetails": {"isComponent": False, "entityType": {"type": "legalEntity", "details": "International financial institution, established by treaty among its member countries"}, "name": r["name"],
                                "identifiers": [{"id": r["lei"], "scheme": "XI-LEI", "schemeName": "Global Legal Entity Identifier"}, {"id": r["wikidata"], "scheme": "XI-WIKIDATA", "schemeName": "Wikidata"}],
                                "uri": r["source"]["url"]},
              "publicationDetails": PUB, "source": {"type": ["officialRegister"], "description": r["source"]["title"], "url": r["source"]["url"]}})
    base = {"directOrIndirect": "direct", "beneficialOwnershipOrControl": False}
    ints = ([dict(base, type="shareholding", share={"exact": r["share_of_subscriptions"]}, details="Share of total subscriptions to capital, as the institution publishes it")] if r.get("share_of_subscriptions") is not None else []) + \
           [dict(base, type="votingRights", share={"exact": r["share_of_votes"]}, details=f"{r['votes']:,} votes, {r['share_of_votes']}% of total voting power, as the institution publishes it")]
    if r.get("member_since"):
        for i in ints: i["startDate"] = iso(r["member_since"])
    S.append({"statementId": sid("r", k, UK, asof), "statementDate": asof, "recordId": rid(f"{k}|{UK}|member-shareholder"), "recordType": "relationship", "recordStatus": "new", "declarationSubject": rid(k),
              "recordDetails": {"isComponent": False, "subject": rid(k), "interestedParty": rid(UK), "interests": ints},
              "publicationDetails": PUB, "source": {"type": ["officialRegister"], "description": f"{r['source']['title']}; as of {asof}", "url": r["source"]["url"], "retrievedAt": IO["read"]},
              "publicAccountability": {"relation": "member-shareholder", "relationLabel": "The UK state is a member and shareholder", "ukLead": r.get("uk_lead", []), "membersOfInstitution": r["members"]}})
# validate against the official schema
reg = Registry()
for f in BODS.glob("*.json"):
    d = json.loads(f.read_text()); reg = reg.with_resource(d["$id"], Resource.from_contents(d))
schema = json.loads((BODS / "statement.json").read_text())
errs = list(Draft202012Validator(schema, registry=reg).iter_errors(S))
print(f"{len(S)} statements ({sum(s['recordType']=='entity' for s in S)} entities, {sum(s['recordType']=='relationship' for s in S)} relationships); schema errors: {len(errs)}")
for e in errs[:8]: print(" -", list(e.absolute_path)[:4], e.message[:200])
if errs: sys.exit(1)
if any(not str(x["publicationDetails"]["publisher"].get("url", "")).startswith("https://cyberdudeuk.github.io/opengovernment-uk/") for x in S): sys.exit("OG-D72: a statement names a publisher address other than the portal")
(OUT / "bods-0.4.json").write_text(json.dumps(S, ensure_ascii=False))
print("wrote docs/bods-0.4.json", (OUT / "bods-0.4.json").stat().st_size)
