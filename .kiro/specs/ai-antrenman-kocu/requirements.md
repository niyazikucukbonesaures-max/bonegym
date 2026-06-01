# Requirements Document

## Introduction

AI Antrenman Koçu, kullanıcının günlük kalori alımına, hedeflerine ve kişisel verilerine göre akıllı antrenman programı oluşturan AI destekli koç sistemidir. Bu sistem mevcut "Antrenman" sayfasına entegre edilecek ve hem yeni başlayanlar hem de deneyimli sporcular için basit, anlaşılır ve etkili antrenman önerileri sunacaktır.

## Glossary

- **AI_Coach**: Kullanıcı verilerine göre antrenman programı oluşturan yapay zeka sistemi
- **Workout_Program**: Belirli bir süre için planlanmış antrenman rutini
- **Calorie_Balance**: Günlük kalori alımı ile kalori harcaması arasındaki fark
- **User_Profile**: Kullanıcının yaş, kilo, boy, aktivite seviyesi gibi kişisel verilerini içeren profil
- **Training_Intensity**: Antrenmanın zorluk seviyesi (düşük, orta, yüksek)
- **Progress_Tracker**: Kullanıcının antrenman ilerlemesini takip eden sistem
- **Workout_Recommendation**: AI tarafından önerilen spesifik antrenman
- **Fitness_Goal**: Kullanıcının fitness hedefi (kilo verme, kas kazanma, kondisyon)

## Requirements

### Requirement 1: Kalori Bazlı Antrenman Yoğunluğu Belirleme

**User Story:** Kullanıcı olarak, günlük kalori alımıma göre uygun antrenman yoğunluğu önerilmesini istiyorum, böylece hedeflerime uygun egzersiz yapabilirim.

#### Acceptance Criteria

1. WHEN kullanıcı günlük kalori fazlası yaşıyorsa, THE AI_Coach SHALL yüksek yoğunluklu kardiyovasküler antrenman önerisi sunacak
2. WHEN kullanıcı günlük kalori açığı yaşıyorsa, THE AI_Coach SHALL düşük yoğunluklu kuvvet antrenmanı önerisi sunacak
3. WHEN kullanıcı kalori dengesi sağlıyorsa, THE AI_Coach SHALL orta yoğunluklu karma antrenman önerisi sunacak
4. THE AI_Coach SHALL kalori dengesini günlük olarak hesaplayacak
5. WHEN kalori dengesi değiştiğinde, THE AI_Coach SHALL antrenman önerisini 24 saat içinde güncelleyecek

### Requirement 2: Kişisel Verilere Göre Program Önerme

**User Story:** Kullanıcı olarak, yaş, kilo, boy ve aktivite seviyeme göre kişiselleştirilmiş antrenman programı almak istiyorum, böylece güvenli ve etkili egzersiz yapabilirim.

#### Acceptance Criteria

1. THE AI_Coach SHALL User_Profile verilerini kullanarak Workout_Program oluşturacak
2. WHEN kullanıcı 18-30 yaş aralığındaysa, THE AI_Coach SHALL yüksek yoğunluklu antrenmanlar önerecek
3. WHEN kullanıcı 50 yaş üzerindeyse, THE AI_Coach SHALL düşük etkili eklem dostu antrenmanlar önerecek
4. WHEN kullanıcı sedanter yaşam tarzına sahipse, THE AI_Coach SHALL başlangıç seviyesi antrenmanlar önerecek
5. WHEN kullanıcı aktif yaşam tarzına sahipse, THE AI_Coach SHALL orta-ileri seviye antrenmanlar önerecek
6. THE AI_Coach SHALL BMI değerine göre antrenman yoğunluğunu ayarlayacak

### Requirement 3: Günlük Kalori Alımına Göre Antrenman Tipi Ayarlama

**User Story:** Kullanıcı olarak, o gün ne kadar kalori aldığıma göre uygun antrenman tipi önerilmesini istiyorum, böylece enerji seviyeme uygun egzersiz yapabilirim.

#### Acceptance Criteria

1. WHEN günlük kalori alımı hedefin %120'sinin üzerindeyse, THE AI_Coach SHALL yağ yakıcı kardiyovasküler antrenman önerecek
2. WHEN günlük kalori alımı hedefin %80'inin altındaysa, THE AI_Coach SHALL hafif kuvvet antrenmanı önerecek
3. WHEN günlük kalori alımı hedef aralığındaysa, THE AI_Coach SHALL dengeli karma antrenman önerecek
4. THE AI_Coach SHALL antrenman öncesi enerji seviyesi uyarısı sunacak
5. WHEN kullanıcı düşük kalori aldığında, THE AI_Coach SHALL antrenman süresini %25 azaltacak

### Requirement 4: İlerleme Takibi ile Dinamik Program Güncelleme

