"""Chunk 'insert, or update if row exists' for any table

Works for Postgres or SQLite. This allows our upsert functions to have a shared helper,
reducing the number of loops needed. This allows us to write tests for upsert functions
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session

from cmo_platform.db.base import Base


def bulk_upsert(
    session: Session,
    model: type[Base],
    records: Sequence[Mapping[Any, Any]],
    conflict_columns: list[str],
    update_columns: list[str],
    chunk_size: int = 5_000,
) -> None:
    """Insert gene values in bulk. A gene value that has a matching row in 'conflict_columns'
    updates that row's 'update_columns'.

    This will also be used in adding gene symbols for genes that have ensembl ID but no matching
    HGNC gene symbol.
    """
    insert = postgresql.insert if session.get_bind().dialect.name == "postgresql" else sqlite.insert
    for start in range(0, len(records), chunk_size):
        stmt = insert(model).values(records[start : start + chunk_size])
        if update_columns:
            stmt = stmt.on_conflict_do_update(
                index_elements=conflict_columns,
                set_={column: stmt.excluded[column] for column in update_columns},
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=conflict_columns)
        session.execute(stmt)
