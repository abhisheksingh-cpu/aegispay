"""One read-only page that shows an incident from detection to refund. Data comes from the existing API."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AegisPay incident timeline</title>
<style>
:root{--bg:#fff;--fg:#1a1a1a;--mut:#666;--line:#ddd;--card:#f6f7f9;--ok:#1a7f37;--bad:#c62828;--warn:#b26a00}
@media (prefers-color-scheme:dark){:root{--bg:#121212;--fg:#eee;--mut:#9aa0a6;--line:#333;--card:#1c1c1c;--ok:#4cc26a;--bad:#ff6b6b;--warn:#f0b050}}
body{font:15px/1.5 system-ui,sans-serif;background:var(--bg);color:var(--fg);max-width:920px;margin:24px auto;padding:0 16px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:24px 0 8px}p.sub{color:var(--mut);margin:0 0 16px}
select{font:inherit;padding:6px;max-width:100%}.item{padding:6px 10px;border-left:3px solid var(--line);margin:4px 0}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left}
th{color:var(--mut);font-weight:600}.box{background:var(--card);padding:10px 12px;border-radius:8px;margin:6px 0}
.badge{display:inline-block;padding:1px 8px;border-radius:10px;border:1px solid var(--line);font-size:12px}
.completed{color:var(--ok)}.failed,.blocked{color:var(--bad)}.warn{color:var(--warn)}.mut{color:var(--mut)}
</style></head><body>
<h1>AegisPay</h1>
<p class="sub">Incident timeline. Read-only, refreshes every 3 seconds.</p>
<select id="sel"></select>
<div id="out"></div>
<script>
const $ = id => document.getElementById(id);
const get = async u => { try { const r = await fetch(u); return r.ok ? await r.json() : null; } catch (e) { return null; } };
// Every value is shown with textContent, never innerHTML: evidence text is untrusted.
function el(tag, text, cls) { const e = document.createElement(tag); if (text !== undefined) e.textContent = String(text); if (cls) e.className = cls; return e; }
function table(headers, rows) {
  const t = el('table'), head = el('tr');
  headers.forEach(h => head.append(el('th', h))); t.append(head);
  rows.forEach(r => { const tr = el('tr'); r.forEach(c => tr.append(el('td', c))); t.append(tr); });
  return t;
}
function when(ts) { const d = new Date(ts); return isNaN(d) ? String(ts) : d.toLocaleTimeString(); }

async function show(id) {
  const [hist, ev, diag, comps, payouts, payments] = await Promise.all([
    get('/incidents/' + id + '/history'), get('/incidents/' + id + '/evidence'),
    get('/incidents/' + id + '/diagnosis'), get('/incidents/' + id + '/compensations'),
    get('/payouts'), get('/payments')]);
  const out = el('div');

  out.append(el('h2', '1. Timeline'));
  (hist || []).forEach(h => out.append(el('div', when(h.changed_at) + '  ->  ' + h.status, 'item')));

  out.append(el('h2', '2. Evidence'));
  const evidence = ev || [], byCustomer = {};
  evidence.forEach(e => { byCustomer[e.customer_id] = (byCustomer[e.customer_id] || 0) + 1; });
  out.append(el('div', evidence.length + ' failed payment attempts. By customer: ' +
    (Object.entries(byCustomer).map(([c, n]) => c + ' (' + n + ')').join(', ') || 'none'), 'box'));
  if (evidence.length) {
    out.append(table(['attempt', 'customer', 'error', 'ms'],
      evidence.slice(0, 8).map(e => [e.attempt_id, e.customer_id, e.error, e.latency_ms])));
    if (evidence.length > 8) out.append(el('div', '... and ' + (evidence.length - 8) + ' more', 'mut'));
  }

  out.append(el('h2', '3. Diagnosis'));
  if (!diag) {
    out.append(el('div', 'No diagnosis yet. Run: python explain_incident.py ' + id, 'box mut'));
  } else {
    const box = el('div', undefined, 'box');
    box.append(el('span', diag.source === 'llm' ? 'AI (' + diag.model + ')' : 'Rule-based (' + diag.source + ')', 'badge'));
    box.append(el('div', 'Cause: ' + diag.cause + '   Confidence: ' + diag.confidence));
    box.append(el('div', diag.summary));
    box.append(el('div', 'Cites ' + diag.cited_attempt_ids.length + ' attempts, ' + diag.tokens + ' tokens' +
      (diag.note ? '. Note: ' + diag.note : ''), 'mut'));
    out.append(box);
  }

  out.append(el('h2', '4. Compensation and refunds'));
  const rows = (comps || []).map(c => {
    const customer = ((payments || []).find(p => p.id === c.payment_id) || {}).customer_id || '?';
    const p = (payouts || []).find(x => x.compensation_id === c.id);
    const kind = !p ? 'not settled' : (p.provider === 'mock_refund' ? 'MOCK (test only)' : 'PayPal sandbox');
    return [customer, c.amount + ' ' + c.currency, c.status, c.rule_version, p ? p.status : '-', kind, p && p.provider_payout_id ? p.provider_payout_id : '-'];
  });
  out.append(rows.length ? table(['customer', 'amount', 'decision', 'rules', 'refund', 'rail', 'refund id'], rows)
    : el('div', 'No compensation yet. After recovery, run: python settle_incident.py ' + id, 'box mut'));

  $('out').replaceChildren(out);
}

let lastSig = '';
async function load() {
  const incidents = ((await get('/incidents')) || []).slice().reverse();
  if (!incidents.length) { $('out').replaceChildren(el('p', 'No incidents yet. Start the watcher, then run: python fault.py down', 'mut')); return; }
  const sig = incidents.map(i => i.id + i.status + i.severity).join();
  const keep = $('sel').value;
  if (sig !== lastSig) {
    lastSig = sig;
    $('sel').replaceChildren(...incidents.map(i => { const o = el('option', '#' + i.id + '  ' + i.service + '  ' + i.status + '  ' + i.severity); o.value = i.id; return o; }));
  }
  $('sel').value = incidents.some(i => String(i.id) === keep) ? keep : incidents[0].id;
  await show($('sel').value);
}
$('sel').addEventListener('change', () => show($('sel').value));
load(); setInterval(load, 3000);
</script></body></html>
"""


@router.get("/ui", response_class=HTMLResponse)
def timeline_page():
    return PAGE