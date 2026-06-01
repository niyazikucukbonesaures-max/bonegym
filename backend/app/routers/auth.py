# Kullanıcı Yetkilendirme Router
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth_service import AuthService
from app.schemas_auth import (
    UserCreate, UserLogin, UserSchema, UserUpdate, 
    PasswordChange, AuthResponse
)

router = APIRouter(tags=["auth"])
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[UserSchema]:
    """Mevcut kullanıcıyı getirir."""
    if not credentials:
        return None
    
    user = await AuthService.get_user_by_session(db, credentials.credentials)
    if not user:
        return None
    
    return UserSchema.model_validate(user)


async def require_auth(
    current_user: Optional[UserSchema] = Depends(get_current_user)
) -> UserSchema:
    """Yetkilendirme gerektirir."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Giriş yapmanız gerekiyor"
        )
    return current_user


@router.post("/register", response_model=AuthResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Yeni kullanıcı kaydı."""
    try:
        user = await AuthService.create_user(
            db=db,
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            password=user_data.password
        )
        
        # Session oluştur
        session_token = await AuthService.create_session(
            db=db,
            user_id=user.id,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None
        )
        
        return AuthResponse(
            access_token=session_token,
            user=UserSchema.model_validate(user)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcı girişi."""
    user = await AuthService.authenticate_user(
        db=db,
        email=login_data.email,
        password=login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı"
        )
    
    # Session oluştur
    session_token = await AuthService.create_session(
        db=db,
        user_id=user.id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None
    )
    
    return AuthResponse(
        access_token=session_token,
        user=UserSchema.model_validate(user)
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcı çıkışı."""
    if credentials:
        await AuthService.logout_session(db, credentials.credentials)
    
    return {"message": "Başarıyla çıkış yapıldı"}


@router.get("/me", response_model=UserSchema)
async def get_me(current_user: UserSchema = Depends(require_auth)):
    """Mevcut kullanıcı bilgilerini getirir."""
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_me(
    user_update: UserUpdate,
    current_user: UserSchema = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcı bilgilerini günceller."""
    # Bu endpoint'i basit tutuyoruz - sadece full_name ve username güncellemesi
    # Gerçek uygulamada daha detaylı validasyon gerekebilir
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Kullanıcı güncelleme henüz desteklenmiyor"
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: UserSchema = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Şifre değiştirme."""
    # Bu endpoint'i basit tutuyoruz
    # Gerçek uygulamada şifre değiştirme mantığı eklenebilir
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Şifre değiştirme henüz desteklenmiyor"
    )