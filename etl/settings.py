import os

from dotenv import load_dotenv
from pydantic import BaseSettings, Field


class PostgresBaseSettingsSettings(BaseSettings):
    dbname: str
    user: str = Field(env="dbuser")
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
    host: str = Field(env="redis_host")
    port: int = Field(env="redis_port")

    class Config:
        env_file = ".env"


class RedisDevSettings(RedisBaseSettings):
    class Config:
        env_file = "dev.env"


class RedisProdSettings(RedisBaseSettings):
    class Config:
        env_file = ".env"


class ESBaseSettings(BaseSettings):
    host: str = Field(env="es_host")

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

    pg_config = dict(dev=PostgresDevSettings, prod=PostgresProdSettings)
    pg_params: PostgresBaseSettingsSettings = pg_config[
        os.environ.get("ENV", "dev").lower()
    ]()

    redis_config = dict(dev=RedisDevSettings, prod=RedisProdSettings)
    redis_params: RedisBaseSettings = redis_config[
        os.environ.get("ENV", "dev").lower()
    ]()

    es_config = dict(dev=ESDevSettings, prod=ESProdSettings)
    es_params: ESBaseSettings = es_config[os.environ.get("ENV", "dev").lower()]()

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


settings = Settings()


base_es_settings = {
        'refresh_interval': '1s',
        'analysis':
            {
                'filter': {
                    'english_stop': {'type': 'stop', 'stopwords': '_english_'},
                    'english_stemmer': {'type': 'stemmer', 'language': 'english'},
                    'english_possessive_stemmer': {'type': 'stemmer', 'language': 'possessive_english'},
                    'russian_stop': {'type': 'stop', 'stopwords': '_russian_'},
                    'russian_stemmer': {'type': 'stemmer', 'language': 'russian'}
                },
                'analyzer': {
                    'ru_en': {
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'english_stop', 'english_stemmer', 'english_possessive_stemmer',
                                   'russian_stop', 'russian_stemmer']
                    }
                }
            },
}

es_movies_mapping = {
    "dynamic": "strict",
    "properties": {
        "id": {"type": "keyword"},
        "imdb_rating": {"type": "float"},
        "title": {
            "type": "text",
            "analyzer": "ru_en",
            "fields": {"raw": {"type": "keyword"}},
        },
        "description": {"type": "text", "analyzer": "ru_en"},
        "director": {"type": "text", "analyzer": "ru_en"},
        "actors_names": {"type": "text", "analyzer": "ru_en"},
        "writers_names": {"type": "text", "analyzer": "ru_en"},
        "genre": {
            "type": "nested",
            "dynamic": "strict",
            "properties": {
                "id": {"type": "keyword"},
                "name": {"type": "text", "analyzer": "ru_en"},
            },
        },
        "directors": {
            "type": "nested",
            "dynamic": "strict",
            "properties": {
                "id": {"type": "keyword"},
                "name": {"type": "text", "analyzer": "ru_en"},
            },
        },
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
        "modified": {
            "type": "date"
        }
    },
}

es_genres_mapping = {
    "dynamic": "strict",
    "properties": {
        "id": {"type": "keyword"},
        "genre_name": {
            "type": "text",
            "analyzer": "ru_en",
            "fields": {"raw": {"type": "keyword"}},
        },
        "description": {"type": "keyword"},
        "modified": {
            "type": "date"
        }
    },
}

es_persons_mapping = {
    "dynamic": "strict",
    "properties": {
        "id": {"type": "keyword"},
        "full_name": {
            "type": "text",
            "analyzer": "ru_en",
            "fields": {"raw": {"type": "keyword"}},
        },
        "modified": {
            "type": "date"
        }
    },
}

pg_es_index_name_with_mappings_dict = {
    "movies": es_movies_mapping,
    "genres": es_genres_mapping,
    "persons": es_persons_mapping
}


index_to_tables_dict = {
    "movies": {
        "table_name": "film_work",
        "select_query": """SELECT
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
                      COALESCE (
                           json_agg(
                               DISTINCT jsonb_build_object(
                                   'genre_id', g.id,
                                   'genre_name', g.name
                               )
                           ) FILTER (WHERE g.id is not null),
                           '[]'
                        ) as genres
                       FROM content.film_work fw
                       LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
                       LEFT JOIN content.person p ON p.id = pfw.person_id
                       LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
                       LEFT JOIN content.genre g ON g.id = gfw.genre_id
                       WHERE fw.modified > %(state)s::timestamp OR p.modified > %(state)s::timestamp OR g.modified > %(state)s::timestamp
                       GROUP BY fw.id
                       ORDER BY fw.modified DESC;
                       """,
    },
    "persons": {
        "table_name": "person",
        "select_query": """SELECT
                               p.id,
                               p.full_name,
                               p.modified
                           FROM content.person p
                           WHERE p.modified > %(state)s::timestamp
                           GROUP BY p.id
                           ORDER BY p.modified DESC;
                           """,
    },
    "genres": {
        "table_name": "genre",
        "select_query": """SELECT
                               g.id,
                               g.name,
                               g.description,
                               g.modified
                           FROM content.genre g
                           WHERE g.modified > %(state)s::timestamp             
                           GROUP BY g.id
                           ORDER BY g.modified DESC;
                           """,
    },
}
