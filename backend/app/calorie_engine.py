# Fitness ve Kalori Takip Uygulaması - Kalori Hesaplama Motoru
# Mifflin-St Jeor BMR formülü, TDEE, makro hesaplama ve günlük günlük yönetimi.

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FoodLog, FoodItem
from app.schemas import DailySummary, FoodLogCreate, FoodLogEntrySchema


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------

@dataclass
class MacroResult:
    """Belirli gram miktarı için hesaplanan makro besin değerleri."""
    calories: float
    protein: float
    carbs: float
    fat: float


@dataclass
class MacroTargets:
    """Günlük kalori hedefine göre hesaplanan makro besin hedefleri (gram)."""
    protein_g: float
    carbs_g: float
    fat_g: float


# ---------------------------------------------------------------------------
# Aktivite Katsayıları
# ---------------------------------------------------------------------------

ACTIVITY_MULTIPLIERS: dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

# ---------------------------------------------------------------------------
# Hedef Bazlı Kalori Ayarlamaları
# ---------------------------------------------------------------------------

# Türkçe -> İngilizce goal mapping
GOAL_MAPPING: dict[str, str] = {
    "kilo_verme": "lose",
    "koruma": "maintain",
    "kas_kazanma": "gain",
    "vucut_rekomposizyonu": "recomp",
}

GOAL_ADJUSTMENTS: dict[str, float] = {
    "lose": -500.0,
    "maintain": 0.0,
    "gain": 300.0,
    "recomp": -250.0,  # Vücut rekomposizyonu: hafif kalori açığı
}


# ---------------------------------------------------------------------------
# CalorieEngine
# ---------------------------------------------------------------------------

