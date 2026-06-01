#!/usr/bin/env python3
"""
Admin kullanıcısını kontrol et
"""

import asyncio
import sys
from pathlib import Path

# Backend dizinini Python path'ine ekle
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import get_db
from app.models_auth import User
from sqlalchemy import select


async def check_admin_user():
    """Admin kullanıcısını kontrol et."""
    print("🔍 Admin kullanıcısı kontrol ediliyor...")
    
    async for db in get_db():
        try:
            # Tüm kullanıcıları listele
            result = await db.execute(select(User))
            users = result.scalars().all()
            
            print(f"📊 Toplam kullanıcı sayısı: {len(users)}")
            
            for user in users:
                print(f"👤 ID: {user.id}")
                print(f"   📧 Email: {user.email}")
                print(f"   👤 Username: {user.username}")
                print(f"   📝 Full Name: {user.full_name}")
                print(f"   ✅ Active: {user.is_active}")
                print(f"   ✅ Verified: {user.is_verified}")
                print(f"   🕒 Created: {user.created_at}")
                print(f"   🔑 Password Hash: {user.hashed_password[:20]}...")
                print()
            
            # Admin kullanıcısını özel olarak ara
            admin_result = await db.execute(
                select(User).where(User.email == "admin@fitness.com")
            )
            admin_user = admin_result.scalar_one_or_none()
            
            if admin_user:
                print("✅ Admin kullanıcısı bulundu!")
                
                # Şifre testi
                from app.auth_service import AuthService
                password_valid = AuthService.verify_password("admin123", admin_user.hashed_password)
                print(f"🔑 Şifre doğrulaması: {'✅ Geçerli' if password_valid else '❌ Geçersiz'}")
                
            else:
                print("❌ Admin kullanıcısı bulunamadı!")
                
        except Exception as e:
            print(f"❌ Hata: {e}")
        
        break


if __name__ == "__main__":
    asyncio.run(check_admin_user())