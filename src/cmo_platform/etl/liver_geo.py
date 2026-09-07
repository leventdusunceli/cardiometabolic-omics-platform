"""Script for joining study GSE126848's sample metadata (series matrix)
and it's count matrix and applies contrast decision documented in DATA_SOURCES.md

This script is liver and study specific because the GEO studies we're using don't share
the same "description code" join key or the same zero-padding quirk, so each
tissue gets its own small glue module rather than one generic function"""

from __future__ import annotations

import pandas as pd

from cmo_platform.db.models import ConditionCategory
from cmo_platform.etl.geo_client import fetch_geo_count_matrix, fetch_geo_series_matrix

LIVER_GEO_ACCESSION = "GSE126848"
LIVER_COUNT_FILENAME = "GSE126848_Gene_counts_raw.txt.gz"

LIVER_DISEASE_TO_CONDITION_CATEGORY = {
    "healthy": ConditionCategory.CONTROL,
    "NASH": ConditionCategory.CASE,
    "obese": ConditionCategory.EXCLUDED,
    "NAFLD": ConditionCategory.EXCLUDED,
}


def fetch_liver_geo_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (counts, samples), both indexed by GSM accession: counts has samples as rows and
    genes as columns; samples carries the native `disease` label plus condition_category.
    """
    samples = fetch_geo_series_matrix(LIVER_GEO_ACCESSION)
    counts = fetch_geo_count_matrix(LIVER_GEO_ACCESSION, LIVER_COUNT_FILENAME)

    # The series matrix's `description` codes are unpadded ("893") but the count matrix's
    # column headers are zero-padded to 4 digits ("0893")
    samples = samples.copy()
    samples["count_matrix_column"] = samples["description"].str.zfill(4)

    counts = counts.loc[samples["count_matrix_column"]]
    counts.index = samples["geo_accession"].to_numpy()

    samples = samples.set_index("geo_accession")
    samples["condition_category"] = samples["disease"].map(LIVER_DISEASE_TO_CONDITION_CATEGORY)

    return counts, samples
