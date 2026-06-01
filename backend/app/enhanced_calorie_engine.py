# Fitness ve Kalori Takip Uygulaması - Gelişmiş Kalori Hesaplama Motoru
# Çift hassasiyet hesaplama, gelişmiş BMR/TDEE formülleri ve spor yapanlara özel özellikler

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FoodLog, FoodItem, UserProfile, SportProfile
from app.schemas import DailySummary, FoodLogCreate, FoodLogEntrySchema


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------

@dataclass
class PrecisionMacroResult:
    """Yüksek hassasiyetli makro besin değerleri."""
    calories: Decimal
    protein: Decimal
    carbs: Decimal
    fat: Decimal
    
    def to_float_dict(self) -> Dict[str, float]:
        """Float değerlere dönüştürür."""
        return {
            "calories": float(self.calories),
            "protein": float(self.protein),
            "carbs": float(self.carbs),
            "fat": float(self.fat)
        }


@dataclass
class EnhancedMacroTargets:
    """Gelişmiş makro besin hedefleri."""
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal
    protein_calories: Decimal
    carbs_calories: Decimal
    fat_calories: Decimal
    total_calories: Decimal
    
    def to_dict(self) -> Dict[str, float]:
        """Dictionary formatına dönüştürür."""
        return {
            "protein_g": float(self.protein_g),
            "carbs_g": float(self.carbs_g),
            "fat_g": float(self.fat_g),
            "protein_calories": float(self.protein_calories),
            "carbs_calories": float(self.carbs_calories),
            "fat_calories": float(self.fat_calories),
            "total_calories": float(self.total_calories)
        }


@dataclass
class BMRCalculationResult:
    """BMR hesaplama sonucu."""
    bmr: Decimal
    formula_used: str
    confidence_score: float
    factors_applied: Dict[str, Any]


# ---------------------------------------------------------------------------
# Sabitler
# ---------------------------------------------------------------------------

# Makro besin kalori katsayıları (kcal/g) - Çift hassasiyet
MACRO_CALORIES_PER_GRAM = {
    "protein": Decimal("4.0"),
    "carbs": Decimal("4.0"),
    "fat": Decimal("9.0")
}

# Aktivite katsayıları - Gelişmiş
ENHANCED_ACTIVITY_MULTIPLIERS = {
    "sedentary": Decimal("1.2"),
    "light": Decimal("1.375"),
    "moderate": Decimal("1.55"),
    "active": Decimal("1.725"),
    "very_active": Decimal("1.9"),
    "extremely_active": Decimal("2.2")  # Yeni kategori
}

# Hedef bazlı kalori ayarlamaları - Gelişmiş
ENHANCED_GOAL_ADJUSTMENTS = {
    "lose": Decimal("-500.0"),
    "lose_fast": Decimal("-750.0"),  # Hızlı kilo verme
    "maintain": Decimal("0.0"),
    "gain": Decimal("300.0"),
    "gain_fast": Decimal("500.0"),  # Hızlı kilo alma
    "recomp": Decimal("-250.0"),  # Vücut rekomposizyonu
    "cut": Decimal("-400.0"),  # Sporcular için cutting
    "bulk": Decimal("400.0")   # Sporcular için bulking
}

# Spor yapanlar için makro oranları
ATHLETE_MACRO_RATIOS = {
    "strength": {"protein": Decimal("0.35"), "carbs": Decimal("0.40"), "fat": Decimal("0.25")},
    "endurance": {"protein": Decimal("0.25"), "carbs": Decimal("0.55"), "fat": Decimal("0.20")},
    "powerlifting": {"protein": Decimal("0.40"), "carbs": Decimal("0.35"), "fat": Decimal("0.25")},
    "bodybuilding": {"protein": Decimal("0.40"), "carbs": Decimal("0.40"), "fat": Decimal("0.20")},
    "crossfit": {"protein": Decimal("0.30"), "carbs": Decimal("0.45"), "fat": Decimal("0.25")},
    "general": {"protein": Decimal("0.30"), "carbs": Decimal("0.40"), "fat": Decimal("0.30")}
}


# ---------------------------------------------------------------------------
# EnhancedCalorieEngine Sınıfı
# ---------------------------------------------------------------------------

