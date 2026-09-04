"""FastAPI dependencies shared across route modules."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from cmo_platform.db.base import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session scoped to one request, closed afterward regardless of outcome."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
