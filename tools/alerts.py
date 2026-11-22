"""Feeds for the masthead on every page -> docs/data/alerts.json and docs/data/search-index.json

  alerts.json        notifications (the bell): grant deadlines coming up, sources that could not be read or are stale,
                     and the build itself; latest changes (the clock): changes to the state (renames, mergers, splits,
                     closures) and new UK treaties. Every item links to its source or to the page that explains it.
  search-index.json  every body's key, name, family and whether it is open, for the masthead search on pages that
                     don't load the whole register. Combined duplicate records are left out, as in the register.
Built from the published data only, with no clock: dates come from the data, so the files change only when it does.

  python tools/alerts.py             build and check
  python tools/alerts.py --negative  prove the checks fail when they should
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
VERB = {"changed_name": "was renamed", "merged": "merged", "split": "was split", "replaced": "was replaced", "closed": "closed", "left_gov": "left government", "devolved": "was devolved"}


def to_hash(k): return "org-" + re.sub(r"[^A-Za-z0-9-]", "", k.replace(":", "--"))  # the portal's own toHash


def safe_url(u): return isinstance(u, str) and (u.startswith("https://") or re.fullmatch(r"(index|nations|world|orgchart|funding|navigator|developers)\.html(#[\w=&%.-]*)?", u) is not None)


def build():
    h = (DOCS / "index.html").read_text()
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', h, re.S).group(1))
    acc = json.loads((DOCS / "accountability.json").read_text())
    st = json.loads((DOCS / "data/source-status.json").read_text())
    folded = {m for ms in acc.get("sa", {}).values() for m in ms}
    name = {r[0]: r[1] for r in D["r"]}
    news = acc.get("news", {})
    notes = [{"date": g["closes"], "kind": "Grant closes", "title": f"{g['title']} ({g['funder']})", "url": g["url"]} for g in news.get("closing", [])]
    notes += [{"date": st["as_of"], "kind": "Source not read", "title": f"{g['source']}: not read. {g['why']}", "url": "index.html#quality"} for g in st["not_read"]]
    notes += [{"date": st["as_of"], "kind": "Source stale", "title": f"{s['name']} was last read {s['read']}", "url": "index.html#quality"} for s in st["sources"] if s["status"] == "stale"]
    ok = sum(1 for s in st["sources"] if s["status"] == "current")
    notes.append({"date": st["as_of"], "kind": "Data rebuilt", "title": f"Register rebuilt from {ok} current sources; every expected count in range", "url": "index.html#quality"})
    ev = sorted((e for e in D["ev"] if e.get("date")), key=lambda e: (e["date"], e["id"]), reverse=True)[:12]
    changes = [{"date": e["date"][:10], "kind": "Change", "title": f"{e['name']} {VERB.get(e['event'], e['event'].replace('_', ' '))}" + (f": now {' and '.join(name.get(s, s) for s in e['successors'][:2])}" if e["successors"] else ""),
                "url": "index.html#" + to_hash(next((s for s in e["successors"] if s in name), e["id"]))} for e in ev]
    changes += [{"date": t["date"], "kind": "Treaty", "title": t["title"], "url": t["url"]} for t in news.get("latest_treaties", [])]
    changes.sort(key=lambda x: (x["date"], x["title"]), reverse=True)
    notes.sort(key=lambda x: (x["date"], x["title"]), reverse=True)
    alerts = {"about": "Notifications and latest changes for the masthead of every page. Dates come from the data; built by tools/alerts.py.", "as_of": st["as_of"], "notifications": notes, "changes": changes[:15]}
    index = [[r[0], r[1], D["fam"][r[2]], 1 if r[4] else 0] for r in D["r"] if r[0] not in folded]
    return alerts, index


def check(alerts, index):
    e = []
    for part in ("notifications", "changes"):
        if not alerts[part]: e.append(f"no {part}")
        for x in alerts[part]:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", x["date"]): e.append(f"{part}: bad date {x['date']!r}")
            if not safe_url(x["url"]): e.append(f"{part}: link refused (only https and the portal's own pages): {x['url']!r}")
            if not x["title"].strip(): e.append(f"{part}: empty title")
    if not any(x["kind"] == "Source not read" and "International Monetary Fund" in x["title"] for x in alerts["notifications"]): e.append("known answer: the IMF source not read is a notification")
    if not 3000 <= len(index) <= 4000: e.append(f"search index has {len(index)} bodies")
    if not any(r[1] == "Met Office" for r in index): e.append("known answer: the Met Office is searchable")
    return e


def main():
    alerts, index = build()
    if "--negative" in sys.argv:
        bad = json.loads(json.dumps(alerts)); bad["changes"][0]["url"] = "javascript:alert(1)"
        bad2 = json.loads(json.dumps(alerts)); bad2["notifications"] = []
        if not check(bad, index) or not check(bad2, index): sys.exit("alerts negative: not caught")
        print("alerts negative: a javascript: link and an empty feed are both caught"); return
    e = check(alerts, index)
    if e: sys.exit("alerts: " + "; ".join(e))
    (DOCS / "data/alerts.json").write_text(json.dumps(alerts, ensure_ascii=False, indent=1) + "\n")
    (DOCS / "data/search-index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"alerts: {len(alerts['notifications'])} notifications, {len(alerts['changes'])} changes | search index: {len(index)} bodies")


if __name__ == "__main__":
    main()
