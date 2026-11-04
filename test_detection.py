"""Run: python test_detection.py  (throwaway SQLite file, fake PayPal, no network)."""
import os

if os.path.exists("test_tmp2.db"):
    os.remove("test_tmp2.db")
os.environ["DATABASE_URL"] = "sqlite:///test_tmp2.db"

from fastapi.testclient import TestClient

import main
import settlement
from database import Base, SessionLocal, engine
from models import IncidentPayment, Payment

Base.metadata.create_all(engine)
client = TestClient(main.app)
paypal_calls = []


def fake_refund(capture_id, amount, currency, request_id):
    paypal_calls.append((capture_id, amount, request_id))
    return {"id": f"REF{len(paypal_calls)}", "status": "COMPLETED"}


settlement.refund_capture = fake_refund

with SessionLocal() as db:
    for cust, cap in (("seed-a", "CAPA"), ("seed-b", "CAPB"), ("seed-c", "CAPC"), ("seed-nocap", None)):
        db.add(Payment(customer_id=cust, amount="20.00", currency="USD", status="completed", capture_id=cap))
    db.commit()


def attempt(cust, ok):
    r = client.post("/attempts", json={"customer_id": cust, "ok": ok, "latency_ms": 5,
                                       "error": None if ok else "HTTP 503"})
    assert r.status_code == 201, r.text
    return r.json()


def incidents():
    return client.get("/incidents").json()


for _ in range(4):
    attempt("seed-a", True)
assert incidents() == []
attempt("seed-a", False); attempt("seed-b", False)
assert incidents() == [], "2 failures must not open an incident"
attempt("seed-a", False)
inc = incidents()
assert len(inc) == 1 and inc[0]["status"] == "open"
iid = inc[0]["id"]
print("1 ok: 3 consecutive failures opened exactly one incident")

for c in ("seed-b", "seed-a", "seed-nocap", "seed-b"):
    attempt(c, False)
assert len(incidents()) == 1
assert len(client.get(f"/incidents/{iid}/evidence").json()) == 7
print("2 ok: more failures reused the same incident (deduped), 7 pieces of evidence")

for _ in range(4):
    attempt("seed-c", True)
assert incidents()[0]["status"] == "open", "4 healthy attempts are not enough"
attempt("seed-c", True)
done = incidents()[0]
assert done["status"] == "resolved" and done["severity"] == "high", done
print("3 ok: resolved only after 5 consecutive healthy attempts; severity high")

with SessionLocal() as db:
    linked = {db.get(Payment, l.payment_id).customer_id for l in db.query(IncidentPayment).all()}
assert linked == {"seed-a", "seed-b"}, linked
print("4 ok: only customers with failed attempts AND a captured payment were linked")

comps = client.post(f"/incidents/{iid}/compensations").json()
assert sorted(c["amount"] for c in comps) == ["1.00", "1.00"], comps
for c in client.get(f"/incidents/{iid}/compensations").json():
    for _ in range(2):
        assert client.post(f"/compensations/{c['id']}/refund").json()["status"] == "completed"
assert len(paypal_calls) == 2, paypal_calls
print("5 ok: 2 compensations of $1.00, refunded once each even when requested twice")

for _ in range(3):
    attempt("seed-a", False)
assert len(incidents()) == 2 and incidents()[1]["status"] == "open"
print("6 ok: a new outage after recovery opens a new incident")
print("ALL TESTS PASSED")
