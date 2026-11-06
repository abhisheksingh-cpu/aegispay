"""Dashboard: a single HTML file with hash-routed pages. Data comes from the existing API."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AegisPay</title>
<style>
:root{--bg:#f5f6f8;--card:#fff;--fg:#14171f;--mut:#667085;--line:#e4e7ec;--brand:#4f46e5;
--ok:#12805c;--okbg:#e3f6ee;--bad:#c0262d;--badbg:#fdeaea;--warn:#a15c00;--warnbg:#fff3df;--info:#175cd3;--infobg:#e6f0ff;--mutbg:#eef0f3}
@media (prefers-color-scheme:dark){:root{--bg:#0e1116;--card:#171b22;--fg:#e8eaee;--mut:#98a2b3;--line:#2a303a;--brand:#8b85ff;
--ok:#4cc38a;--okbg:#12352a;--bad:#ff7a80;--badbg:#3a1a1c;--warn:#f5b45a;--warnbg:#3a2a10;--info:#7aa7ff;--infobg:#14284a;--mutbg:#232932}}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--fg)}
header{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line)}
.bar{max-width:1040px;margin:0 auto;padding:12px 20px;display:flex;align-items:center;gap:24px;flex-wrap:wrap}
.brand{font-weight:700;font-size:18px;color:var(--brand);text-decoration:none}.brand small{color:var(--mut);font-weight:500;margin-left:8px}
nav{display:flex;gap:6px;margin-left:auto}nav a{padding:6px 12px;border-radius:8px;color:var(--mut);text-decoration:none;font-weight:600}
nav a:hover{background:var(--mutbg)}nav a.on{background:var(--brand);color:#fff}
main{max-width:1040px;margin:0 auto;padding:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:0 0 16px}
h1{font-size:22px;margin:0 0 4px}h3{font-size:15px;margin:0 0 10px}.mut{color:var(--mut)}.small{font-size:13px}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.between{justify-content:space-between}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:0 0 16px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.kpi .v{font-size:26px;font-weight:700;margin:2px 0}.kpi .l{color:var(--mut);font-size:13px}
.badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:700;letter-spacing:.2px}
.b-ok{background:var(--okbg);color:var(--ok)}.b-bad{background:var(--badbg);color:var(--bad)}.b-warn{background:var(--warnbg);color:var(--warn)}
.b-info{background:var(--infobg);color:var(--info)}.b-mut{background:var(--mutbg);color:var(--mut)}
.big .badge{font-size:15px;padding:4px 14px}
.btn{font:inherit;font-weight:600;border-radius:9px;padding:7px 14px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
.btn:disabled{opacity:.5;cursor:wait}.btn-primary{background:var(--brand);color:#fff;border-color:var(--brand)}
.btn-bad{color:var(--bad)}.btn-ok{color:var(--ok)}.btn-warn{color:var(--warn)}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
th{color:var(--mut);font-weight:600;font-size:13px}tr:last-child td{border-bottom:0}
a{color:var(--brand)}.feedrow{display:flex;gap:12px;align-items:center;padding:6px 0;border-bottom:1px solid var(--line);font-size:14px}
.feedrow:last-child{border-bottom:0}.dot{width:10px;height:10px;border-radius:50%;flex:none}.dot.ok{background:var(--ok)}.dot.bad{background:var(--bad)}
.badtxt{color:var(--bad);font-weight:600}
.steps{display:flex;gap:0;margin:6px 0 2px;flex-wrap:wrap}.step{flex:1;min-width:120px;text-align:center;position:relative;padding-top:2px}
.step .c{width:30px;height:30px;border-radius:50%;margin:0 auto 6px;display:flex;align-items:center;justify-content:center;font-weight:700;background:var(--mutbg);color:var(--mut)}
.step.done .c{background:var(--ok);color:#fff}.step.now .c{background:var(--brand);color:#fff}.step .t{font-size:13px;font-weight:600}.step.done .t{color:var(--ok)}
.item{padding:6px 12px;border-left:3px solid var(--brand);margin:6px 0;background:var(--mutbg);border-radius:0 8px 8px 0}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 10px}.flow{display:flex;gap:8px;align-items:stretch;flex-wrap:wrap}
.flow .n{flex:1;min-width:130px;background:var(--mutbg);border-radius:10px;padding:10px;font-size:13px}.flow .n b{display:block;margin-bottom:2px}
.flow .ar{align-self:center;color:var(--mut)}ul.clean{padding-left:18px;margin:6px 0}
</style></head><body>
<header><div class="bar">
<a class="brand" href="#/">AegisPay<small>payment reliability and SLA compensation</small></a>
<nav id="nav"><a href="#/" data-r="">Overview</a><a href="#/incidents" data-r="incidents">Incidents</a><a href="#/how" data-r="how">How it works</a></nav>
</div></header>
<main id="app"></main>
<script>
const app = document.getElementById('app');
let current = null, timer = null;

// All values are added as text nodes, never innerHTML: evidence text is untrusted.
function h(tag, props, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) e.setAttribute(k, v);
  kids.flat().forEach(k => { if (k !== null && k !== undefined && k !== false) e.append(k instanceof Node ? k : document.createTextNode(String(k))); });
  return e;
}
const badge = (text, kind) => h('span', {class: 'badge b-' + (kind || 'mut')}, text);
const SEV = {low: 'mut', medium: 'warn', high: 'warn', critical: 'bad'};
const STAT = {open: 'bad', investigating: 'warn', identified: 'warn', remediating: 'warn', resolved: 'ok'};
const SVC = {healthy: 'ok', degraded: 'warn', down: 'bad'};
const money = v => '$' + Number(v).toFixed(2);
function fmt(ts) { const d = new Date(ts); return isNaN(d) ? String(ts) : d.toLocaleTimeString(); }
function table(headers, rows) {
  const t = h('table'); t.append(h('tr', {}, headers.map(x => h('th', {}, x))));
  rows.forEach(r => t.append(h('tr', {}, r.map(c => h('td', {}, c))))); return t;
}
function setSlot(slot, sig, build) { sig = String(sig); if (slot.dataset.sig === sig) return; slot.dataset.sig = sig; slot.replaceChildren(build()); }
function btn(label, kind, fn) {
  const b = h('button', {class: 'btn btn-' + kind}, label);
  b.addEventListener('click', async () => { b.disabled = true; try { await fn(); } finally { b.disabled = false; } });
  return b;
}
async function api(url, opts) {
  try { const r = await fetch(url, opts); let body = null; try { body = await r.json(); } catch (e) {} return {ok: r.ok, status: r.status, body}; }
  catch (e) { return {ok: false, status: 0, body: null}; }
}
const get = async u => { const r = await api(u); return r.ok ? r.body : null; };
const post = (u, body) => api(u, {method: 'POST', headers: {'content-type': 'application/json'}, body: body ? JSON.stringify(body) : undefined});

/* ---------- Overview ---------- */
function overviewPage() {
  const s = {status: h('div'), kpis: h('div', {class: 'grid'}), feed: h('div'), latest: h('div')};
  const setFault = async mode => { await post('/demo/fault', {mode}); await page.refresh(); };
  const node = h('div', {},
    h('div', {class: 'card'}, h('h3', {}, 'Payment service'), s.status,
      h('div', {class: 'row', style: 'margin-top:10px'}, btn('Break service', 'bad', () => setFault('down')), btn('Slow service', 'warn', () => setFault('slow')), btn('Recover', 'ok', () => setFault('none'))),
      h('p', {class: 'mut small'}, 'Demo controls switch the simulated payment service. Customer traffic comes from the watcher: python watcher.py')),
    s.kpis,
    h('div', {class: 'card'}, h('h3', {}, 'Live payment attempts'), s.feed),
    h('div', {class: 'card'}, h('h3', {}, 'Latest incident'), s.latest));
  const page = {node, every: 2000, async refresh() {
    const [ov, fault, incidents] = await Promise.all([get('/overview'), get('/demo/fault'), get('/incidents')]);
    if (!ov) { setSlot(s.status, 'err', () => h('p', {}, 'Cannot reach the API.')); return; }
    const svc = ov.service.status, k = ov.kpis, mode = fault ? fault.mode : 'unknown';
    setSlot(s.status, svc + mode, () => h('div', {class: 'row between'},
      h('div', {class: 'big'}, badge(svc.toUpperCase(), SVC[svc] || 'mut')), h('div', {class: 'mut small'}, 'Fault switch: ' + mode)));
    setSlot(s.kpis, JSON.stringify(k), () => h('div', {class: 'grid', style: 'grid-column:1/-1;margin:0'},
      [['Incidents', k.incidents_total, k.incidents_open + ' open'],
       ['Payment attempts', k.attempts_total, k.attempts_failed + ' failed'],
       ['Real PayPal refunds', money(k.refunds_real_usd), k.refunds_real_count + ' sandbox refund(s)'],
       ['Mock refunds (test only)', money(k.refunds_mock_usd), k.refunds_mock_count + ' mock refund(s)']]
      .map(([l, v, sub]) => h('div', {class: 'kpi'}, h('div', {class: 'l'}, l), h('div', {class: 'v'}, v), h('div', {class: 'mut small'}, sub)))));
    const rec = ov.service.recent.slice(0, 12);
    setSlot(s.feed, rec.map(a => a.id).join(), () => rec.length ? h('div', {}, rec.map(a => h('div', {class: 'feedrow'},
      h('span', {class: 'dot ' + (a.ok ? 'ok' : 'bad')}), h('span', {class: 'mut small'}, fmt(a.at)), h('span', {}, a.customer_id),
      h('span', {class: a.ok ? 'mut' : 'badtxt'}, a.ok ? 'ok, ' + a.latency_ms + ' ms' : 'FAILED ' + (a.error || '')),
      a.incident_id ? h('a', {href: '#/incident/' + a.incident_id, class: 'small'}, 'incident #' + a.incident_id) : ''))) :
      h('p', {class: 'mut'}, 'No traffic yet. In a terminal, run: python watcher.py'));
    const last = (incidents || []).slice(-1)[0];
    setSlot(s.latest, last ? last.id + last.status + last.severity : 'none', () => last ?
      h('div', {class: 'row between'}, h('div', {}, h('b', {}, 'Incident #' + last.id + '  '), badge(last.status, STAT[last.status]), ' ', badge(last.severity, SEV[last.severity]),
        h('div', {class: 'mut small'}, last.reason)), h('a', {href: '#/incident/' + last.id}, 'Open details')) :
      h('p', {class: 'mut'}, 'No incidents yet. Click "Break service" while the watcher is running.'));
  }};
  return page;
}

/* ---------- Incident list ---------- */
function incidentsPage() {
  const slot = h('div');
  return {node: h('div', {}, h('h1', {}, 'Incidents'), h('p', {class: 'mut'}, 'Every incident detected from real customer attempts.'), h('div', {class: 'card'}, slot)), every: 3000, async refresh() {
    const list = ((await get('/incidents')) || []).slice().reverse();
    setSlot(slot, JSON.stringify(list), () => list.length ? table(['#', 'Service', 'Status', 'Severity', 'Reason', ''],
      list.map(i => [i.id, i.service, badge(i.status, STAT[i.status]), badge(i.severity, SEV[i.severity]), i.reason, h('a', {href: '#/incident/' + i.id}, 'View')])) :
      h('p', {class: 'mut'}, 'No incidents yet.'));
  }};
}

/* ---------- Incident detail ---------- */
function incidentPage(id) {
  const s = {head: h('div'), steps: h('div'), time: h('div'), ev: h('div'), diag: h('div'), comp: h('div')};
  const msgD = h('p', {class: 'mut small'}), msgC = h('p', {class: 'mut small'});
  let state = {};
  async function explain() { msgD.textContent = 'Asking the model...'; const r = await post('/incidents/' + id + '/diagnosis'); msgD.textContent = r.ok ? 'Done.' : 'Failed to create a diagnosis.'; await page.refresh(); }
  async function approve() {
    if (!window.confirm('Approve compensation for incident #' + id + '? Refunds will be issued: real PayPal sandbox refunds for real payments, mock refunds for test payments.')) return;
    msgC.textContent = 'Calculating compensation...';
    const c = await post('/incidents/' + id + '/compensations');
    if (!c.ok) { msgC.textContent = 'Cannot compensate: ' + ((c.body && c.body.detail) || 'error'); return; }
    const list = (await get('/incidents/' + id + '/compensations')) || [];
    let done = 0;
    for (const comp of list.filter(x => x.status === 'eligible')) { msgC.textContent = 'Issuing refund ' + (done + 1) + '...'; await post('/compensations/' + comp.id + '/refund'); done++; }
    msgC.textContent = done + ' refund(s) processed.'; await page.refresh();
  }
  const node = h('div', {}, s.head, h('div', {class: 'card'}, h('h3', {}, 'Progress'), s.steps),
    h('div', {class: 'card'}, h('h3', {}, 'Timeline'), s.time),
    h('div', {class: 'card'}, h('h3', {}, 'Evidence: failed payment attempts'), s.ev),
    h('div', {class: 'card'}, h('h3', {}, 'AI diagnosis'), s.diag, h('div', {class: 'row', style: 'margin-top:10px'}, btn('Run AI explanation', 'primary', explain)), msgD),
    h('div', {class: 'card'}, h('h3', {}, 'Compensation and refunds'), s.comp, h('div', {class: 'row', style: 'margin-top:10px'}, btn('Approve and refund', 'primary', approve)), msgC));
  const page = {node, every: 3000, async refresh() {
    const [inc, hist, ev, diag, comps, payouts, payments] = await Promise.all([get('/incidents/' + id), get('/incidents/' + id + '/history'), get('/incidents/' + id + '/evidence'),
      get('/incidents/' + id + '/diagnosis'), get('/incidents/' + id + '/compensations'), get('/payouts'), get('/payments')]);
    if (!inc) { setSlot(s.head, 'nf', () => h('div', {class: 'card'}, 'Incident not found. ', h('a', {href: '#/incidents'}, 'Back to incidents'))); return; }
    setSlot(s.head, JSON.stringify(inc), () => h('div', {class: 'card'}, h('div', {class: 'row'}, h('h1', {style: 'margin:0'}, 'Incident #' + inc.id), badge(inc.status, STAT[inc.status]), badge(inc.severity + ' severity', SEV[inc.severity])),
      h('div', {class: 'mut'}, inc.service + ': ' + inc.reason), h('p', {class: 'small'}, h('a', {href: '#/incidents'}, 'All incidents'))));
    const mine = new Set((comps || []).map(c => c.id)), pays = (payouts || []).filter(p => mine.has(p.compensation_id));
    const flags = [true, inc.status === 'resolved', !!diag, (comps || []).length > 0, pays.some(p => p.status === 'completed')];
    const names = ['Detected', 'Recovery verified', 'Diagnosed', 'Compensation calculated', 'Refunds issued'];
    const firstOpen = flags.indexOf(false);
    setSlot(s.steps, flags.join(), () => h('div', {class: 'steps'}, names.map((n, i) => h('div', {class: 'step ' + (flags[i] ? 'done' : i === firstOpen ? 'now' : '')}, h('div', {class: 'c'}, flags[i] ? '\u2713' : i + 1), h('div', {class: 't'}, n)))));
    setSlot(s.time, JSON.stringify(hist), () => h('div', {}, (hist || []).map(x => h('div', {class: 'item'}, fmt(x.changed_at) + '   status: ' + x.status))));
    const evl = ev || [], by = {}; evl.forEach(e => { by[e.customer_id] = (by[e.customer_id] || 0) + 1; });
    setSlot(s.ev, evl.length + ':' + (evl.length ? evl[evl.length - 1].attempt_id : 0), () => h('div', {},
      h('div', {class: 'chips'}, Object.entries(by).map(([c, n]) => badge(c + ': ' + n + ' failed', 'bad')), evl.length ? '' : h('span', {class: 'mut'}, 'No failed attempts recorded.')),
      evl.length ? table(['Attempt', 'Customer', 'Error', 'Latency'], evl.slice(0, 8).map(e => [e.attempt_id, e.customer_id, e.error, e.latency_ms + ' ms'])) : '',
      evl.length > 8 ? h('p', {class: 'mut small'}, '... and ' + (evl.length - 8) + ' more') : ''));
    setSlot(s.diag, JSON.stringify(diag), () => !diag ? h('p', {class: 'mut'}, 'No diagnosis yet.') : h('div', {},
      h('div', {class: 'chips'}, badge(diag.source === 'llm' ? 'AI: ' + diag.model : diag.source === 'rules_fallback' ? 'Rule-based (AI unavailable or rejected)' : 'Rule-based', diag.source === 'llm' ? 'info' : 'mut'),
        badge('cause: ' + diag.cause, 'warn'), badge('confidence: ' + diag.confidence, diag.confidence === 'high' ? 'ok' : 'mut'),
        diag.note && diag.note.indexOf('disagrees') >= 0 ? badge('needs human review', 'bad') : ''),
      h('p', {}, diag.summary), h('p', {class: 'mut small'}, 'Cites ' + diag.cited_attempt_ids.length + ' attempts, ' + diag.tokens + ' tokens' + (diag.note ? '. ' + diag.note : ''))));
    const rows = (comps || []).map(c => {
      const cust = ((payments || []).find(p => p.id === c.payment_id) || {}).customer_id || '?', p = pays.find(x => x.compensation_id === c.id);
      return [cust, money(c.amount) + ' ' + c.currency, badge(c.status, c.status === 'eligible' ? 'ok' : 'mut'), c.rule_version,
        p ? badge(p.status, p.status === 'completed' ? 'ok' : 'bad') : '-', p ? badge(p.provider === 'mock_refund' ? 'MOCK (test only)' : 'PayPal sandbox', p.provider === 'mock_refund' ? 'mut' : 'info') : '-', p && p.provider_payout_id ? p.provider_payout_id : '-'];
    });
    setSlot(s.comp, JSON.stringify(rows.map(r => r.map(String))) + JSON.stringify(pays.map(p => p.status)), () => rows.length ?
      table(['Customer', 'Credit', 'Decision', 'Rules', 'Refund', 'Rail', 'Refund ID'], rows) : h('p', {class: 'mut'}, 'Not calculated yet. Available after recovery: click "Approve and refund".'));
  }};
  return page;
}

/* ---------- How it works ---------- */
function howPage() {
  const node = h('div', {}, h('h1', {}, 'How it works'), h('p', {class: 'mut'}, 'From a payment outage to a fair, auditable refund.'),
    h('div', {class: 'card'}, h('h3', {}, 'The pipeline'), h('div', {class: 'flow'},
      [['1. Attempts', 'Customers pay through the payment service. Every attempt is recorded.'], ['2. Detect', '3 failures in a row open one incident. 5 healthy attempts in a row close it.'],
       ['3. Evidence', 'Failed attempts link the incident to the customers who were affected.'], ['4. Explain', 'An LLM writes a diagnosis. It is validated, with a rule-based fallback.'],
       ['5. Compensate', 'Versioned rules turn severity into a credit. No AI involved.'], ['6. Refund', 'An operator approves. An idempotent PayPal refund is issued.']]
      .flatMap(([t, d], i) => [i ? h('span', {class: 'ar'}, '\u2192') : null, h('div', {class: 'n'}, h('b', {}, t), d)]))),
    h('div', {class: 'card'}, h('h3', {}, 'Design decisions'), h('ul', {class: 'clean'},
      h('li', {}, 'The LLM is an untrusted advisor: its output is validated and never feeds the money logic.'),
      h('li', {}, 'If the AI and the rules disagree, confidence is capped at low and the diagnosis is flagged for review.'),
      h('li', {}, 'A timeout is an unknown outcome, not a failure. Retries reuse the same idempotency key.'),
      h('li', {}, 'Only customers with recorded failed attempts are compensated.'),
      h('li', {}, 'Money moves only after an operator approves.'))),
    h('div', {class: 'card'}, h('h3', {}, 'Limitations'), h('ul', {class: 'clean'},
      h('li', {}, 'The payment service is simulated, and thresholds and severity levels are demo values.'),
      h('li', {}, 'PayPal sandbox only, with fake money. Mock refunds are labelled and never touch PayPal.'),
      h('li', {}, 'No Kubernetes, automatic remediation, or post-fix verification yet. These are planned next.'))));
  return {node, every: 0, async refresh() {}};
}

/* ---------- Router ---------- */
async function route() {
  clearInterval(timer);
  const parts = location.hash.replace(/^#\/?/, '').split('/'), name = parts[0] || '';
  document.querySelectorAll('#nav a').forEach(a => a.classList.toggle('on', a.dataset.r === (name === 'incident' ? 'incidents' : name)));
  current = name === 'incidents' ? incidentsPage() : name === 'incident' ? incidentPage(parts[1]) : name === 'how' ? howPage() : overviewPage();
  app.replaceChildren(current.node);
  await current.refresh();
  if (current.every) timer = setInterval(() => current.refresh(), current.every);
}
window.addEventListener('hashchange', route);
route();
</script></body></html>
"""


@router.get("/ui", response_class=HTMLResponse)
def dashboard():
    return PAGE
