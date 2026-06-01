# Fitness ve Kalori Takip Uygulaması - Hafif In-Memory Cache Sistemi
# Redis gerektirmeden, TTL destekli, thread-safe cache

import asyncio
import time
import json
import hashlib
from typing import Any, Optional, Callable
from dataclasses import dataclass, field
from functools import wraps


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------

@dataclass
class CacheEntry:
    """Cache girişi."""
    value: Any
    expires_at: float  # Unix timestamp
    created_at: float = field(default_factory=time.time)
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def ttl_remaining(self) -> float:
        return max(0, self.expires_at - time.time())


@dataclass
class CacheStats:
    """Cache istatistikleri."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_entries: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


# ---------------------------------------------------------------------------
# Cache Sistemi
# ---------------------------------------------------------------------------

class InMemoryCache:
    """Thread-safe, TTL destekli in-memory cache."""

    # Varsayılan TTL değerleri (saniye) — mobil app için optimize
    TTL_SHORT = 60          # 1 dakika - sık değişen veriler (su, kalori)
    TTL_MEDIUM = 300        # 5 dakika - dashboard, profil
    TTL_LONG = 3600         # 1 saat - ölçüm geçmişi
    TTL_VERY_LONG = 86400   # 24 saat - besin aramaları, statik veriler

    # Maksimum cache boyutu — 10K kullanıcı için artırıldı
    MAX_ENTRIES = 5000

    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}
        self._stats = CacheStats()
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Temel Operasyonlar
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Optional[Any]:
        """Cache'den değer al."""
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats.misses += 1
                return None

            if entry.is_expired:
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                return None

            entry.hit_count += 1
            self._stats.hits += 1
            return entry.value

    async def set(self, key: str, value: Any, ttl: int = TTL_MEDIUM) -> None:
        """Cache'e değer yaz."""
        async with self._lock:
            # Maksimum boyut kontrolü
            if len(self._cache) >= self.MAX_ENTRIES:
                await self._evict_expired()

                # Hâlâ doluysa en eski girişi sil
                if len(self._cache) >= self.MAX_ENTRIES:
                    oldest_key = min(
                        self._cache.keys(),
                        key=lambda k: self._cache[k].created_at
                    )
                    del self._cache[oldest_key]
                    self._stats.evictions += 1

            self._cache[key] = CacheEntry(
                value=value,
                expires_at=time.time() + ttl
            )
            self._stats.total_entries = len(self._cache)

    async def delete(self, key: str) -> bool:
        """Cache'den değer sil."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.total_entries = len(self._cache)
                return True
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Pattern'e uyan tüm anahtarları sil."""
        async with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
            self._stats.total_entries = len(self._cache)
            return len(keys_to_delete)

    async def clear(self) -> None:
        """Tüm cache'i temizle."""
        async with self._lock:
            self._cache.clear()
            self._stats.total_entries = 0

    async def exists(self, key: str) -> bool:
        """Anahtar var mı ve geçerli mi?"""
        value = await self.get(key)
        return value is not None

    # ------------------------------------------------------------------
    # Yardımcı Metodlar
    # ------------------------------------------------------------------

    async def _evict_expired(self) -> int:
        """Süresi dolmuş girişleri temizle."""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired]
        for key in expired_keys:
            del self._cache[key]
            self._stats.evictions += 1
        return len(expired_keys)

    async def get_stats(self) -> dict:
        """Cache istatistiklerini döndür."""
        async with self._lock:
            await self._evict_expired()
            return {
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "hit_rate": round(self._stats.hit_rate, 2),
                "evictions": self._stats.evictions,
                "total_entries": len(self._cache),
                "max_entries": self.MAX_ENTRIES,
            }

    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """Cache anahtarı oluştur."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Cache Decorator
# ---------------------------------------------------------------------------

def cached(ttl: int = InMemoryCache.TTL_MEDIUM, key_prefix: str = ""):
    """Async fonksiyonlar için cache decorator."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Cache anahtarı oluştur
            cache_key = f"{key_prefix}:{func.__name__}:{InMemoryCache.make_key(*args, **kwargs)}"

            # Cache'den kontrol et
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Fonksiyonu çalıştır
            result = await func(*args, **kwargs)

            # Sonucu cache'e yaz
            if result is not None:
                await cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Cache Invalidation Helpers
# ---------------------------------------------------------------------------

async def invalidate_user_cache(user_id: int) -> None:
    """Belirli bir kullanıcının tüm cache'ini temizle."""
    await cache.delete_pattern(f"user:{user_id}")


async def invalidate_measurements_cache(user_id: int) -> None:
    """Ölçüm cache'ini temizle."""
    await cache.delete_pattern(f"measurements:{user_id}")
    await cache.delete_pattern(f"trend:{user_id}")
    await cache.delete_pattern(f"body_metrics:{user_id}")


async def invalidate_food_log_cache(user_id: int) -> None:
    """Kalori günlüğü cache'ini temizle."""
    await cache.delete_pattern(f"food_log:{user_id}")
    await cache.delete_pattern(f"dashboard:{user_id}")
    # Dashboard'u da temizle — kalori değişti
    await cache.delete(f"dashboard:{user_id}")


# ---------------------------------------------------------------------------
# Global Cache Instance
# ---------------------------------------------------------------------------

# Singleton instance
cache = InMemoryCache()
