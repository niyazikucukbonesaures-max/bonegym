# Su Takibi Router
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.water_tracker import WaterTracker
from app.achievement_system import AchievementSystem
from app.schemas import (
    WaterLogCreate, WaterLogSchema, DailyWaterSummary,
    UserAchievementSchema
)
from app.routers.auth import get_current_user
from app.schemas_auth import UserSchema

router = APIRouter(prefix="/water", tags=["water"])


def _uid(current_user: UserSchema | None, fallback: int = 1) -> int:
    return current_user.id if current_user else fallback


@router.post("/log", response_model=WaterLogSchema)
async def add_water_log(
    water_data: WaterLogCreate,
    db: AsyncSession = Depends(get_db)
):
    """Yeni su kaydı ekler."""
    try:
        # Su kaydını ekle
        water_log = await WaterTracker.add_water_log(db, water_data)
        
        # Başarı rozetlerini kontrol et
        new_achievements = await AchievementSystem.check_and_award_achievements(
            db, water_data.user_id, "water_log", {"amount_ml": water_data.amount_ml}
        )
        
        # Yeni rozetler varsa response'a ekleyebiliriz (şimdilik sadece log döndürüyoruz)
        return water_log
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Su kaydı eklenirken hata oluştu: {str(e)}"
        )


@router.get("/daily-summary", response_model=DailyWaterSummary)
async def get_daily_water_summary(
    target_date: Optional[str] = None,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    """Günlük su tüketim özetini getirir."""
    uid = _uid(current_user, user_id)
    try:
        # Tarih parse et
        parsed_date = None
        if target_date:
            try:
                parsed_date = date.fromisoformat(target_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Geçersiz tarih formatı. YYYY-MM-DD formatında olmalı."
                )
        
        return await WaterTracker.get_daily_water_summary(db, uid, parsed_date)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Su özeti getirilirken hata oluştu: {str(e)}"
        )


@router.get("/logs", response_model=List[WaterLogSchema])
async def get_water_logs(
    user_id: int = 1,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Belirtilen tarih aralığındaki su kayıtlarını getirir."""
    try:
        # Varsayılan tarih aralığı (son 7 gün)
        if not start_date or not end_date:
            end = date.today()
            start = end.replace(day=1)  # Bu ayın başı
        else:
            try:
                start = date.fromisoformat(start_date)
                end = date.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Geçersiz tarih formatı. YYYY-MM-DD formatında olmalı."
                )
        
        return await WaterTracker.get_water_logs_by_date_range(db, user_id, start, end)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Su kayıtları getirilirken hata oluştu: {str(e)}"
        )


@router.delete("/log/{log_id}")
async def delete_water_log(
    log_id: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """Su kaydını siler."""
    try:
        success = await WaterTracker.delete_water_log(db, user_id, log_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Su kaydı bulunamadı"
            )
        
        return {"message": "Su kaydı başarıyla silindi"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Su kaydı silinirken hata oluştu: {str(e)}"
        )


@router.get("/weekly-stats")
async def get_weekly_water_stats(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """Son 7 günün su tüketim istatistiklerini getirir."""
    try:
        return await WaterTracker.get_weekly_water_stats(db, user_id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Su istatistikleri getirilirken hata oluştu: {str(e)}"
        )


# Hızlı su ekleme endpoint'leri
@router.post("/quick-add/{amount_ml}", response_model=WaterLogSchema)
async def quick_add_water(
    amount_ml: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    """Hızlı su ekleme."""
    uid = _uid(current_user, user_id)
    if amount_ml <= 0 or amount_ml > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz miktar. 1-5000ml arasında olmalı."
        )
    
    water_data = WaterLogCreate(
        user_id=uid,
        amount_ml=float(amount_ml)
    )
    
    return await add_water_log(water_data, db)