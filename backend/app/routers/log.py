# Kalori Günlüğü Router'ı
# GET  /{date}       → Günlük kalori günlüğü (YYYY-MM-DD)
# POST /             → Yeni giriş ekle
# DELETE /{entry_id} → Giriş sil

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.calorie_engine import CalorieEngine
from app.achievement_system import AchievementSystem
from app.database import get_db
from app.schemas import DailySummary, FoodLogCreate, FoodLogEntrySchema
from app.cache import cache, invalidate_food_log_cache
from app.routers.auth import get_current_user
from app.schemas_auth import UserSchema

router = APIRouter()
_engine = CalorieEngine()


@router.get("/{log_date}", response_model=DailySummary)
async def get_daily_log(
    log_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
) -> DailySummary:
    """Belirli bir tarih için günlük kalori günlüğünü döndürür."""
    user_id = current_user.id if current_user else 1
    cache_key = f"food_log:{user_id}:{log_date}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    result = await _engine.get_daily_total(db, user_id, log_date)
    await cache.set(cache_key, result, ttl=30)  # 30 saniye
    return result


@router.post("/", response_model=FoodLogEntrySchema, status_code=201)
async def add_log_entry(
    entry: FoodLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
) -> FoodLogEntrySchema:
    """Kalori günlüğüne yeni bir giriş ekler."""
    # Auth varsa token'dan user_id al, yoksa entry'deki user_id'yi kullan
    if current_user:
        entry.user_id = current_user.id
    try:
        # 1. Yemek kaydını ekle
        log = await _engine.add_food_log(db, entry)
        
        # 2. Cache'i temizle
        await invalidate_food_log_cache(entry.user_id)
        
        # 3. Başarı rozetlerini kontrol et
        try:
            await AchievementSystem.check_and_award_achievements(
                db, entry.user_id, "food_log", {
                    "food_name": entry.food_name,
                    "grams": entry.grams,
                    "meal_type": entry.meal_type
                }
            )
        except Exception:
            # Rozet sistemi hatası yemek kaydını bozmasın
            pass
        
        return FoodLogEntrySchema.model_validate(log)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{entry_id}", status_code=204)
async def delete_log_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
) -> None:
    """Kalori günlüğünden bir girişi siler."""
    user_id = current_user.id if current_user else 1
    deleted = await _engine.delete_food_log(db, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Giriş bulunamadı.")
    
    # Cache'i temizle
    await invalidate_food_log_cache(user_id)
