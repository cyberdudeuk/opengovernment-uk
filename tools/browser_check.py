"""Load every published page in a real browser and fail on what a code read misses (OG-D57, OG-D70, OG-D71 class)

For each page, at a phone width (390) and a desktop width (1280), in light and dark:
  - no script errors;
  - no sideways overflow of the page;
  - nothing in the masthead off-screen, and the masthead tools don't overlap each other or the theme switch;
  - the notifications panel opens, shows items, and closes with Escape;
  - search shows suggestions for a known body (the Met Office).
  - the world map labels countries and keeps labels when zoomed; the bullseye carries its 15 icons and 7 nation codes (OG-D79).
Serves docs/ on a local port; nothing is fetched from the internet.

  python tools/browser_check.py             run
  python tools/browser_check.py --negative  prove a page with a script error and overflow is caught
"""
import functools, http.server, pathlib, socketserver, sys, threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from design import PAGES  # noqa: E402  every published page

MAST = """(() => { const W = document.documentElement.clientWidth, m = document.querySelector('.og-shell-mast .in, .mast .in'); if (!m) return ['no masthead'];
  const vis = [...m.querySelectorAll(':scope > *, .og-tools > *')].filter(e => e.offsetParent && !e.classList.contains('og-pop') && e.getBoundingClientRect().width > 0);
  const out = vis.filter(e => e.getBoundingClientRect().right > W + 1).map(e => 'off-screen: ' + (e.id || e.className));
  const box = [...m.querySelectorAll('.og-search, #ogBell, #ogChanges, #ogTheme, #themeBtn')].filter(e => e.offsetParent).map(e => [e.id || e.className, e.getBoundingClientRect()]);
  for (let i = 0; i < box.length; i++) for (let j = i + 1; j < box.length; j++) { const a = box[i][1], b = box[j][1];
    if (a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 1 && b.top < a.bottom - 1) out.push('overlap: ' + box[i][0] + ' / ' + box[j][0]); }
  const s = document.querySelector('.og-search'); if (s && s.offsetParent && s.getBoundingClientRect().width < 140) out.push('search squeezed to ' + Math.round(s.getBoundingClientRect().width) + 'px');
  return out; })()"""


def serve(root):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Quiet, directory=str(root))
    srv = socketserver.TCPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def check(base, pages):
    from playwright.sync_api import sync_playwright
    bad = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for w in (390, 1280):
            for scheme in ("light", "dark"):
                for n in pages:
                    pg = b.new_page(viewport={"width": w, "height": 900}, color_scheme=scheme); errs = []
                    pg.on("pageerror", lambda e, errs=errs: errs.append(str(e)[:160]))
                    pg.goto(f"{base}/{n}"); pg.wait_for_timeout(1800 if n == "index.html" else 700)
                    tag = f"{n} {w}px {scheme}"
                    # OG-D79: map labels and bullseye icons must render (not just exist in the source).
                    # Runs before the tab loop: opening other tabs hides the map (width 0, no labels).
                    if n == "world.html":
                        pg.wait_for_timeout(400); n0 = pg.locator(".wlab text").count()
                        need = 20 if w >= 1024 else 3  # a phone labels only the largest countries until zoomed
                        if n0 < need: bad.append(f"{tag}: world map shows {n0} country labels (expected {need} or more)")
                        if pg.locator("[data-z=in]").count():
                            pg.click("[data-z=in]"); pg.wait_for_timeout(300)
                            if pg.locator(".wlab text").count() == 0: bad.append(f"{tag}: zoomed map lost every label")
                    if n == "index.html":
                        g, c = pg.locator("#bullseye .glyph").count(), pg.locator("#bullseye .ncode").count()
                        if (g, c) != (15, 7): bad.append(f"{tag}: bullseye has {g} icons and {c} nation codes (expected 15 and 7)")
                    bad += [f"{tag}: script error: {e}" for e in errs]
                    ov = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
                    if ov > 1: bad.append(f"{tag}: page overflows sideways by {ov}px")
                    bad += [f"{tag}: {x}" for x in pg.evaluate(MAST)]
                    for i in range(pg.locator("main [role=tab]:visible").count()):  # every tab, not just the first (OG-D73)
                        t = pg.locator("main [role=tab]:visible").nth(i); name = (t.inner_text() or "").strip()[:30]
                        t.click(); pg.wait_for_timeout(150)
                        ov = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
                        if ov > 1: bad.append(f"{tag} tab '{name}': page overflows sideways by {ov}px")
                        if w == 390:  # stress: monospace a little wider, as some browsers draw it (OG-D74)
                            pg.add_style_tag(content="code,pre,kbd,samp{letter-spacing:.06em}")
                            ov = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
                            if ov > 1: bad.append(f"{tag} tab '{name}': overflows by {ov}px when code text is slightly wider")
                    if scheme == "light" and pg.locator("#ogBell").count():
                        pg.click("#ogBell"); pg.wait_for_timeout(500)
                        if pg.locator("#ogBellPanel a").count() == 0: bad.append(f"{tag}: notifications panel opened empty")
                        pg.keyboard.press("Escape")
                        if pg.locator("#ogBellPanel").is_visible(): bad.append(f"{tag}: notifications panel did not close with Escape")
                        q = "#hmQ" if pg.locator("#hmQ").count() else "#ogQ"
                        pg.fill(q, "met office"); pg.wait_for_timeout(900)
                        if not pg.locator(f"{q}r a", has_text="Met Office").count(): bad.append(f"{tag}: search found no Met Office")
                        if pg.evaluate("document.documentElement.scrollWidth - innerWidth") > 1: bad.append(f"{tag}: search suggestions overflow the page")
                    pg.close()
        b.close()
    return bad


def main():
    if "--negative" in sys.argv:
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "bad.html").write_text('<!DOCTYPE html><html><body><div style="width:3000px">wide</div><script>null.x</script></body></html>')
            srv = serve(d); found = check(f"http://127.0.0.1:{srv.server_address[1]}", ["bad.html"]); srv.shutdown()
        if not any("script error" in x for x in found) or not any("overflows" in x for x in found): sys.exit("browser negative: not caught: " + "; ".join(found))
        print("browser negative: a script error and sideways overflow are both caught"); return
    srv = serve(ROOT / "docs")
    bad = check(f"http://127.0.0.1:{srv.server_address[1]}", PAGES); srv.shutdown()
    if bad: sys.exit("browser: " + "; ".join(bad[:12]) + (f" (+{len(bad) - 12} more)" if len(bad) > 12 else ""))
    print(f"browser: {len(PAGES)} pages x 2 widths x 2 themes: no script errors, no overflow, masthead clear, bell and search work")


if __name__ == "__main__":
    main()
