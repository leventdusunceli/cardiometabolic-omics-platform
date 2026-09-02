"""Thin client for the public GTEx Portal REST API v2.

Base URL and endpoint verified live against https://gtexportal.org/api/v2 on 2026-08-30.
"""

from __future__ import annotations

import httpx
from pydantic import BaseModel

GTEX_API_BASE_URL = "https://gtexportal.org/api/v2"

# The API's own default datasetId is now "gtex_v10", but gene IDs resolved via /reference/gene
# use an older GENCODE annotation that gtex_v10 doesn't recognize -- querying without pinning
# this explicitly returns an empty result set with no error. Verified live 2026-08-30.
GTEX_DEFAULT_DATASET_ID = "gtex_v8"

# Curated gene panel spanning the inflammation / adipokine / insulin-signaling / gut-hormone
# axes this project's T2D-cardiovascular crosstalk story is built on.
_INFLAMMATION_GENES = ["CRP", "IL6", "TNF"]
_ADIPOKINE_GENES = ["ADIPOQ", "LEP", "RETN", "SERPINE1"]
_INSULIN_SIGNALING_GENES = ["INSR", "IRS1", "SLC2A4", "PPARG"]
_HORMONE_SIGNALING_GENES = ["FGF21", "GDF15", "GLP1R", "GCG"]

GENE_PANEL = [
    *_INFLAMMATION_GENES,
    *_ADIPOKINE_GENES,
    *_INSULIN_SIGNALING_GENES,
    *_HORMONE_SIGNALING_GENES,
]


class GtexMedianExpression(BaseModel):
    """One row from the medianGeneExpression endpoint: one gene, one tissue, one dataset."""

    gencode_id: str
    gene_symbol: str
    tissue_site_detail_id: str
    median: float
    unit: str
    ontology_id: str
    dataset_id: str


def fetch_median_gene_expression(
    gencode_ids: list[str],
    tissue_site_detail_id: str,
    dataset_id: str = GTEX_DEFAULT_DATASET_ID,
    client: httpx.Client | None = None,
) -> list[GtexMedianExpression]:
    """Fetch median TPM expression for the given genes in one GTEx tissue."""
    owns_client = client is None
    http_client = client or httpx.Client(base_url=GTEX_API_BASE_URL, timeout=30.0)
    try:
        response = http_client.get(
            "/expression/medianGeneExpression",
            params={
                "gencodeId": gencode_ids,
                "tissueSiteDetailId": tissue_site_detail_id,
                "datasetId": dataset_id,
                "itemsPerPage": 250,
            },
        )
        response.raise_for_status()
        payload = response.json()
    finally:
        if owns_client:
            http_client.close()

    return [
        GtexMedianExpression(
            gencode_id=row["gencodeId"],
            gene_symbol=row["geneSymbol"],
            tissue_site_detail_id=row["tissueSiteDetailId"],
            median=row["median"],
            unit=row["unit"],
            ontology_id=row["ontologyId"],
            dataset_id=row["datasetId"],
        )
        for row in payload["data"]
    ]


def fetch_gtex_tissue(
    tissue_site_detail_id: str,
    gene_symbols: list[str] | None = None,
    client: httpx.Client | None = None,
) -> list[GtexMedianExpression]:
    """Fetch median expression for the curated gene panel (or an override) in one tissue."""
    symbols = gene_symbols if gene_symbols is not None else GENE_PANEL
    owns_client = client is None
    http_client = client or httpx.Client(base_url=GTEX_API_BASE_URL, timeout=30.0)
    try:
        gencode_by_symbol = resolve_gencode_ids(symbols, client=http_client)
        return fetch_median_gene_expression(
            gencode_ids=list(gencode_by_symbol.values()),
            tissue_site_detail_id=tissue_site_detail_id,
            client=http_client,
        )
    finally:
        if owns_client:
            http_client.close()


def resolve_gencode_ids(
    gene_symbols: list[str],
    client: httpx.Client | None = None,
) -> dict[str, str]:
    """Look up the current versioned GENCODE ID for each gene symbol.

    gencodeIds are annotation-version-specific (e.g. ENSG00000132693.12) and will drift if
    GENCODE releases a new version, resolving by symbol at call time, rather than hardcoding
    IDs, keeps this pipeline correct without manual updates when that happens.
    """
    owns_client = client is None
    http_client = client or httpx.Client(base_url=GTEX_API_BASE_URL, timeout=30.0)
    try:
        response = http_client.get(
            "/reference/gene",
            params={"geneId": gene_symbols, "itemsPerPage": len(gene_symbols)},
        )
        response.raise_for_status()
        payload = response.json()
    finally:
        if owns_client:
            http_client.close()

    return {row["geneSymbol"]: row["gencodeId"] for row in payload["data"]}
