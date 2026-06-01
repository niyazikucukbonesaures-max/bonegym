# Başarı Rozetleri Router
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.achievement_system import AchievementSystem
from app.schemas import (
    AchievementSchema, UserAchievementSchema, 
    AchievementProgress, AchievementCreate
)

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get("/", response_model=List[AchievementSchema])
async def get_all_achievements(db: AsyncSession = Depends(get_db)):
    """Tüm mevcut başarı rozetlerini getirir."""
    try:
        from sqlalchemy import select
        from app.models import Achievement
        
        stmt = select(Achievement).order_by(Achievement.category, Achievement.points)
        result = await db.execute(stmt)
        achievements = result.scalars().all()
        
        return [AchievementSchema.model_validate(a) for a in achievements]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rozetler getirilirken hata oluştu: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=List[UserAchievementSchema])
async def get_user_achievements(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcının kazandığı rozetleri getirir."""
    try:
        return await AchievementSystem.get_user_achievements(db, user_id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Kullanıcı rozetleri getirilirken hata oluştu: {str(e)}"
        )


@router.get("/progress/{user_id}", response_model=List[AchievementProgress])
async def get_achievement_progress(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcının rozet ilerleme durumunu getirir."""
    try:
        return await AchievementSystem.get_achievement_progress(db, user_id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rozet ilerlemesi getirilirken hata oluştu: {str(e)}"
        )


@router.post("/mark-seen/{user_id}")
async def mark_achievements_as_seen(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcının yeni rozetlerini görüldü olarak işaretler."""
    try:
        await AchievementSystem.mark_achievements_as_seen(db, user_id)
        return {"message": "Rozetler görüldü olarak işaretlendi"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rozetler işaretlenirken hata oluştu: {str(e)}"
        )


@router.post("/check/{user_id}")
async def manually_check_achievements(
    user_id: int,
    activity_type: str = "manual",
    db: AsyncSession = Depends(get_db)
):
    """Manuel olarak rozet kontrolü yapar (test amaçlı)."""
    try:
        new_achievements = await AchievementSystem.check_and_award_achievements(
            db, user_id, activity_type
        )
        
        return {
            "message": f"{len(new_achievements)} yeni rozet kazanıldı",
            "new_achievements": new_achievements
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rozet kontrolü yapılırken hata oluştu: {str(e)}"
        )


@router.post("/initialize")
async def initialize_default_achievements(db: AsyncSession = Depends(get_db)):
    """Varsayılan rozetleri oluşturur (sadece admin için)."""
    try:
        await AchievementSystem.initialize_default_achievements(db)
        return {"message": "Varsayılan rozetler oluşturuldu"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Varsayılan rozetler oluşturulurken hata oluştu: {str(e)}"
        )


@router.get("/stats/{user_id}")
async def get_user_achievement_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcının rozet istatistiklerini getirir."""
    try:
        from sqlalchemy import select, func
        from app.models import Achievement, UserAchievement
        
        # Toplam rozet sayısı
        total_achievements = await db.scalar(select(func.count(Achievement.id)))
        
        # Kullanıcının kazandığı rozet sayısı
        earned_achievements = await db.scalar(
            select(func.count(UserAchievement.id)).where(
                UserAchievement.user_id == user_id
            )
        )
        
        # Toplam puan
        total_points_stmt = select(func.sum(Achievement.points)).select_from(
            UserAchievement.__table__.join(Achievement.__table__)
        ).where(UserAchievement.user_id == user_id)
        
        total_points = await db.scalar(total_points_stmt) or 0
        
        # Kategori bazlı istatistikler
        category_stats_stmt = select(
            Achievement.category,
            func.count(UserAchievement.id).label('earned'),
            func.sum(Achievement.points).label('points')
        ).select_from(
            Achievement.__table__.outerjoin(
                UserAchievement.__table__,
                (Achievement.id == UserAchievement.achievement_id) & 
                (UserAchievement.user_id == user_id)
            )
        ).group_by(Achievement.category)
        
        result = await db.execute(category_stats_stmt)
        category_stats = [
            {
                "category": row.category,
                "earned": row.earned or 0,
                "points": row.points or 0
            }
            for row in result
        ]
        
        return {
            "total_achievements": total_achievements or 0,
            "earned_achievements": earned_achievements or 0,
            "completion_percentage": round(
                (earned_achievements / total_achievements * 100) if total_achievements > 0 else 0, 1
            ),
            "total_points": int(total_points),
            "category_stats": category_stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rozet istatistikleri getirilirken hata oluştu: {str(e)}"
        )