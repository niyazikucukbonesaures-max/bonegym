"""
Kullanıcı yetkilendirme sistemini test eder
"""
import asyncio
from app.database import get_db
from app.auth_service import AuthService

async def test_auth_system():
    """Auth sistemini test eder."""
    async for db in get_db():
        print("🔐 Kullanıcı yetkilendirme sistemi test ediliyor...")
        
        try:
            # Test kullanıcısı oluştur
            user = await AuthService.create_user(
                db=db,
                email="test@example.com",
                username="testuser",
                full_name="Test Kullanıcı",
                password="test123456"
            )
            print(f"✅ Kullanıcı oluşturuldu: {user.email} (ID: {user.id})")
            
            # Giriş testi
            auth_user = await AuthService.authenticate_user(
                db=db,
                email="test@example.com",
                password="test123456"
            )
            
            if auth_user:
                print(f"✅ Giriş başarılı: {auth_user.email}")
                
                # Session oluştur
                session_token = await AuthService.create_session(
                    db=db,
                    user_id=auth_user.id,
                    user_agent="Test Browser",
                    ip_address="127.0.0.1"
                )
                print(f"✅ Session oluşturuldu: {session_token[:20]}...")
                
                # Session ile kullanıcı getir
                session_user = await AuthService.get_user_by_session(db, session_token)
                if session_user:
                    print(f"✅ Session ile kullanıcı getirildi: {session_user.email}")
                else:
                    print("❌ Session ile kullanıcı getirilemedi")
                
                # Logout
                logout_success = await AuthService.logout_session(db, session_token)
                if logout_success:
                    print("✅ Logout başarılı")
                else:
                    print("❌ Logout başarısız")
                    
            else:
                print("❌ Giriş başarısız")
                
        except ValueError as e:
            print(f"❌ Hata: {e}")
        except Exception as e:
            print(f"❌ Beklenmeyen hata: {e}")
        
        print("\n🎯 Auth sistemi testi tamamlandı!")
        break

if __name__ == "__main__":
    asyncio.run(test_auth_system())