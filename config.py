"""Application settings.

Two layers:

* `Settings` — pydantic-settings model that reads `APP_*` env vars (and a
  local `.env`). Performs type validation and refuses to start when
  required fields like `APP_DB_PASSWORD` are missing.
* `BaseConfig / DevConfig / TestConfig / ProdConfig` — Flask config
  classes consumed via `app.config.from_object(...)`. Their values are
  derived from the `Settings` instance, so the same env is the single
  source of truth.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    env: Literal["dev", "test", "prod"] = "dev"

    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "app_db"
    db_user: str = "app_user"
    db_password: str = Field(..., min_length=1)

    database_url: Optional[str] = None

    @computed_field
    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        dsn = PostgresDsn.build(
            scheme="postgresql+psycopg2",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            path=self.db_name,
        )
        return str(dsn)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton settings accessor.

    Tests can call `get_settings.cache_clear()` after monkey-patching env.
    """
    return Settings()


class BaseConfig:
    """Base Flask config — values pulled from `Settings` at class-construction
    time. Subclasses override individual attributes (e.g. tests swap
    `SQLALCHEMY_DATABASE_URI` to point at SQLite)."""

    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = get_settings().sqlalchemy_database_uri


class DevConfig(BaseConfig):
    DEBUG = True


class TestConfig(BaseConfig):
    TESTING = True


class ProdConfig(BaseConfig):
    DEBUG = False
    TESTING = False
