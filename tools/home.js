// ---- HOME: bullseye, search, quick actions, ticker, jump points, carousel, spotlight, wayfinder ----
// Every figure is computed here from the page's own data (D, ACC); nothing is typed in by hand.
// Motion is decorative and stops when the reader asks for reduced motion.
const HM_RM = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
const HM_NOPEN = id => (BY[id] && BY[id].open);
const HM_BT = ["department", "agency", "ndpb", "central", "corporation", "court", "council", "nhs", "territory"];
const HM_NATS = [["UK", "UK-wide"], ["EN", "England"], ["SC", "Scotland"], ["WA", "Wales"], ["NI", "Northern Ireland"], ["CD", "Crown Dependencies"], ["OT", "Overseas Territories"]];
const hmNatCount = c => OPEN.filter(r => (r.nat.length ? r.nat : ["UK"]).includes(c) && !SA_FOLDED.has(r.id)).length;
const hmBtCount = k => OPEN.filter(r => !SA_FOLDED.has(r.id) && CLX(r.id, 2) === k).length;
const hmGo = f => `data-go='${esc(JSON.stringify(Object.assign({stat: "1"}, f)))}'`;

function hmBullseye(){
  const host = $("#bullseye"); if (!host) return;
  const W = 820, H = 600, cx = 410, cy = 300, RAD = [92, 182, 262];
  const N = ACC.news || {};
  const SHORT = {department: "Departments", agency: "Agencies", ndpb: "Arm's-length bodies", central: "Other central bodies", corporation: "Corporations", court: "Courts and tribunals", council: "Councils", nhs: "NHS bodies", territory: "Territories"};
  const NS = {UK: "UK-wide", EN: "England", SC: "Scotland", WA: "Wales", NI: "N. Ireland", CD: "Crown Deps", OT: "Overseas Terr."};
  const rings = [
    HM_NATS.map(([c, l]) => ({label: l, short: NS[c], n: hmNatCount(c), go: {nat: c}, href: "#register", what: `Open bodies in ${c === "UK" ? "the UK as a whole, or with no nation stated" : l}`, more: [["Nation by nation", "nations.html"]]})),
    HM_BT.map(k => ({label: CLL("btype", k), short: SHORT[k], n: hmBtCount(k), go: {bt: k}, href: "#register", what: CLL("btype", k), more: [["Org charts by type", "orgchart.html#view=types"]]})),
    [["Who answers", "#tree", `Accountability traced for ${fmt(Object.keys(ACC.ch || {}).length)} bodies`],
     ["Treaties", "world.html#tab=t", `${fmt(N.treaties || 0)} treaties, mapped by partner`],
     ["Alliances", "world.html#tab=i", `${fmt(N.memberships || 0)} memberships of international bodies`],
     ["Funding", "funding.html", `${fmt(N.grants || 0)} open grants and ${fmt(N.schemes || 0)} schemes`],
     ["Org charts", "orgchart.html", "Every body in context, as a chart you can explore"],
     ["Changes", "#changes", `${fmt(D.ev.length)} closures, mergers and renames`]].map(([l, h, w]) => ({label: l, short: l, href: h, what: w, more: []}))];
  const NAMES = ["Nations and territories", "Types of body", "How it connects"];
  const OFF = [0, .5, .5];  // the outer ring sits between the middle ring's labels
  const pos = (ri, i, n) => { const a = -Math.PI / 2 + (i + OFF[ri]) * 2 * Math.PI / n; return [cx + RAD[ri] * Math.cos(a), cy + RAD[ri] * Math.sin(a), a]; };
  const COL = ["var(--sea)", "var(--navy)", "var(--gold)"];
  let k = 0;
  const nodes = rings.map((ring, ri) => ring.map((nd, i) => {
    const [x, y, a] = pos(ri, i, ring.length), c = Math.cos(a), s = Math.sin(a), right = ri > 0 && c > .3, left = ri > 0 && c < -.3;  // inner-ring labels sit above or below their node, inside the ring's own band
    const tx = x + (right ? 14 : left ? -14 : 0), ty = y + (right || left ? -2 : s > 0 ? 26 : -26), anchor = right ? "start" : left ? "end" : "middle";
    const attrs = nd.go ? hmGo(nd.go) : "";
    const t2 = nd.n !== undefined ? `<tspan x="${tx.toFixed(1)}" dy="15" class="cnt">${fmt(nd.n)}</tspan>` : "";
    return `<a class="bn r${ri}" href="${esc(nd.href)}" ${attrs} data-k="${k++}" style="--d:${(ri * 0.25 + i * 0.06).toFixed(2)}s" aria-label="${esc(nd.label)}${nd.n !== undefined ? ": " + fmt(nd.n) + " bodies" : ""}. ${esc(nd.what)}"><circle class="dot" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${ri === 2 ? 10 : 8}" fill="${COL[ri]}"/><circle class="halo" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="15"/><text x="${tx.toFixed(1)}" y="${(ty - (t2 && !(right || left) && s < 0 ? 15 : 0)).toFixed(1)}" text-anchor="${anchor}">${esc(nd.short)}${t2}</text></a>`;
  }).join("")).join("");
  const flat = rings.flat();
  host.innerHTML = `<div class="bnwrap"><svg viewBox="0 0 ${W} ${H}" role="group" aria-label="The UK state as rings: at the centre, who answers; around it, nations and territories, then types of body, then how they connect. Each node is a link.">
   <defs><radialGradient id="hmg" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="var(--red-soft)"/><stop offset="1" stop-color="var(--paper-2)" stop-opacity="0"/></radialGradient></defs>
   <circle cx="${cx}" cy="${cy}" r="290" fill="url(#hmg)"/>
   ${RAD.map((r, i) => `<circle class="ring" style="--d:${i * .2}s" cx="${cx}" cy="${cy}" r="${r}" fill="none"/><circle class="spin s${i}" cx="${cx}" cy="${cy}" r="${r}" fill="none"/>`).join("")}
   ${nodes}
   <a class="bn core" href="#tree" aria-label="Who answers: trace any body to whoever answers for it"><circle cx="${cx}" cy="${cy}" r="34" fill="var(--red)"/><circle class="pulse" cx="${cx}" cy="${cy}" r="34" fill="none"/><circle cx="${cx}" cy="${cy}" r="12" fill="var(--paper)"/><text x="${cx}" y="${cy - 46}" text-anchor="middle" class="corel">Who answers</text></a>
  </svg>
  <div class="bnside"><div class="bnpanel" id="bnPanel" aria-live="polite"><b>Point at a node, or tab to it</b><span>Each node opens the bodies or the page behind it.</span></div>
   <ul class="bnkey">${NAMES.map((n, i) => `<li><i class="key k${i}"></i>${esc(n)}</li>`).join("")}<li><i class="key kc"></i>Who answers, at the centre</li></ul>
   <div class="bnlist">${rings.map((ring, ri) => `<h3>${esc(NAMES[ri])}</h3><p>${ring.map(nd => `<a href="${esc(nd.href)}" ${nd.go ? hmGo(nd.go) : ""}>${esc(nd.short)}${nd.n !== undefined ? ` <span class="mono">${fmt(nd.n)}</span>` : ""}</a>`).join("")}</p>`).join("")}</div></div></div>`;
  const show = el => { const nd = el.classList.contains("core") ? {label: "Who answers", what: "Trace any body to whoever answers for it, with the money and the owners.", more: []} : flat[+el.dataset.k];
    $("#bnPanel").innerHTML = `<b>${esc(nd.label)}${nd.n !== undefined ? ` · ${fmt(nd.n)}` : ""}</b><span>${esc(nd.what)}</span><span class="bnlinks"><a href="${esc(el.getAttribute("href"))}" ${nd.go ? hmGo(nd.go) : ""}>Open${nd.go ? " in the register" : ""}</a>${nd.more.map(([t, h]) => ` · <a href="${esc(h)}">${esc(t)}</a>`).join("")}</span>`; };
  host.addEventListener("pointerover", e => { const a = e.target.closest(".bn"); if (a) show(a); });
  host.addEventListener("focusin", e => { const a = e.target.closest(".bn"); if (a) show(a); });
}

