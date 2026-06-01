# Implementation Plan: KaloriSpor Fly.io Deploy

## Overview

Bu plan, KaloriSpor uygulamasını Fly.io'ya deploy etmek için gereken tüm kod değişikliklerini kapsar. Backend ve frontend için Dockerfile/fly.toml dosyaları oluşturulacak, mevcut Python dosyaları production-ready hale getirilecek, migration scripti eksik tablolarla tamamlanacak ve property-based testler yazılacaktır.

## Tasks

- [x] 1. Backend Dockerfile ve .dockerignore oluşturma
  - `backend/Dockerfile` dosyasını oluştur: `python:3.12-slim` base image, `libpq-dev` + `gcc` sistem bağımlılıkları, `requirements.txt` layer cache optimizasyonu, `app/` dizini kopyalama, HEALTHCHECK ve `uvicorn app.main:app --host 0.0.0.0 --port 8000` CMD
  - `backend/.dockerignore` dosyasını oluştur: `.env`, `*.db`, `*.db-shm`, `*.db-wal`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.hypothesis/` hariç tut
  - Dockerfile'ın `.env` dosyasını COPY etmediğini doğrula
  - _Requirements: 1.1, 1.2, 3.2_

- [x] 2. Backend fly.toml oluşturma
  - `backend/fly.toml` dosyasını oluştur: `app = "kalorispor-backend"`, `primary_region = "fra"`, `internal_port = 8000`, `force_https = true`, `min_machines_running = 1`, `auto_stop_machines = true`, `auto_start_machines = true`
  - `[http_service.checks]` bölümünü ekle: `/health` endpoint, 30s interval, 10s timeout, 40s grace_period
  - `[[vm]]` bölümünü ekle: `memory = "512mb"`, `cpu_kind = "shared"`, `cpus = 1`
  - `[env]` bölümünde `PORT = "8000"` tanımla
  - _Requirements: 1.2, 1.4, 6.1, 6.3_

- [x] 3. Frontend Dockerfile oluşturma
  - `frontend/Dockerfile` dosyasını oluştur: çok aşamalı (multi-stage) build
    - Aşama 1 (`builder`): `node:20-alpine`, `npm ci --frozen-lockfile`, `ARG VITE_API_URL`, `ENV VITE_API_URL=$VITE_API_URL`, `npm run build`
    - Aşama 2: `nginx:alpine`, `nginx.conf` kopyalama, `dist/` → `/usr/share/nginx/html`, `EXPOSE 80`
  - _Requirements: 2.1, 2.5_

- [x] 4. Frontend nginx.conf oluşturma
  - `frontend/nginx.conf` dosyasını oluştur: `listen 80`, `root /usr/share/nginx/html`, `index index.html`
  - React Router desteği için `location /` bloğuna `try_files $uri $uri/ /index.html` ekle
  - Statik asset'ler için `location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$` bloğuna `expires 1y` ve `Cache-Control: public, immutable` ekle
  - Güvenlik header'larını ekle: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, `Referrer-Policy`
  - Gzip sıkıştırmayı etkinleştir: `gzip on`, `gzip_types` ile JS/CSS/JSON/XML türleri
  - _Requirements: 2.3, 2.4_

- [x] 5. Frontend fly.toml oluşturma
  - `frontend/fly.toml` dosyasını oluştur: `app = "kalorispor-frontend"`, `primary_region = "fra"`, `internal_port = 80`, `force_https = true`, `min_machines_running = 1`
  - `[build.args]` bölümünde `VITE_API_URL = "https://kalorispor-backend.fly.dev"` tanımla
  - `[http_service.checks]` bölümünü ekle: `/` path, 30s interval, 5s timeout, 10s grace_period
  - `[[vm]]` bölümünü ekle: `memory = "256mb"`, `cpu_kind = "shared"`, `cpus = 1`
  - _Requirements: 2.2, 2.5_

- [x] 6. database.py'ye production guard ekleme
  - `backend/app/database.py` dosyasını düzenle: `_pg_url` yoksa ve `ENVIRONMENT == "production"` ise `sys.stderr`'e hata mesajı yaz ve `sys.exit(1)` çağır
  - `import sys` ekle (dosyanın başına)
  - Guard'ı `_pg_url = os.getenv("DATABASE_URL")` satırından hemen sonra yerleştir
  - Hata mesajı: `"HATA: DATABASE_URL ortam değişkeni eksik. Fly.io secrets kontrol edin."`
  - _Requirements: 1.5, 3.1_

  - [ ]* 6.1 Property testi yaz: DATABASE_URL dönüşüm tutarlılığı
    - `backend/tests/test_deploy_properties.py` dosyasını oluştur
    - **Property 1: DATABASE_URL Dönüşüm Tutarlılığı**
    - Hypothesis `@given` ile rastgele `host`, `port`, `dbname` üret; `postgresql://` URL'ini `postgresql+asyncpg://`'ya dönüştür; prefix değişti, geri kalan kısım aynı kaldı doğrula
    - `@settings(max_examples=100)` kullan
    - **Validates: Requirements 7.1, 7.2**

