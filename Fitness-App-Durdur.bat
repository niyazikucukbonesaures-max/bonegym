@echo off
chcp 65001 >nul
title KaloriSpor - Durdur

set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "CYAN=[96m"
set "WHITE=[97m"
set "GRAY=[90m"
set "RESET=[0m"

cls
echo.
echo %CYAN%  ╔══════════════════════════════════════════╗%RESET%
echo %CYAN%  ║     KaloriSpor - Uygulama Durdur        ║%RESET%
echo %CYAN%  ╚══════════════════════════════════════════╝%RESET%
echo.

set /p "ONAY=  Uygulamayı durdurmak istiyor musunuz? (E/H): "
if /i not "%ONAY%"=="E" (
    echo %YELLOW%  İptal edildi.%RESET%
    timeout /t 2 /nobreak >nul
    exit /b 0
)

echo.
echo %YELLOW%  Servisler kapatılıyor...%RESET%
echo.

:: ── Backend (uvicorn / python) ──────────────────────────────
echo %GRAY%  [1/3] Backend (uvicorn) kapatılıyor...%RESET%
set "BACKEND_KILLED=0"
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr /R ":8000 "') do (
    if not "%%p"=="" (
        taskkill /PID %%p /F >nul 2>&1
        set "BACKEND_KILLED=1"
    )
)
if "%BACKEND_KILLED%"=="1" (
    echo %GREEN%  ✓ Backend kapatıldı%RESET%
) else (
    echo %GRAY%  - Backend zaten kapalıydı%RESET%
)

:: ── Frontend (vite / node) ──────────────────────────────────
echo %GRAY%  [2/3] Frontend (vite) kapatılıyor...%RESET%
set "FRONTEND_KILLED=0"
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr /R ":5173 "') do (
    if not "%%p"=="" (
        taskkill /PID %%p /F >nul 2>&1
        set "FRONTEND_KILLED=1"
    )
)
if "%FRONTEND_KILLED%"=="1" (
    echo %GREEN%  ✓ Frontend kapatıldı%RESET%
) else (
    echo %GRAY%  - Frontend zaten kapalıydı%RESET%
)

:: ── Pencere başlıklarına göre CMD'leri kapat ───────────────
echo %GRAY%  [3/3] Açık terminal pencereleri kapatılıyor...%RESET%
taskkill /F /FI "WINDOWTITLE eq KaloriSpor-Backend" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq KaloriSpor-Frontend" >nul 2>&1

timeout /t 1 /nobreak >nul

echo.
echo %GREEN%  ✓ Tüm servisler kapatıldı.%RESET%
echo.
echo %YELLOW%  Bu pencereyi kapatmak için bir tuşa basın...%RESET%
pause >nul
