"""Check every source against what it is expected to give, and publish how each one stands -> docs/data/source-status.json

Reads sources/manifest.json (written by each fetch: publisher, address, licence, fingerprint, when read), the date each
evidence snapshot was read, and sources/expectations.json (set by hand: whether the source is official, how often it
changes, and count ranges). Then:
  - every count range is checked; one outside its range stops the build (fail closed);
  - each source is reported as current, stale (read more than twice its change interval before the build's latest
    read) or not read, with the reason when it could not be read. Stale is reported, not failed: a dated snapshot is
    honest when labelled. Ages are measured from the build's own latest read, not the clock, so the file only changes
    when the data does.

  python tools/sources_check.py             check and publish
  python tools/sources_check.py --negative  prove the checks fail when they should
"""
import csv, datetime as dt, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/data/source-status.json"


def count(a):
    p = ROOT / a["file"]
    if a["count"] == "rows":
        with open(p, newline="") as f: return sum(1 for _ in csv.reader(f)) - 1
    if a["count"] == "lines": return sum(1 for ln in p.read_text().splitlines() if ln.strip())
    d = json.loads(p.read_text())
    for k in a.get("path", "").split(".") if a.get("path") else []: d = d[k]
    if a.get("where"): d = {k: v for k, v in d.items() if v.get(a["where"])} if isinstance(d, dict) else [v for v in d if v.get(a["where"])]
    return d if a["count"] == "value" else len(d)


def check_counts(exp):
    res, bad = [], []
    for a in exp["assertions"]:
        try: n = count(a)
        except (KeyError, FileNotFoundError, TypeError, ValueError) as e: n, err = None, f"could not count: {type(e).__name__} {e}"
        else: err = None
        ok = n is not None and a["min"] <= n <= a["max"]
        res.append({"what": a["what"], "file": a["file"], "count": n, "min": a["min"], "max": a["max"], "ok": ok, "why": a["why"]})
        if not ok: bad.append(f"{a['what']}: {err or n} not in {a['min']}-{a['max']}")
    return res, bad


def day(s): return dt.date.fromisoformat(str(s)[:10]) if s else None


def status():
    man = json.loads((ROOT / "sources/manifest.json").read_text())
    exp = json.loads((ROOT / "sources/expectations.json").read_text())
    src = []
    for k, e in exp["sources"].items():
        if k in man:
            m = man[k]; row = {"key": k, "name": m["name"], "publisher": m.get("owner", ""), "url": m.get("url", ""), "licence": m.get("licence", ""), "read": str(m.get("retrieved", ""))[:10], "fingerprint": m.get("sha256", "")}
        else:
            ev = json.loads((ROOT / e["evidence"]).read_text())
            row = {"key": k, "name": e["name"], "publisher": "", "url": ev.get("source") or ev.get("url") or "", "licence": ev.get("licence", ""), "read": str(ev.get("read") or ev.get("as_of") or "")[:10], "fingerprint": ev.get("sha256", ""), "evidence": e["evidence"]}
        row.update(official=e["official"], frequency_days=e["frequency_days"])
        if e.get("note"): row["note"] = e["note"]
        src.append(row)
    missing = [k for k in man if k not in exp["sources"]]
    latest = max(day(r["read"]) for r in src if r["read"])
    for r in src:
        d, f = day(r["read"]), r["frequency_days"]
        r["age_days"] = (latest - d).days if d else None
        r["status"] = "not read" if not d else "current" if not f or r["age_days"] <= 2 * f else "stale"
        if d and f: r["next_due"] = (d + dt.timedelta(days=f)).isoformat()
    # parts of sources that could not be read, with the reason (never worked around)
    gaps = [{"source": g["name"], "url": g["url"], "status": "not read", "why": g["why"]} for g in json.loads((ROOT / "data/intl-ownership.json").read_text())["not_read"]]
    terr = json.loads((ROOT / "data/territories.json").read_text())["meta"]
    if terr.get("blocked"): gaps.append({"source": "Isle of Man Government website", "url": "https://www.gov.im/", "status": "not read", "why": terr["blocked"]})
    res, bad = check_counts(exp)
    if missing: bad.append("sources with no expectations: " + ", ".join(missing))
    return {"about": "How each source stands at this build: when it was read, how often it changes, whether it is current, and the parts that could not be read and why. Ages count from the build's latest read (" + latest.isoformat() + "). Counts are checked against expected ranges; a count outside its range stops the build.",
            "as_of": latest.isoformat(), "sources": src, "not_read": gaps, "counts": res}, bad


def main():
    if "--negative" in sys.argv:
        exp = json.loads((ROOT / "sources/expectations.json").read_text())
        a0 = next(a for a in exp["assertions"] if a["what"] == "Commonwealth members"); a0["min"] = a0["max"] = 1
        _, bad = check_counts(exp)
        b2 = check_counts({"assertions": [{"what": "x", "file": "data/cooperation.json", "path": "no_such_key", "count": "items", "min": 0, "max": 9, "why": ""}]})[1]
        if not bad or not b2: sys.exit("sources negative: not caught")
        print("sources negative: an out-of-range count and an uncountable path are both caught"); return
    s, bad = status()
    if bad: sys.exit("sources: " + "; ".join(bad))
    OUT.write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n")
    from collections import Counter
    print("sources:", dict(Counter(r["status"] for r in s["sources"])), "| parts not read:", len(s["not_read"]), "| counts in range:", len(s["counts"]))


if __name__ == "__main__":
    main()
