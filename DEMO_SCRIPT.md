# Demo video script (target 2:40, hard limit under 3:00, public on YouTube)

Pre-flight: `docker compose up -d --build`, then `python fault.py none`. Open `http://localhost:8000/ui` full screen. In a terminal run `python watcher.py` and keep it visible in a small window. `.env` must NEVER be on screen. Do one full dry run first.

| Time | Show | Say |
|---|---|---|
| 0:00-0:20 | Title slide, then the **How it works** page | "SLA credits are usually claim-based: the customer has to notice, file, and prove an outage. The provider already measured it. AegisPay turns that measurement into evidence and a fair credit." |
| 0:20-0:45 | **Overview**: status HEALTHY, live attempts scrolling | "Simulated customers pay through a payment service. Every attempt is recorded, and right now everything is healthy." |
| 0:45-1:15 | Click **Break service**. Status turns DOWN, FAILED rows appear, incident card appears | "I break the service. After three failures in a row one incident opens, and it never opens duplicates." Wait 12 to 15 seconds so there are 10 or more failures (critical). |
| 1:15-1:35 | Click **Recover**. Status returns to HEALTHY | "Recovery counts only after five healthy customer attempts in a row, not when the service says it is fine." |
| 1:35-2:05 | **Open details** on the incident. Show the progress bar and evidence, then click **Run AI explanation** | "An LLM explains the cause and must cite real attempt IDs. If its output fails validation, or it disagrees with the rules, it is flagged. It never touches money." |
| 2:05-2:40 | Click **Approve and refund**, confirm. Show the table: PayPal sandbox vs MOCK. Open the PayPal sandbox activity tab | "Compensation comes from versioned rules, only for customers with failed attempts. Money moves only on approval, as an idempotent PayPal refund." |
| 2:40-2:55 | Back to **Overview** KPIs | "A sandbox with a simulated service and demo thresholds. Next: Kubernetes, bounded auto-remediation, verified recovery." |

Optional proof of idempotency: run `python settle_incident.py <id>` in the terminal and show the identical refund IDs.

Tips: record 1080p, speak slowly, add captions, no copyrighted music, show that the unaffected customer received nothing, and say plainly which payments are real sandbox and which are mock.
