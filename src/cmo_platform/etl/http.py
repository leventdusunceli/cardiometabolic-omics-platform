"""HTTP download helper to be shared by all ETL clients

Used in all GEO clients to reduce the number of lines in
each matrix download, including expression matrices.
"""

from __future__ import annotations

import gzip

import httpx


def download_text(
    url: str, client: httpx.Client | None = None, gzipped: bool = False, timeout: float = 60.0
) -> str:
    """GET `url` and return the body as text, unzipping it first if `gzipped`.

    Uses the given client (tests pass a fake one) or opens and closes its own.
    """
    http_client = client or httpx.Client(timeout=timeout)
    try:
        response = http_client.get(url)
        response.raise_for_status()
    finally:
        if client is None:
            http_client.close()
    content = gzip.decompress(response.content) if gzipped else response.content
    return content.decode("utf-8")
