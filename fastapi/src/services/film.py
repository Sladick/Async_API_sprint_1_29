from functools import lru_cache
from typing import Optional

import orjson
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi_redis_cache import cache
from redis.asyncio import Redis

from core.config import FILM_CACHE_EXPIRE_IN_SECONDS
from db.elastic import get_elastic
from db.redis import get_redis
from fastapi import Depends
from models.film import Film
from services.common import CommonQueryParams, GenreFilter


class FilmService:
    """Сервис для получения данных о фильмах."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        """Dозвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе"""
        result = await self._get_film_from_elastic(film_id)
        film = orjson.loads(result.body)
        return Film(**film)

    @cache(expire=FILM_CACHE_EXPIRE_IN_SECONDS)
    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        """Получает данные о фильме из ES по film_id."""
        try:
            doc = await self.elastic.get(index="movies", id=film_id)
        except NotFoundError:
            return None
        return doc["_source"]

    async def get_films(
        self, commons: CommonQueryParams, filter_: GenreFilter
    ) -> Optional[list[Film]]:
        """Dозвращает список фильмов. Он опционален, так как фильмы могут отсутствовать в базе"""
        try:
            results = await self._get_films_from_elastic(commons, filter_)
            films = orjson.loads(results.body)
            result = [Film(**film["_source"]) for film in films]
        except:
            return None
        return result

    @cache(expire=FILM_CACHE_EXPIRE_IN_SECONDS)
    async def _get_films_from_elastic(
        self, commons: CommonQueryParams, filter_: GenreFilter
    ) -> Optional[Film]:
        if commons.sort is not None:
            sort = {commons.sort: "desc"}
        else:
            sort = {}
        if filter_.genre is not None:
            query = {"match": {"genre": filter_.genre.title()}}
        else:
            query = {"match_all": {}}
        films = await self.elastic.search(
            index="movies",
            from_=commons.from_,
            sort=sort,
            size=commons.size,
            query=query,
        )

        return films.body["hits"]["hits"]

    def __str__(self):
        return "FilmService"


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
