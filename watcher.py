"""Simulates customers paying through the payment service and reports every attempt to the API."""
import random
import time

import httpx

API = "http://localhost:8000"
SERVICE = "http://localhost:8001"

payments = httpx.get(f"{API}/payments", timeout=10).json()
customers = list(dict.fromkeys(p["customer_id"] for p in payments if p["capture_id"]))[:2]
if not customers:
    raise SystemExit("No customers with captured payments. Run: python seed_payments.py")
print("Active customers (others stay unaffected):", customers)

while True:
    customer = random.choice(customers)
    start = time.time()
    try:
        r = httpx.post(f"{SERVICE}/pay", json={"customer_id": customer}, timeout=2)
        ok, error = r.is_success, None if r.is_success else f"HTTP {r.status_code}"
    except httpx.HTTPError as exc:
        ok, error = False, type(exc).__name__
    latency = int((time.time() - start) * 1000)

    out = httpx.post(f"{API}/attempts", timeout=10, json={
        "customer_id": customer, "ok": ok, "latency_ms": latency, "error": error,
    }).json()
    print(f"{customer}: {'ok' if ok else 'FAILED ' + str(error)} ({latency} ms) open_incident={out['open_incident_id']}")
    time.sleep(1)
