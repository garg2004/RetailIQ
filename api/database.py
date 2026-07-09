"""
database.py
------------
PostgreSQL connection handling for the RetailIQ API using SQLAlchemy.

Connection details are read from environment variables so the same code
works locally and in any deployment environment - never hardcode
credentials in source code.

Expected env vars (create a .env file locally - see .env.example):
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=retailiq
    DB_USER=postgres
    DB_PASSWORD=yourpassword
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "retailiq")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# DEMO_MODE lets the API run against a local SQLite file (auto-built from the
# cleaned CSVs) with zero setup - handy for quickly testing endpoints or for
# grading without installing PostgreSQL. Production/real usage should set
# DEMO_MODE=false and point DB_HOST/etc at a real Postgres instance.
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

if DEMO_MODE:
    DATABASE_URL = "sqlite:///./retailiq_demo.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency - yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
