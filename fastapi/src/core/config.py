import os
from functools import lru_cache
from logging import config as logging_config

from pydantic import BaseSettings, Field

from core.logger import LOGGING


class AppBaseSettings(BaseSettings):
    redis_host: str = Field(env="redis_host")
    redis_port: int = Field(env="redis_port")
    es_host: str = Field(env="es_host")
    es_port: str = Field(env="es_port")


class AppDevSettings(AppBaseSettings):
    class Config:
        env_file = "dev.env"


class AppProdSettings(AppBaseSettings):
    class Config:
        env_file = "/app/.env"


class Settings(BaseSettings):
    """Settings for establishing all connections."""

    config = dict(dev=AppDevSettings, prod=AppProdSettings)
    params: AppBaseSettings = config[os.environ.get("ENV", "dev").lower()]()

    class Config:
        env_file = "/app/.env"


@lru_cache()
def get_settings():
    return Settings()


conn_params = get_settings()

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Название проекта. Используется в Swagger-документации
PROJECT_NAME = os.getenv("PROJECT_NAME", "movies")

# Настройки Redis
REDIS_HOST = conn_params.params.redis_host
REDIS_PORT = conn_params.params.redis_port

# # Настройки Elasticsearch
ELASTIC_HOST = conn_params.params.es_host
ELASTIC_PORT = conn_params.params.es_port

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
