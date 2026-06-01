# Requirements Document

## Introduction

KaloriSpor, mevcut durumda yalnızca yerel ortamda çalışan bir fitness ve kalori takip uygulamasıdır. Bu özellik, uygulamayı Fly.io platformuna deploy ederek 4-5 kullanıcının internet üzerinden erişebileceği, verilerinin kalıcı olarak saklandığı bir üretim ortamına taşımayı kapsar.

Kapsam şunları içerir:
- Backend (FastAPI + Uvicorn) için Fly.io deploy yapılandırması
- Frontend (React + Vite) için Fly.io deploy yapılandırması
- SQLite'tan Supabase PostgreSQL'e geçiş ve mevcut verilerin taşınması
- Ortam değişkenlerinin (Gemini API anahtarı, JWT secret, DB bağlantısı) güvenli yönetimi
- CORS ve API URL yapılandırmasının production ortamına uyarlanması
- Mevcut SQLite verisinin PostgreSQL'e tek seferlik migration'ı

## Glossary

- **KaloriSpor**: Fitness ve kalori takip uygulamasının adı.
- **Backend**: FastAPI tabanlı Python API sunucusu; `backend/` dizininde yer alır.
- **Frontend**: React + Vite + TypeScript tabanlı web arayüzü; `frontend/` dizininde yer alır.
- **Fly.io**: Uygulamanın deploy edileceği bulut platformu.
- **Fly_App**: Fly.io üzerinde çalışan bir uygulama birimi (backend veya frontend için ayrı ayrı).
- **Supabase_DB**: Mevcut Supabase PostgreSQL veritabanı; `backend/.env` dosyasında yorum satırında tanımlı bağlantı bilgisiyle erişilir.
- **Migration_Script**: `backend/migrate_sqlite_to_postgres.py` — SQLite'tan PostgreSQL'e veri taşıyan Python scripti.
- **Fly_Secret**: Fly.io'nun `fly secrets set` komutuyla yönetilen şifreli ortam değişkeni.
- **Dockerfile**: Fly.io'nun uygulamayı container olarak çalıştırması için gereken yapılandırma dosyası.
- **fly.toml**: Fly.io'nun uygulama yapılandırma dosyası; port, region, health check gibi ayarları içerir.
- **CORS**: Cross-Origin Resource Sharing — frontend'in backend API'sine erişmesine izin veren HTTP mekanizması.
- **JWT_Secret**: JSON Web Token imzalama anahtarı; auth sistemi tarafından kullanılır.
- **Health_Check**: Fly.io'nun uygulamanın ayakta olup olmadığını doğrulamak için periyodik olarak çağırdığı endpoint.

---

## Requirements

### Requirement 1: Backend Dockerfile ve Fly.io Yapılandırması

**User Story:** Bir geliştirici olarak, backend'i Fly.io'da container olarak çalıştırabilmek istiyorum; böylece uygulama internet üzerinden erişilebilir hale gelsin.

#### Acceptance Criteria

1. THE Backend SHALL `backend/Dockerfile` dosyasına sahip olmalı; bu dosya Python 3.12 slim imajını temel almalı, `requirements.txt` bağımlılıklarını kurmalı ve `uvicorn app.main:app --host 0.0.0.0 --port 8000` komutunu başlatma komutu olarak tanımlamalıdır.
2. THE Backend SHALL `backend/fly.toml` dosyasına sahip olmalı; bu dosya 8000 numaralı iç portu, `https` protokolünü ve `fra` (Frankfurt) region'ını tanımlamalıdır.
3. WHEN Fly.io uygulamayı başlattığında, THE Backend SHALL `/health` endpoint'ine yapılan GET isteğine `{"status": "ok"}` yanıtını 5 saniye içinde döndürmelidir.
4. THE Backend SHALL `fly.toml` içinde `[http_service]` bölümünde `force_https = true` ayarını içermelidir; böylece tüm HTTP trafiği HTTPS'e yönlendirilir.
5. IF `DATABASE_URL` ortam değişkeni tanımlı değilse, THEN THE Backend SHALL başlangıçta hata fırlatarak durmalı ve log'a `"DATABASE_URL ortam değişkeni eksik"` mesajını yazmalıdır.

---

### Requirement 2: Frontend Dockerfile ve Fly.io Yapılandırması

**User Story:** Bir geliştirici olarak, frontend'i Fly.io'da statik dosya sunucusu olarak çalıştırabilmek istiyorum; böylece kullanıcılar tarayıcıdan uygulamaya erişebilsin.

#### Acceptance Criteria

