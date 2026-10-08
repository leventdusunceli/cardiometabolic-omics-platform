import pandas as pd

from cmo_platform.db.models import ConditionCategory
from cmo_platform.etl import liver_geo


def test_fetch_liver_geo_dataset_joins_on_padded_codes_and_maps_contrast(monkeypatch) -> None:
    series_matrix = pd.DataFrame(
        {
            "geo_accession": ["GSM1", "GSM2", "GSM3"],
            "description": ["893", "12", "1001"],
            "disease": ["healthy", "NASH", "NAFLD"],
        }
    )
    # Different order than the metadata, plus a sample ("9999") the metadata doesn't list.
    count_matrix = pd.DataFrame({"ENSG01": [5, 6, 7, 8]}, index=["0012", "0893", "1001", "9999"])
    monkeypatch.setattr(liver_geo, "fetch_geo_series_matrix", lambda accession: series_matrix)
    monkeypatch.setattr(
        liver_geo, "fetch_geo_count_matrix", lambda accession, filename: count_matrix
    )

    counts, samples = liver_geo.fetch_liver_geo_dataset()

    assert list(counts.index) == ["GSM1", "GSM2", "GSM3"]
    assert list(counts["ENSG01"]) == [6, 5, 7]
    assert list(samples["condition_category"]) == [
        ConditionCategory.CONTROL,
        ConditionCategory.CASE,
        ConditionCategory.EXCLUDED,
    ]
