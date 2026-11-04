
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://aegis:aegis_dev_password@127.0.0.1:5433/aegispay",
)


engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

