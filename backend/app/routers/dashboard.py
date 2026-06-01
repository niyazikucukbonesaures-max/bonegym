# Pano Router'ı
# GET / → Pano verisi

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard_service import DashboardService
from app.database import get_db
from app.schemas import DashboardSnapshotSchema
from app.cache import cache, InMemoryCache
from app.routers.auth import get_current_user
from app.schemas_auth import UserSchema

router = APIRouter()
_service = DashboardService()


@router.get("/", response_model=DashboardSnapshotSchema)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
) -> DashboardSnapshotSchema:
    """Tek API çağrısıyla tüm pano verilerini döndürür."""
    user_id = current_user.id if current_user else 1

    # Cache kontrolü — 30 saniye TTL
    cache_key = f"dashboard:{user_id}"
    cached_data = await cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    result = await _service.get_dashboard_data(db, user_id)

    # 30 saniye cache
    await cache.set(cache_key, result, ttl=30)

    return result


@router.get("/cache-stats")
async def get_cache_stats() -> dict:
    """Cache istatistiklerini döndürür (debug için)."""
    return await cache.get_stats()


@router.post("/cache-clear")
async def clear_cache(
    current_user: UserSchema = Depends(get_current_user),
) -> dict:
    """Kullanıcı cache'ini temizler."""
    user_id = current_user.id if current_user else 1
    deleted = await cache.delete_pattern(f"dashboard:{user_id}")
    return {"message": "Cache temizlendi", "deleted_entries": deleted}
