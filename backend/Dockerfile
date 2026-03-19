# ЭТАП 1: Сборка зависимостей
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Устанавливаем poetry
RUN pip install poetry==1.8.3

# Системные зависимости для сборки (psycopg2)
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* ./

# Устанавливаем зависимости (без dev-групп)
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# ЭТАП 2: Рантайм
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# libpq нужна для работы psycopg2 в рантайме
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

# Копируем виртуальное окружение
COPY --from=builder /app/.venv /app/.venv

# Создаём директорию для генерированных PDF
RUN mkdir -p /app/generated

# Копируем исходники приложения
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]