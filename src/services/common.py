

class CommonQueryParams:
    def __init__(self, sort: str | None = None, filter: str | None = None, page: int = 0, size: int = 20):
        self.sort = sort
        self.filter_genre = filter
        self.from_ = page * size
        self.size = size
