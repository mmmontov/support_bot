from __future__ import annotations

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///./support.db"
    api_secret: str = "change-me"
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    bot_token: str = ""
    api_base_url: str = "http://127.0.0.1:8000"
    admin_chat_id: int = 0


@lru_cache
def get_settings() -> Settings:
    return Settings()


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
