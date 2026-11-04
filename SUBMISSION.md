# AegisPay: Devpost submission

**Tagline:** Turn a payment outage into evidence, an explanation, and a fair, idempotent PayPal refund.

**Links:** Code: https://github.com/abhisheksingh-cpu/aegispay | Demo video: [YouTube URL] | Built by: Singh Abhishek Jiutbandhan (solo)

## The problem
SLA credits are usually claim-based. After an outage, customers must notice it, file a request, and prove they were affected, even though the provider already has the data. That costs time, causes disputes, and erodes trust.

## What it does
AegisPay watches a payment service through customer payment attempts and closes the loop from outage to refund:

1. **Detects.** Three consecutive failed attempts open one de-duplicated incident. It closes only after five consecutive healthy attempts, so recovery is confirmed by customer behaviour and not by the service's own claim.
2. **Links by evidence.** A customer is treated as affected only if they had failed attempts during the incident and a captured payment to credit. Customers with no failures receive nothing.
3. **Explains.** An LLM (Groq, `openai/gpt-oss-20b`) writes a plain-English diagnosis as JSON. The output is validated: the schema, an allowed list of causes, and every cited attempt ID must exist in the evidence. If validation fails, a rule-based diagnosis is stored instead. If the LLM and the rules disagree, confidence is capped at low and the diagnosis is flagged for human review.
4. **Compensates.** Versioned, deterministic rules turn incident severity into a credit amount. The LLM never sees or decides money.
5. **Settles.** After an operator approves, each credit is issued as a PayPal sandbox partial refund with an idempotency key. Running settlement again changes nothing.
6. **Shows everything.** A live timeline page displays the status history, evidence, diagnosis, and refunds, with real PayPal sandbox refunds clearly separated from mock test refunds.

## What I verified
- **End-to-end run:** one incident recorded 32 failed attempts and was rated critical (10% credit under the demo rules). The affected customer holding a real captured $10 sandbox payment received a **real $1.00 PayPal sandbox refund**. A second affected customer, on a mock test payment, received a $2.00 refund labelled `mock_refund`. A third customer with no failed attempts received nothing.
- **Idempotency:** running the settlement a second time returned the identical refund IDs and sent nothing new to PayPal.
- **Tests:** three suites (detection, settlement, and AI diagnosis, 20 checks in total) pass against a fake PayPal and a fake LLM. They cover de-duplication, recovery, evidence-based linking, timeout handling, permanent errors, mock-payment isolation, and rejection of invalid LLM output.
- **AI evaluation:** on 5 hand-written scenarios, the rule baseline was correct 5/5 and the LLM 4/5, using 1,973 tokens in total (about 400 per diagnosis). The miss was a mixed-failure case where the LLM was confidently wrong, because validation checks format and not truth. That led to the disagreement flag described above. This is a small sample, and the baseline was written with these scenarios in mind, so it is a sanity check and not statistical proof.

## How PayPal and AI are used
- **PayPal** is the settlement rail. Real captured sandbox payments are refunded through the Refunds API with idempotency keys. Timeouts are treated as an unknown outcome and retried safely with the same key, and permanent errors are never retried.
- **AI** explains incidents and is treated as an untrusted advisor. Its output is validated and stored as text, and the compensation and refund code never reads it. In my evaluation it was cheap and mostly accurate, but not better than simple rules on known faults. Its value is readable explanations, with safeguards when it is wrong.

## Built with
Python, FastAPI, PostgreSQL, SQLAlchemy, Docker Compose, PayPal Orders and Refunds APIs, Groq.

## Challenges
- PayPal Payouts was rejected for my sandbox sender country, so I redesigned settlement around refunds.
- India-based sandbox accounts could not complete checkout in my tests, so the sandbox merchant is US-based.
- LLM output cannot be trusted, so every answer is validated and has a deterministic fallback.
- PayPal's sandbox checkout page was sometimes slow, so some demo payments are mock and are labelled as such.

## Limitations
- The payment service is simulated. Detection thresholds and severity levels are demo values, not real SLA terms.
- Sandbox only, with fake money. The merchant account is a US sandbox account.
- Mock test payments are labelled `mock_refund` and never touch PayPal.
- No Kubernetes, automatic remediation, or post-fix verification yet.

## What's next
Kubernetes deployment with least-privilege permissions, bounded automatic remediation (restart or rollback) that acts only when the rules and the AI agree, independent recovery verification, and a larger evaluation set.

## Try it
See the README for setup. In short: `docker compose up -d --build`, `python init_db.py`, `python seed_payments.py --mock 2`, then run `watcher.py`, `fault.py down`, `fault.py none`, and `settle_incident.py <id>`. Open `http://localhost:8000/ui` for the timeline.
