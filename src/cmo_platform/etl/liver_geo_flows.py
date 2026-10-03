"""Prefect flow for triggering ingestion of liver study data and DE analysis

The flow allows us to perform the duties of the following tasks all at once:
fetch_liver_geo_dataset() -> qc_filter_samples() -> normalize_counts_deseq2() ->
-> load_geo_dataset_to_warehouse() -> run_differential_expression_for_tissue()
"""

from __future__ import annotations

import logging

import pandas as pd
from prefect import flow, task
from prefect.cache_policies import NO_CACHE
from sqlalchemy.orm import Session, sessionmaker

from cmo_platform.db.base import SessionLocal
from cmo_platform.db.models import TriggeredVia
from cmo_platform.etl.geo_loader import load_geo_dataset_to_warehouse
from cmo_platform.etl.geo_qc import normalize_counts_deseq2, qc_filter_samples
from cmo_platform.etl.liver_geo import LIVER_GEO_ACCESSION, fetch_liver_geo_dataset
from cmo_platform.jobs.executors import run_differential_expression_for_tissue

logger = logging.getLogger(__name__)

LIVER_TITLE = "GSE126848 liver bulk RNA-seq (NAFLD/NASH)"
LIVER_CITATION = "PMID 30653341"
LIVER_TISSUE = "Liver"


@task(retries=2, retry_delay_seconds=5, cache_policy=NO_CACHE)
def fetch_task() -> tuple[pd.DataFrame, pd.DataFrame]:
    return fetch_liver_geo_dataset()


@task(cache_policy=NO_CACHE)
def qc_task(counts: pd.DataFrame, samples: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    kept_counts, kept_samples, qc_summary = qc_filter_samples(counts, samples)
    logger.info(
        "qc_filter_samples tissue=%s kept=%d/%d",
        LIVER_TISSUE,
        qc_summary["kept_sample_count"],
        qc_summary["input_sample_count"],
    )
    return kept_counts, kept_samples


@task(cache_policy=NO_CACHE)
def normalize_task(
    counts: pd.DataFrame,
) -> pd.DataFrame:
    normalized_counts, _size_factors = normalize_counts_deseq2(counts)
    return normalized_counts


@task(cache_policy=NO_CACHE)
def load_task(
    counts: pd.DataFrame,
    normalized_counts: pd.DataFrame,
    samples: pd.DataFrame,
    session_factory: sessionmaker[Session],
) -> None:
    session = session_factory()
    try:
        load_geo_dataset_to_warehouse(
            accession=LIVER_GEO_ACCESSION,
            title=LIVER_TITLE,
            citation=LIVER_CITATION,
            tissue=LIVER_TISSUE,
            counts=counts,
            normalized_counts=normalized_counts,
            samples=samples,
            session=session,
        )
    finally:
        session.close()


@task(cache_policy=NO_CACHE)
def de_task(session_factory: sessionmaker[Session]) -> int:
    analysis_run_id = run_differential_expression_for_tissue(
        LIVER_TISSUE, triggered_via=TriggeredVia.ETL, session_factory=session_factory
    )
    logger.info(
        "differential expression finished tissue=%s analysis_run_id=%d",
        LIVER_TISSUE,
        analysis_run_id,
    )
    return analysis_run_id


@flow(name="ingest-liver-geo")
def ingest_liver_geo(session_factory: sessionmaker[Session] = SessionLocal) -> int:
    counts, samples = fetch_task()
    kept_counts, kept_samples = qc_task(counts, samples)
    normalized_counts = normalize_task(kept_counts)
    load_task(kept_counts, normalized_counts, kept_samples, session_factory)
    return de_task(session_factory)


if __name__ == "__main__":
    ingest_liver_geo()
