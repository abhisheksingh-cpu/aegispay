
from sqlalchemy import create_engine, text

DATABASE_URL = DATABASE_URL = "postgresql+psycopg://aegis:aegis_dev_password@127.0.0.1:5433/aegispay"

engine = create_engine(DATABASE_URL)

with engine.connect() as connection:
    result = connection.execute(text("SELECT version()"))
    print(result.scalar())

engine.dispose()
