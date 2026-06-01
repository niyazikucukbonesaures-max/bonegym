# 🏋️ Fitness Kalori Takip Uygulaması - Kullanım Kılavuzu

## 🚀 Hızlı Başlangıç

### **Yöntem 1: VBS Dosyası (Önerilen - En Kolay)**

1. **`Fitness-App-Baslat.vbs`** dosyasına çift tıklayın
2. Bilgilendirme mesajlarını okuyun ve "Tamam" deyin
3. Tarayıcınız otomatik açılacak
4. Uygulamayı kullanmaya başlayın!

**Kapatmak için:**
- **`Fitness-App-Durdur.vbs`** dosyasına çift tıklayın

---

### **Yöntem 2: BAT Dosyası**

1. **`start-app.bat`** dosyasına çift tıklayın
2. Terminal pencereleri açılacak
3. Tarayıcınız otomatik açılacak

**Kapatmak için:**
- **`stop-app.bat`** dosyasına çift tıklayın

---

### **Yöntem 3: Manuel (Gelişmiş Kullanıcılar)**

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Tarayıcıda Aç:**
```
http://localhost:5173
```

---

## 🌐 Erişim Adresleri

| Servis | URL | Açıklama |
|--------|-----|----------|
| **Frontend** | http://localhost:5173 | Ana uygulama arayüzü |
| **Backend API** | http://localhost:8000 | REST API sunucusu |
| **API Docs** | http://localhost:8000/docs | Swagger API dokümantasyonu |
| **ReDoc** | http://localhost:8000/redoc | Alternatif API dokümantasyonu |

---

## ✨ Animasyonları Görmek İçin

### **1. Hover Efektleri**
- 🖱️ **Kartların üzerine mouse getir** → Scale ve glow efekti
- 🖱️ **Butonların üzerine mouse getir** → Shadow ve scale efekti
- 🖱️ **Input'ların üzerine mouse getir** → Border ve background değişimi

### **2. Progress Ring Animasyonları**
- 📊 **Makro Besinler** bölümündeki yuvarlak progress bar'lar
- Sayfa yüklendiğinde animasyonlu dolacak
- 🖱️ Üzerine mouse getir → Scale efekti

### **3. Gradient Animasyonları**
- 🎨 **StatCard'lardaki renkli ikonlar** → 3 saniyede döngü
- 🔥 Kalori kartları, BMI kartları → Gradient animasyon

### **4. Number Animasyonları**
- 🔢 Sayfa yüklendiğinde sayılar **0'dan hedef değere** animasyonlu artacak
- 🔄 Sayfa yenilendiğinde tekrar göreceksiniz

### **5. Progress Bar Animasyonları**
- 📈 **"Bu Hafta"** bölümündeki antrenman progress bar'ı
- Gradient animasyonlu ve shadow'lu

### **6. Skeleton Loader**
- 🔄 Sayfayı yenile (F5) → Shimmer animasyonlu skeleton loader

### **7. Button Animasyonları**
- 🖱️ Butona tıkla → Active scale efekti (basılı görünüm)
- 🖱️ "Hızlı Güncelle" butonuna tıkla → Form açılacak

### **8. Alert Kartları**
- 💡 **Akıllı Uyarılar** bölümündeki renkli noktalar → Pulse animasyonu

---

## 🎬 Animasyonları Daha İyi Görmek İçin

1. **Chrome DevTools** aç (F12)
2. **Performance** sekmesine git
3. **Animations** panelini aç
4. Sayfayı yenile ve tüm animasyonları göreceksin

---

## 🔧 Gereksinimler

