# Kreatin Router'ı
# GET  /status  → Bugünkü durum
# POST /log     → Doz kaydet
# GET  /history → Geçmiş (days=30)

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.creatine_tracker import CreatineTracker
from app.database import get_db
from app.schemas import CreatineDoseCreate, CreatineDoseSchema, TodayCreatineStatus

router = APIRouter()
_tracker = CreatineTracker()


@router.get("/status", response_model=TodayCreatineStatus)
async def get_today_status(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
) -> TodayCreatineStatus:
    """Bugünkü kreatin alım durumunu döndürür."""
    return await _tracker.get_today_status(db, user_id)


@router.post("/log", response_model=CreatineDoseSchema, status_code=201)
async def log_dose(
    dose: CreatineDoseCreate,
    db: AsyncSession = Depends(get_db),
) -> CreatineDoseSchema:
    """Yeni bir kreatin dozu kaydeder."""
    return await _tracker.log_dose(db, dose)


@router.delete("/{dose_id}", status_code=204)
async def delete_dose(
    dose_id: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Bir kreatin dozunu siler."""
    success = await _tracker.delete_dose(db, dose_id, user_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Doz bulunamadı")


@router.get("/history", response_model=List[CreatineDoseSchema])
async def get_history(
    user_id: int = 1,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> List[CreatineDoseSchema]:
    """Son N günün kreatin doz geçmişini döndürür."""
    return await _tracker.get_history(db, user_id, days)
