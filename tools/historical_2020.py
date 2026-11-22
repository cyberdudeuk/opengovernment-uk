"""Historical layer from the 2020 public bodies compilation (built on the 2019 Public Bodies edition with WGA, NAO
government companies and ONS lists). Only its non-personal columns were read; the raw rows are not redistributed
(sources/evidence/pb-nov2020-nonpersonal.tsv is gitignored); its SHA-256 is recorded so the copy can be verified.
Each 2020 entry is matched to a register record by exact cleaned name only (safe-fail). Writes data/historical-2020.json."""
import collections, csv, hashlib, html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]; SRC = ROOT / "sources" / "evidence" / "pb-nov2020-nonpersonal.tsv"
EXPECTED_SHA = "4a4f00bebf4c1b0305fb202b15746bb5584d297311ff7d67731d1fe4fb2b2c42"  # computed in the browser at source
PERSONAL = re.compile(r"\b(chair|chief executive|ceo|director|name of|contact|email|phone|sponsor team)\b", re.I)

def clean(s):
    s = html.unescape(str(s or "")).lower().replace("&", " and "); s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"\b(the|ltd|limited|plc)\b", " ", s)).strip()

def build():
    raw = SRC.read_bytes(); sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA: sys.exit(f"pb-2020 fingerprint mismatch: {sha}")  # fail closed
    rows = list(csv.reader(raw.decode("utf-8").splitlines(), delimiter="\t")); head, rows = rows[0], rows[1:]
    if any(PERSONAL.search(h) for h in head): sys.exit(f"personal column present: {head}")
    D = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources/opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
    idx = collections.defaultdict(list)
    for r in D["r"]: idx[clean(r[1])].append(r)
    matched, unmatched = [], []
    for r in rows:
        name, typ, cls, govco, key_alb, wga, dept = (html.unescape(x).strip() for x in r[:7])
        hits = idx.get(clean(name), [])
        rec = {"name_2020": name, "type_2020": typ, "classification_2020": cls, "department_2020": dept,
               "govco": govco == "Yes", "key_alb": key_alb in ("Y", "Yes"), "wga": wga == "Y"}
        if len(hits) >= 1:
            open_now = [h for h in hits if h[4]]
            rec.update({"ids": [h[0] for h in hits], "open_now": bool(open_now)}); matched.append(rec)
        else: unmatched.append(rec)
    return sha, head, matched, unmatched

def check(matched, unmatched, total):
    p = []
    if len(matched) + len(unmatched) != total: p.append("rows not all accounted for")
    if any(PERSONAL.search(k) for r in matched + unmatched for k in r): p.append("personal field in output")
    return p

if __name__ == "__main__":
    sha, head, matched, unmatched = build(); total = len(matched) + len(unmatched)
    if "--negative" in sys.argv:
        bad = matched + [{"chair": "x"}]; ok = bool(check(bad, unmatched, total + 1)); print("caught personal field" if ok else "MISSED personal field"); sys.exit(0 if ok else 1)
    probs = check(matched, unmatched, total)
    out = {"source": "2020 public bodies compilation (built on the 2019 Public Bodies edition, WGA, NAO government companies and ONS lists); non-personal columns only; not redistributed",
           "sha256": sha, "columns_read": head, "rows": total, "matched": len(matched), "matched_closed_now": sum(1 for m in matched if not m["open_now"]),
           "not_matched_by_exact_name": len(unmatched), "note": "an unmatched name usually means a renamed or differently written body, not a closure", "bodies": matched, "unmatched": unmatched}
    (ROOT / "data/historical-2020.json").write_text(json.dumps(out, indent=1))
    print(f"rows {total}, matched {len(matched)} (closed now {out['matched_closed_now']}), not matched by exact name {len(unmatched)}, problems {probs}")
    sys.exit(1 if probs else 0)
