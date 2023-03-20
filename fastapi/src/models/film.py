from typing import Optional

import orjson
from pydantic import UUID4, BaseModel, Field, validator


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class Person(BaseModel):

    id: str
    name: str

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class Genre(BaseModel):

    id: UUID4
    name: str


class Film(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    genre: Optional[list[Genre]]
    imdb_rating: Optional[float]
    directors: Optional[list[Person]]
    writers: Optional[list[Person]]
    actors: Optional[list[Person]]
    writers_names: Optional[list[str]]
    actors_names: Optional[list[str]]
    director: Optional[list[str]]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
        validate_assignment = True

    @validator("description")
    def set_description(cls, description):
        return description or ""
