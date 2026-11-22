"""OpenGovernment UK design system: tokens -> one shared stylesheet, a tokenising pass, the shared page shell, and guards.

  python tools/design.py            build docs/assets/og.css and docs/assets/tokens.json; check contrast (fails closed)
  python tools/design.py --audit    check every published page against the system (run after the pages are built)
  python tools/design.py --negative prove each guard fails when it should

Rules the guards enforce (OG-D42):
  - no third-party fonts or stylesheets (fonts are self-hosted, OFL 1.1);
  - outside the token file, page CSS has no raw hex colours, no raw font sizes and no raw corner radii;
  - media queries use only the two breakpoints;
  - every text and UI colour pair meets WCAG 2.2 AA contrast in light and dark."""
import gzip
import hashlib, json, os, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DES = ROOT / "tools/design"; ASSETS = ROOT / "docs/assets"
TOK = json.loads((DES / "tokens.json").read_text())
FONTS = [("Atkinson Hyperlegible Next", "atkinson-hyperlegible-next-latin-wght-normal.woff2", "normal", "200 800", "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
         ("Atkinson Hyperlegible Next", "atkinson-hyperlegible-next-latin-ext-wght-normal.woff2", "normal", "200 800", "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"),
         ("Atkinson Hyperlegible Next", "atkinson-hyperlegible-next-latin-wght-italic.woff2", "italic", "200 800", "U+0000-00FF,U+0131,U+0152-0153,U+2000-206F,U+20AC,U+2122,U+2212"),
         ("IBM Plex Mono", "ibm-plex-mono-latin-400-normal.woff2", "normal", "400", "U+0000-00FF,U+2000-206F,U+2212"),
         ("IBM Plex Mono", "ibm-plex-mono-latin-500-normal.woff2", "normal", "500", "U+0000-00FF,U+2000-206F,U+2212")]
# old variable names used by existing page CSS -> tokens (so everything adopts the system at once)
ALIAS = {"bg": "bg", "paper": "surface", "paper-2": "surface-2", "paper2": "surface-2", "ink": "ink", "muted": "muted", "line": "line", "line-2": "line-strong",
         "red": "brand", "red-soft": "brand-soft", "hi": "accent", "sea": "accent", "sea-soft": "accent-soft", "navy": "navy", "navy-soft": "navy-soft",
         "gold": "gold", "gold-soft": "gold-soft", "good": "good", "good-soft": "good-soft", "bad": "bad", "bad-soft": "bad-soft", "focus": "focus", "on-accent": "on-accent",
         "nEN": "n-EN", "nSC": "n-SC", "nWA": "n-WA", "nNI": "n-NI", "nUK": "n-UK", "nGB": "n-GB", "leg": "muted", "exe": "line-strong", "jud": "ink"}
CONTRAST = [  # (foreground, background, minimum): text 4.5, large text and UI 3
    *[(f, b, 4.5) for f in ("ink", "muted", "accent", "brand", "navy", "gold", "good", "bad") for b in ("bg", "surface")],
    *[(f, b, 4.5) for f, b in (("accent", "accent-soft"), ("brand", "brand-soft"), ("navy", "navy-soft"), ("gold", "gold-soft"), ("good", "good-soft"), ("bad", "bad-soft"),
                              ("on-accent", "accent"), ("ink", "surface-2"), ("muted", "surface-2"), ("bg", "ink"))],
    *[(f, b, 3.0) for f in ("line-strong", "focus") for b in ("bg", "surface", "surface-2")],
]


def lum(h):
    h = h.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + 0.05) / (lb + 0.05)


def contrast_problems(tok=TOK):
    bad = []
    for mode in ("light", "dark"):
        c = {k: v["$value"] for k, v in tok["color"][mode].items()}
        for f, b, need in CONTRAST:
            r = ratio(c[f], c[b])
            if r < need: bad.append(f"{mode}: {f} on {b} is {r:.2f}:1, needs {need}:1")
    return bad


def val(v):
    if isinstance(v, list) and all(isinstance(x, (int, float)) for x in v): return "cubic-bezier(" + ",".join(str(x) for x in v) + ")"
    if isinstance(v, list): return ",".join(f'"{x}"' if " " in x else x for x in v)
    return str(v)


