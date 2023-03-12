from abc import ABC, abstractmethod
from typing import Generator

from models import MoviesTransformModel
from service import NoNewDataError
from state_rw import State


class BaseTransformer(ABC):
    """Abstract class for all transformers."""

    @abstractmethod
    def transform(self, data: dict) -> tuple[dict, Generator]:
        """Transform data from data source format to data storage format"""
        pass


class PgESTransformer(BaseTransformer):
    """Main PG - ES Transformer."""

    def __init__(self, state: State):
        self.state = state

    def transform(self, data: dict) -> tuple[dict, Generator]:
        """Transform data and get new state parameters"""
        new_params = {}
        new_data = []
        for k, v in data.items():
            try:
                new_params[f"{k}_last_id"] = v[len(v) - 1]["key"]
            except IndexError:
                new_params[f"{k}_last_id"] = self.state.get_state(f"{k}_last_id")
            new_data = new_data + v

        if not len(list(new_data)):
            raise NoNewDataError()
        new_data = self.__get_new_objects(list(new_data))

        return new_params, new_data

    @staticmethod
    def __get_new_objects(lst) -> Generator:
        for i in lst:
            transformed_object = MoviesTransformModel(**i)
            yield transformed_object.as_dict()
