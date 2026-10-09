"""Load GEO expression data into the warehouse.
A separate loader script/method is needed from gtex_loader.py because
the loop logic of that script is not efficient for the dataset sizes we're loading from GEO
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from cmo_platform.db.models import (
    ConditionCategory,
    Dataset,
    DatasetSource,
    ExpressionUnit,
    ExpressionValue,
    Gene,
    Sample,
    Sex,
)
from cmo_platform.db.upsert import bulk_upsert

_SEX_BY_GENDER = {"male": Sex.MALE, "female": Sex.FEMALE}


def _get_or_create_dataset(accession: str, title: str, citation: str, session: Session) -> Dataset:
    dataset = session.query(Dataset).filter_by(accession=accession).one_or_none()
    if dataset is None:
        dataset = Dataset(
            accession=accession,
            source=DatasetSource.GEO,
            title=title,
            assay_type="bulk RNA-seq",
            citation=citation,
        )
        session.add(dataset)
        session.flush()
    return dataset


def _upsert_samples(
    dataset: Dataset, tissue: str, samples: pd.DataFrame, session: Session
) -> dict[str, int]:
    """Upsert one Sample row per real donor. Returns {geo_accession: sample.id}."""
    sample_ids: dict[str, int] = {}
    for geo_accession, row in samples.iterrows():
        sample = (
            session.query(Sample)
            .filter_by(dataset_id=dataset.id, source_sample_id=geo_accession)
            .one_or_none()
        )
        sex = _SEX_BY_GENDER.get(str(row.get("gender", "")).lower(), Sex.UNKNOWN)
        condition_category = ConditionCategory(row["condition_category"])

        if sample is None:
            sample = Sample(
                dataset=dataset,
                tissue=tissue,
                condition=row["disease"],
                condition_category=condition_category,
                sex=sex,
                source_sample_id=geo_accession,
                qc_metrics=row["qc_metrics"],
            )
            session.add(sample)
            session.flush()
        else:
            sample.condition = row["disease"]
            sample.condition_category = condition_category
            sample.sex = sex
            sample.qc_metrics = row["qc_metrics"]

        sample_ids[str(geo_accession)] = sample.id
    return sample_ids


def _upsert_genes(gene_ids: list[str], session: Session) -> None:
    """Ensure every id in `gene_ids` has a Gene row. New rows get symbol=None."""
    bulk_upsert(session, Gene, [{"ensembl_gene_id": g} for g in gene_ids], ["ensembl_gene_id"], [])


def _upsert_expression_values(
    counts: pd.DataFrame,
    normalized_counts: pd.DataFrame,
    sample_ids: dict[str, int],
    session: Session,
    chunk_size: int = 5_000,
) -> None:
    """Bulk upsert method for GEO data, different from the ORM logic for Gtex data
    due to inefficiencies arising from large GEO dataset size"""

    # editing raw count matrix to fit our upsert schema
    raw_long = counts.stack()
    raw_long.index.names = ["accession", "gene_id"]
    normalized_long = normalized_counts.stack()
    normalized_long.index.names = ["accession", "gene_id"]

    rows = pd.DataFrame({"raw_count": raw_long, "normalized_value": normalized_long}).reset_index()
    rows["sample_id"] = rows["accession"].map(sample_ids)
    rows["unit"] = ExpressionUnit.DESEQ2_NORMALIZED

    records = rows[["sample_id", "gene_id", "raw_count", "normalized_value", "unit"]].to_dict(
        "records"
    )
    # upsert gene expression while synching ensembl IDs with HGNC IDs
    bulk_upsert(
        session,
        ExpressionValue,
        records,
        conflict_columns=["sample_id", "gene_id"],
        update_columns=["raw_count", "normalized_value", "unit"],
        chunk_size=chunk_size,
    )


def load_geo_dataset_to_warehouse(
    accession: str,
    title: str,
    citation: str,
    tissue: str,
    counts: pd.DataFrame,
    normalized_counts: pd.DataFrame,
    samples: pd.DataFrame,
    session: Session,
) -> None:
    """Upsert one GEO dataset's sample raw counts+ DESeq2-normalized expression into the
    warehouse. `counts`, `normalized_counts`, and `samples` must all share the same index
    (GSM accession), as produced by qc_filter_samples + normalize_counts_deseq2.
    """
    dataset = _get_or_create_dataset(accession, title, citation, session)
    sample_ids = _upsert_samples(dataset, tissue, samples, session)
    _upsert_genes(list(counts.columns), session)
    _upsert_expression_values(counts, normalized_counts, sample_ids, session)
    session.commit()