def vars_for(mode):
    c = TOK["color"][mode]
    out = [f"--og-{k}:{v['$value']}" for k, v in c.items()]
    out += [f"--{old}:var(--og-{new})" for old, new in ALIAS.items()]
    return ";".join(out) + f";color-scheme:{mode}"


def static_vars():
    out = []
    for k, v in TOK["font"].items():
        if not k.startswith("$"): out.append(f"--og-font-{k}:{val(v['$value'])}")
    for group in ("size", "space", "radius", "shadow", "breakpoint", "layout"):
        for k, v in TOK[group].items():
            if not k.startswith("$"): out.append(f"--og-{group}-{k}:{val(v['$value'])}")
    for k, v in TOK["motion"].items(): out.append(f"--og-motion-{k}:{val(v['$value'])}")
    out.append(f"--og-target-min:{TOK['target']['min']['$value']}")
    out += ["--f-display:var(--og-font-display)", "--f-body:var(--og-font-body)", "--f-mono:var(--og-font-mono)", "--r:var(--og-radius-md)", "--drawer:var(--og-layout-drawer)"]
    return ";".join(out)


def build_css():
    ff = "".join(f'@font-face{{font-family:"{n}";font-style:{st};font-weight:{w};font-display:swap;src:url(fonts/{f}) format("woff2");unicode-range:{u}}}' for n, f, st, w, u in FONTS)
    head = (f"/* OpenGovernment UK design system. Generated by tools/design.py from tools/design/tokens.json; do not edit by hand. Fonts: Atkinson Hyperlegible Next and IBM Plex Mono, SIL Open Font License 1.1, self-hosted. */\n{ff}\n"
            f":root{{{static_vars()};{vars_for('light')}}}\n"
            f"@media (prefers-color-scheme:dark){{:root:not([data-theme=\"light\"]){{{vars_for('dark')}}}}}\n"
            f":root[data-theme=\"dark\"]{{{vars_for('dark')}}}\n:root[data-theme=\"light\"]{{{vars_for('light')}}}\n")
    return head + (DES / "components.css").read_text()


SIZE_STEPS = [(0.8, "xs"), (0.9, "sm"), (1.04, "base"), (1.2, "md"), (1.5, "lg"), (2.2, "xl"), (99, "2xl")]


def _size(m):
    v, unit = float(m.group(2)), m.group(3)
    rem = v / 16 if unit == "px" else v
    if unit == "em": return m.group(0)  # relative to the parent: keep
    return m.group(1) + "var(--og-size-" + next(k for lim, k in SIZE_STEPS if rem <= lim) + ")"


def _radius(m):
    vals = m.group(2).split()
    out = []
    for x in vals:
        mm = re.fullmatch(r"([\d.]+)px", x)
        if not mm: out.append(x); continue
        n = float(mm.group(1)); out.append("0" if n == 0 else "var(--og-radius-sm)" if n <= 8 else "var(--og-radius-md)" if n <= 18 else "var(--og-radius-pill)")
    return m.group(1) + " ".join(out)


def _bp(m):
    n = int(m.group(2)); return f"{m.group(1)}{640 if n <= 760 else 1023}px"


def layer(css):
    """Put a page's own CSS in the 'legacy' cascade layer so the shared system (unlayered) always wins, whatever the order."""
    return "@layer legacy{" + css + "}"


def tokenise(css):
    """Map every raw font size, corner radius and breakpoint to the nearest token; drop old token blocks."""
    css = re.sub(r"@media \(prefers-color-scheme: ?dark\)\{:root[^{]*\{[^{}]*\}\}", "", css)
    css = re.sub(r":root(?:\[data-theme=\"(?:dark|light)\"\]|:not\(\[data-theme=\"light\"\]\))?\{[^{}]*--[\w-]+:[^{}]*\}", "", css)
    css = re.sub(r"(font-size:\s*)([\d.]+)(rem|px|em)\b", _size, css)
    css = re.sub(r"(font:\s*(?:[\w-]+\s+)*?)([\d.]+)(rem|px|em)\b", _size, css)  # the font shorthand carries a size too
    css = re.sub(r"(border-radius:\s*)([^;}]+)", _radius, css)
    css = re.sub(r"(@media[^{]*?(?:max|min)-width:\s*)(\d+)px", _bp, css)
    return css


