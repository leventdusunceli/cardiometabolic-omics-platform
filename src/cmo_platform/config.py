from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://cmo:cmo@localhost:5432/cmo_platform"
    rabbitmq_url: str = "amqp://cmo:cmo@localhost:5672/"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"


settings = Settings()
