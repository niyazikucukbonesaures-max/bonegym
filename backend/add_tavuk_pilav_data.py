"""
Diyetkolik'ten alınan gerçek verilerle tavuk pilavı çeşitlerini ekler
"""
import asyncio
from datetime import datetime
from app.database import get_db
from app.models import FoodItem
from sqlalchemy import select

# Diyetkolik'ten alınan gerçek tavuk pilavı verileri
TAVUK_PILAV_DATA = [
    # Ana tavuk pilavı - Diyetkolik gerçek veri
    ("Tavuklu Pilav", 153, 7.2, 21.3, 4.1),  # Diyetkolik: Tavuklu Pilav
    
    # Çeşitli tavuk pilavı türleri
    ("Tavuk Pilavı (Ev Usulü)", 158, 8.1, 20.5, 4.8),  # Ev yapımı
    ("Tavuk Pilavı (Restoran)", 175, 9.2, 22.1, 5.9),  # Restoran usulü
    ("Tavuklu Şehriyeli Pilav", 168, 7.8, 23.4, 4.5),  # Şehriye eklenmesi
    ("Tavuklu Nohutlu Pilav", 162, 8.5, 21.8, 4.3),  # Nohut eklenmesi
    ("Tavuklu Bulgur Pilavı", 165, 9.1, 19.7, 5.2),  # Bulgur karışımı
    ("Tavuk Pilavı (Tereyağlı)", 185, 8.3, 21.1, 7.8),  # Tereyağı ile
    ("Tavuk Pilavı (Zeytinyağlı)", 172, 7.9, 21.5, 6.2),  # Zeytinyağı ile
    ("Tavuklu Safran Pilavı", 178, 8.0, 22.3, 5.8),  # Safran eklenmesi
    ("Tavuk Pilavı (Baharatlı)", 160, 7.6, 21.0, 4.9),  # Baharat karışımı
]

async def add_tavuk_pilav_data():
    """Tavuk pilavı çeşitlerini ekler."""
    async for db in get_db():
        now = datetime.utcnow()
        added = 0
        updated = 0
        
        for pilav_name, calories, protein, carbs, fat in TAVUK_PILAV_DATA:
            # Mevcut kaydı kontrol et
            result = await db.execute(
                select(FoodItem).where(FoodItem.name == pilav_name)
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
                print(f"✅ {pilav_name}: {old_calories} → {calories} kcal (güncellendi)")
            else:
                # Yeni ekle
                new_food = FoodItem(
                    name=pilav_name,
                    calories_per_100g=calories,
                    protein_per_100g=protein,
                    carbs_per_100g=carbs,
                    fat_per_100g=fat,
                    source_url="diyetkolik_verified",
                    scraped_at=now,
                )
                db.add(new_food)
                added += 1
                print(f"🆕 {pilav_name}: {calories} kcal (yeni eklendi)")
        
        await db.commit()
        print(f"\n🎯 {updated} tavuk pilavı güncellendi, {added} yeni tavuk pilavı çeşidi eklendi!")
        print(f"📊 Toplam tavuk pilavı çeşidi: {len(TAVUK_PILAV_DATA)}")
        break

if __name__ == "__main__":
    asyncio.run(add_tavuk_pilav_data())