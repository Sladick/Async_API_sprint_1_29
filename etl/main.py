from datetime import datetime
import psycopg
from elastic_transport import ConnectionError as ESConnectionError
from elasticsearch import Elasticsearch
from psycopg.rows import dict_row
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError


import log
from extractors import PostgresExtractor
from loaders import ESLoader
from models import transform_model_dict
from service import NoNewDataError, backoff, es_closing, redis_closing
from settings import base_es_settings, settings, pg_es_index_name_with_mappings_dict, index_to_tables_dict
from state_rw import RedisStorage, State
from transformers import PgESTransformer


class ETL:
    """Главный класс. В качестве свойств передаются классы extractor, transformer, loader.
    Возвращает новые параметры состояния и результат перегрузки партии данных."""

    def __init__(
        self, extractor: PostgresExtractor, transformer: PgESTransformer, loader: ESLoader, state: State
    ):
        self.extractor = extractor
        self.transformer = transformer
        self.loader = loader
        self.state = state

    def get_new_state(self, pg_index_name, table_name):
        state_key = "%s_last_id" % table_name
        try:
            new_state = {
                state_key: self.loader.es.search(
                    index=pg_index_name,
                    body={
                        "query": {"match_all": {}},
                        "sort": [{"modified": {"order": "desc"}}],
                        "size": 1
                    }
                )["hits"]["hits"][0]["_source"]["modified"]
            }
        except (IndexError, KeyError):
            new_state = {state_key: self.state.get_state(state_key)}

        return new_state

    def action(self, table_name, select_query, transform_model, pg_index_name):
        data = self.extractor.extract(table_name, select_query)
        transformed_data = self.transformer.transform(table_name, transform_model, data)
        result = self.loader.load(transformed_data, pg_index_name)
        return self.get_new_state(pg_index_name, table_name), result


@backoff
def start_loads_pg_es():
    """
    Процедура подключения и перегрузки данных.
    В случае перехвата ошибки подключения или отсутствия новых данных - перезапускается с задержкой.
    """
    es_conn = Elasticsearch(settings.es_params.host, verify_certs=False)
    redis_conn = Redis(**settings.redis_params.dict())
    logger = log.get_logger_settings()

    try:
        with psycopg.connect(**settings.pg_params.dict(), row_factory=dict_row) as pg_conn, es_closing(
                es_conn) as es_conn_closing, redis_closing(redis_conn) as redis_conn_closing:
            for pg_es_index_name, es_mappings in pg_es_index_name_with_mappings_dict.items():
                try:
                    if not es_conn.indices.exists(index=pg_es_index_name):
                        es_conn.indices.create(index=pg_es_index_name, settings=base_es_settings, mappings=es_mappings)

                    result = load_from_postgres(pg_conn, es_conn_closing, redis_conn_closing, pg_es_index_name)
                    logger.info("Succesfully index %s" % pg_es_index_name, extra={"response": result})
                except NoNewDataError:
                    logger.info(
                        "Checking for new data in source (Postgres)", extra={"response": ""}
                    )

    except ESConnectionError as conn_error:
        logger.error("Elastic connection error", extra={"response": ""})
        raise conn_error

    except psycopg.OperationalError as conn_error:
        logger.error("PG connection error", extra={"response": ""})
        raise conn_error

    except RedisConnectionError as conn_error:
        logger.error("Redis connection error", extra={"response": ""})
        raise conn_error


def load_from_postgres(
        pg_conn: psycopg.connection, es_conn: Elasticsearch, redis_conn: Redis, pg_index_name: str
) -> str:
    """Загрузить данные из Postgres в ElasticSearch."""

    storage = RedisStorage(redis_conn)
    state = State(storage)
    pg_extractor = PostgresExtractor(pg_conn, state)
    pg_es_transformer = PgESTransformer(state)
    es_loader = ESLoader(es_conn)
    table_name = index_to_tables_dict.get(pg_index_name)["table_name"]
    select_query = index_to_tables_dict.get(pg_index_name)["select_query"]
    transform_model = transform_model_dict.get(pg_index_name)

    etl = ETL(extractor=pg_extractor, transformer=pg_es_transformer, loader=es_loader, state=state)

    new_state, result = etl.action(table_name, select_query, transform_model, pg_index_name)

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
