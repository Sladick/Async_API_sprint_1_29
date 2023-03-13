from typing import Optional

import orjson

from pydantic import BaseModel


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class Person(BaseModel):
    id: str
    name: str

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class Film(BaseModel):
    actors: Optional[list[Person]]
    actors_name: Optional[str]
    id: str
    title: Optional[str]
    description: Optional[str] = None
    director: Optional[str]
    genre: Optional[str]
    imdb_rating: Optional[float]
    writers: Optional[list[Person]]
    writers_names: Optional[str]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
