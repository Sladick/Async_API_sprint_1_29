"""Экстракторы и загрузчики."""

from abc import ABC, abstractmethod

from psycopg import connection

from state_rw import State


class BaseExtractor(ABC):
    """Abstract class for all Extractors."""

    @abstractmethod
    def extract(self) -> dict:
        """Извлечь данные из источника"""
        pass


class PostgresExtractor(BaseExtractor):
    """Postgres extractor."""

    def __init__(
        self, connection: connection, tables: list, state: State, n: int = 100
    ):
        self.connection = connection
        self.tables = tables
        self.state = state
        self.n = n

    def extract(self) -> dict:
        """Return data as dict, where key - source table name and value - extracted data."""
        data = {}
        for table in self.tables:
            table_name = table["table_name"]
            modified_param = f"{table_name}_last_id"
            modified_state = (
                self.state.get_state(modified_param)
                if self.state.get_state(modified_param) is not None
                else "00000000-0000-0000-0000-000000000000"
            )
            with self.connection.cursor() as cur:
                cur.execute(
                    table["select_query"], {"uuid": modified_state, "n": self.n}
                )
                data[table_name] = cur.fetchall()

        return data