class CalorieEngine:
    """Kalori ve makro besin hesaplama motoru."""

    # ------------------------------------------------------------------
    # Statik Hesaplama Metodları
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
        """Mifflin-St Jeor formülüyle BMR hesaplar.

        Args:
            weight_kg: Vücut ağırlığı (kg)
            height_cm: Boy (cm)
            age: Yaş
            gender: Cinsiyet ("male" | "female")

        Returns:
            BMR değeri (kalori/gün)
        """
        base = 10 * weight_kg + 6.25 * height_cm - 5 * age
        if gender == "male":
            return base + 5
        else:
            return base - 161

    @staticmethod
    def calculate_tdee(bmr: float, activity_level: str) -> float:
        """BMR ve aktivite seviyesine göre TDEE hesaplar.

        Args:
            bmr: Bazal Metabolizma Hızı
            activity_level: Aktivite seviyesi ("sedentary" | "light" | "moderate" | "active" | "very_active")

        Returns:
            TDEE değeri (kalori/gün)
        """
        multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, ACTIVITY_MULTIPLIERS["sedentary"])
        return bmr * multiplier

    @staticmethod
    def calculate_macros(
        calories_per_100g: float,
        protein_per_100g: float,
        carbs_per_100g: float,
        fat_per_100g: float,
        grams: float,
    ) -> MacroResult:
        """Gram miktarına göre makro besin değerlerini hesaplar.

        Args:
            calories_per_100g: 100g başına kalori
            protein_per_100g: 100g başına protein (g)
            carbs_per_100g: 100g başına karbonhidrat (g)
            fat_per_100g: 100g başına yağ (g)
            grams: Tüketilen miktar (g)

        Returns:
            MacroResult: Hesaplanan kalori ve makro değerleri

        Raises:
            ValueError: grams sıfır veya negatifse
        """
        if grams <= 0:
            raise ValueError(f"Gram miktarı sıfırdan büyük olmalıdır, alınan: {grams}")

        ratio = grams / 100.0
        return MacroResult(
            calories=calories_per_100g * ratio,
            protein=protein_per_100g * ratio,
            carbs=carbs_per_100g * ratio,
            fat=fat_per_100g * ratio,
        )

    @staticmethod
    def get_recommended_calories(tdee: float, goal: str) -> float:
        """Hedefe göre önerilen günlük kalori miktarını hesaplar.

        Args:
            tdee: Toplam Günlük Enerji Harcaması
            goal: Hedef (Türkçe veya İngilizce: "kilo_verme"/"lose" | "koruma"/"maintain" | "kas_kazanma"/"gain" | "vucut_rekomposizyonu"/"recomp")

        Returns:
            Önerilen günlük kalori miktarı
        """
        # Türkçe goal'ü İngilizce'ye çevir
        english_goal = GOAL_MAPPING.get(goal, goal)
        adjustment = GOAL_ADJUSTMENTS.get(english_goal, 0.0)
        return tdee + adjustment

    @staticmethod
    def get_macro_targets(daily_calories: float, goal: str = "maintain") -> MacroTargets:
        """Günlük kalori hedefine göre makro besin hedeflerini hesaplar.

        Dağılım:
          - Normal hedefler:
            - Protein: %30 → gram = (calories * 0.30) / 4
            - Karbonhidrat: %40 → gram = (calories * 0.40) / 4
            - Yağ: %30 → gram = (calories * 0.30) / 9
          - Vücut Rekomposizyonu (recomp):
            - Protein: %40 → gram = (calories * 0.40) / 4 (yüksek protein)
            - Karbonhidrat: %35 → gram = (calories * 0.35) / 4
            - Yağ: %25 → gram = (calories * 0.25) / 9

        Args:
            daily_calories: Günlük kalori hedefi
            goal: Hedef (Türkçe veya İngilizce: "kilo_verme"/"lose" | "koruma"/"maintain" | "kas_kazanma"/"gain" | "vucut_rekomposizyonu"/"recomp")

        Returns:
            MacroTargets: Protein, karbonhidrat ve yağ hedefleri (gram)
        """
        # Türkçe goal'ü İngilizce'ye çevir
        english_goal = GOAL_MAPPING.get(goal, goal)
        
        if english_goal == "recomp":
            # Vücut rekomposizyonu için yüksek protein
            return MacroTargets(
                protein_g=(daily_calories * 0.40) / 4,
                carbs_g=(daily_calories * 0.35) / 4,
                fat_g=(daily_calories * 0.25) / 9,
            )
        else:
            # Normal dağılım
            return MacroTargets(
                protein_g=(daily_calories * 0.30) / 4,
                carbs_g=(daily_calories * 0.40) / 4,
                fat_g=(daily_calories * 0.30) / 9,
            )

    # ------------------------------------------------------------------
    # Async Veritabanı Metodları
    # ------------------------------------------------------------------

    async def get_daily_total(
        self, db: AsyncSession, user_id: int, target_date: date
    ) -> DailySummary:
        """Belirli bir tarih için günlük kalori ve makro özetini döndürür.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si
            target_date: Sorgulanacak tarih

        Returns:
            DailySummary: Günlük toplam ve giriş listesi
        """
        # Tarih aralığı: gün başı → gün sonu (timezone-naive, DB ile uyumlu)
        day_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=timezone.utc)
        day_end = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, 999999, tzinfo=timezone.utc)

        stmt = (
            select(FoodLog)
            .where(
                FoodLog.user_id == user_id,
                FoodLog.logged_at >= day_start,
                FoodLog.logged_at <= day_end,
            )
            .order_by(FoodLog.logged_at)
        )
        result = await db.execute(stmt)
        entries = result.scalars().all()

        total_calories = sum(e.calories for e in entries)
        total_protein = sum(e.protein for e in entries)
        total_carbs = sum(e.carbs for e in entries)
        total_fat = sum(e.fat for e in entries)

        return DailySummary(
            date=target_date.isoformat(),
            total_calories=total_calories,
            total_protein=total_protein,
            total_carbs=total_carbs,
            total_fat=total_fat,
            entries=[FoodLogEntrySchema.model_validate(e) for e in entries],
        )

    async def add_food_log(self, db: AsyncSession, entry: FoodLogCreate) -> FoodLog:
        """Kalori günlüğüne yeni bir giriş ekler.

        Besin öğesinin makro değerlerini veritabanından çeker ve
        girilen gram miktarına göre hesaplar.

        Args:
            db: Async veritabanı oturumu
            entry: Yeni günlük girişi

        Returns:
            FoodLog: Oluşturulan veritabanı kaydı

        Raises:
            ValueError: Gram miktarı sıfır veya negatifse
            ValueError: Besin öğesi bulunamazsa
        """
        if entry.grams <= 0:
            raise ValueError(f"Gram miktarı sıfırdan büyük olmalıdır, alınan: {entry.grams}")

        # Besin öğesini veritabanından çek
        food_item: Optional[FoodItem] = None
        if entry.food_item_id is not None:
            stmt = select(FoodItem).where(FoodItem.id == entry.food_item_id)
            result = await db.execute(stmt)
            food_item = result.scalar_one_or_none()

        # Makro değerleri hesapla
        if food_item is not None:
            macros = self.calculate_macros(
                calories_per_100g=food_item.calories_per_100g,
                protein_per_100g=food_item.protein_per_100g,
                carbs_per_100g=food_item.carbs_per_100g,
                fat_per_100g=food_item.fat_per_100g,
                grams=entry.grams,
            )
        elif (
            entry.calories_per_100g is not None
            and entry.protein_per_100g is not None
            and entry.carbs_per_100g is not None
            and entry.fat_per_100g is not None
        ):
            # AI asistanından gelen makro değerleri kullan
            macros = self.calculate_macros(
                calories_per_100g=entry.calories_per_100g,
                protein_per_100g=entry.protein_per_100g,
                carbs_per_100g=entry.carbs_per_100g,
                fat_per_100g=entry.fat_per_100g,
                grams=entry.grams,
            )
        else:
            # Besin öğesi bulunamadıysa sıfır makro ile kaydet
            macros = MacroResult(calories=0.0, protein=0.0, carbs=0.0, fat=0.0)

        log_entry = FoodLog(
            user_id=entry.user_id,
            food_item_id=entry.food_item_id,
            food_name=entry.food_name,
            grams=entry.grams,
            calories=macros.calories,
            protein=macros.protein,
            carbs=macros.carbs,
            fat=macros.fat,
            meal_type=entry.meal_type,
            logged_at=entry.logged_at if entry.logged_at is not None else datetime.now(timezone.utc),
        )
        db.add(log_entry)
        await db.flush()
        await db.refresh(log_entry)
        return log_entry

    async def delete_food_log(self, db: AsyncSession, entry_id: int) -> bool:
        """Kalori günlüğünden bir girişi siler.

        Args:
            db: Async veritabanı oturumu
            entry_id: Silinecek giriş ID'si

        Returns:
            bool: Silme başarılıysa True, kayıt bulunamazsa False
        """
        stmt = select(FoodLog).where(FoodLog.id == entry_id)
        result = await db.execute(stmt)
        entry = result.scalar_one_or_none()

        if entry is None:
            return False

        await db.delete(entry)
        await db.flush()
        return True
