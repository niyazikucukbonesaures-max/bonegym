# Uygulama Planı: Fitness ve Kalori Takip Uygulaması

## Genel Bakış

Bu plan, Python + FastAPI backend ve React + TypeScript + Tailwind CSS + shadcn/ui + Framer Motion frontend kullanarak fitness ve kalori takip uygulamasını adım adım inşa eder. Her görev bir öncekinin üzerine inşa edilir; son adımda tüm bileşenler birbirine bağlanır.

## Görevler

- [x] 1. Proje yapısını ve temel altyapıyı kur
  - Backend için `backend/` dizini oluştur: `app/`, `tests/`, `alembic/` klasörleri
  - Frontend için `frontend/` dizini oluştur: Vite + React + TypeScript şablonu
  - `backend/requirements.txt` dosyasını oluştur: fastapi, uvicorn, sqlalchemy, aiosqlite, beautifulsoup4, httpx, apscheduler, hypothesis, pytest, pytest-asyncio
  - `frontend/package.json` bağımlılıklarını ekle: tailwindcss, shadcn/ui, framer-motion, recharts, @tanstack/react-query, axios, react-router-dom
  - Tailwind CSS dark mode (`class` stratejisi) ve `tailwind.config.ts` dosyasını yapılandır
  - shadcn/ui başlangıç kurulumunu yap (`components.json`)
  - _Gereksinimler: 1.1, 2.1, 3.1_

- [x] 2. SQLite veritabanı şemasını ve ORM modellerini oluştur
  - [x] 2.1 SQLAlchemy modellerini tanımla
    - `backend/app/models.py` dosyasında tüm tabloları oluştur: `food_items`, `food_log`, `workout_programs`, `exercises`, `workout_logs`, `exercise_logs`, `creatine_doses`, `measurements`, `user_profile`, `scrape_metadata`
    - FTS5 sanal tablosu `food_search` için ham SQL migration ekle
    - SQLite WAL modunu etkinleştir
    - _Gereksinimler: 1.3, 2.5, 4.4, 5.6, 6.3_
  - [x] 2.2 Veritabanı bağlantısı ve başlangıç kurulumunu yaz
    - `backend/app/database.py` dosyasında async SQLite bağlantısı ve `init_db()` fonksiyonu
    - Uygulama başlangıcında şema doğrulama (smoke test)
    - _Gereksinimler: 1.3_

- [x] 3. Web Scraper bileşenini uygula
  - [x] 3.1 `ScraperService` sınıfını yaz
    - `backend/app/scraper.py` dosyasında `scrape_all()`, `scrape_page(url)`, `parse_food_item(html)`, `save_to_db(items)`, `get_last_scrape_info()` metodlarını uygula
    - BeautifulSoup ile `https://www.diyetkolik.com/kac-kalori/kategori/et-tavuk-balik` sayfasını ayrıştır
    - Sayfalama varsa tüm sayfaları dolaş
    - HTTP 4xx/5xx hatalarını yakala, logla ve yerel DB'yi koru
    - _Gereksinimler: 1.1, 1.2, 1.3, 1.4, 1.5, 1.7_
  - [ ]* 3.2 Özellik 1 için property testi yaz
    - **Özellik 1: Besin Verisi Serileştirme Round-Trip**
    - `FoodItem` nesnesini JSON'a serileştirip deserileştirmenin eşdeğer nesne ürettiğini doğrula
    - `st.builds(FoodItem, ...)` stratejisi kullan
    - **Doğrular: Gereksinim 1.8, 1.3**
  - [ ]* 3.3 Scraper birim testlerini yaz
    - HTTP hata durumları, boş yanıt, HTML yapısı değişimi senaryolarını test et
    - _Gereksinimler: 1.4, 1.7_

- [x] 4. APScheduler ile otomatik scraping zamanlayıcısını kur
  - `backend/app/scheduler.py` dosyasında 24 saatlik interval ile `ScraperService.scrape_all()` çağrısını zamanla
  - FastAPI lifespan event'ine scheduler başlatma/durdurma ekle
  - Scheduler konfigürasyonunu doğrulayan smoke testi yaz
  - _Gereksinimler: 1.6_