function hmSearch(){
  const box = $("#hmQ"), out = $("#hmQr"); if (!box) return;
  const PLACES = [["Who answers", "#tree"], ["Register", "#register"], ["Nation by nation", "nations.html"], ["The UK and the world", "world.html"], ["Treaties and the world map", "world.html#tab=t"], ["International bodies", "world.html#tab=i"], ["Org charts", "orgchart.html"], ["Funding, grants and schemes", "funding.html"], ["Changes to the state", "#changes"], ["Downloads and the data", "#data"], ["Ask a question", "#ask"], ["How matching works", "#reconcile"], ["Quality and evidence", "#quality"], ["Glossary and help", "#help"]];
  let sel = -1;
  const HM_QA = [["list", "Find a body", "#register"], ["crown", "Who answers", "#tree"], ["globe", "Treaty map", "world.html#tab=t"], ["tree", "Org charts", "orgchart.html"], ["coin", "Find funding", "funding.html"], ["down", "Download data", "#data"], ["data", "Developer hub", "developers.html"], ["ask", "Ask a question", "#ask"], ["flag", "Report a mistake", "#help"]];
  const quick = () => { sel = -1; out.innerHTML = `<li class="og-qhead" role="presentation">Quick actions</li>` + HM_QA.map(p => `<li role="option"><a href="${esc(p[2])}">${icon(p[0])}<span><b>${esc(p[1])}</b></span></a></li>`).join(""); out.hidden = false; box.setAttribute("aria-expanded", "true"); };
  box.addEventListener("focus", () => { if (!box.value.trim()) quick(); });
  const draw = () => { const q = box.value.trim(); sel = -1; if (!q) { quick(); return; }
    const pl = PLACES.filter(p => p[0].toLowerCase().includes(q.toLowerCase())).slice(0, 3);
    const rs = searchRecords(q, 7).filter(r => !SA_FOLDED.has(r.id));
    out.innerHTML = [...pl.map(p => `<li role="option"><a href="${esc(p[1])}">${icon("atlas")}<span><b>${esc(p[0])}</b><small>Page</small></span></a></li>`),
      ...rs.map(r => `<li role="option"><a href="#${toHash(r.id)}">${icon("list")}<span><b>${esc(r.name)}</b><small>${esc(r.fam)}${r.open ? "" : " · closed"}</small></span></a></li>`),
      `<li role="option"><a href="#register" ${hmGo({q})}>${icon("list")}<span><b>See every match for “${esc(q)}”</b><small>In the register</small></span></a></li>`].join("");
    out.hidden = false; box.setAttribute("aria-expanded", "true"); };
  box.addEventListener("input", draw);
  box.addEventListener("keydown", e => { const its = $$("a", out); if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); sel = (sel + (e.key === "ArrowDown" ? 1 : its.length - 1)) % its.length; its.forEach((a, i) => a.classList.toggle("on", i === sel)); }
    if (e.key === "Enter") { e.preventDefault(); (its[sel] || its[its.length - 1])?.click(); } if (e.key === "Escape") { out.hidden = true; box.setAttribute("aria-expanded", "false"); } });
  document.addEventListener("click", e => { if (!e.target.closest(".og-search")) { out.hidden = true; box.setAttribute("aria-expanded", "false"); } });
}

