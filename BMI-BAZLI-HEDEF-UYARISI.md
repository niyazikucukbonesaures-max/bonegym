# 🚨 BMI Bazlı Hedef Uyarı Sistemi

## 📋 Özet

Yemek planlayıcı artık kullanıcının **BMI'sine bakarak hedefin uygun olup olmadığını kontrol ediyor** ve **yanlış hedef seçilmişse uyarı veriyor**!

---

## ⚠️ Sorun

**Örnek Senaryo:**
- Kullanıcı: 60kg, 180cm (BMI: 18.5 - Zayıf)
- Seçilen Hedef: ⚡ Vücut Rekomposizyonu (Yağ Yak + Kas Koru)
- **SORUN:** Kullanıcı zaten zayıf, yağ yakmamalı, **kilo almalı**!

**Eski Sistem:**
- ❌ Hiçbir uyarı vermiyordu
- ❌ Yanlış hedef için plan oluşturuyordu
- ❌ Kullanıcı daha da zayıflayabilirdi

**Yeni Sistem:**
- ✅ BMI'yi kontrol ediyor
- ✅ Yanlış hedef seçilmişse uyarı veriyor
- ✅ Doğru hedefi öneriyor
- ✅ Kullanıcıyı profil sayfasına yönlendiriyor

---

## 🎯 Uyarı Kuralları

### **1. Ciddi Zayıflık (BMI < 16)**

**Durum:** Çok tehlikeli, acil kilo almalı

**Uyarı Verilen Hedefler:**
- 🔥 Kilo Verme (Yağ Yak)
- ⚡ Vücut Rekomposizyonu (Yağ Yak + Kas Koru)

**Uyarı Tipi:** 🚨 **ERROR** (Kırmızı)

**Mesaj:**
```
⚠️ Uyarı: Yanlış Hedef!
BMI: 15.2 - Ciddi Zayıflık. Kilo ALMALISINIZ! 
Lütfen hedefini '💪 Kas Kazanma (Kilo Al)' olarak değiştirin.
```

**Önerilen Hedef:** 💪 Kas Kazanma (Kilo Al)

---

### **2. Zayıf (BMI < 18.5)**

**Durum:** Zayıf, kilo alması önerilir

**Uyarı Verilen Hedefler:**
- 🔥 Kilo Verme (Yağ Yak)
- ⚡ Vücut Rekomposizyonu (Yağ Yak + Kas Koru)

**Uyarı Tipi:** ⚠️ **WARNING** (Turuncu)

**Mesaj:**
```
⚠️ Dikkat: Uygun Olmayan Hedef
BMI: 17.8 - Zayıf. Kilo almanız önerilir. 
Hedefini '💪 Kas Kazanma (Kilo Al)' olarak değiştirmeyi düşünün.
```

**Önerilen Hedef:** 💪 Kas Kazanma (Kilo Al)

---

### **3. Obez (BMI >= 30)**

**Durum:** Fazla kilolu, kilo vermesi önerilir

**Uyarı Verilen Hedefler:**
- 💪 Kas Kazanma (Kilo Al)

**Uyarı Tipi:** ⚠️ **WARNING** (Turuncu)

**Mesaj:**
```
⚠️ Dikkat: Uygun Olmayan Hedef
BMI: 32.5 - Obez. Önce kilo vermeniz önerilir. 
Hedefini '🔥 Kilo Verme (Yağ Yak)' olarak değiştirmeyi düşünün.
```

**Önerilen Hedef:** 🔥 Kilo Verme (Yağ Yak)

---

## 🎨 UI Tasarımı

### **Uyarı Kartı (ERROR - Kırmızı)**

