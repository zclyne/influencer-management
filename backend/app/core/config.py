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
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
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
