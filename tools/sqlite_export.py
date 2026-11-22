"""One SQLite file of the published data, so anyone can query it in the browser with Datasette Lite (nothing to install,
nothing for us to run). Also writes data/org-id.json: each body's identifiers in the org-id.guide form used by IATI,
360Giving and the Open Contracting Data Standard (GB-COH for Companies House numbers, GB-CHC for charities in England and
Wales). Only codes the register already holds are used. --negative proves the checks fail when they should."""
import csv, json, pathlib, re, sqlite3, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]; DOCS = ROOT / "docs"
ORGID = {"companies_house": ("GB-COH", re.compile(r"^[A-Z0-9]{8}$")), "charity_ew": ("GB-CHC", re.compile(r"^\d{6,8}$"))}


def org_ids(R):
    out = {}
    for r in R:
        ids = [f"{p}-{r[10][k]}" for k, (p, ok) in ORGID.items() if r[10].get(k) and ok.match(str(r[10][k]))]
        if ids: out[r[0]] = ids
    return out


def check_orgid(o):
    return [k for k, v in o.items() for x in v if not re.match(r"^GB-(COH-[A-Z0-9]{8}|CHC-\d{6,8})$", x)]


def build():
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    R = D["r"]; o = org_ids(R)
    cl = json.loads((ROOT / "data/classification.json").read_text())["bodies"]
    web = json.loads((ROOT / "data/websites.json").read_text()); nat = json.loads((ROOT / "data/body-nations.json").read_text())
    sa = json.loads((ROOT / "data/same-as.json").read_text())["groups"]; canon = {m: c for c, g in sa.items() for m in g["members"]}
    nat = nat.get("bodies", nat)
    db = DOCS / "opengovernment-uk.db"
    if db.exists(): db.unlink()
    con = sqlite3.connect(db); cur = con.cursor()
    cur.execute("CREATE TABLE bodies (id TEXT PRIMARY KEY, name TEXT, family TEXT, kind TEXT, open INTEGER, type TEXT, purpose TEXT, activity TEXT, reach TEXT, nations TEXT, website TEXT, website_source TEXT, same_as TEXT, org_ids TEXT, identifiers TEXT)")
    for r in R:
        c = cl.get(r[0], {}); n = nat.get(r[0]); n = n if isinstance(n, list) else (n or {}).get("codes", []) if isinstance(n, dict) else []
        w = web.get(r[0], ["", ""])
        cur.execute("INSERT INTO bodies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (r[0], r[1], D["fam"][r[2]] if isinstance(r[2], int) and isinstance(D.get("fam"), list) else str(r[2]), r[3], int(bool(r[4])),
                    c.get("btype"), c.get("purpose"), c.get("activity"), c.get("reach"), ",".join(n), w[0], w[1], canon.get(r[0], ""), ",".join(o.get(r[0], [])), json.dumps(r[10], ensure_ascii=False)))
    for name in ("edges", "accountable-owner", "ppp", "concordance"):
        f = DOCS / f"{name}.csv"
        if not f.exists(): continue
        rows = list(csv.reader(f.open(encoding="utf-8")))
        if not rows: continue
        t = name.replace("-", "_"); cols = [re.sub(r"\W+", "_", h).strip("_") or f"c{i}" for i, h in enumerate(rows[0])]
        cur.execute(f'CREATE TABLE {t} ({", ".join(f"{c!s} TEXT" for c in cols)})')  # noqa: S608 names come from our own CSV headers, cleaned to word characters
        cur.executemany(f'INSERT INTO {t} VALUES ({",".join("?" * len(cols))})', [x + [""] * (len(cols) - len(x)) for x in rows[1:]])  # noqa: S608
    INTL = json.loads((ROOT / "data/international.json").read_text())
    cur.execute("CREATE TABLE international (body TEXT, grp TEXT, way_in TEXT, lead_id TEXT, lead_name TEXT, role TEXT, sources TEXT)")
    for b in INTL["bodies"]:
        for ld in b["lead"]:
            cur.execute("INSERT INTO international VALUES (?,?,?,?,?,?,?)", (b["name"], INTL["groups"][b["group"]], b["way_in"], ld["id"], ld["name"], b["role"], " ".join(x["url"] for x in b["evidence"])))
    T = json.loads((ROOT / "data/territories.json").read_text())["bodies"]
    cur.execute("CREATE TABLE territory_bodies (id TEXT, name TEXT, jurisdiction TEXT, grp TEXT, branch TEXT, type TEXT, website TEXT, constitutional INTEGER)")
    cur.executemany("INSERT INTO territory_bodies VALUES (?,?,?,?,?,?,?,?)", [(b["id"], b["name"], b["jurisdiction"], b["group"], b["branch"], b["type"], b.get("web", ""), int(bool(b.get("constitutional")))) for b in T])
    io_ = json.loads((ROOT / "data/intl-ownership.json").read_text())  # the UK state's shares and votes in international financial institutions
    cur.execute("CREATE TABLE intl_ownership (institution TEXT, short TEXT, lei TEXT, wikidata TEXT, uk_share_of_votes REAL, uk_share_of_subscriptions REAL, uk_votes INTEGER, members INTEGER, as_of TEXT, source TEXT)")
    cur.executemany("INSERT INTO intl_ownership VALUES (?,?,?,?,?,?,?,?,?,?)", [(r["name"], r["short"], r["lei"], r["wikidata"], r["share_of_votes"], r.get("share_of_subscriptions"), r["votes"], r["members"], r["as_of"], r["source"]["url"]) for r in io_["rows"]])
    co = json.loads((ROOT / "data/cooperation.json").read_text())  # cooperation by country
    cur.execute("CREATE TABLE cooperation (country TEXT, commonwealth INTEGER, trade_agreements TEXT, tax_treaties INTEGER, treaties INTEGER)")
    cur.executemany("INSERT INTO cooperation VALUES (?,?,?,?,?)", [(v["display"], int(bool(v["commonwealth"])), "; ".join(x["agreement"] for x in v["trade"]), len(v["tax"]), v["treaty_total"]) for v in co["countries"].values()])
    con.commit(); n = cur.execute("SELECT count(*) FROM bodies").fetchone()[0]; con.execute("VACUUM"); con.close()
    (ROOT / "data/org-id.json").write_text(json.dumps(o, separators=(",", ":")))
    return n, o, db


def main():
    if "--negative" in sys.argv:
        bad = {"x": ["GB-COH-123"], "y": ["GB-CHC-ABC"]}
        if len(check_orgid(bad)) != 2: sys.exit("sqlite_export negative: a malformed org-id was not caught")
        print("sqlite_export negative: both malformed org-ids caught"); return
    n, o, db = build()
    e = check_orgid(o)
    if e: sys.exit(f"sqlite_export: malformed org-ids for {e[:3]}")
    if n < 3000: sys.exit(f"sqlite_export: only {n} bodies written")
    print(f"sqlite_export: {n} bodies; {db.stat().st_size // 1024} KB; org-ids for {len(o)} bodies")


if __name__ == "__main__":
    main()
