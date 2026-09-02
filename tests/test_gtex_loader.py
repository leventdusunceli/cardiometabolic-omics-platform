from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from cmo_platform.db.base import Base
from cmo_platform.db.models import Dataset, ExpressionValue, Gene, Sample
from cmo_platform.etl.gtex_client import GtexMedianExpression
from cmo_platform.etl.gtex_loader import load_to_warehouse

SAMPLE_RECORDS = [
    GtexMedianExpression(
        gencode_id="ENSG00000132693.12",
        gene_symbol="CRP",
        tissue_site_detail_id="Liver",
        median=5683.19,
        unit="TPM",
        ontology_id="UBERON:0001114",
        dataset_id="gtex_v8",
    ),
    GtexMedianExpression(
        gencode_id="ENSG00000181092.9",
        gene_symbol="ADIPOQ",
        tissue_site_detail_id="Liver",
        median=0.0478836,
        unit="TPM",
        ontology_id="UBERON:0001114",
        dataset_id="gtex_v8",
    ),
]


def _session() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_load_to_warehouse_creates_expected_rows() -> None:
    session = _session()
    load_to_warehouse("Liver", SAMPLE_RECORDS, session)

    assert session.query(Dataset).count() == 1
    assert session.query(Sample).count() == 1
    assert session.query(Gene).count() == 2
    assert session.query(ExpressionValue).count() == 2

    gene = session.get(Gene, "ENSG00000132693")
    assert gene is not None
    assert gene.symbol == "CRP"


def test_load_to_warehouse_is_idempotent() -> None:
    session = _session()
    load_to_warehouse("Liver", SAMPLE_RECORDS, session)
    load_to_warehouse("Liver", SAMPLE_RECORDS, session)  # run again, same data

    assert session.query(Dataset).count() == 1
    assert session.query(Sample).count() == 1
    assert session.query(Gene).count() == 2
    assert session.query(ExpressionValue).count() == 2
