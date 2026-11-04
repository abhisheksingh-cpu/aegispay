"""Create real PayPal sandbox payments (buyer approves each) and store their capture IDs."""
import sys
import uuid

import httpx
from sqlalchemy import text

from database import SessionLocal
from models import Payment
from paypal_service import PAYPAL_BASE_URL, get_access_token

MOCK = "--mock" in sys.argv  # test payments without PayPal checkout; refunds are labelled mock_refund
ARGS = [a for a in sys.argv[1:] if a != "--mock"]
COUNT = int(ARGS[0]) if ARGS else 3
AMOUNT = "20.00"
HEADERS = None if MOCK else {"Authorization": f"Bearer {get_access_token()}"}


def paypal(path: str, body: dict | None = None) -> dict:
    r = httpx.post(
        f"{PAYPAL_BASE_URL}{path}",
        headers={**HEADERS, "PayPal-Request-Id": str(uuid.uuid4())},
        json=body or {},
        timeout=30,
    )
    if not r.is_success:
        raise SystemExit(f"{path} -> {r.status_code}: {r.text[:500]}")
    return r.json()


with SessionLocal() as db:
    db.execute(text("SELECT 1"))  # fail fast if the database is down
    for i in range(1, COUNT + 1):
        if MOCK:
            capture_id = f"MOCK-{uuid.uuid4().hex[:12]}"
        else:
            order = paypal("/v2/checkout/orders", {
                "intent": "CAPTURE",
                "purchase_units": [{"amount": {"currency_code": "USD", "value": AMOUNT}}],
            })
            link = next(l["href"] for l in order["links"] if l["rel"] in ("approve", "payer-action"))
            print(f"\nPayment {i}/{COUNT}: approve as the US SANDBOX BUYER:\n{link}")
            input("Press Enter after you see 'Thanks for using PayPal'...")
            capture = paypal(f"/v2/checkout/orders/{order['id']}/capture")
            capture_id = capture["purchase_units"][0]["payments"]["captures"][0]["id"]

        print("MOCK payment (no PayPal):" if MOCK else "Captured at PayPal:", capture_id)
        db.add(Payment(
            customer_id=f"seed-customer-{uuid.uuid4().hex[:6]}",
            amount=AMOUNT,
            currency="USD",
            status="completed",
            capture_id=capture_id,
        ))
        db.commit()
        print("Saved payment with capture", capture_id)