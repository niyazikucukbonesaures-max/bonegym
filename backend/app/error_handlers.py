# Fitness ve Kalori Takip Uygulaması - Gelişmiş Hata Yönetimi
# Custom exception'lar, graceful degradation, retry mekanizması

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Any, Callable, Optional, Type
from functools import wraps

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Logging Konfigürasyonu
# ---------------------------------------------------------------------------

def setup_logging() -> logging.Logger:
    """Structured logging konfigürasyonu."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger = logging.getLogger("fitness_app")
    logger.setLevel(logging.INFO)
    
    return logger


logger = setup_logging()


# ---------------------------------------------------------------------------
# Custom Exception Sınıfları
# ---------------------------------------------------------------------------

class FitnessAppError(Exception):
    """Temel uygulama hatası."""
    def __init__(self, message: str, code: str = "GENERAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class ValidationError(FitnessAppError):
    """Veri doğrulama hatası."""
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message, code="VALIDATION_ERROR", status_code=400)


class NotFoundError(FitnessAppError):
    """Kayıt bulunamadı hatası."""
    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} bulunamadı" + (f": {resource_id}" if resource_id else "")
        super().__init__(message, code="NOT_FOUND", status_code=404)


class CalculationError(FitnessAppError):
    """Hesaplama hatası."""
    def __init__(self, message: str):
        super().__init__(message, code="CALCULATION_ERROR", status_code=422)


class DatabaseError(FitnessAppError):
    """Veritabanı hatası."""
    def __init__(self, message: str):
        super().__init__(message, code="DATABASE_ERROR", status_code=503)


class ExternalServiceError(FitnessAppError):
    """Harici servis hatası."""
    def __init__(self, service: str, message: str):
        super().__init__(f"{service}: {message}", code="EXTERNAL_SERVICE_ERROR", status_code=502)


class RateLimitError(FitnessAppError):
    """Rate limit hatası."""
    def __init__(self, message: str = "Çok fazla istek gönderildi"):
        super().__init__(message, code="RATE_LIMIT_ERROR", status_code=429)


# ---------------------------------------------------------------------------
# Retry Mekanizması
# ---------------------------------------------------------------------------

def with_retry(
    max_attempts: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Async fonksiyonlar için retry decorator."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {str(e)}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )
            
            raise last_exception
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Graceful Degradation
# ---------------------------------------------------------------------------

def with_fallback(fallback_value: Any = None, log_error: bool = True):
    """Hata durumunda fallback değer döndüren decorator."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.warning(
                        f"Graceful degradation in {func.__name__}: {str(e)}. "
                        f"Returning fallback: {fallback_value}"
                    )
                return fallback_value
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# FastAPI Exception Handlers
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """FastAPI uygulamasına exception handler'ları kaydet."""
    
    @app.exception_handler(FitnessAppError)
    async def fitness_app_error_handler(request: Request, exc: FitnessAppError):
        logger.error(f"FitnessAppError [{exc.code}]: {exc.message} | Path: {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "code": exc.code,
                "message": exc.message,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "code": "VALIDATION_ERROR",
                "message": exc.message,
                "field": exc.field,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning(f"ValueError: {str(exc)} | Path: {request.url.path}")
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "code": "INVALID_VALUE",
                "message": str(exc),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Beklenmedik hatalar için detaylı log
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {str(exc)} | "
            f"Path: {request.url.path} | "
            f"Traceback: {traceback.format_exc()}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Beklenmedik bir hata oluştu. Lütfen tekrar deneyin.",
                "timestamp": datetime.now().isoformat()
            }
        )


# ---------------------------------------------------------------------------
# Request Logging Middleware
# ---------------------------------------------------------------------------

async def log_requests_middleware(request: Request, call_next):
    """Her isteği logla ve performansı ölç."""
    start_time = datetime.now()
    
    # İsteği logla
    logger.info(f"→ {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Yanıt süresini hesapla
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Yavaş istekleri uyar — AI endpoint'leri için daha yüksek limit
        slow_limit = 10000 if "/ai-assistant" in request.url.path or "/ai-coach" in request.url.path else 2000
        if duration_ms > slow_limit:
            logger.warning(
                f"SLOW REQUEST: {request.method} {request.url.path} "
                f"took {duration_ms:.0f}ms (limit: {slow_limit}ms)"
            )
        else:
            logger.info(
                f"← {request.method} {request.url.path} "
                f"{response.status_code} ({duration_ms:.0f}ms)"
            )
        
        return response
        
    except Exception as e:
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(
            f"✗ {request.method} {request.url.path} "
            f"FAILED after {duration_ms:.0f}ms: {str(e)}"
        )
        raise
