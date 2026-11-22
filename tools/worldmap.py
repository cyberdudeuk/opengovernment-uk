"""World map of the UK's treaty partners -> data/worldmap.json

The map is drawn once, here, so the page carries plain SVG paths and no mapping library:
  geometry  world-atlas 2.0.2 (ISC licence, from Natural Earth public-domain data), vendored in sources/vendor
  projection Equal Earth (equal-area, so no country looks bigger than it is), 1000 units wide
  partners  each treaty partner as GOV.UK titles it, placed by exact country name or by sources/evidence/treaty-partners.json;
            a partner that is neither fails the build (never guessed)
States too small to see at this scale are drawn as dots, so Singapore, Malta and Bahrain still show.

  python tools/worldmap.py            build and check
  python tools/worldmap.py --negative prove the checks fail when they should
"""
import collections, gzip, json, math, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "sources/vendor/world-atlas-2.0.2-countries-50m.json"
EV = ROOT / "sources/evidence/treaty-partners.json"
W = 1000
A1, A2, A3, A4, M = 1.340264, -0.081106, 0.000893, 0.003796, math.sqrt(3) / 2
XMAX, YMAX = 2.7066297319, 1.3173627591
S = W / (2 * XMAX)
H = round(2 * YMAX * S)


def project(lon, lat):  # Equal Earth (Šavrič, Patterson and Jenny, 2018)
    t = math.asin(M * math.sin(math.radians(lat)))
    t2, t6 = t * t, t ** 6
    x = 2 * math.sqrt(3) * math.radians(lon) * math.cos(t) / (3 * (9 * A4 * t6 * t2 + 7 * A3 * t6 + 3 * A2 * t2 + A1))
    y = t * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return round((x + XMAX) * S), round((YMAX - y) * S)


def arcs(topo):
    (sx, sy), (tx, ty) = topo["transform"]["scale"], topo["transform"]["translate"]
    out = []
    for arc in topo["arcs"]:
        x = y = 0; pts = []
        for dx, dy in arc:
            x += dx; y += dy; pts.append(project(x * sx + tx, y * sy + ty))
        out.append(pts)
    return out


def ring(ix, A):
    pts = []
    for i in ix:
        a = A[i] if i >= 0 else A[~i][::-1]
        pts += a[1:] if pts else a
    clean = [p for k, p in enumerate(pts) if k == 0 or p != pts[k - 1]]
    return clean


def path(rings):
    d = []
    for r in rings:
        if len(r) < 3: continue
        s = f"M{r[0][0]},{r[0][1]}"
        for (x0, y0), (x1, y1) in zip(r, r[1:], strict=False):
            s += f"l{x1 - x0},{y1 - y0}"
        d.append(s + "z")
    return "".join(d)


def build():
    topo = json.loads(ATLAS.read_text()); A = arcs(topo)
    shapes, dots = {}, {}
    for g in topo["objects"]["countries"]["geometries"]:
        name = g["properties"]["name"]
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]] if g["type"] == "Polygon" else []
        rings = [ring(r, A) for p in polys for r in p]
        allpts = [p for r in rings for p in r]
        if not allpts: continue
        xs, ys = [p[0] for p in allpts], [p[1] for p in allpts]
        big = [r for r in rings if len(set(r)) >= 4]
        if big and (max(xs) - min(xs) >= 3 or max(ys) - min(ys) >= 3): shapes[name] = path(big)
        else: dots[name] = [round(sum(xs) / len(xs)), round(sum(ys) / len(ys))]
    ev = json.loads(EV.read_text())
    for name, x in ev.get("extra_dots", {}).items():  # places too small for the atlas, from Wikidata coordinates
        if name not in shapes and name not in dots: dots[name] = list(project(x["lon"], x["lat"]))
    rel = json.loads((ROOT / "data/relations.json").read_text())
    known = set(shapes) | set(dots)
    place, problems = {}, []
    for p in sorted({t["partner"] for t in rel["treaties"] if t["partner"]}):
        if p in known: place[p] = [p]
        elif p in ev["aliases"]: place[p] = ev["aliases"][p]
        elif p in ev["organisations"] or p in ev["former_states"]: continue
        else: problems.append(f"treaty partner not placed: {p!r} (add it to treaty-partners.json)")
    problems += [f"alias points at no map country: {a} -> {c}" for a, cs in ev["aliases"].items() for c in cs if c not in known]
    return {"w": W, "h": H, "shapes": shapes, "dots": dots, "place": place,
            "not_drawn": {"organisations": ev["organisations"], "former_states": ev["former_states"]},
            "source": "world-atlas 2.0.2 (ISC), from Natural Earth (public domain); Equal Earth projection"}, problems


def check(m, problems):
    e = list(problems)
    for partner, country in [("USA", "United States of America"), ("Rep. of Korea", "South Korea"), ("France", "France")]:  # known answers
        if country not in m["place"].get(partner, []): e.append(f"known answer: {partner} should be on {country}")
    for small in ["Singapore", "Malta", "Bahrain"]:  # tiny states must still be visible
        if small not in m["dots"] and small not in m["shapes"]: e.append(f"{small} is not drawn")
    if "United States of America" not in m["shapes"]: e.append("the United States has no shape")
    n = len(gzip.compress(json.dumps(m, separators=(",", ":")).encode(), 9))
    if n > 120_000: e.append(f"map is {n:,} bytes gzip; budget 120,000")
    return e


def main():
    m, problems = build()
    if "--negative" in sys.argv:
        bad = json.loads(json.dumps(m)); bad["place"]["USA"] = ["Canada"]; bad["dots"].pop("Singapore", None); bad["shapes"].pop("Singapore", None)
        caught = [bool(check(bad, [])), bool(check(m, ["treaty partner not placed: 'Atlantis'"]))]
        if not all(caught): sys.exit(f"worldmap negative: {caught.count(False)} not caught")
        print("worldmap negative: all breakers caught"); return
    e = check(m, problems)
    if e: sys.exit("worldmap: " + "; ".join(e))
    (ROOT / "data/worldmap.json").write_text(json.dumps(m, separators=(",", ":"), ensure_ascii=False))
    print(f"worldmap: {len(m['shapes'])} shapes, {len(m['dots'])} dots, {len(m['place'])} partners placed; "
          f"{len(gzip.compress(json.dumps(m, separators=(',', ':')).encode(), 9)):,} bytes gzip; size {W}x{H}")
    print("countries per partner:", collections.Counter(len(v) for v in m["place"].values()))


if __name__ == "__main__":
    main()
