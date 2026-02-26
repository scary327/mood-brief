FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Системные зависимости (libpq нужна для psycopg2)
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

# Копируем только манифест и ставим зависимости через pip
COPY pyproject.toml ./
RUN pip install --no-cache-dir "fastapi>=0.133.1,<0.134.0" \
    "uvicorn>=0.41.0,<0.42.0" \
    "sqlalchemy>=2.0.47,<3.0.0" \
    "psycopg2-binary>=2.9.11,<3.0.0" \
    "pydantic-settings>=2.13.1,<3.0.0" \
    "python-multipart>=0.0.22,<0.0.23"

# Копируем исходники приложения
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]