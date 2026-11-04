import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Compensation, Payment, Payout
from paypal_service import refund_capture

PROVIDERS = {"paypal_refund", "mock_refund"}
FINAL = {"completed", "blocked", "failed"}  # never retried automatically


def _mock_refund(capture_id: str, amount: str, currency: str, request_id: str) -> dict:
    """Test-only stand-in for PayPal (capture IDs starting with MOCK-). Never moves money."""
    return {"id": f"MOCK-REFUND-{request_id}", "status": "COMPLETED"}


def settle(db: Session, comp: Compensation) -> Payout:
    """Refund one compensation exactly once. Safe to call repeatedly."""
    payment = db.get(Payment, comp.payment_id)
    is_mock = bool(payment and payment.capture_id and payment.capture_id.startswith("MOCK-"))
    provider = "mock_refund" if is_mock else "paypal_refund"

    payout = db.scalar(select(Payout).where(Payout.compensation_id == comp.id))
    if payout is not None and payout.provider not in PROVIDERS:  # old Payouts-API row
        payout.provider, payout.status = provider, "submitting"
        payout.provider_payout_id = payout.error_message = None
    if payout is None:
        payout = Payout(
            compensation_id=comp.id,
            idempotency_key=f"aegispay-compensation-{comp.id}",
            provider=provider,
            status="submitting",
        )
        db.add(payout)
    if payout.status in FINAL:
        return payout

    if payment is None or not payment.capture_id:
        payout.status, payout.error_message = "blocked", "Payment has no PayPal capture to refund"
    else:
        refund = _mock_refund if is_mock else refund_capture
        try:
            result = refund(payment.capture_id, str(comp.amount), comp.currency, payout.idempotency_key)
            payout.provider_payout_id = result["id"]
            payout.status = result["status"].lower()  # completed / pending
            payout.error_message = None
        except httpx.HTTPStatusError as exc:
            # 5xx: outcome unknown, retry is safe (same idempotency key). 4xx: permanent.
            payout.status = "unknown" if exc.response.status_code >= 500 else "failed"
            payout.error_message = exc.response.text[:500]
        except httpx.TransportError as exc:  # timeout / connection lost: outcome UNKNOWN
            payout.status, payout.error_message = "unknown", str(exc)[:500]

    db.commit()
    db.refresh(payout)
    return payout