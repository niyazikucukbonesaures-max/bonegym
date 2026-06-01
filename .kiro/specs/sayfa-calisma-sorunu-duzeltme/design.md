# Sayfa Çalışma Sorunu Düzeltme - Bugfix Design

## Overview

Bu bug fix, fitness kalori takip uygulamasında authentication sisteminin eksik implementasyonundan kaynaklanan kritik bir sorunu çözmektedir. Dashboard sayfası çalışırken, diğer korumalı sayfalar (Kalori Günlüğü, Yemek Planlayıcı, Başarı Rozetleri vb.) authentication kontrolü yapılmadığı için API çağrıları başarısız oluyor ve sayfalar boş görünüyor.

**Fix Stratejisi:**
1. Protected Route component'i oluşturarak route seviyesinde authentication kontrolü eklemek
2. Axios interceptor'ları ekleyerek tüm API isteklerine otomatik token eklenmesini sağlamak
3. 401 hatalarını yakalayıp kullanıcıyı login sayfasına yönlendirmek
4. Login sayfasında zaten giriş yapmış kullanıcıları dashboard'a yönlendirmek

Bu fix minimal ve hedefli bir yaklaşım kullanarak sadece authentication akışını düzeltir, mevcut çalışan özellikleri korur.

## Glossary

- **Bug_Condition (C)**: Korumalı route'lara authentication olmadan erişim - kullanıcı token'ı olmadan `/food-log`, `/meal-plan`, `/achievements` gibi sayfalara erişebiliyor
- **Property (P)**: Authentication olmayan kullanıcılar korumalı sayfalara eriştiğinde login sayfasına yönlendirilmeli, authenticated kullanıcılar için API çağrıları token ile yapılmalı
- **Preservation**: Mevcut login/register akışı, Dashboard sayfası, logout işlevi ve authenticated kullanıcıların tüm sayfalara erişimi korunmalı
- **ProtectedRoute**: Authentication kontrolü yapan ve yetkisiz erişimleri login sayfasına yönlendiren wrapper component
- **Axios Interceptor**: HTTP isteklerini ve yanıtlarını otomatik olarak işleyen middleware fonksiyonları
- **AuthContext**: Kullanıcı authentication durumunu ve token'ı yöneten React context
- **Token**: Backend'den alınan ve localStorage'da saklanan JWT authentication token'ı

## Bug Details

### Bug Condition

Bug, kullanıcı authentication olmadan (token olmadan) korumalı route'lara erişmeye çalıştığında veya authenticated kullanıcı için API çağrılarına token eklenmediğinde ortaya çıkıyor. App.tsx'te route koruması eksik ve api.ts'te token yönetimi yapılmıyor.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type RouteAccess
  OUTPUT: boolean
  
  // input.isAuthenticated: Kullanıcının authentication durumu (boolean)
  // input.route: Erişilmeye çalışılan route (string)
  // input.isProtectedRoute: Route'un korumalı olup olmadığı (boolean)
  // input.hasToken: localStorage'da token olup olmadığı (boolean)
  
  RETURN (input.isProtectedRoute = true AND input.isAuthenticated = false)
         OR (input.isAuthenticated = true AND input.hasToken = false)
         OR (input.isAuthenticated = true AND NOT tokenAddedToApiCalls())
