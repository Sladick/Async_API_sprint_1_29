import log
import psycopg
import settings
from elastic_transport import ConnectionError as ESConnectionError
from elasticsearch import Elasticsearch
from extractors import BaseExtractor, PostgresExtractor
from loaders import BaseLoader, ESLoader
from psycopg.rows import dict_row
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from service import NoNewDataError, backoff, es_closing, redis_closing
from state_rw import RedisStorage, State
from transformers import BaseTransformer, PgESTransformer


class ETL:
    """Главный класс. В качестве свойств передаются классы extractor, transformer, loader.
    Возвращает новые параметры состояния и результат перегрузки партии данных."""

    def __init__(
        self, extractor: BaseExtractor, transformer: BaseTransformer, loader: BaseLoader
    ):
        self.extractor = extractor
        self.transformer = transformer
        self.loader = loader

    def action(self):
        data = self.extractor.extract()
        new_state, transformed_data = self.transformer.transform(data)
        result = self.loader.load(transformed_data)
        return new_state, result


@backoff
def start_loads_pg_es():
    """Процедура подключения и перегрузки данных. В случае перехвата ошибки
    подключения или отсутствия новых данных - перезапускается с задержкой."""
    # conn_params = settings.get_connection_params()
    conn_params = settings.Settings().dict()
    es_conn = Elasticsearch(conn_params["es_params"]["host"], verify_certs=False)
    redis_conn = Redis(**conn_params["redis_params"])
    dsl = conn_params["pg_params"]
    pg_index_name = settings.pg_es_index_name
    tables = settings.tables
    logger = log.get_logger_settings()

    try:
        if not es_conn.indices.exists(index=pg_index_name):
            es_conn.indices.create(
                index=pg_index_name,
                settings=settings.es_settings,
                mappings=settings.es_mapping,
            )

        with psycopg.connect(**dsl, row_factory=dict_row) as pg_conn, es_closing(
            es_conn
            # АЛЕКСАНДР, ПОЖАЛУЙСТА, ОБРАТИТЕ ВНИМАНИЕ НА ЭТОТ КОММЕНТАРИЙ:
            # Я ИСПОЛЬЗУЮ ТРЕТЬЮ ВЕРСИЮ БИБЛИОТЕКИ PSYCOPG, В НЕЙ ЗАКРЫВАТЬ КОННЕКШЕН НЕ ОБЯЗАТЕЛЬНО:
            # https://www.psycopg.org/psycopg3/docs/basic/from_pg2.html#diff-with
        ) as es_conn_closing, redis_closing(redis_conn) as redis_conn_closing:
            while True:
                result = load_from_postgres(
                    pg_conn, es_conn_closing, redis_conn_closing, tables, pg_index_name
                )
                logger.info("Succesfully", extra={"response": result})

    except ESConnectionError as conn_error:
        logger.error("Elastic connection error", extra={"response": ""})
        raise conn_error

    except psycopg.OperationalError as conn_error:
        logger.error("PG connection error", extra={"response": ""})
        raise conn_error

    except RedisConnectionError as conn_error:
        logger.error("Redis connection error", extra={"response": ""})
        raise conn_error

    except NoNewDataError as nnd_error:
        logger.info(
            "Checking for new data in source (Postgres)", extra={"response": ""}
        )
        raise nnd_error from NoNewDataError()


def load_from_postgres(
    pg_conn: psycopg.connection,
    es_conn: Elasticsearch,
    redis_conn: Redis,
    tables: list,
    pg_index_name: str,
):
    """Загрузить данные из Postgres в ElasticSearch."""

    storage = RedisStorage(redis_conn)

    state = State(storage)
    pg_extractor = PostgresExtractor(pg_conn, tables, state)
    pg_es_transformer = PgESTransformer(state)
    es_loader = ESLoader(es_conn, index_name=pg_index_name)

    etl = ETL(extractor=pg_extractor, transformer=pg_es_transformer, loader=es_loader)

    new_state, result = etl.action()

    for k, v in new_state.items():
        state.set_state(k, str(v))

    return result


if __name__ == "__main__":
    while True:
        try:
            start_loads_pg_es()
        except (
            ESConnectionError,
            psycopg.OperationalError,
            RedisConnectionError,
            NoNewDataError,
        ) as err:
            continue
        else:
            break