- [x] 7. main.py'de CORS'u production-ready hale getirme
  - `backend/app/main.py` dosyasını düzenle: CORS origins listesini oluşturan mantığı `build_cors_origins()` adlı ayrı bir fonksiyona çıkar
  - Fonksiyon her zaman `http://localhost:5173`, `http://localhost:5174`, `http://localhost:3000` içermeli
  - `FRONTEND_URL` env var tanımlıysa listeye eklemeli
  - `CORSMiddleware`'i bu fonksiyonun döndürdüğü listeyle yapılandır
  - _Requirements: 3.4, 5.1, 5.4_

  - [ ]* 7.1 Property testi yaz: CORS FRONTEND_URL ekleme tutarlılığı
    - `backend/tests/test_deploy_properties.py` dosyasına ekle
    - **Property 2: CORS FRONTEND_URL Ekleme Tutarlılığı**
    - Hypothesis `@given` ile rastgele `scheme` (`http`/`https`) ve `host` üret; `patch.dict(os.environ, {"FRONTEND_URL": url})` ile env'i mock'la; `build_cors_origins()` çağır; URL listede var, `localhost:5173` ve `localhost:3000` de listede doğrula
    - `@settings(max_examples=100)` kullan
    - **Validates: Requirements 3.4, 5.1, 5.4**

- [x] 8. Checkpoint — Temel dosyalar hazır
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. migrate_sqlite_to_postgres.py'ye eksik tabloları ekleme
  - `backend/migrate_sqlite_to_postgres.py` dosyasını düzenle: her migration bloğunu `try/except` ile sar, hata durumunda tablo adı ve mesajı logla, diğer tablolara devam et
  - Aşağıdaki eksik tabloları ekle (her biri için SQLite'tan okuma, PostgreSQL'e yazma, sequence güncelleme):
    - `users` — `id, username, email, hashed_password, is_active, is_admin, created_at, updated_at` alanları
    - `user_sessions` — `id, user_id, token, created_at, expires_at, is_active` alanları
    - `achievements` — `id, name, description, icon, category, points, condition_type, condition_value, created_at` alanları
    - `user_achievements` — `id, user_id, achievement_id, earned_at, progress` alanları
    - `ai_chat_sessions` — `id, user_id, title, created_at, last_activity, message_count` alanları
    - `ai_chat_messages` — `id, session_id, role, content, created_at, tokens_used` alanları
    - `ai_generated_foods` — `id, user_id, name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, description, created_at` alanları
    - `ai_coach_recommendations` — `id, user_id, recommendation_type, content, priority, created_at, is_read` alanları
    - `ai_coach_progress` — `id, user_id, metric_type, value, recorded_at` alanları
    - `ai_coach_preferences` — `id, user_id, preference_key, preference_value, updated_at` alanları
    - `sport_profiles` — `id, user_id, sport_type, fitness_level, weekly_sessions, created_at, updated_at` alanları
    - `weight_validations` — `id, user_id, weight_kg, validated_at, validation_method, notes` alanları
    - `trend_analyses` — `id, user_id, analysis_type, data_json, analyzed_at` alanları
    - `barcode_products` — `id, barcode, name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, created_at` alanları
    - `scrape_metadata` — `id, url, scraped_at, status, item_count` alanları
    - `exercise_logs` — `id, workout_log_id, exercise_name, sets_completed, reps_completed, weight_kg, logged_at` alanları
  - Migration sonunda başarılı ve başarısız tablo sayılarını özetle
  - _Requirements: 4.1, 4.2, 4.4, 4.5_

  - [ ]* 9.1 Property testi yaz: migration kayıt sayısı korunumu
    - `backend/tests/test_deploy_properties.py` dosyasına ekle
    - **Property 3: Migration Kayıt Sayısı Korunumu**
    - Hypothesis `@given` ile rastgele `food_count` (0-100) ve `log_count` (0-50) üret; in-memory SQLite oluştur, kayıtları ekle, mock migration çalıştır, PostgreSQL'deki sayıların SQLite'takiyle eşleştiğini doğrula
    - `@settings(max_examples=100)` kullan
    - **Validates: Requirements 4.1, 4.2**

