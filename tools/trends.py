"""Public bodies over time, from the Cabinet Office's own transparency editions (2012 to 2023/24), and a check of the
November 2020 baseline against today's register so nothing stale is carried forward.

Evidence rules (see documentation/trends-and-futures-2030.md):
- each edition's money unit is pinned by an anchor body present in every edition (Arts Council England); see UNITS
- scope changes: up to 2020 the reports cover NDPBs; the 2022/23 and 2023/24 directories cover all ALBs. Totals are
  therefore shown by classification, and the like-for-like line is NDPBs only
- a repeated edition (2015 reuses 2013-14 figures) is detected and excluded, not double counted
- real terms use HM Treasury's GDP deflator (October 2026 Budget), 2025-26 prices
Run: python tools/trends.py <folder with the downloaded editions>   (fetch list in EDITIONS; files are OGL v3.0)"""
import csv, io, json, pathlib, re, sys, urllib.request
import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
RAW = pathlib.Path(ARGS[0]) if ARGS else ROOT / "sources" / "public-bodies"
A = "https://assets.publishing.service.gov.uk/media/"
# edition: (file, url, financial year of the figures, money unit multiplier, evidence for the unit)
EDITIONS = {
    "2012": ("2012.csv", A + "5a7c11d0ed915d1c30daa610/PB12-csv_1.csv", "2011-12", 1, "values written in pounds (Arts Council England £393,602,000)"),
    "2013": ("2013.csv", A + "5a7c922640f0b626628acff9/PB13_21-jan-14.csv", "2012-13", 1, "pounds (469,968,000)"),
    "2014": ("2014.csv", A + "5a74e2f0ed915d502d6cbc95/Annex_A_i_public_bodies_2014_for_publication.csv", "2013-14", 1, "pounds (£460,721,000)"),
    "2015": ("2015.csv", A + "5a81750eed915d74e33fe4fe/PB2015_Directory_Dataset_final_Jan_2016.csv", "2013-14", 1, "pounds; repeats 2014's figures"),
    "2016": ("2016.csv", A + "5a80d3b3ed915d74e33fca1c/public_bodies_data_set_for_gov_december_2016.csv", "2015-16", 1, "pounds (£463,095,000)"),
    "2017": ("2017.csv", A + "5a7c1d62ed915d210ade1abb/Public_Bodies_dataset__for_publication.csv", "2016-17", 1, "pounds (£494,161,000)"),
    "2018-19": ("2018fin.csv", A + "5c90d18740f0b633f3d4b657/2017-18_ALB_Financial_Datasets_.csv", "2017-18", 1000, "£'000 in the header (462,442)"),
    "2019": ("2019.xlsx", A + "5f183697d3bf7f597172867a/Public_Bodies_19.xlsx", "2018-19", 1000, "£'000 (486,914)"),
    "2020": ("2020.xlsx", A + "60eddabbe90e0764cd98a00d/PBD20_Data.xlsx", "2019-20", 1000, "£'000 (490,719)"),
    "2022/23": ("2023.xlsx", A + "697898221c24881f40a4d663/2024-12-17_Public_Bodies_Directory_2022_23.xlsx", "2022-23", 1, "pounds (542,047,000)"),
    "2023/24": ("2024.xlsx", A + "697897e25da1fd4ddea98bda/2025-05-29_Public_Bodies_Directory_2023_24.xlsx", "2023-24", 1, "pounds (495,330,000)"),
}
STAFF_ONLY = {"2018-19": ("2018.csv", A + "5c90d1a740f0b633f24d0441/2017-18_ALB_Datasets.csv")}
DEFLATOR = ("deflators.xlsx", A + "6ae32ab0a5c2f99e3a7b82e3/GDP_Deflators_Budget_October_2026_update.xlsx")
PERSONAL = re.compile(r"chair|chief executive|accounting officer|senior responsible|senior_sponsor|chair_nam|address|phone|email", re.I)  # never read

def text(p):
    b = p.read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try: return b.decode(enc)
        except UnicodeDecodeError: pass
    return b.decode("latin-1", "replace")
def table(f):
    p = RAW / f
    if p.suffix == ".csv": rows = list(csv.reader(io.StringIO(text(p), newline="")))
    else:
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
        ws = wb["Data"] if "Data" in wb.sheetnames else wb.worksheets[0]
        ws.reset_dimensions(); rows = [["" if c is None else c for c in r] for r in ws.iter_rows(values_only=True)]
    hi = next(i for i, r in enumerate(rows[:20]) if sum(bool(str(c).strip()) for c in r) > 4)
    head = [re.sub(r"\s+", " ", str(c)).strip() for c in rows[hi]]
    return [{h: r[j] if j < len(r) else "" for j, h in enumerate(head) if h and not PERSONAL.search(h)} for r in rows[hi + 1:] if any(str(c).strip() for c in r)]
