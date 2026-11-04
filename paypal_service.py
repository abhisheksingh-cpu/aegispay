
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"


def get_access_token() -> str:
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("PayPal Sandbox credentials are missing")

    response = httpx.post(
        f"{PAYPAL_BASE_URL}/v1/oauth2/token",
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json"},
        timeout=20.0,
    )

    response.raise_for_status()
    return response.json()["access_token"]


def create_sandbox_payout(
    receiver_email: str,
    amount: str,
    currency: str,
    sender_batch_id: str,
    sender_item_id: str,
) -> dict:
    token = get_access_token()

    payload = {
        "sender_batch_header": {
            "sender_batch_id": sender_batch_id,
            "email_subject": "AegisPay SLA Compensation",
            "email_message": (
                "This is a Sandbox test payout from AegisPay."
            ),
        },
        "items": [
            {
                "recipient_type": "EMAIL",
                "receiver": receiver_email,
                "sender_item_id": sender_item_id,
                "amount": {
                    "value": amount,
                    "currency": currency,
                },
                "note": "Sandbox SLA compensation test",
            }
        ],
    }

    response = httpx.post(
        f"{PAYPAL_BASE_URL}/v1/payments/payouts",
        params={"sync_mode": "false"},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30.0,
    )

    response.raise_for_status()
    return response.json()
def refund_capture(capture_id: str, amount: str, currency: str, request_id: str) -> dict:
    response = httpx.post(
        f"{PAYPAL_BASE_URL}/v2/payments/captures/{capture_id}/refund",
        headers={
            "Authorization": f"Bearer {get_access_token()}",
            "PayPal-Request-Id": request_id,
        },
        json={
            "amount": {"currency_code": currency, "value": amount},
            "note_to_payer": "AegisPay SLA credit",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()