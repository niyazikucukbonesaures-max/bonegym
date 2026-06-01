# Yemek Planlayıcı Router'ı
# GET /meal-plan/weekly → Haftalık plan oluştur
# Optimize edilmiş: Hedefe göre protein/makro dengesi

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.meal_planner import MealPlanner, WeeklyMealPlan

router = APIRouter()


@router.get("/weekly", response_model=dict)
async def get_weekly_meal_plan(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Kullanıcı için haftalık yemek planı oluşturur
    
    Hedefe göre optimize edilmiş:
    - Kilo Verme: %35 protein, %35 karb, %30 yağ
    - Kas Kazanma: %35 protein, %45 karb, %20 yağ
    - Vücut Rekomposizyonu: %40 protein, %35 karb, %25 yağ
    - Kilo Koruma: %30 protein, %40 karb, %30 yağ
    """
    planner = MealPlanner()
    plan = await planner.generate_weekly_plan(db)
    
    # WeeklyMealPlan'ı dict'e çevir
    return {
        "goal_info": plan.goal_info,
        "days": [
            {
                "date": day.date,
                "meals": [
                    {
                        "meal_type": meal.meal_type,
                        "food_name": meal.food_name,
                        "grams": meal.grams,
                        "calories": meal.calories,
                        "protein": meal.protein,
                        "carbs": meal.carbs,
                        "fat": meal.fat,
                        "protein_ratio": meal.protein_ratio,
                    }
                    for meal in day.meals
                ],
                "total_calories": day.total_calories,
                "total_protein": day.total_protein,
                "total_carbs": day.total_carbs,
                "total_fat": day.total_fat,
                "protein_percentage": day.protein_percentage,
            }
            for day in plan.days
        ],
        "shopping_list": plan.shopping_list,
    }
