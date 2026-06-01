# KaloriSpor — Render.com Deploy Rehberi

Ücretsiz deploy. Backend uyku moduna girebilir (15 dk kullanılmazsa), ilk istek ~30 sn gecikir.

## Mimari

```
kalorispor-frontend (Render Static Site)
         ↓ VITE_API_URL
kalorispor-backend (Render Web Service)
         ↓ DATABASE_URL
   Supabase PostgreSQL
```

---

## Adım 1: GitHub'a Yükle

Render GitHub reposundan deploy eder. Önce projeyi GitHub'a yükleyin:

```bash
# Proje kök dizininde (kalorispor/)
git init
git add .
git commit -m "Initial commit"

# GitHub'da yeni repo oluşturun: https://github.com/new
# Sonra:
git remote add origin https://github.com/KULLANICI_ADI/kalorispor.git
git push -u origin main
```

---

## Adım 2: Backend Deploy (Render Web Service)

1. https://render.com adresine gidin, GitHub ile giriş yapın
2. **New → Web Service** tıklayın
3. GitHub reponuzu seçin
4. Ayarlar:
   - **Name**: `kalorispor-backend`
   - **Region**: Frankfurt (EU)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

5. **Environment Variables** bölümüne ekleyin:

   | Key | Value |
   |-----|-------|
   | `ENVIRONMENT` | `production` |
   | `DATABASE_URL` | `postgresql://postgres:EnO3fHrK0wFNbPKI@db.ycnchcjmepluzimmqwho.supabase.co:5432/postgres` |
   | `GEMINI_API_KEY` | `AIzaSyCWqb8ifXudUOqPd14gWYWnBYCZASRsVCg` |
   | `SECRET_KEY` | (Generate butonuna tıklayın — otomatik üretir) |
   | `FRONTEND_URL` | (Şimdilik boş bırakın, frontend deploy sonrası ekleyin) |

6. **Create Web Service** tıklayın

7. Deploy tamamlanınca URL'i not alın: `https://kalorispor-backend.onrender.com`

8. Sağlık kontrolü:
   ```
   https://kalorispor-backend.onrender.com/health
   ```
   Beklenen: `{"status":"ok"}`

---

## Adım 3: Veri Migration (SQLite → PostgreSQL)

> Sadece bir kez çalıştırılır. Yerel verileri Supabase'e taşır.

PowerShell'de backend klasöründe:

```powershell
$env:DATABASE_URL="postgresql://postgres:EnO3fHrK0wFNbPKI@db.ycnchcjmepluzimmqwho.supabase.co:5432/postgres"
python migrate_sqlite_to_postgres.py
```

---

## Adım 4: Frontend Deploy (Render Static Site)

1. Render'da **New → Static Site** tıklayın
2. Aynı GitHub reposunu seçin
3. Ayarlar:
   - **Name**: `kalorispor-frontend`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

4. **Environment Variables** ekleyin:

   | Key | Value |
   |-----|-------|
   | `VITE_API_URL` | `https://kalorispor-backend.onrender.com` |

5. **Create Static Site** tıklayın

6. Deploy tamamlanınca URL'i not alın: `https://kalorispor-frontend.onrender.com`

---

## Adım 5: FRONTEND_URL'i Backend'e Ekle

1. Render dashboard → `kalorispor-backend` → **Environment**
2. `FRONTEND_URL` değerini ekleyin: `https://kalorispor-frontend.onrender.com`
3. **Save Changes** → backend otomatik yeniden başlar

---

## Adım 6: Doğrulama

```
# Backend sağlık kontrolü
https://kalorispor-backend.onrender.com/health

# Uygulamayı aç
https://kalorispor-frontend.onrender.com
```

---

## Güncelleme (Sonraki Deploy'lar)

GitHub'a push yapınca Render otomatik deploy eder:

```bash
git add .
git commit -m "Güncelleme açıklaması"
git push
```

---

## Sorun Giderme

### ❌ "Application failed to respond" (ilk açılışta)
Ücretsiz tier uyku modunda. 30-60 saniye bekleyin, sayfa yenilenince açılır.

### ❌ CORS Hatası
`FRONTEND_URL` environment variable'ının doğru ayarlandığını kontrol edin.

### ❌ "DATABASE_URL ortam değişkeni eksik"
Render dashboard'dan `DATABASE_URL` değerini kontrol edin.

### ❌ Build Hatası
Render loglarına bakın: Dashboard → Service → **Logs** sekmesi.

---

## Kullanıcı Erişimi

Arkadaşlarınıza şu URL'i paylaşın:
```
https://kalorispor-frontend.onrender.com
```

Her kullanıcı kendi hesabını oluşturabilir.

---

## Maliyet

| Servis | Plan | Maliyet |
|--------|------|---------|
| Backend (Web Service) | Free | $0/ay |
| Frontend (Static Site) | Free | $0/ay |
| Supabase PostgreSQL | Free tier | $0/ay |
| **Toplam** | | **$0/ay** |