END FUNCTION
```

### Examples

**Örnek 1: Login Olmadan Food Log Sayfasına Erişim**
- Input: `{ isAuthenticated: false, route: '/food-log', isProtectedRoute: true, token: null }`
- Buggy Behavior: Sayfa render ediliyor, API çağrıları 401 hatası veriyor, sayfa boş görünüyor
- Expected: Kullanıcı `/login` sayfasına yönlendiriliyor, sayfa render edilmiyor

**Örnek 2: Login Olduktan Sonra Meal Plan Sayfasına Erişim**
- Input: `{ isAuthenticated: true, route: '/meal-plan', isProtectedRoute: true, token: 'valid-jwt-token' }`
- Buggy Behavior: Sayfa render ediliyor ancak API çağrılarına token eklenmiyor, 401 hataları alınıyor
- Expected: Sayfa render ediliyor, API çağrıları token ile yapılıyor, veriler başarıyla alınıyor

**Örnek 3: Logout Sonrası Back Button ile Korumalı Sayfaya Dönüş**
- Input: `{ isAuthenticated: false, route: '/achievements', isProtectedRoute: true, token: null, action: 'browser-back' }`
- Buggy Behavior: Sayfa erişilebilir kalıyor, cached veriler gösteriliyor
- Expected: Kullanıcı `/login` sayfasına yönlendiriliyor, cached veriler temizleniyor

**Örnek 4: Token Süresi Dolmuş Kullanıcı API Çağrısı Yapıyor**
- Input: `{ isAuthenticated: true, route: '/food-log', token: 'expired-jwt-token', apiCall: true }`
- Buggy Behavior: API 401 döndürüyor ancak kullanıcı login sayfasına yönlendirilmiyor
- Expected: 401 hatası yakalanıyor, token temizleniyor, kullanıcı login sayfasına yönlendiriliyor

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Login sayfasında email ve şifre ile giriş yapma işlevi değişmeden çalışmalı
- Register işlemi yeni kullanıcı oluşturmalı ve token üretmeli
- Dashboard sayfası authenticated kullanıcılar için düzgün çalışmaya devam etmeli
- Logout butonu kullanıcının session'ını sonlandırmalı ve login sayfasına yönlendirmeli
- localStorage'da geçerli token varsa kullanıcı otomatik giriş yapmalı
- AuthContext'in mevcut login, register, logout fonksiyonları değişmeden çalışmalı

**Scope:**
Authenticated kullanıcıların tüm sayfalara erişimi ve mevcut API çağrıları korunmalı. Sadece authentication kontrolü ve token yönetimi eklenecek, mevcut sayfa içerikleri ve işlevsellik değişmeyecek.

## Hypothesized Root Cause

Requirements dokümanı ve kod analizi temelinde, en olası nedenler:

1. **Missing Protected Route Component**: App.tsx'te route'ları koruyan bir wrapper component yok
   - Tüm route'lar doğrudan render ediliyor
   - Authentication kontrolü yapılmıyor
   - Yetkisiz erişimler engellenmemiş

2. **Missing Axios Request Interceptor**: api.ts'te token'ı otomatik ekleyen interceptor yok
   - AuthContext'te token set ediliyor ancak API çağrılarına eklenmiyor
   - Her sayfa manuel olarak token eklemek zorunda (yapılmamış)
   - Token yönetimi merkezi değil

3. **Missing Axios Response Interceptor**: 401 hatalarını yakalayan interceptor yok
   - Backend 401 döndürdüğünde frontend tepki vermiyor
   - Token süresi dolduğunda kullanıcı login sayfasına yönlendirilmiyor
   - Her sayfa kendi error handling'ini yapmak zorunda

4. **No Login Page Redirect for Authenticated Users**: Login sayfası zaten giriş yapmış kullanıcıları kontrol etmiyor
   - Authenticated kullanıcı `/login` sayfasına gidebiliyor
   - Dashboard'a otomatik yönlendirme yok

## Correctness Properties

Property 1: Bug Condition - Protected Route Access Control

_For any_ route access where the user is not authenticated (token is null or missing) and the route is protected (not `/login`), the fixed routing system SHALL redirect the user to `/login` page without rendering the protected page or making any API calls.

**Validates: Requirements 2.1, 2.4**

Property 2: Bug Condition - API Token Injection

_For any_ API request made by an authenticated user (token exists in AuthContext), the fixed API client SHALL automatically include the authentication token in the Authorization header as `Bearer {token}`.

**Validates: Requirements 2.2**

Property 3: Bug Condition - 401 Error Handling

_For any_ API response with 401 Unauthorized status, the fixed API client SHALL clear the authentication token from localStorage and AuthContext, then redirect the user to `/login` page.

**Validates: Requirements 2.3**

Property 4: Preservation - Authenticated User Access

_For any_ route access where the user is authenticated (token exists and is valid), the fixed routing system SHALL render the requested page and allow API calls to proceed with the token, preserving all existing functionality.

**Validates: Requirements 3.1, 3.2, 3.4, 3.6**

Property 5: Preservation - Login/Register Flow

_For any_ login or register operation, the fixed authentication system SHALL produce the same result as the original system, successfully authenticating the user, storing the token, and redirecting to dashboard.

**Validates: Requirements 3.1, 3.5**

Property 6: Preservation - Logout Functionality

_For any_ logout operation, the fixed authentication system SHALL clear the user session, remove the token from storage, and redirect to login page, exactly as the original system does.

**Validates: Requirements 3.3**

## Fix Implementation

### Changes Required

Kök neden analizimiz doğruysa, aşağıdaki değişiklikler gerekli:

**File 1**: `frontend/src/components/ProtectedRoute.tsx` (YENİ DOSYA)

**Purpose**: Authentication kontrolü yapan wrapper component

**Specific Changes**:
1. **ProtectedRoute Component Oluştur**:
   - `useAuth()` hook'u ile authentication durumunu kontrol et
   - `isLoading` durumunda loading göster
   - `token` yoksa `/login` sayfasına yönlendir
   - `token` varsa children'ı render et

2. **Loading State Ekle**:
   - AuthContext'ten `isLoading` state'ini al
   - Loading sırasında spinner göster
   - Flickering'i önlemek için hızlı geçiş yap

**File 2**: `frontend/src/App.tsx`

**Purpose**: Route'ları ProtectedRoute ile koru

**Specific Changes**:
1. **ProtectedRoute Import Et**:
   - Yeni oluşturulan ProtectedRoute component'ini import et

2. **Korumalı Route'ları Wrap Et**:
   - `/dashboard`, `/food-log`, `/meal-plan`, `/achievements`, `/workouts`, `/creatine`, `/measurements`, `/profile`, `/export` route'larını ProtectedRoute ile sar
   - `/login` route'unu public bırak

3. **Route Yapısını Güncelle**:
   - Her korumalı route için: `<Route path="/..." element={<ProtectedRoute><Layout><Page /></Layout></ProtectedRoute>} />`
   - Login route için: `<Route path="/login" element={<Login />} />` (değişmeden)

**File 3**: `frontend/src/lib/api.ts`

**Purpose**: Axios interceptor'ları ekle

**Specific Changes**:
1. **Request Interceptor Ekle**:
   - localStorage'dan token'ı al
   - Token varsa Authorization header'ına ekle: `Bearer {token}`
   - Her API çağrısında otomatik çalışsın

2. **Response Interceptor Ekle**:
   - 401 hatalarını yakala
   - Token'ı localStorage'dan ve AuthContext'ten temizle
   - Kullanıcıyı `/login` sayfasına yönlendir
   - Diğer hataları olduğu gibi fırlat

3. **Interceptor Setup Function**:
   - `setupInterceptors()` fonksiyonu oluştur
   - Request ve response interceptor'larını kaydet
   - Export et

**File 4**: `frontend/src/contexts/AuthContext.tsx`

**Purpose**: Interceptor'ları initialize et

**Specific Changes**:
1. **setupInterceptors Import Et**:
   - api.ts'ten setupInterceptors fonksiyonunu import et

2. **useEffect'te Interceptor'ları Başlat**:
   - Component mount olduğunda setupInterceptors() çağır
   - Token yüklendiğinde interceptor'lar hazır olsun

**File 5**: `frontend/src/pages/Login.tsx`

**Purpose**: Authenticated kullanıcıları dashboard'a yönlendir

**Specific Changes**:
1. **useAuth Hook Ekle**:
   - AuthContext'ten token ve isLoading al

2. **useEffect ile Redirect Ekle**:
   - Token varsa ve loading bitmişse `/dashboard` sayfasına yönlendir
   - Navigate hook'u kullan

3. **Loading State Göster**:
   - isLoading true ise spinner göster
   - Flickering'i önle

## Testing Strategy

### Validation Approach

Testing stratejisi iki aşamalı: önce bug'ı unfixed code'da göster (exploratory), sonra fix'in çalıştığını ve mevcut davranışı koruduğunu doğrula (fix checking + preservation checking).

### Exploratory Bug Condition Checking

**Goal**: Bug'ı UNFIXED code'da göstermek. Korumalı sayfalara authentication olmadan erişilebildiğini ve API çağrılarının başarısız olduğunu doğrulamak.

**Test Plan**: Manuel test - browser'da unfixed code'u çalıştır ve aşağıdaki senaryoları test et. Her senaryo için console'da hataları ve network tab'ında 401 response'ları gözlemle.

**Test Cases**:
1. **Unauthenticated Access Test**: Logout durumunda `/food-log` sayfasına git (unfixed code'da sayfa render edilir ancak API 401 verir)
2. **Missing Token in API Test**: Login yap, localStorage'dan token'ı sil, `/meal-plan` sayfasına git (unfixed code'da API çağrıları 401 verir)
3. **Back Button After Logout Test**: Login yap, logout yap, browser back butonuna bas (unfixed code'da sayfa erişilebilir kalır)
4. **Expired Token Test**: Geçersiz token ile API çağrısı yap (unfixed code'da 401 hatası yakalanmaz)

**Expected Counterexamples**:
- Korumalı sayfalar authentication olmadan render ediliyor
- API çağrılarına token eklenmiyor
- 401 hataları yakalanmıyor ve kullanıcı login sayfasına yönlendirilmiyor
- Possible causes: Missing ProtectedRoute, missing axios interceptors

### Fix Checking

**Goal**: Fix'in bug condition'ı çözdüğünü doğrulamak. Korumalı sayfalara authentication olmadan erişimin engellendiğini ve API çağrılarına token'ın eklendiğini test etmek.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := handleRouteAccess_fixed(input)
  ASSERT result.redirectedToLogin = true AND 
         result.pageRendered = false AND
         result.apiCallsIncludeToken = true
END FOR
```

