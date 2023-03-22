from typing import Optional

from src.models.mixins import OrjsonConfigMixin, UUIDMixin
from src.models.person import Person


class Film(UUIDMixin, OrjsonConfigMixin):
    actors: Optional[list[Person]]
    actors_name: Optional[list[str]]
    title: Optional[str]
    description: Optional[str] = None
    director: Optional[list[str]]
    genre: Optional[list[str]]
    imdb_rating: Optional[float]
    writers: Optional[list[Person]]
    writers_names: Optional[list[str]]