### **Yazılım Gereksinimleri:**
- ✅ **Python 3.8+** - [İndir](https://www.python.org/)
- ✅ **Node.js 16+** - [İndir](https://nodejs.org/)
- ✅ **npm** (Node.js ile birlikte gelir)

### **İlk Kurulum (Sadece Bir Kez):**

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

---

## 🐛 Sorun Giderme

### **Animasyonlar Görünmüyor**
1. **Tarayıcı cache'ini temizle** (Ctrl + Shift + Delete)
2. **Hard refresh** yap (Ctrl + Shift + R)
3. **Konsolu kontrol et** (F12) - hata var mı bak

### **Uygulama Açılmıyor**
1. **Python ve Node.js yüklü mü kontrol et:**
   ```bash
   python --version
   node --version
   ```
2. **Port'lar kullanımda mı kontrol et:**
   ```bash
   netstat -ano | findstr ":8000"
   netstat -ano | findstr ":5173"
   ```
3. **Eski process'leri kapat:**
   - `Fitness-App-Durdur.vbs` çalıştır
   - Veya `stop-app.bat` çalıştır

### **Backend Hatası**
```bash
cd backend
python -m uvicorn app.main:app --reload
```
Hata mesajını oku ve eksik paketleri yükle:
```bash
pip install -r requirements.txt
```

### **Frontend Hatası**
```bash
cd frontend
npm install
npm run dev
```

### **Port Zaten Kullanımda**
```bash
# Windows'ta port'u kullanan process'i bul ve kapat
netstat -ano | findstr ":8000"
taskkill /PID <PID_NUMARASI> /F
```

---

## 📊 Özellikler

### **Dashboard**
- ✅ Günlük kalori takibi
- ✅ Makro besin dağılımı (Protein, Karbonhidrat, Yağ)
- ✅ BMI hesaplama ve sağlık analizi
- ✅ Kilo trendi grafikleri
- ✅ Akıllı uyarılar sistemi
- ✅ Vücut rekomposizyonu desteği

### **Yemek Günlüğü**
- ✅ Yemek arama (200+ Türk yemeği)
- ✅ Porsiyon hesaplama
- ✅ Günlük kalori takibi
- ✅ Makro besin detayları

### **Antrenman Takibi**
- ✅ Antrenman programları
- ✅ Egzersiz kayıtları
- ✅ Haftalık hedef takibi
- ✅ İlerleme grafikleri

### **Kreatin Takibi**
- ✅ Günlük kreatin kaydı
- ✅ Yükleme/İdame fazları
- ✅ Toplam tüketim takibi

### **Ölçümler**
- ✅ Kilo takibi
- ✅ Boy kaydı
- ✅ BMI hesaplama
- ✅ Geçmiş ölçümler

### **Yemek Planlayıcı**
- ✅ Haftalık yemek planı
- ✅ Otomatik kalori hesaplama
- ✅ Makro besin dengesi

### **Veri Dışa Aktarma**
- ✅ Excel export
- ✅ CSV export
- ✅ Tüm verilerinizi yedekleyin

---

## 🎨 UI/UX Özellikleri

- ✨ **Glassmorphism** tasarım
- 🌙 **Dark mode** (varsayılan)
- 🎭 **Framer Motion** animasyonları
- 📱 **Responsive** tasarım (mobil uyumlu)
- 🚀 **Smooth** transitions ve hover efektleri
- 💫 **Gradient** animasyonları
- 🎯 **Modern** ve minimalist arayüz

---

## 📝 Notlar

- ⚠️ **İlk kullanımda** profil oluşturmanız gerekir
- 💾 **Veriler** SQLite veritabanında saklanır (`backend/fitness.db`)
- 🔄 **Otomatik yedekleme** önerilir
- 🌐 **İnternet bağlantısı** gerekmez (local çalışır)

---

## 🆘 Destek

Sorun yaşarsanız:
1. **Konsolu kontrol edin** (F12)
2. **Log dosyalarını inceleyin**
3. **GitHub Issues** açın
4. **README.md** dosyasını okuyun

---

## 📜 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

---

## 🎉 İyi Kullanımlar!

Fitness hedeflerinize ulaşmanız dileğiyle! 💪🏋️‍♂️

---

**Son Güncelleme:** 2026-04-28
**Versiyon:** 2.0.0 (Optimize Edilmiş)
