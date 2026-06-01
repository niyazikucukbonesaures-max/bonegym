# Fitness ve Kalori Takip Uygulaması - Spor Hedef Motoru
# Spor yapanlara özel kalori hedefleme ve makro besin algoritmaları

from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserProfile, SportProfile, WorkoutLog, Measurement
from app.enhanced_calorie_engine import EnhancedCalorieEngine, EnhancedMacroTargets


# ---------------------------------------------------------------------------
# Enum ve Sabitler
# ---------------------------------------------------------------------------

class TrainingIntensity(Enum):
    """Antrenman yoğunluğu seviyeleri."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class SportType(Enum):
    """Spor türleri."""
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    POWERLIFTING = "powerlifting"
    BODYBUILDING = "bodybuilding"
    CROSSFIT = "crossfit"
    MIXED = "mixed"
    GENERAL = "general"


# Antrenman günü kalori çarpanları
TRAINING_DAY_MULTIPLIERS = {
    TrainingIntensity.LOW: Decimal("1.10"),      # %10 artış
    TrainingIntensity.MODERATE: Decimal("1.15"), # %15 artış
    TrainingIntensity.HIGH: Decimal("1.20"),     # %20 artış
    TrainingIntensity.VERY_HIGH: Decimal("1.25") # %25 artış
}

# Dinlenme günü kalori çarpanları
REST_DAY_MULTIPLIERS = {
    TrainingIntensity.LOW: Decimal("1.02"),      # %2 artış
    TrainingIntensity.MODERATE: Decimal("1.05"), # %5 artış
    TrainingIntensity.HIGH: Decimal("1.08"),     # %8 artış
    TrainingIntensity.VERY_HIGH: Decimal("1.10") # %10 artış
}

# Spor tipine göre makro oranları
SPORT_SPECIFIC_MACROS = {
    SportType.STRENGTH: {
        "muscle_gain": {"protein": Decimal("0.35"), "carbs": Decimal("0.45"), "fat": Decimal("0.20")},
        "maintenance": {"protein": Decimal("0.30"), "carbs": Decimal("0.40"), "fat": Decimal("0.30")},
        "cut": {"protein": Decimal("0.40"), "carbs": Decimal("0.35"), "fat": Decimal("0.25")}
    },
    SportType.ENDURANCE: {
        "performance": {"protein": Decimal("0.25"), "carbs": Decimal("0.55"), "fat": Decimal("0.20")},
        "maintenance": {"protein": Decimal("0.25"), "carbs": Decimal("0.50"), "fat": Decimal("0.25")},
        "weight_loss": {"protein": Decimal("0.30"), "carbs": Decimal("0.45"), "fat": Decimal("0.25")}
    },
    SportType.POWERLIFTING: {
        "strength": {"protein": Decimal("0.40"), "carbs": Decimal("0.35"), "fat": Decimal("0.25")},
        "bulk": {"protein": Decimal("0.35"), "carbs": Decimal("0.45"), "fat": Decimal("0.20")},
        "cut": {"protein": Decimal("0.45"), "carbs": Decimal("0.30"), "fat": Decimal("0.25")}
    },
    SportType.BODYBUILDING: {
        "bulk": {"protein": Decimal("0.35"), "carbs": Decimal("0.45"), "fat": Decimal("0.20")},
        "cut": {"protein": Decimal("0.45"), "carbs": Decimal("0.30"), "fat": Decimal("0.25")},
        "maintenance": {"protein": Decimal("0.40"), "carbs": Decimal("0.35"), "fat": Decimal("0.25")}
    },
    SportType.CROSSFIT: {
        "performance": {"protein": Decimal("0.30"), "carbs": Decimal("0.45"), "fat": Decimal("0.25")},
        "lean_gain": {"protein": Decimal("0.35"), "carbs": Decimal("0.40"), "fat": Decimal("0.25")},
        "weight_loss": {"protein": Decimal("0.35"), "carbs": Decimal("0.40"), "fat": Decimal("0.25")}
    }
}


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------

@dataclass
class AthleteCalorieResult:
    """Sporcu kalori hesaplama sonucu."""
    base_calories: Decimal
    training_day_calories: Decimal
    rest_day_calories: Decimal
    weekly_average: Decimal
    training_days_per_week: int
    intensity_level: str
    adjustments_applied: Dict[str, str]


@dataclass
class SportSpecificMacros:
    """Spor tipine özel makro besin hedefleri."""
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal
    protein_percentage: float
    carbs_percentage: float
    fat_percentage: float
    sport_type: str
    goal_type: str
    rationale: str


@dataclass
class TrainingDayRecommendation:
    """Antrenman günü önerisi."""
    is_training_day: bool
    recommended_calories: Decimal
    macros: SportSpecificMacros
    pre_workout_carbs: Decimal
    post_workout_protein: Decimal
    hydration_ml: int
    timing_notes: List[str]


# ---------------------------------------------------------------------------
# SportTargetEngine Sınıfı
# ---------------------------------------------------------------------------

class SportTargetEngine:
    """Spor yapanlara özel kalori ve makro hedefleme motoru."""
    
    def __init__(self):
        """Enhanced CalorieEngine ile entegrasyon."""
        self.calorie_engine = EnhancedCalorieEngine()
    
    # ------------------------------------------------------------------
    # Ana Kalori Hesaplama Metodları
    # ------------------------------------------------------------------
    
    async def calculate_athlete_calories(
        self, 
        user_profile: UserProfile, 
        training_day: bool,
        db: AsyncSession,
        custom_intensity: Optional[str] = None
    ) -> AthleteCalorieResult:
        """Sporcu için kalori hesaplama.
        
        Args:
            user_profile: Kullanıcı profili
            training_day: Antrenman günü mü?
            db: Veritabanı oturumu
            custom_intensity: Özel yoğunluk seviyesi
            
        Returns:
            AthleteCalorieResult: Detaylı kalori hesaplama sonucu
        """
        # Spor profili al
        sport_profile = await self._get_sport_profile(user_profile.id, db)
        
        # BMR ve TDEE hesapla
        bmr_result = self.calorie_engine.calculate_enhanced_bmr(
            weight_kg=user_profile.weight_kg,
            height_cm=user_profile.height_cm,
            age=user_profile.age,
            gender=user_profile.gender,
            is_athlete=sport_profile.is_athlete if sport_profile else False
        )
        
        # Antrenman bilgilerini al
        training_frequency = sport_profile.training_frequency if sport_profile else 3
        intensity = custom_intensity or (sport_profile.training_intensity if sport_profile else "moderate")
        
        tdee = self.calorie_engine.calculate_enhanced_tdee(
            bmr=bmr_result.bmr,
            activity_level=user_profile.activity_level,
            training_days_per_week=training_frequency,
            training_intensity=intensity
        )
        
        # Yoğunluk seviyesini enum'a dönüştür
        intensity_enum = TrainingIntensity(intensity)
        
        # Antrenman ve dinlenme günü çarpanları
        training_multiplier = TRAINING_DAY_MULTIPLIERS[intensity_enum]
        rest_multiplier = REST_DAY_MULTIPLIERS[intensity_enum]
        
        # Kalori hesaplamaları
        base_calories = self.calorie_engine.get_enhanced_recommended_calories(
            tdee=tdee,
            goal=user_profile.goal,
            is_athlete=sport_profile.is_athlete if sport_profile else False
        )
        
        training_day_calories = base_calories * training_multiplier
        rest_day_calories = base_calories * rest_multiplier
        
        # Haftalık ortalama
        weekly_average = (
            (training_day_calories * Decimal(str(training_frequency))) +
            (rest_day_calories * Decimal(str(7 - training_frequency)))
        ) / Decimal("7")
        
        adjustments_applied = {
            "base_formula": "Enhanced Mifflin-St Jeor + TDEE",
            "training_adjustment": f"+{(training_multiplier - 1) * 100:.0f}%",
            "rest_adjustment": f"+{(rest_multiplier - 1) * 100:.0f}%",
            "intensity": intensity,
            "frequency": f"{training_frequency} days/week"
        }
        
        return AthleteCalorieResult(
            base_calories=base_calories,
            training_day_calories=training_day_calories.quantize(Decimal("1"), rounding=ROUND_HALF_UP),
            rest_day_calories=rest_day_calories.quantize(Decimal("1"), rounding=ROUND_HALF_UP),
            weekly_average=weekly_average.quantize(Decimal("1"), rounding=ROUND_HALF_UP),
            training_days_per_week=training_frequency,
            intensity_level=intensity,
            adjustments_applied=adjustments_applied
        )
    
    async def get_sport_specific_macros(
        self, 
        goal: str, 
        daily_calories: float,
        user_id: int,
        db: AsyncSession,
        sport_type: Optional[str] = None
    ) -> SportSpecificMacros:
        """Spor tipine göre makro besin hedefleri.
        
        Args:
            goal: Hedef (muscle_gain, cut, bulk, vb.)
            daily_calories: Günlük kalori hedefi
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            sport_type: Spor tipi
            
        Returns:
            SportSpecificMacros: Spor tipine özel makro hedefleri
        """
        # Spor profili al
        sport_profile = await self._get_sport_profile(user_id, db)
        
        # Spor tipini belirle
        if sport_type:
            sport_enum = SportType(sport_type)
        elif sport_profile and sport_profile.sport_type:
            sport_enum = SportType(sport_profile.sport_type)
        else:
            sport_enum = SportType.GENERAL
        
        # Hedef tipini normalize et
        normalized_goal = self._normalize_goal(goal)
        
        # Makro oranlarını al
        if sport_enum in SPORT_SPECIFIC_MACROS:
            sport_macros = SPORT_SPECIFIC_MACROS[sport_enum]
            if normalized_goal in sport_macros:
                ratios = sport_macros[normalized_goal]
            else:
                # Varsayılan oran
                ratios = list(sport_macros.values())[0]
        else:
            # Genel spor makroları
            ratios = {"protein": Decimal("0.30"), "carbs": Decimal("0.40"), "fat": Decimal("0.30")}
        
        # Kalori dağılımı
        calories_decimal = Decimal(str(daily_calories))
        protein_calories = calories_decimal * ratios["protein"]
        carbs_calories = calories_decimal * ratios["carbs"]
        fat_calories = calories_decimal * ratios["fat"]
        
        # Gram hesaplama
        protein_g = protein_calories / Decimal("4")
        carbs_g = carbs_calories / Decimal("4")
        fat_g = fat_calories / Decimal("9")
        
        # Rationale oluştur
        rationale = self._generate_macro_rationale(sport_enum, normalized_goal)
        
        return SportSpecificMacros(
            protein_g=protein_g.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            carbs_g=carbs_g.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            fat_g=fat_g.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            protein_percentage=float(ratios["protein"] * 100),
            carbs_percentage=float(ratios["carbs"] * 100),
            fat_percentage=float(ratios["fat"] * 100),
            sport_type=sport_enum.value,
            goal_type=normalized_goal,
            rationale=rationale
        )
    
    async def adjust_for_training_intensity(
        self, 
        base_calories: float, 
        intensity: str,
        user_id: int,
        db: AsyncSession
    ) -> Decimal:
        """Antrenman yoğunluğuna göre kalori ayarlama.
        
        Args:
            base_calories: Temel kalori miktarı
            intensity: Antrenman yoğunluğu
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            
        Returns:
            Decimal: Ayarlanmış kalori miktarı
        """
        # Son antrenman verilerini analiz et
        recent_workouts = await self._get_recent_workouts(user_id, db, days=7)
        
        # Yoğunluk seviyesini belirle
        intensity_enum = TrainingIntensity(intensity)
        
        # Temel çarpan
        base_multiplier = TRAINING_DAY_MULTIPLIERS[intensity_enum]
        
        # Son antrenman performansına göre ayarlama
        if recent_workouts:
            avg_duration = sum(w.duration_minutes for w in recent_workouts) / len(recent_workouts)
            
            # Uzun antrenmanlar için ek kalori
            if avg_duration > 90:
                base_multiplier *= Decimal("1.05")  # %5 ek
            elif avg_duration > 120:
                base_multiplier *= Decimal("1.10")  # %10 ek
        
        adjusted_calories = Decimal(str(base_calories)) * base_multiplier
        return adjusted_calories.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    
    # ------------------------------------------------------------------
    # Günlük Öneriler
    # ------------------------------------------------------------------
    
    async def get_daily_recommendation(
        self, 
        user_id: int, 
        target_date: date,
        db: AsyncSession
    ) -> TrainingDayRecommendation:
        """Belirli bir gün için antrenman önerisi.
        
        Args:
            user_id: Kullanıcı ID'si
            target_date: Hedef tarih
            db: Veritabanı oturumu
            
        Returns:
            TrainingDayRecommendation: Günlük antrenman önerisi
        """
        # Kullanıcı profili al
        user_profile = await self._get_user_profile(user_id, db)
        sport_profile = await self._get_sport_profile(user_id, db)
        
        # Bu gün antrenman günü mü?
        is_training_day = await self._is_training_day(user_id, target_date, db)
        
        # Kalori hesapla
        calorie_result = await self.calculate_athlete_calories(
            user_profile=user_profile,
            training_day=is_training_day,
            db=db
        )
        
        # Makro hedefleri al
        daily_calories = float(calorie_result.training_day_calories if is_training_day else calorie_result.rest_day_calories)
        macros = await self.get_sport_specific_macros(
            goal=user_profile.goal,
            daily_calories=daily_calories,
            user_id=user_id,
            db=db,
            sport_type=sport_profile.sport_type if sport_profile else None
        )
        
        # Antrenman öncesi/sonrası öneriler
        pre_workout_carbs = macros.carbs_g * Decimal("0.3") if is_training_day else Decimal("0")
        post_workout_protein = macros.protein_g * Decimal("0.4") if is_training_day else Decimal("0")
        
        # Hidrasyon önerisi
        base_hydration = 2000  # ml
        if is_training_day:
            base_hydration += 500  # Antrenman günü ek su
        
        # Zamanlama notları
        timing_notes = []
        if is_training_day:
            timing_notes.extend([
                f"Antrenman öncesi: {float(pre_workout_carbs):.1f}g karbonhidrat (1-2 saat önce)",
                f"Antrenman sonrası: {float(post_workout_protein):.1f}g protein (30 dakika içinde)",
                "Antrenman sırasında: 150-250ml su her 15-20 dakikada"
            ])
        else:
            timing_notes.append("Dinlenme günü: Düzenli öğün zamanlarını koruyun")
        
        return TrainingDayRecommendation(
            is_training_day=is_training_day,
            recommended_calories=Decimal(str(daily_calories)),
            macros=macros,
            pre_workout_carbs=pre_workout_carbs,
            post_workout_protein=post_workout_protein,
            hydration_ml=base_hydration,
            timing_notes=timing_notes
        )
    
    # ------------------------------------------------------------------
    # Yardımcı Metodlar
    # ------------------------------------------------------------------
    
    async def _get_sport_profile(self, user_id: int, db: AsyncSession) -> Optional[SportProfile]:
        """Kullanıcının spor profilini getirir."""
        stmt = select(SportProfile).where(SportProfile.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_user_profile(self, user_id: int, db: AsyncSession) -> UserProfile:
        """Kullanıcı profilini getirir."""
        stmt = select(UserProfile).where(UserProfile.id == user_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            raise ValueError(f"User profile not found for user_id: {user_id}")
        return profile
    
    async def _get_recent_workouts(self, user_id: int, db: AsyncSession, days: int = 7) -> List[WorkoutLog]:
        """Son N gündeki antrenmanları getirir."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stmt = (
            select(WorkoutLog)
            .where(
                WorkoutLog.completed_at >= cutoff_date
            )
            .order_by(WorkoutLog.completed_at.desc())
        )
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def _is_training_day(self, user_id: int, target_date: date, db: AsyncSession) -> bool:
        """Belirli bir günün antrenman günü olup olmadığını kontrol eder."""
        # Spor profili al
        sport_profile = await self._get_sport_profile(user_id, db)
        
        if not sport_profile:
            # Varsayılan: Pazartesi, Çarşamba, Cuma
            return target_date.weekday() in [0, 2, 4]
        
        # Haftalık antrenman sıklığına göre
        training_frequency = sport_profile.training_frequency
        
        # Basit algoritma: Haftanın ilk N günü antrenman
        return target_date.weekday() < training_frequency
    
    def _normalize_goal(self, goal: str) -> str:
        """Hedef tipini normalize eder."""
        goal_mapping = {
            "lose": "weight_loss",
            "lose_fast": "weight_loss",
            "cut": "cut",
            "maintain": "maintenance",
            "gain": "muscle_gain",
            "gain_fast": "bulk",
            "bulk": "bulk",
            "recomp": "lean_gain"
        }
        
        return goal_mapping.get(goal, "maintenance")
    
    def _generate_macro_rationale(self, sport_type: SportType, goal: str) -> str:
        """Makro oranları için açıklama oluşturur."""
        rationales = {
            (SportType.STRENGTH, "muscle_gain"): "Güç antrenmanı için yüksek protein ve karbonhidrat",
            (SportType.STRENGTH, "cut"): "Kas koruma için çok yüksek protein, kontrollü karbonhidrat",
            (SportType.ENDURANCE, "performance"): "Dayanıklılık için yüksek karbonhidrat, orta protein",
            (SportType.POWERLIFTING, "strength"): "Maksimal güç için çok yüksek protein, orta karbonhidrat",
            (SportType.BODYBUILDING, "bulk"): "Kas büyümesi için yüksek protein ve karbonhidrat",
            (SportType.BODYBUILDING, "cut"): "Tanımlama için çok yüksek protein, düşük yağ",
            (SportType.CROSSFIT, "performance"): "Fonksiyonel fitness için dengeli makrolar"
        }
        
        return rationales.get((sport_type, goal), "Genel fitness hedefleri için dengeli makro dağılımı")


# ---------------------------------------------------------------------------
# Global Instance
# ---------------------------------------------------------------------------

# Singleton instance
sport_target_engine = SportTargetEngine()