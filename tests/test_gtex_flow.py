from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cmo_platform.db.base import Base
from cmo_platform.db.models import ExpressionValue, Sample
from cmo_platform.etl import flows
from cmo_platform.etl.gtex_client import GtexMedianExpression


def _fake_records(tissue: str) -> list[GtexMedianExpression]:
    return [
        GtexMedianExpression(
            gencode_id="ENSG00000132693.12",
            gene_symbol="CRP",
            tissue_site_detail_id=tissue,
            median=5.0,
            unit="TPM",
            ontology_id="UBERON:0001114",
            dataset_id="gtex_v8",
        )
    ]


def _sqlite_session_factory() -> sessionmaker:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def test_ingest_gtex_tissue_is_idempotent(monkeypatch):
    monkeypatch.setattr(flows, "fetch_gtex_tissue", _fake_records)
    session_factory = _sqlite_session_factory()

    flows.ingest_gtex_tissue("Liver", session_factory=session_factory)
    flows.ingest_gtex_tissue("Liver", session_factory=session_factory)

    session = session_factory()
    try:
        assert session.query(Sample).count() == 1
        assert session.query(ExpressionValue).count() == 1
    finally:
        session.close()
