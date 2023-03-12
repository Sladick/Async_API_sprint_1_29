import os

from dotenv import load_dotenv
from pydantic import BaseSettings, Field
from pydantic.env_settings import SettingsSourceCallable


class PostgresBaseSettingsSettings(BaseSettings):
    dbname: str
    user: str = Field(env='dbuser')
    password: str
    host: str
    port: int

    class Config:
        env_file = ".env"


class PostgresDevSettings(PostgresBaseSettingsSettings):
    class Config:
        env_file = "dev.env"


class PostgresProdSettings(PostgresBaseSettingsSettings):
    class Config:
        env_file = ".env"


class RedisBaseSettings(BaseSettings):

    redis_host: str
    redis_port: int

    class Config:
        env_file = ".env"


class RedisDevSettings(RedisBaseSettings):

    class Config:
        env_file = "dev.env"


class RedisProdSettings(RedisBaseSettings):
    class Config:
        env_file = ".env"


class ESBaseSettings(BaseSettings):

    es_host: str

    class Config:
        env_file = ".env"


class ESDevSettings(ESBaseSettings):

    class Config:
        env_file = "dev.env"


class ESProdSettings(ESBaseSettings):
    class Config:
        env_file = ".env"


class Settings(BaseSettings):
    """Settings for establishing all connections."""
    pg_config = dict(
        dev=PostgresDevSettings,
        prod=PostgresProdSettings
    )
    pg_params: PostgresBaseSettingsSettings = pg_config[os.environ.get('ENV', 'dev').lower()]()

    redis_config = dict(
        dev=RedisDevSettings,
        prod=RedisProdSettings
    )
    redis_params: RedisBaseSettings = redis_config[os.environ.get('ENV', 'dev').lower()]()

    es_config = dict(
        dev=ESDevSettings,
        prod=ESProdSettings
    )
    es_params: ESBaseSettings = es_config[os.environ.get('ENV', 'dev').lower()]()

    class Config:
        env_file = ".env"





def get_connection_params():
    """Returns all connection parameters as dict."""
    load_dotenv()
    dsl = {
        "dbname": os.environ.get("dbname"),
        "user": os.environ.get("user"),
        "password": os.environ.get("password"),
        "host": os.environ.get("host"),
        "port": int(os.environ.get("port")),
    }

    es_params = os.environ.get("es_host")

    redis_params = {
        "host": os.environ.get("redis_host"),
        "port": os.environ.get("redis_port"),
    }

    return {"dsl": dsl, "es_params": es_params, "redis_params": redis_params}


pg_es_index_name = "movies"


tables = [
    {
        "table_name": "film_work",
        "select_query": """SELECT
                       fw.id as key,
                       fw.id,
                       fw.title,
                       fw.description,
                       fw.rating,
                       fw.type,
                       fw.created,
                       fw.modified,
                       COALESCE (
                           json_agg(
                               DISTINCT jsonb_build_object(
                                   'person_role', pfw.role,
                                   'person_id', p.id,
                                   'person_name', p.full_name
                               )
                           ) FILTER (WHERE p.id is not null),
                           '[]'
                        ) as persons,
                       array_agg(DISTINCT COALESCE(g.name, '')) as genres
                       FROM content.film_work fw
                       LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
                       LEFT JOIN content.person p ON p.id = pfw.person_id
                       LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
                       LEFT JOIN content.genre g ON g.id = gfw.genre_id
                       WHERE fw.id > %(uuid)s
                       GROUP BY fw.id
                       ORDER BY fw.modified, fw.id
                       LIMIT %(n)s;""",
    },
    {
        "table_name": "person",
        "select_query": """SELECT
                           p.id as key,
                           fw.id,
                           fw.title,
                           fw.description,
                           fw.rating,
                           fw.type,
                           max(p.created) as created,
                           max(p.modified) as modified,
                           COALESCE (
                               json_agg(
                                   DISTINCT jsonb_build_object(
                                       'person_role', pfw.role,
                                       'person_id', p.id,
                                       'person_name', p.full_name
                                   )
                               ) FILTER (WHERE p.id is not null),
                               '[]'
                            ) as persons,
                           array_agg(DISTINCT COALESCE(g.name, '')) as genres
                           FROM content.person p
                           LEFT JOIN content.person_film_work pfw ON pfw.person_id = p.id
                           LEFT JOIN content.film_work fw ON fw.id = pfw.film_work_id
                           LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
                           LEFT JOIN content.genre g ON g.id = gfw.genre_id
                           WHERE p.id > %(uuid)s
                           GROUP BY p.id, fw.id
                           ORDER BY max(p.modified), fw.id
                           LIMIT %(n)s""",
    },
    {
        "table_name": "genre",
        "select_query": """SELECT
                               g.id as key,
                               fw.id,
                               fw.title,
                               fw.description,
                               fw.rating,
                               fw.type,
                               max(g.created) as created,
                               max(g.modified) as modified,
                               COALESCE (
                                   json_agg(
                                       DISTINCT jsonb_build_object(
                                           'person_role', pfw.role,
                                           'person_id', p.id,
                                           'person_name', p.full_name
                                       )
                                   ) FILTER (WHERE p.id is not null),
                                   '[]'
                                ) as persons,
                               array_agg(DISTINCT COALESCE(g.name, '')) as genres
                               FROM content.genre g
                               LEFT JOIN content.genre_film_work gfw ON gfw.genre_id = g.id
                               LEFT JOIN content.film_work fw ON fw.id = gfw.film_work_id
                               LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
                               LEFT JOIN content.person p ON p.id = pfw.person_id
                               WHERE g.id > %(uuid)s                              
                               GROUP BY g.id, fw.id
                               ORDER BY max(g.modified), fw.id
                               LIMIT %(n)s""",
    },
]


es_settings = {
    "refresh_interval": "1s",
    "analysis": {
        "filter": {
            "english_stop": {"type": "stop", "stopwords": "_english_"},
            "english_stemmer": {"type": "stemmer", "language": "english"},
            "english_possessive_stemmer": {
                "type": "stemmer",
                "language": "possessive_english",
            },
            "russian_stop": {"type": "stop", "stopwords": "_russian_"},
            "russian_stemmer": {"type": "stemmer", "language": "russian"},
        },
        "analyzer": {
            "ru_en": {
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "english_stop",
                    "english_stemmer",
                    "english_possessive_stemmer",
                    "russian_stop",
                    "russian_stemmer",
                ],
            }
        },
    },
}
es_mapping = {
    "dynamic": "strict",
    "properties": {
        "id": {"type": "keyword"},
        "imdb_rating": {"type": "float"},
        "genre": {"type": "keyword"},
        "title": {
            "type": "text",
            "analyzer": "ru_en",
            "fields": {"raw": {"type": "keyword"}},
        },
        "description": {"type": "text", "analyzer": "ru_en"},
        "director": {"type": "text", "analyzer": "ru_en"},
        "actors_names": {"type": "text", "analyzer": "ru_en"},
        "writers_names": {"type": "text", "analyzer": "ru_en"},
        "actors": {
            "type": "nested",
            "dynamic": "strict",
            "properties": {
                "id": {"type": "keyword"},
                "name": {"type": "text", "analyzer": "ru_en"},
            },
        },
        "writers": {
            "type": "nested",
            "dynamic": "strict",
            "properties": {
                "id": {"type": "keyword"},
                "name": {"type": "text", "analyzer": "ru_en"},
            },
        },
    },
}
