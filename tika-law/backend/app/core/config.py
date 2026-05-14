from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Tika Law"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins_raw: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="BACKEND_CORS_ORIGINS",
    )

    database_url_raw: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/tika_law",
        alias="DATABASE_URL",
    )

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    resend_api_key: str | None = None
    resend_from: str = "Tika Law <onboarding@resend.dev>"

    @property
    def backend_cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins_raw.split(",")
            if origin.strip()
        ]

    @property
    def database_url(self) -> str:
        if self.database_url_raw.startswith("postgresql://"):
            return self.database_url_raw.replace("postgresql://", "postgresql+psycopg://", 1)

        return self.database_url_raw


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
