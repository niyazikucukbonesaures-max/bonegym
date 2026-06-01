# Bugfix Requirements Document

## Introduction

Fitness kalori takip uygulamasında kritik bir authentication bug'ı tespit edildi. Dashboard sayfası çalışırken, Kalori Günlüğü, Yemek Planlayıcı ve Başarı Rozetleri sayfaları çalışmıyor. Kullanıcı login yapabiliyor ancak diğer sayfalara eriştiğinde authentication kontrolü yapılmadığı için API çağrıları başarısız oluyor ve sayfalar boş görünüyor.

**Etkilenen Sayfalar:**
- `/food-log` - Kalori Günlüğü
- `/meal-plan` - Yemek Planlayıcı
- `/achievements` - Başarı Rozetleri
- Diğer korumalı sayfalar (Workouts, Creatine, Measurements, Profile, Export)

**Çalışan Sayfalar:**
- `/login` - Login sayfası
- `/dashboard` - Dashboard sayfası (kısmen çalışıyor)

**Kök Neden:**
App.tsx'te route koruması (Protected Route) implementasyonu eksik. Kullanıcı authentication durumu kontrol edilmiyor ve token olmadan sayfalara erişim sağlanıyor.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN kullanıcı login yapmadan herhangi bir sayfaya (örn: `/food-log`, `/meal-plan`, `/achievements`) erişmeye çalıştığında THEN sistem kullanıcıyı login sayfasına yönlendirmiyor ve sayfa boş görünüyor

1.2 WHEN kullanıcı login yaptıktan sonra Dashboard dışındaki sayfalara (örn: `/food-log`, `/meal-plan`, `/achievements`) gittiğinde THEN sayfalar yükleniyor ancak API çağrıları başarısız oluyor ve içerik gösterilmiyor

1.3 WHEN kullanıcı token'ı olmadan korumalı API endpoint'lerine istek gönderildiğinde THEN backend 401 Unauthorized hatası döndürüyor ancak frontend bu hatayı yakalayıp kullanıcıyı login sayfasına yönlendirmiyor

1.4 WHEN kullanıcı logout yaptıktan sonra browser'ın back butonuyla korumalı sayfalara geri gittiğinde THEN sayfalar hala erişilebilir durumda kalıyor

### Expected Behavior (Correct)

2.1 WHEN kullanıcı login yapmadan herhangi bir korumalı sayfaya erişmeye çalıştığında THEN sistem kullanıcıyı otomatik olarak `/login` sayfasına yönlendirmeli

2.2 WHEN kullanıcı login yaptıktan sonra Dashboard dışındaki sayfalara gittiğinde THEN authentication token API çağrılarına dahil edilmeli ve sayfalar düzgün çalışmalı

2.3 WHEN kullanıcı token'ı olmadan veya geçersiz token ile korumalı API endpoint'lerine istek gönderildiğinde THEN frontend 401 hatalarını yakalayıp kullanıcıyı login sayfasına yönlendirmeli

2.4 WHEN kullanıcı logout yaptıktan sonra browser'ın back butonuyla korumalı sayfalara geri gitmeye çalıştığında THEN sistem kullanıcıyı login sayfasına yönlendirmeli

2.5 WHEN kullanıcı login sayfasındayken ve zaten giriş yapmışsa THEN sistem kullanıcıyı otomatik olarak dashboard'a yönlendirmeli

### Unchanged Behavior (Regression Prevention)

3.1 WHEN kullanıcı login sayfasında email ve şifre girip giriş yaptığında THEN sistem kullanıcıyı başarıyla authenticate etmeli ve dashboard'a yönlendirmeli

3.2 WHEN kullanıcı Dashboard sayfasında olduğunda THEN sayfa düzgün çalışmaya devam etmeli ve tüm veriler gösterilmeli

3.3 WHEN kullanıcı logout butonuna tıkladığında THEN sistem kullanıcının session'ını sonlandırmalı ve login sayfasına yönlendirmeli

