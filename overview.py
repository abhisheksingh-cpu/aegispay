"""Numbers for the dashboard overview page."""
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from detector import OPEN_STATUSES
from models import Attempt, Compensation, Incident, Payout

router = APIRouter()


def _count(db: Session, query) -> int:
    return db.scalar(query) or 0


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    recent = db.scalars(select(Attempt).order_by(Attempt.id.desc()).limit(20)).all()
    last5 = recent[:5]
    if not last5:
        status = "no data"
    elif all(a.ok for a in last5):
        status = "healthy"
    elif not any(a.ok for a in last5):
        status = "down"
    else:
        status = "degraded"

    refunds = {"paypal_refund": [0, Decimal("0")], "mock_refund": [0, Decimal("0")]}
    rows = db.execute(
        select(Payout.provider, Compensation.amount)
        .join(Compensation, Compensation.id == Payout.compensation_id)
        .where(Payout.status == "completed")
    )
    for provider, amount in rows:
        if provider in refunds:
            refunds[provider][0] += 1
            refunds[provider][1] += amount

    return {
        "service": {
            "status": status,
            "recent": [
                {"id": a.id, "customer_id": a.customer_id, "ok": a.ok, "latency_ms": a.latency_ms,
                 "error": a.error, "incident_id": a.incident_id, "at": a.created_at}
                for a in recent
            ],
        },
        "kpis": {
            "incidents_total": _count(db, select(func.count()).select_from(Incident)),
            "incidents_open": _count(db, select(func.count()).select_from(Incident).where(Incident.status.in_(OPEN_STATUSES))),
            "attempts_total": _count(db, select(func.count()).select_from(Attempt)),
            "attempts_failed": _count(db, select(func.count()).select_from(Attempt).where(Attempt.ok.is_(False))),
            "refunds_real_count": refunds["paypal_refund"][0],
            "refunds_real_usd": str(refunds["paypal_refund"][1]),
            "refunds_mock_count": refunds["mock_refund"][0],
            "refunds_mock_usd": str(refunds["mock_refund"][1]),
        },
    }
