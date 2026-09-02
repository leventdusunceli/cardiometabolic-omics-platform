"""Loads GTEx median-expression records (from gtex_client) into the Postgres warehouse.

Idempotent by design: re-running against the same tissue's data must not create duplicates,
since a future Prefect flow will call this repeatedly, not just once.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from cmo_platform.db.models import (
    Dataset,
    DatasetSource,
    ExpressionUnit,
    ExpressionValue,
    Gene,
    Sample,
)
from cmo_platform.etl.gtex_client import GTEX_DEFAULT_DATASET_ID, GtexMedianExpression

# The single documented label every GTEx aggregate sample gets. GTEx's medianGeneExpression
# endpoint returns one value already aggregated across hundreds of donors, not a real
# case/control condition. This string exists so that we can determine which Sample rows are
# GTEx's non-contrastive baseline data versus a future GEO study's real disease/control labels.
GTEX_BASELINE_CONDITION = "population_baseline"


def _strip_gencode_version(gencode_id: str) -> str:
    """ENSG00000132693.12 -> ENSG00000132693.

    The version suffix is GENCODE-release metadata, not part of the gene's identity, and GEO
    datasets won't reliably carry a matching version -- the unversioned form is what `genes`
    (shared across GTEx and GEO) uses as its join key.
    """
    return gencode_id.split(".")[0]


def load_to_warehouse(
    tissue_site_detail_id: str,
    records: list[GtexMedianExpression],
    session: Session,
    dataset_id: str = GTEX_DEFAULT_DATASET_ID,
    qc_metrics: dict[str,object] | None = None,
) -> None:
    """Upsert one tissue's GTEx records into datasets/samples/genes/expression_values."""
    accession = f"{dataset_id}_{tissue_site_detail_id}"
    dataset = session.query(Dataset).filter_by(accession=accession).one_or_none()
    if dataset is None:
        dataset = Dataset(
            accession=accession,
            source=DatasetSource.GTEX,
            title=f"GTEx {dataset_id} median gene expression - {tissue_site_detail_id}",
            assay_type="bulk RNA-seq",
            citation="GTEx Consortium, https://gtexportal.org",
        )
        session.add(dataset)
        session.flush()  # assigns dataset.id without committing yet

    sample = (
        session.query(Sample)
        .filter_by(
            dataset_id=dataset.id, tissue=tissue_site_detail_id, condition=GTEX_BASELINE_CONDITION
        )
        .one_or_none()
    )
    resolved_qc_metrics = qc_metrics or {
        "aggregation": "population_median",
        "source": "gtex_median_gene_expression",
    }
    if sample is None:
        sample = Sample(
            dataset=dataset,
            tissue=tissue_site_detail_id,
            condition=GTEX_BASELINE_CONDITION,
            qc_metrics=qc_metrics or {
                "aggregation": "population_median",
                "source": "gtex_median_gene_expression",
            },
        )
        session.add(sample)
        session.flush()
    else:
        sample.qc_metrics = resolved_qc_metrics


    for record in records:
        gene_id = _strip_gencode_version(record.gencode_id)
        gene = session.get(Gene, gene_id)
        if gene is None:
            gene = Gene(ensembl_gene_id=gene_id, symbol=record.gene_symbol)
            session.add(gene)
            session.flush()

        expression_value = (
            session.query(ExpressionValue)
            .filter_by(sample_id=sample.id, gene_id=gene_id)
            .one_or_none()
        )
        if expression_value is None:
            session.add(
                ExpressionValue(
                    sample=sample,
                    gene=gene,
                    normalized_value=record.median,
                    unit=ExpressionUnit.TPM,
                )
            )
        else:
            expression_value.normalized_value = record.median

    session.commit()
