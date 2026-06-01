# Gereksinimler Dokümanı

## Giriş

Bu doküman, kullanıcıların günlük kalori alımını takip etmesini, düzenli spor programlarını yönetmesini, kreatin kullanımını izlemesini ve kilo/vücut ölçümlerini kaydetmesini sağlayan bir fitness ve kalori takip uygulamasının gereksinimlerini tanımlamaktadır. Uygulama, diyetkolik.com'dan besin kalori verilerini çekerek kapsamlı bir besin veritabanı oluşturur ve kullanıcıya güncel bir spor/kilo-kas kazanım panosu sunar.

## Sözlük

- **Sistem**: Fitness ve kalori takip uygulamasının tamamı
- **Kullanıcı**: Uygulamayı kullanan kişi
- **Besin_Veritabanı**: diyetkolik.com'dan çekilen ve yerel olarak saklanan besin kalori bilgilerini içeren veri deposu
- **Web_Scraper**: diyetkolik.com'dan besin verilerini çeken bileşen
- **Kalori_Hesaplayici**: Günlük kalori alımını ve harcamasını hesaplayan bileşen
- **Spor_Takipci**: Egzersiz programlarını ve antrenman geçmişini yöneten bileşen
- **Kreatin_Takipci**: Kreatin takviyesi alım zamanlamasını ve dozajını izleyen bileşen
- **Olcum_Kayit**: Kilo ve vücut ölçümlerini saklayan ve izleyen bileşen
- **Pano**: Kullanıcının güncel spor, kilo ve kas kazanım verilerini görselleştiren ana ekran
- **Gunluk_Hedef**: Kullanıcının belirlediği günlük kalori ve makro besin hedefleri
- **Antrenman_Programi**: Belirli egzersizleri, set/tekrar sayılarını ve zamanlamayı içeren spor planı
- **Makro_Besin**: Protein, karbonhidrat ve yağ değerleri
- **BMR**: Bazal Metabolizma Hızı — dinlenme halinde harcanan kalori miktarı
- **TDEE**: Toplam Günlük Enerji Harcaması — aktivite seviyesi dahil günlük kalori ihtiyacı

---

## Gereksinimler

### Gereksinim 1: Besin Verisi Çekme (Web Scraping)

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, diyetkolik.com'daki et, tavuk ve balık kategorisindeki besinlerin kalori bilgilerine erişmek istiyorum; böylece doğru ve güncel besin verilerine dayanarak kalori takibi yapabileyim.

#### Kabul Kriterleri

1. WHEN Web_Scraper başlatıldığında, THE Sistem SHALL `https://www.diyetkolik.com/kac-kalori/kategori/et-tavuk-balik` adresinden tüm besin öğelerini çekmelidir.
2. WHEN bir besin öğesi çekildiğinde, THE Web_Scraper SHALL her besin için besin adı, 100g başına kalori, protein (g), karbonhidrat (g) ve yağ (g) değerlerini ayrıştırmalıdır.
3. THE Besin_Veritabanı SHALL çekilen tüm besin verilerini yerel depolama alanına kaydetmelidir.
4. WHEN Web_Scraper bir HTTP hatasıyla karşılaştığında, THE Sistem SHALL hatayı günlüğe kaydetmeli ve mevcut yerel veritabanını kullanmaya devam etmelidir.
5. WHEN Web_Scraper başarıyla tamamlandığında, THE Sistem SHALL son güncelleme tarihini ve çekilen besin sayısını kaydetmelidir.
6. THE Web_Scraper SHALL en az 24 saatte bir otomatik olarak çalışmalıdır.
7. WHEN ağ bağlantısı mevcut değilse, THE Sistem SHALL son başarılı çekimden kalan yerel veritabanını kullanmalıdır.
8. FOR ALL çekilen besin verileri, veriyi ayrıştırıp yeniden serileştirip tekrar ayrıştırmak eşdeğer bir nesne üretmelidir (round-trip özelliği).

---

### Gereksinim 2: Besin Arama ve Kalori Günlüğü

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, yediğim besinleri arayıp günlük kalori günlüğüme eklemek istiyorum; böylece günlük kalori alımımı kolayca takip edebileyim.

#### Kabul Kriterleri

