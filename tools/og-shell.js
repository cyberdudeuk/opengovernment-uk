/* OpenGovernment UK masthead tools, shared by every page: notifications (bell), latest changes (clock) and search.
   Source: tools/og-shell.js, copied to docs/assets/og-shell.js by tools/design.py. Reads data/alerts.json and, for
   search on pages without the register, data/search-index.json. Built with DOM nodes and textContent only (no HTML
   strings from data); links are followed only if they are https or one of the portal's own pages. */
(() => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const IDX = location.pathname.endsWith("/") || /\/index\.html$/.test(location.pathname);
  const local = u => IDX && u.startsWith("index.html#") ? u.slice(10) : u;  // on the portal page, stay on the page
  const okUrl = u => typeof u === "string" && (u.startsWith("https://") || /^(index|nations|world|orgchart|funding|navigator|developers)\.html(#[\w=&%.?-]*)?$/.test(u));
  const store = {get: k => { try { return localStorage.getItem(k) || ""; } catch (e) { return ""; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* storage off: badges just stay */ } }};
  const el = (tag, props = {}, kids = []) => { const n = document.createElement(tag); Object.entries(props).forEach(([k, v]) => k === "text" ? n.textContent = v : n.setAttribute(k, v)); kids.forEach(c => c && n.appendChild(c)); return n; };
  const day = d => new Date(d + "T00:00:00Z").toLocaleDateString("en-GB", {day: "numeric", month: "short", year: "numeric", timeZone: "UTC"});

  // ---- pop-out panels ----
  const PANELS = [["ogBell", "ogBellPanel", "notifications", "og-seen-notifications"], ["ogChanges", "ogChangesPanel", "changes", "og-seen-changes"]];
  let feed = null, openId = null;
  const load = () => feed || (feed = fetch("data/alerts.json", {credentials: "same-origin"}).then(r => r.ok ? r.json() : Promise.reject(r.status)));
  const item = x => {
    const ext = x.url.startsWith("https://");
    const a = el("a", Object.assign({href: local(x.url)}, ext ? {rel: "noopener", target: "_blank"} : {}), [el("span", {class: "og-pop-k", text: x.kind}), el("time", {datetime: x.date, text: day(x.date)}), el("span", {class: "og-pop-t", text: x.title})]);
    if (ext) a.appendChild(el("span", {class: "sr-only", text: " (opens in a new tab)"}));
    return el("li", {}, [a]);
  };
  function close(restore) {
    if (!openId) return;
    const [b, p] = PANELS.find(x => x[1] === openId); const btn = document.getElementById(b), pan = document.getElementById(p);
    pan.hidden = true; btn.setAttribute("aria-expanded", "false"); openId = null; if (restore) btn.focus();
  }
  function open(b, p, key, seenKey) {
    close(false);
    const btn = document.getElementById(b), pan = document.getElementById(p), list = $(".og-pop-list", pan);
    pan.hidden = false; btn.setAttribute("aria-expanded", "true"); openId = p;
    (($("h2", pan)) || pan).focus();
    load().then(f => {
      const xs = (f[key] || []).filter(x => okUrl(x.url));
      list.replaceChildren(...(xs.length ? xs.map(item) : [el("li", {class: "og-pop-empty", text: "Nothing new."})]));
      if (xs[0]) store.set(seenKey, xs.map(x => x.date).sort().pop());
      const badge = $(".og-badge", btn); if (badge) badge.hidden = true;
    }).catch(() => list.replaceChildren(el("li", {class: "og-pop-empty", text: "Couldn't load the latest items. Try again later."})));
  }
  PANELS.forEach(([b, p, key, seenKey]) => {
    const btn = document.getElementById(b), pan = document.getElementById(p); if (!btn || !pan) return;
    btn.addEventListener("click", e => { e.stopPropagation(); openId === p ? close(true) : open(b, p, key, seenKey); });
    $(".og-pop-x", pan)?.addEventListener("click", () => close(true));
    load().then(f => {  // unread count: items newer than the last time this panel was opened
      const seen = store.get(seenKey), n = (f[key] || []).filter(x => !seen || x.date > seen).length, badge = $(".og-badge", btn);
      if (badge && n) { badge.textContent = n > 9 ? "9+" : String(n); badge.hidden = false; btn.setAttribute("aria-label", `${btn.dataset.label}, ${n} new`); }
    }).catch(() => {});
  });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && openId) close(true); });
  document.addEventListener("click", e => { if (openId && !e.target.closest(".og-pop")) close(false); });

  // ---- search on pages that don't hold the register (the portal page has its own, with every record in memory) ----
  const box = document.getElementById("ogQ"), out = document.getElementById("ogQr");
  if (!box || !out) return;
  const PLACES = [["Register", "index.html#register"], ["Who answers", "index.html#tree"], ["Nation by nation", "nations.html"], ["The UK and the world", "world.html"], ["Treaties and the world map", "world.html#tab=t"], ["Org charts", "orgchart.html"], ["Funding, grants and schemes", "funding.html"], ["Changes to the state", "index.html#changes"], ["Developer hub", "developers.html"], ["Documentation", "navigator.html"], ["Ask a question", "index.html#ask"]];
  let bodies = null, sel = -1;
  const getBodies = () => bodies || (bodies = fetch("data/search-index.json", {credentials: "same-origin"}).then(r => r.ok ? r.json() : []).catch(() => []));
  const hash = id => "org-" + id.replace(/:/g, "--").replace(/[^A-Za-z0-9-]/g, "");
  const row = (title, sub, href) => el("li", {role: "option"}, [el("a", {href}, [el("span", {}, [el("b", {text: title}), el("small", {text: sub})])])]);
  async function draw() {
    const q = box.value.trim().toLowerCase(); sel = -1;
    if (!q) { out.hidden = true; box.setAttribute("aria-expanded", "false"); return; }
    const all = await getBodies();
    if (box.value.trim().toLowerCase() !== q) return;  // typed on while loading
    const hits = all.filter(r => r[1].toLowerCase().includes(q) || r[0].toLowerCase().includes(q)).sort((a, b) => (b[1].toLowerCase().startsWith(q) - a[1].toLowerCase().startsWith(q)) || b[3] - a[3] || a[1].localeCompare(b[1])).slice(0, 7);
    out.replaceChildren(...PLACES.filter(p => p[0].toLowerCase().includes(q)).slice(0, 3).map(p => row(p[0], "Page", p[1])),
      ...hits.map(r => row(r[1], r[2] + (r[3] ? "" : " · closed"), "index.html#" + hash(r[0]))),
      row(`See every match for “${box.value.trim()}”`, "In the register", "index.html#register?q=" + encodeURIComponent(box.value.trim())));
    out.hidden = false; box.setAttribute("aria-expanded", "true");
  }
  box.addEventListener("focus", getBodies, {once: true});
  box.addEventListener("input", draw);
  box.addEventListener("keydown", e => {
    const its = [...out.querySelectorAll("a")];
    if ((e.key === "ArrowDown" || e.key === "ArrowUp") && its.length) { e.preventDefault(); sel = (sel + (e.key === "ArrowDown" ? 1 : its.length - 1)) % its.length; its.forEach((a, i) => a.classList.toggle("on", i === sel)); box.setAttribute("aria-activedescendant", ""); }
    if (e.key === "Enter") { e.preventDefault(); const a = its[sel] || its[its.length - 1]; if (a) location.href = a.href; else if (box.value.trim()) location.href = "index.html#register?q=" + encodeURIComponent(box.value.trim()); }
    if (e.key === "Escape") { out.hidden = true; box.setAttribute("aria-expanded", "false"); }
  });
  document.addEventListener("click", e => { if (!e.target.closest(".og-search")) out.hidden = true; });
})();