class EnhancedCalorieEngine:
    """Gelişmiş kalori ve makro besin hesaplama motoru."""
    
    def __init__(self):
        """Çift hassasiyet için Decimal context ayarları."""
        # Decimal hassasiyeti: 10 ondalık basamak
        self.precision = 10
        
    # ------------------------------------------------------------------
    # Gelişmiş BMR Hesaplama Metodları
    # ------------------------------------------------------------------
    
    def calculate_enhanced_bmr(
        self, 
        weight_kg: float, 
        height_cm: float, 
        age: int, 
        gender: str,
        body_fat_percentage: Optional[float] = None,
        is_athlete: bool = False
    ) -> BMRCalculationResult:
        """Gelişmiş BMR hesaplama - Mifflin-St Jeor + düzeltme faktörleri.
        
        Args:
            weight_kg: Vücut ağırlığı (kg)
            height_cm: Boy (cm)
            age: Yaş
            gender: Cinsiyet ("male" | "female")
            body_fat_percentage: Vücut yağ oranı (opsiyonel)
            is_athlete: Sporcu mu?
            
        Returns:
            BMRCalculationResult: Detaylı BMR hesaplama sonucu
        """
        # Decimal'e dönüştür
        weight = Decimal(str(weight_kg))
        height = Decimal(str(height_cm))
        age_decimal = Decimal(str(age))
        
        # Mifflin-St Jeor formülü (temel)
        base_bmr = Decimal("10") * weight + Decimal("6.25") * height - Decimal("5") * age_decimal
        
        if gender.lower() == "male":
            base_bmr += Decimal("5")
        else:
            base_bmr -= Decimal("161")
        
        factors_applied = {"base_formula": "Mifflin-St Jeor"}
        confidence_score = 0.85
        
        # Vücut yağ oranı düzeltmesi (Katch-McArdle etkisi)
        if body_fat_percentage is not None and 5 <= body_fat_percentage <= 50:
            lean_mass_kg = weight * (Decimal("100") - Decimal(str(body_fat_percentage))) / Decimal("100")
            katch_bmr = Decimal("370") + (Decimal("21.6") * lean_mass_kg)
            
            # İki formülün ağırlıklı ortalaması
            base_bmr = (base_bmr * Decimal("0.7")) + (katch_bmr * Decimal("0.3"))
            factors_applied["body_fat_adjustment"] = f"{body_fat_percentage}%"
            confidence_score = 0.92
        
        # Sporcu düzeltmesi
        if is_athlete:
            athlete_multiplier = Decimal("1.05")  # %5 artış
            base_bmr *= athlete_multiplier
            factors_applied["athlete_adjustment"] = "+5%"
            confidence_score = min(confidence_score + 0.05, 1.0)
        
        # Yaş düzeltmesi (40 yaş üstü için metabolizma yavaşlaması)
        if age > 40:
            age_factor = Decimal("1") - (Decimal(str(age - 40)) * Decimal("0.002"))
            base_bmr *= age_factor
            factors_applied["age_adjustment"] = f"-{(age-40)*0.2:.1f}%"
        
        return BMRCalculationResult(
            bmr=base_bmr.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            formula_used="Enhanced Mifflin-St Jeor",
            confidence_score=confidence_score,
            factors_applied=factors_applied
        )
    
    def calculate_enhanced_tdee(
        self, 
        bmr: Decimal, 
        activity_level: str,
        training_days_per_week: int = 0,
        training_intensity: str = "moderate"
    ) -> Decimal:
        """Gelişmiş TDEE hesaplama.
        
        Args:
            bmr: Bazal Metabolizma Hızı
            activity_level: Aktivite seviyesi
            training_days_per_week: Haftalık antrenman günü sayısı
            training_intensity: Antrenman yoğunluğu
            
        Returns:
            Decimal: TDEE değeri
        """
        # Temel aktivite çarpanı
        base_multiplier = ENHANCED_ACTIVITY_MULTIPLIERS.get(
            activity_level, 
            ENHANCED_ACTIVITY_MULTIPLIERS["sedentary"]
        )
        
        tdee = bmr * base_multiplier
        
        # Antrenman düzeltmesi
        if training_days_per_week > 0:
            training_multipliers = {
                "low": Decimal("0.02"),
                "moderate": Decimal("0.05"),
                "high": Decimal("0.08"),
                "very_high": Decimal("0.12")
            }
            
            training_factor = training_multipliers.get(training_intensity, Decimal("0.05"))
            training_adjustment = Decimal(str(training_days_per_week)) * training_factor
            tdee *= (Decimal("1") + training_adjustment)
        
        return tdee.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    
    # ------------------------------------------------------------------
    # Çift Hassasiyet Makro Hesaplama
    # ------------------------------------------------------------------
    
    def calculate_precision_macros(
        self,
        calories_per_100g: float,
        protein_per_100g: float,
        carbs_per_100g: float,
        fat_per_100g: float,
        grams: float,
    ) -> PrecisionMacroResult:
        """Çift hassasiyetli makro besin hesaplama.
        
        Args:
            calories_per_100g: 100g başına kalori
            protein_per_100g: 100g başına protein (g)
            carbs_per_100g: 100g başına karbonhidrat (g)
            fat_per_100g: 100g başına yağ (g)
            grams: Tüketilen miktar (g)
            
        Returns:
            PrecisionMacroResult: Yüksek hassasiyetli makro değerleri
        """
        if grams <= 0:
            raise ValueError(f"Gram miktarı sıfırdan büyük olmalıdır, alınan: {grams}")
        
        # Decimal'e dönüştür
        calories_100 = Decimal(str(calories_per_100g))
        protein_100 = Decimal(str(protein_per_100g))
        carbs_100 = Decimal(str(carbs_per_100g))
        fat_100 = Decimal(str(fat_per_100g))
        grams_decimal = Decimal(str(grams))
        
        # Oran hesapla
        ratio = grams_decimal / Decimal("100")
        
        # Hassas hesaplama
        calories = calories_100 * ratio
        protein = protein_100 * ratio
        carbs = carbs_100 * ratio
        fat = fat_100 * ratio
        
        # Yuvarlama (0.1 hassasiyetle)
        return PrecisionMacroResult(
            calories=calories.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            protein=protein.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            carbs=carbs.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            fat=fat.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        )
    
    def validate_macro_consistency(self, macros: PrecisionMacroResult) -> bool:
        """Makro besin tutarlılığını kontrol eder.
        
        Protein, karbonhidrat ve yağdan gelen kalorilerin toplamı,
        toplam kalori ile uyumlu olmalıdır (±5% tolerans).
        """
        calculated_calories = (
            macros.protein * MACRO_CALORIES_PER_GRAM["protein"] +
            macros.carbs * MACRO_CALORIES_PER_GRAM["carbs"] +
            macros.fat * MACRO_CALORIES_PER_GRAM["fat"]
        )
        
        # %5 tolerans
        tolerance = macros.calories * Decimal("0.05")
        difference = abs(calculated_calories - macros.calories)
        
        return difference <= tolerance
    
    # ------------------------------------------------------------------
    # Gelişmiş Makro Hedef Hesaplama
    # ------------------------------------------------------------------
    
    async def get_enhanced_macro_targets(
        self, 
        daily_calories: float, 
        goal: str,
        user_id: int,
        db: AsyncSession,
        sport_type: Optional[str] = None
    ) -> EnhancedMacroTargets:
        """Gelişmiş makro besin hedefleri hesaplama.
        
        Args:
            daily_calories: Günlük kalori hedefi
            goal: Hedef (lose, maintain, gain, recomp, vb.)
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            sport_type: Spor tipi (opsiyonel)
            
        Returns:
            EnhancedMacroTargets: Detaylı makro hedefleri
        """
        calories_decimal = Decimal(str(daily_calories))
        
        # Spor profili kontrol et
        sport_profile = await self._get_sport_profile(user_id, db)
        
        # Makro oranlarını belirle
        if sport_profile and sport_profile.is_athlete and sport_type:
            ratios = ATHLETE_MACRO_RATIOS.get(sport_type, ATHLETE_MACRO_RATIOS["general"])
        elif goal == "recomp":
            # Vücut rekomposizyonu için yüksek protein
            ratios = {"protein": Decimal("0.40"), "carbs": Decimal("0.35"), "fat": Decimal("0.25")}
        elif goal in ["cut", "lose", "lose_fast"]:
            # Kilo verme için yüksek protein, düşük yağ
            ratios = {"protein": Decimal("0.35"), "carbs": Decimal("0.45"), "fat": Decimal("0.20")}
        elif goal in ["bulk", "gain", "gain_fast"]:
            # Kilo alma için dengeli makrolar
            ratios = {"protein": Decimal("0.25"), "carbs": Decimal("0.50"), "fat": Decimal("0.25")}
        else:
            # Varsayılan oranlar
            ratios = {"protein": Decimal("0.30"), "carbs": Decimal("0.40"), "fat": Decimal("0.30")}
        
        # Kalori dağılımı
        protein_calories = calories_decimal * ratios["protein"]
        carbs_calories = calories_decimal * ratios["carbs"]
        fat_calories = calories_decimal * ratios["fat"]
        
        # Gram hesaplama
        protein_g = protein_calories / MACRO_CALORIES_PER_GRAM["protein"]
        carbs_g = carbs_calories / MACRO_CALORIES_PER_GRAM["carbs"]
        fat_g = fat_calories / MACRO_CALORIES_PER_GRAM["fat"]
        
        return EnhancedMacroTargets(
            protein_g=protein_g.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            carbs_g=carbs_g.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            fat_g=fat_g.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            protein_calories=protein_calories.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            carbs_calories=carbs_calories.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            fat_calories=fat_calories.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
            total_calories=calories_decimal
        )
    
    def get_enhanced_recommended_calories(
        self, 
        tdee: Decimal, 
        goal: str,
        is_athlete: bool = False
    ) -> Decimal:
        """Gelişmiş kalori önerisi hesaplama.
        
        Args:
            tdee: Toplam Günlük Enerji Harcaması
            goal: Hedef
            is_athlete: Sporcu mu?
            
        Returns:
            Decimal: Önerilen günlük kalori miktarı
        """
        adjustment = ENHANCED_GOAL_ADJUSTMENTS.get(goal, Decimal("0"))
        
        # Sporcu düzeltmesi
        if is_athlete and goal in ["lose", "cut"]:
            # Sporcular için daha konservatif kalori açığı
            adjustment *= Decimal("0.8")
        elif is_athlete and goal in ["gain", "bulk"]:
            # Sporcular için daha kontrollü kalori fazlası
            adjustment *= Decimal("0.9")
        
        recommended_calories = tdee + adjustment
        
        # Minimum kalori kontrolü (BMR'nin %80'i)
        min_calories = tdee * Decimal("0.67")  # Yaklaşık BMR
        
        if recommended_calories < min_calories:
            recommended_calories = min_calories
        
        return recommended_calories.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    
    # ------------------------------------------------------------------
    # Yardımcı Metodlar
    # ------------------------------------------------------------------
    
    async def _get_sport_profile(self, user_id: int, db: AsyncSession) -> Optional[SportProfile]:
        """Kullanıcının spor profilini getirir."""
        stmt = select(SportProfile).where(SportProfile.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    def calculate_macro_percentages(self, macros: PrecisionMacroResult) -> Dict[str, float]:
        """Makro besinlerin yüzde dağılımını hesaplar."""
        if macros.calories == 0:
            return {"protein": 0.0, "carbs": 0.0, "fat": 0.0}
        
        protein_calories = macros.protein * MACRO_CALORIES_PER_GRAM["protein"]
        carbs_calories = macros.carbs * MACRO_CALORIES_PER_GRAM["carbs"]
        fat_calories = macros.fat * MACRO_CALORIES_PER_GRAM["fat"]
        
        return {
            "protein": float((protein_calories / macros.calories) * Decimal("100")),
            "carbs": float((carbs_calories / macros.calories) * Decimal("100")),
            "fat": float((fat_calories / macros.calories) * Decimal("100"))
        }
    
    def round_to_precision(self, value: float, precision: int = 1) -> float:
        """Değeri belirtilen hassasiyete yuvarlar."""
        decimal_value = Decimal(str(value))
        precision_str = "0." + "0" * (precision - 1) + "1"
        return float(decimal_value.quantize(Decimal(precision_str), rounding=ROUND_HALF_UP))


# ---------------------------------------------------------------------------
# Global Instance
# ---------------------------------------------------------------------------

# Singleton instance
enhanced_calorie_engine = EnhancedCalorieEngine()