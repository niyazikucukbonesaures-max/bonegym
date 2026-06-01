#!/usr/bin/env python3
"""
AI Chat Tabloları Migrasyon Script'i
Bu script AI besin asistanı için gerekli tabloları oluşturur.
"""

import asyncio
import sys
from pathlib import Path

# Backend dizinini Python path'ine ekle
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import engine
from app.models import Base, AIChatSession, AIChatMessage, AIGeneratedFood


async def create_ai_chat_tables():
    """AI chat tablolarını oluştur."""
    print("🤖 AI Chat tabloları oluşturuluyor...")
    
    try:
        async with engine.begin() as conn:
            # Sadece AI chat tablolarını oluştur
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        
        print("✅ AI Chat tabloları başarıyla oluşturuldu!")
        print("📋 Oluşturulan tablolar:")
        print("   - ai_chat_sessions")
        print("   - ai_chat_messages") 
        print("   - ai_generated_foods")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False
    
    return True


async def verify_tables():
    """Tabloların doğru oluşturulduğunu kontrol et."""
    print("\n🔍 Tablo yapısı kontrol ediliyor...")
    
    try:
        from sqlalchemy import text
        
        async with engine.begin() as conn:
            # Tabloların varlığını kontrol et
            tables_to_check = [
                "ai_chat_sessions",
                "ai_chat_messages", 
                "ai_generated_foods"
            ]
            
            for table_name in tables_to_check:
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
                    {"table_name": table_name}
                )
                if result.fetchone():
                    print(f"   ✅ {table_name} tablosu mevcut")
                else:
                    print(f"   ❌ {table_name} tablosu bulunamadı")
                    return False
        
        print("✅ Tüm AI chat tabloları doğru şekilde oluşturuldu!")
        return True
        
    except Exception as e:
        print(f"❌ Kontrol hatası: {e}")
        return False


async def main():
    """Ana migrasyon fonksiyonu."""
    print("🚀 AI Besin Asistanı - Veritabanı Migrasyonu")
    print("=" * 50)
    
    # Tabloları oluştur
    success = await create_ai_chat_tables()
    if not success:
        print("❌ Migrasyon başarısız!")
        return 1
    
    # Tabloları doğrula
    success = await verify_tables()
    if not success:
        print("❌ Tablo doğrulama başarısız!")
        return 1
    
    print("\n🎉 AI Chat migrasyonu tamamlandı!")
    print("💡 Artık AI besin asistanı özelliğini kullanabilirsiniz.")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)