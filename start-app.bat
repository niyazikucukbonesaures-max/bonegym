@echo off
chcp 65001 >nul
title Fitness Kalori Takip - Başlatma
color 0A

echo.
echo ╔════════════════════════════════════════╗
echo ║  Fitness Kalori Takip Uygulaması      ║
echo ║  Optimize Edilmiş Başlatma Scripti    ║
echo ╚════════════════════════════════════════╝
echo.

REM Yol kontrolü
if not exist "backend\" (
    echo [HATA] Backend klasörü bulunamadı!
    pause
    exit /b 1
)

if not exist "frontend\" (
    echo [HATA] Frontend klasörü bulunamadı!
    pause
    exit /b 1
)

REM Python kontrolü
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python yüklü değil!
    echo Lütfen Python'u yükleyin: https://www.python.org/
    pause
    exit /b 1
)

REM Node.js kontrolü
node --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Node.js yüklü değil!
    echo Lütfen Node.js'i yükleyin: https://nodejs.org/
    pause
    exit /b 1
)

echo [✓] Gereksinimler kontrol edildi
echo.
echo ┌────────────────────────────────────────┐
echo │ Backend ve Frontend başlatılıyor...   │
echo └────────────────────────────────────────┘
echo.

REM Backend'i başlat
echo [1/3] Backend sunucusu başlatılıyor...
start "Backend Server - Fitness App" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Backend'in başlaması için bekle
echo [2/3] Backend hazırlanıyor (5 saniye)...
timeout /t 5 /nobreak >nul

REM Frontend'i başlat
echo [3/3] Frontend sunucusu başlatılıyor...
start "Frontend Server - Fitness App" cmd /k "cd frontend && npm run dev"

REM Frontend'in başlaması için bekle
echo       Frontend hazırlanıyor (5 saniye)...
timeout /t 5 /nobreak >nul

echo.
echo ╔════════════════════════════════════════╗
echo ║  ✓ Sunucular başarıyla başlatıldı!    ║
echo ╚════════════════════════════════════════╝
echo.
echo ┌────────────────────────────────────────┐
echo │ Erişim Adresleri:                      │
echo ├────────────────────────────────────────┤
echo │ Backend:  http://localhost:8000        │
echo │ Frontend: http://localhost:5173        │
echo │ API Docs: http://localhost:8000/docs   │
echo └────────────────────────────────────────┘
echo.
echo [INFO] Tarayıcınız otomatik açılacak...
echo.

REM Tarayıcıyı aç
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo.
echo ┌────────────────────────────────────────┐
echo │ Uygulamayı kapatmak için:              │
echo │ • stop-app.bat dosyasını çalıştırın    │
echo │ • Fitness-App-Durdur.vbs çalıştırın    │
echo └────────────────────────────────────────┘
echo.
echo [ENTER] tuşuna basarak bu pencereyi kapatabilirsiniz
echo (Sunucular arka planda çalışmaya devam edecek)
echo.
pause >nul
