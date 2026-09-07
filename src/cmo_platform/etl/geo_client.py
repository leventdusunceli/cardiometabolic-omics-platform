"""Generic GEO series ingestion. Downloads a series matrix and
the raw count matrix, then add them into one file together.

GEO ubmitters don't standardize supplementary filenames or which sample-metadata field
matches the count matrix's column headers. Both must be supplied explicitly per dataset,
verified against the real files during dataset validation (see DATA_SOURCES.md)
"""

from __future__ import annotations

import gzip

import httpx
import pandas as pd

GEO_FTP_BASE_URL = "https://ftp.ncbi.nlm.nih.gov/geo/series"


def _series_dir(accession: str) -> str:
    """Helper function to remove ast 3 integers from study accession code
    Needed to access the parent directories of given studies, and consequently
    to the needed study matrix. This is due to NCBI's directory bucketing convention"""
    return f"{accession[:-3]}nnn"


def fetch_geo_series_matrix(accession: str, client: httpx.Client | None = None) -> pd.DataFrame:
    """ "Parse a GEO series matrix file"""
    owns_client = client is None
    http_client = client or httpx.Client(timeout=30.0)
    try:
        url = (
            f"{GEO_FTP_BASE_URL}/{_series_dir(accession)}/{accession}/matrix/"
            f"{accession}_series_matrix.txt.gz"
        )
        response = http_client.get(url)
        response.raise_for_status()
        text = gzip.decompress(response.content).decode("utf-8")
    finally:
        if owns_client:
            http_client.close()

    records: dict[str, list[str]] = {}
    relevant_keys = {"geo_accession", "description"}
    for line in text.splitlines():
        if not line.startswith("!Sample_"):
            continue
        key, *raw_values = line.split("\t")
        key = key.removeprefix("!Sample_")
        values = [v.strip('"') for v in raw_values]

        if key == "characteristics_ch1":
            for value in values:
                char_name, _, char_value = value.partition(": ")
                records.setdefault(char_name, []).append(char_value)
        elif key in relevant_keys and key not in records:
            records[key] = values

    return pd.DataFrame(records)


def fetch_geo_count_matrix(
    accession: str, filename: str, client: httpx.Client | None = None
) -> pd.DataFrame:
    """Download and parse a dataset's raw supplementary count matrix"""
    owns_client = client is None
    http_client = client or httpx.Client(timeout=60.0)
    try:
        url = f"{GEO_FTP_BASE_URL}/{_series_dir(accession)}/{accession}/suppl/{filename}"
        response = http_client.get(url)
        response.raise_for_status()
        text = gzip.decompress(response.content).decode("utf-8")
    finally:
        if owns_client:
            http_client.close()

    from io import StringIO

    counts = pd.read_csv(StringIO(text), sep="\t", index_col=0)
    return counts.transpose()