def col(row, *pats):
    for p in pats:
        for k in row:
            if re.fullmatch(p, k, re.I): return row[k]
    return None
def money(v, unit):
    if v in (None, ""): return None
    if isinstance(v, (int, float)): return float(v) * unit
    s = re.sub(r"[£,\s]", "", str(v))
    try: return float(s) * unit
    except ValueError: return None
def num(v):
    try: return float(re.sub(r"[,\s]", "", str(v)))
    except ValueError: return None
def klass(c):
    c = (c or "").lower()
    if "advisory" in c: return "NDPB"
    if "tribunal" in c or "monitoring" in c or "ndpb" in c or "non-departmental" in c or "non departmental" in c: return "NDPB"
    if "executive agency" in c: return "Executive agency"
    if "non-ministerial" in c or "non ministerial" in c: return "Non-ministerial department"
    if "corporation" in c: return "Public corporation"
    return "Other"
def detail(c):
    c = (c or "").lower()
    for k, v in (("advisory", "Advisory NDPB"), ("tribunal", "Tribunal NDPB"), ("monitoring", "Independent monitoring board"), ("executive ndpb", "Executive NDPB")):
        if k in c: return v
    return None

def edition_rows(ed):
    f, url, fy, unit, ev = EDITIONS[ed]; out = []
    for r in table(f):
        name = col(r, "name", "organisation", "legislated body name", "overall_alb_name", "overall_organisation")
        if not name or not str(name).strip() or str(name).strip().lower() in ("total", "totals"): continue
        n = num(col(r, r"no\.? bodies", "number of bodies", "count", "overall_body_numbers")) or 1
        if ed in ("2012", "2013", "2014", "2015"): n = num(col(r, "multiple bodies")) or 1
        out.append({"name": re.sub(r"\s+", " ", str(name)).strip(), "department": str(col(r, "department", "sponsor department", "overall_parent_department") or "").strip(),
                    "class": klass(str(col(r, "classification", "overall_classification") or "")), "detail": detail(str(col(r, "classification", "overall_classification") or "")),
                    "bodies": max(1, int(n)), "gov_funding": money(col(r, "government funding", "overall_budget_govt_income", "finance_budget_govt_income", "income"), unit) if ed != "2018-19" else money(col(r, r"income £'000"), unit),
                    "spend": money(col(r, "total gross expenditure", "finance_spend_tme", r"expenditure £'000"), unit),
                    "staff": num(col(r, r"staff employed.*", "total fte staff employed", "staffing_fte_inpost"))})
    if ed in ("2019", "2020"):  # spend = RDEL + CDEL + RAME (£'000)
        for row, r in zip(out, [r for r in table(f) if col(r, "name", "legislated body name") and str(col(r, "name", "legislated body name")).strip()], strict=False):
            parts = [money(col(r, p), unit) for p in ("expenditure: rdel", "expenditure: cdel", "expenditure: rame")]
            row["spend"] = sum(x for x in parts if x is not None) if any(x is not None for x in parts) else None
    if ed == "2018-19":  # staff are in the companion dataset
        staff = {re.sub(r"\s+", " ", str(col(r, "name"))).strip().lower(): num(col(r, "staff employed")) for r in table(STAFF_ONLY[ed][0]) if col(r, "name")}
        for row in out: row["staff"] = staff.get(row["name"].lower())
    return out

def deflators():
    """GDP deflator (2025-26 = 100) and money GDP (£m) by financial year. Forecast years give only the % change, so the index is chained."""
    wb = openpyxl.load_workbook(RAW / DEFLATOR[0], read_only=True, data_only=True); ws = wb.worksheets[0]; d, g, last = {}, {}, None
    for r in ws.iter_rows(values_only=True):
        if not r or len(r) < 5 or not isinstance(r[1], str): continue
        m = re.match(r"(\d{4}-\d{2})", r[1])
        if not m: continue
        y = m.group(1)
        if isinstance(r[2], (int, float)): d[y] = float(r[2])
        elif isinstance(r[3], (int, float)) and last: d[y] = d[last] * (1 + r[3] / 100)
        if isinstance(r[4], (int, float)): g[y] = float(r[4]) * 1e6
        last = y
    return d, g
