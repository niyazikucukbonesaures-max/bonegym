# 🏋️ Fitness ve Kalori Takip Uygulaması

Modern, kullanıcı dostu fitness ve kalori takip uygulaması. Glassmorphism tasarım, dark mode ve akıllı BMI analizi ile.

## ✨ Özellikler

- 🍽️ **Kalori Takibi**: Günlük kalori ve makro besin takibi
- 💪 **Spor Programları**: Antrenman programları oluşturma ve takip
- 💊 **Kreatin Takibi**: Yükleme ve idame fazı yönetimi
- 📊 **Ölçüm Takibi**: Kilo ve vücut ölçümleri
- 🎯 **BMI Analizi**: 7 kategori BMI sınıflandırması ve sağlık önerileri
- 🔔 **Akıllı Uyarılar**: Kişiselleştirilmiş beslenme ve egzersiz önerileri
- 🌙 **Dark Mode**: Göz dostu karanlık tema
- 📱 **Responsive**: Mobil ve masaüstü uyumlu

## 🚀 Hızlı Başlangıç

### Tek Tıkla Başlatma

1. **Uygulamayı Başlat**: `start-app.bat` dosyasına çift tıklayın
   - Backend ve Frontend otomatik olarak başlar
   - Tarayıcınız otomatik açılır
   - Uygulama http://localhost:5173 adresinde çalışır

2. **Uygulamayı Durdur**: `stop-app.bat` dosyasına çift tıklayın
   - Tüm sunucular güvenli şekilde kapatılır

### Manuel Başlatma

**Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## 📦 Teknolojiler

### Backend
- Python 3.14
- FastAPI
- SQLite + SQLAlchemy
- BeautifulSoup4 (Web Scraping)
- APScheduler

### Frontend
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui
- Framer Motion
- Recharts
- React Query

## 🎨 Özellikler Detay

### BMI Analizi
- 7 kategori sınıflandırma (Ciddi Zayıflık → Morbid Obez)
- Sağlık riski değerlendirmesi
- İdeal kilo hesaplama
- Hedef kilo önerileri
- Kişiselleştirilmiş sağlık tavsiyeleri

### Akıllı Uyarı Sistemi
- Kalori takibi uyarıları
- Protein alımı izleme
- BMI tabanlı öneriler
- Hedef bazlı tavsiyeler

### Performans Optimizasyonları
- React.memo ile memoized bileşenler
- useMemo ile optimize edilmiş hesaplamalar
- React Query ile verimli veri yönetimi
- Lazy loading ve code splitting

## 📱 Kullanım

1. **Profil Oluştur**: Boy, kilo, yaş ve hedeflerinizi girin
2. **Kalori Takibi**: Yediğiniz besinleri arayın ve ekleyin
3. **Spor Programı**: Antrenman programınızı oluşturun
4. **Ölçüm Kaydet**: Düzenli kilo ve vücut ölçümlerinizi kaydedin
5. **İlerleme Takibi**: Pano'dan genel ilerlemenizi görün

## 🔧 Geliştirme

### Gereksinimler
- Python 3.10+
- Node.js 18+
- npm veya yarn

### Kurulum

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

## 📄 Lisans

Bu proje özel kullanım içindir.

## 🤝 Katkıda Bulunma

Bu proje aktif geliştirme aşamasındadır.

## 📞 İletişim

Sorularınız için lütfen iletişime geçin.

---

**Not**: İlk çalıştırmada besin veritabanı otomatik olarak diyetkolik.com'dan çekilecektir.
