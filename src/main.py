import logging

import uvicorn
from elasticsearch import AsyncElasticsearch
from fastapi import Cookie, Depends, FastAPI, Request, Response
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis
from fastapi_redis_cache import FastApiRedisCache, cache

from api.v1 import films
from core import config
from core.logger import LOGGING
from db import elastic, redis
from services.film import FilmService

app = FastAPI(
    title=config.PROJECT_NAME,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)


@app.on_event("startup")
async def startup():
    redis.redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    elastic.es = AsyncElasticsearch(
        hosts=[
            f"{config.ELASTIC_HOST}:{config.ELASTIC_PORT}",
        ],
        verify_certs=False,
    )
    redis_cache = FastApiRedisCache()
    redis_cache.init(
        host_url=f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
        prefix="myapi-cache",
        response_header="X-MyAPI-Cache",
        ignore_arg_types=[Request, Response, FilmService]
    )


@app.on_event("shutdown")
async def shutdown():
    await redis.redis.close()
    await elastic.es.close()


# Подключаем роутер к серверу, указав префикс /v1/films
# Теги указываем для удобства навигации по документации
app.include_router(films.router, prefix="/api/v1/films", tags=["films"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
    )
