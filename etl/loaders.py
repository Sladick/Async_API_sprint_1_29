from abc import ABC, abstractmethod
from typing import List, Generator

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


class BaseLoader(ABC):
    @abstractmethod
    def load(self, data: Generator, index_name: str):
        pass


class ESLoader(BaseLoader):
    def __init__(self, es: Elasticsearch):
        self.es = es

    def load(self, data: Generator, index_name: str) -> tuple:
        bulk_data = []
        for row in data:
            bulk_data.append(
                {"_index": index_name, "_id": row["id"], "_source": row}
            )
        return bulk(self.es, bulk_data)
