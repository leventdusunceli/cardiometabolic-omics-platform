"""Functions for executing analysis and recording it in analysis_runs

Called by Prefect flows. Allows the system to have a provenance feature
"""

from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy import insert
from sqlalchemy.orm import Session, sessionmaker

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

logger = logging.getLogger(__name__)

DE_INSERT_CHUNK_SIZE = 5_000


def run_differential_expression_for_tissue(
    tissue: str,
    triggered_via: TriggeredVia,
    session_factory: sessionmaker[Session] = SessionLocal,
) -> int:
    """Run pydeseq2 DE for one tissue's CASE vs CONTROL samples and return the analysis_run_id.

    The AnalysisRun row is committed as RUNNING before the fit starts, so a crash mid-fit still
    leaves a durable FAILED record. Results are a plain bulk insert
    """
    session = session_factory()
    analysis_run = AnalysisRun(
        type=AnalysisType.DIFFERENTIAL_EXPRESSION,
        parameters={"tissue": tissue},
        status=AnalysisStatus.RUNNING,
        triggered_via=triggered_via,
    )
    session.add(analysis_run)
    session.commit()
    analysis_run_id: int = analysis_run.id
    logger.info(
        "differential expression started: tissue=%s analysis_run_id=%d", tissue, analysis_run_id
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
        for start in range(0, len(records), DE_INSERT_CHUNK_SIZE):
            session.execute(
                insert(DifferentialExpressionResult),
                records[start : start + DE_INSERT_CHUNK_SIZE],
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
            "differential expression failed: tissue=%s analysis_run_id=%d",
            tissue,
            analysis_run_id,
        )
        raise
    finally:
        session.close()

    logger.info(
        "differential expression completed: tissue=%s analysis_run_id=%d genes=%d",
        tissue,
        analysis_run_id,
        len(records),
    )
    return analysis_run_id
