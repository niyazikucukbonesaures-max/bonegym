# Fitness Kalori Takip İyileştirme Gereksinimleri

## Giriş

Bu doküman, mevcut fitness uygulamasındaki kilo hesaplama sistemi ve spor yapanlara yönelik özelliklerin iyileştirilmesi için gereksinimleri tanımlar. Sistem, daha doğru kilo takibi, gelişmiş kalori hesaplama, spor yapanlara özel özellikler ve iyileştirilmiş kullanıcı deneyimi sunacaktır.

## Sözlük

- **Kalori_Motoru**: Kalori hesaplama ve makro besin değeri hesaplama sistemi
- **Ölçüm_Takipçisi**: Kilo ve vücut ölçümlerini takip eden sistem
- **Spor_Profili**: Spor yapan kullanıcılar için özelleştirilmiş profil sistemi
- **Hedef_Hesaplayıcısı**: Kullanıcının hedeflerine göre kalori ve makro hedeflerini hesaplayan sistem
- **Trend_Analizörü**: Kilo ve ölçüm verilerindeki eğilimleri analiz eden sistem
- **Bildirim_Sistemi**: Kullanıcıya hatırlatma ve motivasyon bildirimleri gönderen sistem
- **Veri_Doğrulayıcısı**: Girilen verilerin mantıklı aralıklarda olup olmadığını kontrol eden sistem

## Gereksinimler

### Gereksinim 1: Gelişmiş Kilo Hesaplama Sistemi

**Kullanıcı Hikayesi:** Spor yapan bir kullanıcı olarak, doğru ve güvenilir kilo hesaplama sistemi istiyorum, böylece ilerlememi doğru şekilde takip edebilirim.

#### Kabul Kriterleri

1. WHEN kullanıcı kilo girişi yapar, THE Veri_Doğrulayıcısı SHALL girilen değerin 30-300 kg arasında olduğunu kontrol etmek
2. IF kilo değeri mantıksız aralıkta ise, THEN THE Sistem SHALL açıklayıcı hata mesajı göstermek
3. THE Kalori_Motoru SHALL Mifflin-St Jeor formülünü kullanarak BMR hesaplamak
4. WHEN yeni kilo ölçümü eklenir, THE Trend_Analizörü SHALL haftalık ortalama kilo değişimini hesaplamak
5. THE Sistem SHALL günlük kilo değişim limitini 0.5 kg olarak belirlemek ve aşılırsa uyarı vermek

### Gereksinim 2: Spor Yapanlara Özel Kalori Hedefleme

**Kullanıcı Hikayesi:** Aktif spor yapan bir kullanıcı olarak, antrenman günlerime göre farklı kalori hedefleri istiyorum, böylece performansımı optimize edebilirim.

#### Kabul Kriterleri

1. WHERE kullanıcı spor profili aktif ise, THE Hedef_Hesaplayıcısı SHALL antrenman günleri için %10-15 fazla kalori hedefi belirlemek
2. WHEN kullanıcı dinlenme günü seçer, THE Sistem SHALL bazal metabolizma hızına yakın kalori hedefi önermek
3. THE Sistem SHALL kas kazanma hedefi için protein oranını %35-40 arasında ayarlamak
4. WHEN kullanıcı yoğun antrenman yapar, THE Sistem SHALL karbonhidrat oranını %45-50 arasında artırmak
5. THE Hedef_Hesaplayıcısı SHALL vücut rekomposizyonu için hafif kalori açığı (-250 kalori) önermek

### Gereksinim 3: Gelişmiş Ölçüm Takip Sistemi

**Kullanıcı Hikayesi:** Fitness hedeflerim olan bir kullanıcı olarak, sadece kilo değil tüm vücut ölçümlerimi takip etmek istiyorum, böylece gerçek ilerlemeimi görebilirim.

#### Kabul Kriterleri

1. THE Ölçüm_Takipçisi SHALL kilo, bel, kalça, göğüs, kol ve bacak ölçümlerini kaydetmek
2. WHEN ölçüm girişi yapılır, THE Veri_Doğrulayıcısı SHALL her ölçüm için mantıklı aralıkları kontrol etmek
3. THE Trend_Analizörü SHALL son 30 günlük ölçüm değişimlerini görselleştirmek
4. WHEN ölçüm değeri %20'den fazla değişirse, THE Sistem SHALL doğrulama isteyerek uyarı vermek
5. THE Sistem SHALL vücut kompozisyonu değişimini (kas/yağ oranı tahmini) hesaplamak

### Gereksinim 4: Akıllı Bildirim ve Hatırlatma Sistemi

