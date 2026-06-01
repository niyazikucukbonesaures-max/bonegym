# 🍽️ Yemek Planlayıcı - Hedefe Göre Optimize Edildi

## 📋 Özet

Yemek planlayıcı artık kullanıcının hedefine göre (kilo verme, kas kazanma, vücut rekomposizyonu) **otomatik olarak protein ve makro besin oranlarını optimize ediyor**!

---

## ✨ Yeni Özellikler

### **1. Hedefe Göre Makro Oranları**

| Hedef | Protein | Karbonhidrat | Yağ | Açıklama |
|-------|---------|--------------|-----|----------|
| **Kilo Verme** | %35 | %35 | %30 | Kas koruma + kalori açığı |
| **Kas Kazanma** | %35 | %45 | %20 | Protein + enerji dengesi |
| **Vücut Rekomposizyonu** | %40 | %35 | %25 | Yüksek protein (kas koruma + yağ yakma) |
| **Kilo Koruma** | %30 | %40 | %30 | Dengeli beslenme |

### **2. Akıllı Yemek Seçimi**

Sistem artık yemekleri **4 kategoriye** ayırıyor:

- 🥩 **Yüksek Protein** (>20g/100g): Tavuk, et, balık, yumurta
- 🍗 **Orta Protein** (10-20g/100g): Baklagiller, süt ürünleri
- 🍚 **Düşük Protein** (<10g/100g): Tahıllar, sebzeler, meyveler
- 🥑 **Sağlıklı Yağ**: Zeytinyağı, fındık, avokado

**Hedefe göre seçim stratejisi:**

#### **Vücut Rekomposizyonu:**
- 2x Yüksek Protein + 1x Orta Protein
- Maksimum kas koruma ve yağ yakma

#### **Kas Kazanma:**
- 1x Yüksek Protein + 1x Orta Protein + 1x Düşük Protein
- Protein + karbonhidrat dengesi (enerji için)

#### **Kilo Verme:**
- 1x Yüksek Protein + 1x Orta Protein + 1x Sağlıklı Yağ
- Protein + düşük kalori

### **3. Protein Oranı Gösterimi**

Her yemek için **protein oranı (%)** gösteriliyor:
- Yüksek protein yemekleri kolayca tanımlayabilirsin
- Günlük protein hedefini takip edebilirsin

### **4. Hedef Bilgi Kartı**

Yemek planlayıcı sayfasında artık **hedef bilgi kartı** var:
- 🎯 Hedef adı ve ikonu
- 📊 Günlük makro hedefleri (gram ve yüzde)
- 💡 Hedefe özel açıklama

---

## 🎯 Kullanım Örnekleri

### **Örnek 1: Vücut Rekomposizyonu (95kg, 180cm)**

**Hedef:** Yağ yak + Kas koru

**Günlük Hedefler:**
- Kalori: 1,384 kcal
- Protein: 138g (%40) ← **Yüksek!**
- Karbonhidrat: 121g (%35)
- Yağ: 38g (%25)

**Örnek Öğün (Öğle Yemeği):**
1. Tavuk Göğsü Izgara - 200g (330 kcal, 62g protein) - **P%: 75%** 🔥
2. Bulgur Pilavı - 150g (180 kcal, 6g protein) - **P%: 13%**
3. Zeytinyağlı Fasulye - 100g (90 kcal, 5g protein) - **P%: 22%**

**Toplam:** 600 kcal, 73g protein (%49 protein oranı)

---

### **Örnek 2: Kas Kazanma**

**Hedef:** Kas yap + Enerji al

**Günlük Hedefler:**
- Kalori: 2,500 kcal
- Protein: 219g (%35)
- Karbonhidrat: 281g (%45) ← **Yüksek!**
- Yağ: 56g (%20)

**Örnek Öğün (Kahvaltı):**
1. Yumurta - 3 adet (210 kcal, 18g protein) - **P%: 34%**
2. Ekmek - 2 dilim (160 kcal, 5g protein) - **P%: 13%**
3. Peynir - 50g (150 kcal, 12g protein) - **P%: 32%**

**Toplam:** 520 kcal, 35g protein (%27 protein oranı)

---

### **Örnek 3: Kilo Verme**

**Hedef:** Yağ yak + Kas koru

**Günlük Hedefler:**
- Kalori: 1,600 kcal
- Protein: 140g (%35) ← **Yüksek!**
- Karbonhidrat: 140g (%35)
- Yağ: 53g (%30)

**Örnek Öğün (Akşam Yemeği):**
1. Izgara Balık - 200g (220 kcal, 44g protein) - **P%: 80%** 🔥
2. Salata - 150g (50 kcal, 2g protein) - **P%: 16%**
3. Zeytinyağı - 10g (90 kcal, 0g protein) - **P%: 0%**

**Toplam:** 360 kcal, 46g protein (%51 protein oranı)

---

## 🔧 Teknik Detaylar

### **Backend Değişiklikleri**

