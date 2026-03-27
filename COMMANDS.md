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

---

## Авторизация и базовый фасет

### ⚙️ Конфигурация

Перед запуском приложения скопируйте `.env.example` файлы и отредактируйте их:

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env.local
```

**Важные переменные:**

- `backend/.env`: DATABASE_URL, SECRET_KEY, OPENROUTER_API_KEY
- `frontend/.env.local`: NEXT_PUBLIC_API_URL (должен указывать на backend)

### 🔐 Использование авторизации

1. **Регистрация**: `/auth/register` - email, username, password (≥8 символов, буквы + цифры)
2. **Логин**: `/auth/login` - email, password
3. **Защищенные маршруты**: `/dashboard`, `/moodboard` требуют авторизации
4. **Выход**: кнопка "Выйти" в Header
5. **Refresh токены**: автоматический если session истекла (Ctrl+R)

#### Тестовые учетные данные (для разработки)

```
Email: test@example.com
Username: testuser
Password: TestPass123
```

### 📚 Документация

Полное руководство по авторизации см. в [QUICKSTART_AUTH.md](./QUICKSTART_AUTH.md)
