# Kullanıcı Yetkilendirme Şemaları
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------------------------------------------------------------------------
# Kullanıcı Şemaları
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    """Kullanıcı için ortak alanlar."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=2, max_length=100)


class UserCreate(UserBase):
    """Yeni kullanıcı kayıt isteği."""
    password: str = Field(min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Kullanıcı giriş isteği."""
    email: EmailStr
    password: str


class UserSchema(UserBase):
    """Kullanıcı API yanıtı."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UserUpdate(BaseModel):
    """Kullanıcı güncelleme isteği."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50)


class PasswordChange(BaseModel):
    """Şifre değiştirme isteği."""
    current_password: str
    new_password: str = Field(min_length=6, max_length=100)


# ---------------------------------------------------------------------------
# Auth Yanıt Şemaları
# ---------------------------------------------------------------------------

class AuthResponse(BaseModel):
    """Giriş/kayıt yanıtı."""
    access_token: str
    token_type: str = "bearer"
    user: UserSchema


class TokenData(BaseModel):
    """Token içeriği."""
    user_id: int
    email: str
    exp: datetime