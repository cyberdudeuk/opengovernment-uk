// ---- WHO ANSWERS (0.3.0): accountability, money and ownership, traced to source ----
const ACC = JSON.parse(document.getElementById("tree").textContent);
const ACCE = ACC.e.map(a => ({c:a[0], p:a[1], pt:a[2], rel:a[3], src:a[4], ref:a[5], how:a[6], x:a[7]}));
const ECHILD = {}, EPARENT = {}; ACCE.forEach((e, i) => { (ECHILD[e.c] = ECHILD[e.c] || []).push(i); if (e.p) (EPARENT[e.p] = EPARENT[e.p] || []).push(i); });
const CHAIN = id => { const c = ACC.ch[id]; return c ? {path:c[0].map(i => ACCE[i]), root:c[1], ans:ACC.ans[c[2]], agree:c[3], n:c[4]} : null; };
const RELNAME = {accounts:"included in the estimate and accounts of", sponsors:"sponsored by", controls:"controlled by", parent:"GOV.UK lists its parent as", owns:"owned or controlled by"};
const RELICON = {accounts:"scale", sponsors:"people", controls:"shield", parent:"tree", owns:"coin"};
const SRC = k => ACC.src[k] || {name:k, url:"#"};
const money = n => n == null || isNaN(n) ? "not published" : n >= 1e9 ? "£" + (n / 1e9).toFixed(n >= 1e10 ? 0 : 1) + "bn" : n >= 1e6 ? "£" + (n / 1e6).toFixed(n >= 1e8 ? 0 : 1) + "m" : "£" + fmt(Math.round(n));
const mlm = n => n == null ? "" : fmt(Math.round(n * 10) / 10);
const TERMS = {
 "estimate": "The Supply Estimate a department lays before Parliament each year. The Estimates and Accounts Order names every body whose spending and accounts are included in it: in law, that department answers to Parliament for the body's money.",
 "sponsor": "The department or devolved government that sets a body's budget, appoints or oversees its board, and answers for it to ministers. Recorded by the Cabinet Office Public Bodies Directory and by ONS.",
 "accountable owner": "The body at the top of a chain: a ministerial department, a devolved government, a council or a body that answers to a legislature directly. The public-sector equivalent of an ultimate parent.",
 "person with significant control": "Companies House's term for whoever owns or controls a company. For a government-owned company this is usually a Secretary of State or HM Treasury, which is the Crown acting through a minister.",
 "trading fund": "A government operation financed from its own income rather than from votes in Parliament, set up by an order under the Government Trading Funds Act 1973. It still answers to a minister.",
 "public corporation": "A body ONS classifies as a market producer controlled by government, such as a publicly owned company. It sits in the public sector but outside central and local government.",
 "PFI": "The Private Finance Initiative and its successor PF2: a private project company builds and runs an asset, and a public authority pays it a yearly unitary charge for the life of the contract.",
 "unitary charge": "The annual payment a public authority makes to a PFI project company. HM Treasury publishes the forecast for every year of each contract.",
 "project company": "The company set up to deliver one PFI contract, also called a special purpose vehicle (SPV). Its owners are the equity holders.",
 "Whole of Government Accounts": "One set of accounts for the UK public sector, prepared by HM Treasury. The designation order names the bodies that must supply data for it.",
 "SHA-256": "A fingerprint of a file's exact bytes. If even one character changes, the fingerprint changes.",
 "agreement": "How many independent sources name the same body as the one this body answers to. More agreement means the link is better attested; it doesn't make it a legal opinion.",
 "English Devolution Act": "The English Devolution and Community Empowerment Act 2026. It creates strategic authorities with set powers, brings back the supplementary vote for mayors, ends the committee system for running councils, and gives communities new rights such as first refusal to buy local assets.",
 "strategic authority": "Under the English Devolution Act 2026, a council or group of councils given powers over a wider area: a foundation authority, a mayoral authority, or an established mayoral authority with the most powers.",
 "area of competence": "One of the nine subjects the 2026 Act lets strategic authorities work on, such as transport, skills, housing and public safety.",
 "local government reorganisation": "The government's programme to replace county and district councils (two tiers) with single unitary councils that do everything, in 21 areas of England.",
 "unitary council": "A single council that runs all local services in its area, rather than sharing them between a county council and a district council.",
 "shadow council": "A newly elected council that prepares to take over before the old councils close on vesting day.",
 "vesting day": "The day new councils take over and the old ones close.",
 "supplementary vote": "A voting system for electing one person: you mark a first and a second choice. If nobody gets more than half the first choices, the top two go through and second choices for them are added.",
 "unresolved": "A name in a source that couldn't be matched to exactly one register record. It is listed for a person to resolve rather than guessed."
};
function termHTML(word, label){ const k = Object.keys(TERMS).find(t => t.toLowerCase() === word.toLowerCase()); return k ? `<button type="button" class="term-b" data-tip="${esc(TERMS[k])}">${esc(label || word)}</button>` : esc(label || word); }
function applyTerms(root = document){ $$("[data-term]", root).forEach(s => { s.outerHTML = termHTML(s.dataset.term, s.textContent || s.dataset.term); }); }
(() => {
  const box = document.createElement("div"); box.id = "tipbox"; box.setAttribute("role", "tooltip"); box.hidden = true; document.body.append(box);
  const show = b => { box.textContent = b.dataset.tip; box.hidden = false; b.setAttribute("aria-describedby", "tipbox"); const r = b.getBoundingClientRect(), w = box.offsetWidth, h = box.offsetHeight; box.style.left = Math.max(8, Math.min(innerWidth - w - 8, r.left)) + "px"; box.style.top = (r.bottom + h + 12 > innerHeight ? r.top - h - 6 : r.bottom + 6) + "px"; };
  const hide = () => { box.hidden = true; $$(".term-b[aria-describedby]").forEach(b => b.removeAttribute("aria-describedby")); };
  document.addEventListener("mouseover", e => { const b = e.target.closest(".term-b"); if (b) show(b); });
  document.addEventListener("mouseout", e => { if (e.target.closest(".term-b")) hide(); });
  document.addEventListener("focusin", e => { const b = e.target.closest(".term-b"); b ? show(b) : hide(); });
  document.addEventListener("click", e => { const b = e.target.closest(".term-b"); if (b) show(b); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") hide(); });
  addEventListener("scroll", hide, {passive:true});
})();
function stepEvidence(e){ const s = SRC(e.src); return `<div class="ev">${termHTML("source", "Source")}: <a href="${esc(s.url)}" rel="noopener" target="_blank">${esc(s.name)}</a>, ${esc(e.ref)}. Written there as “${esc(e.pt)}”. Matched by ${esc(e.how)}.${s.sha256 ? ` <span class="mono" title="SHA-256 of the file read">#${esc(s.sha256.slice(0, 12))}</span>` : ""}</div>`; }
// nations: final placement from tools/nations.py; colour is always paired with the two-letter label
const NATNAME = {EN:"England", SC:"Scotland", WA:"Wales", NI:"Northern Ireland", UK:"Whole UK", GB:"UK Government, extent not stated", OT:"Overseas Territories", CD:"Crown Dependencies"};
const natOf = id => (ACC.nat && ACC.nat[id]) || [];
const nsw = k => ["EN","SC","WA","NI","UK"].includes(k) ? `<span class="nsw" style="--c:var(--n${k})" aria-hidden="true"></span>` : k === "GB" ? `<span class="nsw gb" aria-hidden="true"></span>` : "";
const nchip = k => `<span class="nchip" title="${esc(NATNAME[k] || k)}">${nsw(k)}${esc(k)}</span>`;
const natHTML = id => { const n = natOf(id); if (!n.length) return ""; const home = n.filter(k => ["EN","SC","WA","NI"].includes(k));
  const multi = home.length > 1 || n.includes("UK"); return `${multi ? `<span class="nmulti" title="Performs functions for more than one nation">serves ${n.includes("UK") ? "the whole UK" : home.length + " nations"}</span>` : ""}${n.map(nchip).join("")}`; };
function chainHTML(id){
  const r = BY[id], c = CHAIN(id); if (!r || !c) return `<p class="muted">No accountability data for this record.</p>`;
  const steps = [`<div class="step start"><span class="dot">${icon("tree")}</span><div><b>${orgLink(id)}</b>${natHTML(id)}<span class="rel">${esc(r.fam)} · ${esc(r.kind)}</span></div></div>`];
  c.path.forEach(e => steps.push(`<div class="step"><span class="dot">${icon(RELICON[e.rel] || "link")}</span><div><span class="rel">${esc(RELNAME[e.rel] || e.rel)}</span><b>${orgLink(e.p)}</b>${stepEvidence(e)}</div></div>`));
  const nf = /^not established/.test(c.ans);
  steps.push(`<div class="step root"><span class="dot">${icon("crown")}</span><div><span class="rel">${nf ? "No further link in the sources" : "Answers in the end to"}</span><b>${esc(nf ? "Not established from the sources: listed under What couldn't be matched" : c.ans)}</b></div></div>`);
  const conf = ACC.cf.find(x => x[0] === id);
  const agree = c.n ? `<p class="muted" style="margin-top:4px">${termHTML("agreement", "Agreement")}: ${c.agree} source${c.agree === 1 ? "" : "s"} name the same body for the first link${c.n > 1 ? `; ${c.n} different bodies are named in all` : ""}.</p>` : "";
  const cf = conf ? `<div class="note" style="margin-top:8px"><b>Sources differ.</b> ${conf[1].map(v => `${orgLink(v[0])} <span class="muted">(${v[1].map(s => esc(SRC(s).name.split(":")[0])).join(", ")})</span>`).join("; ")}. The chain follows the law first, then the Public Bodies Directory, then ONS, then GOV.UK.</div>` : "";
  return `<div class="chain">${steps.join("")}</div>${agree}${cf}`;
}
function factsHTML(id){
  const m = ACC.m[id], w = ACC.w[id], wo = ACC.wo[id], out = [];
  if (m) out.push(`<dt>Government funding (${esc(m[0])})</dt><dd class="mny">${money(m[1])} <span class="muted">of which other income ${money(m[2])}</span></dd><dt>Total managed expenditure</dt><dd class="mny">${money(m[3])}</dd>${m[4] ? `<dt>Classification</dt><dd>${esc(m[4])}</dd>` : ""}${m[6] ? `<dt>Ombudsman</dt><dd>${esc(m[6])}</dd>` : ""}`);
  if (wo) out.push(`<dt>${termHTML("Whole of Government Accounts", "WGA designation")} 2026</dt><dd>${esc(wo)}</dd>`);
  if (w) out.push(`<dt>WGA 2024-25</dt><dd>${esc(w[0])}${w[1] ? " · " + esc(w[1]) : ""}</dd>`);
  if (LGAREA[id]) { const a = LG.reorganisation.areas[LGAREA[id][0]]; out.push(`<dt>Reorganisation</dt><dd>Part of <b>${esc(a.area)}</b>: ${esc(LG.reorganisation.statuses[a.status].label.toLowerCase())}. New councils take over ${esc(lgDate(a.vesting))}${a.status !== "decided" ? " (planned)" : ""}. <a href="#s-localgov">What's changing</a> · ${lgSrc(a.src)}</dd>`); }
  if (LGSA[id]) { const s2 = LGSA[id]; out.push(`<dt>Under the 2026 Act</dt><dd>${termHTML("strategic authority", LGTIER[s2.tier].label)}${s2.first_mayor ? `, first mayoral election ${esc(lgDate(s2.first_mayor))}` : ""} · ${lgSrc(s2.src)}</dd>`); }
  if (ACC.tf.includes(id)) out.push(`<dt>Financing</dt><dd>${termHTML("trading fund", "Trading fund")}</dd>`);
  if (ACC.pcs[id]) out.push(`<dt>ONS sector</dt><dd>${termHTML("public corporation", "Public corporation")}: ${esc(ACC.pcs[id])}</dd>`);
  const pp = ACC.ppp.filter(p => p[4] === id || p[6] === id);
  if (pp.length) out.push(`<dt>${termHTML("PFI", "PFI and PF2 contracts")}</dt><dd class="mny">${fmt(pp.length)} contracts, capital £${fmt(Math.round(pp.reduce((s, p) => s + (p[12] || 0), 0)))}m, ${termHTML("unitary charge", "charges")} in 2025-26 £${fmt(Math.round(pp.reduce((s, p) => s + (p[13] || 0), 0)))}m</dd>`);
  if (ACC.pw[id]) out.push(`<dt>${termHTML("person with significant control", "People with significant control")}</dt><dd>${ACC.pw[id]} natural person${ACC.pw[id] > 1 ? "s" : ""}, not named here</dd>`);
  return out.length ? `<dl class="kv" style="margin-top:12px">${out.join("")}</dl>` : "";
}
function linksTable(id){
  const up = (ECHILD[id] || []).map(i => ACCE[i]), down = (EPARENT[id] || []).map(i => ACCE[i]);
  const row = (e, other) => `<tr><td>${esc(RELNAME[e.rel] || e.rel)}</td><td>${orgLink(other)}</td><td><a href="${esc(SRC(e.src).url)}" rel="noopener" target="_blank">${esc(SRC(e.src).name.split(":")[0])}</a></td><td>${esc(e.ref)}</td></tr>`;
  const answersFor = Object.keys(ACC.ch).filter(k => ACC.ch[k][1] === id && k !== id).length;
  return `<h3 style="margin-top:14px">Every link recorded for this body</h3><div class="tablewrap"><table><thead><tr><th scope="col">Relation</th><th scope="col">Other body</th><th scope="col">Source</th><th scope="col">Where in the source</th></tr></thead><tbody>${up.map(e => row(e, e.p)).join("") || '<tr><td colspan="4" class="muted">No upward link in the sources.</td></tr>'}</tbody></table></div>${down.length ? `<details style="margin-top:8px"><summary>${fmt(down.length)} bodies link up to it${answersFor ? `; it is the ${termHTML("accountable owner", "accountable owner")} of ${fmt(answersFor)}` : ""}</summary><div class="tablewrap"><table><tbody>${down.slice(0, 400).map(e => `<tr><td>${orgLink(e.c)}</td><td>${esc(RELNAME[e.rel] || e.rel)} it</td><td>${esc(SRC(e.src).name.split(":")[0])}</td></tr>`).join("")}</tbody></table></div></details>` : ""}`;
}
// the profile gains a card: who it answers to, the money, every link and its evidence
const _renderProfileBase = renderProfile;
renderProfile = function(id){
  _renderProfileBase(id);
  const host = $("#profile"); if (!host || !ACC.ch[id]) return;
  const card = document.createElement("div"); card.className = "card";
  card.innerHTML = `<h2>Who it answers to</h2><p class="muted" style="margin:4px 0 0">Traced one source at a time to an elected body. ${termHTML("accountable owner", "What this means")}.</p>${chainHTML(id)}${factsHTML(id)}${linksTable(id)}`;
  const first = host.querySelector(".card"); first ? first.after(card) : host.prepend(card);
  $$("#profile > .card").forEach((c, i) => c.id = "s-p" + i);
};
function tbars(el, rows, fv = fmt){ const max = Math.max(1, ...rows.map(r => r[1])); el.innerHTML = rows.map(r => `<div class="bar"><span>${r[2] ? orgLink(r[2]) : esc(r[0])}</span><span class="track" aria-hidden="true"><span class="fill" style="width:${(r[1] / max * 100).toFixed(1)}%"></span></span><span class="v">${fv(r[1])}</span></div>`).join(""); }
const CPK = {}; (function walk(ns){ ns.forEach(n => { if (n.member && n.kind) CPK[n.id] = n.kind; if (n.children) walk(n.children); }); })(ACC.corp.trees);
// grouping facets shared by the department tree and the corporation trees (purpose and activity are MODELLED: tools/classify.py)
const FACET = {purpose:0, activity:1, btype:2};
const facetKey = (id, by) => by === "kind" ? (CPK[id] || "other") : ((ACC.cl[id] || [])[FACET[by]] || "unknown");
const facetLab = (by, k) => by === "kind" ? (ACC.corp.meta.kinds[k] || ["Other body", "Not itself a trading fund or public corporation: a body recorded as answering to one."]) : ((ACC.clm[by] || {})[k] || [k, ""]);
const grpHead = (by, k, n) => { const [l, x] = facetLab(by, k); return `<span class="gl">${x ? `<button type="button" class="term-b" data-tip="${esc(x)}">${esc(l)}</button>` : esc(l)}</span><span class="c">${fmt(n)}</span>`; };
const bucket = (ids, by) => { const g = new Map(); ids.forEach(x => { const k = facetKey(Array.isArray(x) ? x[0] : x.id || x, by); (g.get(k) || g.set(k, []).get(k)).push(x); });
  return [...g.entries()].sort((a, b) => (a[0] === "unknown") - (b[0] === "unknown") || b[1].length - a[1].length || facetLab(by, a[0])[0].localeCompare(facetLab(by, b[0])[0])); };
const GROUP_MIN = 6; // fewer children than this are listed straight, without folders
const SPLIT_MIN = 12; // a folder this big is split again by the next facet
const NEXT = {purpose:["purpose", "btype", "activity"], activity:["activity", "btype", "purpose"], btype:["btype", "purpose", "activity"], kind:["kind", "purpose", "activity"]};
// folders inside folders: group by the chosen facet, then split any big folder by the next one (purpose, type of body, activity)
function folders(items, order, render, cls = "grp", openAll = false){
  const [by, ...rest] = order;
  return bucket(items, by).map(([k, xs]) => { const inner = rest.length && xs.length >= SPLIT_MIN ? folders(xs, rest, render, cls, openAll) : render(xs);
    return cls === "grp" ? `<li class="grp"><details ${openAll ? "open" : ""}><summary>${grpHead(by, k, xs.length)}</summary><ul>${inner}</ul></details></li>` : `<details class="${cls}" ${openAll ? "open" : ""}><summary>${grpHead(by, k, xs.length)}</summary>${inner}</details>`; }).join("");
}
function treeOf(rootId, by = ""){
  // corporate-tree view: bodies whose chain passes through each body, built from the chains themselves
  const kids = {}; Object.keys(ACC.ch).forEach(k => { const p = ACC.ch[k][0].map(i => ACCE[i]); let child = k; p.forEach(e => { (kids[e.p] = kids[e.p] || new Map()).set(child, e.rel); child = e.p; }); });
  const size = {}; const count = (id, seen = new Set()) => { if (size[id] != null) return size[id]; if (seen.has(id)) return 0; seen.add(id); let n = 0; (kids[id] || new Map()).forEach((_, c) => n += 1 + count(c, seen)); return size[id] = n; };
  const nm = id => BY[id] ? BY[id].name : "";
  const list = (ks, depth) => `${ks.slice(0, 250).map(([c, r]) => node(c, r, depth + 1)).join("")}${ks.length > 250 ? `<li class="muted">and ${fmt(ks.length - 250)} more</li>` : ""}`;
  const node = (id, rel, depth) => { const ks = [...(kids[id] || new Map()).entries()].sort((a, b) => count(b[0]) - count(a[0]) || nm(a[0]).localeCompare(nm(b[0])));
    const lab = `${orgLink(id)}${rel ? `<span class="rl">${esc(rel)}</span>` : ""}${ks.length ? `<span class="c">${fmt(count(id))}</span>` : ""}`;
    if (!ks.length || depth > 4) return `<li>${lab}</li>`;
    const body = by && ks.length >= GROUP_MIN ? folders(ks, NEXT[by], xs => list(xs, depth)) : list(ks, depth);
    return `<li><details ${depth < 1 ? "open" : ""}><summary>${lab}</summary><ul>${body}</ul></details></li>`; };
  return {html: `<ul class="otree">${node(rootId, "", 0)}</ul>`, kids, count};
}
function whoAnswers(){
  localGov();
  const ids = Object.keys(ACC.ch), traced = ids.filter(k => !/^not established/.test(ACC.ans[ACC.ch[k][2]]));
  const linked = ids.filter(k => ACC.ch[k][0].length);
  const st = [[ids.length, "open bodies with a chain"], [traced.length, "reach an elected body"], [ACCE.length, "links, each with its source"], [Object.keys(ACC.src).length, "authoritative sources"], [ACC.ppp.length, "PFI and PF2 contracts"], [ACC.un.length, "names left for a person"]];
  $("#tStats").innerHTML = st.map((x, i) => `<div class="stat ${["navy","sea","gold","navy","red","gold"][i]}"><b data-n="${x[0]}">0</b><span>${esc(x[1])}</span></div>`).join(""); $$("#tStats b").forEach(b => countUp(b, +b.dataset.n));
  const pct = n => (n / ids.length * 100).toFixed(0) + "%";
  const pwTot = Object.values(ACC.pw).reduce((a, b) => a + b, 0) + ACC.ppp.reduce((a, p) => a + (p[11] || 0), 0);
  $("#tLimits").innerHTML = `<h3>What this can and can't tell you</h3><ul>
   <li><b>It is a reading of the sources, not a legal opinion.</b> Each step is the strongest link one source states. The law comes first (the Estimates and Accounts Orders), then the Public Bodies Directory, then ONS, then GOV.UK, then ownership records.</li>
   <li><b>Base rate.</b> ${fmt(traced.length)} of ${fmt(ids.length)} open bodies (${pct(traced.length)}) reach an elected body; ${fmt(ids.length - traced.length)} (${pct(ids.length - traced.length)}) don't. Most of those are ONS-classified bodies whose sponsor isn't itself a register record. ${fmt(ids.length - linked.length)} bodies have no upward link and are their own root, which is right for departments, councils and NHS bodies.</li>
   <li><b>The sources are of different dates.</b> Public Bodies Directory 2023/24; Whole of Government Accounts 2024-25; PFI at 31 March 2025; ONS November 2026; the Orders for 2026-27. Money is shown as each source publishes it and is not reconciled between them.</li>
   <li><b>Disagreement is settled openly.</b> Where sources name different parents, each case is checked against the published order of sources and against the other sources. ${fmt(ACC.cfr)} cases are settled that way; ${fmt(ACC.cf.length)} still need a person to decide and are listed.</li>
   <li><b>No personal data.</b> ${fmt(pwTot)} natural persons who own or control a company or a PFI project company are counted and never named.</li></ul>`;
  // trace
  const show = id => { $("#tChain").innerHTML = `<div class="card" style="background:var(--paper-2)">${chainHTML(id)}${factsHTML(id)}<p style="margin-top:10px"><a class="btn ghost small" href="#${toHash(id)}">${icon("tree")}Open the full profile</a></p></div>`; };
  const hits = q => { const rs = q.length < 2 ? [] : searchRecords(q, 30).filter(r => ACC.ch[r.id]).slice(0, 9); $("#tHits").innerHTML = rs.map(r => `<button class="tile" type="button" data-tid="${esc(r.id)}">${icon("tree")}<b>${esc(r.name)}</b><span>${esc(r.kind)}</span></button>`).join(""); };
  $("#tQ").addEventListener("input", e => hits(e.target.value.trim()));
  $("#tHits").addEventListener("click", e => { const b = e.target.closest("[data-tid]"); if (b) show(b.dataset.tid); });
  const eg = R.find(r => r.ids.govuk_slug === "met-office"); if (eg) show(eg.id);
  // roots
  const byAns = {}; ids.forEach(k => { const a = ACC.ans[ACC.ch[k][2]]; byAns[a] = (byAns[a] || 0) + 1; });
  const byRoot = {}; ids.forEach(k => { const c = ACC.ch[k]; if (c[0].length) byRoot[c[1]] = (byRoot[c[1]] || 0) + 1; });
  const depts = R.filter(r => r.open && r.kind === "Ministerial department").sort((a, b) => (byRoot[b.id] || 0) - (byRoot[a.id] || 0));
  const RT = [["Answers to", `<p class="muted" style="margin:8px 0">Each open body, grouped by the elected body it answers to in the end.</p><div class="bars" id="ansBars"></div>`],
              ["Ultimate owners", `<p class="muted" style="margin:8px 0">The bodies at the top of the most chains, the public-sector equivalent of a group parent, split by the nation each one serves. A body that serves more than one nation appears under each, flagged. <a href="nations.html">See every nation's register</a>.</p><div class="natgrid" id="ownNat"></div>`],
              ["Tree", `<div class="controls" style="margin-top:8px"><label>Start from<select id="treeRoot">${depts.map(d => `<option value="${esc(d.id)}">${esc(d.name)} (${fmt(byRoot[d.id] || 0)})</option>`).join("")}</select></label><label>Group the bodies under each one by<select id="treeBy"><option value="purpose">What it is for</option><option value="activity">What it does</option><option value="btype">Type of body</option><option value="">Don't group</option></select></label></div><p class="muted">Every body whose chain passes through it, nested by the link that joins them. The number is how many bodies sit below. Where a body has ${GROUP_MIN} or more bodies under it, they are put in folders by what they are for, what they do or what type of body they are, so a long list is easier to read. “What it is for” and “what it does” are worked out from each body's kind, name and description, so a few may be wrong: send a correction if you spot one.</p><div id="treeOut"></div>`]];
  $("#rootTabs").innerHTML = RT.map((t, i) => `<button class="tab" role="tab" id="rt-${i}" aria-controls="rp-${i}" aria-selected="${i === 0}" tabindex="${i ? -1 : 0}">${esc(t[0])}</button>`).join("");
  $("#rootPanels").innerHTML = RT.map((t, i) => `<div class="tabpanel" role="tabpanel" id="rp-${i}" aria-labelledby="rt-${i}" ${i ? "hidden" : ""}>${t[1]}</div>`).join(""); tabs($("#rootTabs"));
  tbars($("#ansBars"), Object.entries(byAns).sort((a, b) => b[1] - a[1]).map(([a, n]) => [a, n]));
  { const cols = {EN:[], SC:[], WA:[], NI:[], UK:[], GB:[]};
    Object.entries(byRoot).forEach(([k, n]) => { const ns = natOf(k); (ns.length ? ns : ["GB"]).forEach(c => { if (cols[c]) cols[c].push([k, n]); }); });
    $("#ownNat").innerHTML = Object.entries(cols).map(([c, xs]) => `<section class="natcol" style="--c:var(--n${c})" aria-labelledby="on-${c}"><h3 id="on-${c}">${nsw(c)}${esc(NATNAME[c])} <span class="muted" style="font-weight:400">· ${fmt(xs.length)} owners</span></h3><div class="bars" id="ob-${c}"></div></section>`).join("");
    Object.entries(cols).forEach(([c, xs]) => { const el = $("#ob-" + c); el.innerHTML = xs.length ? "" : `<p class="muted">None in the sources.</p>`;
      if (xs.length) { tbars(el, xs.sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, n]) => [BY[k] ? BY[k].name : k, n, k]));
        el.querySelectorAll(".bar").forEach((b, i) => { const k = xs[i][0], h = natHTML(k); if (h && (natOf(k).length > 1 || natOf(k).includes("UK"))) b.firstElementChild.insertAdjacentHTML("beforeend", h); }); } }); }
  const drawTree = () => { $("#treeOut").innerHTML = treeOf($("#treeRoot").value, $("#treeBy").value).html; }; ["treeRoot", "treeBy"].forEach(i => $("#" + i).addEventListener("change", drawTree)); if (depts.length) drawTree();
  // money
  const gf = Object.entries(ACC.m).filter(([, m]) => m[1] > 0).sort((a, b) => b[1][1] - a[1][1]);
  const pfiDept = {}; ACC.ppp.forEach(p => { const k = p[6] || ("t:" + p[7]); const a = pfiDept[k] = pfiDept[k] || {n:0, cap:0, pay:0, label:p[7]}; a.n++; a.cap += p[12] || 0; a.pay += p[13] || 0; });
  const MT = [["Government funding", `<p class="muted" style="margin:8px 0">The 25 bodies that receive the most income from government, as the Cabinet Office Public Bodies Directory 2023/24 records it. ${fmt(gf.length)} bodies report a figure.</p><div class="bars" id="gfBars"></div>`],
              ["PFI charges by department", `<p class="muted" style="margin:8px 0">${termHTML("unitary charge", "Unitary charges")} forecast for 2025-26 across ${fmt(ACC.ppp.length)} ${termHTML("PFI", "PFI and PF2")} contracts, by the department HM Treasury records. £ millions, nominal.</p><div class="bars" id="pfiBars"></div>`],
              ["How the money flows", `<div class="prose" style="margin-top:8px"><ol><li><b>Parliament votes Supply</b> to each department through its Estimate.</li><li><b>The department funds its bodies</b> by grant-in-aid or by including them in its own accounts. The Estimates and Accounts Order says which, in law; the Public Bodies Directory records the amounts.</li><li><b>Some bodies earn their own income</b>: ${termHTML("trading fund", "trading funds")} and ${termHTML("public corporation", "public corporations")} sell services, and still answer to a minister.</li><li><b>Some assets are financed privately</b>: under ${termHTML("PFI")}, a ${termHTML("project company")} owned by investors is paid a yearly charge by the procuring authority.</li><li><b>Everything is consolidated</b> in the ${termHTML("Whole of Government Accounts")}, which the designation order defines.</li></ol></div>`]];
  $("#moneyTabs").innerHTML = MT.map((t, i) => `<button class="tab" role="tab" id="mt-${i}" aria-controls="mp-${i}" aria-selected="${i === 0}" tabindex="${i ? -1 : 0}">${esc(t[0])}</button>`).join("");
  $("#moneyPanels").innerHTML = MT.map((t, i) => `<div class="tabpanel" role="tabpanel" id="mp-${i}" aria-labelledby="mt-${i}" ${i ? "hidden" : ""}>${t[1]}</div>`).join(""); tabs($("#moneyTabs"));
  tbars($("#gfBars"), gf.slice(0, 25).map(([k, m]) => [BY[k] ? BY[k].name : k, m[1], k]), money);
  tbars($("#pfiBars"), Object.entries(pfiDept).sort((a, b) => b[1].pay - a[1].pay).slice(0, 15).map(([k, a]) => [a.label, a.pay, k.startsWith("t:") ? null : k]), v => "£" + fmt(Math.round(v)) + "m");
  // PPP
  const PS = [...new Set(ACC.ppp.map(p => p[2]))].sort(), SS = [...new Set(ACC.ppp.map(p => p[3]))].sort();
  $("#pppStat").innerHTML += PS.map(s => `<option>${esc(s)}</option>`).join(""); $("#pppSec").innerHTML += SS.map(s => `<option>${esc(s)}</option>`).join("");
  const cap = ACC.ppp.reduce((s, p) => s + (p[12] || 0), 0), pay = ACC.ppp.reduce((s, p) => s + (p[13] || 0), 0);
  $("#pppIntro").innerHTML = `${fmt(ACC.ppp.length)} contracts from HM Treasury's register at 31 March 2025: capital value £${fmt(Math.round(cap))}m, charges forecast for 2025-26 £${fmt(Math.round(pay))}m. Each names its procuring authority, its ${termHTML("project company")} and the investors who own it, which is the ownership chain of the asset.`;
  let lim = 60;
  const ppRender = () => { const q = $("#pppQ").value.toLowerCase(), s = $("#pppStat").value, sc = $("#pppSec").value;
    const rs = ACC.ppp.filter(p => (!s || p[2] === s) && (!sc || p[3] === sc) && (!q || [p[1], p[5], p[7], p[8], ...p[10].map(x => x[0])].join(" ").toLowerCase().includes(q)));
    $("#pppCap").textContent = `${fmt(rs.length)} contracts match; showing ${fmt(Math.min(lim, rs.length))}.`;
    $("#pppRows").innerHTML = rs.slice(0, lim).map(p => `<tr><td><b>${esc(p[1])}</b><br><span class="muted">${esc(p[3])} · ${esc(p[2])}</span></td><td>${p[4] ? orgLink(p[4]) : esc(p[5])}</td><td>${p[6] ? orgLink(p[6]) : esc(p[7])}</td><td>${p[9] ? `<a href="https://find-and-update.company-information.service.gov.uk/company/${esc(p[9])}" rel="noopener" target="_blank">${esc(p[8] || p[9])}</a>` : esc(p[8] || "not published")}<div class="inv">${p[10].map(x => `${esc(x[0])}${typeof x[1] === "number" ? " " + (x[1] <= 1 ? Math.round(x[1] * 100) : Math.round(x[1])) + "%" : ""}`).join("; ")}${p[11] ? `; ${p[11]} individual${p[11] > 1 ? "s" : ""} not named` : ""}</div></td><td class="num">${mlm(p[12])}</td><td class="num">${mlm(p[13])}</td><td class="mono">${esc((p[14] || "").slice(0, 10))}</td></tr>`).join("");
    $("#pppMore").hidden = rs.length <= lim; };
  ["pppQ", "pppStat", "pppSec"].forEach(i => $("#" + i).addEventListener("input", () => { lim = 60; ppRender(); }));
  $("#pppMore").addEventListener("click", () => { lim += 120; ppRender(); }); ppRender();
  // trading funds and public corporations: one family tree each (tools/corporations.py), grouped by owner, then by a chosen facet
  { const C = ACC.corp, K = C.meta.kinds, cn = C.meta.counts, LV = C.meta.levels;
    $("#cpIntro").innerHTML = `A ${termHTML("trading fund")} pays its way from what it charges; a ${termHTML("public corporation")} is a business that government owns or controls. Here each one is the top of its own family tree, showing the companies and bodies under it and the chain above it to whoever answers for it. Where one belongs to another (an airport company owned by an airport group, say), it sits inside its parent's tree instead of on its own, so every body appears once.`;
    $("#cpStats").innerHTML = [[cn.members, "bodies"], [cn.trees, "family trees"], [cn.consolidated, "sit inside another's tree"], [cn.trading_funds, "trading funds"], [cn.both, "are both"]].map((x, i) => `<div class="stat ${["navy","sea","gold","red","navy"][i]}"><b data-n="${x[0]}">0</b><span>${esc(x[1])}</span></div>`).join(""); $$("#cpStats b").forEach(b => countUp(b, +b.dataset.n));
    $("#cpRule").textContent = C.meta.rule.replace(/\s+/g, " ");
    $("#cpKind").innerHTML += Object.entries(K).map(([k, v]) => `<option value="${esc(k)}">${esc(v[0])}</option>`).join("");
    const kchip = n => n.kind ? `<span class="kchip k-${esc(n.kind)}" title="${esc(K[n.kind][1])}">${esc(K[n.kind][0])}${n.also ? " · " + esc(K[n.also][0]) : ""}</span>` : "";
    const nodeH = (n, d) => { const lab = `${orgLink(n.id)}${n.member ? kchip(n) : ""}${natHTML(n.id)}${n.children ? `<span class="c">${fmt(n.children.length)}</span>` : ""}`;
      return n.children ? `<li><details ${d < 1 ? "open" : ""}><summary>${lab}</summary><ul>${n.children.map(k => nodeH(k, d + 1)).join("")}</ul></details></li>` : `<li>${lab}</li>`; };
    const treeH = t => { const mid = t.up.filter(u => u !== t.owner);
      const up = mid.length ? `<p class="crumb">${icon("link")} Under ${t.owner ? orgLink(t.owner) + " › " : ""}${mid.slice().reverse().map(orgLink).join(" › ")}</p>`
        : !t.owner ? `<p class="crumb muted">${icon("flag")} ${!t.answerable || /^not established/.test(t.answerable) ? "The sources don't yet say who owns it or who it answers to." : "It answers to " + esc(t.answerable) + ", but no owning body is named in the sources."}</p>` : "";
      const gone = t.owner_open === false ? `<p class="muted" style="font-size:.85rem">${icon("clock")} ${esc(t.owner_name)} has closed${t.owner_successor.length ? "; its work moved to " + t.owner_successor.map(esc).join(", ") : ""}. The source still names it, so it is shown as written.</p>` : "";
      return `<article class="cptree" style="--c:var(--n${(natOf(t.id).length === 1 && natOf(t.id)[0]) || "GB"})">${up}${gone}<ul class="otree">${nodeH(t, 0)}</ul></article>`; };
    const match = (t, q, k) => { const walk = n => (!q || n.name.toLowerCase().includes(q)) && (!k || n.kind === k || n.also === k) || (n.children || []).some(walk); return walk(t); };
    const levels = Object.keys(LV).filter(l => C.groups[l]);
    $("#cpTabs").innerHTML = levels.map((l, i) => { const n = Object.values(C.groups[l]).flat().reduce((a, j) => a + C.trees[j].members, 0); return `<button class="tab" role="tab" id="cpt-${l}" aria-selected="${i === 0}" tabindex="${i ? -1 : 0}" data-lv="${l}">${l === "uk" ? nsw("UK") : l.length === 2 ? nsw(l) : ""}${esc(LV[l])} <span class="muted">${fmt(n)}</span></button>`; }).join("");
    let lv = levels[0];
    const draw = () => { const q = $("#cpQ").value.trim().toLowerCase(), k = $("#cpKind").value, by = $("#cpBy").value; let shown = 0;
      const html = Object.entries(C.groups[lv] || {}).map(([owner, idx]) => { const ts = idx.map(i => C.trees[i]).filter(t => match(t, q, k)); if (!ts.length) return ""; shown += ts.length;
        const mem = ts.reduce((a, t) => a + t.members, 0), oid = ts[0].owner;
        const inner = by && ts.length >= GROUP_MIN ? folders(ts, NEXT[by], xs => xs.map(treeH).join(""), "cpgrp", !!q) : ts.map(treeH).join("");
        return `<details class="cpown" ${q || idx.length <= 3 ? "open" : ""}><summary>${icon(lv === "local" ? "home" : lv === "other" ? "help" : "crown")}<b>${oid ? orgLink(oid) : esc(owner)}</b> <span class="muted">${fmt(ts.length)} ${ts.length === 1 ? "tree" : "trees"}, ${fmt(mem)} ${mem === 1 ? "body" : "bodies"}</span></summary>${inner}</details>`; }).join("");
      $("#cpOut").innerHTML = html || `<p class="muted">Nothing matches here. Try another tab or clear the search.</p>`;
      $("#cpOut").insertAdjacentHTML("afterbegin", `<p class="muted" style="margin:8px 0">${fmt(shown)} ${shown === 1 ? "tree" : "trees"} under ${esc(LV[lv])}.${lv === "other" ? " The sources name no owner for these yet: many are harbour trusts, which run themselves under their own Acts, or companies left from a rescue or a closed scheme." : ""}</p>`); applyTerms($("#cpOut")); };
    $("#cpTabs").addEventListener("click", e => { const b = e.target.closest("[data-lv]"); if (!b) return; lv = b.dataset.lv; $$("#cpTabs .tab").forEach(t => { t.setAttribute("aria-selected", t === b); t.tabIndex = t === b ? 0 : -1; }); draw(); });
    $("#cpTabs").addEventListener("keydown", e => { if (!["ArrowLeft", "ArrowRight"].includes(e.key)) return; const ts = $$("#cpTabs .tab"), i = ts.indexOf(document.activeElement); if (i < 0) return; const n = ts[(i + (e.key === "ArrowRight" ? 1 : ts.length - 1)) % ts.length]; n.focus(); n.click(); });
    ["cpQ", "cpKind", "cpBy"].forEach(i => $("#" + i).addEventListener("input", draw)); draw(); }
  // conflicts
  $("#confIntro").textContent = `${fmt(ACC.cf.length)} bodies where the sources still disagree about who it answers to, after each case was checked against the published order of sources (the law first, then the Public Bodies Directory, ONS and GOV.UK) and against how many sources agree. ${fmt(ACC.cfr)} other cases were settled that way and are not listed. If you know which is right, send a correction with a source.`;
  $("#confRows").innerHTML = ACC.cf.map(x => `<tr><td>${orgLink(x[0])}<div class="muted" style="font-size:.85rem">${esc(x[2] || "")}</div></td><td>${x[1].map(v => `${orgLink(v[0])} <span class="muted">(${v[1].map(s => esc(SRC(s).name.split(":")[0].split(",")[0])).join("; ")})</span>`).join("<br>")}</td></tr>`).join("");
  // gaps
  const gs = {}; ACC.un.forEach(u => gs[u[0]] = (gs[u[0]] || 0) + 1);
  $("#gapIntro").innerHTML = `${fmt(ACC.un.length)} names in the sources that didn't match exactly one register record. They are kept here, with the reason, rather than guessed. Many are classes of body (“NHS foundation trusts”) or bodies the register doesn't hold yet. Each is ${termHTML("unresolved")}.`;
  tbars($("#gapBars"), Object.entries(gs).sort((a, b) => b[1] - a[1]).map(([k, n]) => [SRC(k).name.split(":")[0].split(",")[0], n]));
  $("#gapSrc").innerHTML += Object.keys(gs).sort().map(k => `<option value="${esc(k)}">${esc(SRC(k).name.split(":")[0].split(",")[0])} (${gs[k]})</option>`).join("");
  const gRender = () => { const s = $("#gapSrc").value, q = $("#gapQ").value.toLowerCase(); $("#gapRows").innerHTML = ACC.un.filter(u => (!s || u[0] === s) && (!q || String(u[1]).toLowerCase().includes(q))).slice(0, 250).map(u => `<tr><td>${esc(SRC(u[0]).name.split(":")[0].split(",")[0])}</td><td>${esc(u[1])}</td><td>${esc(u[2])}</td><td>${esc(u[3])}</td></tr>`).join(""); };
  $("#gapSrc").addEventListener("change", gRender); $("#gapQ").addEventListener("input", gRender); gRender();
  // ledger
  const per = {}; ACCE.forEach(e => per[e.src] = (per[e.src] || 0) + 1);
  $("#ledgerRows").innerHTML = Object.entries(ACC.src).map(([k, s]) => `<tr><td><a href="${esc(s.url)}" rel="noopener" target="_blank">${esc(s.name)}</a></td><td>${esc(s.asserts)}</td><td>${esc(s.owner)}<br><span class="muted">${esc(s.licence)}</span></td><td class="mono">${esc(s.retrieved || "")}</td><td class="num">${fmt(per[k] || 0)}</td><td class="mono" title="${esc(s.sha256 || "")}">${esc((s.sha256 || "").slice(0, 16))}…</td></tr>`).join("");
  $("#digestLine").innerHTML = `Build ${esc(ACC.built)}. Fingerprint of the whole accountability layer: <span class="mono" style="overflow-wrap:anywhere">${esc(ACC.digest)}</span>.`;
  // SSOT
  $("#ssotRows").innerHTML = D.contract.consumers.map(x => `<tr><td><b>${esc(x.app)}</b>${x.note ? `<br><span class="muted">${esc(x.note)}</span>` : ""}</td><td>${esc(x.holds_now)}</td><td class="mono">${esc(x.reads)}</td><td><span class="pill ${/adopt|live/.test(x.status) ? "good" : "gold"}">${esc(x.status)}</span></td></tr>`).join("");
  applyTerms($("#v-tree"));
  Object.assign(COUNTS, {"s-tchain": ids.length, "s-tppp": ACC.ppp.length, "s-tconf": ACC.cf.length, "s-tgaps": ACC.un.length, "s-tledger": Object.keys(ACC.src).length, "s-tssot": D.contract.consumers.length, "s-ttf": ACC.corp.meta.counts.members});
}
["s-localgov","s-tintro","s-tchain","s-troots","s-tmoney","s-tppp","s-ttf","s-tconf","s-tgaps","s-tledger","s-tssot"].forEach(s => NEWSEC.add(s));
Object.assign(SECICON, {"s-localgov":"home","s-tintro":"crown","s-tchain":"link","s-troots":"tree","s-tmoney":"coin","s-tppp":"coin","s-ttf":"scale","s-tconf":"flag","s-tgaps":"list","s-tledger":"shield","s-tssot":"data"});
// downloads built from the same data, so they can't drift from what the page shows
const csvq = v => { const s = v == null ? "" : String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
const csv = rows => rows.map(r => r.map(csvq).join(",")).join("\n");
FILES["accountability.json"] = JSON.stringify(ACC);
FILES["edges.csv"] = csv([["child_id","child_name","parent_id","parent_name","parent_as_written","relation","source","source_ref","match_method"], ...ACCE.map(e => [e.c, BY[e.c] ? BY[e.c].name : "", e.p, BY[e.p] ? BY[e.p].name : "", e.pt, e.rel, e.src, e.ref, e.how])]);
FILES["accountable-owner.csv"] = csv([["id","name","accountable_owner_id","accountable_owner","answers_to","chain","sources_agreeing"], ...Object.keys(ACC.ch).map(k => { const c = CHAIN(k); return [k, BY[k] ? BY[k].name : "", c.root, BY[c.root] ? BY[c.root].name : "", c.ans, [BY[k] ? BY[k].name : k, ...c.path.map(e => (BY[e.p] ? BY[e.p].name : e.p) + " [" + e.rel + ":" + e.src + "]")].join(" > "), c.agree]; })]);
FILES["ppp.csv"] = csv([["hmt_project_id","project","status","sector","procuring_authority_id","procuring_authority","department_id","department","project_company","company_number","equity_holders","individuals_not_named","capital_gbp_m","unitary_charge_2025_26_gbp_m","contract_end","esa_balance_sheet"], ...ACC.ppp.map(p => [p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10].map(x => x[0] + (x[1] != null ? " " + x[1] : "")).join("; "), p[11], p[12], p[13], p[14], p[15]])]);
Object.assign(FDESC, {"accountability.json":["Who answers for each body: links, chains, money, PFI and the provenance ledger","JSON"],"edges.csv":["Every accountability, sponsorship and ownership link, with its source and match","CSV"],"accountable-owner.csv":["One row per open body: its accountable owner and the chain to it","CSV"],"ppp.csv":["PFI and PF2 contracts with authority, department, project company and investors","CSV"]});
const TREE_TERMS = [["Design token", "A named value, such as a colour or a type size, that every page uses instead of typing the value itself. Change the token and every page changes with it. See the design system page."], ["Strategic authority", TERMS["strategic authority"]], ["Local government reorganisation", TERMS["local government reorganisation"]], ["Unitary council", TERMS["unitary council"]], ["Shadow council", TERMS["shadow council"]], ["Vesting day", TERMS["vesting day"]], ["Supplementary vote", TERMS["supplementary vote"]], ["English Devolution Act", TERMS["English Devolution Act"]], ["Area of competence", TERMS["area of competence"]], ["Activity (what a body does)", "A second way of grouping bodies, beside purpose: whether a body runs a government, decides cases, sets rules, inspects, advises, gives out money, sells goods or services, looks after collections, keeps records, does research, promotes or runs public services. Worked out from its kind, name and description, so a few may be wrong."], ["Accountable owner", TERMS["accountable owner"]],["Estimate (Estimates and Accounts Order)", TERMS["estimate"]],["Sponsor", TERMS["sponsor"]],["Person with significant control", TERMS["person with significant control"]],["Trading fund", TERMS["trading fund"]],["Public corporation", TERMS["public corporation"]],["PFI and PF2", TERMS["PFI"]],["Unitary charge", TERMS["unitary charge"]],["Project company (SPV)", TERMS["project company"]],["Whole of Government Accounts", TERMS["Whole of Government Accounts"]],["SHA-256 fingerprint", TERMS["SHA-256"]],["Agreement", TERMS["agreement"]],["Unresolved name", TERMS["unresolved"]]];

