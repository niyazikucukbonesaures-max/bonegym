# Başarı Rozeti Sistemi
# Kullanıcı aktivitelerine göre otomatik rozet verir

from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Achievement, UserAchievement, FoodLog, WaterLog, 
    WorkoutLog, CreatineDose, UserProfile
)
from app.schemas import (
    AchievementSchema, UserAchievementSchema, 
    AchievementProgress, AchievementCreate
)


class AchievementSystem:
    """Başarı rozeti sistemi."""
    
    @staticmethod
    async def initialize_default_achievements(db: AsyncSession):
        """Varsayılan başarı rozetlerini oluşturur."""
        
        default_achievements = [
            # Yemek Takibi Rozetleri
            {
                "name": "İlk Adım",
                "description": "İlk yemeğini kaydet",
                "icon": "🎉",
                "category": "food",
                "condition_type": "count",
                "condition_value": 1,
                "points": 10
            },
            {
                "name": "Günlük Rutin",
                "description": "Bir günde 3 öğün kaydet",
                "icon": "🍽️",
                "category": "food",
                "condition_type": "daily_meals",
                "condition_value": 3,
                "points": 20
            },
            {
                "name": "Haftalık Kahraman",
                "description": "7 gün üst üste yemek kaydet",
                "icon": "🔥",
                "category": "food",
                "condition_type": "streak",
                "condition_value": 7,
                "points": 50
            },
            {
                "name": "Aylık Şampiyon",
                "description": "30 gün üst üste yemek kaydet",
                "icon": "👑",
                "category": "food",
                "condition_type": "streak",
                "condition_value": 30,
                "points": 100
            },
            {
                "name": "Yemek Uzmanı",
                "description": "100 farklı yemek kaydet",
                "icon": "🧑‍🍳",
                "category": "food",
                "condition_type": "unique_foods",
                "condition_value": 100,
                "points": 75
            },
            
            # Su Takibi Rozetleri
            {
                "name": "İlk Yudum",
                "description": "İlk su kaydını yap",
                "icon": "💧",
                "category": "water",
                "condition_type": "count",
                "condition_value": 1,
                "points": 10
            },
            {
                "name": "Hidrasyon Kahramanı",
                "description": "Günlük su hedefini tut",
                "icon": "🌊",
                "category": "water",
                "condition_type": "daily_goal",
                "condition_value": 1,
                "points": 20
            },
            {
                "name": "Su İçme Ustası",
                "description": "7 gün üst üste su hedefini tut",
                "icon": "🏆",
                "category": "water",
                "condition_type": "streak",
                "condition_value": 7,
                "points": 50
            },
            {
                "name": "Hidrasyon Efsanesi",
                "description": "30 gün üst üste su hedefini tut",
                "icon": "💎",
                "category": "water",
                "condition_type": "streak",
                "condition_value": 30,
                "points": 100
            },
            
            # Egzersiz Rozetleri
            {
                "name": "İlk Antrenman",
                "description": "İlk antrenmanını tamamla",
                "icon": "💪",
                "category": "workout",
                "condition_type": "count",
                "condition_value": 1,
                "points": 15
            },
            {
                "name": "Haftalık Savaşçı",
                "description": "Haftada 3 antrenman yap",
                "icon": "⚡",
                "category": "workout",
                "condition_type": "weekly_count",
                "condition_value": 3,
                "points": 30
            },
            {
                "name": "Fitness Canavarı",
                "description": "Haftada 5 antrenman yap",
                "icon": "🦾",
                "category": "workout",
                "condition_type": "weekly_count",
                "condition_value": 5,
                "points": 50
            },
            {
                "name": "Antrenman Ustası",
                "description": "50 antrenman tamamla",
                "icon": "🏅",
                "category": "workout",
                "condition_type": "count",
                "condition_value": 50,
                "points": 75
            },
            
            # Kreatin Rozetleri
            {
                "name": "Kreatin Başlangıcı",
                "description": "İlk kreatin dozunu al",
                "icon": "💊",
                "category": "creatine",
                "condition_type": "count",
                "condition_value": 1,
                "points": 10
            },
            {
                "name": "Kreatin Disiplini",
                "description": "7 gün üst üste kreatin al",
                "icon": "📅",
                "category": "creatine",
                "condition_type": "streak",
                "condition_value": 7,
                "points": 30
            },
            
            # Milestone Rozetleri
            {
                "name": "İlk Kilo",
                "description": "İlk kilonu ver",
                "icon": "📉",
                "category": "milestone",
                "condition_type": "weight_loss",
                "condition_value": 1,
                "points": 25
            },
            {
                "name": "5 Kilo Kahramanı",
                "description": "5 kilo ver",
                "icon": "🎯",
                "category": "milestone",
                "condition_type": "weight_loss",
                "condition_value": 5,
                "points": 50
            },
            {
                "name": "10 Kilo Efsanesi",
                "description": "10 kilo ver",
                "icon": "🌟",
                "category": "milestone",
                "condition_type": "weight_loss",
                "condition_value": 10,
                "points": 100
            },
            
            # Genel Rozetler
            {
                "name": "Mükemmeliyetçi",
                "description": "Bir günde tüm aktiviteleri kaydet (yemek, su, egzersiz)",
                "icon": "✨",
                "category": "streak",
                "condition_type": "perfect_day",
                "condition_value": 1,
                "points": 40
            },
            {
                "name": "Süper İnsan",
                "description": "7 gün üst üste mükemmel gün",
                "icon": "🦸",
                "category": "streak",
                "condition_type": "perfect_streak",
                "condition_value": 7,
                "points": 100
            }
        ]
        
        # Mevcut rozetleri kontrol et
        existing_count = await db.scalar(select(func.count(Achievement.id)))
        
        if existing_count == 0:
            # Rozetleri oluştur
            for achievement_data in default_achievements:
                achievement = Achievement(**achievement_data)
                db.add(achievement)
            
            await db.commit()
            print(f"✅ {len(default_achievements)} varsayılan rozet oluşturuldu!")
    
    @staticmethod
    async def check_and_award_achievements(
        db: AsyncSession,
        user_id: int,
        activity_type: str,
        activity_data: dict = None
    ) -> List[UserAchievementSchema]:
        """
        Kullanıcı aktivitesine göre rozetleri kontrol eder ve verir.
        
        Args:
            user_id: Kullanıcı ID
            activity_type: "food_log", "water_log", "workout_log", "creatine_dose"
            activity_data: Aktivite ile ilgili ek veriler
        
        Returns:
            Yeni kazanılan rozetlerin listesi
        """
        
        new_achievements = []
        
        # Tüm rozetleri getir
        stmt = select(Achievement)
        result = await db.execute(stmt)
        all_achievements = result.scalars().all()
        
        # Kullanıcının mevcut rozetlerini getir
        user_achievements_stmt = select(UserAchievement.achievement_id).where(
            UserAchievement.user_id == user_id
        )
        result = await db.execute(user_achievements_stmt)
        earned_achievement_ids = set(result.scalars().all())
        
        # Her rozeti kontrol et
        for achievement in all_achievements:
            # Zaten kazanılmışsa atla
            if achievement.id in earned_achievement_ids:
                continue
            
            # Rozet koşulunu kontrol et
            is_earned = await AchievementSystem._check_achievement_condition(
                db, user_id, achievement, activity_type, activity_data
            )
            
            if is_earned:
                # Rozeti ver
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    is_new=True
                )
                
                db.add(user_achievement)
                await db.commit()
                await db.refresh(user_achievement)
                
                # Achievement ilişkisini yükle
                await db.refresh(user_achievement, ["achievement"])
                
                new_achievements.append(
                    UserAchievementSchema.model_validate(user_achievement)
                )
                
                earned_achievement_ids.add(achievement.id)
        
        return new_achievements
    
    @staticmethod
    async def _check_achievement_condition(
        db: AsyncSession,
        user_id: int,
        achievement: Achievement,
        activity_type: str,
        activity_data: dict = None
    ) -> bool:
        """Rozet koşulunu kontrol eder."""
        
        condition_type = achievement.condition_type
        condition_value = achievement.condition_value
        category = achievement.category
        
        if condition_type == "count":
            return await AchievementSystem._check_count_condition(
                db, user_id, category, condition_value
            )
        
        elif condition_type == "streak":
            return await AchievementSystem._check_streak_condition(
                db, user_id, category, condition_value
            )
        
        elif condition_type == "daily_meals":
            return await AchievementSystem._check_daily_meals_condition(
                db, user_id, condition_value
            )
        
        elif condition_type == "daily_goal":
            return await AchievementSystem._check_daily_goal_condition(
                db, user_id, category, condition_value
            )
        
        elif condition_type == "weekly_count":
            return await AchievementSystem._check_weekly_count_condition(
                db, user_id, category, condition_value
            )
        
        elif condition_type == "unique_foods":
            return await AchievementSystem._check_unique_foods_condition(
                db, user_id, condition_value
            )
        
        elif condition_type == "weight_loss":
            return await AchievementSystem._check_weight_loss_condition(
                db, user_id, condition_value
            )
        
        elif condition_type == "perfect_day":
            return await AchievementSystem._check_perfect_day_condition(
                db, user_id, date.today()
            )
        
        elif condition_type == "perfect_streak":
            return await AchievementSystem._check_perfect_streak_condition(
                db, user_id, condition_value
            )
        
        return False
    
    @staticmethod
    async def _check_count_condition(
        db: AsyncSession,
        user_id: int,
        category: str,
        target_count: int
    ) -> bool:
        """Toplam sayı koşulunu kontrol eder."""
        
        if category == "food":
            stmt = select(func.count(FoodLog.id)).where(FoodLog.user_id == user_id)
        elif category == "water":
            stmt = select(func.count(WaterLog.id)).where(WaterLog.user_id == user_id)
        elif category == "workout":
            stmt = select(func.count(WorkoutLog.id))  # Şu an user_id yok
        elif category == "creatine":
            stmt = select(func.count(CreatineDose.id)).where(CreatineDose.user_id == user_id)
        else:
            return False
        
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        return count >= target_count
    
    @staticmethod
    async def _check_streak_condition(
        db: AsyncSession,
        user_id: int,
        category: str,
        target_streak: int
    ) -> bool:
        """Streak koşulunu kontrol eder."""
        
        current_date = date.today()
        streak_days = 0
        
        # Geriye doğru gün gün kontrol et
        for i in range(target_streak + 5):  # Biraz fazla kontrol et
            check_date = current_date - timedelta(days=i)
            
            has_activity = False
            
            if category == "food":
                has_activity = await AchievementSystem._has_food_activity_on_date(
                    db, user_id, check_date
                )
            elif category == "water":
                has_activity = await AchievementSystem._has_water_goal_met_on_date(
                    db, user_id, check_date
                )
            elif category == "creatine":
                has_activity = await AchievementSystem._has_creatine_activity_on_date(
                    db, user_id, check_date
                )
            
            if has_activity:
                streak_days += 1
            else:
                break  # Streak kırıldı
        
        return streak_days >= target_streak
    
    @staticmethod
    async def _check_daily_meals_condition(
        db: AsyncSession,
        user_id: int,
        target_meals: int
    ) -> bool:
        """Günlük öğün sayısı koşulunu kontrol eder."""
        
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # Bugün kaç farklı öğün tipi kaydedilmiş
        stmt = select(func.count(func.distinct(FoodLog.meal_type))).where(
            and_(
                FoodLog.user_id == user_id,
                FoodLog.logged_at >= start_of_day,
                FoodLog.logged_at <= end_of_day
            )
        )
        
        result = await db.execute(stmt)
        meal_count = result.scalar() or 0
        
        return meal_count >= target_meals
    
    @staticmethod
    async def _has_food_activity_on_date(
        db: AsyncSession,
        user_id: int,
        check_date: date
    ) -> bool:
        """Belirtilen tarihte yemek kaydı var mı kontrol eder."""
        
        start_of_day = datetime.combine(check_date, datetime.min.time())
        end_of_day = datetime.combine(check_date, datetime.max.time())
        
        stmt = select(func.count(FoodLog.id)).where(
            and_(
                FoodLog.user_id == user_id,
                FoodLog.logged_at >= start_of_day,
                FoodLog.logged_at <= end_of_day
            )
        )
        
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        return count > 0
    
    @staticmethod
    async def _has_water_goal_met_on_date(
        db: AsyncSession,
        user_id: int,
        check_date: date
    ) -> bool:
        """Belirtilen tarihte su hedefi tutulmuş mu kontrol eder."""
        
        from app.water_tracker import WaterTracker
        
        daily_summary = await WaterTracker.get_daily_water_summary(
            db, user_id, check_date
        )
        
        return daily_summary.percentage >= 100
    
    @staticmethod
    async def _check_weekly_count_condition(
        db: AsyncSession,
        user_id: int,
        category: str,
        target_count: int
    ) -> bool:
        """Haftalık sayı koşulunu kontrol eder."""
        
        # Son 7 günün başlangıcı
        week_start = date.today() - timedelta(days=6)
        week_start_datetime = datetime.combine(week_start, datetime.min.time())
        
        if category == "workout":
            stmt = select(func.count(WorkoutLog.id)).where(
                WorkoutLog.completed_at >= week_start_datetime
            )
        else:
            return False
        
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        return count >= target_count
    
    @staticmethod
    async def _check_daily_goal_condition(
        db: AsyncSession,
        user_id: int,
        category: str,
        target_value: int
    ) -> bool:
        """Günlük hedef koşulunu kontrol eder."""
        
        if category == "water":
            from app.water_tracker import WaterTracker
            daily_summary = await WaterTracker.get_daily_water_summary(db, user_id, date.today())
            return daily_summary.percentage >= 100
        
        return False
    
    @staticmethod
    async def _check_unique_foods_condition(
        db: AsyncSession,
        user_id: int,
        target_count: int
    ) -> bool:
        """Benzersiz yemek sayısı koşulunu kontrol eder."""
        
        stmt = select(func.count(func.distinct(FoodLog.food_name))).where(
            FoodLog.user_id == user_id
        )
        
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        return count >= target_count
    
    @staticmethod
    async def _check_weight_loss_condition(
        db: AsyncSession,
        user_id: int,
        target_kg: int
    ) -> bool:
        """Kilo verme koşulunu kontrol eder."""
        
        # İlk ve son ölçümü al
        from app.models import Measurement
        
        first_stmt = select(Measurement).where(
            and_(
                Measurement.user_id == user_id,
                Measurement.weight_kg.isnot(None)
            )
        ).order_by(Measurement.measured_at.asc()).limit(1)
        
        last_stmt = select(Measurement).where(
            and_(
                Measurement.user_id == user_id,
                Measurement.weight_kg.isnot(None)
            )
        ).order_by(Measurement.measured_at.desc()).limit(1)
        
        first_result = await db.execute(first_stmt)
        last_result = await db.execute(last_stmt)
        
        first_measurement = first_result.scalar_one_or_none()
        last_measurement = last_result.scalar_one_or_none()
        
        if not first_measurement or not last_measurement:
            return False
        
        weight_loss = first_measurement.weight_kg - last_measurement.weight_kg
        return weight_loss >= target_kg
    
    @staticmethod
    async def _check_perfect_day_condition(
        db: AsyncSession,
        user_id: int,
        check_date: date
    ) -> bool:
        """Mükemmel gün koşulunu kontrol eder (yemek + su + egzersiz)."""
        
        # Yemek kaydı var mı?
        has_food = await AchievementSystem._has_food_activity_on_date(db, user_id, check_date)
        
        # Su hedefi tutulmuş mu?
        has_water = await AchievementSystem._has_water_goal_met_on_date(db, user_id, check_date)
        
        # Egzersiz yapılmış mı?
        start_of_day = datetime.combine(check_date, datetime.min.time())
        end_of_day = datetime.combine(check_date, datetime.max.time())
        
        workout_stmt = select(func.count(WorkoutLog.id)).where(
            and_(
                WorkoutLog.completed_at >= start_of_day,
                WorkoutLog.completed_at <= end_of_day
            )
        )
        
        result = await db.execute(workout_stmt)
        has_workout = (result.scalar() or 0) > 0
        
        return has_food and has_water and has_workout
    
    @staticmethod
    async def _check_perfect_streak_condition(
        db: AsyncSession,
        user_id: int,
        target_streak: int
    ) -> bool:
        """Mükemmel gün streak koşulunu kontrol eder."""
        
        current_date = date.today()
        streak_days = 0
        
        # Geriye doğru gün gün kontrol et
        for i in range(target_streak + 5):
            check_date = current_date - timedelta(days=i)
            
            is_perfect = await AchievementSystem._check_perfect_day_condition(
                db, user_id, check_date
            )
            
            if is_perfect:
                streak_days += 1
            else:
                break  # Streak kırıldı
        
        return streak_days >= target_streak
    
    @staticmethod
    async def get_user_achievements(
        db: AsyncSession,
        user_id: int
    ) -> List[UserAchievementSchema]:
        """Kullanıcının tüm rozetlerini getirir."""
        
        stmt = select(UserAchievement).where(
            UserAchievement.user_id == user_id
        ).order_by(desc(UserAchievement.earned_at))
        
        result = await db.execute(stmt)
        user_achievements = result.scalars().all()
        
        # Achievement ilişkilerini yükle
        for ua in user_achievements:
            await db.refresh(ua, ["achievement"])
        
        return [UserAchievementSchema.model_validate(ua) for ua in user_achievements]
    
    @staticmethod
    async def mark_achievements_as_seen(
        db: AsyncSession,
        user_id: int
    ):
        """Kullanıcının yeni rozetlerini görüldü olarak işaretle."""
        
        stmt = select(UserAchievement).where(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.is_new == True
            )
        )
        
        result = await db.execute(stmt)
        new_achievements = result.scalars().all()
        
        for achievement in new_achievements:
            achievement.is_new = False
        
        await db.commit()
    
    @staticmethod
    async def get_achievement_progress(
        db: AsyncSession,
        user_id: int
    ) -> List[AchievementProgress]:
        """Kullanıcının rozet ilerleme durumunu getirir."""
        
        # Henüz kazanılmamış rozetleri getir
        earned_ids_stmt = select(UserAchievement.achievement_id).where(
            UserAchievement.user_id == user_id
        )
        result = await db.execute(earned_ids_stmt)
        earned_ids = set(result.scalars().all())
        
        stmt = select(Achievement).where(
            Achievement.id.notin_(earned_ids)
        ).limit(5)  # İlk 5 tane göster
        
        result = await db.execute(stmt)
        pending_achievements = result.scalars().all()
        
        progress_list = []
        
        for achievement in pending_achievements:
            current_value = await AchievementSystem._get_current_progress_value(
                db, user_id, achievement
            )
            
            percentage = min((current_value / achievement.condition_value * 100), 100)
            
            progress_list.append(AchievementProgress(
                achievement=AchievementSchema.model_validate(achievement),
                current_value=current_value,
                target_value=achievement.condition_value,
                percentage=round(percentage, 1),
                is_completed=current_value >= achievement.condition_value
            ))
        
        return progress_list
    
    @staticmethod
    async def _get_current_progress_value(
        db: AsyncSession,
        user_id: int,
        achievement: Achievement
    ) -> int:
        """Rozet için mevcut ilerleme değerini getirir."""
        
        if achievement.condition_type == "count":
            return await AchievementSystem._get_count_progress(
                db, user_id, achievement.category
            )
        elif achievement.condition_type == "streak":
            return await AchievementSystem._get_streak_progress(
                db, user_id, achievement.category
            )
        # Diğer condition_type'lar için de benzer metodlar eklenebilir
        
        return 0
    
    @staticmethod
    async def _get_count_progress(
        db: AsyncSession,
        user_id: int,
        category: str
    ) -> int:
        """Sayı bazlı ilerlemeyi getirir."""
        
        if category == "food":
            stmt = select(func.count(FoodLog.id)).where(FoodLog.user_id == user_id)
        elif category == "water":
            stmt = select(func.count(WaterLog.id)).where(WaterLog.user_id == user_id)
        elif category == "workout":
            stmt = select(func.count(WorkoutLog.id))
        elif category == "creatine":
            stmt = select(func.count(CreatineDose.id)).where(CreatineDose.user_id == user_id)
        else:
            return 0
        
        result = await db.execute(stmt)
        return result.scalar() or 0
    
    @staticmethod
    async def _get_streak_progress(
        db: AsyncSession,
        user_id: int,
        category: str
    ) -> int:
        """Streak bazlı ilerlemeyi getirir."""
        
        current_date = date.today()
        streak_days = 0
        
        # Geriye doğru gün gün kontrol et
        for i in range(30):  # Maksimum 30 gün kontrol et
            check_date = current_date - timedelta(days=i)
            
            has_activity = False
            
            if category == "food":
                has_activity = await AchievementSystem._has_food_activity_on_date(
                    db, user_id, check_date
                )
            elif category == "water":
                has_activity = await AchievementSystem._has_water_goal_met_on_date(
                    db, user_id, check_date
                )
            elif category == "creatine":
                has_activity = await AchievementSystem._has_creatine_activity_on_date(
                    db, user_id, check_date
                )
            
            if has_activity:
                streak_days += 1
            else:
                break  # Streak kırıldı
        
        return streak_days
    
    @staticmethod
    async def _has_creatine_activity_on_date(
        db: AsyncSession,
        user_id: int,
        check_date: date
    ) -> bool:
        """Belirtilen tarihte kreatin kaydı var mı kontrol eder."""
        
        start_of_day = datetime.combine(check_date, datetime.min.time())
        end_of_day = datetime.combine(check_date, datetime.max.time())
        
        stmt = select(func.count(CreatineDose.id)).where(
            and_(
                CreatineDose.user_id == user_id,
                CreatineDose.taken_at >= start_of_day,
                CreatineDose.taken_at <= end_of_day
            )
        )
        
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        return count > 0