# Развёртывание MoodBrief на тестовом сервере

Цель: поднять приложение на свежем Linux-сервере по SSH одной командой
`docker compose up -d`. HTTPS не настраиваем — это тестовый стенд.

> Все шаги предполагают Ubuntu / Debian. На других дистрибутивах
> отличаются только пакетные менеджеры.

---

## 1. Подготовка сервера (один раз)

```bash
ssh user@SERVER_IP

# 1.1. Базовые пакеты
sudo apt update && sudo apt -y upgrade
sudo apt -y install git curl ufw

# 1.2. Docker + compose plugin
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Выйти/зайти в SSH, чтобы группа подтянулась:
exit
ssh user@SERVER_IP
docker compose version    # проверка

# 1.3. Файрвол: открыть только 22 и 80
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw --force enable
sudo ufw status
```

Порты `5432`, `8000`, `3000` **не открываем** наружу — внутри docker-сети
сервисы видят друг друга, а снаружи ходим только через nginx на 80.

---

## 2. Клонирование репозитория

```bash
mkdir -p ~/apps && cd ~/apps
git clone <URL_РЕПОЗИТОРИЯ> mood-brief
cd mood-brief
```

---

## 3. Конфигурация `.env`

```bash
cp .env.example .env
nano .env
```

Заполнить **минимум** эти переменные:

| Переменная           | Что туда                                                              |
| -------------------- | --------------------------------------------------------------------- |
| `DB_PASSWORD`        | Сильный пароль (например `openssl rand -base64 24`)                   |
| `DATABASE_URL`       | Подставить тот же пароль                                              |
| `OPENROUTER_API_KEY` | Свежий ключ с https://openrouter.ai/keys                              |
| `SECRET_KEY`         | `openssl rand -hex 48` — JWT-секрет                                   |
| `BACKEND_CORS_ORIGINS` | `["http://SERVER_IP"]` (или домен, если есть)                       |
| `COOKIE_SECURE`      | `False` (т.к. HTTP)                                                   |
| `ALLOW_DEVTUNNELS`   | `False`                                                               |

Удобный однострочник для генерации секретов:

```bash
echo "SECRET_KEY=$(openssl rand -hex 48)" >> .env
echo "DB_PASSWORD=$(openssl rand -base64 24)" >> .env
```

---

## 4. Запуск

```bash
docker compose up -d --build
docker compose ps     # все четыре сервиса должны быть Up
docker compose logs -f --tail=100
```

Проверка:

```bash
curl http://localhost/health
# → {"status":"ok","service":"mood-brief-backend","version":"0.2.0"}
```

Из браузера: `http://SERVER_IP/`.

---

## 5. Обновление кода

```bash
cd ~/apps/mood-brief
git pull
docker compose up -d --build
```

Откат:

```bash
git checkout <prev-commit>
docker compose up -d --build
```

---

## 6. Бэкап БД

```bash
# Дамп
docker compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > backup-$(date +%F).sql

# Восстановить
docker compose exec -T db psql -U "$DB_USER" "$DB_NAME" < backup-2026-05-26.sql
```

Раз в день в cron:

```cron
0 3 * * * cd /home/USER/apps/mood-brief && docker compose exec -T db pg_dump -U user moodbrief_db | gzip > backups/db-$(date +\%F).sql.gz
```

---

# Что было залатано перед деплоем

| Что                  | Где                                                  | Зачем                                                                                              |
| -------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `SECRET_KEY`         | `backend/app/config.py`                              | Логируется CRITICAL если оставлен дефолт; в проде обязательно через env                            |
| Cookie `secure`      | `backend/app/routes/auth.py`                         | Было захардкожено `True` + `samesite=strict` — на HTTP кука дропалась браузером; вынесено в конфиг |
| CORS devtunnels      | `backend/app/main.py`                                | Регекс `*.devtunnels.ms` теперь под флагом `ALLOW_DEVTUNNELS` — выключен по умолчанию              |
| `/api/auth/refresh`  | `backend/app/routes/auth.py`                         | Удалён мёртвый stub, возвращавший 501                                                              |
| Feedback GET         | `backend/app/routes/feedback.py`                     | Был анонимным — теперь требует auth + проверка владельца                                           |
| Лимит файлов analyze | `backend/app/routes/analyze.py`                      | Жёсткий MAX_FILES=10 на сервере (фронт-ограничение легко обходится)                                |
| Rate-limit auth      | `backend/app/routes/auth.py` + `nginx/default.conf`  | Per-IP лимиты на /api/auth/* (3 req/s в nginx + 10/мин в приложении)                               |
| nginx rate-limit API | `nginx/default.conf`                                 | Per-IP 10 req/s на /api/ — лечит примитивные DDoS / scrape                                         |
| Security headers     | `nginx/default.conf`                                 | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`                                     |
| SSRF guard           | `backend/app/routes/fetch_url.py`                    | Резолв хоста, отказ для приватных / loopback / link-local IP                                       |
| .env.example         | корень                                               | Шаблон с пояснениями; `.env` уже в `.gitignore`                                                    |

---

# Чек-лист перед публичным запуском

- [ ] `.env` создан, в нём свежий `SECRET_KEY` и сильный `DB_PASSWORD`
- [ ] `OPENROUTER_API_KEY` — действующий, не из git-истории
- [ ] `BACKEND_CORS_ORIGINS` содержит только нужные домены / IP
- [ ] `ALLOW_DEVTUNNELS=False`
- [ ] UFW открывает только 22 и 80
- [ ] `docker compose ps` — все Up, healthcheck БД зелёный
- [ ] `curl http://SERVER_IP/health` отвечает 200
- [ ] Регистрация / логин работают; refresh после 15 минут продлевает сессию
- [ ] Бэкап БД настроен в cron
- [ ] (опционально) `fail2ban` на /api/auth/login по логам nginx

---

# Известные ограничения и что доделать перед прод-боем

1. **HTTPS.** На тесте опущен по согласованию. Перед открытием на публику —
   подключить TLS (Cloudflare-proxy или Caddy / Certbot + nginx). После
   включения выставить `COOKIE_SECURE=True`.
2. **Rate-limit в памяти процесса.** При горизонтальном масштабировании
   заменить in-process счётчик в `auth.py` на slowapi+Redis.
3. **Хранилище PDF.** `/app/generated` живёт внутри контейнера backend —
   при пересоздании контейнера PDF не теряются (тома нет!). Если важно
   сохранять — добавить в `docker-compose.yml`:
   ```yaml
   backend:
     volumes:
       - generated_pdfs:/app/generated
   volumes:
     generated_pdfs:
   ```
4. **Логи.** Сейчас только stdout контейнеров. Для прод-стенда —
   `docker compose logs` ротируется через `logging.driver=json-file` с
   `max-size`/`max-file`, либо подключить Loki / journald.
5. **БД-миграции.** Сейчас схема создаётся `Base.metadata.create_all` —
   нормально для теста, но любое изменение модели потребует ручного
   `ALTER TABLE`. Перед прод-боем — Alembic.
