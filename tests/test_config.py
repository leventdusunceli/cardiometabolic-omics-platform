import os

from cmo_platform.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.api_v1_prefix == "/api/v1"


def test_settings_reads_environment_override() -> None:
    os.environ["LOG_LEVEL"] = "DEBUG"
    try:
        settings = Settings(_env_file=None)
        assert settings.log_level == "DEBUG"
    finally:
        del os.environ["LOG_LEVEL"]
