from datetime import datetime
from decimal import Decimal
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from compensation_rules import COMPENSATION_RATES, calculate_compensation
from database import get_db
from evidence import router as evidence_router
from overview import router as overview_router
from demo import router as demo_router
from ui import router as ui_router
from models import Compensation, Incident, IncidentHistory, IncidentPayment, Payment, Payout
from settlement import settle


app = FastAPI(title="AegisPay API")
app.include_router(evidence_router)
app.include_router(overview_router)
app.include_router(demo_router)
app.include_router(ui_router)


IncidentStatus = Literal[
    "open",
    "investigating",
    "identified",
    "remediating",
    "resolved",
]



class PayoutResponse(BaseModel):
    id: int
    compensation_id: int
    idempotency_key: str
    provider: str
    provider_payout_id: str | None
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ---------- Request schemas ----------


class CompensationResponse(BaseModel):
    id: int
    incident_id: int
    payment_id: int
    amount: Decimal
    currency: str
    status: str
    decision_reason: str
    rule_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentCreate(BaseModel):
    customer_id: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: Literal["INR", "USD"] = "USD"


class PaymentResponse(BaseModel):
    id: int
    customer_id: str
    capture_id: str | None = None
    amount: Decimal
    currency: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IncidentCreate(BaseModel):
    service: str = Field(min_length=1, max_length=100)
    severity: Literal["low", "medium", "high", "critical"]
    reason: str = Field(min_length=1, max_length=500)


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


# ---------- Response schemas ----------

class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service: str
    status: str
    severity: Literal["low", "medium", "high", "critical"]
    reason: str


class IncidentHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    status: str
    changed_at: datetime


# ---------- Basic endpoints ----------

