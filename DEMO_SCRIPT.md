# Demo video script (target 2:40, hard limit under 3:00, public on YouTube)

Pre-flight: `docker compose up -d`, API and payment service healthy, `/ui` open in a browser, two terminals ready, mock + real customers seeded, `.env` NEVER on screen. Do one full dry run first.

| Time | Show | Say |
|---|---|---|
| 0:00-0:20 | Title slide, then the README diagram | "SLA credits are usually claim-based: the customer has to notice, file, and prove an outage. The provider already measured it. AegisPay turns that measurement into evidence and a fair credit." |
| 0:20-0:50 | Terminal: `python watcher.py` (ok lines). Browser: `/ui` | "Simulated customers pay through a payment service. Every attempt is recorded. Right now everything is healthy." |
| 0:50-1:20 | Run `python fault.py down`. Watch FAILED lines, then the incident appears in `/ui` | "I break the service. After three failures in a row one incident opens, and it never opens duplicates." |
| 1:20-1:40 | Run `python fault.py none`. Show recovery line | "Recovery counts only after five healthy customer attempts in a row, not when the service says it is fine." |
| 1:40-2:05 | `python explain_incident.py <id>`, then `/ui` Diagnosis box | "An LLM explains the cause and must cite real attempt IDs. If its output fails validation, rules take over. It never touches money." |
| 2:05-2:30 | `python settle_incident.py <id>` (operator approval). Show PayPal sandbox activity with the refund. Run settle again | "Compensation comes from versioned rules, only for customers with failed attempts. Money moves only on approval, as an idempotent PayPal refund. Running it twice sends nothing new." |
| 2:30-2:50 | `/ui` compensation table (PayPal sandbox vs MOCK labels) | "This is a sandbox with a simulated service and demo thresholds. Next: Kubernetes, bounded auto-remediation, verified recovery." |

Tips: record 1080p, speak slowly, add captions, no copyrighted music, show the unaffected customer receiving nothing, and say plainly which payments are real sandbox and which are mock.