- [x] 5. Kalori Hesaplama Motorunu uygula
  - [x] 5.1 `CalorieEngine` sınıfını yaz
    - `backend/app/calorie_engine.py` dosyasında Mifflin-St Jeor BMR formülünü uygula (erkek/kadın)
    - `calculate_bmr()`, `calculate_tdee()`, `calculate_macros()`, `get_daily_total()`, `add_food_log()`, `delete_food_log()` metodlarını uygula
    - Hedef bazlı kalori önerisi: lose → TDEE - 500, maintain → TDEE, gain → TDEE + 300
    - Makro hedef dağılımı: protein %30, karbonhidrat %40, yağ %30
    - Sıfır/negatif gram için `ValueError` fırlat
    - _Gereksinimler: 2.2, 2.3, 2.4, 3.1, 3.2, 3.3_
  - [ ]* 5.2 Özellik 2 için property testi yaz
    - **Özellik 2: Gram Bazlı Makro Hesaplama Orantısallığı**
    - `calories = calories_per_100g * grams / 100` formülünü tüm geçerli giriş uzayında doğrula
    - `st.floats(min_value=1, max_value=5000)` stratejisi kullan
    - **Doğrular: Gereksinim 2.2**
  - [ ]* 5.3 Özellik 3 için property testi yaz
    - **Özellik 3: Kalori Günlüğü Toplam Invariantı**
    - Günlük toplam = tüm girişlerin toplamı; silme sonrası toplam doğru azalıyor mu?
    - `st.lists(st.builds(FoodLogEntry, ...))` stratejisi kullan
    - **Doğrular: Gereksinim 2.3, 2.4**
  - [ ]* 5.4 Özellik 4 için property testi yaz
    - **Özellik 4: BMR Pozitiflik ve Cinsiyet Farkı Invariantı**
    - BMR > 0, erkek BMR - kadın BMR = 166, TDEE > BMR koşullarını doğrula
    - `st.builds(UserProfile, ...)` stratejisi kullan
    - **Doğrular: Gereksinim 3.1**
  - [ ]* 5.5 Özellik 5 için property testi yaz
    - **Özellik 5: Hedef Bazlı Kalori Önerisi Yönü**
    - lose → öneri < TDEE, gain → öneri > TDEE, maintain → öneri = TDEE
    - `st.sampled_from(["lose", "maintain", "gain"])` stratejisi kullan
    - **Doğrular: Gereksinim 3.2**
  - [ ]* 5.6 Özellik 6 için property testi yaz
    - **Özellik 6: Makro Kalori Toplamı Tutarlılığı**
    - `protein_g * 4 + carbs_g * 4 + fat_g * 9` ≈ günlük kalori hedefi (±5 tolerans)
    - `st.floats(min_value=1200, max_value=5000)` stratejisi kullan
    - **Doğrular: Gereksinim 3.3, 3.6**
  - [ ]* 5.7 CalorieEngine birim testlerini yaz
    - Somut BMR/TDEE örnekleri, sıfır gram hatası, eksik profil senaryoları
    - _Gereksinimler: 3.1, 3.2, 3.3_

- [x] 6. Checkpoint — Tüm testlerin geçtiğinden emin ol
  - Tüm testlerin geçtiğinden emin ol, sorular varsa kullanıcıya sor.

- [x] 7. Spor Takipçi bileşenini uygula
  - [x] 7.1 `WorkoutTracker` sınıfını yaz
    - `backend/app/workout_tracker.py` dosyasında `create_program()`, `list_programs()`, `log_workout()`, `get_history(weeks=12)`, `get_exercise_progress()`, `get_weekly_stats()` metodlarını uygula
    - 3 gün antrenman yapılmadığında bildirim üret
    - _Gereksinimler: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  - [ ]* 7.2 WorkoutTracker birim testlerini yaz
    - Program CRUD, antrenman kaydı, haftalık istatistik, bildirim tetikleme
    - _Gereksinimler: 4.1, 4.3, 4.7_

