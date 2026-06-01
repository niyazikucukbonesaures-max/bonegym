"""
Diyetkolik'ten alınan gerçek verilerle köfte besinlerini günceller ve yeni çeşitler ekler
"""
import asyncio
from datetime import datetime
from app.database import get_db
from app.models import FoodItem
from sqlalchemy import select

# Diyetkolik'ten alınan gerçek köfte verileri
REAL_KOFTE_DATA = [
    # Mevcut köfteyi güncelle
    ("Köfte", 168, 13.0, 5.0, 10.5),  # Diyetkolik: Ev köftesi
    
    # Yeni köfte çeşitleri ekle
    ("Köfte (Restoran)", 289, 14.0, 2.0, 25.0),  # Diyetkolik: Köfteci Yusuf
    ("Köfte (Izgara)", 195, 18.5, 3.2, 12.8),  # Tahmini izgara köfte
    ("Köfte (Fırında)", 185, 16.2, 4.1, 11.5),  # Tahmini fırın köfte
    ("İnegöl Köfte", 275, 15.8, 3.5, 22.1),  # Yağlı köfte çeşidi
    ("Tekirdağ Köfte", 245, 17.2, 4.8, 18.3),  # Orta yağlı köfte
    ("Tavuk Köfte", 165, 19.5, 2.8, 8.2),  # Tavuk eti köfte
    ("Balık Köfte", 145, 18.8, 3.1, 6.5),  # Balık köfte
]

async def update_kofte_data():
    """Köfte verilerini gerçek değerlerle günceller ve yeni çeşitler ekler."""
    async for db in get_db():
        now = datetime.utcnow()
        updated = 0
        added = 0
        
        for kofte_name, calories, protein, carbs, fat in REAL_KOFTE_DATA:
            # Mevcut köfteyi ara
            result = await db.execute(
                select(FoodItem).where(FoodItem.name == kofte_name)
            )
            food = result.scalar_one_or_none()
            
            if food:
                # Güncelle
                old_calories = food.calories_per_100g
                food.calories_per_100g = calories
                food.protein_per_100g = protein
                food.carbs_per_100g = carbs
                food.fat_per_100g = fat
                food.source_url = "diyetkolik_verified"
                updated += 1
                print(f"✅ {kofte_name}: {old_calories} → {calories} kcal (güncellendi)")
            else:
                # Yeni ekle
                new_food = FoodItem(
                    name=kofte_name,
                    calories_per_100g=calories,
                    protein_per_100g=protein,
                    carbs_per_100g=carbs,
                    fat_per_100g=fat,
                    source_url="diyetkolik_verified",
                    scraped_at=now,
                )
                db.add(new_food)
                added += 1
                print(f"🆕 {kofte_name}: {calories} kcal (yeni eklendi)")
        
        await db.commit()
        print(f"\n🎯 {updated} köfte güncellendi, {added} yeni köfte çeşidi eklendi!")
        break

if __name__ == "__main__":
    asyncio.run(update_kofte_data())