import abc
import json
import os
from typing import Any, Optional

from redis import Redis


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        """Сохранить состояние в постоянное хранилище"""
        pass

    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        """Загрузить состояние локально из постоянного хранилища"""
        pass


class JsonFileStorage(BaseStorage):
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as file:
                pass

    def save_state(self, state: dict):
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(state, file)

    def retrieve_state(self):
        with open(self.file_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except:
                data = {}
            return data


class RedisStorage(BaseStorage):
    def __init__(self, redis_adapter: Redis):
        self.redis_adapter = redis_adapter

    def save_state(self, state: dict):
        self.redis_adapter.mset(state)

    def retrieve_state(self):
        keys = self.redis_adapter.keys("*")
        data = self.redis_adapter.mget(keys)
        return {
            key.decode("utf-8"): value.decode("utf-8") for key, value in zip(keys, data)
        }


class State:
    """
    Класс для хранения состояния при работе с данными, чтобы постоянно не перечитывать данные с начала.
    Здесь представлена реализация с сохранением состояния в файл.
    В целом ничего не мешает поменять это поведение на работу с БД или распределённым хранилищем.
    """

    def __init__(self, storage: BaseStorage):
        self.storage = storage

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа"""
        current_state = self.storage.retrieve_state()
        current_state[key] = value
        self.storage.save_state(current_state)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу"""
        current_state = self.storage.retrieve_state()
        if key in current_state:
            return current_state[key]
        else:
            return None
