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
    actors_name: Optional[list[str]]
    id: str
    title: Optional[str]
    description: Optional[str] = None
    director: Optional[list[str]]
    genre: Optional[list[str]]
    imdb_rating: Optional[float]
    writers: Optional[list[Person]]
    writers_names: Optional[list[str]]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