- [x] 8. Kreatin Takipçi bileşenini uygula
  - [x] 8.1 `CreatineTracker` sınıfını yaz
    - `backend/app/creatine_tracker.py` dosyasında `log_dose()`, `get_current_phase()`, `get_history(days=30)`, `check_phase_transition()`, `get_today_status()` metodlarını uygula
    - Yükleme fazı 7 gün sonra idame fazına geçiş bildirimi üret
    - Günlük alım yapılmadıysa hatırlatma bildirimi üret
    - _Gereksinimler: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_
  - [ ]* 8.2 CreatineTracker birim testlerini yaz
    - Faz geçiş mantığı, bildirim tetikleme, doz kayıt
    - _Gereksinimler: 5.2, 5.5, 5.7_

- [x] 9. Ölçüm Kayıt bileşenini uygula
  - [x] 9.1 `MeasurementTracker` sınıfını yaz
    - `backend/app/measurement_tracker.py` dosyasında `add_measurement()`, `get_history()`, `get_trend(days=30)`, `get_delta()` metodlarını uygula
    - 7 gün kilo kaydı yapılmadığında hatırlatma bildirimi üret
    - _Gereksinimler: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
  - [ ]* 9.2 MeasurementTracker birim testlerini yaz
    - Ölçüm CRUD, delta hesaplama, bildirim tetikleme
    - _Gereksinimler: 6.5, 6.7_

- [x] 10. Dışa Aktarma Servisi ve CSV round-trip özelliğini uygula
  - [x] 10.1 `ExportService` sınıfını yaz
    - `backend/app/export_service.py` dosyasında kalori günlüğü, ölçüm geçmişi ve antrenman geçmişi için CSV dışa aktarma uygula
    - Tarih aralığı filtresi ekle
    - Başarısız dışa aktarmada geçici dosyayı sil, hata mesajı döndür
    - _Gereksinimler: 8.1, 8.2, 8.4_
  - [ ]* 10.2 Özellik 8 için property testi yaz
    - **Özellik 8: CSV Dışa Aktarma Round-Trip**
    - Veriyi CSV'ye aktarıp geri okumak orijinal koleksiyonla eşdeğer olmalı
    - `st.lists(st.builds(...), min_size=1)` stratejisi kullan
    - **Doğrular: Gereksinim 8.3**
  - [ ]* 10.3 ExportService birim testlerini yaz
    - Başarısız dışa aktarma, boş veri seti, tarih aralığı filtreleme
    - _Gereksinimler: 8.1, 8.2, 8.4_

- [x] 11. Pano Servisi ve REST API katmanını uygula
  - [x] 11.1 `DashboardService` sınıfını yaz
    - `backend/app/dashboard_service.py` dosyasında `get_dashboard_data()` metodunu uygula
    - Tek API çağrısıyla tüm pano verilerini (`DashboardSnapshot`) döndür
    - _Gereksinimler: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_
  - [x] 11.2 FastAPI router'larını yaz
    - `backend/app/routers/` altında `foods.py`, `log.py`, `profile.py`, `workouts.py`, `creatine.py`, `measurements.py`, `dashboard.py`, `export.py` dosyalarını oluştur
    - Tasarım dokümanındaki tüm REST uç noktalarını uygula
    - FTS5 ile besin araması için `/api/foods/search` uç noktasını uygula (300ms eşiği)
    - _Gereksinimler: 2.1, 7.6_
  - [x] 11.3 Tarih bazlı filtreleme için Özellik 7'yi uygula
    - `/api/log/{date}` uç noktasında tarih filtrelemesini doğrula
    - _Gereksinimler: 2.6_
  - [ ]* 11.4 Özellik 7 için property testi yaz
    - **Özellik 7: Tarih Bazlı Günlük Filtreleme Doğruluğu**
    - Döndürülen tüm girişlerin `logged_at` tarihi sorgu tarihiyle eşleşmeli; hiçbir giriş atlanmamalı
    - `st.dates()`, `st.lists(...)` stratejisi kullan
    - **Doğrular: Gereksinim 2.6**
  - [ ]* 11.5 Pano API entegrasyon testini yaz
    - Gerçek SQLite DB ile pano yanıt süresi testi (1 saniye eşiği)
    - FTS5 arama performans testi (300ms eşiği)
    - _Gereksinimler: 2.1, 7.6_

