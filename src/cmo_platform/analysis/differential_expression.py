"""Differential expression analysis script. Methods read 
a tissue's CASE/CONTROL data from the Postgres database. Then
runs pydeseq2 statistical DE model against it.

Designed as a separate part from the ETL flow of the package
"""

from __future__ import annotations

import pandas as pd
from pydeseq2.dds import DeseqDataSet
from pydeseq2.ds import DeseqStats
from sqlalchemy import select
from sqlalchemy.orm import Session

from cmo_platform.db.models import ConditionCategory, ExpressionValue, Sample


def load_case_control_matrix(tissue:str, session:Session)->tuple[pd.DataFrame, pd.Series]:
    """Returns (raw counts. condition_category) for one tissue's CASE/CONTROL samples
    pydeseq2 requires raw counts as input and not normalized counts.
    """

    rows = session.execute(
        select(
            ExpressionValue.sample_id,
            ExpressionValue.gene_id,
            ExpressionValue.raw_count,
            Sample.condition_category,
        )
        .join(Sample, Sample.id == ExpressionValue.sample_id)
        .where(
            Sample.tissue == tissue,
            Sample.condition_category.in_([ConditionCategory.CASE, ConditionCategory.CONTROL]),
        )
    ).all()

    long = pd.DataFrame(rows, columns=["sample_id", "gene_id", "raw_count", "condition_category"])
    counts = long.pivot(index="sample_id", columns="gene_id", values="raw_count")
    condition_category = (
        long.drop_duplicates("sample_id").set_index("sample_id")["condition_category"]
    )
    return counts, condition_category

def run_deseq2_differential_expression(
        counts: pd.DataFrame, condition_category:pd.Series
)-> pd.DataFrame: 
    """Fit pydeseq2;s DEseq2 model for a CASE vs CONTROL DE analysis. 
    
    Returns a DataFrame of Benjamin-Hochberg-corrected DE results. 
    DataFrame is indexed by gene_id and has log2FoldCahnge, pvalue and 
    Benjamin-Hochberg-corrected padj columns. There's also an additional filtering
    included, dropping genes with NaN padj values (genes with too low mean count)
    """
    metadata = pd.DataFrame({"condition_category": condition_category.astype(str)})
    dds = DeseqDataSet(
        counts=counts,
        metadata=metadata,
        design="~condition_category",
        quiet=True,
    )
    dds.deseq2()

    stats = DeseqStats(dds, contrast=["condition_category", "case", "control"], quiet=True)
    stats.summary()

    results: pd.DataFrame = stats.results_df[["log2FoldChange", "pvalue", "padj"]].dropna(
    subset=["padj"]
    )
    return results

