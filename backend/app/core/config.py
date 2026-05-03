from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="local", alias="APP_ENV")
    database_url: str = Field(default="sqlite:///../.data/desktop_irm.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    local_storage_dir: Path = Field(default=Path("../.data/storage"), alias="LOCAL_STORAGE_DIR")
    local_secret_dir: Path = Field(default=Path("../.data/secrets"), alias="LOCAL_SECRET_DIR")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    gmail_client_id: str | None = Field(default=None, alias="GMAIL_CLIENT_ID")
    gmail_client_secret: str | None = Field(default=None, alias="GMAIL_CLIENT_SECRET")
    gmail_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/email/auth/callback",
        alias="GMAIL_REDIRECT_URI",
    )
    gmail_frontend_redirect_uri: str = Field(
        default="http://localhost:5173/email",
        alias="GMAIL_FRONTEND_REDIRECT_URI",
    )
    gmail_credential_file: Path = Field(
        default=Path("../.data/secrets/gmail_oauth.json.enc"),
        alias="GMAIL_CREDENTIAL_FILE",
    )
    gmail_credential_key_file: Path = Field(
        default=Path("../.data/secrets/gmail_oauth.key"),
        alias="GMAIL_CREDENTIAL_KEY_FILE",
    )
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:5173"], alias="CORS_ORIGINS"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return value
        return ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
