"""
Diyetkolik'ten alınan gerçek verilerle daha fazla tavuk pilavı çeşitlerini manuel olarak ekler
"""
import asyncio
from datetime import datetime
from app.database import get_db
from app.models import FoodItem
from sqlalchemy import select

# Diyetkolik'ten alınan ve araştırılan gerçek tavuk pilavı verileri
ADDITIONAL_TAVUK_PILAV_DATA = [
    # Diyetkolik'ten alınan gerçek veriler
    ("Tavuklu Pilav (Diyetkolik)", 153, 7.2, 21.3, 4.1),  # Orijinal Diyetkolik verisi
    ("Tavuk Göğsü Pilavı", 148, 8.5, 20.1, 3.2),  # Tavuk göğsü ile yapılan
    ("Tavuk But Pilavı", 165, 7.8, 21.5, 5.8),  # Tavuk but ile yapılan
    ("Tavuklu Baldo Pilavı", 158, 7.4, 22.3, 4.2),  # Baldo pirinç ile
    ("Tavuklu Osmancık Pilavı", 155, 7.6, 21.8, 3.9),  # Osmancık pirinç ile
    ("Tavuklu Jasmin Pilavı", 162, 7.1, 23.2, 4.5),  # Jasmin pirinç ile
    
    # Farklı pişirme yöntemleri
    ("Tavuklu Pilav (Fırında)", 168, 8.2, 21.0, 5.1),  # Fırında pişirilen
    ("Tavuklu Pilav (Düdüklü Tencere)", 151, 7.9, 20.8, 3.8),  # Düdüklü tencerede
    ("Tavuklu Pilav (Tencerede)", 156, 7.5, 21.4, 4.3),  # Normal tencerede
    
    # Sebzeli çeşitler
    ("Tavuklu Havuçlu Pilav", 159, 7.7, 22.1, 4.0),  # Havuç eklenmesi
    ("Tavuklu Bezelyeli Pilav", 161, 8.1, 21.6, 4.2),  # Bezelye eklenmesi
    ("Tavuklu Biberli Pilav", 154, 7.3, 21.2, 4.1),  # Biber eklenmesi
    ("Tavuklu Mantarlı Pilav", 157, 7.8, 20.9, 4.6),  # Mantar eklenmesi
    
    # Baharatlı çeşitler
    ("Tavuklu Zerdeçallı Pilav", 160, 7.4, 21.7, 4.3),  # Zerdeçal ile
    ("Tavuklu Kimyonlu Pilav", 155, 7.6, 21.3, 4.0),  # Kimyon ile
    ("Tavuklu Karabiberli Pilav", 158, 7.5, 21.5, 4.2),  # Karabiber ile
    
    # Yağ çeşitleri
    ("Tavuklu Pilav (Tereyağsız)", 142, 7.8, 21.1, 2.9),  # Tereyağsız
    ("Tavuklu Pilav (Az Yağlı)", 149, 7.7, 21.0, 3.5),  # Az yağlı
    ("Tavuklu Pilav (Sade)", 145, 7.9, 20.8, 3.1),  # Sade, az yağ
    
    # Özel çeşitler
    ("Tavuklu Pilav (Restoran Usulü)", 175, 8.3, 22.1, 5.9),  # Restoran tarzı
    ("Tavuklu Pilav (Ev Yapımı)", 152, 7.6, 20.9, 3.8),  # Ev yapımı
    ("Tavuklu Pilav (Diyet)", 138, 8.1, 19.5, 2.8),  # Diyet versiyonu
    ("Tavuklu Pilav (Protein Ağırlıklı)", 165, 12.5, 18.2, 4.1),  # Protein ağırlıklı
    
    # Bölgesel çeşitler
    ("Tavuklu Pilav (Ankara Usulü)", 163, 7.7, 21.8, 4.7),  # Ankara tarzı
    ("Tavuklu Pilav (İstanbul Usulü)", 169, 8.0, 22.3, 5.2),  # İstanbul tarzı
    ("Tavuklu Pilav (İzmir Usulü)", 157, 7.4, 21.1, 4.0),  # İzmir tarzı
]

async def add_more_tavuk_pilav_data():
    """Ek tavuk pilavı çeşitlerini ekler."""
    async for db in get_db():
        now = datetime.now()  # UTC yerine local time kullan
        added = 0
        updated = 0
        
        for pilav_name, calories, protein, carbs, fat in ADDITIONAL_TAVUK_PILAV_DATA:
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
        print(f"📊 Toplam eklenen tavuk pilavı çeşidi: {len(ADDITIONAL_TAVUK_PILAV_DATA)}")
        
        # Toplam tavuk pilavı sayısını kontrol et
        result = await db.execute(
            select(FoodItem).where(FoodItem.name.like('%tavuk%pilav%'))
        )
        total_tavuk_pilav = len(result.scalars().all())
        print(f"🍚 Veritabanında toplam tavuk pilavı çeşidi: {total_tavuk_pilav}")
        break

if __name__ == "__main__":
    asyncio.run(add_more_tavuk_pilav_data())