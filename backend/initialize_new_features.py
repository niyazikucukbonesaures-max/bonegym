"""
Yeni özellikler için veritabanını günceller ve varsayılan verileri oluşturur.
"""
import asyncio
from app.database import init_db, AsyncSessionLocal
from app.achievement_system import AchievementSystem


async def initialize_new_features():
    """Yeni özellikler için gerekli başlangıç işlemlerini yapar."""
    
    print("🔄 Veritabanı tabloları güncelleniyor...")
    
    # Veritabanı tablolarını oluştur/güncelle
    await init_db()
    print("✅ Veritabanı tabloları güncellendi!")
    
    # Varsayılan başarı rozetlerini oluştur
    async with AsyncSessionLocal() as db:
        print("\n🏆 Varsayılan başarı rozetleri oluşturuluyor...")
        await AchievementSystem.initialize_default_achievements(db)
        print("✅ Başarı rozetleri oluşturuldu!")
    
    print("\n✨ Yeni özellikler hazır!")
    print("\n📋 Eklenen Özellikler:")
    print("   💧 Su Takibi")
    print("   🏆 Başarı Rozetleri")
    print("   📊 Rozet İlerleme Sistemi")
    print("\n🚀 Backend yeniden başlatılıyor...")


if __name__ == "__main__":
    asyncio.run(initialize_new_features())