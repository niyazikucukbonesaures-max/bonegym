# Fitness ve Kalori Takip Uygulaması - FastAPI Ana Uygulama
# Lifespan event ile DB başlatma ve scheduler yönetimi.

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import creatine, dashboard, export, foods, log, measurements, profile, workouts, notifications, auth, meal_plan, water, achievements, ai_assistant, crowdsource, ai_coach, sport_profiles, analytics, data_management
from app.scheduler import start_scheduler, stop_scheduler
from app.ai_service import ai_assistant_service
from app.error_handlers import register_exception_handlers, log_requests_middleware, logger
from app.security import security_headers_middleware, rate_limit_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Uygulama başlangıç ve kapanış işlemlerini yönetir."""
    # Başlangıç
    logger.info("🚀 Fitness App başlatılıyor...")
    await init_db()
    logger.info("✅ Veritabanı başlatıldı")
    start_scheduler()
    logger.info("✅ Scheduler başlatıldı")
    
    # AI asistanını başlat
    await ai_assistant_service.initialize()
    logger.info("✅ AI servisi başlatıldı")
    logger.info("🎯 Uygulama hazır!")

    yield

    # Kapanış
    logger.info("🛑 Uygulama kapatılıyor...")
    stop_scheduler()
    logger.info("✅ Uygulama kapatıldı")


app = FastAPI(
    title="Fitness ve Kalori Takip API",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------

register_exception_handlers(app)

# ---------------------------------------------------------------------------
# GZip Compression — büyük yanıtları sıkıştır, bant genişliği tasarrufu
# ---------------------------------------------------------------------------

from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------

import os


def build_cors_origins() -> list[str]:
    """CORS izin verilen origin listesini oluşturur.
    
    Geliştirme ortamı URL'leri her zaman dahil edilir.
    FRONTEND_URL env var tanımlıysa production URL'i de eklenir.
    """
    origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ]
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        origins.append(frontend_url)
    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=build_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Güvenlik ve logging middleware'leri
from starlette.middleware.base import BaseHTTPMiddleware
app.add_middleware(BaseHTTPMiddleware, dispatch=security_headers_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests_middleware)

# ---------------------------------------------------------------------------
# Router'lar
# ---------------------------------------------------------------------------

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(foods.router, prefix="/api/foods", tags=["foods"])
app.include_router(log.router, prefix="/api/log", tags=["log"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(workouts.router, prefix="/api/workouts", tags=["workouts"])
app.include_router(creatine.router, prefix="/api/creatine", tags=["creatine"])
app.include_router(measurements.router, prefix="/api/measurements", tags=["measurements"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(meal_plan.router, prefix="/api/meal-plan", tags=["meal-plan"])
app.include_router(water.router, prefix="/api", tags=["water"])
app.include_router(achievements.router, prefix="/api", tags=["achievements"])
app.include_router(ai_assistant.router, prefix="/api/ai-assistant", tags=["ai-assistant"])
app.include_router(ai_coach.router, prefix="/api/ai-coach", tags=["ai-coach"])
app.include_router(crowdsource.router, tags=["crowdsource"])

# Yeni gelişmiş API endpoint'leri
app.include_router(sport_profiles.router, prefix="/api/sport-profiles", tags=["sport-profiles"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(data_management.router, prefix="/api/data-management", tags=["data-management"])


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Uygulamanın çalışır durumda olduğunu doğrular."""
    return {"status": "ok"}