SHELL_NAV = [("index.html#home", "Home", "home"), ("index.html#register", "Register", "register"), ("index.html#tree", "Who answers", "tree"), ("nations.html", "Nations", "nations"), ("world.html", "UK and the world", "world"), ("orgchart.html", "Org charts", "orgchart"), ("funding.html", "Funding", "funding"),
             ("index.html#changes", "Changes", "changes"), ("navigator.html", "Documentation", "docs")]  # the design system page is linked from every footer
LOGO = '<svg viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="18" fill="var(--og-brand)"/><circle cx="20" cy="20" r="11.5" fill="none" stroke="var(--og-surface)" stroke-width="2"/><circle cx="20" cy="20" r="5" fill="var(--og-surface)"/><path d="M20 2v7M20 31v7M2 20h7M31 20h7" stroke="var(--og-surface)" stroke-width="2"/></svg>'
# The global navigation must never wrap or exceed the screen: when its links would not fit on one line, it folds into
# the Menu button (the 1023px media rule is the fallback without JavaScript).
NAVFIT_JS = ('<script>(()=>{const m=document.querySelector(".og-shell-mast"),n=m&&m.querySelector(".og-shell-nav");if(!n)return;'
             'const L=[...n.querySelectorAll(":scope>a")],mo=document.createElement("details");mo.className="og-shell-more";mo.innerHTML="<summary>More</summary><nav aria-label=\\"More sections\\"></nav>";n.appendChild(mo);const mn=mo.querySelector("nav");'
             'const W=()=>document.documentElement.clientWidth,over=()=>{const v=L.filter(a=>!a.hidden);const last=mo.hidden?v[v.length-1]:mo;return last.getBoundingClientRect().top>L[0].getBoundingClientRect().top+2||n.scrollWidth>n.clientWidth+1||document.documentElement.scrollWidth>W()+1||[...m.querySelectorAll(".in > *")].some(e=>e.getBoundingClientRect().right>W()+1)};'
             'const fit=()=>{m.classList.remove("og-fold");L.forEach(a=>a.hidden=false);mo.hidden=true;mn.innerHTML="";mo.open=false;if(getComputedStyle(n).display==="none")return;if(!over())return;mo.hidden=false;'
             'for(let i=L.length-1;i>0&&over();i--){if(L[i].getAttribute("aria-current"))continue;L[i].hidden=true}'
             'L.filter(a=>a.hidden).forEach(a=>{const c=a.cloneNode(true);c.hidden=false;mn.appendChild(c)});if(over()||L.filter(a=>!a.hidden).length<3)m.classList.add("og-fold")};'
             'fit();addEventListener("resize",fit);document.fonts&&document.fonts.ready.then(fit)})()</script>')
THEME_JS = ('<script>(()=>{const k="og-theme",r=document.documentElement,b=document.getElementById("ogTheme"),L={"":"Device","light":"Light","dark":"Dark"},N={"":"light","light":"dark","dark":""};'
            'let t="";try{t=localStorage.getItem(k)||""}catch(e){}const set=x=>{t=x;x?r.setAttribute("data-theme",x):r.removeAttribute("data-theme");b.querySelector(".v").textContent=L[x];try{localStorage.setItem(k,x)}catch(e){}};'
            'set(t);b.addEventListener("click",()=>set(N[t]));})();</script>')