MEGA = {"nhs england": "NHS England", "education and skills funding agency": "Education and Skills Funding Agency", "education funding agency": "Education and Skills Funding Agency",
        "hm revenue and customs": "HM Revenue and Customs", "her majesty's revenue and customs": "HM Revenue and Customs", "hm revenue & customs": "HM Revenue and Customs", "network rail": "Network Rail", "network rail limited": "Network Rail"}
FY_UNCERTAIN = {"2015"}  # its annual-report years are mostly 2013-14, the same as the 2014 edition, yet 81% of its figures differ: excluded from money series

def fetch():
    """Download every edition into RAW (not committed: the files name office holders)."""
    RAW.mkdir(parents=True, exist_ok=True)
    for f, url in [(v[0], v[1]) for v in EDITIONS.values()] + list(STAFF_ONLY.values()) + [DEFLATOR]:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "OpenGovernment-UK-build"}), timeout=120) as r: (RAW / f).write_bytes(r.read())
        print("fetched", f)

if __name__ == "__main__":
    if "--fetch" in sys.argv: fetch(); sys.exit(0)
    D, GDP = deflators(); series = {}; rows = {}
    for ed in EDITIONS: rows[ed] = edition_rows(ed)
    cls18 = {re.sub(r"\s+", " ", str(col(r, "name"))).strip().lower(): (klass(str(col(r, "classification") or "")), detail(str(col(r, "classification") or ""))) for r in table(STAFF_ONLY["2018-19"][0]) if col(r, "name")}
    for r in rows["2018-19"]: r["class"], r["detail"] = cls18.get(r["name"].lower(), (r["class"], r["detail"]))
    key = lambda n: re.sub(r"\s+", " ", re.sub(r"[^a-z0-9& ]", "", n.lower().replace("&", "and"))).strip()
    names = list(EDITIONS)
    for ed, (_f, url, fy, _unit, ev) in EDITIONS.items():
        rs = rows[ed]; defl = D.get(fy); s = series.setdefault(ed, {})
        by, nd, mega = {}, {}, {}
        for r in rs:
            b = by.setdefault(r["class"], {"bodies": 0, "records": 0, "gov_funding": 0.0, "spend": 0.0, "staff": 0.0})
            b["bodies"] += r["bodies"]; b["records"] += 1; b["gov_funding"] += r["gov_funding"] or 0; b["spend"] += r["spend"] or 0; b["staff"] += r["staff"] or 0
            if r["detail"]: nd[r["detail"]] = nd.get(r["detail"], 0) + r["bodies"]
            m = MEGA.get(key(r["name"]))
            if m: mega[m] = r["gov_funding"]
        rest = sum((r["gov_funding"] or 0) for r in rs if not MEGA.get(key(r["name"])))
        nd_rest = sum((r["gov_funding"] or 0) for r in rs if r["class"] == "NDPB" and not MEGA.get(key(r["name"])))
        tot = {k: sum(v[k] for v in by.values()) for k in ("bodies", "records", "gov_funding", "spend", "staff")}
        real = (lambda x, defl=defl: x * 100 / defl if defl and x is not None else None)
        cov = sum(1 for r in rs if r["gov_funding"]) / len(rs)
        s.update({"money_coverage": round(cov, 2), "financial_year": fy, "file": url, "unit_evidence": ev, "by_class": by, "ndpb_detail": nd, "total": tot, "largest_bodies": mega,
                  "gov_funding_excl_largest": rest, "ndpb_gov_funding_excl_largest": nd_rest, "deflator_2025_26_100": defl,
                  "real": {"gov_funding": real(tot["gov_funding"]), "gov_funding_excl_largest": real(rest), "ndpb_gov_funding_excl_largest": real(nd_rest)},
                  "share_of_gdp": tot["gov_funding"] / GDP[fy] if fy in GDP else None, "money_series": ed not in FY_UNCERTAIN})
    # like-for-like: bodies present in consecutive money editions, real-terms change
    mon = [e for e in names if e not in FY_UNCERTAIN]
    for a, b in zip(mon, mon[1:], strict=False):
        fa, fb = {key(r["name"]): r["gov_funding"] for r in rows[a] if r["gov_funding"]}, {key(r["name"]): r["gov_funding"] for r in rows[b] if r["gov_funding"]}
        common = set(fa) & set(fb); da, db = D.get(EDITIONS[a][2]), D.get(EDITIONS[b][2])
        # outlier rule: a body whose funding moves more than threefold either way (or is negative) is set aside and listed:
        # these are source anomalies (units, part years, reclassifications), not trend
        odd = sorted(k for k in common if fa[k] <= 0 or fb[k] <= 0 or not (1 / 3 <= fb[k] / fa[k] <= 3))
        keep = [k for k in common if k not in odd and k not in MEGA]
        if keep and da and db:
            ra, rb = sum(fa[k] for k in keep) * 100 / da, sum(fb[k] for k in keep) * 100 / db
            series[b]["like_for_like"] = {"from": a, "bodies": len(keep), "real_change": round(rb / ra - 1, 4), "set_aside": odd, "entered": len(set(fb) - set(fa)), "left": len(set(fa) - set(fb))}
    (ROOT / "data" / "public-bodies-trends.json").write_text(json.dumps({"editions": series, "deflator_source": DEFLATOR[1], "deflator": {k: v for k, v in D.items() if k >= "2010-11"}}, indent=1))
    # ---- November 2020 baseline v today's register ----
    base = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources" / "opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    REG = {r[0]: r for r in base["r"]}
    def norm(s): s = (s or "").lower().replace("’", "'").replace("&", " and "); s = re.sub(r"[.,'`\"()]", "", s); s = re.sub(r"[-/]", " ", s); s = re.sub(r"^(the|board of trustees of the|trustees of the) ", "", s); return re.sub(r"\s+", " ", s).strip()
    IDX = {}
    for r in base["r"]:
        for n in {r[1], r[10].get("ons_name") or ""} - {""}: IDX.setdefault(norm(n), set()).add(r[0])
    now = {norm(r["name"]) for r in rows["2023/24"]}
    def variants(n):
        """Documented cleaning rules for the 2020 names; every variant must still match exactly one register record."""
        n = re.sub(r"\bher majesty'?s\b", "HM", n, flags=re.I); out = {n}
        out.add(re.sub(r",?\s*(excluding|with the exception of)\b.*$", "", n, flags=re.I))   # qualifiers on who is covered
        out.add(re.sub(r",\s*the$", "", n, flags=re.I))                                       # "National Archives, The"
        for v in list(out):
            out.add(re.sub(r"\s*\([^)]*\)\s*$", "", v))                                     # trailing acronym or alternative
            m = re.search(r"\(([^)]*)\)", v)
            if m and len(m.group(1)) > 6: out.add(m.group(1))                                  # alternative name in brackets
            for part in v.split("/"): out.add(part)                                            # "A / B"
            out.add(re.sub(r"\bpublicly known as\b.*$", "", v, flags=re.I))
        return {norm(x) for x in out if x.strip()}
    out = []
    for r in rows["2020"]:
        hits = set()
        for v in variants(r["name"]): hits |= IDX.get(v, set())
        if len(hits) > 1: hits = {h for h in hits if REG[h][4]} or hits
        rid = next(iter(hits)) if len(hits) == 1 else None; rec = REG.get(rid)
        succ = [REG[s][1] for s in (rec[16] if rec else []) if s in REG]
        if not rec: verdict = "not matched: for a person" if not hits else "ambiguous: for a person"
        elif rec[4]: verdict = "current"
        elif succ: verdict = "replaced: " + "; ".join(succ)
        else: verdict = "closed"
        out.append({"name_2020": r["name"], "department_2020": r["department"], "class_2020": r["class"], "register_id": rid or "", "register_status": ("open" if rec and rec[4] else "closed") if rec else "",
                    "closed": rec[8] if rec else "", "close_reason": (rec[17] or "") if rec else "", "in_directory_2023_24": norm(r["name"]) in now, "verdict": verdict})
    with open(ROOT / "data" / "reconciliation-2020.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, list(out[0])); w.writeheader(); w.writerows(out)
    from collections import Counter
    v = Counter(o["verdict"].split(":")[0] for o in out)
    print("2020 baseline:", len(out), "records;", dict(v), "; in 2023/24 directory:", sum(o["in_directory_2023_24"] for o in out))
    for ed, s in series.items():
        t, b = s["total"], s["by_class"]; ll = s.get("like_for_like") or {}
        print(f'{ed:8} FY {s["financial_year"]} ' + " ".join(f'{k[:4]}:{v["bodies"]}' for k, v in sorted(b.items())) + f' | NDPB-excl £{s["ndpb_gov_funding_excl_largest"]/1e9:5.1f}bn real £{(s["real"]["ndpb_gov_funding_excl_largest"] or 0)/1e9:5.1f}bn | staff {t["staff"]:7.0f} | cov {s["money_coverage"]:.0%} | L4L {ll.get("bodies","")} {ll.get("real_change","")} aside {len(ll.get("set_aside",[]))} | {"" if s["money_series"] else "COUNTS ONLY"}')