3.4 WHEN kullanıcı giriş yapmış ve token'ı geçerliyken API çağrıları yapıldığında THEN backend istekleri başarıyla işlemeli ve veri döndürmeli

3.5 WHEN kullanıcı kayıt (register) işlemi yaptığında THEN sistem yeni kullanıcı oluşturmalı, token üretmeli ve dashboard'a yönlendirmeli

3.6 WHEN kullanıcı tarayıcıyı kapattıktan sonra tekrar açtığında ve localStorage'da geçerli token varsa THEN sistem kullanıcıyı otomatik olarak giriş yapmış saymalı

## Bug Condition

### Bug Condition Function

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type RouteAccess
  OUTPUT: boolean
  
  // X.isAuthenticated: Kullanıcının authentication durumu (boolean)
  // X.route: Erişilmeye çalışılan route (string)
  // X.isProtectedRoute: Route'un korumalı olup olmadığı (boolean)
  
  // Bug condition: Korumalı route'a authentication olmadan erişim
  RETURN X.isProtectedRoute = true AND X.isAuthenticated = false
END FUNCTION
```

### Property Specification - Fix Checking

```pascal
// Property: Protected Route Access Control
FOR ALL X WHERE isBugCondition(X) DO
  result ← handleRouteAccess'(X)
  ASSERT result.redirectedToLogin = true AND 
         result.pageRendered = false AND
         result.apiCallsMade = false
END FOR
```

**Açıklama:**
- Korumalı route'lara authentication olmadan erişim denendiğinde
- Kullanıcı login sayfasına yönlendirilmeli
- Sayfa render edilmemeli
- API çağrıları yapılmamalı

### Property Specification - Preservation Checking

```pascal
// Property: Authenticated User Access Preservation
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT handleRouteAccess(X) = handleRouteAccess'(X)
END FOR
```

**Açıklama:**
- Authentication yapılmış kullanıcılar için mevcut davranış korunmalı
- Login/Register işlemleri etkilenmemeli
- Public route'lar (login sayfası) etkilenmemeli
- Authenticated kullanıcıların tüm sayfalara erişimi korunmalı

## Counterexamples

### Örnek 1: Login Olmadan Food Log Sayfasına Erişim

**Input:**
```typescript
{
  isAuthenticated: false,
  route: '/food-log',
  isProtectedRoute: true,
  token: null
}
```

**Current Behavior (Buggy):**
- Sayfa render ediliyor
- API çağrıları yapılıyor
- 401 hataları alınıyor
- Sayfa boş görünüyor
- Kullanıcı login sayfasına yönlendirilmiyor

**Expected Behavior (Fixed):**
- Kullanıcı `/login` sayfasına yönlendiriliyor
- Sayfa render edilmiyor
- API çağrıları yapılmıyor

### Örnek 2: Login Olduktan Sonra Meal Plan Sayfasına Erişim

**Input:**
```typescript
{
  isAuthenticated: true,
  route: '/meal-plan',
  isProtectedRoute: true,
  token: 'valid-jwt-token-xyz'
}
```

**Current Behavior (Buggy):**
- Sayfa render ediliyor
- API çağrıları yapılıyor ancak token header'a eklenmiyor
- 401 hataları alınıyor
- Sayfa boş görünüyor

**Expected Behavior (Fixed):**
- Sayfa render ediliyor
- API çağrıları token ile yapılıyor
- Veriler başarıyla alınıyor
- Sayfa düzgün çalışıyor

### Örnek 3: Logout Sonrası Back Button ile Korumalı Sayfaya Dönüş

**Input:**
```typescript
{
  isAuthenticated: false,
  route: '/achievements',
  isProtectedRoute: true,
  token: null,
  action: 'browser-back'
}
```

**Current Behavior (Buggy):**
- Sayfa erişilebilir kalıyor
- Cached veriler gösteriliyor (varsa)
- Kullanıcı login sayfasına yönlendirilmiyor

**Expected Behavior (Fixed):**
- Kullanıcı `/login` sayfasına yönlendiriliyor
- Cached veriler temizleniyor
- Sayfa erişilemez hale geliyor
