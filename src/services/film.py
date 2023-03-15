from functools import lru_cache
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film
from .common import CommonQueryParams, GenreFilter

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService:
    """Сервис для получения данных о фильмах."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        """Dозвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе"""
        film = await self._film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)

        return film

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        """Получает данные о фильме из ES по film_id."""
        try:
            doc = await self.elastic.get("movies", film_id)
        except NotFoundError:
            return None
        return Film(**doc["_source"])

    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        """Получает данные о фильме из кеша."""
        data = await self.redis.get(film_id)
        if not data:
            return None

        film = Film.parse_raw(data)
        return film

    async def _put_film_to_cache(self, film: Film):
        """Сохраняем данные о фильме в кэш. Время жизни — 5 минут."""
        await self.redis.set(film.id, film.json(), FILM_CACHE_EXPIRE_IN_SECONDS)

    async def get_films(
        self, commons: CommonQueryParams, filter_: GenreFilter
    ) -> Optional[list[Film]]:
        """Dозвращает список фильмов. Он опционален, так как фильмы могут отсутствовать в базе"""
        try:
            film = await self._get_films_from_elastic(commons, filter_)
        except:
            return None
        return film

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
        result = [Film(**film["_source"]) for film in films.body["hits"]["hits"]]
        return result


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
