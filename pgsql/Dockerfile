FROM postgres:13

ENV POSTGRES_USER=app
ENV POSTGRES_PASSWORD=cegth
ENV POSTGRES_DB=movies_database
      
COPY ./movies_database.sql /docker-entrypoint-initdb.d/dump.sql
COPY ./entry_script.sh /docker-entrypoint-initdb.d/entry_script.sh


EXPOSE 5432
