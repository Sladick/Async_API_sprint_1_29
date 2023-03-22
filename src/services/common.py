from fastapi import Query


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
    sorts = {"imdb_rating": "imdb_rating"}

    def __init__(self, sort: str | None = None, page: int = 1, size: int = 20):
        self.from_ = page * size
        self.size = size
        self.sort = self.sorts.get(sort)

    def __str__(self):
        return f"sort={self.sort}&page={self.from_}&size={self.size}"


class GenreFilter:
    def __init__(self, genre: str | None = None):
        self.genre = genre

    def __str__(self):
        return f"genre={self.genre}"
