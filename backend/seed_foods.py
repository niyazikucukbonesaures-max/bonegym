"""
Örnek besin verilerini veritabanına ekler.
Diyetkolik.com JavaScript ile render edildiği için scraping çalışmıyor.
Bu script manuel olarak örnek veriler ekler.
"""
import asyncio
from datetime import datetime
from app.database import get_db, init_db
from app.models import FoodItem

# Türk mutfağından yaygın besinler ve kalori değerleri
SAMPLE_FOODS = [
    # Et, Tavuk, Balık
    ("Tavuk Göğsü (Haşlanmış)", 165, 31, 0, 3.6),
    ("Tavuk But (Haşlanmış)", 190, 26, 0, 9),
    ("Dana Eti (Yağsız)", 250, 26, 0, 15),
    ("Kıyma (Yağlı)", 332, 14, 0, 30),
    ("Köfte", 280, 17, 8, 20),
    ("Izgara Tavuk", 195, 29, 0, 7.4),
    ("Somon Balığı", 208, 20, 0, 13),
    ("Levrek", 97, 18, 0, 2),
    ("Ton Balığı (Konserve)", 116, 26, 0, 0.8),
    ("Sardalya", 208, 25, 0, 11),
    
    # Süt Ürünleri
    ("Süt (Tam Yağlı)", 61, 3.2, 4.8, 3.3),
    ("Süt (Yarım Yağlı)", 46, 3.3, 4.8, 1.6),
    ("Yoğurt (Tam Yağlı)", 61, 3.5, 4.7, 3.3),
    ("Yoğurt (Yağsız)", 56, 5.7, 7.7, 0.2),
    ("Ayran", 31, 1.5, 3.5, 1.1),
    ("Beyaz Peynir", 264, 18, 1.5, 21),
    ("Kaşar Peyniri", 374, 25, 0, 31),
    ("Lor Peyniri", 176, 13, 3, 12),
    ("Labne", 159, 7.5, 4.5, 13),
    
    # Tahıllar ve Ekmek
    ("Beyaz Ekmek", 265, 9, 49, 3.2),
    ("Tam Buğday Ekmeği", 247, 13, 41, 3.4),
    ("Çavdar Ekmeği", 259, 8.5, 48, 3.3),
    ("Pirinç (Pişmiş)", 130, 2.7, 28, 0.3),
    ("Bulgur (Pişmiş)", 83, 3, 19, 0.2),
    ("Makarna (Pişmiş)", 131, 5, 25, 1.1),
    ("Yulaf Ezmesi", 389, 17, 66, 6.9),
    ("Mısır Gevreği", 357, 7.5, 84, 0.9),
    
    # Sebzeler
    ("Domates", 18, 0.9, 3.9, 0.2),
    ("Salatalık", 15, 0.7, 3.6, 0.1),
    ("Marul", 15, 1.4, 2.9, 0.2),
    ("Soğan", 40, 1.1, 9.3, 0.1),
    ("Sarımsak", 149, 6.4, 33, 0.5),
    ("Biber (Yeşil)", 20, 0.9, 4.6, 0.2),
    ("Patlıcan", 25, 1, 6, 0.2),
    ("Kabak", 17, 1.2, 3.1, 0.3),
    ("Havuç", 41, 0.9, 10, 0.2),
    ("Brokoli", 34, 2.8, 7, 0.4),
    ("Karnabahar", 25, 1.9, 5, 0.3),
    ("Ispanak", 23, 2.9, 3.6, 0.4),
    
    # Meyveler
    ("Elma", 52, 0.3, 14, 0.2),
    ("Muz", 89, 1.1, 23, 0.3),
    ("Portakal", 47, 0.9, 12, 0.1),
    ("Mandalina", 53, 0.8, 13, 0.3),
    ("Üzüm", 69, 0.7, 18, 0.2),
    ("Çilek", 32, 0.7, 7.7, 0.3),
    ("Karpuz", 30, 0.6, 7.6, 0.2),
    ("Kavun", 34, 0.8, 8.2, 0.2),
    ("Şeftali", 39, 0.9, 9.5, 0.3),
    ("Armut", 57, 0.4, 15, 0.1),
    
    # Kuruyemişler
    ("Badem", 579, 21, 22, 50),
    ("Ceviz", 654, 15, 14, 65),
    ("Fındık", 628, 15, 17, 61),
    ("Fıstık", 567, 26, 16, 49),
    ("Kaju", 553, 18, 30, 44),
    
    # Baklagiller
    ("Nohut (Haşlanmış)", 164, 8.9, 27, 2.6),
    ("Kuru Fasulye (Haşlanmış)", 127, 8.7, 23, 0.5),
    ("Mercimek (Haşlanmış)", 116, 9, 20, 0.4),
    ("Yeşil Mercimek", 352, 25, 60, 1.1),
    
    # Yağlar
    ("Zeytinyağı", 884, 0, 0, 100),
    ("Tereyağı", 717, 0.9, 0.1, 81),
    ("Ayçiçek Yağı", 884, 0, 0, 100),
    
    # Tatlılar ve Atıştırmalıklar
    ("Çikolata (Sütlü)", 535, 7.6, 59, 30),
    ("Çikolata (Bitter)", 546, 4.9, 61, 31),
    ("Bal", 304, 0.3, 82, 0),
    ("Reçel", 278, 0.4, 69, 0.1),
    ("Patates Cipsi", 536, 6.6, 53, 35),
    
    # İçecekler
    ("Kola", 42, 0, 10.6, 0),
    ("Portakal Suyu", 45, 0.7, 10, 0.2),
    ("Çay (Şekersiz)", 1, 0, 0.3, 0),
    ("Kahve (Şekersiz)", 2, 0.3, 0, 0),
    ("Ayran (Hazır)", 31, 1.5, 3.5, 1.1),
]


async def seed_database():
    """Örnek besin verilerini veritabanına ekler."""
    from sqlalchemy import text
    await init_db()
    
    async for db in get_db():
        now = datetime.utcnow()
        count = 0
        
        for name, calories, protein, carbs, fat in SAMPLE_FOODS:
            food = FoodItem(
                name=name,
                calories_per_100g=calories,
                protein_per_100g=protein,
                carbs_per_100g=carbs,
                fat_per_100g=fat,
                source_url="manuel",
                scraped_at=now,
            )
            db.add(food)
            count += 1
        
        await db.commit()
        print(f"✅ {count} besin başarıyla eklendi!")
        
        # FTS5 tablosunu güncelle
        print("FTS5 tablosunu güncelleniyor...")
        await db.execute(text("""
            INSERT INTO food_search(rowid, name)
            SELECT id, name FROM food_items
        """))
        await db.commit()
        print("✅ FTS5 tablosu güncellendi!")
        
        break


if __name__ == "__main__":
    asyncio.run(seed_database())