// ---- LOCAL GOVERNMENT: English Devolution and Community Empowerment Act 2026, current and planned (tools/localgov.py) ----
const LG = ACC.lg, LGAREA = LG.council_area, LGSA = Object.fromEntries(LG.strategic_authorities.filter(s => s.id).map(s => [s.id, s]));
const lgSrc = ks => (ks || []).map((k, i, a) => { const s = LG.sources[k]; return s ? `<a href="${esc(s.url)}" rel="noopener" target="_blank" title="${esc(s.title)}">${esc((s.kind === "secondary" ? "summary" : "source") + (a.length > 1 ? " " + (i + 1) : ""))}<span class="sr-only"> (opens in a new tab): ${esc(s.title)}</span></a>` : ""; }).join(", ");
const lgDate = d => { if (!d) return ""; const [y, m, dd] = d.split("-"); const M = ["January","February","March","April","May","June","July","August","September","October","November","December"]; return dd ? `${+dd} ${M[m - 1]} ${y}` : m ? `${M[m - 1]} ${y}` : y; };
const LGTIER = Object.fromEntries(LG.act.tiers.map(t => [t.key, t]));
function localGov(){
  const c = LG.meta.counts, A = LG.reorganisation.areas, ST = LG.reorganisation.statuses;
  $("#lgLede").innerHTML = `The ${termHTML("English Devolution Act", "English Devolution and Community Empowerment Act 2026")} became law on ${esc(lgDate(LG.act.royal_assent.value))} (${lgSrc(LG.act.royal_assent.src)}). It groups councils into ${termHTML("strategic authority", "strategic authorities")} with set powers, and it sits alongside ${termHTML("local government reorganisation")}, which replaces county and district councils with single ${termHTML("unitary council", "unitary councils")}. Checked against the government's own announcements on ${esc(lgDate(LG.meta.as_of))}.`;
  $("#lgStats").innerHTML = [[c.sa_current, "strategic authorities now"], [c.sa_planned, "more planned"], [c.areas, "areas being reorganised"], [c.councils_in_areas, "councils in those areas"], [c.by_status["minded-to"] || 0, "areas with a 'minded to' decision"]].map((x, i) => `<div class="stat ${["sea","gold","navy","red","sea"][i]}"><b data-n="${x[0]}">0</b><span>${esc(x[1])}</span></div>`).join(""); $$("#lgStats b").forEach(b => countUp(b, +b.dataset.n));
  // strategic authorities, by tier
  const tierCol = t => { const xs = LG.strategic_authorities.filter(s => s.tier === t.key).sort((a, b) => (a.status > b.status) - (a.status < b.status) || a.name.localeCompare(b.name));
    return `<section class="lgtier" aria-labelledby="lgt-${t.key}"><h3 id="lgt-${t.key}">${esc(t.label)} <span class="muted">· ${fmt(xs.length)}</span></h3><p class="muted">${esc(t.plain)}</p><p class="law">${icon("scale")} ${esc(t.law)} ${lgSrc(t.src)}</p>
      <ul class="lglist">${xs.map(s => `<li><span class="lgst ${s.status}">${s.status === "current" ? "Now" : "Planned"}</span> ${s.id ? orgLink(s.id) : `<b>${esc(s.name)}</b>`}${s.first_mayor ? ` <span class="muted">· first mayoral election ${esc(lgDate(s.first_mayor))}</span>` : ""}${s.note ? `<div class="muted" style="font-size:.85rem">${esc(s.note)}</div>` : ""}<div class="src">${lgSrc(s.src)}</div></li>`).join("") || `<li class="muted">${t.key === "mayoral-established" ? "Which authorities have been designated as established isn't confirmed in the sources read, so none is listed yet." : "None designated yet in the sources read."}</li>`}</ul></section>`; };
  const P1 = `<p class="muted" style="margin:8px 0">Under section 1 of the Act every combined authority, combined county authority and the Greater London Authority is a strategic authority. The tier decides its powers in nine ${termHTML("area of competence", "areas of competence")}. Ten of these authorities aren't in the register yet, so they are listed here by name until the next register update.</p><div class="lgtiers">${LG.act.tiers.map(tierCol).join("")}</div>`;
  // reorganisation, by status
  const areaCard = a => { const n = a.councils.length; return `<article class="lgarea st-${a.status}"><h4>${esc(a.area)} <span class="lgst ${a.status}">${esc(ST[a.status].label)}</span></h4>
      <dl class="lgdl">${a.new_councils ? `<dt>New councils</dt><dd>${fmt(a.new_councils)}${a.new_names ? ": " + a.new_names.map(esc).join(" and ") : ""}</dd>` : `<dt>New councils</dt><dd class="muted">Not decided</dd>`}
      ${a.why ? `<dt>Why</dt><dd>${esc(a.why)}</dd>` : ""}${a.existing_elections ? `<dt>Next vote for today's councils</dt><dd>${esc(lgDate(a.existing_elections))}</dd>` : ""}
      <dt>Vote for the new councils</dt><dd>${esc(lgDate(a.shadow_election))}</dd><dt>New councils take over</dt><dd>${esc(lgDate(a.vesting))}${a.status !== "decided" ? " (planned)" : ""}</dd></dl>
      <details><summary>The ${fmt(n)} councils being replaced</summary><ul class="lgcouncils">${a.councils.map(id => `<li>${orgLink(id)}</li>`).join("")}</ul></details><div class="src">${lgSrc(a.src)}</div></article>`; };
  const P2 = `<p class="muted" style="margin:8px 0">${esc(LG.reorganisation.summary.value)} ${lgSrc(LG.reorganisation.summary.src)} ${esc(LG.reorganisation.postponed_2026.value)} ${lgSrc(LG.reorganisation.postponed_2026.src)}</p>
    <p class="muted" style="font-size:.85rem">Each area's councils come from the ONS list of which district councils sit in which county, plus the neighbouring councils the area's own name includes. Every council named also shows this on its profile.</p>
    ${Object.entries(ST).map(([k, s]) => { const xs = A.filter(a => a.status === k); return xs.length ? `<h3 class="lgh">${esc(s.label)} <span class="muted">· ${fmt(xs.length)} ${xs.length === 1 ? "area" : "areas"}</span></h3><p class="muted">${esc(s.plain)}</p><div class="lgareas">${xs.map(areaCard).join("")}</div>` : ""; }).join("")}`;
  // what the Act changes
  const P3 = `<h3 class="lgh">What a strategic authority can work on ${lgSrc(LG.act.competences.src)}</h3><ul class="lgchips">${LG.act.competences.value.map(v => `<li>${esc(v)}</li>`).join("")}</ul>
    <h3 class="lgh">What else changes</h3><ul class="lgchanges">${LG.act.changes.map(x => `<li>${esc(x.now)} <span class="src">${lgSrc(x.src)}</span></li>`).join("")}</ul>`;
  // timeline
  const P4 = `<ol class="lgtl">${LG.timeline.map(t => `<li class="${t.when}"><span class="d">${esc(lgDate(t.date))}</span><span class="w">${esc(t.what)}${t.when === "planned" ? ' <span class="lgst planned">Planned</span>' : ""}</span><span class="src">${lgSrc(t.src)}</span></li>`).join("")}</ol>`;
  const T = [["Strategic authorities", P1], ["Councils being reorganised", P2], ["What the Act changes", P3], ["Timeline", P4]];
  $("#lgTabs").innerHTML = T.map((t, i) => `<button class="tab" role="tab" id="lgtab-${i}" aria-controls="lgp-${i}" aria-selected="${i === 0}" tabindex="${i ? -1 : 0}">${esc(t[0])}</button>`).join("");
  $("#lgPanels").innerHTML = T.map((t, i) => `<div class="tabpanel" role="tabpanel" id="lgp-${i}" aria-labelledby="lgtab-${i}" ${i ? "hidden" : ""}>${t[1]}</div>`).join(""); tabs($("#lgTabs"));
  $("#lgFoot").textContent = `Sources: ${Object.values(LG.sources).filter(s => s.kind === "primary").length} primary (legislation.gov.uk, Parliament, GOV.UK, councils, ONS) and ${Object.values(LG.sources).filter(s => s.kind === "secondary").length} secondary, marked “summary”. Decisions marked planned or minded to may still change: the government says every area will have an outcome by early 2027.`;
  applyTerms($("#s-localgov"));
}

function treeSelfChecks(){
  const res = [];
  res.push(["Every open record has an accountability chain", OPEN.every(r => ACC.ch[r.id])]);
  res.push(["Every link names its source and where in it", ACCE.every(e => ACC.src[e.src] && e.ref)]);
  res.push(["No personal name in the accountability data", !ACCE.some(e => /^(mr|mrs|ms|miss|dr|dame|sir)\s/i.test(e.pt) && !/limited|ltd|plc|llp/i.test(e.pt))]);
  res.push(["The former office name appears nowhere", !document.body.innerText.includes(["Office of the", "Chief Data", "Officer"].join(" "))]);
  { const seen = {}; (function w(ns){ ns.forEach(n => { if (n.member) seen[n.id] = (seen[n.id] || 0) + 1; if (n.children) w(n.children); }); })(ACC.corp.trees);
    res.push(["Every trading fund and public corporation sits in exactly one family tree", Object.values(seen).every(v => v === 1) && Object.keys(seen).length === ACC.corp.meta.counts.members]); }
  res.push(["Every local government fact names its source", [...LG.reorganisation.areas, ...LG.strategic_authorities, ...LG.timeline].every(x => (x.src || []).length && x.src.every(k => LG.sources[k]))]);
  res.push(["All 21 reorganisation areas are shown", $$("#s-localgov .lgarea").length === LG.reorganisation.areas.length && LG.reorganisation.areas.length === 21]);
  res.push(["Every chain ends at the root it states", Object.keys(ACC.ch).every(k => { const c = CHAIN(k); return (c.path.length ? c.path[c.path.length - 1].p : k) === c.root; })]);
  $("#selfChecks").insertAdjacentHTML("beforeend", res.map(([n, ok]) => `<li>${ok ? '<span class="pill good">Pass</span>' : '<span class="pill bad">Fail</span>'} ${esc(n)}</li>`).join(""));
  window.__selfchecks = (window.__selfchecks || []).concat(res);
}