def shell(active):
    """Masthead, global navigation, theme switch and footer shared by every subpage (the main portal keeps its own richer shell)."""
    cur = ' aria-current="page"'
    nav = "".join(f'<a href="{h}"{cur if k == active else ""}>{t}</a>' for h, t, k in SHELL_NAV)
    head = (f'<a class="og-skip" href="#og-main">Skip to main content</a><header class="og-shell-mast"><div class="in"><a class="brand" href="index.html#home" aria-label="OpenGovernment UK, home">{LOGO}'
            f'<span><b>OpenGovernment UK</b><small>The anatomy of the state, from the registers that keep it</small></span></a>'
            f'<nav class="og-shell-nav" aria-label="Sections of the portal">{nav}</nav>'
            f'<details class="og-shell-menu"><summary>Menu</summary><nav aria-label="Sections of the portal (menu)">{nav}</nav></details>'
            f'<button class="iconbtn" id="ogTheme" type="button" aria-label="Switch colour theme"><span class="og-phone-hide">Theme:&nbsp;</span><span class="v">Device</span></button></div></header>')
    foot = ('<footer class="og-shell-foot"><div class="in">'
            '<div><h2>Disclaimer</h2><p>A pilot built from open registers. It isn\'t an official government list, isn\'t affiliated with any public body, and no body named here has endorsed it.</p></div>'
            '<div><h2>Transparency</h2><p>An open-source public good, built in the open. AI (Claude) helps with harvesting, matching and building; every change is checked and reviewed in public.</p></div>'
            '<div><h2>Contact</h2><p><a href="https://github.com/cyberdudeuk/opengovernment-uk/issues/new?template=feedback.yml" rel="noopener" target="_blank">Tell us what\'s wrong or missing</a> through the feedback form.</p></div>'
            '<div><h2>Colophon</h2><p>Source and issues on <a href="https://github.com/cyberdudeuk/opengovernment-uk" rel="noopener" target="_blank">GitHub</a>. Code MIT, documentation CC BY 4.0, data OGL v3. '
            'Fonts: Atkinson Hyperlegible Next and IBM Plex Mono (SIL Open Font License), served from this site. <a href="design-system.html">Design system</a>.</p></div>'
            f'</div></footer>{THEME_JS}{NAVFIT_JS}')
    return head, foot


def wrap_page(html, active):
    """Put the shared shell and stylesheet on a generated subpage."""
    head, foot = shell(active)
    html = re.sub(r'<link[^>]+fonts\.(googleapis|gstatic)\.com[^>]*>', "", html)
    html = html.replace("</head>", '<link rel="stylesheet" href="assets/og.css"></head>', 1)
    html = re.sub(r"<style>(.*?)</style>", lambda m: "<style>" + layer(tokenise(m.group(1))) + "</style>", html, count=1, flags=re.S)
    html = re.sub(r"<body([^>]*)>", lambda m: f"<body{m.group(1)}>{head}<div id=\"og-main\" tabindex=\"-1\">", html, count=1)
    html = re.sub(r"<footer[^>]*>.*?</footer>", "", html, count=1, flags=re.S)
    return html.replace("</body>", f"</div>{foot}</body>", 1)


# Narrow-screen guards for elements that refuse to wrap (each from a defect in documentation/defect-register.md)
WRAP_GUARDS = [("nmulti", "@media (max-width:640px){.nmulti{white-space:normal}}", "OG-D50"), ('class="ins"', "dl.kv dd,ul.ins li{overflow-wrap:anywhere", "OG-D50")]


def css_guards(css):
    """Rules the shared stylesheet must keep (each from a defect)."""
    return [f"og.css lacks {r} ({d})" for r, d in [(".og-shell-nav a[hidden]{display:none}", "OG-D53"), (".sr-only{", "OG-D53")] if r not in css]


def audit_html(name, html):
    """Problems with one published page."""
    p = []
    if "og-shell-nav" in html and ("og-fold" not in html or "og-shell-more" not in html): p.append(f"{name}: the global navigation has no More menu and fold for when it would not fit (OG-D51)")
    for sel, rule, d in WRAP_GUARDS:
        if sel in html and rule not in html: p.append(f"{name}: {sel} has no narrow-screen wrap rule ({d})")
    if re.search(r"fonts\.(googleapis|gstatic)\.com|<link[^>]+rel=\"stylesheet\"[^>]+href=\"https?://", html): p.append(f"{name}: third-party font or stylesheet")
    if 'href="assets/og.css"' not in html: p.append(f"{name}: doesn't use the shared stylesheet")
    css = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
    hx = re.search(r".{0,40}#[0-9a-fA-F]{3,8}\b", css)
    if hx: p.append(f"{name}: raw hex colour in page CSS: {hx.group(0)}")
    fs = re.search(r".{0,40}font(?:-size)?:\s*(?:[\w-]+\s+)*?[\d.]+(rem|px)\b", css)
    if fs: p.append(f"{name}: raw font size in page CSS: {fs.group(0)}")
    if re.search(r"border-radius:[^;}]*\b[1-9][\d.]*px", css): p.append(f"{name}: raw corner radius in page CSS")
    bps = set(re.findall(r"@media[^{]*?width:\s*(\d+)px", css))
    if bps - {"640", "1023"}: p.append(f"{name}: breakpoints outside the system: {sorted(bps - {'640', '1023'})}")
    return p


