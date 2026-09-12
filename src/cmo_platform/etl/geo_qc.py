"""Per sample QC methods for GEO count-matrix data. Methods defined here wil be performed before
normalization.  Note that we're using fixed thresholds below (MIN_LIBRARY_SIZE,MIN_DETECTED_GENES)
for cut-off values.  Deriving these numbers based on to dataset distributions would be statistically
more robust but due to our low sample size datasets, the generated medians wouldn't be robust.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from pydeseq2.dds import DeseqDataSet

logger = logging.getLogger(__name__)

# Fixed conventional QC thresholds. Not derived from dataset distribution.
# Worth adjusting once larger datasets are integrated
MIN_LIBRARY_SIZE = 1_000_000
MIN_DETECTED_GENES = 10_000


def qc_filter_samples(
    counts: pd.DataFrame,
    samples: pd.DataFrame,
    min_library_size: int = MIN_LIBRARY_SIZE,
    min_detected_genes: int = MIN_DETECTED_GENES,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Drop samples that fall below library size and detected gene count thersholds
    For this method to work, 'counts' and 'samples' fetched from the
    fetch_tissuex_geo_dataset() method should share the same index (GSM accession number)
    """
    library_size = counts.sum(axis=1)
    detected_genes = (counts > 0).sum(axis=1)
    passed = (library_size >= min_library_size) & (detected_genes >= min_detected_genes)

    samples = samples.copy()
    qc_metrics = [
        {
            "library_size": int(library_size[sample_id]),
            "detected_genes": int(detected_genes[sample_id]),
            "min_library_size": min_library_size,
            "min_detected_genes": min_detected_genes,
        }
        for sample_id in samples.index
    ]
    samples["qc_metrics"] = pd.Series(qc_metrics, index=samples.index, dtype=object)

    dropped = [
        {"sample_id": sample_id, **samples.loc[sample_id, "qc_metrics"]}
        for sample_id in samples.index[~passed]
    ]
    if dropped:
        logger.warning(
            "qc_filter_samples dropped %d/%d samples: %s", len(dropped), len(counts), dropped
        )

    kept_counts = counts.loc[passed]
    kept_samples = samples.loc[passed]

    batch_summary: dict[str, Any] = {
        "min_library_size": min_library_size,
        "min_detected_genes": min_detected_genes,
        "input_sample_count": len(counts),
        "kept_sample_count": int(passed.sum()),
        "dropped_samples": dropped,
    }
    return kept_counts, kept_samples, batch_summary

def normalize_counts_deseq2(counts: pd.DataFrame) -> tuple[pd.DataFrame,pd.Series]: 
    """DESeq2 median-of-ratios normalization. 

    Returns (normalized_counts,size_factors), both indexed the same way as 'counts'
    """
    metadata = pd.DataFrame(index=counts.index)
    dds = DeseqDataSet(counts=counts, metadata=metadata, design="~1", quiet=True)
    dds.fit_size_factors()

    normalized_counts = pd.DataFrame(
        dds.layers['normed_counts'], index = counts.index, columns = counts.columns)
    size_factors: pd.Series = dds.obs['size_factos']
    return normalized_counts, size_factors