function hmTicker(){
  const t = $("#hmTicker"); if (!t) return;
  const N = ACC.news || {}, verb = {changed_name: "was renamed", merged: "merged", split: "was split", replaced: "was replaced", closed: "closed", left_gov: "left government", devolved: "was devolved"};
  const ev = D.ev.filter(e => e.date).sort((a, b) => b.date.localeCompare(a.date)).slice(0, 6).map(e => ({d: e.date, k: "Change", t: `${e.name} ${verb[e.event] || e.event.replace(/_/g, " ")}${e.successors.length ? ": now " + e.successors.map(s => BY[s] ? BY[s].name : s).slice(0, 2).join(" and ") : ""}`, h: "#" + toHash((e.successors.find(HM_NOPEN)) || e.id)}));
  const tr = (N.latest_treaties || []).map(x => ({d: x.date, k: "Treaty", t: x.title, h: x.url, ext: 1}));
  const gr = (N.closing || []).map(x => ({d: x.closes, k: "Grant closes", t: `${x.title} (${x.funder})`, h: x.url, ext: 1}));
  const items = [...ev, ...tr].sort((a, b) => b.d.localeCompare(a.d)).concat(gr);
  const li = x => `<li><span class="tk ${x.k === "Change" ? "c" : x.k === "Treaty" ? "t" : "g"}">${esc(x.k)}</span><time datetime="${esc(x.d)}">${esc(new Date(x.d + "T00:00:00").toLocaleDateString("en-GB", {day: "numeric", month: "short", year: "numeric"}))}</time><a href="${esc(x.h)}"${x.ext ? ' rel="noopener" target="_blank"' : ""}>${esc(x.t)}${x.ext ? '<span class="sr-only"> (opens in a new tab)</span>' : ""}</a></li>`;
  t.innerHTML = `<span class="tklabel">${icon("clock")}Latest</span><div class="tkview"><ul class="tktrack">${items.map(li).join("")}</ul><ul class="tktrack" aria-hidden="true">${items.map(li).join("").replace(/<a /g, '<a tabindex="-1" ')}</ul></div><button type="button" class="tkbtn" aria-pressed="false">Pause</button>`;
  const box = t.closest(".ticker") || t;  // the paused state lives on the outer ticker, where the CSS looks for it
  box.style.setProperty("--tkdur", Math.max(60, items.length * 7) + "s");
  const b = $(".tkbtn", t), set = p => { box.classList.toggle("paused", p); b.setAttribute("aria-pressed", String(p)); b.textContent = p ? "Play" : "Pause"; };
  if (HM_RM()) set(true);
  b.addEventListener("click", () => set(!box.classList.contains("paused")));
  COUNTS["s-ticker"] = items.length;
}

