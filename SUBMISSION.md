# Devpost description (draft: edit freely, keep it honest)

**Tagline:** Turn a payment outage into evidence, an explanation, and a fair, idempotent PayPal refund.

**Problem.** SLA credits are usually claim-based. Customers must notice an outage, file a request and prove it, while the provider already has the data. Disputes cost time and trust.

**What it does.** AegisPay records customer payment attempts, opens one de-duplicated incident after three consecutive failures, and confirms recovery after five healthy attempts. Failed attempts become evidence linking the incident to only the affected customers. An LLM writes a plain-English diagnosis that must cite real evidence IDs; invalid output falls back to deterministic rules. Versioned rules compute the credit, and after operator approval it is issued as an idempotent PayPal sandbox refund. A live timeline shows the full audit trail.

**How we built it.** Python, FastAPI, PostgreSQL, SQLAlchemy, Docker Compose, PayPal Orders and Refunds APIs, and Groq (`gpt-oss-20b`). Three test suites run against a fake PayPal and a fake LLM.

**Where PayPal and AI matter.** PayPal is the settlement rail: real captured sandbox payments are refunded with idempotency keys and unknown-outcome handling. AI explains incidents, constrained by schema validation, evidence-ID checks and a safe fallback, and it never decides money.

**Challenges.** PayPal Payouts was rejected for my sandbox sender country, so I switched to refunds. India-based sandbox accounts could not complete checkout, so the sandbox merchant is US-based. LLM output cannot be trusted, so everything is validated.

**What we are proud of.** The safety design: the LLM cannot affect money, retries cannot double-pay, and only customers with recorded failures are credited.

**Limitations (be upfront).** Simulated payment service, demo thresholds, sandbox only, small diagnosis evaluation ([fill in: result of `python eval_diagnosis.py`]).

**What's next.** Kubernetes deployment with least-privilege RBAC, bounded automatic remediation, independent recovery verification, and a larger evaluation set.
