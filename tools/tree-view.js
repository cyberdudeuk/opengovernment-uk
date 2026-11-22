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
function chainHTML(id){
  const r = BY[id], c = CHAIN(id); if (!r || !c) return `<p class="muted">No accountability data for this record.</p>`;
  const steps = [`<div class="step start"><span class="dot">${icon("tree")}</span><div><b>${orgLink(id)}</b><span class="rel">${esc(r.fam)} · ${esc(r.kind)}</span></div></div>`];
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
function treeOf(rootId){
  // corporate-tree view: bodies whose chain passes through each body, built from the chains themselves
  const kids = {}; Object.keys(ACC.ch).forEach(k => { const p = ACC.ch[k][0].map(i => ACCE[i]); let child = k; p.forEach(e => { (kids[e.p] = kids[e.p] || new Map()).set(child, e.rel); child = e.p; }); });
  const size = {}; const count = (id, seen = new Set()) => { if (size[id] != null) return size[id]; if (seen.has(id)) return 0; seen.add(id); let n = 0; (kids[id] || new Map()).forEach((_, c) => n += 1 + count(c, seen)); return size[id] = n; };
  const node = (id, rel, depth) => { const ks = [...(kids[id] || new Map()).entries()].sort((a, b) => count(b[0]) - count(a[0]) || (BY[a[0]] ? BY[a[0]].name : "").localeCompare(BY[b[0]] ? BY[b[0]].name : "")); const lab = `${orgLink(id)}${rel ? `<span class="rl">${esc(rel)}</span>` : ""}${ks.length ? `<span class="c">${fmt(count(id))}</span>` : ""}`; if (!ks.length || depth > 4) return `<li>${lab}</li>`; return `<li><details ${depth < 1 ? "open" : ""}><summary>${lab}</summary><ul>${ks.slice(0, 250).map(([c, r]) => node(c, r, depth + 1)).join("")}${ks.length > 250 ? `<li class="muted">and ${fmt(ks.length - 250)} more</li>` : ""}</ul></details></li>`; };
  return {html: `<ul class="otree">${node(rootId, "", 0)}</ul>`, kids, count};
}
function whoAnswers(){
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
   <li><b>Disagreement is shown, not hidden.</b> ${fmt(ACC.cf.length)} bodies have sources naming different parents, often because of a recent machinery-of-government change or joint sponsorship.</li>
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
              ["Ultimate owners", `<p class="muted" style="margin:8px 0">The bodies that sit at the top of the most chains: the public-sector equivalent of a group parent.</p><div class="bars" id="ownBars"></div>`],
              ["Tree", `<div class="controls" style="margin-top:8px"><label>Start from<select id="treeRoot">${depts.map(d => `<option value="${esc(d.id)}">${esc(d.name)} (${fmt(byRoot[d.id] || 0)})</option>`).join("")}</select></label></div><p class="muted">Every body whose chain passes through it, nested by the link that joins them. The number is how many bodies sit below.</p><div id="treeOut"></div>`]];
  $("#rootTabs").innerHTML = RT.map((t, i) => `<button class="tab" role="tab" id="rt-${i}" aria-controls="rp-${i}" aria-selected="${i === 0}" tabindex="${i ? -1 : 0}">${esc(t[0])}</button>`).join("");
  $("#rootPanels").innerHTML = RT.map((t, i) => `<div class="tabpanel" role="tabpanel" id="rp-${i}" aria-labelledby="rt-${i}" ${i ? "hidden" : ""}>${t[1]}</div>`).join(""); tabs($("#rootTabs"));
  tbars($("#ansBars"), Object.entries(byAns).sort((a, b) => b[1] - a[1]).map(([a, n]) => [a, n]));
  tbars($("#ownBars"), Object.entries(byRoot).sort((a, b) => b[1] - a[1]).slice(0, 20).map(([k, n]) => [BY[k] ? BY[k].name : k, n, k]));
  const drawTree = () => { $("#treeOut").innerHTML = treeOf($("#treeRoot").value).html; }; $("#treeRoot").addEventListener("change", drawTree); if (depts.length) drawTree();
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
  // trading funds and public corporations
  $("#tfIntro").textContent = `${ACC.tf.length} open bodies identified from trading fund orders on legislation.gov.uk and the ONS guide's notes.`;
  $("#tfList").innerHTML = ACC.tf.map(id => { const c = CHAIN(id); return `<li>${orgLink(id)}${c && c.path[0] ? ` <span class="muted">answers via ${esc(BY[c.path[0].p] ? BY[c.path[0].p].name : "")}</span>` : ""}</li>`; }).join("");
  const pcs = Object.keys(ACC.pcs).filter(k => BY[k]).sort((a, b) => BY[a].name.localeCompare(BY[b].name));
  $("#pcIntro").textContent = `${fmt(pcs.length)} open bodies classified by ONS as public non-financial or financial corporations, or the central bank.`;
  const pcRender = () => { const q = $("#pcQ").value.toLowerCase(); const rs = pcs.filter(k => !q || BY[k].name.toLowerCase().includes(q)); $("#pcList").innerHTML = rs.slice(0, 80).map(k => { const c = CHAIN(k); return `<li>${orgLink(k)} <span class="muted">${c && c.path.length ? "→ " + esc(BY[c.root] ? BY[c.root].name : "") : ""}</span></li>`; }).join("") + (rs.length > 80 ? `<li class="muted">and ${fmt(rs.length - 80)} more: refine the search</li>` : ""); };
  $("#pcQ").addEventListener("input", pcRender); pcRender();
  // conflicts
  $("#confIntro").textContent = `${fmt(ACC.cf.length)} bodies where sources name different bodies as the one it answers to. Most are recent machinery-of-government changes the slower sources haven't caught up with, or bodies sponsored jointly by more than one government.`;
  $("#confRows").innerHTML = ACC.cf.map(x => `<tr><td>${orgLink(x[0])}</td><td>${x[1].map(v => `${orgLink(v[0])} <span class="muted">(${v[1].map(s => esc(SRC(s).name.split(":")[0].split(",")[0])).join("; ")})</span>`).join("<br>")}</td></tr>`).join("");
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
  Object.assign(COUNTS, {"s-tchain": ids.length, "s-tppp": ACC.ppp.length, "s-tconf": ACC.cf.length, "s-tgaps": ACC.un.length, "s-tledger": Object.keys(ACC.src).length, "s-tssot": D.contract.consumers.length, "s-ttf": ACC.tf.length + pcs.length});
}
["s-tintro","s-tchain","s-troots","s-tmoney","s-tppp","s-ttf","s-tconf","s-tgaps","s-tledger","s-tssot"].forEach(s => NEWSEC.add(s));
Object.assign(SECICON, {"s-tintro":"crown","s-tchain":"link","s-troots":"tree","s-tmoney":"coin","s-tppp":"coin","s-ttf":"scale","s-tconf":"flag","s-tgaps":"list","s-tledger":"shield","s-tssot":"data"});
// downloads built from the same data, so they can't drift from what the page shows
const csvq = v => { const s = v == null ? "" : String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
const csv = rows => rows.map(r => r.map(csvq).join(",")).join("\n");
FILES["accountability.json"] = JSON.stringify(ACC);
FILES["edges.csv"] = csv([["child_id","child_name","parent_id","parent_name","parent_as_written","relation","source","source_ref","match_method"], ...ACCE.map(e => [e.c, BY[e.c] ? BY[e.c].name : "", e.p, BY[e.p] ? BY[e.p].name : "", e.pt, e.rel, e.src, e.ref, e.how])]);
FILES["accountable-owner.csv"] = csv([["id","name","accountable_owner_id","accountable_owner","answers_to","chain","sources_agreeing"], ...Object.keys(ACC.ch).map(k => { const c = CHAIN(k); return [k, BY[k] ? BY[k].name : "", c.root, BY[c.root] ? BY[c.root].name : "", c.ans, [BY[k] ? BY[k].name : k, ...c.path.map(e => (BY[e.p] ? BY[e.p].name : e.p) + " [" + e.rel + ":" + e.src + "]")].join(" > "), c.agree]; })]);
FILES["ppp.csv"] = csv([["hmt_project_id","project","status","sector","procuring_authority_id","procuring_authority","department_id","department","project_company","company_number","equity_holders","individuals_not_named","capital_gbp_m","unitary_charge_2025_26_gbp_m","contract_end","esa_balance_sheet"], ...ACC.ppp.map(p => [p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10].map(x => x[0] + (x[1] != null ? " " + x[1] : "")).join("; "), p[11], p[12], p[13], p[14], p[15]])]);
Object.assign(FDESC, {"accountability.json":["Who answers for each body: links, chains, money, PFI and the provenance ledger","JSON"],"edges.csv":["Every accountability, sponsorship and ownership link, with its source and match","CSV"],"accountable-owner.csv":["One row per open body: its accountable owner and the chain to it","CSV"],"ppp.csv":["PFI and PF2 contracts with authority, department, project company and investors","CSV"]});
const TREE_TERMS = [["Accountable owner", TERMS["accountable owner"]],["Estimate (Estimates and Accounts Order)", TERMS["estimate"]],["Sponsor", TERMS["sponsor"]],["Person with significant control", TERMS["person with significant control"]],["Trading fund", TERMS["trading fund"]],["Public corporation", TERMS["public corporation"]],["PFI and PF2", TERMS["PFI"]],["Unitary charge", TERMS["unitary charge"]],["Project company (SPV)", TERMS["project company"]],["Whole of Government Accounts", TERMS["Whole of Government Accounts"]],["SHA-256 fingerprint", TERMS["SHA-256"]],["Agreement", TERMS["agreement"]],["Unresolved name", TERMS["unresolved"]]];
function treeSelfChecks(){
  const res = [];
  res.push(["Every open record has an accountability chain", OPEN.every(r => ACC.ch[r.id])]);
  res.push(["Every link names its source and where in it", ACCE.every(e => ACC.src[e.src] && e.ref)]);
  res.push(["No personal name in the accountability data", !ACCE.some(e => /^(mr|mrs|ms|miss|dr|dame|sir)\s/i.test(e.pt) && !/limited|ltd|plc|llp/i.test(e.pt))]);
  res.push(["The former office name appears nowhere", !document.body.innerText.includes(["Office of the", "Chief Data", "Officer"].join(" "))]);
  res.push(["Every chain ends at the root it states", Object.keys(ACC.ch).every(k => { const c = CHAIN(k); return (c.path.length ? c.path[c.path.length - 1].p : k) === c.root; })]);
  $("#selfChecks").insertAdjacentHTML("beforeend", res.map(([n, ok]) => `<li>${ok ? '<span class="pill good">Pass</span>' : '<span class="pill bad">Fail</span>'} ${esc(n)}</li>`).join(""));
  window.__selfchecks = (window.__selfchecks || []).concat(res);
}
