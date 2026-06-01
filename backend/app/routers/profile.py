# Kullanıcı Profili Router'ı
# GET / → Profil getir (BMR/TDEE hesaplanmış)
# PUT / → Profil güncelle

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calorie_engine import CalorieEngine
from app.database import get_db
from app.models import UserProfile
from app.schemas import UserProfileUpdate, UserProfileWithStats
from app.routers.auth import get_current_user
from app.schemas_auth import UserSchema
from app.cache import cache

router = APIRouter()


def _build_profile_with_stats(profile: UserProfile) -> UserProfileWithStats:
    """Profil modeline BMR/TDEE/recommended_calories ekler."""
    bmr = CalorieEngine.calculate_bmr(
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
        age=profile.age,
        gender=profile.gender,
    )
    tdee = CalorieEngine.calculate_tdee(bmr, profile.activity_level)
    recommended = CalorieEngine.get_recommended_calories(tdee, profile.goal)

    return UserProfileWithStats(
        id=profile.id,
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
        age=profile.age,
        gender=profile.gender,
        activity_level=profile.activity_level,
        goal=profile.goal,
        weekly_workout_goal=profile.weekly_workout_goal,
        daily_calorie_target=profile.daily_calorie_target,
        updated_at=profile.updated_at,
        bmr=round(bmr, 2),
        tdee=round(tdee, 2),
        recommended_calories=round(recommended, 2),
    )


def _get_user_id(current_user: UserSchema | None) -> int:
    """Auth varsa token'dan user_id al, yoksa 1 döndür (geriye dönük uyumluluk)."""
    return current_user.id if current_user else 1


@router.get("/", response_model=UserProfileWithStats)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
) -> UserProfileWithStats:
    """Kullanıcı profilini BMR/TDEE hesaplanmış olarak döndürür."""
    user_id = _get_user_id(current_user)
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == user_id)
    )
    profile = result.scalar_one_or_none()
    # Geriye dönük uyumluluk: user_id ile bulunamazsa ilk profili al
    if profile is None:
        result = await db.execute(select(UserProfile).limit(1))
        profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profil bulunamadı.")
    return _build_profile_with_stats(profile)


@router.put("/", response_model=UserProfileWithStats)
async def update_profile(
    data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
) -> UserProfileWithStats:
    """Kullanıcı profilini günceller veya yoksa oluşturur."""
    user_id = _get_user_id(current_user)
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == user_id)
    )
    profile = result.scalar_one_or_none()

    # Geriye dönük uyumluluk
    if profile is None:
        result = await db.execute(select(UserProfile).limit(1))
        profile = result.scalar_one_or_none()

    if profile is None:
        profile = UserProfile()
        db.add(profile)

    profile.weight_kg = data.weight_kg
    profile.height_cm = data.height_cm
    profile.age = data.age
    profile.gender = data.gender
    profile.activity_level = data.activity_level
    profile.goal = data.goal
    profile.weekly_workout_goal = data.weekly_workout_goal
    profile.daily_calorie_target = data.daily_calorie_target
    profile.fitness_level = data.fitness_level
    profile.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(profile)

    # Dashboard cache'ini temizle
    await cache.delete_pattern(f"dashboard:{user_id}")

    return _build_profile_with_stats(profile)


@router.delete("/")
async def delete_profile(
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
) -> dict:
    """Kullanıcı profilini siler."""
    user_id = _get_user_id(current_user)
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == user_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        result = await db.execute(select(UserProfile).limit(1))
        profile = result.scalar_one_or_none()
    
    if profile is None:
        raise HTTPException(status_code=404, detail="Profil bulunamadı.")
    
    await db.delete(profile)
    await db.commit()
    
    return {"message": "Profil başarıyla silindi."}