```
┌─────────────────────────────────────────────────┐
│ 🚨  ⚠️ Uyarı: Yanlış Hedef!                    │
│                                                 │
│ BMI: 15.2 - Ciddi Zayıflık. Kilo ALMALISINIZ! │
│ Lütfen hedefini '💪 Kas Kazanma (Kilo Al)'    │
│ olarak değiştirin.                              │
│                                                 │
│ [Hedefimi Değiştir]  Önerilen: 💪 Kas Kazanma │
└─────────────────────────────────────────────────┘
```

### **Uyarı Kartı (WARNING - Turuncu)**

```
┌─────────────────────────────────────────────────┐
│ ⚠️  ⚠️ Dikkat: Uygun Olmayan Hedef             │
│                                                 │
│ BMI: 17.8 - Zayıf. Kilo almanız önerilir.     │
│ Hedefini '💪 Kas Kazanma (Kilo Al)' olarak    │
│ değiştirmeyi düşünün.                           │
│                                                 │
│ [Hedefimi Değiştir]  Önerilen: 💪 Kas Kazanma │
└─────────────────────────────────────────────────┘
```

---

## 📊 Örnek Senaryolar

### **Senaryo 1: Çok Zayıf Kullanıcı**

**Profil:**
- Kilo: 55kg
- Boy: 180cm
- BMI: 17.0 (Zayıf)
- Seçilen Hedef: ⚡ Vücut Rekomposizyonu

**Sistem Tepkisi:**
```
⚠️ Dikkat: Uygun Olmayan Hedef
BMI: 17.0 - Zayıf. Kilo almanız önerilir.
Hedefini '💪 Kas Kazanma (Kilo Al)' olarak değiştirmeyi düşünün.

[Hedefimi Değiştir] → Profil sayfasına yönlendirir
```

**Kullanıcı Aksiyonu:**
1. "Hedefimi Değiştir" butonuna tıklar
2. Profil sayfasına gider
3. Hedefi "💪 Kas Kazanma (Kilo Al)" olarak değiştirir
4. Yemek planlayıcıya geri döner
5. Artık uyarı yok, kilo alma planı görür

---

### **Senaryo 2: Obez Kullanıcı**

**Profil:**
- Kilo: 110kg
- Boy: 180cm
- BMI: 33.9 (Obez)
- Seçilen Hedef: 💪 Kas Kazanma (Kilo Al)

**Sistem Tepkisi:**
```
⚠️ Dikkat: Uygun Olmayan Hedef
BMI: 33.9 - Obez. Önce kilo vermeniz önerilir.
Hedefini '🔥 Kilo Verme (Yağ Yak)' olarak değiştirmeyi düşünün.

[Hedefimi Değiştir] → Profil sayfasına yönlendirir
```

---

### **Senaryo 3: Normal Kilolu Kullanıcı**

**Profil:**
- Kilo: 75kg
- Boy: 180cm
- BMI: 23.1 (Normal)
- Seçilen Hedef: ⚡ Vücut Rekomposizyonu

**Sistem Tepkisi:**
- ✅ Uyarı yok
- ✅ Plan normal şekilde oluşturulur
- ✅ Hedef uygun

---

## 🔧 Teknik Detaylar

### **Backend (meal_planner.py)**

#### **Yeni Fonksiyonlar:**

```python
def _calculate_bmi(self, weight_kg: float, height_cm: float) -> float:
    """BMI hesaplar"""
    height_m = height_cm / 100
    return weight_kg / (height_m * height_m)

def _check_goal_suitability(self, bmi: float, goal: str) -> Optional[Dict[str, str]]:
    """Hedefin BMI'ye uygunluğunu kontrol eder"""
    # BMI < 16: Ciddi zayıflık → ERROR
    # BMI < 18.5: Zayıf → WARNING
    # BMI >= 30: Obez → WARNING
    # Diğer: Uygun → None
```

#### **generate_weekly_plan() Güncellemesi:**

