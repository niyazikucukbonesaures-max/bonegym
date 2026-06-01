import asyncio
from app.database import get_db, init_db
from sqlalchemy import text

async def check_fts():
    await init_db()
    
    async for db in get_db():
        # FTS5 tablosunu kontrol et
        result = await db.execute(text("SELECT COUNT(*) FROM food_search"))
        count = result.scalar()
        print(f"FTS5 tablosundaki kayıt sayısı: {count}")
        
        # FTS5 tablosunu yeniden oluştur
        print("\nFTS5 tablosunu yeniden oluşturuyor...")
        
        # Önce mevcut FTS5 tablosunu temizle
        await db.execute(text("DELETE FROM food_search"))
        
        # Tüm besinleri FTS5'e ekle
        await db.execute(text("""
            INSERT INTO food_search(rowid, name)
            SELECT id, name FROM food_items
        """))
        
        await db.commit()
        
        # Kontrol et
        result = await db.execute(text("SELECT COUNT(*) FROM food_search"))
        count = result.scalar()
        print(f"FTS5 tablosu güncellendi. Yeni kayıt sayısı: {count}")
        
        # Test arama
        result = await db.execute(
            text("SELECT rowid, name FROM food_search WHERE food_search MATCH :query LIMIT 5"),
            {"query": "tavuk"}
        )
        rows = result.all()
        print(f"\n'tavuk' araması sonuçları ({len(rows)} sonuç):")
        for row in rows:
            print(f"  {row[0]}: {row[1]}")
        
        break

if __name__ == "__main__":
    asyncio.run(check_fts())