**Test Plan**: Manuel test - fixed code'u çalıştır ve aşağıdaki senaryoları test et.

**Test Cases**:
1. **Protected Route Redirect Test**: Logout durumunda `/food-log` sayfasına git → `/login` sayfasına yönlendirilmeli
2. **API Token Injection Test**: Login yap, network tab'ında API çağrılarını kontrol et → Authorization header'ı olmalı
3. **401 Error Handling Test**: Backend'i durdur veya geçersiz token kullan → 401 hatası yakalanmalı, login sayfasına yönlendirilmeli
4. **Back Button Protection Test**: Login yap, logout yap, back butonuna bas → Login sayfasına yönlendirilmeli

### Preservation Checking

**Goal**: Fix'in mevcut çalışan özellikleri bozmadığını doğrulamak. Authenticated kullanıcıların tüm sayfalara erişimini ve login/register/logout işlevlerini test etmek.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT handleRouteAccess_original(input) = handleRouteAccess_fixed(input)
END FOR
```

**Testing Approach**: Manuel test - fixed code'da mevcut özelliklerin çalıştığını doğrula.

**Test Plan**: Unfixed code'da çalışan özellikleri gözlemle, sonra fixed code'da aynı davranışı doğrula.

**Test Cases**:
1. **Login Flow Preservation**: Email ve şifre ile login yap → Dashboard'a yönlendirilmeli, token kaydedilmeli
2. **Register Flow Preservation**: Yeni kullanıcı kaydet → Token alınmalı, dashboard'a yönlendirilmeli
3. **Dashboard Access Preservation**: Login yap, dashboard'a git → Sayfa düzgün çalışmalı, veriler gösterilmeli
4. **Logout Preservation**: Logout butonuna tıkla → Token temizlenmeli, login sayfasına yönlendirilmeli
5. **Auto Login Preservation**: Browser'ı kapat, tekrar aç (localStorage'da token var) → Otomatik giriş yapmalı
6. **All Pages Access Preservation**: Login yap, tüm sayfalara git → Her sayfa düzgün çalışmalı, API çağrıları başarılı olmalı

### Unit Tests

- ProtectedRoute component'i için unit test: authenticated ve unauthenticated durumları test et
- Axios interceptor'ları için unit test: token ekleme ve 401 handling'i test et
- Login page redirect logic için unit test: authenticated kullanıcı yönlendirmesini test et

### Property-Based Tests

Property-based testing bu bug fix için uygun değil çünkü:
- Authentication durumu binary (authenticated/unauthenticated)
- Route'lar sabit (protected/public)
- Test senaryoları sınırlı ve manuel test ile kolayca doğrulanabilir

Manuel test ve unit test'ler yeterli coverage sağlar.

### Integration Tests

- Full authentication flow test: Login → Protected page access → API calls → Logout → Access denied
- Token expiration flow test: Login → Wait for token expiration → API call → 401 → Redirect to login
- Browser navigation test: Login → Navigate to pages → Logout → Back button → Redirect to login
- Auto login test: Login → Close browser → Reopen → Auto login → Access protected pages
