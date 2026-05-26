# ЭТАП 1: Установка зависимостей через npm ci
FROM node:20-alpine AS deps
WORKDIR /app

# Копируем оба файла, чтобы lock-file был доступен для ci
COPY package.json package-lock.json ./ 

# Устанавливаем зависимости строго по lock-файлу
RUN npm ci

# ЭТАП 2: Сборка (Build)
FROM node:20-alpine AS builder
WORKDIR /app

# NEXT_PUBLIC_* must be present at build time — Next bakes them into the
# client bundle. Pass via docker-compose build.args.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Копируем установленные node_modules из первого этапа
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Сборка Next 16 с Turbopack может съесть 3–4 GB RAM и упасть OOM на
# небольших VPS. Поднимаем лимит heap и собираем через webpack
# (см. флаг --webpack в package.json) — медленнее, зато стабильно.
ENV NODE_OPTIONS=--max-old-space-size=2048
RUN npm run build

# ЭТАП 3: Рантайм (Минимальный образ)
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# В Next.js для продакшена лучше всего использовать standalone режим
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]