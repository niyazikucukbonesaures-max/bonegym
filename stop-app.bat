@echo off
chcp 65001 >nul
title Fitness Kalori Takip - Durdurma
color 0C

echo.
echo ╔════════════════════════════════════════╗
echo ║  Fitness Kalori Takip Uygulaması      ║
echo ║  Optimize Edilmiş Durdurma Scripti    ║
echo ╚════════════════════════════════════════╝
echo.

echo [!] Uygulama kapatılıyor...
echo.

REM Backend process'lerini say
set /a backend_count=0
for /f %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH 2^>nul ^| find /c "python.exe"') do set /a backend_count=%%i

REM Frontend process'lerini say
set /a frontend_count=0
for /f %%i in ('tasklist /FI "IMAGENAME eq node.exe" /FO CSV /NH 2^>nul ^| find /c "node.exe"') do set /a frontend_count=%%i

echo [1/4] Backend process'leri kapatılıyor...
REM Python uvicorn process'lerini kapat
taskkill /F /FI "WINDOWTITLE eq Backend Server*" >nul 2>&1
taskkill /F /FI "IMAGENAME eq python.exe" /FI "COMMANDLINE eq *uvicorn*" >nul 2>&1
echo       ✓ Backend kapatıldı (%backend_count% process)

echo [2/4] Frontend process'leri kapatılıyor...
REM Node.js process'lerini kapat
taskkill /F /FI "WINDOWTITLE eq Frontend Server*" >nul 2>&1
taskkill /F /FI "IMAGENAME eq node.exe" /FI "COMMANDLINE eq *vite*" >nul 2>&1
taskkill /F /FI "IMAGENAME eq node.exe" /FI "COMMANDLINE eq *npm*" >nul 2>&1
echo       ✓ Frontend kapatıldı (%frontend_count% process)

echo [3/4] CMD pencerelerini temizleniyor...
timeout /t 1 /nobreak >nul
echo       ✓ Temizlendi

echo [4/4] Port'lar kontrol ediliyor...
REM Port 8000 ve 5173'ü kontrol et
netstat -ano | findstr ":8000" >nul 2>&1
if errorlevel 1 (
    echo       ✓ Port 8000 serbest
) else (
    echo       ⚠ Port 8000 hala kullanımda
)

netstat -ano | findstr ":5173" >nul 2>&1
if errorlevel 1 (
    echo       ✓ Port 5173 serbest
) else (
    echo       ⚠ Port 5173 hala kullanımda
)

echo.
echo ╔════════════════════════════════════════╗
echo ║  ✓ Uygulama başarıyla kapatıldı!       ║
echo ╚════════════════════════════════════════╝
echo.
echo ┌────────────────────────────────────────┐
echo │ İstatistikler:                         │
echo ├────────────────────────────────────────┤
echo │ Backend:  %backend_count% process kapatıldı          │
echo │ Frontend: %frontend_count% process kapatıldı          │
echo └────────────────────────────────────────┘
echo.
echo [ENTER] tuşuna basarak çıkabilirsiniz
pause >nul
