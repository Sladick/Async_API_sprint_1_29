from pydantic import UUID4, BaseModel
from fastapi import Depends


class GenreFilter(BaseModel):

    genre: UUID4 | None = None

    def __str__(self):
        """Нужна для корректного формированию ключа в кэше (Redis)."""
        return f"genre={self.genre}"


class MatchQuery(BaseModel):
    query: str

    def __str__(self):
        """Нужна для корректного формированию ключа в кэше (Redis)."""
        return f"query={self.query}"


class FilmQuery:
    def __init__(self, filter_: GenreFilter | None, match_query: MatchQuery | None):

        self.filter_ = filter_
        self.match_query = match_query

        if self.filter_ is not None:
            self.query = {
                "bool": {
                    "filter": {
                        "nested": {
                            "path": "genre",
                            "query": {"term": {"genre.id": str(self.filter_.genre)}},
                        }
                    }
                }
            }
        elif self.match_query is not None:
            self.query = {
                "multi_match": {
                    "query": self.match_query.query,
                    "fields": ["title^3", "description"],
                    "fuzziness": "AUTO",
                }
            }
        else:
            self.query = {"match_all": {}}

    def __str__(self):
        """Нужна для корректного формированию ключа в кэше (Redis)."""
        return f"filter_={self.filter_}&match_query={self.match_query}"