- [x] 12. Checkpoint — Backend testlerinin tamamı geçiyor mu kontrol et
  - Tüm testlerin geçtiğinden emin ol, sorular varsa kullanıcıya sor.

- [x] 13. Frontend temel yapısını ve tema sistemini kur
  - [x] 13.1 React Router ve sayfa iskeletini oluştur
    - `frontend/src/pages/` altında `Dashboard.tsx`, `FoodLog.tsx`, `Workouts.tsx`, `Creatine.tsx`, `Measurements.tsx`, `Profile.tsx`, `Export.tsx` sayfalarını oluştur
    - React Router v6 ile route yapısını kur
    - _Gereksinimler: 7.1_
  - [x] 13.2 Dark mode tema sistemini uygula
    - `ThemeProvider` bileşenini yaz; `localStorage`'a tema tercihini kaydet
    - Tailwind `dark:` sınıflarını etkinleştir
    - Tema geçiş butonu bileşenini oluştur
    - _Gereksinimler: 7.1_
  - [x] 13.3 Temel layout ve navigasyon bileşenlerini oluştur
    - `Sidebar.tsx` ve `TopBar.tsx` bileşenlerini yaz
    - Glassmorphism efekti için `backdrop-blur`, `bg-white/10`, `border-white/20` Tailwind sınıflarını kullan
    - Framer Motion ile sidebar açılma/kapanma animasyonu ekle
    - Mobil uyumlu responsive layout (hamburger menü)
    - _Gereksinimler: 7.1_

- [x] 14. shadcn/ui temel bileşenlerini ve glassmorphism kart sistemini oluştur
  - `frontend/src/components/ui/` altında `GlassCard.tsx` bileşenini yaz
    - `backdrop-blur-md bg-white/10 dark:bg-white/5 border border-white/20 rounded-2xl shadow-xl` stilini uygula
    - Framer Motion ile `whileHover` scale animasyonu ekle
  - `StatCard.tsx` bileşenini yaz: gradient ikon, büyük sayı, alt etiket
  - `ProgressRing.tsx` bileşenini yaz: SVG tabanlı dairesel ilerleme göstergesi
  - Gradient arka plan sistemi: `from-violet-600 via-purple-600 to-indigo-600` gibi Tailwind gradient sınıfları
  - _Gereksinimler: 7.1, 3.4, 3.6_

- [x] 15. React Query ile API istemcisini ve veri katmanını kur
  - `frontend/src/lib/api.ts` dosyasında axios instance ve tüm API çağrı fonksiyonlarını yaz
  - `frontend/src/hooks/` altında `useDashboard.ts`, `useFoodLog.ts`, `useWorkouts.ts`, `useCreatine.ts`, `useMeasurements.ts` custom hook'larını oluştur
  - React Query `QueryClient` konfigürasyonunu `main.tsx`'e ekle
  - _Gereksinimler: 7.6_

- [x] 16. Ana Pano sayfasını uygula
  - [x] 16.1 Pano bileşenlerini yaz
    - `Dashboard.tsx` sayfasında `useDashboard` hook'u ile veri çek
    - Günlük kalori özeti için `StatCard` bileşenlerini kullan (tüketilen, kalan, hedef)
    - Makro dağılımı için `ProgressRing` bileşenlerini kullan (protein, karbonhidrat, yağ)
    - Kreatin durumu için `GlassCard` içinde alındı/alınmadı badge'i göster
    - Haftalık antrenman hedefi için ilerleme çubuğu ekle
    - Framer Motion ile `staggerChildren` animasyonu ile kartları sırayla göster
    - _Gereksinimler: 7.1, 7.3, 7.4, 7.8_
  - [x] 16.2 Pano grafik bileşenlerini yaz
    - Son 7 günlük kilo değişimi için Recharts `AreaChart` (gradient fill, smooth curves)
    - Son 4 haftaya ait haftalık kalori ortalaması için Recharts `BarChart` (gradient fill)
    - Son 30 günlük vücut ölçümü trendi için Recharts `LineChart` (kilo + bel çevresi)
    - Tüm grafikler dark mode uyumlu renk paleti kullanmalı
    - _Gereksinimler: 7.2, 7.5, 7.7_
  - [ ]* 16.3 Pano bileşeni snapshot testlerini yaz
    - React Testing Library + Vitest ile pano render testi
    - API mock ile veri yükleme testi
    - _Gereksinimler: 7.1_

