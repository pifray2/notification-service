from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Настройки приложения"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "notification-service"
    app_env: Literal["local", "dev", "test", "prod"] = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/notification-service",
    )
    sql_echo: bool = False


    kafka_brokers: str = "kafka:9092"
    kafka_topic: str = "legal-entities-created"
    kafka_group_id: str = "notification-service"
    
    
@lru_cache
def get_settings() -> Settings:
    """Возвращает кэшированный объект настроек"""

    return Settings()
