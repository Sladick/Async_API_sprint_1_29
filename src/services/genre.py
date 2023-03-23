from functools import lru_cache
from typing import Optional, List

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from fastapi_redis_cache import cache
from redis.asyncio import Redis
import orjson

from src.core.config import GENRE_CACHE_EXPIRE_IN_SECONDS
from src.db.elastic import get_elastic
from src.db.redis import get_redis
from src.models.genre import Genre
from src.services.common import CommonQueryParamsMixin


class GenreService:
    """Сервис для получения данных о жанрах."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_genre_by_id(self, genre_id: str) -> Optional[Genre]:
        """Получааем данные о жанре по ID."""
        result = await self._get_genre_by_id_from_elastic(genre_id)
        genre = orjson.loads(result.body)
        return Genre(**genre)

    @cache(expire=GENRE_CACHE_EXPIRE_IN_SECONDS)
    async def _get_genre_by_id_from_elastic(self, genre_id: str) -> Optional[Genre]:
        """Получаем данные о жанре по ID из кэша Redis'а, если в кэше нет данных, то получаем данные из ES."""
        try:
            doc = await self.elastic.get(index="genres", id=genre_id)
        except NotFoundError:
            return None
        return doc["_source"]

    async def get_genres(self, commons: CommonQueryParamsMixin) -> Optional[List[Genre]]:
        """Возвращает список жанров."""
        try:
            results = await self._get_genres_from_elastic(commons)
            genres = orjson.loads(results.body)
            result = [Genre(**genre["_source"]) for genre in genres]
        except:
            return None
        return result

    @cache(expire=GENRE_CACHE_EXPIRE_IN_SECONDS)
    async def _get_genres_from_elastic(self, commons: CommonQueryParamsMixin) -> Optional[Genre]:
        sort = {}
        query = {"match_all": {}}
        if commons.sort:
            sort = dict([(k, v) if k != "name" else ("genre_name.raw", v) for k,v in tuple(tuple(v.split(':')) for v in commons.sort.split(','))])

        if commons.filter_:
            query = {"match": {"name": commons.filter_}}

        genres = await self.elastic.search(
            index="genres",
            from_=commons.from_,
            sort=sort,
            size=commons.size,
            query=query,
        )

        return genres.body["hits"]["hits"]

    def __str__(self):
        return "GenreService"


@lru_cache()
def get_genre_service(redis: Redis = Depends(get_redis),
                      elastic: AsyncElasticsearch = Depends(get_elastic)) -> GenreService:
    return GenreService(redis, elastic)