- [x] 17. Besin Arama ve Kalori Günlüğü sayfasını uygula
  - [x] 17.1 Besin arama bileşenini yaz
    - `FoodSearch.tsx` bileşeninde debounce ile `/api/foods/search` çağrısı yap
    - Arama sonuçlarını `GlassCard` içinde listele
    - Framer Motion ile sonuç listesi animasyonu ekle
    - _Gereksinimler: 2.1_
  - [x] 17.2 Kalori günlüğü formunu yaz
    - `FoodLogForm.tsx` bileşeninde besin seçimi, gram girişi ve öğün tipi seçimi
    - shadcn/ui `Select`, `Input`, `Button` bileşenlerini kullan
    - Gerçek zamanlı kalori/makro önizlemesi göster
    - _Gereksinimler: 2.2, 2.3_
  - [x] 17.3 Günlük kalori özeti ve geçmiş bileşenini yaz
    - `FoodLog.tsx` sayfasında tarih seçici ile geçmiş günlere erişim
    - Günlük toplam kalori ve makro özeti
    - Giriş silme işlevi (onay dialogu ile)
    - Kalori hedefi aşıldığında görsel uyarı (kırmızı gradient badge)
    - _Gereksinimler: 2.4, 2.5, 2.6, 3.4, 3.5, 3.6_
  - [ ]* 17.4 Form doğrulama birim testlerini yaz
    - Sıfır gram, negatif değer, boş besin seçimi hata durumları
    - _Gereksinimler: 2.2_

- [x] 18. Spor Programı ve Antrenman Takibi sayfasını uygula
  - [x] 18.1 Antrenman programı CRUD bileşenlerini yaz
    - `WorkoutProgramForm.tsx` bileşeninde egzersiz ekleme/silme/sıralama (drag-and-drop opsiyonel)
    - shadcn/ui `Dialog`, `Form`, `Table` bileşenlerini kullan
    - _Gereksinimler: 4.1, 4.2_
  - [x] 18.2 Antrenman kaydı ve geçmiş bileşenini yaz
    - `WorkoutLog.tsx` bileşeninde program seçimi, süre girişi, set/tekrar/ağırlık kaydı
    - Son 12 haftaya ait antrenman geçmişini tablo halinde göster
    - Haftalık sıklık ve toplam süre istatistikleri
    - _Gereksinimler: 4.3, 4.4, 4.5_
  - [x] 18.3 Egzersiz ilerleme grafiğini yaz
    - Seçilen egzersiz için Recharts `LineChart` ile ağırlık/tekrar ilerlemesi
    - Gradient fill ve smooth curves kullan
    - _Gereksinimler: 4.6_
  - [ ]* 18.4 Antrenman bileşeni render testlerini yaz
    - Program formu doğrulama, antrenman kaydı mock testi
    - _Gereksinimler: 4.1, 4.3_

