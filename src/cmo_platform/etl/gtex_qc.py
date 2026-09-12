"""QC and normalization step between fetching and loading GTEx data.

GTEx's medianGeneExpression endpoint already returns population-median TPM values, there are no raw
counts or per-donor library sizes for us to see, so there is no meaningful normalization left to do
here (unlike a future GEO ingestion, which will need pydeseq2-based normalization from raw
counts). This task still validates the data is what we expect and records a QC summary as
provenance, for good coding practices.
"""

from __future__ import annotations

import logging
from typing import Any

from cmo_platform.etl.gtex_client import GtexMedianExpression

logger = logging.getLogger(__name__)

EXPECTED_UNIT = "TPM"


def qc_and_normalize(
    records: list[GtexMedianExpression],
) -> tuple[list[GtexMedianExpression], dict[str, Any]]:
    """Validate GTEx records and produce a QC summary; drop any record that fails validation.

    Returns the (possibly filtered) records plus a summary dict suitable for storing in
    Sample.qc_metrics, documenting what was checked and what, if anything, was dropped.
    """
    kept: list[GtexMedianExpression] = []
    dropped: list[dict[str, Any]] = []

    for record in records:
        if record.unit != EXPECTED_UNIT:
            dropped.append(
                {"gene_symbol": record.gene_symbol, "reason": f"unexpected unit {record.unit!r}"}
            )
            continue
        if record.median < 0:
            dropped.append(
                {"gene_symbol": record.gene_symbol, "reason": f"negative median {record.median}"}
            )
            continue
        kept.append(record)

    if dropped:
        logger.warning(
            "qc_and_normalize dropped %d/%d records: %s", len(dropped), len(records), dropped
        )

    detected_gene_count = sum(1 for r in kept if r.median > 0)

    qc_summary: dict[str, Any] = {
        "aggregation": "population_median",
        "source": "gtex_median_gene_expression",
        "normalization": "none_required_pre_normalized_tpm_from_gtex_portal",
        "input_gene_count": len(records),
        "kept_gene_count": len(kept),
        "detected_gene_count": detected_gene_count,
        "dropped_records": dropped,
    }
    return kept, qc_summary
