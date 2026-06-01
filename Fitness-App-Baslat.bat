@echo off
chcp 65001 >nul
title KaloriSpor - Başlatıcı

:: ============================================================
::  Renk kodları (ANSI)
:: ============================================================
set "GREEN=[92m"
set "CYAN=[96m"
set "YELLOW=[93m"
set "RED=[91m"
set "WHITE=[97m"
set "GRAY=[90m"
set "RESET=[0m"

cls

:: ============================================================
::  ASCII Banner
:: ============================================================
echo.
echo %CYAN%  ██╗  ██╗ █████╗ ██╗      ██████╗ ██████╗ ██╗    ███████╗██████╗  ██████╗ ██████╗ %RESET%
echo %CYAN%  ██║ ██╔╝██╔══██╗██║     ██╔═══██╗██╔══██╗██║    ██╔════╝██╔══██╗██╔═══██╗██╔══██╗%RESET%
echo %CYAN%  █████╔╝ ███████║██║     ██║   ██║██████╔╝██║    ███████╗██████╔╝██║   ██║██████╔╝%RESET%
echo %CYAN%  ██╔═██╗ ██╔══██║██║     ██║   ██║██╔══██╗██║    ╚════██║██╔═══╝ ██║   ██║██╔══██╗%RESET%
echo %CYAN%  ██║  ██╗██║  ██║███████╗╚██████╔╝██║  ██║██║    ███████║██║     ╚██████╔╝██║  ██║%RESET%
echo %CYAN%  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝    ╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝%RESET%
echo.
echo %GRAY%  ─────────────────────────────────────────────────────────────────────────────────%RESET%
echo %WHITE%                    Fitness ve Kalori Takip Uygulaması v2.0%RESET%
echo %GRAY%  ─────────────────────────────────────────────────────────────────────────────────%RESET%
echo.

:: ============================================================
::  Dizin ayarları
:: ============================================================
set "ROOT=%~dp0"
:: Sondaki ters bölü işaretini kaldır
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"
set "VENV=%BACKEND%\venv"

:: ============================================================
::  Klasör kontrolleri
:: ============================================================
if not exist "%BACKEND%" (
    echo %RED%  [HATA] Backend klasörü bulunamadı: %BACKEND%%RESET%
    pause & exit /b 1
)
if not exist "%FRONTEND%" (
    echo %RED%  [HATA] Frontend klasörü bulunamadı: %FRONTEND%%RESET%
    pause & exit /b 1
)

:: ============================================================
::  [1/5] Python kontrolü
:: ============================================================
echo %YELLOW%  [1/5] Python kontrol ediliyor...%RESET%
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%       ✗ Python bulunamadı! https://python.org adresinden indirin.%RESET%
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo %GREEN%       ✓ %PYVER% bulundu%RESET%

:: ============================================================
::  [2/5] Node.js kontrolü
:: ============================================================
echo %YELLOW%  [2/5] Node.js kontrol ediliyor...%RESET%
node --version >nul 2>&1
if errorlevel 1 (
    echo %RED%       ✗ Node.js bulunamadı! https://nodejs.org adresinden indirin.%RESET%
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do set NODEVER=%%v
echo %GREEN%       ✓ Node.js %NODEVER% bulundu%RESET%

:: ============================================================
::  [3/5] Virtual environment ve bağımlılıklar
:: ============================================================
echo %YELLOW%  [3/5] Python ortamı hazırlanıyor...%RESET%

:: venv yoksa oluştur
if not exist "%VENV%\Scripts\activate.bat" (
    echo %GRAY%       venv bulunamadı, oluşturuluyor...%RESET%
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo %RED%       ✗ venv oluşturulamadı!%RESET%
        pause & exit /b 1
    )
    echo %GREEN%       ✓ venv oluşturuldu%RESET%
    :: İlk kurulumda bağımlılıkları yükle
    echo %GRAY%       Bağımlılıklar yükleniyor (ilk kurulum, biraz sürebilir)...%RESET%
    call "%VENV%\Scripts\activate.bat"
    pip install -q -r "%BACKEND%\requirements.txt"
    if errorlevel 1 (
        echo %RED%       ✗ Bağımlılıklar yüklenemedi!%RESET%
        pause & exit /b 1
    )
    echo %GREEN%       ✓ Bağımlılıklar yüklendi%RESET%
) else (
    echo %GREEN%       ✓ venv mevcut%RESET%
)