#### **meal_planner.py:**
- ✅ `_get_categorized_foods()`: Yemekleri 4 kategoriye ayırır
- ✅ `_select_foods_for_meal()`: Hedefe göre akıllı seçim
- ✅ `_calculate_daily_targets()`: Hedefe göre makro oranları
- ✅ `protein_ratio` ve `protein_percentage` hesaplamaları
- ✅ `goal_info` objesi eklendi

#### **routers/meal_plan.py:**
- ✅ Response'a `goal_info` eklendi
- ✅ Her yemek için `protein_ratio` eklendi
- ✅ Her gün için `protein_percentage` eklendi

### **Frontend Değişiklikleri**

#### **MealPlan.tsx:**
- ✅ **Hedef Bilgi Kartı** eklendi (gradient background)
- ✅ Protein yüzdesi gösterimi
- ✅ Hedefe göre renk kodlaması
- ✅ Hedefe göre emoji ikonları

#### **api.ts:**
- ✅ `GoalInfo` interface eklendi
- ✅ `MealSuggestion` ve `DayPlan` güncellenmiş
- ✅ TypeScript type safety

---

## 📊 Karşılaştırma: Eski vs Yeni

### **Eski Sistem:**
- ❌ Tüm hedefler için aynı makro oranları
- ❌ Rastgele yemek seçimi
- ❌ Protein oranı gösterilmiyor
- ❌ Hedef bilgisi yok

### **Yeni Sistem:**
- ✅ Hedefe göre optimize edilmiş makro oranları
- ✅ Akıllı yemek seçimi (4 kategori)
- ✅ Her yemek için protein oranı
- ✅ Hedef bilgi kartı
- ✅ Günlük protein yüzdesi
- ✅ Hedefe özel açıklamalar

---

## 🎨 UI İyileştirmeleri

### **Hedef Bilgi Kartı:**
```
┌─────────────────────────────────────────────────┐
│ 🔥 Kilo Verme                                   │
│ Bu plan senin hedefine göre optimize edildi    │
│                                                 │
│ Protein: 35%  Karb: 35%  Yağ: 30%             │
│ 140g/gün      140g/gün   53g/gün              │
└─────────────────────────────────────────────────┘
```

### **Yemek Kartı:**
```
🍽️ Öğle Yemeği
┌─────────────────────────────────────────────────┐
│ Tavuk Göğsü Izgara                              │
│ 200g                                            │
│                                                 │
│ Kalori: 330  Protein: 62g  P%: 75% 🔥         │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Nasıl Test Edilir?

1. **Uygulamayı başlat:**
   ```bash
   Fitness-App-Baslat.vbs
   ```

2. **Profil ayarla:**
   - Profil sayfasına git
   - Hedefini seç (Kilo Ver, Kas Kazan, Rekomp)
   - Kaydet

3. **Yemek planını oluştur:**
   - Yemek Planlayıcı sayfasına git
   - "Yeni Plan Oluştur" butonuna tıkla
   - Hedef bilgi kartını kontrol et

4. **Protein oranlarını kontrol et:**
   - Her yemeğin yanında **P%** göreceksin
   - Yüksek protein yemekleri **75%+** olacak
   - Günlük protein yüzdesi üstte gösteriliyor

---

## 💡 İpuçları

### **Vücut Rekomposizyonu için:**
- 🎯 Günlük **%40 protein** hedefle
- 🥩 Yüksek protein yemekleri seç (P% > 70%)
- 📊 Günlük protein yüzdesini takip et
- 💪 Kas koruma + yağ yakma dengesi

### **Kas Kazanma için:**
- 🎯 Günlük **%35 protein + %45 karb** hedefle
- 🍚 Karbonhidrat kaynaklarını ihmal etme
- 🏋️ Antrenman öncesi/sonrası karb al
- 💪 Protein + enerji dengesi

### **Kilo Verme için:**
- 🎯 Günlük **%35 protein** hedefle (kas koruma)
- 🥗 Düşük kalorili, yüksek protein yemekler
- 📉 Kalori açığını koru
- 💪 Kas kaybını önle

---

## 🐛 Bilinen Sorunlar

- ⚠️ Veritabanında yeterli yemek yoksa plan oluşturulamayabilir
- ⚠️ İlk kullanımda profil oluşturulmalı
- ⚠️ Alışveriş listesi PDF export henüz çalışmıyor

---

## 📝 Gelecek Güncellemeler

- [ ] Alerjik yiyecekleri hariç tutma
- [ ] Favori yemekleri kaydetme
- [ ] Öğün değiştirme özelliği
- [ ] PDF export
- [ ] Yemek tarifleri
- [ ] Besin değeri detayları

---

## 🎉 Sonuç

Yemek planlayıcı artık **hedefe göre optimize edilmiş** ve **protein odaklı**! 

Hedefine ulaşmak için doğru makro oranlarıyla beslen! 💪🔥

---

**Son Güncelleme:** 2026-04-28  
**Versiyon:** 2.1.0 (Hedefe Göre Optimize Edilmiş)
