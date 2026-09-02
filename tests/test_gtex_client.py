import httpx
import pytest

from cmo_platform.etl.gtex_client import (
    GTEX_API_BASE_URL,
    fetch_gtex_tissue,
    fetch_median_gene_expression,
)

SAMPLE_RESPONSE = {
    "data": [
        {
            "median": 5683.19,
            "tissueSiteDetailId": "Liver",
            "ontologyId": "UBERON:0001114",
            "datasetId": "gtex_v8",
            "gencodeId": "ENSG00000132693.12",
            "geneSymbol": "CRP",
            "unit": "TPM",
        },
        {
            "median": 0.0478836,
            "tissueSiteDetailId": "Liver",
            "ontologyId": "UBERON:0001114",
            "datasetId": "gtex_v8",
            "gencodeId": "ENSG00000181092.9",
            "geneSymbol": "ADIPOQ",
            "unit": "TPM",
        },
    ],
    "paging_info": {"numberOfPages": 1, "page": 0, "maxItemsPerPage": 250, "totalNumberOfItems": 2},
}


def test_fetch_median_gene_expression_parses_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v2/expression/medianGeneExpression"
        assert request.url.params.get_list("gencodeId") == [
            "ENSG00000132693.12",
            "ENSG00000181092.9",
        ]
        assert request.url.params["datasetId"] == "gtex_v8"
        return httpx.Response(200, json=SAMPLE_RESPONSE)

    mock_client = httpx.Client(base_url=GTEX_API_BASE_URL, transport=httpx.MockTransport(handler))

    results = fetch_median_gene_expression(
        gencode_ids=["ENSG00000132693.12", "ENSG00000181092.9"],
        tissue_site_detail_id="Liver",
        client=mock_client,
    )

    assert len(results) == 2
    assert results[0].gene_symbol == "CRP"
    assert results[0].median == pytest.approx(5683.19)
    assert results[1].gene_symbol == "ADIPOQ"


GENE_LOOKUP_RESPONSE = {
    "data": [
        {"geneSymbol": "CRP", "gencodeId": "ENSG00000132693.12"},
        {"geneSymbol": "ADIPOQ", "gencodeId": "ENSG00000181092.9"},
    ],
}


def test_fetch_gtex_tissue_resolves_symbols_then_fetches_expression() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/reference/gene":
            return httpx.Response(200, json=GENE_LOOKUP_RESPONSE)
        assert request.url.path == "/api/v2/expression/medianGeneExpression"
        return httpx.Response(200, json=SAMPLE_RESPONSE)

    mock_client = httpx.Client(base_url=GTEX_API_BASE_URL, transport=httpx.MockTransport(handler))

    results = fetch_gtex_tissue("Liver", gene_symbols=["CRP", "ADIPOQ"], client=mock_client)

    assert len(results) == 2
    assert {r.gene_symbol for r in results} == {"CRP", "ADIPOQ"}