:: ============================================================
::  [4/5] Node modülleri kontrolü
:: ============================================================
echo %YELLOW%  [4/5] Frontend bağımlılıkları kontrol ediliyor...%RESET%
if not exist "%FRONTEND%\node_modules" (
    echo %GRAY%       node_modules bulunamadı, npm install çalıştırılıyor...%RESET%
    pushd "%FRONTEND%"
    npm install --silent
    if errorlevel 1 (
        echo %RED%       ✗ npm install başarısız!%RESET%
        popd & pause & exit /b 1
    )
    popd
    echo %GREEN%       ✓ npm paketleri yüklendi%RESET%
) else (
    echo %GREEN%       ✓ node_modules mevcut%RESET%
)

:: ============================================================
::  [5/5] Port temizliği
:: ============================================================
echo %YELLOW%  [5/5] Portlar temizleniyor...%RESET%

:: Port 8000 kontrolü
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr /R ":8000 "') do (
    if not "%%p"=="" (
        echo %GRAY%       Port 8000 kullanımda (PID: %%p), kapatılıyor...%RESET%
        taskkill /PID %%p /F >nul 2>&1
    )
)

:: Port 5173 kontrolü
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr /R ":5173 "') do (
    if not "%%p"=="" (
        echo %GRAY%       Port 5173 kullanımda (PID: %%p), kapatılıyor...%RESET%
        taskkill /PID %%p /F >nul 2>&1
    )
)

timeout /t 1 /nobreak >nul
echo %GREEN%       ✓ Portlar hazır (8000, 5173)%RESET%

:: ============================================================
::  Backend başlat
:: ============================================================
echo.
echo %CYAN%  ┌─────────────────────────────────────────┐%RESET%
echo %CYAN%  │  🚀 Backend başlatılıyor (port 8000)    │%RESET%
echo %CYAN%  └─────────────────────────────────────────┘%RESET%

start "KaloriSpor-Backend" cmd /k "title KaloriSpor-Backend && color 0A && cd /d "%BACKEND%" && call venv\Scripts\activate.bat && echo. && echo  ╔══════════════════════════════════╗ && echo  ║  KaloriSpor Backend API v2.0     ║ && echo  ║  http://localhost:8000           ║ && echo  ║  http://localhost:8000/docs      ║ && echo  ╚══════════════════════════════════╝ && echo. && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo %GRAY%       Backend başlaması bekleniyor...%RESET%
timeout /t 6 /nobreak >nul

:: Backend sağlık kontrolü (curl varsa)
curl -s --max-time 3 http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%       ⚠ Backend henüz yanıt vermiyor, 4 saniye daha bekleniyor...%RESET%
    timeout /t 4 /nobreak >nul
)
echo %GREEN%       ✓ Backend çalışıyor → http://localhost:8000%RESET%

:: ============================================================
::  Frontend başlat
:: ============================================================
echo.
echo %CYAN%  ┌─────────────────────────────────────────┐%RESET%
echo %CYAN%  │  🌐 Frontend başlatılıyor (port 5173)   │%RESET%
echo %CYAN%  └─────────────────────────────────────────┘%RESET%

start "KaloriSpor-Frontend" cmd /k "title KaloriSpor-Frontend && color 0B && cd /d "%FRONTEND%" && echo. && echo  ╔══════════════════════════════════╗ && echo  ║  KaloriSpor Frontend v2.0        ║ && echo  ║  http://localhost:5173           ║ && echo  ╚══════════════════════════════════╝ && echo. && npm run dev"

echo %GRAY%       Frontend başlaması bekleniyor...%RESET%
timeout /t 7 /nobreak >nul
echo %GREEN%       ✓ Frontend çalışıyor → http://localhost:5173%RESET%

:: ============================================================
::  Tarayıcı aç
:: ============================================================
echo.
timeout /t 1 /nobreak >nul
start "" "http://localhost:5173"

:: ============================================================
::  Başarı ekranı
:: ============================================================
echo.
echo %GRAY%  ─────────────────────────────────────────────────────────────────────────────────%RESET%
echo.
echo %GREEN%  ✓ KaloriSpor başarıyla başlatıldı!%RESET%
echo.
echo %WHITE%  📌 Adresler:%RESET%
echo %CYAN%     • Web Arayüzü  : http://localhost:5173%RESET%
echo %CYAN%     • API Sunucusu : http://localhost:8000%RESET%
echo %CYAN%     • API Docs     : http://localhost:8000/docs%RESET%
echo.
echo %WHITE%  💡 İpuçları:%RESET%
echo %GRAY%     • Kapatmak için: Fitness-App-Durdur.bat çalıştırın%RESET%
echo %GRAY%     • Backend ve Frontend pencereleri açık kalmalı%RESET%
echo %GRAY%     • Bu pencereyi kapatabilirsiniz%RESET%
echo.
echo %GRAY%  ─────────────────────────────────────────────────────────────────────────────────%RESET%
echo.
echo %YELLOW%  Bu pencereyi kapatmak için bir tuşa basın...%RESET%
pause >nul
