"""Operator approval step: money moves only when you run this. Usage: python settle_incident.py <incident_id>"""
import sys

import httpx

c = httpx.Client(base_url="http://localhost:8000", timeout=60)
iid = int(sys.argv[1])

evidence = c.get(f"/incidents/{iid}/evidence").json()
print(f"Incident {iid}: {len(evidence)} failed attempts recorded as evidence")

r = c.post(f"/incidents/{iid}/compensations")  # existing records are skipped, so it is safe to repeat
if r.status_code not in (200, 201):
    raise SystemExit(f"Cannot compensate: {r.json()['detail']}")

for comp in c.get(f"/incidents/{iid}/compensations").json():
    if comp["status"] != "eligible":
        print(f"compensation {comp['id']}: {comp['status']} ({comp['decision_reason']})")
        continue
    out = c.post(f"/compensations/{comp['id']}/refund").json()
    print(f"compensation {comp['id']}: ${comp['amount']} -> {out['status']} (refund {out['provider_payout_id']})")
