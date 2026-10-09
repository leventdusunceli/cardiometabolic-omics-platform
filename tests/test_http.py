import gzip

import httpx

from cmo_platform.etl.http import download_text


def test_download_text_unzips_gzipped_body() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=gzip.compress(b"a\tb"))
    )
    with httpx.Client(transport=transport) as client:
        assert download_text("https://example.org/f.gz", client, gzipped=True) == "a\tb"
