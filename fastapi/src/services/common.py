from pydantic import UUID4, BaseModel


class CommonQueryParams:
    sorts = {
        "imdb_rating": {"imdb_rating": "asc"},
        "-imdb_rating": {"imdb_rating": "desc"},
    }

    def __init__(self, page: int = 1, size: int = 20, sort: str | None = None):
        self.page = page
        self.size = size
        self.from_ = (page - 1) * size

        if sort in self.sorts:
            self.sort = self.sorts[sort]
        else:
            self.sort = None

    def __str__(self):
        """Нужна для корректного формированию ключа в кэше (Redis)."""
        return f"sort={self.sort}&page={self.from_}&size={self.size}"


class Uuid(BaseModel):
    uuid: UUID4

    def __str__(self):
        """Нужна для корректного формированию ключа в кэше (Redis)."""
        return f"uuid={self.uuid}"