def esc(x): return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def design_page():
    """The living design system page, generated from the tokens so it can't drift from them."""
    L, D = TOK["color"]["light"], TOK["color"]["dark"]
    roles = [k for k in L if not k.startswith(("n-", "$"))]
    def sw(k):
        lv, dv = L[k]["$value"], D[k]["$value"]
        pair = next(((b, need) for f, b, need in CONTRAST if f == k), None)
        if pair:
            b, need = pair
            rtxt = f"On {b}: {ratio(lv, L[b]['$value']):.1f}:1 light, {ratio(dv, D[b]['$value']):.1f}:1 dark (needs {need:g}:1)"
        else:
            rtxt = "A background: the text on it is what gets checked"
        return (f'<li class="ds-sw"><span class="ds-chip" style="--l:var(--og-{k})" aria-hidden="true"></span><b>{esc(k)}</b>'
                f'<span class="mono">{lv} · {dv}</span><span class="muted">{esc(L[k].get("$description", ""))}</span>'
                f'<span class="ds-ratio">{rtxt}</span></li>')
    nat = "".join(f'<li class="ds-sw"><span class="ds-chip" style="--l:var(--og-{k})" aria-hidden="true"></span><b>{k[2:]}</b><span class="mono">{L[k]["$value"]} · {D[k]["$value"]}</span></li>' for k in L if k.startswith("n-"))
    sizes = "".join(f'<li><span class="ds-tag mono">size-{k}</span><span style="font-size:var(--og-size-{k});font-weight:{800 if k in ("xl", "2xl") else 400}">Who answers for this body?</span><span class="mono muted">{esc(v["$value"])}</span></li>' for k, v in TOK["size"].items() if not k.startswith("$"))
    space = "".join(f'<li><span class="ds-tag mono">space-{k}</span><span class="ds-bar" style="width:var(--og-space-{k})"></span><span class="mono muted">{v["$value"]}</span></li>' for k, v in TOK["space"].items() if not k.startswith("$"))
    radii = "".join(f'<li><span class="ds-box" style="border-radius:var(--og-radius-{k})"></span><span class="mono">radius-{k} · {v["$value"]}</span><span class="muted">{esc(v.get("$description", ""))}</span></li>' for k, v in TOK["radius"].items() if not k.startswith("$"))
    comp = ('<div class="ds-row"><a class="btn" href="#components">Primary action</a><a class="btn ghost" href="#components">Secondary action</a><button class="btn small" type="button">Small</button></div>'
            '<div class="ds-row"><span class="pill">Neutral</span><span class="pill sea">Link or selected</span><span class="pill good">Pass</span><span class="pill gold">Modelled</span><span class="pill bad">Fail</span><span class="pill navy">Information</span><span class="pill red">Brand</span></div>'
            '<div class="ds-row"><div class="stat sea"><b>2,824</b><span>open bodies</span></div><div class="stat gold"><b>513</b><span>without a nation yet</span></div><div class="stat navy"><b>21</b><span>areas being reorganised</span></div></div>'
            '<div class="tabs" role="tablist" aria-label="Example tabs"><button class="tab" role="tab" aria-selected="true" type="button">Selected tab</button><button class="tab" role="tab" aria-selected="false" type="button">Another tab</button></div>'
            '<div class="ds-row" style="margin-top:var(--og-space-4)"><label class="ds-field">Search<input type="search" placeholder="Met Office, Ofsted…"></label><label class="ds-field">Group by<select><option>What it is for</option></select></label></div>'
            '<div class="note sea" style="margin-top:var(--og-space-4);padding:var(--og-space-3) var(--og-space-4)">A note: something the reader should know before going on.</div>'
            '<div class="tablewrap" style="margin-top:var(--og-space-4)"><table><thead><tr><th scope="col">Body</th><th scope="col">Answers to</th><th scope="col" class="num">Links</th></tr></thead><tbody><tr><td>Met Office</td><td>Ministry of Defence</td><td class="num">3</td></tr><tr><td>Scottish Water</td><td>The Scottish Government</td><td class="num">2</td></tr><tr><td>Ordnance Survey</td><td>Department for Science, Innovation and Technology</td><td class="num">2</td></tr></tbody></table></div>')
    rules = "".join(f"<li>{esc(x)}</li>" for x in [
        "Every value comes from a token. Page stylesheets may not contain raw colours, font sizes or corner radii: the build checks every page and stops if one appears.",
        "Teal means you can click or have chosen it. Red is for the logo and small brand marks. Colour never carries meaning alone: every nation colour is shown with its label, every status with its word.",
        "Text meets WCAG 2.2 AA contrast (4.5:1), and borders and focus rings meet 3:1, in both light and dark. The build checks 32 pairs in each mode.",
        "Anything you can tap is at least 44 pixels high.",
        "Two breakpoints only: phones up to 640 pixels and tablets up to 1023 pixels. On narrow screens, menus fold into a Menu button rather than scrolling off the edge.",
        "Fonts are served from this site. No request goes to a third party, so no visitor's address is shared.",
        "Motion is short (120 to 220 milliseconds) and switches off for anyone who asks for less motion.",
        "Old page CSS sits in a 'legacy' cascade layer, so the design system always wins without !important."])
    body = f"""<main class="ds"><header class="ds-hero"><span class="eyebrow">Design system</span><h1>How OpenGovernment UK looks, and why</h1>
<p class="lede">One set of design tokens drives every page: colour, type, space, corners, shadow, motion and breakpoints. They are written in the open <a href="https://tr.designtokens.org/format/" rel="noopener" target="_blank">W3C Design Tokens format</a>, so any other app can reuse them: <a href="assets/tokens.json">download tokens.json</a> or link <a href="assets/og.css">og.css</a>.</p></header>
<nav class="ds-toc" aria-label="On this page"><a href="#principles">Principles</a><a href="#colour">Colour</a><a href="#type">Type</a><a href="#space">Space and corners</a><a href="#components">Components</a><a href="#use">Use it</a></nav>
<section id="principles" class="card ds-sec"><h2>Principles</h2><ul class="ds-rules">{rules}</ul></section>
<section id="colour" class="card ds-sec"><h2>Colour</h2><p class="muted">Each role has a light and a dark value. The ratio is its contrast against a card in each mode.</p><ul class="ds-grid">{"".join(sw(k) for k in roles)}</ul>
<h3>Nations</h3><p class="muted">Checked for colour-blind readers (separation of at least 8 for every neighbouring pair) and for 3:1 contrast, in light and dark. UK-wide and Great Britain are deliberately grey: they belong to no single nation. Every nation colour is always shown with its EN, SC, WA or NI label.</p><ul class="ds-grid">{nat}</ul></section>
<section id="type" class="card ds-sec"><h2>Type</h2><p class="muted">Atkinson Hyperlegible Next, made by the Braille Institute so letters that look alike (I, l and 1; O and 0) are easy to tell apart. IBM Plex Mono for codes such as <span class="mono">government-organisation:D303</span>. Both under the SIL Open Font License, served from this site. Seven sizes; the two largest grow with the screen.</p><ul class="ds-type">{sizes}</ul></section>
<section id="space" class="card ds-sec"><h2>Space and corners</h2><p class="muted">Spacing steps on a 4 and 8 pixel grid. Three corner sizes.</p><ul class="ds-space">{space}</ul><ul class="ds-radii">{radii}</ul></section>
<section id="components" class="card ds-sec"><h2>Components</h2><p class="muted">The same pieces on every page. Use the theme switch at the top to see them in dark mode.</p>{comp}</section>
<section id="use" class="card ds-sec"><h2>Use it</h2><ol class="ds-rules"><li>Change a value in <span class="mono">tools/design/tokens.json</span>, never in page CSS.</li><li>Run <span class="mono">python tools/design.py</span>. It rebuilds the stylesheet and this page, and stops if any contrast pair fails.</li><li>Rebuild the pages; <span class="mono">python tools/design.py --audit</span> then checks every page against the rules above. CI runs both on every change.</li></ol></section></main>"""
    css = """.ds{max-width:1100px;margin:0 auto;padding:var(--og-space-5) var(--og-space-4) var(--og-space-7);display:grid;gap:var(--og-space-5)}
.ds-hero h1{margin:var(--og-space-2) 0}.ds-sec{padding:var(--og-space-5)}.ds-sec h2{margin-top:0}
.ds-toc{display:flex;flex-wrap:wrap;gap:var(--og-space-2)}.ds-toc a{min-height:var(--og-target-min);display:inline-flex;align-items:center;padding:0 var(--og-space-3);border:1px solid var(--og-line);border-radius:var(--og-radius-pill);text-decoration:none;font-weight:600;background:var(--og-surface)}
.ds-grid{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:var(--og-space-3)}
.ds-sw{display:grid;grid-template-columns:44px 1fr;gap:0 var(--og-space-3);align-items:start;padding:var(--og-space-3);border:1px solid var(--og-line);border-radius:var(--og-radius-md)}
.ds-sw>*:not(.ds-chip){grid-column:2}.ds-chip{grid-row:span 4;width:44px;height:44px;border-radius:var(--og-radius-sm);background:var(--l);box-shadow:inset 0 0 0 1px var(--og-line)}
.ds-sw .mono,.ds-ratio,.ds-sw .muted{font-size:var(--og-size-xs)}
.ds-type,.ds-space,.ds-radii,.ds-rules{padding:0;list-style:none;display:grid;gap:var(--og-space-3)}.ds-rules{list-style:disc;padding-left:var(--og-space-5)}ol.ds-rules{list-style:decimal}
.ds-type li,.ds-space li,.ds-radii li{display:flex;gap:var(--og-space-4);align-items:center;flex-wrap:wrap}
.ds-tag{min-width:90px;font-size:var(--og-size-xs);color:var(--og-muted)}
.ds-bar{display:inline-block;height:16px;background:var(--og-accent);border-radius:var(--og-radius-sm)}
.ds-box{width:56px;height:40px;background:var(--og-accent-soft);border:2px solid var(--og-accent)}
.ds-radii{margin-top:var(--og-space-4)}.ds-row{display:flex;flex-wrap:wrap;gap:var(--og-space-3);align-items:center;margin-bottom:var(--og-space-4)}
.ds-row .stat{min-width:180px}.ds-field{display:grid;gap:var(--og-space-1);font-weight:600;font-size:var(--og-size-sm);color:var(--og-muted)}"""
    html = f'<!DOCTYPE html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Design system · OpenGovernment UK</title><meta name="description" content="The design tokens, type, colour and components behind OpenGovernment UK."><style>{css}</style></head><body></body></html>'
    return wrap_page(html, "design").replace('<div id="og-main" tabindex="-1">', f'<div id="og-main" tabindex="-1">{body}', 1)


