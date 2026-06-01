# Fitness ve Kalori Takip Uygulaması - Güvenlik Sistemi
# Input validation, rate limiting, güvenli header'lar

import re
import time
import hashlib
from typing import Optional
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Input Validation
# ---------------------------------------------------------------------------

class InputValidator:
    """Güvenli input doğrulama."""
    
    # SQL injection pattern'leri
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
    ]
    
    # XSS pattern'leri
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 500) -> str:
        """String değeri temizle ve doğrula."""
        if not isinstance(value, str):
            return str(value)
        
        # Uzunluk kontrolü
        if len(value) > max_length:
            value = value[:max_length]
        
        # Tehlikeli karakterleri temizle
        value = value.strip()
        
        return value
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """SQL injection kontrolü."""
        value_upper = value.upper()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_xss(cls, value: str) -> bool:
        """XSS kontrolü."""
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Email formatı doğrulama."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @classmethod
    def validate_numeric_range(cls, value: float, min_val: float, max_val: float) -> bool:
        """Sayısal aralık doğrulama."""
        return min_val <= value <= max_val


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------

class RateLimiter:
    """Basit in-memory rate limiter."""
    
    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)
    
    def is_allowed(
        self, 
        key: str, 
        max_requests: int = 100, 
        window_seconds: int = 60
    ) -> bool:
        """İstek izni kontrolü."""
        now = time.time()
        window_start = now - window_seconds
        
        # Eski istekleri temizle
        self._requests[key] = [
            req_time for req_time in self._requests[key] 
            if req_time > window_start
        ]
        
        # Limit kontrolü
        if len(self._requests[key]) >= max_requests:
            return False
        
        # İsteği kaydet
        self._requests[key].append(now)
        return True
    
    def get_remaining(self, key: str, max_requests: int = 100, window_seconds: int = 60) -> int:
        """Kalan istek sayısı."""
        now = time.time()
        window_start = now - window_seconds
        recent_requests = [
            req_time for req_time in self._requests.get(key, [])
            if req_time > window_start
        ]
        return max(0, max_requests - len(recent_requests))


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------

async def security_headers_middleware(request: Request, call_next):
    """Güvenlik header'larını ekle."""
    response = await call_next(request)
    
    # Güvenlik header'ları
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Cache kontrolü (API yanıtları için)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    
    return response


# ---------------------------------------------------------------------------
# Rate Limiting Middleware
# ---------------------------------------------------------------------------

rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware — endpoint türüne göre farklı limitler."""
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # Auth endpoint'leri — en sıkı (brute force koruması)
    if "/auth/login" in path or "/auth/register" in path:
        if not rate_limiter.is_allowed(f"auth:{client_ip}", max_requests=10, window_seconds=60):
            return JSONResponse(status_code=429, content={
                "error": True, "code": "RATE_LIMIT_EXCEEDED",
                "message": "Çok fazla giriş denemesi. 1 dakika bekleyin.",
                "retry_after": 60
            })

    # AI endpoint'leri — orta sıkı (Gemini kota koruması)
    elif "/ai-assistant" in path or "/ai-coach" in path:
        if not rate_limiter.is_allowed(f"ai:{client_ip}", max_requests=20, window_seconds=60):
            return JSONResponse(status_code=429, content={
                "error": True, "code": "RATE_LIMIT_EXCEEDED",
                "message": "AI servisi için çok fazla istek. 1 dakika bekleyin.",
                "retry_after": 60
            })

    # Genel API — geniş limit (normal kullanım)
    else:
        if not rate_limiter.is_allowed(f"api:{client_ip}", max_requests=300, window_seconds=60):
            return JSONResponse(status_code=429, content={
                "error": True, "code": "RATE_LIMIT_EXCEEDED",
                "message": "Çok fazla istek. Lütfen bekleyin.",
                "retry_after": 60
            })

    return await call_next(request)


# ---------------------------------------------------------------------------
# Global Instances
# ---------------------------------------------------------------------------

input_validator = InputValidator()
