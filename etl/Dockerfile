FROM python:3.10

WORKDIR /opt/app

ENV YOUR_ENV=production
ENV PATH="$POETRY_HOME/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=1
ENV POETRY_VERSION=1.3.2

ENV DB_HOST 'new_admin_panel_sprint_3-postgres-1'

RUN pip install "poetry==$POETRY_VERSION"

COPY poetry.lock pyproject.toml .

RUN POETRY_VIRTUALENVS_CREATE=false \
  && poetry install $(test "$YOUR_ENV" == production && echo "--no-dev") --no-interaction --no-ansi --no-root

COPY . .


ENTRYPOINT ["poetry", "run", "python", "main.py"]
