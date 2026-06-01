# Fitness ve Kalori Takip Uygulaması - Pano Servisi
# Tek API çağrısıyla tüm pano verilerini toplar ve döndürür.

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calorie_engine import CalorieEngine
from app.creatine_tracker import CreatineTracker
from app.measurement_tracker import MeasurementTracker
from app.water_tracker import WaterTracker
from app.achievement_system import AchievementSystem
from app.models import Measurement, UserProfile
from app.schemas import (
    DashboardSnapshotSchema,
    MeasurementSchema,
    UserProfileWithStats,
    WeeklyWorkoutStats,
)
from app.workout_tracker import WorkoutTracker


class DashboardService:
    """Tüm pano verilerini tek seferde toplayan servis."""

    def __init__(self) -> None:
        self._calorie_engine = CalorieEngine()
        self._creatine_tracker = CreatineTracker()
        self._measurement_tracker = MeasurementTracker()
        self._workout_tracker = WorkoutTracker()
        self._water_tracker = WaterTracker()
        self._achievement_system = AchievementSystem()

    async def get_dashboard_data(
        self, db: AsyncSession, user_id: int = 1
    ) -> DashboardSnapshotSchema:
        """Tek API çağrısıyla tüm pano verilerini toplar.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si

        Returns:
            DashboardSnapshotSchema: Tüm pano verileri
        """
        today = date.today()
        notifications: list[str] = []

        # 1. Günlük kalori özeti
        daily_summary = await self._calorie_engine.get_daily_total(db, user_id, today)

        # 2. Kullanıcı profili + hesaplanan BMR/TDEE/recommended_calories
        profile_with_stats = await self._get_profile_with_stats(db)

        # 3. Kreatin durumu
        creatine_status = await self._creatine_tracker.get_today_status(db, user_id)

        # 4. Haftalık antrenman istatistikleri
        weekly_stats_raw = await self._workout_tracker.get_weekly_stats(db, user_id)
        weekly_workout_goal = profile_with_stats.weekly_workout_goal if profile_with_stats else 4
        weekly_workout_stats = WeeklyWorkoutStats(
            completed=weekly_stats_raw.completed_count,
            goal=weekly_workout_goal,
            percentage=(
                round(weekly_stats_raw.completed_count / weekly_workout_goal * 100, 1)
                if weekly_workout_goal > 0
                else 0.0
            ),
            total_duration_minutes=weekly_stats_raw.total_duration_minutes,
        )

        # 5. Son 7 günlük kilo ölçümleri
        weight_trend = await self._get_weight_trend(db, user_id, days=7)

        # 6. Günlük su tüketim özeti
        daily_water_summary = await self._water_tracker.get_daily_water_summary(db, user_id, today)

        # 7. Yeni kazanılan rozetler (is_new=True olanlar)
        new_achievements = []
        try:
            user_achievements = await self._achievement_system.get_user_achievements(db, user_id)
            new_achievements = [ua for ua in user_achievements if ua.is_new]
        except Exception:
            pass  # Rozet sistemi hatası dashboard'ı bozmasın

        # 8. Rozet ilerleme durumu
        achievement_progress = []
        try:
            achievement_progress = await self._achievement_system.get_achievement_progress(db, user_id)
        except Exception:
            pass  # Rozet sistemi hatası dashboard'ı bozmasın

        # 9. Bildirimleri tüm servislerden topla
        workout_notifications = await self._workout_tracker.get_notifications(db, user_id)
        creatine_notifications = await self._creatine_tracker.get_notifications(db, user_id)
        measurement_notifications = await self._measurement_tracker.get_notifications(db, user_id)

        notifications.extend(workout_notifications)
        notifications.extend(creatine_notifications)
        notifications.extend(measurement_notifications)

        return DashboardSnapshotSchema(
            daily_summary=daily_summary,
            profile=profile_with_stats,
            creatine_status=creatine_status,
            weekly_workout_stats=weekly_workout_stats,
            weight_trend=weight_trend,
            daily_water_summary=daily_water_summary,
            new_achievements=new_achievements,
            achievement_progress=achievement_progress,
            notifications=notifications,
        )

    async def _get_profile_with_stats(
        self, db: AsyncSession
    ) -> Optional[UserProfileWithStats]:
        """Kullanıcı profilini BMR/TDEE/recommended_calories ile birlikte döndürür."""
        stmt = select(UserProfile).limit(1)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if profile is None:
            return None

        bmr = CalorieEngine.calculate_bmr(
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            age=profile.age,
            gender=profile.gender,
        )
        tdee = CalorieEngine.calculate_tdee(bmr, profile.activity_level)
        recommended = CalorieEngine.get_recommended_calories(tdee, profile.goal)

        return UserProfileWithStats(
            id=profile.id,
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            age=profile.age,
            gender=profile.gender,
            activity_level=profile.activity_level,
            goal=profile.goal,
            weekly_workout_goal=profile.weekly_workout_goal,
            daily_calorie_target=profile.daily_calorie_target,
            updated_at=profile.updated_at,
            bmr=round(bmr, 2),
            tdee=round(tdee, 2),
            recommended_calories=round(recommended, 2),
        )

    async def _get_weight_trend(
        self, db: AsyncSession, user_id: int, days: int = 7
    ) -> list[MeasurementSchema]:
        """Son N günlük kilo ölçümlerini döndürür."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(Measurement)
            .where(
                Measurement.user_id == user_id,
                Measurement.measured_at >= cutoff,
                Measurement.weight_kg.isnot(None),
            )
            .order_by(Measurement.measured_at.desc())  # AZALAN - en yeni önce!
        )
        result = await db.execute(stmt)
        measurements = result.scalars().all()
        return [MeasurementSchema.model_validate(m) for m in measurements]
