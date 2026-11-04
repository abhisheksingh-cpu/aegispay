import uuid
import httpx
from paypal_service import PAYPAL_BASE_URL, get_access_token

HEADERS = {"Authorization": f"Bearer {get_access_token()}"}


def call(path, body=None):
    r = httpx.post(
        f"{PAYPAL_BASE_URL}{path}",
        headers={**HEADERS, "PayPal-Request-Id": str(uuid.uuid4())},
        json=body or {},
        timeout=30,
    )
    print(path, "->", r.status_code)
    if not r.is_success:
        raise SystemExit(r.text[:800])
    return r.json()


order = call("/v2/checkout/orders", {
    "intent": "CAPTURE",
    "purchase_units": [{
        "description": "AegisPay SLA service test",
        "amount": {"currency_code": "USD", "value": "10.00"},
    }],
    "application_context": {
        "shipping_preference": "NO_SHIPPING",
        "user_action": "PAY_NOW",
    },
})
link = next(l["href"] for l in order["links"] if l["rel"] in ("approve", "payer-action"))
print("Open in a browser, log in as your SANDBOX BUYER, approve:\n", link)
input("Press Enter after approving...")

cap = call(f"/v2/checkout/orders/{order['id']}/capture")
capture_id = cap["purchase_units"][0]["payments"]["captures"][0]["id"]
print("Captured:", capture_id)

refund = call(f"/v2/payments/captures/{capture_id}/refund", {
    "amount": {"currency_code": "USD", "value": "0.50"},
    "note_to_payer": "AegisPay SLA credit test",
})
print("Refund:", refund["id"], refund["status"])