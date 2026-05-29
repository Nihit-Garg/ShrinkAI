"""
SQLAlchemy engine, session factory, and declarative base.
All database table operations use this — the Supabase client is only used for Auth.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # Reconnect on stale connections
    pool_size=5,
    max_overflow=10,
    echo=settings.env == "development",  # SQL logging in dev
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base — all ORM models inherit from this."""
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
