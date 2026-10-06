from urllib.parse import quote_plus

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", populate_by_name=True
    )

    postgres_host: str = "localhost"
    postgres_database_name: str = "search_db"
    postgres_password: str = "postgres"
    postgres_port: int = 5435
    postgres_username: str = "postgres"

    # Explicit DSN (DATABASE_URL) wins; otherwise it's assembled from POSTGRES_*.
    database_url: str = ""

    # The LMS cluster injects the real broker as KAFKA_BROKERS next to a dummy
    # KAFKA_BOOTSTRAP_SERVERS=localhost:9092, so KAFKA_BROKERS takes precedence.
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        validation_alias=AliasChoices("KAFKA_BROKERS", "KAFKA_BOOTSTRAP_SERVERS"),
    )
    kafka_topic_ads: str = "ads"
    # Empty means derived from the topic (see below).
    kafka_consumer_group: str = ""
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

    @model_validator(mode="after")
    def _build_consumer_group(self) -> "Settings":
        # The cluster Kafka is shared between students and a bare "search-service"
        # group is already taken there, so namespace it by the (per-student) topic.
        if not self.kafka_consumer_group:
            self.kafka_consumer_group = (
                "search-service"
                if self.kafka_topic_ads == "ads"
                else f"{self.kafka_topic_ads}.search-service"
            )
        return self
