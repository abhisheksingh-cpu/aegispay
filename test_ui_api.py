"""Run: python test_ui_api.py  (dashboard endpoints; throwaway SQLite; no network)."""
import os

if os.path.exists("test_tmp4.db"):
    os.remove("test_tmp4.db")
os.environ["DATABASE_URL"] = "sqlite:///test_tmp4.db"

import httpx
from fastapi.testclient import TestClient

import demo
import main
from database import Base, SessionLocal, engine
from models import Payment

Base.metadata.create_all(engine)
client = TestClient(main.app)
with SessionLocal() as db:
    db.add_all([Payment(customer_id="seed-a", amount="20.00", currency="USD", status="completed", capture_id="MOCK-A")])
    db.commit()


def attempt(ok):
    client.post("/attempts", json={"customer_id": "seed-a", "ok": ok, "latency_ms": 5, "error": None if ok else "HTTP 503"})


ov = client.get("/overview").json()
assert ov["service"]["status"] == "no data" and ov["kpis"]["attempts_total"] == 0
print("1 ok: empty system reports 'no data'")

for _ in range(3):
    attempt(False)
ov = client.get("/overview").json()
assert ov["service"]["status"] == "down" and ov["kpis"]["incidents_open"] == 1 and ov["kpis"]["attempts_failed"] == 3
attempt(True)
assert client.get("/overview").json()["service"]["status"] == "degraded"
print("2 ok: status goes down -> degraded, open incident counted")

for _ in range(4):
    attempt(True)
iid = client.get("/incidents").json()[0]["id"]
client.post(f"/incidents/{iid}/compensations")
for c in client.get(f"/incidents/{iid}/compensations").json():
    client.post(f"/compensations/{c['id']}/refund")
k = client.get("/overview").json()["kpis"]
assert k["refunds_mock_count"] == 1 and k["refunds_mock_usd"] == "0.40" and k["refunds_real_count"] == 0 and k["incidents_open"] == 0, k
print("3 ok: refunds counted separately for mock and real (0.40 mock)")

calls = []
demo.httpx.post = lambda url, json=None, timeout=None: (calls.append(json) or httpx.Response(200, json={"mode": json["mode"]}, request=httpx.Request("POST", url)))
demo.httpx.get = lambda url, timeout=None: httpx.Response(200, json={"mode": "none"}, request=httpx.Request("GET", url))
assert client.post("/demo/fault", json={"mode": "down"}).json() == {"mode": "down"} and calls == [{"mode": "down"}]
assert client.post("/demo/fault", json={"mode": "bogus"}).status_code == 422
print("4 ok: demo fault switch forwards valid modes and rejects invalid ones")


def unreachable(*a, **k):
    raise httpx.ConnectError("down")


demo.httpx.get = unreachable
demo.httpx.post = unreachable
assert client.get("/demo/fault").json() == {"mode": "unreachable"}
assert client.post("/demo/fault", json={"mode": "none"}).status_code == 502
print("5 ok: unreachable payment service handled")
print("ALL TESTS PASSED")
