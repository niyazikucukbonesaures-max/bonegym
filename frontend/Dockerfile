# ── Aşama 1: Build ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Bağımlılıkları önce kopyala — Docker layer cache optimizasyonu
COPY package.json package-lock.json* ./
RUN npm ci --frozen-lockfile

# Kaynak kodu kopyala
COPY . .

# Build-time API URL argümanı (Fly.io --build-arg ile geçilir)
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Production build
RUN npm run build

# ── Aşama 2: Serve ───────────────────────────────────────────────────────────
FROM nginx:alpine

# Özel nginx konfigürasyonu (React Router + güvenlik header'ları)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Build çıktısını nginx'e kopyala
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