1. WHEN kullanıcı bir arama terimi girdiğinde, THE Besin_Veritabanı SHALL 300ms içinde eşleşen besinleri döndürmelidir.
2. WHEN kullanıcı bir besin seçtiğinde, THE Kalori_Hesaplayici SHALL kullanıcının girdiği gram miktarına göre kalori ve makro besin değerlerini hesaplamalıdır.
3. THE Kalori_Hesaplayici SHALL hesaplanan değeri kullanıcının günlük kalori günlüğüne eklemelidir.
4. WHEN kullanıcı bir günlük girişi sildiğinde, THE Kalori_Hesaplayici SHALL günlük toplamı buna göre güncellemelidir.
5. THE Sistem SHALL kullanıcının geçmiş 90 günlük kalori günlüğünü saklamalıdır.
6. WHEN kullanıcı bir tarih seçtiğinde, THE Sistem SHALL o tarihe ait kalori günlüğünü göstermelidir.

---

### Gereksinim 3: Günlük Kalori Hedefi ve Makro Takibi

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, günlük kalori ve makro besin hedeflerimi belirlemek ve ilerlemeyi takip etmek istiyorum; böylece beslenme hedeflerime ulaşabileyim.

#### Kabul Kriterleri

1. WHEN kullanıcı boy, kilo, yaş, cinsiyet ve aktivite seviyesini girdiğinde, THE Kalori_Hesaplayici SHALL BMR ve TDEE değerlerini hesaplamalıdır.
2. THE Sistem SHALL kullanıcının kilo verme, kilo alma veya kilo koruma hedefine göre önerilen günlük kalori hedefini hesaplamalıdır.
3. THE Sistem SHALL günlük protein, karbonhidrat ve yağ hedeflerini gram cinsinden göstermelidir.
4. WHILE kullanıcı günlük kalori günlüğünü görüntülüyorken, THE Pano SHALL tüketilen ve kalan kalori miktarını gerçek zamanlı olarak göstermelidir.
5. WHEN günlük kalori alımı Gunluk_Hedef'i aştığında, THE Sistem SHALL kullanıcıya görsel bir uyarı göstermelidir.
6. THE Sistem SHALL her makro besin için tüketilen miktarı ve hedefe olan yüzdeyi göstermelidir.

---

### Gereksinim 4: Spor Programı Oluşturma ve Takibi

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, düzenli antrenman programlarımı oluşturmak ve tamamlanan antrenmanları kaydetmek istiyorum; böylece spor rutinime sadık kalabileyim.

#### Kabul Kriterleri

1. THE Spor_Takipci SHALL kullanıcının egzersiz adı, set sayısı, tekrar sayısı ve ağırlık (kg) bilgilerini içeren Antrenman_Programi oluşturmasına izin vermelidir.
2. THE Spor_Takipci SHALL birden fazla Antrenman_Programi saklamalıdır (örn. Pazartesi-Üst Vücut, Çarşamba-Alt Vücut).
3. WHEN kullanıcı bir antrenmanı tamamlandı olarak işaretlediğinde, THE Spor_Takipci SHALL tamamlanma tarihini, süresini ve gerçekleştirilen set/tekrar/ağırlık bilgilerini kaydetmelidir.
4. THE Spor_Takipci SHALL son 12 haftaya ait antrenman geçmişini saklamalıdır.
5. WHEN kullanıcı antrenman geçmişini görüntülediğinde, THE Spor_Takipci SHALL haftalık antrenman sıklığını ve toplam antrenman süresini göstermelidir.
6. THE Sistem SHALL belirli bir egzersiz için ağırlık/tekrar ilerlemesini zaman içinde grafik olarak göstermelidir.
7. IF kullanıcı 3 veya daha fazla gün antrenman yapmadıysa, THE Sistem SHALL kullanıcıya bir hatırlatma bildirimi göstermelidir.

---

### Gereksinim 5: Kreatin Takibi

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, kreatin takviyesi alımımı takip etmek istiyorum; böylece yükleme ve idame fazlarını doğru şekilde yönetebileyim.

#### Kabul Kriterleri

