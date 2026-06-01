# Kullanıcı Yetkilendirme Modelleri
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# Timezone-aware DateTime
TZ_DATETIME = DateTime(timezone=True)


class User(Base):
    """Kullanıcı tablosu."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(TZ_DATETIME, nullable=True)
    
    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class UserSession(Base):
    """Kullanıcı oturum tablosu."""
    
    __tablename__ = "user_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    session_token: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    def __repr__(self) -> str:
        return f"<UserSession id={self.id} user_id={self.user_id}>"