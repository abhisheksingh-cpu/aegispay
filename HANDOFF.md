# AegisPay Handoff (paste into a new Claude chat)

## Goal
AI-assisted payment reliability + SLA compensation. Target: PayPal AI Hackathon (closes Nov 12, 2026; confirm on Devpost) and my major project.
Rules: code small/clean/explainable; explain simply; no Java; keep DB data; don't bypass PayPal restrictions; keep replies short.

## Decisions
- Phase 1 (hackathon): plain Docker, NO Kubernetes. Phase 2: Kubernetes, auto-remediation, verification.
- Flow: watcher/prober -> incident + evidence -> AI explains (LLM never decides money) -> deterministic compensation rules -> PayPal REFUND -> audit trail.
- Compensation rail = PayPal partial REFUND on a captured payment (Payouts API blocked for my India sender).
- LLM = untrusted advisor; code/policy decides.

## Verified
- Stack: FastAPI, Postgres 17 (compose: aegispay-db, aegispay-api), SQLAlchemy, httpx. DB backup done (backup.sql, gitignored).
- PayPal OAuth works. India Business sandbox + India buyer: checkout error page (cause unconfirmed).
- US Business sandbox app + US Personal buyer: order -> capture -> $0.50 partial refund COMPLETED (refund_spike.py).
- Each refund needs a captured payment (browser approval by buyer once).

## STATUS (Nov 2): detection -> evidence -> compensation -> refund WORKS end to end
- Verified on my machine: incident 6, 32 failed attempts, critical (10%). Real PayPal refund $1.00 on real capture; mock refund $2.00 (labelled mock_refund); unaffected customer got nothing.
- Real capture 0D013091UK850034T ($10, ~$8.50 refundable left). PayPal checkout page often spins; retry later for fresh real payments.
- Tests pass: test_settlement.py, test_detection.py (fake PayPal, SQLite).
- Files: payment_service.py (fault switch), watcher.py (customer traffic), detector.py (open after 3 fails, resolve after 5 ok, dedupe), evidence.py, settlement.py (refund + mock), settle_incident.py (operator approval), fault.py.
- Run: docker compose up -d --build; python watcher.py; python fault.py down|none; python settle_incident.py <id>
- Deadline: PayPal AI Hackathon closes Nov 12 (confirm on Devpost). Submit by ~Nov 10.

## UPDATE (Nov 4-5): dashboard + AI + submission files done
- Repo public: github.com/abhisheksingh-cpu/aegispay (main). README, LICENSE, SUBMISSION.md, DEMO_SCRIPT.md exist.
- AI: Groq openai/gpt-oss-20b via llm.py; explain.py validates and falls back to rules; flags disagreement with rules. Eval: rules 5/5, LLM 4/5, 1973 tokens.
- Dashboard /ui (ui.py, overview.py, demo.py): Overview, Incidents, Incident detail, How it works; demo buttons (break/slow/recover, run AI, approve+refund). Tested in jsdom.
- Tests: test_detection (6), test_settlement (6), test_explain (9), test_ui_api (5).
- Remaining: fill [YouTube URL]/[YOUR NAME], dry run, record (<3 min), submit on Devpost by ~Nov 10. Phase 2: Kubernetes, remediation.

## Code state (older notes)
- main.py ~500 lines (to split into routers). compensation_rules.py (v1, severity rates). Payout flow in main.py still uses Payouts API (to replace).
- Added: Payment.capture_id (models.py) + refund_capture() (paypal_service.py).
- DB: run ALTER TABLE payments ADD COLUMN IF NOT EXISTS capture_id VARCHAR(50) UNIQUE;

## Next steps (updated)
1. AI explanation of incident from evidence (schema output, cites attempt ids, never decides money) + small eval vs rule baseline.
2. One-page read-only incident timeline.
3. Fresh real PayPal payments when checkout works; README + architecture diagram + demo video; honest limits (US sandbox merchant, mock payments, demo thresholds, no auto-fix yet).

## Older next steps
1. Seed script: create+approve N real sandbox payments, store capture_id.
2. Replace payout endpoint with refund (idempotent: PayPal-Request-Id = aegispay-compensation-<id>; handle unknown/timeout by reconcile; double-run test).
3. Switch demo currency to USD.
4. Prober + fault switch + incident dedupe; evidence records; AI diagnosis + eval vs rule baseline.
5. Split main.py; read-only timeline page; demo video + README. Be honest about limits (US sandbox merchant).

## Secrets
Never share .env values. Rotate PayPal secret if exposed.