PAGES = ["index.html", "nations.html", "world.html", "orgchart.html", "funding.html", "navigator.html", "design-system.html"]  # every published page; a new page must be added here

# Page-weight budget, in gzip bytes (what GitHub Pages sends). Measured 22 Nov 2026: index 974,578 (ready in 1.8 s on a
# 4x-throttled CPU, about 0.8 s more to download on 4G), nations 263,437, orgchart 160,032, funding 57,625.
# The budget leaves about 15% headroom; going over it means lazy-loading per-body data (ACC.ins is the largest part).
BUDGET = {"index.html": 1_100_000, "nations.html": 320_000, "world.html": 220_000, "orgchart.html": 200_000, "funding.html": 80_000}
BUDGET_DEFAULT = 150_000


def weight(name, html):
    n = len(gzip.compress(html.encode(), 9))
    cap = BUDGET.get(name, BUDGET_DEFAULT)
    return [f"{name}: {n:,} bytes gzip is over its {cap:,} budget (lazy-load per-body data)"] if n > cap else []


def audit():
    p = []
    for n in PAGES:
        f = ROOT / "docs" / n
        if not f.exists(): p.append(f"{n}: missing"); continue
        p += audit_html(n, f.read_text()) + weight(n, f.read_text())
    og = (ASSETS / "og.css").read_text()
    p += css_guards(og)
    pub = sorted(f.name for f in (ROOT / "docs").glob("*.html"))
    p += [f"{n}: published but not audited (add it to PAGES)" for n in pub if n not in PAGES]
    if og != build_css(): p.append("og.css is stale: rebuild from the tokens")
    ds = re.sub(r'<script type="application/ld\+json" id="og-dataset">.*?</script><link rel="alternate"[^>]*>', "", (ROOT / "docs/design-system.html").read_text(), flags=re.S)  # tools/standards.py adds that block to every page
    if ds != design_page(): p.append("design-system.html is stale: rebuild from the tokens")
    for _, f, *_ in FONTS:
        if not (ASSETS / "fonts" / f).exists(): p.append(f"font file missing: {f}")
    return p + contrast_problems()


