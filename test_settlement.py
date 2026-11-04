"""Run: python test_settlement.py  (uses a throwaway SQLite file and a fake PayPal; no network)."""
import os

if os.path.exists("test_tmp.db"):
    os.remove("test_tmp.db")
os.environ["DATABASE_URL"] = "sqlite:///test_tmp.db"
import httpx
from fastapi.testclient import TestClient
import settlement
from database import Base, engine, SessionLocal
import models
from models import Payment, Payout
import main

Base.metadata.create_all(engine)
client = TestClient(main.app)
calls = []

def mk_resp(code, body):
    req = httpx.Request("POST", "http://x")
    return httpx.Response(code, json=body, request=req)

def fake_ok(capture_id, amount, currency, request_id):
    calls.append((capture_id, amount, currency, request_id))
    return {"id": f"REFUND{len(calls)}", "status": "COMPLETED"}

def setup(with_capture=True):
    with SessionLocal() as db:
        p = Payment(customer_id="seed-x", amount="20.00", currency="USD",
                    status="completed", capture_id=("CAP%d" % (len(calls)+id(object()) % 9999)) if with_capture else None)
        db.add(p); db.commit(); db.refresh(p); pid = p.id
    inc = client.post("/incidents", json={"service": "s", "severity": "critical", "reason": "r"}).json()["id"]
    assert client.post(f"/incidents/{inc}/payments", json={"payment_id": pid, "impact_reason": "t"}).status_code == 201
    client.patch(f"/incidents/{inc}/status", json={"status": "resolved"})
    comps = client.post(f"/incidents/{inc}/compensations").json()
    return comps[0]

# 1. happy path + idempotency
settlement.refund_capture = fake_ok
c = setup()
assert c["amount"] == "2.00", c
r1 = client.post(f"/compensations/{c['id']}/refund").json()
r2 = client.post(f"/compensations/{c['id']}/refund").json()
assert r1["status"] == r2["status"] == "completed" and len(calls) == 1, (r1, r2, calls)
assert calls[0][3] == f"aegispay-compensation-{c['id']}" and calls[0][1] == "2.00"
print("1 ok: completed once, second call did not hit PayPal")

# 2. timeout -> unknown -> retry with SAME idempotency key
def fake_timeout(*a):
    calls.append(a); raise httpx.ReadTimeout("slow")
settlement.refund_capture = fake_timeout
c = setup()
n = len(calls)
r = client.post(f"/compensations/{c['id']}/refund").json()
assert r["status"] == "unknown", r
settlement.refund_capture = fake_ok
r = client.post(f"/compensations/{c['id']}/refund").json()
assert r["status"] == "completed" and calls[n][3] == calls[-1][3], (r, calls[n:])
print("2 ok: timeout = unknown, retry reused same idempotency key, then completed")

# 3. permanent 4xx -> failed, never auto-retried
def fake_422(*a):
    calls.append(a); raise httpx.HTTPStatusError("bad", request=None, response=mk_resp(422, {"name": "REFUND_AMOUNT_EXCEEDED"}))
settlement.refund_capture = fake_422
c = setup(); n = len(calls)
r = client.post(f"/compensations/{c['id']}/refund").json()
client.post(f"/compensations/{c['id']}/refund")
assert r["status"] == "failed" and len(calls) == n + 1, (r, len(calls) - n)
print("3 ok: 4xx = failed, not retried")

# 4. no capture -> blocked, PayPal never called
c = setup(with_capture=False); n = len(calls)
r = client.post(f"/compensations/{c['id']}/refund").json()
assert r["status"] == "blocked" and len(calls) == n, r
print("4 ok: no capture = blocked, PayPal not called")

# 5. legacy Payouts-API row gets converted
settlement.refund_capture = fake_ok
with SessionLocal() as db:
    c2 = setup()
    db.add(Payout(compensation_id=c2["id"], idempotency_key="aegispay-compensation-%d" % c2["id"],
                  provider="paypal", status="blocked", error_message="old country error"))
    db.commit()
r = client.post(f"/compensations/{c2['id']}/refund").json()
assert r["status"] == "completed" and r["error_message"] is None, r
print("5 ok: legacy payout row converted and settled")
# 6. MOCK capture ids never reach PayPal and are labelled mock_refund
settlement.refund_capture = fake_ok
c = setup(); n = len(calls)
with SessionLocal() as db:
    pay = db.get(Payment, db.get(models.Compensation, c["id"]).payment_id)
    pay.capture_id = "MOCK-TEST1"
    db.commit()
r = client.post(f"/compensations/{c['id']}/refund").json()
assert r["status"] == "completed" and r["provider"] == "mock_refund" and len(calls) == n, r
print("6 ok: mock payment refunded as mock_refund, PayPal not called")
print("ALL TESTS PASSED")