from fastapi import Query
from pydantic import BaseModel, UUID4


class CommonQueryParamsMixin:
    def __init__(
            self,
            sort: str = Query(None, description='Сортировка данных по полям. Пример: field_name:(asc|desc),field_name:(asc|desc)'),
            page: int = Query(default=1),
            size: int = Query(default=20, ge=1, le=50),
            filter_: str = Query(None, alias='filter', description='Текст фильтрации данных')

    ):
        self.sort: str = sort
        self.page: int = page
        self.size: int = size
        self.from_: int = size * (page-1)
        self.filter_: str = filter_


class CommonQueryParams:
    sorts = {
        "imdb_rating": {"imdb_rating": "asc"},
        "-imdb_rating": {"imdb_rating": "desc"},
    }

    def __init__(self, page: int = 1, size: int = 20, sort: str | None = None):
        self.from_ = (page - 1) * size
        self.size = size
        self.sort = self.sorts.get(sort)

    def __str__(self):
        """Нужна для корректного формированию ключа в кэше (Redis)."""
        return f"sort={self.sort}&page={self.from_}&size={self.size}"


class Uuid(BaseModel):
    uuid: UUID4

    def __str__(self):
        """Нужна для корректного формированию ключа в кэше (Redis)."""
        return f"uuid={self.uuid}"
