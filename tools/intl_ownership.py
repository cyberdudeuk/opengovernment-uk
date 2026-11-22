"""The UK state's shareholdings and voting power in international financial institutions -> data/intl-ownership.json

Real ownership, so it belongs in BODS (tools/export_bods.py adds these as relationship statements). Each figure comes
from the institution's own published table, read into sources/evidence/intl-shareholdings.json (--refresh re-reads):
  IBRD, IDA, IFC, MIGA   World Bank Group Finances One open datasets (CC BY 4.0): DS00051, DS00049, DS00050, DS00045
  AIIB                   the Bank's "Members of the Bank" table (its voting-power data file)
Institutions whose tables could not be read automatically are listed with the reason, never estimated.
Percentages and votes only: money amounts are left out because the tables use different units.

  python tools/intl_ownership.py             build and check (offline, from the evidence file)
  python tools/intl_ownership.py --refresh   re-read the institutions' tables first
  python tools/intl_ownership.py --negative  prove the checks fail when they should
"""
import json, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
EV = ROOT / "sources/evidence/intl-shareholdings.json"
UA = "OpenGovernmentUK/0.4 (https://github.com/cyberdudeuk/opengovernment-uk)"
WB = "https://datacatalogapi.worldbank.org/dexapps/fone/api/apiservice?datasetId={d}&resourceId={r}&top=1000&type=json"
INST = [  # name, short, dataset, documented resource, LEI (GLEIF, checked), Wikidata, members expected roughly
    ("International Bank for Reconstruction and Development", "IBRD", "DS00051", "RS00053", "ZTMSNXROF84AHWJNKQ93", "Q191384"),
    ("International Development Association", "IDA", "DS00049", "RS00051", "P41R60HC414IWQA1XW02", "Q827525"),
    ("International Finance Corporation", "IFC", "DS00050", "RS00052", "QKL54NQY28TCDAI75F60", "Q656801"),
    ("Multilateral Investment Guarantee Agency", "MIGA", "DS00045", "RS00044", "549300ZG5PH6MA164968", "Q1043527")]
AIIB = ("Asian Infrastructure Investment Bank", "AIIB", "https://www.aiib.org/en/about-aiib/governance/members-of-bank/.content/voting-power.js",
        "https://www.aiib.org/en/about-aiib/governance/members-of-bank/index.html", "25490065OSV2524LCR32", "Q18109843")
NOT_READ = [
    {"name": "International Monetary Fund", "why": "The IMF's quotas and voting power page refuses automated reads (access denied); it is not worked around.", "url": "https://www.imf.org/en/About/executive-board/members-quotas"},
    {"name": "European Bank for Reconstruction and Development", "why": "No machine-readable shareholding table found on its site.", "url": "https://www.ebrd.com/shareholders-and-board-of-governors.html"},
    {"name": "Asian Development Bank", "why": "Its UK member fact sheet could not be found at a stable address.", "url": "https://www.adb.org/"},
    {"name": "African Development Bank", "why": "Its shareholders page refuses automated reads (HTTP 403).", "url": "https://www.afdb.org/en/about/shareholders"},
    {"name": "Caribbean Development Bank", "why": "Its members page could not be found (HTTP 404).", "url": "https://www.caribank.org/"}]
LEI_NOTE = "GLEIF has two records named International Finance Corporation; the one in Washington DC (QKL54NQY28TCDAI75F60) is the World Bank Group institution, the other (in Florida) is an unrelated company."


def get(u):
    return subprocess.run(["curl", "-s", "-L", "-m", "60", "-A", UA, u], capture_output=True, text=True).stdout  # noqa: S603,S607 fixed program, our own URLs


