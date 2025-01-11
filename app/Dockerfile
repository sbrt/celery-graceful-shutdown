FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN pip install poetry

WORKDIR /app
COPY src/app/ .
COPY entrypoint.sh pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false && poetry install --no-root --no-cache --no-interaction

EXPOSE 8000

ENTRYPOINT [ "./entrypoint.sh" ]
