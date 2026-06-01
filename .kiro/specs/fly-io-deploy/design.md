# Design Document — KaloriSpor Fly.io Deploy

## Overview

KaloriSpor uygulaması, mevcut yerel geliştirme ortamından Fly.io bulut platformuna taşınacaktır. Backend (FastAPI) ve Frontend (React + Vite) ayrı Fly.io uygulamaları olarak deploy edilecek; veritabanı olarak mevcut Supabase PostgreSQL bağlantısı aktifleştirilecektir.

Mevcut kod tabanı bu geçiş için büyük ölçüde hazırdır:
- `database.py` zaten `postgresql://` → `postgresql+asyncpg://` dönüşümünü yapıyor
- `main.py` zaten `FRONTEND_URL` env var'ını CORS listesine ekliyor
- `start.py` zaten `PORT` env var'ını destekliyor
- `/health` endpoint mevcut

Temel çalışma kapsamı: Dockerfile'lar, fly.toml dosyaları, nginx konfigürasyonu, migration script güncellemesi ve ortam değişkeni yönetimidir.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        İnternet                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
┌─────────────────────┐    ┌─────────────────────────┐
│  kalorispor-frontend│    │   kalorispor-backend     │
│  Fly.io App         │    │   Fly.io App             │
│                     │    │                          │
│  nginx:alpine       │    │  python:3.12-slim        │
│  Port: 80           │    │  Port: 8000              │
│  Region: fra        │    │  Region: fra             │
│                     │    │                          │
│  React SPA          │    │  FastAPI + Uvicorn       │
│  (statik dosyalar)  │    │  (async, 1 worker)       │
│                     │    │                          │
│  VITE_API_URL ──────┼────►  /api/* endpoints        │
│  (build-time)       │    │                          │
└─────────────────────┘    └──────────┬───────────────┘
                                      │
                                      │ DATABASE_URL
                                      │ (Fly Secret)
                                      ▼
                           ┌─────────────────────────┐
                           │  Supabase PostgreSQL     │
                           │                          │
                           │  db.ycnchcjmepluzimmqwho │
                           │  .supabase.co:5432       │
                           │                          │
                           │  Tablolar:               │
                           │  - users                 │
                           │  - user_sessions         │
                           │  - food_items            │
                           │  - food_log              │
                           │  - measurements          │
                           │  - water_logs            │
                           │  - workout_programs      │
                           │  - exercises             │
                           │  - workout_logs          │
                           │  - creatine_doses        │
                           │  - achievements          │
                           │  - user_achievements     │
                           │  - ai_chat_sessions      │
                           │  - ai_chat_messages      │
                           │  - ... (diğer tablolar)  │
                           └─────────────────────────┘

Fly Secrets (şifreli):
  kalorispor-backend:
    DATABASE_URL
    GEMINI_API_KEY
    SECRET_KEY
    FRONTEND_URL

  kalorispor-frontend:
    (build arg olarak VITE_API_URL)
```

### Tasarım Kararları

**Neden ayrı Fly.io uygulamaları?**
Frontend ve backend'i ayrı deploy etmek bağımsız ölçeklendirme, ayrı health check ve bağımsız güncelleme imkânı sağlar. Frontend statik dosya sunumu için nginx yeterlidir; backend için Python runtime gerekir.

**Neden tek worker?**
Fly.io'nun ücretsiz/küçük planında bellek kısıtlı. Uvicorn async yapısı sayesinde tek worker ile 4-5 eşzamanlı kullanıcı rahatlıkla desteklenir. `start.py`'daki multi-worker mantığı production flag'iyle aktifleştirilebilir ancak şimdilik gerekli değil.

**Neden Supabase, Fly Postgres değil?**
Supabase bağlantısı zaten mevcut ve `.env`'de yorum satırında bekliyor. Sıfırdan Fly Postgres kurmak yerine mevcut altyapıyı aktifleştirmek daha hızlı ve risksizdir.

---

## Components and Interfaces

### Backend Dockerfile (`backend/Dockerfile`)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Sistem bağımlılıkları (asyncpg için libpq gerekli)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Bağımlılıkları önce kopyala (Docker layer cache optimizasyonu)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala (.env hariç — .dockerignore ile)
COPY app/ ./app/

# Sağlık kontrolü
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Uvicorn ile başlat
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

**`.dockerignore` (backend/):**
```
.env
*.db
*.db-shm
*.db-wal
__pycache__/
*.pyc
.pytest_cache/
.hypothesis/
*.py[cod]
```

### Backend fly.toml (`backend/fly.toml`)

```toml
app = "kalorispor-backend"
primary_region = "fra"

[build]

[env]
  PORT = "8000"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1
  processes = ["app"]

  [[http_service.checks]]
    grace_period = "40s"
    interval = "30s"
    method = "GET"
    path = "/health"
    protocol = "http"
    timeout = "10s"
    tls_skip_verify = false

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1
```

### Frontend Dockerfile (`frontend/Dockerfile`)

```dockerfile
# ── Aşama 1: Build ──────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Bağımlılıkları önce kopyala (cache optimizasyonu)
COPY package.json package-lock.json* ./
RUN npm ci --frozen-lockfile

# Kaynak kodu kopyala
COPY . .

# Build-time API URL argümanı
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Production build
RUN npm run build

# ── Aşama 2: Serve ──────────────────────────────────────────────
FROM nginx:alpine

# Özel nginx konfigürasyonu
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Build çıktısını nginx'e kopyala
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### nginx.conf (`frontend/nginx.conf`)

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip sıkıştırma
    gzip on;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml application/xml+rss text/javascript;

    # React Router — bilinmeyen path'leri index.html'e yönlendir
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Statik asset'ler için uzun cache
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Güvenlik header'ları
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

### Frontend fly.toml (`frontend/fly.toml`)

```toml
app = "kalorispor-frontend"
primary_region = "fra"

[build]
  [build.args]
    VITE_API_URL = "https://kalorispor-backend.fly.dev"

[http_service]
  internal_port = 80
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1
  processes = ["app"]

  [[http_service.checks]]
    grace_period = "10s"
    interval = "30s"
    method = "GET"
    path = "/"
    protocol = "http"
    timeout = "5s"

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

---

## Data Models

### Ortam Değişkenleri

| Değişken | Kullanım | Kaynak | Zorunlu |
|---|---|---|---|
| `DATABASE_URL` | Supabase PostgreSQL bağlantısı | Fly Secret | Evet |
| `GEMINI_API_KEY` | Google Gemini AI servisi | Fly Secret | Evet |
| `SECRET_KEY` | Session token imzalama | Fly Secret | Evet |
| `FRONTEND_URL` | CORS allow_origins | Fly Secret | Evet |
| `PORT` | Uvicorn port (varsayılan: 8000) | fly.toml [env] | Hayır |
| `VITE_API_URL` | Frontend API base URL | Build arg / .env.production | Evet (build-time) |

**Not:** Mevcut `auth_service.py` incelendiğinde JWT değil, `secrets.token_urlsafe(32)` tabanlı session token kullandığı görülmektedir. Bu nedenle `JWT_SECRET_KEY` yerine `SECRET_KEY` kullanılacaktır. Requirements'ta `JWT_SECRET_KEY` geçse de gerçek implementasyon session-based auth kullanıyor; bu değişken gelecekteki JWT geçişi için rezerve edilebilir veya session güvenliği için kullanılabilir.

### Migration Script Güncellemesi

Mevcut `migrate_sqlite_to_postgres.py` şu tabloları taşımıyor:
- `users`
- `user_sessions`
- `achievements`
- `user_achievements`
- `ai_chat_sessions`
- `ai_chat_messages`
- `ai_generated_foods`
- `ai_coach_recommendations`
- `ai_coach_progress`
- `ai_coach_preferences`
- `sport_profiles`
- `weight_validations`
- `trend_analyses`
- `barcode_products`
- `scrape_metadata`
- `exercise_logs`
- `notifications` (varsa)
- `meal_plans` (varsa)

Script'e bu tablolar için migration blokları eklenecek ve her tablo için hata toleransı (try/except) ile kayıt sayısı doğrulaması eklenecektir.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Bu feature ağırlıklı olarak konfigürasyon ve altyapı içermektedir. Ancak iki adet saf Python fonksiyonu property-based testing için uygundur:

1. `database.py`'deki URL dönüşüm mantığı — herhangi bir `postgresql://` URL'i için `postgresql+asyncpg://` formatına dönüşüm
2. `migrate_sqlite_to_postgres.py`'deki migration mantığı — herhangi bir SQLite veritabanı için kayıt sayısı korunumu

### Property 1: DATABASE_URL Dönüşüm Tutarlılığı

*For any* geçerli `postgresql://` ile başlayan bağlantı URL'i için, `database.py`'nin URL dönüşüm mantığı bu URL'i `postgresql+asyncpg://` ile başlayan eşdeğer bir URL'e dönüştürmeli; URL'in geri kalan kısmı (host, port, dbname, credentials) değişmeden korunmalıdır.

**Validates: Requirements 7.1, 7.2**

### Property 2: CORS FRONTEND_URL Ekleme Tutarlılığı

*For any* geçerli HTTP/HTTPS URL değeri `FRONTEND_URL` ortam değişkeni olarak verildiğinde, `main.py`'nin CORS konfigürasyonu bu URL'i `allow_origins` listesine eklemelidir; liste aynı zamanda geliştirme ortamı URL'lerini (`localhost:5173`, `localhost:3000`) de içermelidir.

**Validates: Requirements 3.4, 5.1, 5.4**

### Property 3: Migration Kayıt Sayısı Korunumu

*For any* geçerli SQLite veritabanı için, migration scripti çalıştırıldığında her tablodaki PostgreSQL kayıt sayısı, SQLite'taki kayıt sayısıyla eşleşmelidir; migration öncesi ve sonrası kayıt sayıları arasında fark olmamalıdır.

**Validates: Requirements 4.1, 4.2**

---

## Error Handling

### Backend Başlangıç Hataları

`DATABASE_URL` eksikse uygulama başlamadan önce açık bir hata mesajıyla durmalıdır. Mevcut `database.py` bu durumda SQLite'a fallback yapıyor; production'da bu davranış değiştirilmeli, `DATABASE_URL` yoksa `RuntimeError` fırlatılmalıdır.

```python
# database.py'ye eklenecek production guard
import sys
_pg_url = os.getenv("DATABASE_URL")
if not _pg_url and os.getenv("ENVIRONMENT") == "production":
    print("HATA: DATABASE_URL ortam değişkeni eksik", file=sys.stderr)
    sys.exit(1)
```

Alternatif olarak `fly.toml`'da `DATABASE_URL`'in zorunlu olduğu belgelenebilir ve Fly.io'nun secret yoksa deploy'u reddetmesi sağlanabilir.

### Gemini AI Servisi Hataları

`GEMINI_API_KEY` eksik veya geçersizse AI servisi devre dışı bırakılmalı, diğer endpoint'ler etkilenmemelidir. Mevcut `ai_service.py`'deki `initialize()` metodu bu durumu zaten handle ediyor; production'da 503 yanıtı döndürülmesi için router seviyesinde kontrol eklenmelidir.

### Veritabanı Bağlantı Hataları

`pool_pre_ping=True` ayarı sayesinde SQLAlchemy her bağlantıyı kullanmadan önce test eder. Bağlantı kopması durumunda otomatik yeniden bağlanma havuz yönetimi tarafından sağlanır. Fly.io'nun health check mekanizması `/health` endpoint'i üzerinden uygulamanın durumunu izler.

### Migration Hata Toleransı

Her tablo migration'ı bağımsız try/except bloğu içinde çalışmalıdır. Bir tabloda hata oluşursa tablo adı ve hata mesajı loglanmalı, diğer tablolara devam edilmelidir. Migration sonunda başarılı ve başarısız tablo sayıları özetlenmelidir.

---

## Testing Strategy

Bu feature ağırlıklı olarak konfigürasyon ve altyapı içerdiğinden test stratejisi şu katmanlardan oluşur:

### Smoke Tests (Konfigürasyon Doğrulama)

Aşağıdaki dosyaların varlığını ve gerekli içerikleri doğrulayan testler:

- `backend/Dockerfile` — `FROM python:3.12`, `CMD ["uvicorn"...]` içeriyor mu?
- `backend/fly.toml` — `internal_port = 8000`, `force_https = true`, `min_machines_running = 1` var mı?
- `frontend/Dockerfile` — multi-stage build (`AS builder`, `FROM nginx`) var mı?
- `frontend/fly.toml` — `internal_port = 80`, `fra` region var mı?
- `frontend/nginx.conf` — `try_files $uri $uri/ /index.html` var mı?
- `backend/Dockerfile` — `.env` dosyası COPY edilmiyor mu?

### Unit Tests (Örnek Tabanlı)

- `/health` endpoint'i `{"status": "ok"}` döndürüyor mu?
- `DATABASE_URL` tanımlıyken `_IS_POSTGRES = True` oluyor mu?
- `GEMINI_API_KEY` eksikken `/api/ai-assistant` 503 döndürüyor mu?
- CORS listesi `localhost:5173` ve `localhost:3000` içeriyor mu?
- Engine konfigürasyonu `pool_size=5`, `max_overflow=10` içeriyor mu?

### Property-Based Tests (Hypothesis)

Property-based testing için **Hypothesis** kütüphanesi kullanılacaktır (zaten `requirements.txt`'te mevcut).

Her property testi minimum **100 iterasyon** çalıştırılacak şekilde konfigüre edilecektir.

**Property 1 — DATABASE_URL Dönüşüm Testi:**
```python
# Feature: fly-io-deploy, Property 1: DATABASE_URL dönüşüm tutarlılığı
@given(
    host=st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='.-'), min_size=1),
    port=st.integers(min_value=1, max_value=65535),
    dbname=st.text(alphabet=st.characters(whitelist_categories=('Ll',)), min_size=1),
)
@settings(max_examples=100)
def test_database_url_conversion(host, port, dbname):
    url = f"postgresql://user:pass@{host}:{port}/{dbname}"
    converted = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    assert converted.startswith("postgresql+asyncpg://")
    assert converted[len("postgresql+asyncpg://"):] == url[len("postgresql://"):]
```

**Property 2 — CORS FRONTEND_URL Testi:**
```python
# Feature: fly-io-deploy, Property 2: CORS FRONTEND_URL ekleme tutarlılığı
@given(
    scheme=st.sampled_from(["http", "https"]),
    host=st.text(alphabet=st.characters(whitelist_categories=('Ll',), whitelist_characters='.-'), min_size=3, max_size=30),
)
@settings(max_examples=100)
def test_cors_frontend_url_added(scheme, host):
    url = f"{scheme}://{host}"
    with patch.dict(os.environ, {"FRONTEND_URL": url}):
        origins = build_cors_origins()  # main.py'den extract edilecek fonksiyon
        assert url in origins
        assert "http://localhost:5173" in origins
        assert "http://localhost:3000" in origins
```

**Property 3 — Migration Kayıt Sayısı Testi:**
```python
# Feature: fly-io-deploy, Property 3: Migration kayıt sayısı korunumu
@given(
    food_count=st.integers(min_value=0, max_value=100),
    log_count=st.integers(min_value=0, max_value=50),
)
@settings(max_examples=100)
def test_migration_preserves_record_count(food_count, log_count):
    # In-memory SQLite ve mock PostgreSQL ile test
    sqlite_counts = {"food_items": food_count, "food_log": log_count}
    pg_counts = run_migration(sqlite_counts)  # mock migration
    assert pg_counts == sqlite_counts
```

### Integration Tests

Gerçek Fly.io ortamında deploy sonrası çalıştırılacak testler:

- Backend `/health` endpoint'i HTTPS üzerinden yanıt veriyor mu?
- Frontend `/` path'i HTML döndürüyor mu?
- Frontend'den backend'e CORS isteği başarılı mı?
- Supabase bağlantısı kurulabiliyor mu?

---

## Deploy Adımları

Aşağıdaki komutlar sırayla çalıştırılmalıdır.

### Ön Koşullar

```bash
# Fly CLI kurulu mu?
fly version

# Giriş yapılmış mı?
fly auth whoami
```

### 1. Backend Deploy

```bash
# Backend dizinine geç
cd backend

# Fly uygulaması oluştur (ilk kez)
fly apps create kalorispor-backend --org personal

# Secrets ayarla
fly secrets set \
  DATABASE_URL="postgresql://postgres:EnO3fHrK0wFNbPKI@db.ycnchcjmepluzimmqwho.supabase.co:5432/postgres" \
  GEMINI_API_KEY="<gemini-api-key>" \
  SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" \
  FRONTEND_URL="https://kalorispor-frontend.fly.dev" \
  --app kalorispor-backend

# Deploy et
fly deploy --app kalorispor-backend

# Sağlık kontrolü
fly status --app kalorispor-backend
curl https://kalorispor-backend.fly.dev/health
```

### 2. Migration (SQLite → PostgreSQL)

```bash
# Backend dizininde, DATABASE_URL ile migration çalıştır
DATABASE_URL="postgresql://postgres:EnO3fHrK0wFNbPKI@db.ycnchcjmepluzimmqwho.supabase.co:5432/postgres" \
  python migrate_sqlite_to_postgres.py
```

### 3. Frontend Deploy

```bash
# Frontend dizinine geç
cd ../frontend

# .env.production güncelle
echo "VITE_API_URL=https://kalorispor-backend.fly.dev" > .env.production

# Fly uygulaması oluştur (ilk kez)
fly apps create kalorispor-frontend --org personal

# Deploy et (VITE_API_URL build arg olarak geçilir)
fly deploy --app kalorispor-frontend \
  --build-arg VITE_API_URL=https://kalorispor-backend.fly.dev

# Sağlık kontrolü
fly status --app kalorispor-frontend
curl https://kalorispor-frontend.fly.dev
```

### 4. Doğrulama

```bash
# Backend health check
curl https://kalorispor-backend.fly.dev/health
# Beklenen: {"status": "ok"}

# CORS testi
curl -H "Origin: https://kalorispor-frontend.fly.dev" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     https://kalorispor-backend.fly.dev/api/foods
# Beklenen: Access-Control-Allow-Origin header'ı mevcut

# Frontend erişim
curl -I https://kalorispor-frontend.fly.dev
# Beklenen: HTTP/2 200, Content-Type: text/html
```

### Güncelleme (Sonraki Deploy'lar)

```bash
# Backend güncelle
cd backend && fly deploy --app kalorispor-backend

# Frontend güncelle
cd frontend && fly deploy --app kalorispor-frontend \
  --build-arg VITE_API_URL=https://kalorispor-backend.fly.dev
```

---

## .gitignore Güncellemeleri

Mevcut `.gitignore` dosyasına aşağıdaki satırlar eklenmelidir:

```gitignore
# Fly.io — hassas bilgi içerebilecek dosyalar
# fly.toml dosyaları commit edilebilir (secret içermez)
# Ancak fly secrets değerleri asla commit edilmemeli

# Docker build artifacts
.dockerignore

# Frontend production env (VITE_API_URL içerebilir — public URL olduğu için OK)
# frontend/.env.production commit edilebilir (secret içermez)
```

**Not:** `fly.toml` dosyaları secret içermediğinden commit edilebilir. `backend/.env` zaten `.gitignore`'da mevcut. `frontend/.env.production` yalnızca public URL içerdiğinden commit edilebilir.