function hmCarousel(){
  const c = $("#hmCarousel"); if (!c) return;
  const N = ACC.news || {};
  const S = [
    ["crown", "Who answers", `${fmt(Object.keys(ACC.ch || {}).length)} bodies traced to whoever answers for them`, "Follow any body up its chain to Parliament or an assembly, with the law or record behind each step, the money that funds it and who owns it.", "#tree", "Trace a body"],
    ["atlas", "Nation by nation", `${fmt(hmNatCount("SC"))} in Scotland, ${fmt(hmNatCount("WA"))} in Wales, ${fmt(hmNatCount("NI"))} in Northern Ireland`, "Each nation's legislature, executive and judiciary, the Crown Dependencies and Overseas Territories, and the rings that connect them.", "nations.html", "Open the nations"],
    ["globe", "The UK and the world", `${fmt(N.treaties || 0)} treaties with ${fmt(N.partners || 0)} countries`, "A world map of treaty partners, the alliances and international bodies the UK belongs to, and which UK body speaks for it in each.", "world.html", "Open the section"],
    ["tree", "Org charts", `${fmt(OPEN.length)} open bodies in context`, "Who sits under whom, by accountability, nation, type or the world stage. Zoom, pan and open any body from the chart.", "orgchart.html", "Explore the charts"],
    ["coin", "Funding", `${fmt(N.grants || 0)} grants and ${fmt(N.schemes || 0)} schemes`, "Grants, finance schemes and innovation services from public funders, filtered by sector (fintech, medtech, govtech, regtech and more) and by who can apply.", "funding.html", "Find funding"],
    ["scale", "How matching works", `${fmt(N.sa_decided || 0)} of ${fmt(N.sa_total || 0)} near-name pairs decided`, "A wrong join is worse than a missing one. Every join says how it was made, and every decision keeps its evidence.", "#reconcile", "See the evidence"],
    ["data", "Use the data", "SQLite, CSV, JSON and BODS", "Query everything in your browser, or download it under the Open Government Licence.", "#data", "Get the data"]];
  c.innerHTML = `<div class="cslides" aria-live="off">${S.map((s, i) => `<div class="cslide" role="group" aria-roledescription="slide" aria-label="${i + 1} of ${S.length}: ${esc(s[1])}" ${i ? "hidden" : ""}><div class="cicon">${icon(s[0])}</div><div><span class="eyebrow">${esc(s[1])}</span><h3>${esc(s[2])}</h3><p>${esc(s[3])}</p><a class="btn" href="${esc(s[4])}">${esc(s[5])}</a></div></div>`).join("")}</div>
   <div class="cctl"><button type="button" class="cbtn" data-c="prev" aria-label="Previous slide">‹</button><span class="cdots">${S.map((s, i) => `<button type="button" class="cdot" data-c="${i}" aria-label="Slide ${i + 1}: ${esc(s[1])}" aria-current="${i === 0}"></button>`).join("")}</span><button type="button" class="cbtn" data-c="next" aria-label="Next slide">›</button><button type="button" class="cbtn cplay" aria-pressed="false">Pause</button></div>`;
  let cur = 0, timer = null, paused = HM_RM();
  const go = i => { cur = (i + S.length) % S.length; $$(".cslide", c).forEach((s, j) => s.hidden = j !== cur); $$(".cdot", c).forEach((d, j) => d.setAttribute("aria-current", String(j === cur))); };
  const play = () => { clearInterval(timer); if (!paused) timer = setInterval(() => go(cur + 1), 7000); };
  const pb = $(".cplay", c), setP = p => { paused = p; pb.setAttribute("aria-pressed", String(p)); pb.textContent = p ? "Play" : "Pause"; $(".cslides", c).setAttribute("aria-live", p ? "polite" : "off"); play(); };
  c.addEventListener("click", e => { const b = e.target.closest("[data-c]"); if (b) { const v = b.dataset.c; go(v === "prev" ? cur - 1 : v === "next" ? cur + 1 : +v); setP(true); } if (e.target.closest(".cplay")) setP(!paused); });
  c.addEventListener("mouseenter", () => clearInterval(timer)); c.addEventListener("mouseleave", play);
  c.addEventListener("focusin", () => clearInterval(timer)); c.addEventListener("focusout", e => { if (!c.contains(e.relatedTarget)) play(); });
  setP(paused);
}

