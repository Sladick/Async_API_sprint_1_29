class CommonQueryParams:
    sorts = {"imdb_rating": "imdb_rating"}

    def __init__(self, sort: str | None = None, page: int = 0, size: int = 20):
        self.from_ = page * size
        self.size = size
        if sort in self.sorts:
            self.sort = self.sorts[sort]
        else:
            self.sort = None

    def __str__(self):
        return f"sort={self.sort}&page={self.from_}&size={self.size}"


class GenreFilter:
    def __init__(self, genre: str | None = None):
        self.genre = genre

    def __str__(self):
        return f"genre={self.genre}"
