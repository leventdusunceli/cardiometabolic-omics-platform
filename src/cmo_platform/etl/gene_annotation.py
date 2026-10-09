"""HGNC gene annotations table. Our official table matching Ensembl IDs to gene symbols.
'genes' table will contain all HGNC genes, symbols, chromosomes etc.

GEO count matrices list genes by Ensembl ID only, so without this table most genes have no
symbol. Human gene symbols are retrieved from HGNC (CC0, https://www.genenames.org).
"""

from __future__ import annotations

from io import StringIO

import httpx
import pandas as pd
from sqlalchemy.orm import Session

from cmo_platform.db.models import Gene
from cmo_platform.db.upsert import bulk_upsert
from cmo_platform.etl.http import download_text

HGNC_COMPLETE_SET_URL = (
    "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"
)


def fetch_hgnc_genes(client: httpx.Client | None = None) -> pd.DataFrame:
    """Return one row per Ensembl gene ID with columns matching `genes`.

    `biotype` is HGNC's locus_group (e.g. "protein-coding gene"), not an Ensembl biotype.
    `chromosome` comes from HGNC's cytogenetic location ("6p21.2" -> "6", "mitochondria" -> "MT").
    HGNC rows without an Ensembl ID are dropped; the few IDs listed twice keep their first row.
    """
    hgnc = pd.read_csv(
        StringIO(download_text(HGNC_COMPLETE_SET_URL, client)),
        sep="\t",
        usecols=["ensembl_gene_id", "symbol", "locus_group", "location"],
        dtype=str,
    )
    hgnc = hgnc.dropna(subset=["ensembl_gene_id"]).drop_duplicates("ensembl_gene_id")
    chromosome = hgnc["location"].str.extract(r"^(\d+|X|Y)", expand=False)
    return pd.DataFrame(
        {
            "ensembl_gene_id": hgnc["ensembl_gene_id"],
            "symbol": hgnc["symbol"],
            "biotype": hgnc["locus_group"],
            "chromosome": chromosome.mask(hgnc["location"] == "mitochondria", "MT"),
        }
    )


def load_gene_annotation(genes: pd.DataFrame, session: Session) -> None:
    """Upsert HGNC rows into `genes`: new IDs are inserted; existing IDs get symbol, biotype and
    chromosome overwritten, since HGNC is the authority (also over symbols GTEx supplied).
    """
    records = genes.astype(object).where(genes.notna(), None).to_dict("records")
    bulk_upsert(session, Gene, records, ["ensembl_gene_id"], ["symbol", "biotype", "chromosome"])
    session.commit()
