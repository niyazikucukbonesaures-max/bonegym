# 🔐 Admin Hesap Bilgileri

## Giriş Bilgileri

Kullanıcı tablolarını sıfırladık ve yeni bir admin hesabı oluşturduk:

### Admin Hesabı
- **📧 Email:** `admin@fitness.com`
- **👤 Kullanıcı Adı:** `admin`
- **🔑 Şifre:** `admin123`
- **🆔 User ID:** `1`

## Nasıl Giriş Yapılır?

1. **Frontend'i Aç:** http://localhost:5173
2. **Login Sayfasına Git:** Sol menüden "Giriş Yap" butonuna tıkla
3. **Giriş Bilgilerini Gir:**
   - Email: `admin@fitness.com`
   - Şifre: `admin123`
4. **Giriş Yap** butonuna tıkla

## Yeni Kullanıcı Kaydı

Artık yeni kullanıcılar kayıt olabilir:

1. Login sayfasında **"Kayıt Ol"** linkine tıkla
2. Formu doldur:
   - Email
   - Kullanıcı Adı
   - Tam Ad
   - Şifre
3. **Kayıt Ol** butonuna tıkla
4. Otomatik olarak giriş yapılacak

## Veritabanını Tekrar Sıfırlamak İsterseniz

Eğer tekrar sıfırlamak isterseniz:

```bash
cd backend
python reset_auth_and_create_admin.py
```

Bu komut:
- ✅ Tüm kullanıcıları siler
- ✅ Tüm oturumları siler
- ✅ Yeni admin hesabı oluşturur

## Güvenlik Notları

⚠️ **ÖNEMLİ:** Üretim ortamında (production) admin şifresini mutlaka değiştirin!

- Admin şifresi şu an basit: `admin123`
- Gerçek kullanımda güçlü bir şifre kullanın
- Şifre değiştirme özelliği henüz eklenmedi (gelecek güncellemede eklenecek)

## Sorun Giderme

### Kayıt Olurken Hata Alıyorsanız

1. **Backend çalışıyor mu?** → http://localhost:8000/docs kontrol edin
2. **Email zaten kullanılıyor mu?** → Farklı bir email deneyin
3. **Kullanıcı adı zaten kullanılıyor mu?** → Farklı bir kullanıcı adı deneyin

### Giriş Yapamıyorsanız

1. **Email doğru mu?** → `admin@fitness.com` olmalı
2. **Şifre doğru mu?** → `admin123` olmalı
3. **Backend çalışıyor mu?** → Terminal'de kontrol edin

## Sistem Durumu

✅ **Backend:** http://localhost:8000 (Çalışıyor)
✅ **Frontend:** http://localhost:5173 (Çalışıyor)
✅ **API Docs:** http://localhost:8000/docs
✅ **Database:** `backend/fitness.db` (SQLite)

---

**Son Güncelleme:** 28 Nisan 2026
**Durum:** Kullanıma Hazır ✨
