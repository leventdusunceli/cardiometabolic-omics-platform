import httpx
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from cmo_platform.db.base import Base
from cmo_platform.db.models import Gene
from cmo_platform.etl.gene_annotation import fetch_hgnc_genes, load_gene_annotation

HGNC_TSV = (
    "hgnc_id\tsymbol\tlocus_group\tlocation\tensembl_gene_id\n"
    "HGNC:1\tGLP1R\tprotein-coding gene\t6p21.2\tENSG00000112164\n"
    "HGNC:2\tMT-ND1\tprotein-coding gene\tmitochondria\tENSG00000198888\n"
    "HGNC:3\tNOID\tpseudogene\t1q21\t\n"
    "HGNC:4\tDUP2\tother\tXq28\tENSG00000112164\n"
)


def _fetch() -> pd.DataFrame:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=HGNC_TSV))
    with httpx.Client(transport=transport) as client:
        return fetch_hgnc_genes(client)


def test_fetch_hgnc_genes_drops_missing_and_duplicate_ids() -> None:
    genes = _fetch().set_index("ensembl_gene_id")

    assert list(genes.index) == ["ENSG00000112164", "ENSG00000198888"]
    assert genes.loc["ENSG00000112164"].to_dict() == {
        "symbol": "GLP1R",
        "biotype": "protein-coding gene",
        "chromosome": "6",
    }
    assert genes.loc["ENSG00000198888", "chromosome"] == "MT"


def test_load_gene_annotation_fills_symbols_and_is_idempotent() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.add(Gene(ensembl_gene_id="ENSG00000112164"))  # as the GEO loader leaves it
    session.commit()

    load_gene_annotation(_fetch(), session)
    load_gene_annotation(_fetch(), session)

    assert session.query(Gene).count() == 2
    assert session.get(Gene, "ENSG00000112164").symbol == "GLP1R"
