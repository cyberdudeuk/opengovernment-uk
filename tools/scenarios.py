"""Three lenses on the arm's-length body landscape to 2030: evolution, reform, revolution.
MODELLED: every output is the arithmetic of the stated assumptions on the 2023/24 baseline; nothing here is a forecast
or a government plan. Change ASSUMPTIONS and rerun. Baseline facts come from the Public Bodies Directory 2023/24 (via
tools/trends.py); events come from cited sources in documentation/trends-and-futures-2030.md."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = {  # Public Bodies Directory 2023/24, computed by tools/trends.py and the profile in the trends document
    "entries": 251, "staff_fte": 397003, "admin_rdel_gbp": 5.5e9,
    "admin_by_size_gbp": {"under_50": 6e6, "50_499": 747e6, "500_plus": 4742e6},
    "entries_by_size": {"under_50": 98, "50_499": 77, "500_plus": 76},
    "advisory_ndpbs": 64, "advisory_admin_gbp": 22.3e6, "bodies_with_regulatory_powers": 56,
    "nhs_england": {"staff_fte": 14599, "admin_rdel_gbp": 1.892e9},
}
KNOWN = {  # already decided, sourced: applies in every lens
    "closed_or_merged_under_2025_review": 16,       # Cabinet Office, reported April 2026 (includes NHS England)
    "nhs_england_annual_saving_gbp": 1.0e9,        # Minister of State, Health Bill committee, June 2026: "up to about £1 billion" by end of Parliament
}
ASSUMPTIONS = {
    "evolution": {"label": "Evolution: the present review runs its course",
                  "net_change_per_year_after_2026": -5,   # history: dated closures 9-20 a year against 1-7 openings (lower bounds)
                  "further_closures_2026": 4, "avg_admin_released_per_closure_gbp": 5e6,
                  "large_body_efficiency": 0.0},
    "reform": {"label": "Reform: consolidate by function, share the back office",
               "advisory_ndpbs_after": 10,             # advisory NDPBs folded into about ten standing expert councils
               "regulators_merged_away": 15,           # sector regulators consolidated (water already legislated)
               "agencies_repatriated": 10, "large_body_efficiency": 0.10, "medium_body_efficiency": 0.10},
    "revolution": {"label": "Revolution: AI-enabled, digitally native by default",
                   "advisory_ndpbs_after": 0,          # independent advice on demand from standing panels with AI evidence synthesis
                   "regulators_merged_away": 30, "agencies_repatriated": 30,
                   "new_bodies_need_sunset_clause": True,
                   "large_body_efficiency": (0.20, 0.30), "medium_body_efficiency": 0.20},
}

def run():
    b, k, a = BASE, KNOWN, ASSUMPTIONS; out = {"modelled": True, "prices": "2023-24 cash, admin RDEL only (running costs, not programme spend)", "baseline": b, "known": k, "lenses": {}}
    start = b["entries"] - k["closed_or_merged_under_2025_review"]
    e = a["evolution"]; n = start - e["further_closures_2026"] + 4 * e["net_change_per_year_after_2026"]
    closed = b["entries"] - n
    out["lenses"]["evolution"] = {"label": e["label"], "entries_2030": n, "change": round(n / b["entries"] - 1, 3),
                                  "admin_released_gbp": k["nhs_england_annual_saving_gbp"] + (closed - 1) * e["avg_admin_released_per_closure_gbp"]}
    for name in ("reform", "revolution"):
        r = a[name]
        n = start - (b["advisory_ndpbs"] - r["advisory_ndpbs_after"]) - r["regulators_merged_away"] - r["agencies_repatriated"]
        eff = r["large_body_efficiency"]; lo, hi = (eff, eff) if not isinstance(eff, tuple) else eff
        large = b["admin_by_size_gbp"]["500_plus"] - b["nhs_england"]["admin_rdel_gbp"]
        rng = [k["nhs_england_annual_saving_gbp"] + large * x + b["admin_by_size_gbp"]["50_499"] * r["medium_body_efficiency"] + b["advisory_admin_gbp"] * (1 - r["advisory_ndpbs_after"] / b["advisory_ndpbs"]) for x in (lo, hi)]
        out["lenses"][name] = {"label": r["label"], "entries_2030": n, "change": round(n / b["entries"] - 1, 3), "admin_released_gbp": rng[0] if lo == hi else rng}
    for v in out["lenses"].values():
        x = v["admin_released_gbp"]; v["admin_released_share"] = round((x if not isinstance(x, list) else x[1]) / b["admin_rdel_gbp"], 3)
    return out

if __name__ == "__main__":
    o = run(); (ROOT / "data" / "scenarios-2030.json").write_text(json.dumps(o, indent=1))
    for k, v in o["lenses"].items():
        x = v["admin_released_gbp"]; xs = f"£{x/1e9:.1f}bn" if not isinstance(x, list) else f"£{x[0]/1e9:.1f}-{x[1]/1e9:.1f}bn"
        print(f"{k:10} entries 2030 {v['entries_2030']:4}  ({v['change']:+.0%})  admin released {xs} a year (up to {v['admin_released_share']:.0%} of £5.5bn)")
