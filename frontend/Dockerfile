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

# Копируем установленные node_modules из первого этапа
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Собираем оптимизированный билд
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