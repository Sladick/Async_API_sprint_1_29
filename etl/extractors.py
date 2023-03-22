"""Экстракторы и загрузчики."""

from abc import ABC, abstractmethod
from datetime import datetime

from psycopg import connection
from state_rw import State


class BaseExtractor(ABC):
    """Abstract class for all Extractors."""

    @abstractmethod
    def extract(self, table_name: str, select_query: str) -> dict:
        """Извлечь данные из источника"""
        pass


class PostgresExtractor(BaseExtractor):
    """Postgres extractor."""

    def __init__(self, pg_connection: connection, state: State):
        self.pg_connection = pg_connection
        self.state = state

    def extract(self, table_name: str, select_query: str) -> list:
        """Return data as dict, where key - source table name and value - extracted data."""
        modified_param = "%s_last_id" % table_name
        modified_state = self.state.get_state(modified_param) or datetime.min
        with self.pg_connection.cursor() as cur:
            cur.execute(select_query, {"state": modified_state})
            data = cur.fetchall()

        return data
