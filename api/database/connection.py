from __future__ import annotations
import os
from collections.abc import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from api.database.models import Base

def _build_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    user = os.environ.get("PGUSER", "aidss")
    password = os.environ.get("PGPASSWORD", "aidss")
    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    dbname = os.environ.get("PGDATABASE", "aidss")
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

_DATABASE_URL = _build_database_url()

_engine = create_engine(
    _DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
    max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "10")),
    echo=os.environ.get("SQL_ECHO", "0") == "1",
)

_SessionFactory = sessionmaker(bind=_engine, autocommit=False, autoflush=False)

def get_engine():
    return _engine

def get_session_factory() -> sessionmaker:
    return _SessionFactory

def get_db() -> Generator[Session, None, None]:
    db: Session = _SessionFactory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db() -> None:
    try:
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise RuntimeError(
            "Database unreachable at startup. "
            "Is docker-compose.dev.yml running?\n"
            f"  URL: {_DATABASE_URL!r}\n"
            f"  Error: {exc}"
        ) from exc

    env = os.environ.get("AIDSS_ENV", "development")
    if env == "development":
        Base.metadata.create_all(bind=_engine)
