# Akıllı Yemek Planlayıcı Servisi
# Kullanıcının hedefine göre haftalık menü önerir
# Optimize edilmiş: Hedefe göre protein/makro dengesi

from datetime import date, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import random

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FoodItem, UserProfile
from app.calorie_engine import CalorieEngine


@dataclass
class MealSuggestion:
    """Tek bir öğün önerisi"""
    meal_type: str  # breakfast, lunch, dinner, snack
    food_name: str
    grams: float
    calories: float
    protein: float
    carbs: float
    fat: float
    protein_ratio: float  # Protein oranı (%)


@dataclass
class DayPlan:
    """Bir günlük yemek planı"""
    date: str
    meals: List[MealSuggestion]
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    protein_percentage: float  # Günlük protein yüzdesi


@dataclass
class WeeklyMealPlan:
    """Haftalık yemek planı"""
    days: List[DayPlan]
    shopping_list: Dict[str, float]  # food_name -> total_grams
    goal_info: Dict[str, any]  # Hedef bilgileri


class MealPlanner:
    """Akıllı yemek planlayıcı - Hedefe göre optimize edilmiş"""
    
    def __init__(self):
        self.meal_types = ["breakfast", "lunch", "dinner", "snack"]
        
        # Hedefe göre öğün dağılımı
        self.meal_distributions = {
            "kilo_verme": {
                "breakfast": 0.25,
                "lunch": 0.35,
                "dinner": 0.30,
                "snack": 0.10,
            },
            "kas_kazanma": {
                "breakfast": 0.30,
                "lunch": 0.30,
                "dinner": 0.30,
                "snack": 0.10,
            },
            "vucut_rekomposizyonu": {
                "breakfast": 0.25,
                "lunch": 0.35,
                "dinner": 0.30,
                "snack": 0.10,
            },
            "kilo_koruma": {
                "breakfast": 0.25,
                "lunch": 0.35,
                "dinner": 0.30,
                "snack": 0.10,
            }
        }
    
    async def generate_weekly_plan(
        self, 
        db: AsyncSession, 
        user_id: int = 1
    ) -> WeeklyMealPlan:
        """Kullanıcı için haftalık yemek planı oluşturur"""
        
        # 1. Kullanıcı profilini al
        profile = await self._get_user_profile(db)
        if not profile:
            raise ValueError("Kullanıcı profili bulunamadı")
        
        # 2. BMI hesapla ve hedef uygunluğunu kontrol et
        bmi = self._calculate_bmi(profile.weight_kg, profile.height_cm)
        goal_warning = self._check_goal_suitability(bmi, profile.goal)
        
        # 3. Günlük kalori ve makro hedeflerini hesapla
        daily_target = self._calculate_daily_targets(profile)
        
        # 4. Hedefe göre besin kategorilerini al
        food_categories = await self._get_categorized_foods(db, profile.goal)
        
        # 5. 7 günlük plan oluştur
        days = []
        shopping_list: Dict[str, float] = {}
        
        start_date = date.today()
        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            day_plan = self._generate_day_plan(
                current_date, 
                food_categories, 
                daily_target,
                profile.goal
            )
            days.append(day_plan)
            
            # Alışveriş listesine ekle
            for meal in day_plan.meals:
                if meal.food_name in shopping_list:
                    shopping_list[meal.food_name] += meal.grams
                else:
                    shopping_list[meal.food_name] = meal.grams
        
        # Hedef bilgileri
        goal_info = {
            "goal": profile.goal,
            "goal_name": self._get_goal_name(profile.goal),
            "daily_calories": daily_target["calories"],
            "daily_protein": daily_target["protein"],
            "daily_carbs": daily_target["carbs"],
            "daily_fat": daily_target["fat"],
            "protein_ratio": daily_target["protein_ratio"],
            "carbs_ratio": daily_target["carbs_ratio"],
            "fat_ratio": daily_target["fat_ratio"],
            "bmi": round(bmi, 1),
            "goal_warning": goal_warning,
        }
        
        return WeeklyMealPlan(days=days, shopping_list=shopping_list, goal_info=goal_info)
    
    async def _get_user_profile(self, db: AsyncSession) -> Optional[UserProfile]:
        """Kullanıcı profilini getirir"""
        stmt = select(UserProfile).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    def _calculate_daily_targets(self, profile: UserProfile) -> Dict[str, float]:
        """Günlük kalori ve makro hedeflerini hesaplar"""
        bmr = CalorieEngine.calculate_bmr(
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            age=profile.age,
            gender=profile.gender
        )
        tdee = CalorieEngine.calculate_tdee(bmr, profile.activity_level)
        target_calories = CalorieEngine.get_recommended_calories(tdee, profile.goal)
        
        # Makro hedefleri (hedefe göre optimize edilmiş)
        if profile.goal == "vucut_rekomposizyonu":
            protein_ratio = 0.40  # %40 protein (yüksek)
            carbs_ratio = 0.35    # %35 karb
            fat_ratio = 0.25      # %25 yağ
        elif profile.goal == "kas_kazanma":
            # KAS KAZANMA = KİLO ALMA (Kas + Yağ)
            protein_ratio = 0.35  # %35 protein
            carbs_ratio = 0.45    # %45 karb (enerji + kilo alma)
            fat_ratio = 0.20      # %20 yağ
        elif profile.goal == "kilo_verme":
            protein_ratio = 0.35  # %35 protein (kas koruma)
            carbs_ratio = 0.35    # %35 karb
            fat_ratio = 0.30      # %30 yağ
        else:  # kilo_koruma
            protein_ratio = 0.30
            carbs_ratio = 0.40
            fat_ratio = 0.30
        
        return {
            "calories": target_calories,
            "protein": (target_calories * protein_ratio) / 4,
            "carbs": (target_calories * carbs_ratio) / 4,
            "fat": (target_calories * fat_ratio) / 9,
            "protein_ratio": protein_ratio,
            "carbs_ratio": carbs_ratio,
            "fat_ratio": fat_ratio,
        }
    
    async def _get_categorized_foods(
        self, 
        db: AsyncSession, 
        goal: str
    ) -> Dict[str, List[FoodItem]]:
        """Hedefe göre kategorize edilmiş yiyecekleri getirir"""
        
        # Yüksek protein (>20g/100g)
        high_protein_stmt = select(FoodItem).where(
            FoodItem.protein_per_100g >= 20
        ).order_by(func.random()).limit(30)
        
        # Orta protein (10-20g/100g)
        medium_protein_stmt = select(FoodItem).where(
            and_(
                FoodItem.protein_per_100g >= 10,
                FoodItem.protein_per_100g < 20
            )
        ).order_by(func.random()).limit(30)
        
        # Düşük protein (<10g/100g) - karbonhidrat kaynakları
        low_protein_stmt = select(FoodItem).where(
            FoodItem.protein_per_100g < 10
        ).order_by(func.random()).limit(30)
        
        # Sağlıklı yağ kaynakları (yüksek yağ, düşük karb)
        healthy_fat_stmt = select(FoodItem).where(
            and_(
                FoodItem.fat_per_100g >= 10,
                FoodItem.carbs_per_100g < 20
            )
        ).order_by(func.random()).limit(20)
        
        high_protein_result = await db.execute(high_protein_stmt)
        medium_protein_result = await db.execute(medium_protein_stmt)
        low_protein_result = await db.execute(low_protein_stmt)
        healthy_fat_result = await db.execute(healthy_fat_stmt)
        
        return {
            "high_protein": list(high_protein_result.scalars().all()),
            "medium_protein": list(medium_protein_result.scalars().all()),
            "low_protein": list(low_protein_result.scalars().all()),
            "healthy_fat": list(healthy_fat_result.scalars().all()),
        }
    
    def _generate_day_plan(
        self,
        current_date: date,
        food_categories: Dict[str, List[FoodItem]],
        daily_target: Dict[str, float],
        goal: str
    ) -> DayPlan:
        """Bir günlük yemek planı oluşturur - Hedefe göre optimize edilmiş"""
        
        # Öğün başına kalori dağılımı (hedefe göre)
        meal_distribution = self.meal_distributions.get(goal, self.meal_distributions["kilo_koruma"])
        
        meals = []
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        # Hedefe göre yemek seçim stratejisi
        for meal_type, ratio in meal_distribution.items():
            target_calories = daily_target["calories"] * ratio
            target_protein = daily_target["protein"] * ratio
            
            # Öğün için yemek seçimi
            meal_foods = self._select_foods_for_meal(
                meal_type,
                target_calories,
                target_protein,
                food_categories,
                goal
            )
            
            for food, grams in meal_foods:
                # Makroları hesapla
                calories = (food.calories_per_100g * grams) / 100
                protein = (food.protein_per_100g * grams) / 100
                carbs = (food.carbs_per_100g * grams) / 100
                fat = (food.fat_per_100g * grams) / 100
                
                # Protein oranı
                protein_ratio = (protein * 4 / calories * 100) if calories > 0 else 0
                
                meal = MealSuggestion(
                    meal_type=meal_type,
                    food_name=food.name,
                    grams=round(grams, 1),
                    calories=round(calories, 1),
                    protein=round(protein, 1),
                    carbs=round(carbs, 1),
                    fat=round(fat, 1),
                    protein_ratio=round(protein_ratio, 1)
                )
                meals.append(meal)
                
                total_calories += calories
                total_protein += protein
                total_carbs += carbs
                total_fat += fat
        
        # Günlük protein yüzdesi
        protein_percentage = (total_protein * 4 / total_calories * 100) if total_calories > 0 else 0
        
        return DayPlan(
            date=current_date.isoformat(),
            meals=meals,
            total_calories=round(total_calories, 1),
            total_protein=round(total_protein, 1),
            total_carbs=round(total_carbs, 1),
            total_fat=round(total_fat, 1),
            protein_percentage=round(protein_percentage, 1)
        )
    
    def _select_foods_for_meal(
        self,
        meal_type: str,
        target_calories: float,
        target_protein: float,
        food_categories: Dict[str, List[FoodItem]],
        goal: str
    ) -> List[tuple[FoodItem, float]]:
        """Öğün için yemek seçer - Hedefe göre optimize edilmiş"""
        
        selected_foods = []
        
        # Öğün başına yemek sayısı
        foods_per_meal = 2 if meal_type == "snack" else 3
        
        # Hedefe göre kategori ağırlıkları
        if goal == "vucut_rekomposizyonu":
            # Yüksek protein odaklı (Yağ yak + Kas koru)
            categories = ["high_protein"] * 2 + ["medium_protein"]
        elif goal == "kas_kazanma":
            # KAS KAZANMA = KİLO ALMA
            # Protein + Karbonhidrat dengeli (Kas yap + Kilo al)
            categories = ["high_protein", "medium_protein", "low_protein"]
        elif goal == "kilo_verme":
            # Protein + düşük kalori (Yağ yak + Kas koru)
            categories = ["high_protein", "medium_protein", "healthy_fat"]
        else:
            # Dengeli beslenme
            categories = ["high_protein", "medium_protein", "low_protein"]
        
        # Rastgele karıştır
        random.shuffle(categories)
        
        for i in range(foods_per_meal):
            category = categories[i % len(categories)]
            foods = food_categories.get(category, [])
            
            if not foods:
                continue
            
            # Rastgele yemek seç
            food = random.choice(foods)
            
            # Gram hesapla (hedef kaloriye göre)
            target_per_food = target_calories / foods_per_meal
            grams = (target_per_food / food.calories_per_100g) * 100
            
            # Minimum ve maksimum gram sınırları
            grams = max(50, min(grams, 500))  # 50g - 500g arası
            
            selected_foods.append((food, grams))
        
        return selected_foods
    
    def _get_goal_name(self, goal: str) -> str:
        """Hedef adını Türkçe döndürür"""
        goal_names = {
            "kilo_verme": "Kilo Verme (Yağ Yak)",
            "kas_kazanma": "Kas Kazanma (Kilo Al)",
            "vucut_rekomposizyonu": "Vücut Rekomposizyonu (Yağ Yak + Kas Koru)",
            "kilo_koruma": "Kilo Koruma (Dengeli Beslenme)"
        }
        return goal_names.get(goal, "Bilinmeyen")
    
    def _calculate_bmi(self, weight_kg: float, height_cm: float) -> float:
        """BMI hesaplar"""
        height_m = height_cm / 100
        return weight_kg / (height_m * height_m)
    
    def _check_goal_suitability(self, bmi: float, goal: str) -> Optional[Dict[str, str]]:
        """
        Hedefin BMI'ye uygunluğunu kontrol eder
        
        Returns:
            Uyarı varsa dict, yoksa None
        """
        # BMI kategorileri
        if bmi < 16:
            category = "Ciddi Zayıflık"
            if goal in ["kilo_verme", "vucut_rekomposizyonu"]:
                return {
                    "type": "error",
                    "title": "⚠️ Uyarı: Yanlış Hedef!",
                    "message": f"BMI: {bmi:.1f} - {category}. Kilo ALMALISINIZ! Lütfen hedefini '💪 Kas Kazanma (Kilo Al)' olarak değiştirin.",
                    "recommended_goal": "kas_kazanma",
                    "recommended_goal_name": "💪 Kas Kazanma (Kilo Al)"
                }
        elif bmi < 18.5:
            category = "Zayıf"
            if goal in ["kilo_verme", "vucut_rekomposizyonu"]:
                return {
                    "type": "warning",
                    "title": "⚠️ Dikkat: Uygun Olmayan Hedef",
                    "message": f"BMI: {bmi:.1f} - {category}. Kilo almanız önerilir. Hedefini '💪 Kas Kazanma (Kilo Al)' olarak değiştirmeyi düşünün.",
                    "recommended_goal": "kas_kazanma",
                    "recommended_goal_name": "💪 Kas Kazanma (Kilo Al)"
                }
        elif bmi >= 30:
            category = "Obez"
            if goal == "kas_kazanma":
                return {
                    "type": "warning",
                    "title": "⚠️ Dikkat: Uygun Olmayan Hedef",
                    "message": f"BMI: {bmi:.1f} - {category}. Önce kilo vermeniz önerilir. Hedefini '🔥 Kilo Verme (Yağ Yak)' olarak değiştirmeyi düşünün.",
                    "recommended_goal": "kilo_verme",
                    "recommended_goal_name": "🔥 Kilo Verme (Yağ Yak)"
                }
        
        return None  # Hedef uygun
