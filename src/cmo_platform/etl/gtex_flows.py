"""First Prefect flow of the project. 
fetch_gtex_tissue -> qc_and_normalize -> load_to_warehouse  
This flow is aimed to be used for GTEx tissues."""

from __future__ import annotations

import logging
from typing import Any

from prefect import flow, task
from sqlalchemy.orm import Session, sessionmaker

from cmo_platform.db.base import SessionLocal
from cmo_platform.etl.gtex_client import GtexMedianExpression, fetch_gtex_tissue
from cmo_platform.etl.gtex_loader import load_to_warehouse
from cmo_platform.etl.gtex_qc import qc_and_normalize

logger = logging.getLogger(__name__)

TARGET_TISSUES = [
    "Liver",
    "Adipose_Subcutaneous",
    "Small_Intestine_Terminal_Ileum",
    "Whole_Blood",
]

@task(retries=2, retry_delay_seconds=5)
def fetch_task(tissue:str)-> list[GtexMedianExpression]: 
    return fetch_gtex_tissue(tissue)

@task
def qc_task(
    tissue: str, records: list[GtexMedianExpression]
) -> tuple[list[GtexMedianExpression], dict[str, Any]]:
    kept, summary = qc_and_normalize(records)
    logger.info("qc_and_normalize tissue=%s kept=%d/%d", tissue, len(kept), len(records))
    return kept, summary

@task
def load_task(tissue: str,
    records: list[GtexMedianExpression],
    qc_summary: dict[str, Any],
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    try: 
        load_to_warehouse(tissue,records,session,qc_metrics=qc_summary)
    finally: 
        session.close()

@flow(name='ingest-gtex-tissue')
def ingest_gtex_tissue(
    tissue: str, session_factory: sessionmaker[Session]=SessionLocal
) -> None: 
    records = fetch_task(tissue)
    kept, qc_summary = qc_task(tissue,records)
    load_task(tissue,records,qc_summary,session_factory)

@flow(name="ingest-gtex-baseline")
def ingest_gtex_baseline(
    tissues: list[str] | None = None, session_factory: sessionmaker[Session] = SessionLocal
) -> None:
    for tissue in tissues or TARGET_TISSUES:
        ingest_gtex_tissue(tissue, session_factory)

if __name__ == "__main__": 
    ingest_gtex_baseline()
    