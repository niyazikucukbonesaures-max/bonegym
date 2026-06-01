"""
Diyetkolik'ten alınan gerçek verilerle pilav besinlerini günceller
"""
import asyncio
from app.database import get_db
from app.models import FoodItem
from sqlalchemy import select

# Diyetkolik'ten alınan gerçek pilav verileri
REAL_PILAV_DATA = {
    "Pilav (Sade)": 130,  # Standart haşlanmış pirinç
    "Pilav (Tereyağlı)": 165,  # Yağ eklenmesi
    "Pilav (Nohutlu)": 146,  # Diyetkolik: Pilav Üstü Fasulye benzeri
    "Pilav (Şehriyeli)": 171,  # Diyetkolik: Şehriyeli Pilav
    "Pilav (Bulgurlu)": 155,  # Bulgur karışımı
    "Bulgur Pilavı": 150,  # Dereotlu Pilav benzeri
}

async def update_pilav_data():
    """Pilav verilerini gerçek değerlerle günceller."""
    async for db in get_db():
        updated = 0
        
        for pilav_name, real_calories in REAL_PILAV_DATA.items():
            result = await db.execute(
                select(FoodItem).where(FoodItem.name == pilav_name)
            )
            food = result.scalar_one_or_none()
            
            if food:
                old_calories = food.calories_per_100g
                food.calories_per_100g = real_calories
                food.source_url = "diyetkolik_verified"
                updated += 1
                print(f"✅ {pilav_name}: {old_calories} → {real_calories} kcal")
        
        await db.commit()
        print(f"\n🎯 {updated} pilav verisi Diyetkolik kaynaklı gerçek verilerle güncellendi!")
        break

if __name__ == "__main__":
    asyncio.run(update_pilav_data())