def main():
    if "--negative" in sys.argv:
        import copy
        caught = []
        t = copy.deepcopy(TOK); t["color"]["light"]["muted"]["$value"] = "#9aa3ad"; caught.append(bool(contrast_problems(t)))
        ok = '<head><link rel="stylesheet" href="assets/og.css"></head><style>a{color:var(--og-accent)}</style>'
        caught.append(not audit_html("ok", ok))  # the clean page passes
        for bad in ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter">', "<style>a{color:#ff0000}</style>", "<style>p{font-size:13px}</style>", "<style>p{font:700 .9rem var(--f-body)}</style>",
                    "<style>.c{border-radius:14px}</style>", "<style>@media (max-width:900px){a{color:red}}</style>"):
            caught.append(bool(audit_html("bad", ok + bad)))
        caught.append(bool(css_guards(".og-shell-nav a{display:inline-flex}")))  # OG-D53: hidden links shown because author CSS overrides [hidden]
        caught.append(bool(audit_html("bad", ok + '<nav class="og-shell-nav"><a href="#">A</a></nav>')))  # OG-D51: a shell navigation without its fold
        caught.append(bool(audit_html("bad", ok + '<span class="nmulti">serves the whole UK</span>')))  # OG-D50: a no-wrap chip without its narrow-screen rule
        caught.append(bool(weight("design-system.html", os.urandom(200_000).hex())))  # page weight: an oversized page fails the audit
        caught.append(tokenise("p{font-size:.72rem;border-radius:10px}@media (max-width:900px){}") == "p{font-size:var(--og-size-xs);border-radius:var(--og-radius-md)}@media (max-width:1023px){}")
        if not all(caught): sys.exit(f"design negative: {caught.count(False)} not caught")
        print(f"design negative: all {len(caught)} cases behave as they should"); return
    if "--audit" in sys.argv:
        p = audit()
        if p: sys.exit("design audit: " + "; ".join(p))
        print("design audit: every page uses the shared system; contrast passes"); return
    p = contrast_problems()
    if p: sys.exit("design: contrast fails: " + "; ".join(p))
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "og.css").write_text(build_css())
    (ASSETS / "tokens.json").write_text(json.dumps(TOK, indent=1, ensure_ascii=False))
    (ROOT / "docs/design-system.html").write_text(design_page())
    fonts = {f: hashlib.sha256((ASSETS / "fonts" / f).read_bytes()).hexdigest() for _, f, *_ in FONTS}
    (ASSETS / "fonts" / "fonts.json").write_text(json.dumps({"licence": "SIL Open Font License 1.1 (see OFL-*.txt)", "source": "Fontsource npm packages @fontsource-variable/atkinson-hyperlegible-next@5.3.0 and @fontsource/ibm-plex-mono@5.3.0", "sha256": fonts}, indent=1))
    print(f"design: og.css {len((ASSETS / 'og.css').read_text()) // 1024}KB; {len(CONTRAST) * 2} contrast pairs pass in light and dark")


if __name__ == "__main__":
    main()