1. THE Frontend SHALL `frontend/Dockerfile` dosyasına sahip olmalı; bu dosya çok aşamalı (multi-stage) build kullanmalı: ilk aşamada Node.js ile `vite build` çalıştırılmalı, ikinci aşamada `nginx:alpine` imajı ile `dist/` klasörü sunulmalıdır.
2. THE Frontend SHALL `frontend/fly.toml` dosyasına sahip olmalı; bu dosya 80 numaralı iç portu ve `fra` region'ını tanımlamalıdır.
3. WHEN Fly.io frontend uygulamasını başlattığında, THE Frontend SHALL `/` path'ine yapılan GET isteğine `index.html` içeriğini döndürmelidir.
4. THE Frontend SHALL `frontend/nginx.conf` dosyasına sahip olmalı; bu dosya React Router'ın client-side routing'ini desteklemek için bilinmeyen path'leri `index.html`'e yönlendirmelidir (`try_files $uri $uri/ /index.html`).
5. WHEN `vite build` çalıştırıldığında, THE Frontend SHALL `VITE_API_URL` ortam değişkenini backend'in Fly.io URL'i olarak kullanmalıdır; bu değişken build zamanında `frontend/.env.production` dosyasına veya Fly.io build arg olarak sağlanmalıdır.

---

### Requirement 3: Ortam Değişkenlerinin Güvenli Yönetimi

**User Story:** Bir geliştirici olarak, API anahtarları ve veritabanı şifrelerinin kaynak kodda görünmemesini istiyorum; böylece güvenlik açığı oluşmasın.

#### Acceptance Criteria

1. THE Backend SHALL `DATABASE_URL`, `GEMINI_API_KEY` ve `JWT_SECRET_KEY` değerlerini yalnızca Fly_Secret mekanizmasıyla almalıdır; bu değerler `Dockerfile` veya `fly.toml` içinde düz metin olarak yer almamalıdır.
2. THE Backend SHALL `backend/.env` dosyasını production container imajına kopyalamamalıdır; `Dockerfile` içinde `.env` dosyası `COPY` komutuna dahil edilmemelidir.
3. WHEN `fly secrets set` komutu çalıştırıldığında, THE Fly_App SHALL ilgili ortam değişkenini şifreli olarak saklamalı ve uygulama yeniden başlatıldığında bu değeri otomatik olarak enjekte etmelidir.
4. THE Backend SHALL `FRONTEND_URL` ortam değişkenini Fly_Secret olarak almalı ve bu değeri CORS `allow_origins` listesine eklemelidir; böylece yalnızca tanımlı frontend URL'inden gelen istekler kabul edilir.
5. IF `JWT_SECRET_KEY` ortam değişkeni tanımlı değilse, THEN THE Backend SHALL başlangıçta hata fırlatarak durmalı ve log'a `"JWT_SECRET_KEY ortam değişkeni eksik"` mesajını yazmalıdır.

---

### Requirement 4: SQLite'tan PostgreSQL'e Veri Geçişi

**User Story:** Bir kullanıcı olarak, yerel ortamda biriktirdiğim fitness ve kalori verilerimin production ortamında da erişilebilir olmasını istiyorum; böylece geçmiş verilerimi kaybetmeyeyim.

#### Acceptance Criteria

1. WHEN `python migrate_sqlite_to_postgres.py` komutu `DATABASE_URL` ortam değişkeni tanımlıyken çalıştırıldığında, THE Migration_Script SHALL `backend/fitness.db` içindeki tüm tabloları Supabase_DB'ye aktarmalı ve her tablo için aktarılan kayıt sayısını log'a yazmalıdır.
2. WHEN migration tamamlandığında, THE Migration_Script SHALL PostgreSQL'deki kayıt sayısının SQLite'takiyle eşleştiğini doğrulamalı; eşleşmiyorsa log'a uyarı yazmalıdır.
3. THE Backend SHALL `DATABASE_URL` ortam değişkeni tanımlıyken başlatıldığında SQLite'ı hiç kullanmamalı; tüm okuma ve yazma işlemleri Supabase_DB üzerinden gerçekleşmelidir.
4. IF migration sırasında bir tabloda hata oluşursa, THEN THE Migration_Script SHALL o tablonun adını ve hata mesajını log'a yazmalı ve diğer tabloların migration'ına devam etmelidir.
5. THE Migration_Script SHALL `users` ve `user_sessions` tablolarını da taşımalıdır; böylece mevcut kullanıcı hesapları ve oturumları production ortamında geçerli olmaya devam etmelidir.

---

