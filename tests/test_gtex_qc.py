from cmo_platform.etl.gtex_client import GtexMedianExpression
from cmo_platform.etl.gtex_qc import qc_and_normalize


def _record(**overrides: object) -> GtexMedianExpression:
    defaults = dict(
        gencode_id="ENSG00000132693.12",
        gene_symbol="CRP",
        tissue_site_detail_id="Liver",
        median=5.0,
        unit="TPM",
        ontology_id="UBERON:0001114",
        dataset_id="gtex_v8",
    )
    defaults.update(overrides)
    return GtexMedianExpression(**defaults)


def test_keeps_valid_records():
    kept, summary = qc_and_normalize([_record()])
    assert len(kept) == 1
    assert summary["dropped_records"] == []
    assert summary["kept_gene_count"] == 1


def test_drops_wrong_unit():
    kept, summary = qc_and_normalize([_record(unit="counts")])
    assert kept == []
    assert len(summary["dropped_records"]) == 1


def test_drops_negative_median():
    kept, summary = qc_and_normalize([_record(median=-1.0)])
    assert kept == []
    assert summary["dropped_records"][0]["reason"] == "negative median -1.0"


def test_detected_gene_count_excludes_zero_median():
    kept, summary = qc_and_normalize([_record(median=0.0), _record(gene_symbol="IL6", median=3.0)])
    assert len(kept) == 2
    assert summary["detected_gene_count"] == 1