**User Story:** Kullanıcı olarak, antrenman ilerlememe göre programımın otomatik güncellenmesini istiyorum, böylece sürekli gelişim sağlayabilirim.

#### Acceptance Criteria

1. THE Progress_Tracker SHALL kullanıcının haftalık antrenman performansını kayıt edecek
2. WHEN kullanıcı 3 hafta boyunca aynı antrenmanı kolayca tamamlıyorsa, THE AI_Coach SHALL zorluk seviyesini artıracak
3. WHEN kullanıcı antrenmanları %50'den az tamamlıyorsa, THE AI_Coach SHALL zorluk seviyesini azaltacak
4. THE AI_Coach SHALL aylık ilerleme raporu oluşturacak
5. WHEN kullanıcı hedefine ulaştığında, THE AI_Coach SHALL yeni hedef önerecek
6. THE Progress_Tracker SHALL antrenman sıklığını, süresini ve yoğunluğunu takip edecek

### Requirement 5: AI Destekli Kişiselleştirilmiş Öneriler

**User Story:** Kullanıcı olarak, AI tarafından analiz edilen verilerime göre akıllı antrenman önerileri almak istiyorum, böylece en etkili sonuçları elde edebilirim.

#### Acceptance Criteria

1. THE AI_Coach SHALL kullanıcının geçmiş antrenman verilerini analiz edecek
2. WHEN kullanıcı belirli kas gruplarını ihmal ediyorsa, THE AI_Coach SHALL o kas gruplarına odaklanan antrenmanlar önerecek
3. THE AI_Coach SHALL kullanıcının tercih ettiği antrenman türlerini öğrenecek
4. WHEN kullanıcı kardiyodan kaçınıyorsa, THE AI_Coach SHALL alternatif kardiyovasküler aktiviteler önerecek
5. THE AI_Coach SHALL antrenman öncesi motivasyon mesajları sunacak
6. WHEN kullanıcı dinlenme günündeyse, THE AI_Coach SHALL aktif dinlenme aktiviteleri önerecek

### Requirement 6: Mevcut Antrenman Sayfası Entegrasyonu

**User Story:** Kullanıcı olarak, AI koç özelliklerinin mevcut antrenman sayfasında sorunsuz çalışmasını istiyorum, böylece tek bir yerden tüm antrenman işlemlerimi yönetebilirim.

#### Acceptance Criteria

1. THE AI_Coach SHALL mevcut antrenman sayfası arayüzüne entegre olacak
2. THE AI_Coach SHALL mevcut antrenman kayıt sistemiyle uyumlu çalışacak
3. WHEN kullanıcı antrenman sayfasını açtığında, THE AI_Coach SHALL günlük önerisini 3 saniye içinde gösterecek
4. THE AI_Coach SHALL mevcut kullanıcı verilerini otomatik olarak kullanacak
5. THE AI_Coach SHALL basit ve anlaşılır arayüz sunacak
6. WHEN kullanıcı önerilen antrenmanı kabul ettiğinde, THE AI_Coach SHALL antrenmanı otomatik olarak kayıt edecek

### Requirement 7: Antrenman Güvenliği ve Sınırlamalar

**User Story:** Kullanıcı olarak, güvenli antrenman önerileri almak istiyorum, böylece yaralanma riskini minimize edebilirim.

#### Acceptance Criteria

1. THE AI_Coach SHALL kullanıcının sağlık durumunu dikkate alacak
2. WHEN kullanıcı yaralanma geçmişi bildirirse, THE AI_Coach SHALL o bölgeyi koruyucu antrenmanlar önerecek
3. THE AI_Coach SHALL günlük maksimum antrenman süresini 90 dakika ile sınırlayacak
4. WHEN kullanıcı aşırı yorgunluk belirtisi gösterirse, THE AI_Coach SHALL dinlenme günü önerecek
5. THE AI_Coach SHALL antrenman öncesi ısınma ve sonrası soğuma egzersizleri dahil edecek
6. IF kullanıcı sağlık sorunu bildirirse, THEN THE AI_Coach SHALL doktor onayı almasını önerecek

### Requirement 8: Performans ve Yanıt Süresi

**User Story:** Kullanıcı olarak, AI koçun hızlı yanıt vermesini istiyorum, böylece antrenman planımı geciktirmeden alabilirim.

#### Acceptance Criteria

1. THE AI_Coach SHALL antrenman önerisini 5 saniye içinde oluşturacak
2. THE AI_Coach SHALL kullanıcı etkileşimlerine 2 saniye içinde yanıt verecek
3. WHEN sistem yoğun olduğunda, THE AI_Coach SHALL önbelleğe alınmış önerileri sunacak
4. THE AI_Coach SHALL çevrimdışı modda temel önerileri sunabilecek
5. THE AI_Coach SHALL günde en fazla 1000 kullanıcıya eş zamanlı hizmet verebilecek