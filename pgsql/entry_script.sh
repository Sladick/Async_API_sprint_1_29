#!/bin/bash
set -e

psql movies_database app -f /docker-entrypoint-initdb.d/dump.sql

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	GRANT ALL PRIVILEGES ON SCHEMA content TO app;
	GRANT ALL PRIVILEGES ON DATABASE movies_database TO app;
EOSQL
