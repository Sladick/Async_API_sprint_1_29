from abc import ABC, abstractmethod

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


class BaseLoader(ABC):
    @abstractmethod
    def load(self, data):
        pass


class ESLoader(BaseLoader):
    def __init__(self, es: Elasticsearch, index_name: str):
        self.es = es
        self.index_name = index_name

    def load(self, data) -> tuple:
        bulk_data = []
        for row in data:
            bulk_data.append(
                {"_index": self.index_name, "_id": row["id"], "_source": row}
            )
        return bulk(self.es, bulk_data)
