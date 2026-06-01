"""
Temel besinleri (pilav, makarna, ekmek vb.) manuel olarak ekler
"""
import asyncio
from datetime import datetime
from app.database import get_db, init_db
from app.models import FoodItem

# Temel Türk mutfağı besinleri
STAPLE_FOODS = [
    # Pirinç ve Pilav çeşitleri
    ("Pilav (Sade)", 130, 2.7, 28, 0.3),
    ("Pilav (Tereyağlı)", 180, 3.2, 28, 6.5),
    ("Pilav (Nohutlu)", 145, 4.1, 29, 1.2),
    ("Pilav (Şehriyeli)", 155, 3.8, 30, 2.1),
    ("Pilav (Bulgurlu)", 140, 4.2, 27, 1.8),
    ("Pirinç (Çiğ)", 365, 7.1, 77, 0.7),
    ("Pirinç (Haşlanmış)", 130, 2.7, 28, 0.3),
    
    # Makarna çeşitleri
    ("Makarna (Haşlanmış)", 131, 5, 25, 1.1),
    ("Makarna (Çiğ)", 371, 13, 74, 1.5),
    ("Spagetti (Haşlanmış)", 131, 5, 25, 1.1),
    ("Penne (Haşlanmış)", 131, 5, 25, 1.1),
    ("Fusilli (Haşlanmış)", 131, 5, 25, 1.1),
    ("Makarna (Soslu)", 180, 6, 28, 5.2),
    ("Makarna (Kremalı)", 220, 8, 26, 9.8),
    
    # Bulgur çeşitleri
    ("Bulgur (Haşlanmış)", 83, 3, 19, 0.2),
    ("Bulgur (Çiğ)", 342, 12, 76, 1.3),
    ("Bulgur Pilavı", 120, 4.1, 22, 1.8),
    ("Kısır", 165, 4.5, 28, 4.2),
    
    # Ekmek çeşitleri
    ("Ekmek (Beyaz)", 265, 9, 49, 3.2),
    ("Ekmek (Tam Buğday)", 247, 13, 41, 3.4),
    ("Ekmek (Çavdar)", 259, 8.5, 48, 3.3),
    ("Somun Ekmek", 280, 9.2, 52, 3.8),
    ("Pide", 275, 8.8, 50, 4.1),
    ("Lavaş", 258, 8.2, 48, 3.5),
    ("Yufka", 301, 9.5, 58, 2.8),
    ("Simit", 298, 9.8, 56, 3.2),
    
    # Patates çeşitleri
    ("Patates (Haşlanmış)", 87, 1.9, 20, 0.1),
    ("Patates (Kızarmış)", 365, 4, 63, 17),
    ("Patates (Fırında)", 93, 2.1, 21, 0.1),
    ("Patates Püresi", 113, 2, 16, 4.2),
    ("Patates Salatası", 143, 1.8, 13, 10.3),
    
    # Çorba çeşitleri
    ("Mercimek Çorbası", 85, 4.2, 14, 1.8),
    ("Domates Çorbası", 45, 1.2, 8.5, 1.1),
    ("Tavuk Çorbası", 62, 5.8, 3.2, 3.1),
    ("Yayla Çorbası", 78, 3.5, 6.8, 4.2),
    ("Ezogelin Çorbası", 92, 4.8, 15, 1.9),
    ("Tarhana Çorbası", 68, 3.2, 12, 1.4),
    
    # Salata çeşitleri
    ("Çoban Salatası", 35, 1.2, 6.8, 0.8),
    ("Yeşil Salata", 18, 1.1, 3.2, 0.2),
    ("Mevsim Salatası", 28, 1.4, 5.1, 0.4),
    ("Roka Salatası", 42, 2.1, 4.8, 2.1),
    ("Karışık Salata", 32, 1.6, 5.9, 0.6),
    
    # Türk mutfağı ana yemekleri
    ("Kuru Fasulye", 127, 8.7, 23, 0.5),
    ("Nohut Yemeği", 164, 8.9, 27, 2.6),
    ("Mercimek Yemeği", 116, 9, 20, 0.4),
    ("Bamya Yemeği", 45, 2.1, 8.2, 0.8),
    ("Patlıcan Musakka", 158, 4.2, 12, 11.2),
    ("Dolma (Yaprak)", 185, 3.8, 18, 12.1),
    ("İmam Bayıldı", 142, 2.1, 15, 8.9),
    
    # Kahvaltılık
    ("Menemen", 168, 8.2, 6.1, 12.8),
    ("Sucuklu Yumurta", 285, 16.2, 2.1, 23.8),
    ("Peynirli Omlet", 198, 14.5, 2.8, 14.2),
    ("Börek (Su Böreği)", 245, 8.9, 28, 11.2),
    ("Börek (Sigara Böreği)", 312, 9.8, 32, 16.8),
    ("Poğaça", 298, 8.2, 42, 11.5),
]

async def add_staple_foods():
    """Temel besinleri ekler."""
    from sqlalchemy import text
    await init_db()
    
    async for db in get_db():
        now = datetime.utcnow()
        count = 0
        
        for name, calories, protein, carbs, fat in STAPLE_FOODS:
            food = FoodItem(
                name=name,
                calories_per_100g=calories,
                protein_per_100g=protein,
                carbs_per_100g=carbs,
                fat_per_100g=fat,
                source_url="manuel_temel",
                scraped_at=now,
            )
            db.add(food)
            count += 1
        
        await db.commit()
        print(f"✅ {count} temel besin eklendi!")
        
        # FTS5 tablosunu güncelle
        print("FTS5 tablosunu güncelleniyor...")
        await db.execute(text("""
            INSERT INTO food_search(rowid, name)
            SELECT id, name FROM food_items
            WHERE source_url = 'manuel_temel'
        """))
        await db.commit()
        print("✅ FTS5 tablosu güncellendi!")
        
        break

if __name__ == "__main__":
    asyncio.run(add_staple_foods())