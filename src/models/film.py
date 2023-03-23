from typing import Optional

from pydantic import validator

from src.models.mixins import OrjsonConfigMixin, UUIDMixin


class Genre(UUIDMixin):
    name: str


class Person(UUIDMixin):
    name: str


class Film(UUIDMixin, OrjsonConfigMixin):
    title: Optional[str]
    description: Optional[str] = ""
    genre: Optional[list[Genre]]
    imdb_rating: Optional[float]
    actors: Optional[list[Person]]
    directors: Optional[list[Person]]
    writers: Optional[list[Person]]
    actors_name: Optional[list[str]]
    director: Optional[list[str]]
    writers_names: Optional[list[str]]

    @validator("description")
    def set_description(cls, description):
        return description or ""
