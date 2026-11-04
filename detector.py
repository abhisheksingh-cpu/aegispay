"""Deterministic incident detection from payment attempts. No AI, fully inspectable."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Attempt, Incident, IncidentHistory, IncidentPayment, Payment

OPEN_STATUSES = ("open", "investigating", "identified", "remediating")
OPEN_AFTER = 3   # consecutive failed attempts that open an incident
CLOSE_AFTER = 5  # consecutive healthy attempts needed to confirm recovery


def severity_for(failed_attempts: int) -> str:
    """Demo thresholds, not real SLA terms."""
    if failed_attempts >= 10:
        return "critical"
    if failed_attempts >= 6:
        return "high"
    return "medium" if failed_attempts >= 3 else "low"


def evaluate(db: Session, service: str) -> int | None:
    """Update incident state after a new attempt. Returns the open incident id, if any."""
    recent = db.scalars(
        select(Attempt).where(Attempt.service == service)
        .order_by(Attempt.id.desc()).limit(CLOSE_AFTER)
    ).all()
    incident = db.scalar(
        select(Incident).where(Incident.service == service, Incident.status.in_(OPEN_STATUSES))
        .order_by(Incident.id.desc())
    )

    if incident is None:  # dedupe: a new incident only if none is already open
        last = recent[:OPEN_AFTER]
        if len(last) == OPEN_AFTER and not any(a.ok for a in last):
            incident = Incident(
                service=service, status="open", severity="low",
                reason=f"{OPEN_AFTER} consecutive failed payment attempts",
            )
            db.add(incident)
            db.flush()
            db.add(IncidentHistory(incident_id=incident.id, status="open"))
            for a in last:
                a.incident_id = incident.id
    else:
        recent[0].incident_id = incident.id
        if len(recent) == CLOSE_AFTER and all(a.ok for a in recent):
            _resolve(db, incident)
            incident = None

    db.commit()
    return incident.id if incident else None


def _resolve(db: Session, incident: Incident) -> None:
    """Recovery verified by healthy customer traffic. Link affected payments using evidence."""
    failed = db.scalars(
        select(Attempt).where(Attempt.incident_id == incident.id, Attempt.ok.is_(False))
    ).all()
    incident.severity = severity_for(len(failed))
    incident.status = "resolved"
    db.add(IncidentHistory(incident_id=incident.id, status="resolved"))

    by_customer: dict[str, list[int]] = {}
    for a in failed:
        by_customer.setdefault(a.customer_id, []).append(a.id)

    for customer, ids in by_customer.items():
        payment = db.scalar(  # the customer's captured fee payment is the credit anchor
            select(Payment)
            .where(Payment.customer_id == customer, Payment.capture_id.is_not(None))
            .order_by(Payment.id.desc())
        )
        if payment is not None:
            db.add(IncidentPayment(
                incident_id=incident.id, payment_id=payment.id,
                impact_reason=f"{len(ids)} failed payment attempts during incident (attempt ids {ids[:10]})"[:500],
            ))
