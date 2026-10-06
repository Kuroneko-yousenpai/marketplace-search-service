from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    postgres_host: str = "localhost"
    postgres_database_name: str = "search_db"
    postgres_password: str = "postgres"
    postgres_port: int = 5435
    postgres_username: str = "postgres"

    # Explicit DSN (DATABASE_URL) wins; otherwise it's assembled from POSTGRES_*.
    database_url: str = ""

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_ads: str = "ads"
    kafka_consumer_group: str = "search-service"
    ad_service_url: str = "http://localhost:8002"

    @model_validator(mode="after")
    def _build_database_url(self) -> "Settings":
        if not self.database_url:
            self.database_url = (
                f"postgresql+asyncpg://{quote_plus(self.postgres_username)}"
                f":{quote_plus(self.postgres_password)}"
                f"@{self.postgres_host}:{self.postgres_port}"
                f"/{self.postgres_database_name}"
            )
        return self
