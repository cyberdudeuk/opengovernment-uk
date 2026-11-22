"""Reconcile peer reference lists from the National Data Library catalogue with the register, record by record.
Exact cleaned-name matching only (the build's own rule); anything else is reported unmatched, never guessed.
First peer: FCDO's IATI Organisation Identifiers for UK government organisations (GB-GOV-n)."""
import json, pathlib, re, sys
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', (ROOT / "sources" / "opengovernment-uk-0.2.2.html").read_text(), re.S).group(1))
def norm(s): s = (s or "").lower().replace("’", "'").replace("&", " and "); s = re.sub(r"[.,'`\"()]", "", s); s = re.sub(r"[-/]", " ", s); return re.sub(r"\s+", " ", re.sub(r"^the ", "", s)).strip()
IDX = {}
for r in BASE["r"]:
    for n in {r[1], r[10].get("ons_name") or "", r[18] or ""} - {""}: IDX.setdefault(norm(n), set()).add(r[0])
OPEN = {r[0]: bool(r[4]) for r in BASE["r"]}
def match(name):
    hits = IDX.get(norm(name), set())
    if len(hits) > 1: hits = {h for h in hits if OPEN[h]} or hits
    return (next(iter(hits)), "name, cleaned") if len(hits) == 1 else (None, "ambiguous" if hits else "no register record with this name")
src = sys.argv[1] if len(sys.argv) > 1 else ROOT / "sources" / "peer-iati-organisation-identifiers.ods"
df = pd.read_excel(src, engine="odf", sheet_name="Organisation_Identifiers")
rows = []
for _, r in df.iterrows():
    name = None if pd.isna(r["Organisation"]) else str(r["Organisation"]).strip()
    rid, how = match(name) if name else (None, "no name given (deprecated code)")
    rows.append({"iati_id": r["Org ID"], "name": name, "status": r["Status"], "note": None if pd.isna(r["Note"]) else str(r["Note"]), "register_id": rid, "how": how})
out = {"peer": "IATI Organisation Identifiers for UK government organisations (FCDO)", "catalogue": "https://www.data.gov.uk/dataset/3daf2e08-170e-4aa0-850b-bde231a2031a",
       "file": "https://assets.publishing.service.gov.uk/media/656a277f1104cf0013fa73cf/iati-organisation-identifiers.ods", "rows": rows,
       "matched": sum(1 for r in rows if r["register_id"]), "named": sum(1 for r in rows if r["name"])}
(ROOT / "data" / "peer-iati.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(f'{out["matched"]} of {out["named"]} named IATI organisations matched exactly ({len(rows)} codes incl. deprecated)')
for r in rows:
    if r["name"] and not r["register_id"]: print("  unmatched:", r["iati_id"], r["name"], "—", r["how"])
