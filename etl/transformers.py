from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Any, Generator

from etl.models import GenresTransformModel, MoviesTransformModel, PersonsTransformModel
from service import NoNewDataError
from state_rw import State


class BaseTransformer(ABC):
    """Abstract class for all transformers."""

    @abstractmethod
    def transform(self, transform_model: Any, data: dict) -> tuple[dict, Generator]:
        """Transform data from data source format to data storage format"""
        pass


class PgESTransformer(BaseTransformer):
    """Main PG - ES Transformer."""

    def __init__(self, state: State):
        self.state = state

    def transform(self, table_name: str, transform_model, data: list) -> tuple[dict, Generator]:
        """Transform data and get new state parameters"""
        if not data:
            raise NoNewDataError()

        new_data = self.__get_new_objects(transform_model, data)

        return new_data

    @staticmethod
    def __get_new_objects(transform_model, lst) -> Generator:
        for i in lst:
            transformed_object = transform_model(**i)
            yield transformed_object.as_dict()
