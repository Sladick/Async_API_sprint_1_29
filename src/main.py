import os

import uvicorn
from elasticsearch import AsyncElasticsearch, Elasticsearch
from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import ORJSONResponse
from fastapi_redis_cache import FastApiRedisCache
from pydantic import ValidationError
from redis.asyncio import Redis
from starlette.responses import JSONResponse

from src.api.v1 import films, genres, persons
from src.core import config
from src.db import elastic, redis

app = FastAPI(
    title=config.PROJECT_NAME,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors()}),
    )


@app.on_event("startup")
async def startup():
    redis.redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    elastic.es = AsyncElasticsearch(hosts=[f"{config.ELASTIC_HOST}:{config.ELASTIC_PORT}"], verify_certs=False)

    redis_cache = FastApiRedisCache()
    redis_cache.init(
        host_url=f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
        prefix="myapi-cache",
        response_header="X-MyAPI-Cache",
        ignore_arg_types=[Request, Response],
    )


@app.on_event("shutdown")
async def shutdown():
    await redis.redis.close()
    await elastic.es.close()


app.include_router(films.router, prefix="/api/v1/films", tags=["films"])
app.include_router(genres.router, prefix="/api/v1/genres", tags=["genres"])
app.include_router(persons.router, prefix="/api/v1/persons", tags=["persons"])

if __name__ == "__main__":
    if os.environ.get("ENV", "dev") == "dev":
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
        )