function hmSpotlight(pick){
  const s = $("#s-spot"); if (!s) return;
  const pool = OPEN.filter(r => !SA_FOLDED.has(r.id) && ACC.web && ACC.web[r.id] && ACC.ch && ACC.ch[r.id] && ACC.cl && ACC.cl[r.id] && CLX(r.id, 0) !== "unknown").sort((a, b) => a.id.localeCompare(b.id));
  if (!pool.length) { s.hidden = true; return; }
  const day = Math.floor(Date.parse(D.built.slice(0, 10)) / 864e5);
  const r = pool[pick !== undefined ? pick : day % pool.length];
  const ch = CHAIN(r.id), topName = ch && ch.root !== r.id && BY[ch.root] ? BY[ch.root].name : "";
  const ins = ACC.ins && ACC.ins[r.id], rules = ins && ins.applies ? ins.applies.length : 0;
  s.innerHTML = `<span class="eyebrow">${icon("star")}Spotlight</span><h2><a href="#${toHash(r.id)}">${esc(r.name)}</a></h2>${facetLine(r.id)}
   <dl class="spotdl"><dt>Where</dt><dd>${esc(r.nat.map(x => NAT[x]).join(", ") || "UK-wide or not stated")}</dd>${topName ? `<dt>Answers in the end to</dt><dd>${esc(topName)}</dd>` : ""}<dt>Website</dt><dd>${profWeb(r).replace(/^<dt>Website<\/dt>/, "").replace(/^<dd>|<\/dd>$/g, "")}</dd>${rules ? `<dt>Rules that apply</dt><dd>${fmt(rules)}</dd>` : ""}</dl>
   <p class="spotact"><a class="btn" href="#${toHash(r.id)}">Open the profile</a><button type="button" class="btn ghost" id="spotNext">Show another</button></p>
   <p class="muted small">A different body each day, chosen from the ${fmt(pool.length)} with a website, a traced chain and a worked-out purpose.</p>`;
  $("#spotNext").addEventListener("click", () => { hmSpotlight(Math.floor(Math.random() * pool.length)); $("#spotNext").focus(); });
}

const HM_WAYS = [
  ["Find out who a body answers to", [["Search for the body", "#register"], ["Open its profile", "#register"], ["Follow its chain", "#tree"]]],
  ["Find funding for my organisation", [["Pick your sector", "funding.html"], ["Check who can apply", "funding.html#tab=grants"], ["Open the funder's page", "funding.html#tab=funders"]]],
  ["See how a nation is governed", [["Choose a nation", "nations.html"], ["Read its branches", "nations.html"], ["See its bodies", "#explore"]]],
  ["See the UK's place in the world", [["Open the treaty map", "world.html#tab=t"], ["Pick a country", "world.html#tab=c"], ["See the alliances", "world.html#tab=i"]]],
  ["Use the data in my own work", [["Download a file", "#data"], ["Query it in your browser", "#data"], ["Check the evidence", "#quality"]]],
  ["Check a fact or report a mistake", [["Find the body", "#register"], ["Read where each fact came from", "#quality"], ["Tell us", "#help"]]],
  ["Follow changes to the state", [["See closures and mergers", "#changes"], ["Read the latest", "jump:s-ticker"], ["Track a body's lineage", "#register"]]]];

