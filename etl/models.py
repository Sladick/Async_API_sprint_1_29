from dataclasses import dataclass, field
from datetime import datetime


@dataclass()
class MoviesTransformModel:
    """Movies PG - ES Transform model."""

    key: str
    id: str
    title: str
    persons: list
    genres: list
    created: datetime
    modified: datetime
    rating: float = 0
    type: str = field(default="")
    description: str = field(default="")
    genre: list = field(init=False)
    director: list = field(init=False)
    actors_names: list = field(init=False)
    writers_names: list = field(init=False)
    directors: list = field(init=False)
    actors: list = field(init=False)
    writers: list = field(init=False)
    imdb_rating: float = field(init=False)

    def __post_init__(self):
        self.actors = [
            {"id": i["person_id"], "name": i["person_name"]}
            for i in self.persons
            if i["person_role"] == "actor"
        ]
        self.writers = [
            {"id": i["person_id"], "name": i["person_name"]}
            for i in self.persons
            if i["person_role"] == "writer"
        ]
        self.directors = [
            {"id": i["person_id"], "name": i["person_name"]}
            for i in self.persons
            if i["person_role"] == "director"
        ]
        self.actors_names = [
            i["person_name"] for i in self.persons if i["person_role"] == "actor"
        ]
        self.writers_names = [
            i["person_name"] for i in self.persons if i["person_role"] == "writer"
        ]
        self.director = [
            i["person_name"] for i in self.persons if i["person_role"] == "director"
        ]
        self.genre = [
            {"id": i["genre_id"], "name": i["genre_name"]}
            for i in self.genres
        ]
        self.imdb_rating = self.rating

    def as_dict(self) -> dict:
        """Returns ES required properties as dict."""
        rd = {
            "id": self.id,
            "imdb_rating": self.imdb_rating,
            "genre": self.genre,
            "title": self.title,
            "description": self.description,
            "director": self.director,
            "directors": self.directors,
            "actors_names": self.actors_names,
            "writers_names": self.writers_names,
            "actors": self.actors,
            "writers": self.writers,
        }
        return rd
