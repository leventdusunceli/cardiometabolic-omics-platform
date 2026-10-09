"""Preferct flow for laoding HGNC gene annotations into the 'genes' reference table"""

from __future__ import annotations

import logging

import pandas as pd
from prefect import flow, task
from prefect.cache_policies import NO_CACHE
from sqlalchemy.orm import Session, sessionmaker

from cmo_platform.db.base import SessionLocal
from cmo_platform.etl.gene_annotation import fetch_hgnc_genes, load_gene_annotation

logger = logging.getLogger(__name__)


@task(retries=2, retry_delay_seconds=5, cache_policy=NO_CACHE)
def fetch_task() -> pd.DataFrame:
    return fetch_hgnc_genes()


@task(cache_policy=NO_CACHE)
def load_task(genes: pd.DataFrame, session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    try:
        load_gene_annotation(genes, session)
    finally:
        session.close()
    logger.info("load_gene_annotation upserted %d HGNC genes", len(genes))


@flow(name="load-gene-annotation")
def load_gene_annotation_flow(session_factory: sessionmaker[Session] = SessionLocal) -> None:
    load_task(fetch_task(), session_factory)


if __name__ == "__main__":
    load_gene_annotation_flow()