- [x] 10. .gitignore güncelleme
  - Kök `.gitignore` dosyasına Fly.io ile ilgili notları ekle:
    - `# Fly.io` başlığı altında `fly.toml` dosyalarının commit edilebilir olduğunu belirt (secret içermez)
    - `backend/.dockerignore` ve `frontend/.dockerignore` satırlarını ekle (build artifact)
    - `.fly/` dizinini ekle (Fly CLI geçici dosyaları)
  - _Requirements: 3.1, 3.2_

- [x] 11. frontend/.env.production güncelleme
  - `frontend/.env.production` dosyasını güncelle: `VITE_API_URL=https://kalorispor-backend.fly.dev` değerini yaz
  - `VITE_API_URL_NATIVE` satırını koru (mobil geliştirme için)
  - Açıklayıcı yorum satırları ekle: Fly.io deploy URL'i, build-time değişken olduğunu belirt
  - _Requirements: 2.5, 5.3_

- [x] 12. Checkpoint — Tüm dosyalar hazır
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Deploy dokümantasyonu (DEPLOY.md) oluşturma
  - Kök dizinde `DEPLOY.md` dosyasını oluştur; aşağıdaki bölümleri içermeli:
    - **Ön Koşullar**: `fly version` ve `fly auth whoami` komutları
    - **Backend Deploy**: `fly apps create`, `fly secrets set` (DATABASE_URL, GEMINI_API_KEY, SECRET_KEY, FRONTEND_URL), `fly deploy`, `fly status` komutları
    - **Migration**: `DATABASE_URL` ile `python migrate_sqlite_to_postgres.py` çalıştırma adımları
    - **Frontend Deploy**: `fly apps create`, `fly deploy --build-arg VITE_API_URL=...` komutları
    - **Doğrulama**: `/health` endpoint curl testi, CORS testi, frontend erişim testi
    - **Güncelleme**: Sonraki deploy'lar için kısa komutlar
    - **Sorun Giderme**: Yaygın hatalar ve çözümleri (DATABASE_URL eksik, CORS hatası, health check başarısız)
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 4.1_

- [x] 14. Son Checkpoint — Deploy hazırlığı tamamlandı
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- `*` ile işaretli görevler isteğe bağlıdır; MVP için atlanabilir
- Her görev belirli requirements'lara referans verir (izlenebilirlik için)
- Property testleri Hypothesis kütüphanesiyle yazılır (`requirements.txt`'te zaten mevcut)
- `build_cors_origins()` fonksiyonu (Görev 7) hem production hem de property testi için gereklidir
- `backend/tests/` dizini yoksa oluşturulmalı, `__init__.py` eklenmelidir
- Migration scripti çalıştırılmadan önce `DATABASE_URL` env var'ının tanımlı olduğundan emin olun