**Kullanıcı Hikayesi:** Düzenli takip yapmak isteyen bir kullanıcı olarak, akıllı hatırlatmalar almak istiyorum, böylece tutarlı veri girişi yapabilirim.

#### Kabul Kriterleri

1. WHEN kullanıcı 3 gün kilo ölçümü yapmaz, THE Bildirim_Sistemi SHALL hatırlatma bildirimi göndermek
2. THE Sistem SHALL kullanıcının geçmiş ölçüm saatlerini analiz ederek optimal hatırlatma zamanı önermek
3. WHEN haftalık hedef %80'in altında kalır, THE Sistem SHALL motivasyon mesajı göndermek
4. THE Bildirim_Sistemi SHALL aşırı bildirim göndermemek için günde maksimum 2 hatırlatma sınırı koymak
5. WHERE kullanıcı bildirim tercihlerini ayarlar, THE Sistem SHALL bu tercihleri kaydetmek ve uygulamak

### Gereksinim 5: Performans Analiz ve Raporlama

**Kullanıcı Hikayesi:** İlerlememi takip eden bir kullanıcı olarak, detaylı analiz raporları görmek istiyorum, böylece hangi alanlarda başarılı olduğumu anlayabilirim.

#### Kabul Kriterleri

1. THE Trend_Analizörü SHALL haftalık, aylık ve 3 aylık ilerleme raporları oluşturmak
2. WHEN kullanıcı rapor talep eder, THE Sistem SHALL kilo kaybı/kazanımı hızını hesaplamak
3. THE Sistem SHALL hedef başarım oranını yüzde olarak göstermek
4. WHEN veri yetersiz ise, THE Sistem SHALL "daha fazla veri gerekli" mesajı göstermek
5. THE Sistem SHALL ölçüm tutarlılığı skorunu hesaplamak ve göstermek

### Gereksinim 6: Veri Güvenliği ve Yedekleme

**Kullanıcı Hikayesi:** Verilerimi kaybetmek istemeyen bir kullanıcı olarak, güvenli veri saklama ve yedekleme sistemi istiyorum, böylece ölçümlerimi güvenle saklayabilirim.

#### Kabul Kriterleri

1. THE Sistem SHALL tüm ölçüm verilerini şifreleyerek veritabanında saklamak
2. WHEN veri girişi yapılır, THE Sistem SHALL otomatik yedekleme işlemi başlatmak
3. THE Sistem SHALL kullanıcı verilerini JSON formatında dışa aktarma imkanı sunmak
4. WHEN sistem hatası oluşur, THE Sistem SHALL veri kaybını önlemek için rollback işlemi yapmak
5. THE Sistem SHALL 30 günden eski geçici verileri temizlemek

### Gereksinim 7: Kullanıcı Deneyimi İyileştirmeleri

**Kullanıcı Hikayesi:** Kolay kullanım isteyen bir kullanıcı olarak, sezgisel ve hızlı veri girişi yapabilmek istiyorum, böylece uygulamayı düzenli kullanabilirim.

#### Kabul Kriterleri

1. THE Sistem SHALL son girilen değerleri hatırlayarak otomatik tamamlama sunmak
2. WHEN ölçüm girişi yapılır, THE Sistem SHALL 3 saniye içinde işlemi tamamlamak
3. THE Sistem SHALL görsel ilerleme çubukları ve grafikler göstermek
4. WHEN hata oluşur, THE Sistem SHALL kullanıcı dostu hata mesajları göstermek
5. THE Sistem SHALL koyu/açık tema seçenekleri sunmak

### Gereksinim 8: Kalori Hesaplama Doğruluğu

**Kullanıcı Hikayesi:** Doğru beslenme planı yapmak isteyen bir kullanıcı olarak, hassas kalori hesaplamaları görmek istiyorum, böylece hedeflerime ulaşabilirim.

#### Kabul Kriterleri

1. THE Kalori_Motoru SHALL besin değerlerini 100g başına 0.1 kalori hassasiyetle hesaplamak
2. WHEN makro besin hesaplaması yapılır, THE Sistem SHALL protein için 4 kal/g, karbonhidrat için 4 kal/g, yağ için 9 kal/g kullanmak
3. THE Sistem SHALL günlük kalori toplamını gerçek zamanlı güncellemek
4. WHEN besin verisi eksik ise, THE Sistem SHALL kullanıcıyı bilgilendirmek ve alternatif önermek
5. THE Kalori_Motoru SHALL yuvarlama hatalarını minimize etmek için çift hassasiyet kullanmak