```python
# BMI hesapla ve hedef uygunluğunu kontrol et
bmi = self._calculate_bmi(profile.weight_kg, profile.height_cm)
goal_warning = self._check_goal_suitability(bmi, profile.goal)

# goal_info'ya ekle
goal_info = {
    ...
    "bmi": round(bmi, 1),
    "goal_warning": goal_warning,  # Uyarı varsa dict, yoksa None
}
```

### **Frontend (MealPlan.tsx)**

#### **Uyarı Kartı:**

```tsx
{goalInfo?.goal_warning && (
  <GlassCard className={`p-6 border-2 ${
    goalInfo.goal_warning.type === 'error' 
      ? 'bg-red-500/10 border-red-500/50' 
      : 'bg-orange-500/10 border-orange-500/50'
  }`}>
    <div className="flex items-start gap-4">
      <div className="text-4xl">
        {goalInfo.goal_warning.type === 'error' ? '🚨' : '⚠️'}
      </div>
      <div className="flex-1">
        <h3>{goalInfo.goal_warning.title}</h3>
        <p>{goalInfo.goal_warning.message}</p>
        <Button onClick={() => window.location.href = '/profile'}>
          Hedefimi Değiştir
        </Button>
      </div>
    </div>
  </GlassCard>
)}
```

#### **BMI Gösterimi:**

```tsx
{goalInfo.bmi && (
  <p className="text-white/50 text-xs">
    • BMI: {goalInfo.bmi}
  </p>
)}
```

---

## 🚀 Nasıl Test Edilir?

### **Test 1: Zayıf Kullanıcı**

1. **Profil ayarla:**
   - Kilo: 55kg
   - Boy: 180cm
   - Hedef: ⚡ Vücut Rekomposizyonu

2. **Yemek Planlayıcı'ya git**

3. **"Yeni Plan Oluştur" butonuna tıkla**

4. **Uyarı kartını gör:**
   - ⚠️ Turuncu uyarı
   - "BMI: 17.0 - Zayıf"
   - "Kilo almanız önerilir"
   - Önerilen: 💪 Kas Kazanma

5. **"Hedefimi Değiştir" butonuna tıkla**

6. **Profil sayfasına yönlendir**

7. **Hedefi değiştir:** 💪 Kas Kazanma (Kilo Al)

8. **Yemek Planlayıcı'ya geri dön**

9. **Artık uyarı yok!**

---

### **Test 2: Obez Kullanıcı**

1. **Profil ayarla:**
   - Kilo: 110kg
   - Boy: 180cm
   - Hedef: 💪 Kas Kazanma

2. **Yemek Planlayıcı'ya git**

3. **Uyarı kartını gör:**
   - ⚠️ Turuncu uyarı
   - "BMI: 33.9 - Obez"
   - "Önce kilo vermeniz önerilir"
   - Önerilen: 🔥 Kilo Verme

---

## 📁 Güncellenen Dosyalar

- ✅ `backend/app/meal_planner.py`
  - `_calculate_bmi()` fonksiyonu eklendi
  - `_check_goal_suitability()` fonksiyonu eklendi
  - `generate_weekly_plan()` güncellendi

- ✅ `frontend/src/lib/api.ts`
  - `GoalInfo` interface'ine `bmi` ve `goal_warning` eklendi

- ✅ `frontend/src/pages/MealPlan.tsx`
  - Uyarı kartı eklendi
  - BMI gösterimi eklendi
  - "Hedefimi Değiştir" butonu eklendi

---

## 🎉 Sonuç

Artık sistem **akıllı**! 

- Zayıf kullanıcıya "yağ yak" demiyor ✅
- Obez kullanıcıya "kilo al" demiyor ✅
- BMI'ye göre doğru hedefi öneriyor ✅
- Kullanıcıyı yanlış yönlendirmiyor ✅

**Sağlıklı beslenme için akıllı uyarılar!** 🚨💪

---

**Son Güncelleme:** 2026-04-28  
**Versiyon:** 2.3.0 (BMI Bazlı Hedef Uyarı Sistemi)