function hmWayfinder(){
  const w = $("#hmWays"); if (!w) return;
  w.innerHTML = `<div class="waypick" role="group" aria-label="I want to">${HM_WAYS.map((x, i) => `<button type="button" class="pchip" data-w="${i}" aria-pressed="${i === 0}">${esc(x[0])}</button>`).join("")}</div><ol class="path" id="hmPath" aria-live="polite"></ol>`;
  const draw = i => { $("#hmPath").innerHTML = HM_WAYS[i][1].map((s, j) => `<li><span class="pn">${j + 1}</span>${s[1].startsWith("jump:") ? `<button type="button" class="linkbtn" data-jump="${esc(s[1].slice(5))}">${esc(s[0])}</button>` : `<a href="${esc(s[1])}">${esc(s[0])}</a>`}</li>`).join(""); $$("[data-w]", w).forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.w === i))); };
  w.addEventListener("click", e => { const b = e.target.closest("[data-w]"); if (b) draw(+b.dataset.w); });
  draw(0);
}

function hmSignposts(){
  const s = $("#hmSign"); if (!s) return;
  // Every section, in the order and groups of the global navigation (tools/design.py NAV)
  const GROUPS = [["Find", [["list", "Register", "Any body by name, code or identifier", "#register"], ["ask", "Ask a question", "Answers drawn only from the register", "#ask"]]],
    ["The state", [["atlas", "Explore the anatomy", "Families, sectors and department trees", "#explore"], ["atlas", "Nation by nation", "Law-makers, government and courts", "nations.html"], ["globe", "UK and the world", "Treaties, alliances and partners", "world.html"], ["tree", "Org charts", "Every body in context", "orgchart.html"]]],
    ["Accountability and money", [["crown", "Who answers", "Chains, money and owners", "#tree"], ["coin", "Funding", "Grants, schemes and services", "funding.html"], ["clock", "Change", "Renames, mergers and closures", "#changes"]]],
    ["Data", [["data", "Data and feeds", "Downloads and the SQLite file", "#data"], ["data", "Developer hub", "Connect, harvest, crosswalks, MCP", "developers.html"]]],
    ["Take part and trust", [["scale", "What needs a person", "How matching works; names to decide", "#reconcile"], ["shield", "Quality and trust", "Sources, checks and the audit trail", "#quality"], ["help", "Help", "Guides, tours and the glossary", "#help"]]]];
  s.innerHTML = GROUPS.map(([g, xs]) => `<div class="signgrp"><h3>${esc(g)}</h3><div class="signrow">${xs.map(p => `<a class="sign" href="${esc(p[3])}">${icon(p[0])}<b>${esc(p[1])}</b><span>${esc(p[2])}</span><i aria-hidden="true">→</i></a>`).join("")}</div></div>`).join("");
}

function hmFind(){  // Find your way: three tabs, arrow keys move between them, the choice is remembered
  const tabs = $$('#s-find [role="tab"]'); if (!tabs.length) return;
  const show = (id, focus) => { tabs.forEach(t => { const on = t.id === "fyt-" + id; t.setAttribute("aria-selected", String(on)); t.tabIndex = on ? 0 : -1; $("#" + t.getAttribute("aria-controls")).hidden = !on; if (on && focus) t.focus(); }); try { localStorage.setItem("og-find", id); } catch (e) { /* storage off */ } };
  tabs.forEach((t, i) => { t.addEventListener("click", () => show(t.id.slice(4))); t.addEventListener("keydown", e => { if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return; e.preventDefault(); const n = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length]; show(n.id.slice(4), true); }); });
  let last = ""; try { last = localStorage.getItem("og-find") || ""; } catch (e) { /* storage off */ }
  if (["who", "task", "all"].includes(last)) show(last);
}

document.addEventListener("click", e => { const b = e.target.closest("[data-jump]"); if (!b) return; const s = document.getElementById(b.dataset.jump); if (!s) return; if (s.tagName === "DETAILS") s.open = true; s.scrollIntoView({behavior: HM_RM() ? "auto" : "smooth", block: "start"}); const h = $("h2,h3", s) || s; h.tabIndex = -1; h.focus({preventScroll: true}); });

function homeExtras(){
  ["s-find", "s-carousel", "s-spot"].forEach(x => NEWSEC.add(x));
  hmBullseye(); hmSearch(); hmTicker(); hmCarousel(); hmSpotlight(); hmWayfinder(); hmSignposts(); hmFind();
  COUNTS["s-spot"] = 1;
}
