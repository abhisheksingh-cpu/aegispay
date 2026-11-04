"""Usage: python explain_incident.py <incident_id>   (needs GROQ_API_KEY in the API's .env)"""
import sys

import httpx

r = httpx.post(f"http://localhost:8000/incidents/{int(sys.argv[1])}/diagnosis", timeout=60)
r.raise_for_status()
d = r.json()
print(f"[{d['source']}] cause={d['cause']} confidence={d['confidence']} tokens={d['tokens']}")
print(d["summary"])
print("cited attempts:", d["cited_attempt_ids"])
if d["note"]:
    print("note:", d["note"])
