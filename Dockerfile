FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BIONIC_DB_PATH=/app/bionic.db

WORKDIR /app

RUN pip install --no-cache-dir \
    "fastapi>=0.116,<1" \
    "uvicorn[standard]>=0.35,<1"

RUN groupadd --system bionicdb \
    && useradd --system --gid bionicdb --home-dir /app bionicdb

COPY --chown=bionicdb:bionicdb api/app /app/api/app
COPY --chown=bionicdb:bionicdb api/static /app/api/static
COPY --chown=bionicdb:bionicdb bionic.db /app/bionic.db
COPY --chown=bionicdb:bionicdb objects /app/objects

USER bionicdb
WORKDIR /app/api

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
