import pandas as pd

from cmo_platform.etl.geo_qc import qc_filter_samples


def _run_qc() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    counts = pd.DataFrame(
        {"G1": [100, 100, 1], "G2": [100, 0, 1], "G3": [100, 0, 1]},
        index=["GSM_ok", "GSM_few_genes", "GSM_small_library"],
    )
    samples = pd.DataFrame({"disease": ["healthy", "NASH", "NASH"]}, index=counts.index)
    kept_counts, kept_samples, summary = qc_filter_samples(
        counts, samples, min_library_size=50, min_detected_genes=2
    )
    return samples, kept_counts, kept_samples, summary


def test_qc_filter_samples_drops_samples_failing_either_threshold() -> None:
    _, kept_counts, kept_samples, summary = _run_qc()

    assert list(kept_counts.index) == ["GSM_ok"]
    assert list(kept_samples.index) == ["GSM_ok"]
    assert summary["kept_sample_count"] == 1
    assert [d["sample_id"] for d in summary["dropped_samples"]] == [
        "GSM_few_genes",
        "GSM_small_library",
    ]


def test_qc_filter_samples_records_metrics_without_mutating_input() -> None:
    samples, _, kept_samples, _ = _run_qc()

    assert kept_samples.loc["GSM_ok", "qc_metrics"] == {
        "library_size": 300,
        "detected_genes": 3,
        "min_library_size": 50,
        "min_detected_genes": 2,
    }
    assert "qc_metrics" not in samples.columns
