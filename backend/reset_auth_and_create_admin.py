"""
Kullanıcı tablolarını sıfırlar ve admin hesabı oluşturur.
"""
import asyncio
from sqlalchemy import text
from app.database import engine, AsyncSessionLocal
from app.models_auth import User, UserSession
from app.auth_service import AuthService


async def reset_auth_tables():
    """Auth tablolarını sıfırlar ve admin hesabı oluşturur."""
    
    async with engine.begin() as conn:
        print("🗑️  Kullanıcı tablolarını temizliyorum...")
        
        # Tabloları sıfırla (CASCADE ile ilişkili kayıtlar da silinir)
        await conn.execute(text("DELETE FROM user_sessions"))
        await conn.execute(text("DELETE FROM users"))
        
        # Auto-increment sayaçlarını sıfırla (eğer tablo varsa)
        try:
            await conn.execute(text("DELETE FROM sqlite_sequence WHERE name='users'"))
            await conn.execute(text("DELETE FROM sqlite_sequence WHERE name='user_sessions'"))
        except Exception:
            pass  # sqlite_sequence tablosu yoksa sorun değil
        
        print("✅ Tablolar temizlendi!")
    
    # Admin hesabı oluştur
    async with AsyncSessionLocal() as db:
        print("\n👤 Admin hesabı oluşturuluyor...")
        
        try:
            admin_user = await AuthService.create_user(
                db=db,
                email="admin@fitness.com",
                username="admin",
                full_name="Admin User",
                password="admin123"
            )
            
            print(f"✅ Admin hesabı oluşturuldu!")
            print(f"   📧 Email: admin@fitness.com")
            print(f"   👤 Kullanıcı Adı: admin")
            print(f"   🔑 Şifre: admin123")
            print(f"   🆔 User ID: {admin_user.id}")
            
        except Exception as e:
            print(f"❌ Admin hesabı oluşturulamadı: {e}")
            raise
    
    print("\n✨ İşlem tamamlandı! Artık admin hesabıyla giriş yapabilirsiniz.")


if __name__ == "__main__":
    asyncio.run(reset_auth_tables())