- [x] 19. Kreatin Takibi sayfasını uygula
  - `Creatine.tsx` sayfasında bugünkü doz kayıt formu (shadcn/ui `Input`, `Button`)
  - Mevcut faz, geçen gün sayısı ve toplam alınan kreatin miktarını `StatCard` ile göster
  - Son 30 günlük alım geçmişini Recharts `BarChart` ile göster
  - Faz geçiş bildirimi için `toast` (shadcn/ui `Sonner`) bileşenini kullan
  - Framer Motion ile faz badge animasyonu ekle
  - _Gereksinimler: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 20. Kilo ve Vücut Ölçümleri sayfasını uygula
  - [x] 20.1 Ölçüm kayıt formunu yaz
    - `MeasurementForm.tsx` bileşeninde kilo, bel, kalça, göğüs, kol, bacak alanları
    - shadcn/ui `Form`, `Input` bileşenlerini kullan
    - _Gereksinimler: 6.1, 6.2_
  - [x] 20.2 Ölçüm geçmişi ve trend grafiklerini yaz
    - Kilo değişimi için Recharts `AreaChart` (gradient fill)
    - Her vücut ölçümü için ayrı `LineChart` bileşeni
    - İlk kayıt ile son kayıt arasındaki delta değerlerini `StatCard` ile göster
    - _Gereksinimler: 6.3, 6.4, 6.5, 6.6_

- [x] 21. Kullanıcı Profili sayfasını uygula
  - `Profile.tsx` sayfasında boy, kilo, yaş, cinsiyet, aktivite seviyesi, hedef ve haftalık antrenman hedefi formu
  - shadcn/ui `Select`, `RadioGroup`, `Slider` bileşenlerini kullan
  - Hesaplanan BMR, TDEE ve önerilen kalori hedefini `StatCard` ile göster
  - Profil kaydedildiğinde `toast` bildirimi göster
  - _Gereksinimler: 3.1, 3.2, 3.3_

- [x] 22. Veri Dışa Aktarma sayfasını uygula
  - `Export.tsx` sayfasında dışa aktarma tipi seçimi (kalori, ölçüm, antrenman) ve tarih aralığı seçici
  - shadcn/ui `DatePicker`, `Select`, `Button` bileşenlerini kullan
  - Başarılı dışa aktarmada dosya indirme tetikle
  - Hata durumunda `toast` ile açıklayıcı hata mesajı göster
  - _Gereksinimler: 8.1, 8.2, 8.4_

- [x] 23. Bildirim sistemi ve hatırlatmaları uygula
  - `frontend/src/components/NotificationBanner.tsx` bileşenini yaz
  - Pano yüklendiğinde backend'den bildirim listesini çek
  - Framer Motion ile bildirim banner'ı animasyonu ekle (slide-down)
  - 3 gün antrenman yok, 7 gün kilo kaydı yok, kreatin hatırlatması bildirimlerini göster
  - _Gereksinimler: 4.7, 5.7, 6.7_

- [x] 24. Checkpoint — Frontend bileşenlerinin tamamı çalışıyor mu kontrol et
  - Tüm testlerin geçtiğinden emin ol, sorular varsa kullanıcıya sor.

- [x] 25. Backend ve Frontend'i birbirine bağla (entegrasyon)
  - FastAPI CORS middleware'ini `frontend` origin için yapılandır
  - Frontend `api.ts` dosyasındaki base URL'i backend adresine yönlendir
  - `vite.config.ts` dosyasına `/api` proxy kuralı ekle (geliştirme ortamı için)
  - Tüm sayfaların gerçek API verileriyle çalıştığını doğrula
  - _Gereksinimler: 7.6_

- [x] 26. Son Checkpoint — Tüm testler geçiyor, uygulama entegre çalışıyor
  - Tüm backend ve frontend testlerinin geçtiğinden emin ol.
  - Pano 1 saniye içinde yükleniyor mu kontrol et.
  - Besin araması 300ms altında yanıt veriyor mu kontrol et.
  - Sorular varsa kullanıcıya sor.

## Notlar

- `*` ile işaretli görevler isteğe bağlıdır; daha hızlı MVP için atlanabilir
- Her görev, izlenebilirlik için ilgili gereksinimlere referans verir
- Property testleri evrensel doğruluk özelliklerini, birim testleri somut örnekleri doğrular
- Hypothesis kütüphanesi CI profilinde minimum 100 iterasyon ile çalışır
- Modern UI: Glassmorphism kartlar, gradient renkler, Framer Motion animasyonları, dark mode desteği
- Tüm Recharts grafikleri gradient fill ve smooth curves kullanır
- shadcn/ui bileşenleri Tailwind ile özelleştirilir
