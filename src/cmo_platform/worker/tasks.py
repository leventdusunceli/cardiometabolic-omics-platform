"""Celery tasks. `ping` is a placeholder proving the queue is wired correctly end to end;
real analysis tasks (run_differential_expression, etc.) land once GEO
ingestion provides data to analyze."""

from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy import insert

from cmo_platform.analysis.differential_expression import (
    load_case_control_matrix,
    run_deseq2_differential_expression,
)
from cmo_platform.db.base import SessionLocal
from cmo_platform.db.models import (
    AnalysisRun,
    AnalysisStatus,
    AnalysisType,
    DifferentialExpressionResult,
    TriggeredVia,
)
from cmo_platform.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="cmo_platform_ping")
def ping(message: str = "pong") -> str:
    logger.info("ping task receieved: %s", message)
    return message


@celery_app.task(name="cmo_platform_run_differential_expression")
def run_differential_expression(tissue: str, triggered_via: str = "api") -> int:
    """Celery task for performing DE analysis for one tissue's CASE vs CONTROL using
    the run_deseq2_differential_expression method within the /cmo_platform/analysis pipeline

    This celery task also records the run status into the analysis_runs table within the database.
    Allows us to trace back each initiated run and see the run parameters.
    """
    session = SessionLocal()
    analysis_run = AnalysisRun(
        type=AnalysisType.DIFFERENTIAL_EXPRESSION,
        parameters={"tissue": tissue},
        status=AnalysisStatus.RUNNING,
        triggered_via=TriggeredVia(triggered_via),
    )
    session.add(analysis_run)
    session.commit()
    analysis_run_id: int = analysis_run.id
    logger.info(
        "run_differential_expression started: tissue=%s analysis_run_id=%d", tissue, analysis_run_id
    )

    try:
        counts, condition_category = load_case_control_matrix(tissue, session)
        results = run_deseq2_differential_expression(counts, condition_category)

        records: list[dict[str, int | str | float]] = [
            {
                "analysis_run_id": analysis_run_id,
                "gene_id": str(gene_id),
                "tissue": tissue,
                "log2_fold_change": row.log2FoldChange,
                "pvalue": row.pvalue,
                "padj": row.padj,
            }
            for gene_id, row in results.iterrows()
        ]
        chunk_size = 5_000
        for start in range(0, len(records), chunk_size):
            session.execute(
                insert(DifferentialExpressionResult), records[start : start + chunk_size]
            )

        analysis_run.status = AnalysisStatus.COMPLETED
        analysis_run.completed_at = dt.datetime.now(dt.UTC)
        session.commit()
    except Exception:
        session.rollback()
        analysis_run.status = AnalysisStatus.FAILED
        analysis_run.completed_at = dt.datetime.now(dt.UTC)
        session.commit()
        logger.exception(
            "run_differential_expression failed: tissue=%s analysis_run_id=%d",
            tissue,
            analysis_run_id,
        )
        raise
    finally:
        session.close()

    logger.info(
        "run_differential_expression completed: tissue=%s analysis_run_id=%d genes=%d",
        tissue,
        analysis_run_id,
        len(records),
    )
    return analysis_run_id
