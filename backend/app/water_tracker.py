# Su Takibi Servisi
# Kullanıcının günlük su tüketimini takip eder

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WaterLog, UserProfile
from app.schemas import WaterLogCreate, WaterLogSchema, DailyWaterSummary


class WaterTracker:
    """Su takibi servisi."""
    
    @staticmethod
    async def add_water_log(
        db: AsyncSession, 
        water_data: WaterLogCreate
    ) -> WaterLogSchema:
        """Yeni su kaydı ekler."""
        
        water_log = WaterLog(
            user_id=water_data.user_id,
            amount_ml=water_data.amount_ml
        )
        
        db.add(water_log)
        await db.commit()
        await db.refresh(water_log)
        
        return WaterLogSchema.model_validate(water_log)
    
    @staticmethod
    async def get_daily_water_summary(
        db: AsyncSession, 
        user_id: int, 
        target_date: Optional[date] = None
    ) -> DailyWaterSummary:
        """Belirtilen gün için su tüketim özetini getirir."""
        
        if target_date is None:
            target_date = date.today()
        
        # Günün başlangıcı ve bitişi (UTC timezone-aware)
        start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Günlük su kayıtlarını getir
        stmt = select(WaterLog).where(
            and_(
                WaterLog.user_id == user_id,
                WaterLog.logged_at >= start_of_day,
                WaterLog.logged_at <= end_of_day
            )
        ).order_by(WaterLog.logged_at.desc())
        
        result = await db.execute(stmt)
        water_logs = result.scalars().all()
        
        # Toplam su miktarını hesapla
        total_ml = sum(log.amount_ml for log in water_logs)
        
        # Günlük su hedefini hesapla (kilo bazlı: 35ml x kilo)
        goal_ml = await WaterTracker._calculate_daily_water_goal(db, user_id)
        
        # Yüzdeyi hesapla
        percentage = min((total_ml / goal_ml * 100) if goal_ml > 0 else 0, 100)
        
        # Schema'ya dönüştür
        entries = [WaterLogSchema.model_validate(log) for log in water_logs]
        
        return DailyWaterSummary(
            date=target_date.isoformat(),
            total_ml=total_ml,
            goal_ml=goal_ml,
            percentage=round(percentage, 1),
            entries=entries
        )
    
    @staticmethod
    async def get_water_logs_by_date_range(
        db: AsyncSession,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[WaterLogSchema]:
        """Belirtilen tarih aralığındaki su kayıtlarını getirir."""
        
        start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        stmt = select(WaterLog).where(
            and_(
                WaterLog.user_id == user_id,
                WaterLog.logged_at >= start_datetime,
                WaterLog.logged_at <= end_datetime
            )
        ).order_by(WaterLog.logged_at.desc())
        
        result = await db.execute(stmt)
        water_logs = result.scalars().all()
        
        return [WaterLogSchema.model_validate(log) for log in water_logs]
    
    @staticmethod
    async def delete_water_log(
        db: AsyncSession,
        user_id: int,
        log_id: int
    ) -> bool:
        """Su kaydını siler."""
        
        stmt = select(WaterLog).where(
            and_(
                WaterLog.id == log_id,
                WaterLog.user_id == user_id
            )
        )
        
        result = await db.execute(stmt)
        water_log = result.scalar_one_or_none()
        
        if not water_log:
            return False
        
        await db.delete(water_log)
        await db.commit()
        return True
    
    @staticmethod
    async def get_weekly_water_stats(
        db: AsyncSession,
        user_id: int
    ) -> dict:
        """Son 7 günün su tüketim istatistiklerini getirir."""
        
        end_date = date.today()
        start_date = end_date - timedelta(days=6)  # Son 7 gün
        
        daily_stats = []
        total_days_goal_met = 0
        
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            daily_summary = await WaterTracker.get_daily_water_summary(
                db, user_id, current_date
            )
            
            daily_stats.append({
                "date": current_date.isoformat(),
                "total_ml": daily_summary.total_ml,
                "goal_ml": daily_summary.goal_ml,
                "percentage": daily_summary.percentage,
                "goal_met": daily_summary.percentage >= 100
            })
            
            if daily_summary.percentage >= 100:
                total_days_goal_met += 1
        
        # Haftalık ortalama
        avg_daily_ml = sum(day["total_ml"] for day in daily_stats) / 7
        avg_goal_percentage = sum(day["percentage"] for day in daily_stats) / 7
        
        return {
            "daily_stats": daily_stats,
            "weekly_average_ml": round(avg_daily_ml, 1),
            "weekly_average_percentage": round(avg_goal_percentage, 1),
            "days_goal_met": total_days_goal_met,
            "streak_days": await WaterTracker._calculate_water_streak(db, user_id)
        }
    
    @staticmethod
    async def _calculate_daily_water_goal(
        db: AsyncSession,
        user_id: int
    ) -> float:
        """Kullanıcının günlük su hedefini hesaplar (kilo bazlı)."""
        
        # Kullanıcı profilini getir
        stmt = select(UserProfile).limit(1)  # Şu an tek kullanıcı var
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            return 2000.0  # Varsayılan 2L
        
        # Kilo bazlı hesaplama: 35ml x kilo
        # Minimum 1.5L, maksimum 4L
        goal_ml = profile.weight_kg * 35
        return max(1500, min(goal_ml, 4000))
    
    @staticmethod
    async def _calculate_water_streak(
        db: AsyncSession,
        user_id: int
    ) -> int:
        """Kullanıcının su içme streak'ini hesaplar (kaç gün üst üste hedefi tuttu)."""
        
        current_date = date.today()
        streak_days = 0
        
        # Geriye doğru gün gün kontrol et
        for i in range(30):  # Maksimum 30 gün kontrol et
            check_date = current_date - timedelta(days=i)
            
            daily_summary = await WaterTracker.get_daily_water_summary(
                db, user_id, check_date
            )
            
            if daily_summary.percentage >= 100:
                streak_days += 1
            else:
                break  # Streak kırıldı
        
        return streak_days