def refresh():
    rows = []
    for name, short, ds, rs, lei, qid in INST:
        d = json.loads(get(WB.format(d=ds, r=rs))); data = d["data"]
        uk = next(r for r in data if r["member"].upper() == "UNITED KINGDOM")
        rows.append({"name": name, "short": short, "lei": lei, "wikidata": qid, "members": len(data), "as_of": uk["as_of_date"],
                     "votes": uk["number_of_votes"], "share_of_votes": uk["percentage_of_total_voting_power"],
                     "share_of_subscriptions": uk.get("percentage_of_total_subscriptions"),
                     "source": {"title": f"World Bank Group Finances One, {short} subscriptions and voting power of member countries ({ds})",
                                "url": f"https://financesone.worldbank.org/d/{ds}", "api": WB.format(d=ds, r=rs), "licence": "CC BY 4.0"}})
        time.sleep(8)  # the API limits request rates
    js = get(AIIB[2]); upd = re.search(r'update_date = "([^"]+)"', js).group(1)
    members = re.findall(r'"([^"|]+)\|\s*[^|]*\|\s*[\d,.]+\s*\|\s*[\d.]+%\|\s*[\d,]+\s*\|\s*[\d.]+%"', js)
    m = re.search(r'"United Kingdom\|\s*([^|]+)\|\s*([\d,.]+)\s*\|\s*([\d.]+)%\|\s*([\d,]+)\s*\|\s*([\d.]+)%"', js)
    rows.append({"name": AIIB[0], "short": AIIB[1], "lei": AIIB[4], "wikidata": AIIB[5], "members": len(members), "as_of": upd,
                 "member_since": m.group(1).strip(), "votes": int(m.group(4).replace(",", "")), "share_of_votes": float(m.group(5)), "share_of_subscriptions": float(m.group(3)),
                 "source": {"title": "Asian Infrastructure Investment Bank, Members of the Bank", "url": AIIB[3], "api": AIIB[2], "licence": "published by the Bank"}})
    for r in rows:  # OG-D62: every identifier is read back from its register, never written from memory
        e = json.loads(get(f"https://www.wikidata.org/wiki/Special:EntityData/{r['wikidata']}.json"))["entities"]
        r["wikidata_label"] = next(iter(e.values()))["labels"]["en"]["value"]
        g = json.loads(get(f"https://api.gleif.org/api/v1/lei-records/{r['lei']}"))["data"]["attributes"]["entity"]
        r["lei_name"], r["lei_city"] = g["legalName"]["name"], g["legalAddress"].get("city")
        time.sleep(1)
    EV.write_text(json.dumps({"read": "2026-11-22", "holder": "wikidata:Q145", "rows": rows, "not_read": NOT_READ, "lei_note": LEI_NOTE}, indent=1, ensure_ascii=False))


def build():
    E = json.loads(EV.read_text())
    rel = json.loads((ROOT / "data/relations.json").read_text())
    lead = {}
    for m in rel["memberships"]:
        for r in E["rows"]:
            if m["name"].startswith(r["name"]) or (r["short"] == "AIIB" and "AIIB" in m["name"]) or (m["name"] == "World Bank Group" and r["short"] in ("IBRD", "IDA", "IFC", "MIGA")):
                lead.setdefault(r["short"], set()).update(m["lead"])
    for r in E["rows"]: r["uk_lead"] = sorted(lead.get(r["short"], []))
    return E


def check(E):
    e = []
    R = {r["short"]: r for r in E["rows"]}
    for k in ("IBRD", "IDA", "IFC", "MIGA", "AIIB"):
        if k not in R: e.append(f"{k} missing")
    for r in E["rows"]:
        if not (0 < r["share_of_votes"] < 20): e.append(f"{r['short']}: share of votes {r['share_of_votes']} is outside a believable range")
        if r["members"] < 100: e.append(f"{r['short']}: only {r['members']} members read; the table may have changed")
        if not re.fullmatch(r"[0-9A-Z]{18}[0-9]{2}", r["lei"]): e.append(f"{r['short']}: malformed LEI")
        if r.get("wikidata_label", "").lower() != r["name"].lower(): e.append(f"{r['short']}: Wikidata {r['wikidata']} is {r.get('wikidata_label')!r}, not this institution (OG-D62)")
        if r.get("lei_name", "").lower() != r["name"].lower(): e.append(f"{r['short']}: LEI {r['lei']} belongs to {r.get('lei_name')!r}")
    if R.get("IFC", {}).get("lei") != "QKL54NQY28TCDAI75F60": e.append("known answer: the IFC's LEI is the Washington DC record")
    if R.get("AIIB", {}).get("member_since", "").replace(" ", "") != "Dec25,2015": e.append("known answer: the UK joined the AIIB on 25 December 2015")
    if not all(x["why"] for x in E["not_read"]): e.append("an unread institution has no reason")
    return e


def main():
    if "--refresh" in sys.argv: refresh()
    E = build()
    if "--negative" in sys.argv:
        bad = json.loads(json.dumps(E)); bad["rows"][0]["share_of_votes"] = 87.0; bad["rows"][2]["lei"] = "984500AE69C2AC487849"; bad["rows"][4]["wikidata_label"] = "Congressional Research Service report"
        miss = json.loads(json.dumps(E)); miss["rows"] = miss["rows"][:-1]
        caught = [bool(check(bad)), bool(check(miss))]
        if not all(caught): sys.exit("intl_ownership negative: not caught")
        print("intl_ownership negative: all breakers caught"); return
    e = check(E)
    if e: sys.exit("intl_ownership: " + "; ".join(e))
    (ROOT / "data/intl-ownership.json").write_text(json.dumps(E, ensure_ascii=False, indent=0))
    print("intl_ownership:", ", ".join(f"{r['short']} {r['share_of_votes']}% of votes" for r in E["rows"]), f"| not read: {len(E['not_read'])}")


if __name__ == "__main__":
    main()
