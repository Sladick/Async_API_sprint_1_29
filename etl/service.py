import time
from contextlib import contextmanager
from functools import wraps


def backoff(_func=None, *, start_sleep_time=0.1, factor=2, border_sleep_time=10):
    """
    Функция для повторного выполнения функции через некоторое время, если возникла ошибка. Использует наивный экспоненциальный рост времени повтора (factor) до граничного времени ожидания (border_sleep_time)

    Формула:
        t = start_sleep_time * 2^(n) if t < border_sleep_time
        t = border_sleep_time if t >= border_sleep_time
    :param start_sleep_time: начальное время повтора
    :param factor: во сколько раз нужно увеличить время ожидания
    :param border_sleep_time: граничное время ожидания
    :return: результат выполнения функции
    """

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if inner.t < border_sleep_time:
                inner.t = inner.t * 2**factor
            else:
                inner.t = border_sleep_time
            time.sleep(inner.t)
            return func(*args, **kwargs)

        inner.t = start_sleep_time
        return inner

    if _func is None:
        return func_wrapper
    else:
        return func_wrapper(_func)


class NoNewDataError(Exception):
    def __str__(self):
        return "No new data to extract"


@contextmanager
def es_closing(conn):
    try:
        yield conn
    finally:
        conn.transport.close()


@contextmanager
def redis_closing(conn):
    try:
        yield conn
    finally:
        conn.close()
