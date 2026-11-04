import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from detector import evaluate
from explain import diagnose
from llm import DEFAULT_MODEL, call_llm
from models import Attempt, Incident, IncidentDiagnosis

router = APIRouter()


class AttemptIn(BaseModel):
    customer_id: str = Field(min_length=1, max_length=100)
    ok: bool
    latency_ms: int = Field(ge=0)
    error: str | None = Field(default=None, max_length=200)
    service: str = "payment-service"


def _evidence(db: Session, incident_id: int) -> list[dict]:
    if db.get(Incident, incident_id) is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    rows = db.scalars(
        select(Attempt)
        .where(Attempt.incident_id == incident_id, Attempt.ok.is_(False))
        .order_by(Attempt.id)
    ).all()
    return [
        {"attempt_id": a.id, "customer_id": a.customer_id, "error": a.error,
         "latency_ms": a.latency_ms, "at": a.created_at}
        for a in rows
    ]


def _diagnosis_dict(d: IncidentDiagnosis) -> dict:
    return {
        "id": d.id, "incident_id": d.incident_id, "source": d.source, "model": d.model,
        "cause": d.cause, "confidence": d.confidence, "summary": d.summary,
        "cited_attempt_ids": [int(x) for x in d.cited_attempt_ids.split(",") if x],
        "tokens": d.tokens, "note": d.note, "created_at": d.created_at,
    }


@router.post("/attempts", status_code=201)
def record_attempt(data: AttemptIn, db: Session = Depends(get_db)):
    attempt = Attempt(**data.model_dump())
    db.add(attempt)
    db.flush()
    return {"attempt_id": attempt.id, "open_incident_id": evaluate(db, data.service)}


@router.get("/incidents/{incident_id}/evidence")
def incident_evidence(incident_id: int, db: Session = Depends(get_db)):
    return _evidence(db, incident_id)


@router.post("/incidents/{incident_id}/diagnosis", status_code=201)
def create_diagnosis(incident_id: int, db: Session = Depends(get_db)):
    out = diagnose(_evidence(db, incident_id), call_llm)
    d = out["diagnosis"]
    record = IncidentDiagnosis(
        incident_id=incident_id, source=out["source"],
        model=os.getenv("GROQ_MODEL", DEFAULT_MODEL) if out["source"] == "llm" else None,
        cause=d.cause, confidence=d.confidence, summary=d.summary,
        cited_attempt_ids=",".join(str(i) for i in d.cited_attempt_ids),
        tokens=out["tokens"], note=out["note"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _diagnosis_dict(record)


@router.get("/incidents/{incident_id}/diagnosis")
def latest_diagnosis(incident_id: int, db: Session = Depends(get_db)):
    record = db.scalar(
        select(IncidentDiagnosis)
        .where(IncidentDiagnosis.incident_id == incident_id)
        .order_by(IncidentDiagnosis.id.desc())
    )
    if record is None:
        raise HTTPException(status_code=404, detail="No diagnosis yet")
    return _diagnosis_dict(record)