1. THE Kreatin_Takipci SHALL kullanıcının günlük kreatin dozunu gram cinsinden kaydetmesine izin vermelidir.
2. THE Kreatin_Takipci SHALL yükleme fazı (günde 20g, 5-7 gün) ve idame fazı (günde 3-5g) olmak üzere iki faz modunu desteklemelidir.
3. WHEN kullanıcı kreatin alımını kaydettiğinde, THE Kreatin_Takipci SHALL alım zamanını ve dozunu kaydetmelidir.
4. THE Kreatin_Takipci SHALL mevcut faz, geçen gün sayısı ve toplam alınan kreatin miktarını göstermelidir.
5. WHEN yükleme fazı tamamlandığında (7 gün), THE Sistem SHALL kullanıcıya idame fazına geçmesi için bir bildirim göstermelidir.
6. THE Kreatin_Takipci SHALL son 30 günlük kreatin alım geçmişini göstermelidir.
7. IF kullanıcı günlük kreatin alımını kaydetmediyse, THE Sistem SHALL günün sonunda bir hatırlatma bildirimi göstermelidir.

---

### Gereksinim 6: Kilo ve Vücut Ölçümleri Kaydı

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, kilo ve vücut ölçümlerimi düzenli olarak kaydetmek istiyorum; böylece fiziksel değişimlerimi zaman içinde izleyebileyim.

#### Kabul Kriterleri

1. THE Olcum_Kayit SHALL kullanıcının kilo (kg), bel çevresi (cm), kalça çevresi (cm), göğüs çevresi (cm), kol çevresi (cm) ve bacak çevresi (cm) değerlerini kaydetmesine izin vermelidir.
2. WHEN kullanıcı yeni bir ölçüm kaydettiğinde, THE Olcum_Kayit SHALL ölçüm tarihini ve saatini otomatik olarak ekleyerek veriyi saklamalıdır.
3. THE Olcum_Kayit SHALL tüm ölçüm geçmişini saklamalıdır.
4. THE Sistem SHALL kilo değişimini zaman içinde grafik olarak göstermelidir.
5. WHEN kullanıcı ölçüm geçmişini görüntülediğinde, THE Olcum_Kayit SHALL ilk kayıt ile en son kayıt arasındaki farkı göstermelidir.
6. THE Sistem SHALL vücut ölçümlerinin her birini ayrı grafikler halinde göstermelidir.
7. IF kullanıcı 7 gün boyunca kilo kaydı yapmadıysa, THE Sistem SHALL kullanıcıya bir hatırlatma bildirimi göstermelidir.

---

### Gereksinim 7: Ana Pano (Dashboard)

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, spor, kilo ve kas kazanım verilerimi tek bir ekranda görmek istiyorum; böylece genel ilerlememimi hızlıca değerlendirebileyim.

#### Kabul Kriterleri

1. THE Pano SHALL günlük kalori alımı, kalan kalori, tüketilen makro besinler ve Gunluk_Hedef'e ulaşma yüzdesini göstermelidir.
2. THE Pano SHALL son 7 günlük kilo değişimini grafik olarak göstermelidir.
3. THE Pano SHALL bu haftaki tamamlanan antrenman sayısını ve bir sonraki planlanmış antrenmanı göstermelidir.
4. THE Pano SHALL bugünkü kreatin alım durumunu (alındı / alınmadı) göstermelidir.
5. THE Pano SHALL son 4 haftaya ait haftalık kalori ortalamasını grafik olarak göstermelidir.
6. WHEN kullanıcı Pano'yu açtığında, THE Sistem SHALL tüm verileri 1 saniye içinde yükleyip göstermelidir.
7. THE Pano SHALL son 30 günlük vücut ölçümü trendini (kilo + bel çevresi) göstermelidir.
8. THE Sistem SHALL kullanıcının haftalık antrenman hedefine (örn. haftada 4 gün) ulaşma yüzdesini göstermelidir.

---

### Gereksinim 8: Veri Dışa Aktarma

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, kalori ve ölçüm verilerimi dışa aktarmak istiyorum; böylece verilerimi yedekleyebileyim veya başka araçlarla analiz edebileyim.

#### Kabul Kriterleri

1. THE Sistem SHALL kalori günlüğü, ölçüm geçmişi ve antrenman geçmişini CSV formatında dışa aktarmalıdır.
2. WHEN kullanıcı dışa aktarma işlemini başlattığında, THE Sistem SHALL dışa aktarılacak tarih aralığını seçmesine izin vermelidir.
3. FOR ALL dışa aktarılan veriler, CSV dosyasını içe aktarıp tekrar dışa aktarmak aynı veriyi üretmelidir (round-trip özelliği).
4. IF dışa aktarma işlemi başarısız olursa, THE Sistem SHALL kullanıcıya açıklayıcı bir hata mesajı göstermelidir.
