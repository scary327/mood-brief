# Docker команды

> Все команды запускаются из корня проекта (`mood-brief/`)

## Запуск / Остановка

```bash
# Запустить всё (с пересборкой образов)
docker-compose up --build -d

# Запустить без пересборки
docker-compose up -d

# Остановить
docker-compose down

# Остановить и удалить volumes (БД сбросится!)
docker-compose down -v
```

## Перезапуск

```bash
# Перезапустить конкретный сервис
docker-compose restart backend
docker-compose restart frontend

# Пересобрать и перезапустить один сервис
docker-compose up --build -d backend
```

## Логи

```bash
# Логи всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db

# Последние 50 строк бэкенда
docker-compose logs --tail=50 backend
```

## Статус

```bash
# Посмотреть статус контейнеров
docker-compose ps
```

## URL

| Сервис      | URL                        |
| ----------- | -------------------------- |
| Frontend    | http://localhost:3000      |
| Backend API | http://localhost:8000      |
| Swagger UI  | http://localhost:8000/docs |
