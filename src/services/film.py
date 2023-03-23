from functools import lru_cache
from typing import Optional

import orjson
from elasticsearch import AsyncElasticsearch, BadRequestError, NotFoundError
from fastapi import Depends
from fastapi_redis_cache import cache
from pydantic import UUID4
from redis.asyncio import Redis
from starlette.responses import Response

from src.core.config import FILM_CACHE_EXPIRE_IN_SECONDS
from src.db.elastic import get_elastic
from src.db.redis import get_redis
from src.models.film import Film, Genre, Person
from src.services.common import CommonQueryParams
from src.services.filmdependencies import FilmQuery, GenreFilter, MatchQuery


class FilmService:
    """Сервис для получения данных о фильмах."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: UUID4) -> Optional[Film]:
        """Возвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе"""
        result = await self._get_film_from_elastic(str(film_id))
        film = orjson.loads(result.body)
        return self._json_to_film(film)

    @cache(expire=FILM_CACHE_EXPIRE_IN_SECONDS)
    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        """Получает данные о фильме из ES по film_id."""
        try:
            doc = await self.elastic.get(index="movies", id=film_id)
        except NotFoundError:
            return None
        return doc["_source"]

    async def get_films(
        self,
        commons: CommonQueryParams,
        filter_: GenreFilter | None = None,
        match_query: MatchQuery | None = None,
        cache_: bool = False
    ) -> Optional[list[Film]]:
        """Возвращает список фильмов, полученных из данных JSON"""
        query = FilmQuery(filter_=filter_, match_query=match_query)
        try:
            if cache_:
                results = await self._get_films_with_cache(commons=commons, query=query)
                results = orjson.loads(results.body)
            else:
                results = await self._get_films_without_cache(commons=commons, query=query)

            result = [self._json_to_film(film["_source"]) for film in results]
        except BadRequestError:
            return None

        return result

    @cache(expire=FILM_CACHE_EXPIRE_IN_SECONDS)
    async def _get_films_with_cache(self, commons: CommonQueryParams, query: FilmQuery) -> Optional[Response]:
        films = await self.elastic.search(
            index="movies",
            from_=commons.from_,
            sort=commons.sort,
            size=commons.size,
            query=query.query,
        )

        return films.body["hits"]["hits"]

    async def _get_films_without_cache(
        self,
        commons: CommonQueryParams,
        query: FilmQuery,
    ) -> Optional[Response]:

        films = await self.elastic.search(
            index="movies",
            from_=commons.from_,
            sort=commons.sort,
            size=commons.size,
            query=query.query,
        )

        return films.body["hits"]["hits"]

    @staticmethod
    def _json_to_film(films_json):
        actors = [Person(**f) for f in films_json["actors"]]
        directors = [Person(**f) for f in films_json["directors"]]
        writers = [Person(**f) for f in films_json["writers"]]
        genre = [Genre(**f) for f in films_json["genre"]]
        film = Film(
            id=films_json["id"],
            imdb_rating=films_json["imdb_rating"],
            description=films_json["description"],
            title=films_json["title"],
            actors=actors,
            directors=directors,
            writers=writers,
            genre=genre,
        )
        return film

    def __str__(self):
        return "FilmService"


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
