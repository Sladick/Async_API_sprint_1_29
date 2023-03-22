from functools import lru_cache
from typing import List, Optional

import orjson
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi_redis_cache import cache
from redis.asyncio import Redis

from src.core.config import PERSON_CACHE_EXPIRE_IN_SECONDS
from src.db.elastic import get_elastic
from src.db.redis import get_redis
from fastapi import Depends

from src.services.common import CommonQueryParamsMixin
from src.models.person import Person


class PersonService:
    """Сервис для получения данных о персонажах."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_person_by_id(self, person_id: str) -> Optional[Person]:
        """Возвращает данные персонажа по его ID."""
        result = await self._get_person_from_elastic(person_id)
        person = orjson.loads(result.body)
        return Person(**person)

    @cache(expire=PERSON_CACHE_EXPIRE_IN_SECONDS)
    async def _get_person_from_elastic(self, person_id: str) -> Optional[Person]:
        """Получает данные о фильме из ES по person_id."""
        try:
            doc = await self.elastic.get(index="persons", id=person_id)
        except NotFoundError:
            return None
        return doc["_source"]

    async def get_persons(self, commons: CommonQueryParamsMixin) -> Optional[List[Person]]:
        """Получаем список персонажей."""
        try:
            results = await self._get_persons_from_elastic(commons)
            persons = orjson.loads(results.body)
            result = [Person(**person["_source"]) for person in persons]
        except:
            return None
        return result

    @cache(expire=PERSON_CACHE_EXPIRE_IN_SECONDS)
    async def _get_persons_from_elastic(self, commons: CommonQueryParamsMixin) -> Optional[Person]:
        sort = {}
        if commons.sort:
            sort = dict([(k, v) if k != "full_name" else ("full_name.raw", v) for k, v in tuple(tuple(v.split(':')) for v in commons.sort.split(','))])

        if commons.filter_ is not None:
            query = {"match": {"full_name": commons.filter_}}
        else:
            query = {"match_all": {}}
        persons = await self.elastic.search(
            index="persons",
            from_=commons.from_,
            sort=sort,
            size=commons.size,
            query=query,
        )

        return persons.body["hits"]["hits"]

    def __str__(self):
        return "PersonService"


@lru_cache()
def get_person_service(redis: Redis = Depends(get_redis),
                       elastic: AsyncElasticsearch = Depends(get_elastic)) -> PersonService:
    return PersonService(redis, elastic)
