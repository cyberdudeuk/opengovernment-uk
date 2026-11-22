"""The register in FollowTheMoney (FtM) -> docs/data/register.ftm.json (one entity per line)

FollowTheMoney is the data model OpenSanctions, OpenAleph and yente use. Publishing the register in it lets those tools
load the UK state's public bodies directly: for example to recognise a public body, or a company it controls, when it
appears in other data.
  entities   each register record: PublicBody, or Company where it has a Companies House number; the international
             bodies and financial institutions the UK belongs to: Organization
  links      taken from the BODS file (tools/export_bods.py), so the two never disagree, using the published
             BODS-to-FtM mapping (github.com/StephenAbbott/bods-ftm): a stated shareholding in a company -> Ownership;
             any other control -> Control (controlType "state" for control by law);
             renames, mergers and splits -> Succession; memberships of international bodies -> Membership.
  one difference from that mapping: FtM only lets an Ownership point at an Asset (a company), so the UK's shares in
             international financial institutions are a Membership whose description gives the share of votes.
Checked against FtM's own compiled model (vendor/followthemoney/defaultModel.json, FtM 4.11.3, MIT): every schema,
property, reference, required property, country code and date. Not run through the FtM library itself, which needs a
compiled ICU dependency that would add upkeep.

  python tools/ftm_export.py             build and check
  python tools/ftm_export.py --negative  prove the checks fail when they should
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "vendor/followthemoney/defaultModel.json").read_text())
SITE = "https://cyberdudeuk.github.io/opengovernment-uk/"
PUB = {"publisher": ["OpenGovernment UK (pilot)"], "publisherUrl": [SITE]}
NAT = {"EN": "gb", "SC": "gb-sct", "WA": "gb-wls", "NI": "gb-nir", "UK": "gb", "GB": "gb"}


def fid(k): return "oguk-" + re.sub(r"[^a-zA-Z0-9.-]+", "-", k).strip("-").lower()


def build():
    h = (ROOT / "docs/index.html").read_text()
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', h, re.S).group(1))
    web = json.loads((ROOT / "data/websites.json").read_text())
    cls = json.loads((ROOT / "data/classification.json").read_text())
    blab = {b["key"]: b["label"] for b in cls["meta"]["btypes"]}
    countries = {v.lower(): k for k, v in M["types"]["country"]["values"].items()}
    out = {}
    def add(e): out[e["id"]] = e
    for r in D["r"]:
        k, ids = r[0], r[10] or {}
        schema = "Company" if ids.get("companies_house") else "PublicBody"
        nat = (r[5] or "")[:2]
        c = NAT.get(nat) or countries.get(r[1].lower()) or "gb"
        p = {"name": [r[1]], "country": [c], "sourceUrl": [f"{SITE}index.html#org-{k.replace(':', '--')}"], "status": ["active" if r[4] else "inactive"], **PUB}
        if k in web: p["website"] = [web[k][0]]
        if ids.get("wikidata"): p["wikidataId"] = [ids["wikidata"]]
        if ids.get("lei"): p["leiCode"] = [ids["lei"]]
        if ids.get("companies_house"): p["registrationNumber"] = [str(ids["companies_house"])]
        if r[7]: p["incorporationDate"] = [r[7][:10]]
        if r[8]: p["dissolutionDate"] = [r[8][:10]]
        b = (cls["bodies"].get(k) or {}).get("btype")
        if b: p["classification"] = [blab.get(b, b)]
        add({"id": fid(k), "schema": schema, "properties": p})
    # links from BODS
    bods = json.loads((ROOT / "docs/bods-0.4.json").read_text())
    rec = {}
    for s in bods:
        if s["recordType"] != "entity": continue
        idn = s["recordDetails"].get("identifiers", [])
        key = next((i["id"] for i in idn if i.get("schemeName") == "OpenGovernment UK register key"), None)
        lei = next((i["id"] for i in idn if i.get("scheme") == "XI-LEI"), None)
        if key: rec[s["recordId"]] = fid(key)
        elif lei:
            eid = "oguk-lei-" + lei.lower(); rec[s["recordId"]] = eid
            qid = next((i["id"] for i in idn if i.get("scheme") == "XI-WIKIDATA"), None)
            add({"id": eid, "schema": "Organization", "properties": {"name": [s["recordDetails"]["name"]], "leiCode": [lei], **({"wikidataId": [qid]} if qid else {}), "sourceUrl": [s["recordDetails"].get("uri", SITE)], **PUB}})
    n = 0
    for s in bods:
        if s["recordType"] != "relationship": continue
        d = s["recordDetails"]; subj, party = rec.get(d["subject"]), rec.get(d["interestedParty"])
        if not subj or not party or subj not in out or party not in out: continue
        pa = s.get("publicAccountability", {})
        for it in d["interests"]:
            n += 1; base = {"role": [it["type"]], "summary": [pa.get("relationLabel") or it.get("details", "")][:1], "sourceUrl": [s["source"].get("url", SITE)], **PUB}
            if it.get("startDate"): base["startDate"] = [it["startDate"]]
            if pa.get("relation") == "member-shareholder":
                if it["type"] != "votingRights": continue
                add({"id": f"oguk-ms-{subj}-{party}", "schema": "Membership", "properties": {**base, "member": [party], "organization": [subj], "role": ["member and shareholder"],
                     "description": [it.get("details", "")]}})
            elif it["type"] == "shareholding" and out[subj]["schema"] == "Company":
                pp = {**base, "owner": [party], "asset": [subj]}
                if (it.get("share") or {}).get("exact") is not None: pp["percentage"] = [str(it["share"]["exact"])]
                add({"id": f"oguk-own-{n}", "schema": "Ownership", "properties": pp})
            else:
                pp = {**base, "controller": [party], "controlled": [subj]}
                if it["type"] == "controlByLegalFramework": pp["controlType"] = ["state"]
                add({"id": f"oguk-ctl-{n}", "schema": "Control", "properties": pp})
    # renames, mergers and splits
    for i, e in enumerate(D["ev"]):
        for s2 in e.get("successors", []):
            if fid(e["id"]) in out and fid(s2) in out:
                add({"id": f"oguk-succ-{i}-{fid(s2)}", "schema": "Succession", "properties": {"predecessor": [fid(e["id"])], "successor": [fid(s2)], "role": [e["event"].replace("_", " ")],
                     **({"date": [e["date"][:10]]} if e.get("date") else {}), **PUB}})
    # memberships of international bodies
    rel = json.loads((ROOT / "data/relations.json").read_text())
    who = {"UK": "wikidata:Q145", "EN": "wikidata:Q21", "SC": "wikidata:Q22", "WA": "wikidata:Q25", "NI": "wikidata:Q26"}
    for i, m in enumerate(rel["memberships"]):
        org = "oguk-wd-" + m["qid"].lower() if m["qid"] else "oguk-intl-" + re.sub(r"[^a-z0-9]+", "-", m["name"].lower()).strip("-")
        if org not in out:
            add({"id": org, "schema": "Organization", "properties": {"name": [m["name"]], **({"wikidataId": [m["qid"]]} if m["qid"] else {}), **({"website": [m["site"]]} if m.get("site") else {}), **PUB}})
        member = fid(who.get(m["who"], "wikidata:Q145"))
        if member in out:
            pp = {"member": [member], "organization": [org], "role": ["member"], "status": [m["status"]], **PUB}
            if m.get("start"): pp["startDate"] = [m["start"][:10]]
            if m.get("end"): pp["endDate"] = [m["end"][:10]]
            add({"id": f"oguk-mem-{i}", "schema": "Membership", "properties": pp})
    return out


def props_of(schema):
    s = M["schemata"][schema]; out = {}
    for anc in s["schemata"]: out.update(M["schemata"][anc].get("properties", {}))
    return out


def check(out):
    e = []
    countries = set(M["types"]["country"]["values"])
    for x in out.values():
        if x["schema"] not in M["schemata"]: e.append(f"{x['id']}: unknown schema {x['schema']}"); continue
        P = props_of(x["schema"])
        for req in M["schemata"][x["schema"]].get("required", []):
            if not x["properties"].get(req): e.append(f"{x['id']}: missing required {req}")
        for k, vals in x["properties"].items():
            if k not in P: e.append(f"{x['id']}: {x['schema']} has no property {k}"); continue
            t = P[k].get("type")
            for v in vals:
                if t == "entity":
                    tgt = out.get(v)
                    if not tgt: e.append(f"{x['id']}.{k}: reference {v} missing")
                    elif P[k].get("range") and P[k]["range"] not in M["schemata"][tgt["schema"]]["schemata"]: e.append(f"{x['id']}.{k}: {tgt['schema']} is not a {P[k]['range']}")
                if t == "country" and v not in countries: e.append(f"{x['id']}.{k}: country {v} not in FtM's list")
                if t == "date" and not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", v): e.append(f"{x['id']}.{k}: date {v}")
        if not re.fullmatch(r"[a-zA-Z0-9.-]+", x["id"]): e.append(f"bad id {x['id']}")
    met = out.get(fid("government-organisation:EA46"), {})
    if not met.get("properties", {}).get("wikidataId"): e.append("known answer: the Met Office carries its Wikidata id")
    if not any(x["schema"] == "Membership" and "votes" in " ".join(x["properties"].get("description", [])) for x in out.values()): e.append("known answer: the UK's IFI holdings as Membership")
    if not any(x["schema"] == "Succession" for x in out.values()): e.append("known answer: machinery of government changes as Succession")
    return e


def main():
    out = build()
    if "--negative" in sys.argv:
        bad = json.loads(json.dumps(out)); k = next(iter(bad)); bad[k]["properties"]["shareholders"] = ["x"]
        c2 = json.loads(json.dumps(out)); own = next(x for x in c2.values() if x["schema"] == "Membership"); own["schema"] = "Ownership"; own["properties"]["owner"] = own["properties"].pop("member"); own["properties"]["asset"] = own["properties"].pop("organization")
        ok = bool(check(bad)) and bool(check(c2))
        if not ok: sys.exit("ftm negative: not caught")
        print("ftm negative: an unknown property and an Ownership of a non-asset are both caught"); return
    e = check(out)
    if e: sys.exit("ftm: " + "; ".join(e[:10]) + (f" (+{len(e) - 10} more)" if len(e) > 10 else ""))
    (ROOT / "docs/data/register.ftm.json").write_text("\n".join(json.dumps(x, ensure_ascii=False, sort_keys=True) for x in sorted(out.values(), key=lambda x: x["id"])) + "\n")
    from collections import Counter
    print("ftm:", dict(Counter(x["schema"] for x in out.values())))


if __name__ == "__main__":
    main()