@app.get("/")
def home():
    return {"message": "AegisPay backend is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---------- Incident endpoints ----------

@app.post(
    "/incidents",
    status_code=status.HTTP_201_CREATED,
    response_model=IncidentResponse,
)
def create_incident(
    incident: IncidentCreate,
    db: Session = Depends(get_db),
):
    new_incident = Incident(
        service=incident.service,
        status="open",
        severity=incident.severity,
        reason=incident.reason,
    )

    try:
        db.add(new_incident)
        db.flush()

        # Record the initial status in the history table.
        db.add(
            IncidentHistory(
                incident_id=new_incident.id,
                status=new_incident.status,
            )
        )

        db.commit()
        db.refresh(new_incident)
        return new_incident

    except Exception:
        db.rollback()
        raise


@app.get(
    "/incidents",
    response_model=list[IncidentResponse],
)
def get_incidents(db: Session = Depends(get_db)):
    return db.scalars(
        select(Incident).order_by(Incident.id)
    ).all()


@app.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return incident


@app.patch(
    "/incidents/{incident_id}/status",
    response_model=IncidentResponse,
)
def update_incident_status(
    incident_id: int,
    update: IncidentStatusUpdate,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    try:
        if incident.status != update.status:
            incident.status = update.status

            db.add(
                IncidentHistory(
                    incident_id=incident.id,
                    status=update.status,
                )
            )

        db.commit()
        db.refresh(incident)
        return incident

    except Exception:
        db.rollback()
        raise


@app.get(
    "/incidents/{incident_id}/history",
    response_model=list[IncidentHistoryResponse],
)
def get_incident_history(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    history = db.scalars(
        select(IncidentHistory)
        .where(IncidentHistory.incident_id == incident_id)
        .order_by(
            IncidentHistory.changed_at,
            IncidentHistory.id,
        )
    ).all()

    return history


@app.delete("/incidents/{incident_id}")
def delete_incident(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    try:
        db.delete(incident)
        db.commit()

        return {
            "message": "Incident deleted successfully",
            "incident_id": incident_id,
        }

    except Exception:
        db.rollback()
        raise


@app.post("/payments", response_model=PaymentResponse, status_code=201)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
):
    payment = Payment(
        customer_id=payment_data.customer_id,
        amount=payment_data.amount,
        currency=payment_data.currency,
        status="pending",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


@app.get("/payments", response_model=list[PaymentResponse])
def get_payments(
    db: Session = Depends(get_db),
):
    payments = db.scalars(
        select(Payment).order_by(Payment.id.desc())
    ).all()

    return payments


@app.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
):
    payment = db.get(Payment, payment_id)

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment


class IncidentPaymentCreate(BaseModel):
    payment_id: int = Field(gt=0)
    impact_reason: str = Field(min_length=1, max_length=500)


class IncidentPaymentResponse(BaseModel):
    id: int
    incident_id: int
    payment_id: int
    impact_reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

@app.get(
    "/payouts/{payout_id}",
    response_model=PayoutResponse,
)
def get_payout(
    payout_id: int,
    db: Session = Depends(get_db),
):
    payout = db.get(Payout, payout_id)

    if payout is None:
        raise HTTPException(
            status_code=404,
            detail="Payout not found",
        )

    return payout


@app.get(
    "/payouts",
    response_model=list[PayoutResponse],
)
def list_payouts(
    db: Session = Depends(get_db),
):
    payouts = db.scalars(
        select(Payout).order_by(Payout.id.desc())
    ).all()

    return payouts


@app.post(
    "/incidents/{incident_id}/payments",
    response_model=IncidentPaymentResponse,
    status_code=201,
)
def link_payment_to_incident(
    incident_id: int,
    link_data: IncidentPaymentCreate,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    payment = db.get(Payment, link_data.payment_id)
    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    existing = db.scalar(
        select(IncidentPayment).where(
            IncidentPayment.incident_id == incident_id,
            IncidentPayment.payment_id == link_data.payment_id,
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Payment is already linked to this incident",
        )

    link = IncidentPayment(
        incident_id=incident_id,
        payment_id=link_data.payment_id,
        impact_reason=link_data.impact_reason,
    )

    db.add(link)

    try:
        db.commit()
        db.refresh(link)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Payment is already linked to this incident",
        )

    return link


@app.post(
    "/incidents/{incident_id}/compensations",
    response_model=list[CompensationResponse],
    status_code=201,
)
def create_compensations(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    if incident.status != "resolved":
        raise HTTPException(
            status_code=409,
            detail="Incident must be resolved before compensation",
        )

    links = db.scalars(
        select(IncidentPayment).where(
            IncidentPayment.incident_id == incident_id
        )
    ).all()

    if not links:
        raise HTTPException(
            status_code=409,
            detail="No payments are linked to this incident",
        )

    created_records = []

    try:
        for link in links:
            existing = db.scalar(
                select(Compensation).where(
                    Compensation.incident_id == incident_id,
                    Compensation.payment_id == link.payment_id,
                )
            )

            if existing is not None:
                continue

            payment = db.get(Payment, link.payment_id)

            if payment is None:
                continue

            amount, rule_version = calculate_compensation(
                payment.amount,
                incident.severity,
            )

            rate = COMPENSATION_RATES[incident.severity.lower()]

            if rate == Decimal("0.00"):
                status = "ineligible"
                reason = (
                    f"Severity '{incident.severity}' has no compensation "
                    f"under policy {rule_version}."
                )
            else:
                status = "eligible"
                reason = (
                    f"Policy {rule_version}: {rate * 100}% of payment "
                    f"{payment.id} for a {incident.severity} incident."
                )

            record = Compensation(
                incident_id=incident_id,
                payment_id=payment.id,
                amount=amount,
                currency=payment.currency,
                status=status,
                decision_reason=reason,
                rule_version=rule_version,
            )

            db.add(record)
            created_records.append(record)

        db.commit()

        for record in created_records:
            db.refresh(record)

    except Exception:
        db.rollback()
        raise

    return created_records



@app.post(
    "/compensations/{compensation_id}/refund",
    response_model=PayoutResponse,
    status_code=201,
)
def refund_compensation(
    compensation_id: int,
    db: Session = Depends(get_db),
):
    compensation = db.get(Compensation, compensation_id)

    if compensation is None:
        raise HTTPException(status_code=404, detail="Compensation not found")

    if compensation.status != "eligible":
        raise HTTPException(
            status_code=409,
            detail="Only eligible compensations can be paid",
        )

    return settle(db, compensation)


@app.get(
    "/incidents/{incident_id}/compensations",
    response_model=list[CompensationResponse],
)
def list_compensations(incident_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(Compensation)
        .where(Compensation.incident_id == incident_id)
        .order_by(Compensation.id)
    ).all()
