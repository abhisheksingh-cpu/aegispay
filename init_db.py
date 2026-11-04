
from sqlalchemy import select

from database import Base, engine, SessionLocal
from models import (
    Incident,
    IncidentHistory,
    Payment,
    IncidentPayment,
    Compensation,
    Payout,
)


Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    incidents = db.scalars(
        select(Incident).order_by(Incident.id)
    ).all()

    for incident in incidents:
        existing_history = db.scalar(
            select(IncidentHistory.id)
            .where(
                IncidentHistory.incident_id == incident.id
            )
            .limit(1)
        )

        if existing_history is None:
            db.add(
                IncidentHistory(
                    incident_id=incident.id,
                    status=incident.status,
                )
            )

    db.commit()

print("Database tables created successfully.")
print("Existing incident history initialized.")
