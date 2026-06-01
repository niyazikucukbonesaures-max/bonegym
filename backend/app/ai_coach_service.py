# AI Coach Service - Ana AI Antrenman Koçu Servisi
# Kalori dengesi analizi, antrenman önerileri ve kişiselleştirme

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    AICoachPreferences,
    AICoachProgress,
    AICoachRecommendation,
    FoodLog,
    UserProfile,
    WorkoutLog,
)

logger = logging.getLogger(__name__)


class AICoachService:
    """
    AI Antrenman Koçu ana servisi.
    
    Kalori dengesi analizi, kişiselleştirilmiş antrenman önerileri,
    ilerleme takibi ve güvenlik kontrollerini yönetir.
    """
    
    def __init__(self):
        self.workout_engine = WorkoutRecommendationEngine()
        self.progress_engine = ProgressAnalysisEngine()
        self.safety_engine = SafetyPersonalizationEngine()
    
    async def get_daily_recommendation(self, user_id: int) -> Dict:
        """
        Kullanıcı için günlük antrenman önerisi oluşturur.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Antrenman önerisi dictionary'si
        """
        try:
            async for session in get_db():
                # Kullanıcı profilini al
                profile = await self._get_user_profile(session, user_id)
                if not profile:
                    raise ValueError(f"Kullanıcı profili bulunamadı: {user_id}")
                
                # Kullanıcı tercihlerini al
                preferences = await self._get_user_preferences(session, user_id)
                
                # Kalori dengesi analizi
                calorie_analysis = await self._analyze_calorie_balance(session, user_id, profile)
                
                # İlerleme analizi
                progress_analysis = await self.progress_engine.analyze_weekly_progress(session, user_id)
                
                # Güvenlik kontrolü
                safety_constraints = await self.safety_engine.get_safety_constraints(
                    session, user_id, preferences
                )
                
                # Antrenman önerisi oluştur
                recommendation = await self.workout_engine.generate_recommendation(
                    profile=profile,
                    preferences=preferences,
                    calorie_analysis=calorie_analysis,
                    progress_analysis=progress_analysis,
                    safety_constraints=safety_constraints
                )
                
                # Önerileri veritabanına kaydet
                saved_recommendation = await self._save_recommendation(
                    session, user_id, recommendation, calorie_analysis
                )
                
                await session.commit()
                return saved_recommendation
                
        except Exception as e:
            logger.error(f"Günlük öneri oluşturulurken hata: {e}")
            raise
    
    async def process_user_feedback(
        self, 
        user_id: int, 
        recommendation_id: int, 
        feedback: str, 
        reason: Optional[str] = None
    ) -> bool:
        """
        Kullanıcı geri bildirimini işler ve öğrenme algoritmasını günceller.
        
        Args:
            user_id: Kullanıcı ID'si
            recommendation_id: Öneri ID'si
            feedback: Geri bildirim (accepted/rejected/modified)
            reason: Geri bildirim nedeni
            
        Returns:
            İşlem başarı durumu
        """
        try:
            async for session in get_db():
                # Öneriyi güncelle
                recommendation = await session.get(AICoachRecommendation, recommendation_id)
                if not recommendation or recommendation.user_id != user_id:
                    return False
                
                recommendation.user_feedback = feedback
                recommendation.feedback_reason = reason
                recommendation.status = feedback
                
                if feedback == "accepted":
                    recommendation.accepted_at = datetime.utcnow()
                
                # Kullanıcı tercihlerini güncelle (öğrenme)
                await self._update_learned_preferences(session, user_id, feedback, recommendation)
                
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Geri bildirim işlenirken hata: {e}")
            return False
    
    async def get_progress_insights(self, user_id: int) -> Dict:
        """
        Kullanıcının ilerleme analizini ve öngörülerini döndürür.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            İlerleme analizi dictionary'si
        """
        try:
            async for session in get_db():
                return await self.progress_engine.get_comprehensive_analysis(session, user_id)
        except Exception as e:
            logger.error(f"İlerleme analizi alınırken hata: {e}")
            raise
    
    # Private helper methods
    
    async def _get_user_profile(self, session: AsyncSession, user_id: int) -> Optional[UserProfile]:
        """Kullanıcı profilini getirir."""
        result = await session.execute(
            select(UserProfile).where(UserProfile.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_user_preferences(self, session: AsyncSession, user_id: int) -> AICoachPreferences:
        """Kullanıcı tercihlerini getirir, yoksa varsayılan oluşturur."""
        result = await session.execute(
            select(AICoachPreferences).where(AICoachPreferences.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        if not preferences:
            # Varsayılan preferences oluştur
            preferences = AICoachPreferences(
                user_id=user_id,
                preferred_workout_types=["strength_training", "cardio"],
                preferred_duration_min=30,
                preferred_duration_max=60,
                preferred_intensity={"low": 0.3, "moderate": 0.5, "high": 0.2},
                avoided_exercises=[],
                health_conditions=[],
                learned_patterns={},
                feedback_history={"accepted": 0, "rejected": 0, "modified": 0},
                motivation_style="balanced",
                safety_level="standard"
            )
            session.add(preferences)
            await session.flush()
        
        return preferences
    
    async def _analyze_calorie_balance(
        self, 
        session: AsyncSession, 
        user_id: int, 
        profile: UserProfile
    ) -> Dict:
        """Günlük kalori dengesi analizi yapar."""
        today = datetime.now().date()
        
        # Bugünkü kalori alımını hesapla
        result = await session.execute(
            select(func.sum(FoodLog.calories))
            .where(
                and_(
                    FoodLog.user_id == user_id,
                    func.date(FoodLog.logged_at) == today
                )
            )
        )
        daily_calories = result.scalar() or 0.0
        
        # Hedef kaloriyi hesapla (TDEE veya manuel hedef)
        target_calories = profile.daily_calorie_target or self._calculate_tdee(profile)
        
        # Kalori dengesi analizi
        calorie_balance = daily_calories - target_calories
        calorie_percentage = (daily_calories / target_calories) * 100 if target_calories > 0 else 0
        
        return {
            "daily_calories": daily_calories,
            "target_calories": target_calories,
            "calorie_balance": calorie_balance,
            "calorie_percentage": calorie_percentage,
            "status": self._get_calorie_status(calorie_percentage)
        }
    
    def _calculate_tdee(self, profile: UserProfile) -> float:
        """TDEE (Total Daily Energy Expenditure) hesaplar."""
        # BMR hesaplama (Mifflin-St Jeor denklemi)
        if profile.gender == "male":
            bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5
        else:
            bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age - 161
        
        # Aktivite çarpanları
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        
        tdee = bmr * activity_multipliers.get(profile.activity_level, 1.55)
        
        # Hedef ayarlaması
        if profile.goal == "lose":
            tdee *= 0.85  # %15 kalori açığı
        elif profile.goal == "gain":
            tdee *= 1.15  # %15 kalori fazlası
        
        return tdee
    
    def _get_calorie_status(self, percentage: float) -> str:
        """Kalori yüzdesine göre durum döndürür."""
        if percentage < 70:
            return "very_low"
        elif percentage < 85:
            return "low"
        elif percentage <= 115:
            return "optimal"
        elif percentage <= 130:
            return "high"
        else:
            return "very_high"
    
    async def _save_recommendation(
        self, 
        session: AsyncSession, 
        user_id: int, 
        recommendation: Dict, 
        calorie_analysis: Dict
    ) -> Dict:
        """Önerileri veritabanına kaydeder."""
        db_recommendation = AICoachRecommendation(
            user_id=user_id,
            recommendation_type=recommendation["type"],
            workout_plan=recommendation.get("workout_plan"),
            calorie_balance=calorie_analysis["calorie_balance"],
            calorie_percentage=calorie_analysis["calorie_percentage"],
            intensity_level=recommendation["intensity"],
            duration_minutes=recommendation["duration"],
            motivation_message=recommendation["motivation_message"],
            status="pending"
        )
        
        session.add(db_recommendation)
        await session.flush()
        
        return {
            "id": db_recommendation.id,
            "type": recommendation["type"],
            "workout_plan": recommendation.get("workout_plan"),
            "intensity": recommendation["intensity"],
            "duration": recommendation["duration"],
            "motivation_message": recommendation["motivation_message"],
            "calorie_analysis": calorie_analysis,
            "created_at": db_recommendation.created_at.isoformat()
        }
    
    async def _update_learned_preferences(
        self, 
        session: AsyncSession, 
        user_id: int, 
        feedback: str, 
        recommendation: AICoachRecommendation
    ):
        """Kullanıcı geri bildiriminden öğrenme yapar."""
        preferences = await self._get_user_preferences(session, user_id)
        
        # Geri bildirim geçmişini güncelle
        feedback_history = preferences.feedback_history or {}
        feedback_history[feedback] = feedback_history.get(feedback, 0) + 1
        feedback_history["total_recommendations"] = feedback_history.get("total_recommendations", 0) + 1
        
        # Öğrenilen kalıpları güncelle
        learned_patterns = preferences.learned_patterns or {}
        
        if feedback == "accepted":
            # Kabul edilen önerilerin özelliklerini öğren
            if "accepted_intensities" not in learned_patterns:
                learned_patterns["accepted_intensities"] = {}
            
            intensity = recommendation.intensity_level
            learned_patterns["accepted_intensities"][intensity] = \
                learned_patterns["accepted_intensities"].get(intensity, 0) + 1
        
        preferences.feedback_history = feedback_history
        preferences.learned_patterns = learned_patterns
        preferences.updated_at = datetime.utcnow()


class WorkoutRecommendationEngine:
    """Antrenman önerisi oluşturma motoru."""
    
    async def generate_recommendation(
        self,
        profile: UserProfile,
        preferences: AICoachPreferences,
        calorie_analysis: Dict,
        progress_analysis: Dict,
        safety_constraints: Dict
    ) -> Dict:
        """Kişiselleştirilmiş antrenman önerisi oluşturur — önce Gemini, sonra fallback."""

        # ── Gemini ile dene ────────────────────────────────────────────────
        try:
            from app.gemini_service import ask_workout_coach, is_gemini_available
            if is_gemini_available():
                profile_dict = {
                    "goal": profile.goal,
                    "weight_kg": profile.weight_kg,
                    "height_cm": profile.height_cm,
                    "activity_level": profile.activity_level,
                    "age": profile.age,
                    "fitness_level": getattr(profile, "fitness_level", "beginner"),
                }
                result = await ask_workout_coach(
                    user_profile=profile_dict,
                    daily_calories=calorie_analysis["daily_calories"],
                    target_calories=calorie_analysis["target_calories"],
                )
                if result["error"] is None and result["workout_plan"]:
                    wp = result["workout_plan"]
                    return {
                        "type": wp.get("workout_type", "balanced_workout"),
                        "intensity": wp.get("intensity", "moderate"),
                        "duration": wp.get("duration_minutes", 45),
                        "workout_plan": {
                            "exercises": wp.get("exercises", []),
                            "warm_up": "5 dakika hafif kardiyo",
                            "cool_down": "5 dakika stretching",
                            "total_duration": wp.get("duration_minutes", 45),
                            "notes": result["response"][:200] if result["response"] else "",
                        },
                        "motivation_message": wp.get("motivation", result["response"][:150] if result["response"] else "Harika bir antrenman seni bekliyor! 💪"),
                    }
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Gemini antrenman önerisi başarısız, fallback kullanılıyor: {e}")

        # ── Fallback: Kural tabanlı sistem ────────────────────────────────
        workout_type = self._determine_workout_type(calorie_analysis, profile.goal)
        intensity = self._determine_intensity(calorie_analysis, progress_analysis, preferences)
        duration = self._determine_duration(calorie_analysis, preferences, safety_constraints)
        workout_plan = self._create_workout_plan(
            workout_type, intensity, duration, preferences, safety_constraints
        )
        motivation_message = self._generate_motivation_message(
            calorie_analysis, workout_type, preferences.motivation_style
        )
        return {
            "type": workout_type,
            "intensity": intensity,
            "duration": duration,
            "workout_plan": workout_plan,
            "motivation_message": motivation_message
        }
    
    def _determine_workout_type(self, calorie_analysis: Dict, goal: str) -> str:
        """Kalori durumu ve hedefe göre antrenman türü belirler."""
        calorie_status = calorie_analysis["status"]
        
        if calorie_status in ["very_low", "low"]:
            # Düşük kalori alımında hafif aktivite öner
            return "light_activity"
        elif calorie_status == "optimal":
            # Optimal kalori alımında hedefe göre antrenman
            if goal == "lose":
                return "cardio_focused"
            elif goal == "gain":
                return "strength_focused"
            else:
                return "balanced_workout"
        else:
            # Yüksek kalori alımında yoğun antrenman
            return "high_intensity"
    
    def _determine_intensity(
        self, 
        calorie_analysis: Dict, 
        progress_analysis: Dict, 
        preferences: AICoachPreferences
    ) -> str:
        """Yoğunluk seviyesi belirler."""
        calorie_percentage = calorie_analysis["calorie_percentage"]
        
        # Kalori durumuna göre temel yoğunluk
        if calorie_percentage < 70:
            base_intensity = "low"
        elif calorie_percentage < 85:
            base_intensity = "moderate"
        else:
            base_intensity = "high"
        
        # Kullanıcı tercihlerine göre ayarla
        preferred_intensities = preferences.preferred_intensity or {}
        if base_intensity in preferred_intensities:
            # Tercihlere uygunsa aynı kalır
            return base_intensity
        else:
            # En çok tercih edilen yoğunluğu seç
            return max(preferred_intensities.keys(), key=lambda k: preferred_intensities[k])
    
    def _determine_duration(
        self, 
        calorie_analysis: Dict, 
        preferences: AICoachPreferences, 
        safety_constraints: Dict
    ) -> int:
        """Antrenman süresini belirler."""
        base_duration = (preferences.preferred_duration_min + preferences.preferred_duration_max) // 2
        
        # Kalori durumuna göre ayarlama
        calorie_percentage = calorie_analysis["calorie_percentage"]
        if calorie_percentage < 75:
            # %25 süre azaltma
            duration = int(base_duration * 0.75)
        else:
            duration = base_duration
        
        # Güvenlik kısıtlamalarını uygula
        max_duration = safety_constraints.get("max_duration", 90)
        duration = min(duration, max_duration)
        
        # Minimum süre kontrolü
        duration = max(duration, 15)
        
        return duration
    
    def _create_workout_plan(
        self,
        workout_type: str,
        intensity: str,
        duration: int,
        preferences: AICoachPreferences,
        safety_constraints: Dict
    ) -> Dict:
        """Detaylı egzersiz planı oluşturur."""
        
        # Kaçınılacak egzersizler
        avoided = set(preferences.avoided_exercises or [])
        
        # Antrenman türüne göre egzersiz havuzu
        exercise_pools = {
            "strength_focused": [
                {"name": "Squat", "sets": 3, "reps": "8-12", "rest": 90},
                {"name": "Bench Press", "sets": 3, "reps": "8-12", "rest": 90},
                {"name": "Deadlift", "sets": 3, "reps": "5-8", "rest": 120},
                {"name": "Pull-up", "sets": 3, "reps": "6-10", "rest": 90},
            ],
            "cardio_focused": [
                {"name": "Koşu", "duration": 20, "intensity": "moderate"},
                {"name": "Bisiklet", "duration": 25, "intensity": "moderate"},
                {"name": "Yürüyüş", "duration": 30, "intensity": "low"},
                {"name": "HIIT", "duration": 15, "intensity": "high"},
            ],
            "balanced_workout": [
                {"name": "Squat", "sets": 2, "reps": "10-15", "rest": 60},
                {"name": "Push-up", "sets": 2, "reps": "10-15", "rest": 60},
                {"name": "Koşu", "duration": 15, "intensity": "moderate"},
            ],
            "light_activity": [
                {"name": "Yürüyüş", "duration": 20, "intensity": "low"},
                {"name": "Stretching", "duration": 10, "intensity": "low"},
                {"name": "Yoga", "duration": 15, "intensity": "low"},
            ],
            "high_intensity": [
                {"name": "Burpee", "sets": 3, "reps": "10-15", "rest": 45},
                {"name": "Mountain Climber", "sets": 3, "reps": "20-30", "rest": 45},
                {"name": "Jump Squat", "sets": 3, "reps": "15-20", "rest": 45},
            ]
        }
        
        # Egzersizleri seç ve filtrele
        available_exercises = exercise_pools.get(workout_type, exercise_pools["balanced_workout"])
        selected_exercises = [ex for ex in available_exercises if ex["name"] not in avoided]
        
        # Süreye göre egzersiz sayısını ayarla
        max_exercises = min(len(selected_exercises), duration // 10)
        selected_exercises = selected_exercises[:max_exercises]
        
        return {
            "exercises": selected_exercises,
            "warm_up": "5 dakika hafif kardiyo",
            "cool_down": "5 dakika stretching",
            "total_duration": duration,
            "notes": f"{intensity.title()} yoğunlukta {workout_type.replace('_', ' ')} antrenmanı"
        }
    
    def _generate_motivation_message(
        self, 
        calorie_analysis: Dict, 
        workout_type: str, 
        motivation_style: str
    ) -> str:
        """Motivasyon mesajı oluşturur."""
        calorie_status = calorie_analysis["status"]
        
        messages = {
            "encouraging": {
                "very_low": "Bugün enerjin düşük olabilir, hafif bir aktivite ile başlayalım! 💪",
                "low": "Hafif bir antrenman ile günü güzel bitirelim! 🌟",
                "optimal": "Mükemmel! Bugün harika bir antrenman için hazırsın! 🔥",
                "high": "Enerji dolu bir gün! Bu enerjiyi harika bir antrenmana dönüştürelim! ⚡",
                "very_high": "Süper enerji seviyesi! Bugün kendini aşma zamanı! 🚀"
            },
            "challenging": {
                "very_low": "Zorlu günlerde bile hareket etmek önemli. Kendini zorla! 💪",
                "low": "Bahaneler yok! Hafif de olsa antrenman yapalım! 🔥",
                "optimal": "Mükemmel koşullar! Limitlerini zorla! ⚡",
                "high": "Bu enerjiyi boşa harcama! Yoğun antrenman zamanı! 🚀",
                "very_high": "Maksimum güç! Bugün rekor kırma günü! 💥"
            },
            "balanced": {
                "very_low": "Bugün kendine nazik ol, hafif aktivite yeterli 🌸",
                "low": "Yavaş başla, vücudunu dinle 🎯",
                "optimal": "Harika bir antrenman için mükemmel koşullar! 🌟",
                "high": "Enerji dolu bir antrenman seni bekliyor! 💪",
                "very_high": "Yüksek enerji, yüksek performans! Hadi başlayalım! 🔥"
            }
        }
        
        return messages.get(motivation_style, messages["balanced"]).get(calorie_status, 
            "Bugün de harika bir antrenman yapacaksın! 💪")


class ProgressAnalysisEngine:
    """İlerleme analizi ve adaptasyon motoru."""
    
    async def analyze_weekly_progress(self, session: AsyncSession, user_id: int) -> Dict:
        """Haftalık ilerleme analizi yapar."""
        # Son 7 günün verilerini al
        week_start = datetime.now() - timedelta(days=7)
        
        # Tamamlanan antrenmanları say
        result = await session.execute(
            select(func.count(WorkoutLog.id))
            .where(
                and_(
                    WorkoutLog.program_id.isnot(None),  # AI Coach önerileri için program_id None olabilir
                    WorkoutLog.completed_at >= week_start
                )
            )
        )
        workouts_completed = result.scalar() or 0
        
        # Ortalama antrenman süresini hesapla
        result = await session.execute(
            select(func.avg(WorkoutLog.duration_minutes))
            .where(
                and_(
                    WorkoutLog.program_id.isnot(None),
                    WorkoutLog.completed_at >= week_start
                )
            )
        )
        avg_duration = result.scalar() or 0
        
        return {
            "workouts_completed": workouts_completed,
            "avg_duration": float(avg_duration),
            "completion_rate": min(workouts_completed / 4.0, 1.0),  # 4 antrenman hedefi
            "trend": "improving" if workouts_completed >= 3 else "needs_improvement"
        }
    
    async def get_comprehensive_analysis(self, session: AsyncSession, user_id: int) -> Dict:
        """Kapsamlı ilerleme analizi döndürür."""
        # Son 4 haftanın verilerini al
        four_weeks_ago = datetime.now() - timedelta(weeks=4)
        
        # Haftalık istatistikleri hesapla
        weekly_stats = []
        for week in range(4):
            week_start = datetime.now() - timedelta(weeks=week+1)
            week_end = datetime.now() - timedelta(weeks=week)
            
            result = await session.execute(
                select(
                    func.count(WorkoutLog.id),
                    func.avg(WorkoutLog.duration_minutes)
                )
                .where(
                    and_(
                        WorkoutLog.completed_at >= week_start,
                        WorkoutLog.completed_at < week_end
                    )
                )
            )
            count, avg_duration = result.first()
            
            weekly_stats.append({
                "week": f"Hafta {4-week}",
                "workouts": count or 0,
                "avg_duration": float(avg_duration or 0)
            })
        
        # Genel trend analizi
        workout_counts = [stat["workouts"] for stat in weekly_stats]
        trend = "improving" if workout_counts[-1] > workout_counts[0] else "declining"
        
        return {
            "weekly_stats": weekly_stats,
            "overall_trend": trend,
            "total_workouts": sum(workout_counts),
            "consistency_score": self._calculate_consistency_score(workout_counts)
        }
    
    def _calculate_consistency_score(self, workout_counts: List[int]) -> float:
        """Tutarlılık skoru hesaplar (0-100)."""
        if not workout_counts:
            return 0.0
        
        # Standart sapma ile tutarlılığı ölç
        mean = sum(workout_counts) / len(workout_counts)
        if mean == 0:
            return 0.0
        
        variance = sum((x - mean) ** 2 for x in workout_counts) / len(workout_counts)
        std_dev = variance ** 0.5
        
        # Tutarlılık skoru (düşük standart sapma = yüksek tutarlılık)
        consistency = max(0, 100 - (std_dev / mean) * 50)
        return min(consistency, 100.0)


class SafetyPersonalizationEngine:
    """Güvenlik ve kişiselleştirme motoru."""
    
    async def get_safety_constraints(
        self, 
        session: AsyncSession, 
        user_id: int, 
        preferences: AICoachPreferences
    ) -> Dict:
        """Güvenlik kısıtlamalarını döndürür."""
        
        # Kullanıcı profilini al
        result = await session.execute(
            select(UserProfile).where(UserProfile.id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        constraints = {
            "max_duration": 90,  # Varsayılan maksimum süre
            "intensity_limit": "high",
            "avoided_exercises": preferences.avoided_exercises or [],
            "health_modifications": []
        }
        
        if profile:
            # Yaş bazlı ayarlamalar
            if profile.age >= 65:
                constraints["max_duration"] = 60
                constraints["intensity_limit"] = "moderate"
                constraints["health_modifications"].append("senior_friendly")
            elif profile.age >= 50:
                constraints["max_duration"] = 75
                constraints["health_modifications"].append("age_appropriate")
        
        # Sağlık durumu kontrolü
        health_conditions = preferences.health_conditions or []
        for condition in health_conditions:
            if condition in ["heart_condition", "high_blood_pressure"]:
                constraints["intensity_limit"] = "moderate"
                constraints["health_modifications"].append("cardio_limited")
            elif condition in ["joint_problems", "arthritis"]:
                constraints["avoided_exercises"].extend(["high_impact", "jumping"])
                constraints["health_modifications"].append("joint_friendly")
        
        # Güvenlik seviyesi ayarlaması
        safety_level = preferences.safety_level
        if safety_level == "conservative":
            constraints["max_duration"] = min(constraints["max_duration"], 45)
            if constraints["intensity_limit"] == "high":
                constraints["intensity_limit"] = "moderate"
        elif safety_level == "aggressive":
            constraints["max_duration"] = min(constraints["max_duration"] + 15, 120)
        
        return constraints


# Global AI Coach Service instance
ai_coach_service = AICoachService()