### Requirement 5: CORS ve API URL Yapılandırması

**User Story:** Bir kullanıcı olarak, tarayıcıdan frontend'e eriştiğimde API isteklerinin başarıyla tamamlanmasını istiyorum; böylece uygulama düzgün çalışsın.

#### Acceptance Criteria

1. WHEN frontend, backend API'sine istek gönderdiğinde, THE Backend SHALL `FRONTEND_URL` ortam değişkeninde tanımlı origin'den gelen istekleri CORS politikası kapsamında kabul etmelidir.
2. THE Backend SHALL production ortamında `http://localhost:5173` ve `http://localhost:3000` origin'lerini CORS listesinden çıkarmamalıdır; bu değerler yalnızca geliştirme ortamında geçerlidir.
3. WHEN `VITE_API_URL` ortam değişkeni tanımlıyken frontend build edildiğinde, THE Frontend SHALL tüm API isteklerini bu URL'e yönlendirmelidir; Vite proxy kullanılmamalıdır.
4. THE Backend SHALL production ortamında `allow_credentials=True` ile birlikte yalnızca `FRONTEND_URL` değerini `allow_origins` listesinde bulundurmalıdır.

---

### Requirement 6: Fly.io Health Check ve Yeniden Başlatma Politikası

**User Story:** Bir geliştirici olarak, uygulamanın çökmesi durumunda Fly.io'nun otomatik olarak yeniden başlatmasını istiyorum; böylece kullanıcılar kesinti yaşamasın.

#### Acceptance Criteria

1. THE Backend `fly.toml` SHALL `[http_service.checks]` bölümünde `/health` endpoint'ini 30 saniyede bir kontrol eden bir health check tanımlamalıdır.
2. WHEN health check art arda 3 kez başarısız olduğunda, THE Fly_App SHALL uygulamayı otomatik olarak yeniden başlatmalıdır.
3. THE Backend `fly.toml` SHALL `min_machines_running = 1` ayarını içermelidir; böylece uygulama her zaman en az bir instance üzerinde çalışır.
4. WHEN Backend yeniden başlatıldığında, THE Backend SHALL veritabanı bağlantısını yeniden kurmalı ve `/health` endpoint'ini 30 saniye içinde yanıt verir hale getirmelidir.

---

### Requirement 7: Mevcut Supabase PostgreSQL Bağlantısının Aktifleştirilmesi

**User Story:** Bir geliştirici olarak, `backend/.env` dosyasında yorum satırında bekleyen Supabase bağlantısını production için aktif etmek istiyorum; böylece veritabanı altyapısını sıfırdan kurmak zorunda kalmayayım.

#### Acceptance Criteria

1. THE Backend SHALL `DATABASE_URL` değeri olarak `postgresql://postgres:<password>@db.ycnchcjmepluzimmqwho.supabase.co:5432/postgres` formatındaki Supabase bağlantı URL'ini kabul etmelidir.
2. WHEN `DATABASE_URL` `postgresql://` ile başlıyorsa, THE Backend `database.py` SHALL bu URL'i otomatik olarak `postgresql+asyncpg://` formatına dönüştürmelidir.
3. THE Backend SHALL Supabase_DB'ye bağlanırken `pool_size=5`, `max_overflow=10`, `pool_timeout=30` ve `pool_pre_ping=True` bağlantı havuzu ayarlarını kullanmalıdır.
4. WHEN Supabase_DB bağlantısı kurulamadığında, THE Backend SHALL log'a bağlantı hatasını yazmalı ve 30 saniye içinde yeniden bağlanmayı denemeli; 3 başarısız denemeden sonra başlangıcı iptal etmelidir.

---

### Requirement 8: Gemini AI Servisinin Production Ortamında Çalışması

**User Story:** Bir kullanıcı olarak, production ortamında da AI destekli besin analizi ve koç özelliklerini kullanabilmek istiyorum; böylece uygulamanın tüm özellikleri erişilebilir olsun.

#### Acceptance Criteria

1. THE Backend SHALL `GEMINI_API_KEY` değerini Fly_Secret'tan alarak Gemini AI servisini başlatmalıdır.
2. WHEN `GEMINI_API_KEY` geçersiz veya eksikse, THE Backend SHALL AI servisini devre dışı bırakmalı ve `/api/ai-assistant` endpoint'lerine yapılan isteklere `503 Service Unavailable` yanıtı döndürmelidir; diğer endpoint'ler etkilenmemelidir.
3. THE Backend SHALL Gemini API'ye yapılan isteklerde 30 saniyelik zaman aşımı uygulamalıdır.
