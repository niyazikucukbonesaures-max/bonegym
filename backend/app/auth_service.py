# Kullanıcı Yetkilendirme Servisi
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_auth import User, UserSession


class AuthService:
    """Kullanıcı yetkilendirme servisi."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Şifreyi hash'ler."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Şifreyi doğrular."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def generate_session_token() -> str:
        """Güvenli session token üretir."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        username: str,
        full_name: str,
        password: str
    ) -> User:
        """Yeni kullanıcı oluşturur."""
        # Email kontrolü
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ValueError("Bu email adresi zaten kullanılıyor")
        
        # Username kontrolü
        result = await db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            raise ValueError("Bu kullanıcı adı zaten kullanılıyor")
        
        # Kullanıcı oluştur
        hashed_password = AuthService.hash_password(password)
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True  # Basit sistem için otomatik doğrula
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[User]:
        """Kullanıcı giriş doğrulaması."""
        result = await db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if not user or not AuthService.verify_password(password, user.hashed_password):
            return None
        
        # Son giriş zamanını güncelle
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
        
        return user
    
    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: int,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """Kullanıcı oturumu oluşturur."""
        session_token = AuthService.generate_session_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)  # 30 gün
        
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        db.add(session)
        await db.commit()
        return session_token
    
    @staticmethod
    async def get_user_by_session(
        db: AsyncSession,
        session_token: str
    ) -> Optional[User]:
        """Session token ile kullanıcı getirir."""
        now = datetime.now(timezone.utc)
        
        result = await db.execute(
            select(UserSession).where(
                UserSession.session_token == session_token,
                UserSession.expires_at > now
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        result = await db.execute(
            select(User).where(
                User.id == session.user_id,
                User.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def logout_session(
        db: AsyncSession,
        session_token: str
    ) -> bool:
        """Oturumu sonlandırır."""
        result = await db.execute(
            select(UserSession).where(UserSession.session_token == session_token)
        )
        session = result.scalar_one_or_none()
        
        if session:
            await db.delete(session)
            await db.commit()
            return True
        return False