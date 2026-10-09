from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from cmo_platform.db.base import Base
from cmo_platform.db.models import Gene
from cmo_platform.db.upsert import bulk_upsert


def _session() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_bulk_upsert_inserts_then_updates() -> None:
    session = _session()
    bulk_upsert(session, Gene, [{"ensembl_gene_id": "ENSG1"}], ["ensembl_gene_id"], [])
    bulk_upsert(
        session,
        Gene,
        [
            {"ensembl_gene_id": "ENSG1", "symbol": "CRP"},
            {"ensembl_gene_id": "ENSG2", "symbol": "IL6"},
        ],
        ["ensembl_gene_id"],
        ["symbol"],
    )

    assert {g.ensembl_gene_id: g.symbol for g in session.query(Gene)} == {
        "ENSG1": "CRP",
        "ENSG2": "IL6",
    }


def test_bulk_upsert_without_update_columns_keeps_existing_rows() -> None:
    session = _session()
    session.add(Gene(ensembl_gene_id="ENSG1", symbol="CRP"))
    session.flush()

    bulk_upsert(
        session, Gene, [{"ensembl_gene_id": "ENSG1", "symbol": None}], ["ensembl_gene_id"], []
    )

    assert session.get(Gene, "ENSG1").symbol == "CRP"
