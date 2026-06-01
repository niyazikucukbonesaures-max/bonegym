# Spor Profili Router'ı
# GET    /                    → Spor profili getir
# POST   /                    → Spor profili oluştur/güncelle
# DELETE /                    → Spor profili sil
# GET    /calorie-targets     → Kalori hedefleri hesapla
# GET    /macro-targets       → Makro hedefleri hesapla
# GET    /daily-recommendation → Günlük antrenman önerisi

from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import SportProfile, UserProfile
from app.sport_target_engine import sport_target_engine
from app.schemas import SportProfileCreate, SportProfileSchema

router = APIRouter()


@router.get("/", response_model=Optional[SportProfileSchema])
async def get_sport_profile(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    db: AsyncSession = Depends(get_db),
) -> Optional[SportProfileSchema]:
    """Kullanıcının spor profilini getirir."""
    try:
        stmt = select(SportProfile).where(SportProfile.user_id == user_id)
        result = await db.execute(stmt)
        sport_profile = result.scalar_one_or_none()
        
        if not sport_profile:
            return None
        
        return SportProfileSchema(
            id=sport_profile.id,
            user_id=sport_profile.user_id,
            is_athlete=sport_profile.is_athlete,
            sport_type=sport_profile.sport_type,
            training_frequency=sport_profile.training_frequency,
            training_intensity=sport_profile.training_intensity,
            rest_day_calories_adjustment=sport_profile.rest_day_calories_adjustment,
            training_day_calories_adjustment=sport_profile.training_day_calories_adjustment,
            preferred_macro_split=sport_profile.preferred_macro_split,
            created_at=sport_profile.created_at,
            updated_at=sport_profile.updated_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spor profili getirme hatası: {str(e)}")


@router.post("/", response_model=SportProfileSchema, status_code=201)
async def create_or_update_sport_profile(
    profile_data: SportProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> SportProfileSchema:
    """Spor profili oluşturur veya günceller."""
    try:
        # Mevcut profili kontrol et
        stmt = select(SportProfile).where(SportProfile.user_id == profile_data.user_id)
        result = await db.execute(stmt)
        existing_profile = result.scalar_one_or_none()
        
        if existing_profile:
            # Güncelle
            existing_profile.is_athlete = profile_data.is_athlete
            existing_profile.sport_type = profile_data.sport_type
            existing_profile.training_frequency = profile_data.training_frequency
            existing_profile.training_intensity = profile_data.training_intensity
            existing_profile.rest_day_calories_adjustment = profile_data.rest_day_calories_adjustment
            existing_profile.training_day_calories_adjustment = profile_data.training_day_calories_adjustment
            existing_profile.preferred_macro_split = profile_data.preferred_macro_split or {}
            
            await db.commit()
            await db.refresh(existing_profile)
            sport_profile = existing_profile
        else:
            # Yeni oluştur
            sport_profile = SportProfile(
                user_id=profile_data.user_id,
                is_athlete=profile_data.is_athlete,
                sport_type=profile_data.sport_type,
                training_frequency=profile_data.training_frequency,
                training_intensity=profile_data.training_intensity,
                rest_day_calories_adjustment=profile_data.rest_day_calories_adjustment,
                training_day_calories_adjustment=profile_data.training_day_calories_adjustment,
                preferred_macro_split=profile_data.preferred_macro_split or {}
            )
            
            db.add(sport_profile)
            await db.commit()
            await db.refresh(sport_profile)
        
        return SportProfileSchema(
            id=sport_profile.id,
            user_id=sport_profile.user_id,
            is_athlete=sport_profile.is_athlete,
            sport_type=sport_profile.sport_type,
            training_frequency=sport_profile.training_frequency,
            training_intensity=sport_profile.training_intensity,
            rest_day_calories_adjustment=sport_profile.rest_day_calories_adjustment,
            training_day_calories_adjustment=sport_profile.training_day_calories_adjustment,
            preferred_macro_split=sport_profile.preferred_macro_split,
            created_at=sport_profile.created_at,
            updated_at=sport_profile.updated_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spor profili kaydetme hatası: {str(e)}")


@router.delete("/")
async def delete_sport_profile(
    user_id: int = Query(..., description="Kullanıcı ID'si"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Spor profilini siler."""
    try:
        stmt = select(SportProfile).where(SportProfile.user_id == user_id)
        result = await db.execute(stmt)
        sport_profile = result.scalar_one_or_none()
        
        if not sport_profile:
            raise HTTPException(status_code=404, detail="Spor profili bulunamadı")
        
        await db.delete(sport_profile)
        await db.commit()
        
        return {"message": "Spor profili başarıyla silindi"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spor profili silme hatası: {str(e)}")


@router.get("/calorie-targets")
async def get_calorie_targets(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    training_day: bool = Query(True, description="Antrenman günü mü?"),
    custom_intensity: Optional[str] = Query(None, description="Özel yoğunluk seviyesi"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Spor yapanlar için kalori hedefleri hesaplar."""
    try:
        # Kullanıcı profilini al
        user_stmt = select(UserProfile).where(UserProfile.id == user_id)
        user_result = await db.execute(user_stmt)
        user_profile = user_result.scalar_one_or_none()
        
        if not user_profile:
            raise HTTPException(status_code=404, detail="Kullanıcı profili bulunamadı")
        
        # Sporcu kalori hesaplama
        calorie_result = await sport_target_engine.calculate_athlete_calories(
            user_profile=user_profile,
            training_day=training_day,
            db=db,
            custom_intensity=custom_intensity
        )
        
        return {
            "base_calories": float(calorie_result.base_calories),
            "training_day_calories": float(calorie_result.training_day_calories),
            "rest_day_calories": float(calorie_result.rest_day_calories),
            "weekly_average": float(calorie_result.weekly_average),
            "training_days_per_week": calorie_result.training_days_per_week,
            "intensity_level": calorie_result.intensity_level,
            "adjustments_applied": calorie_result.adjustments_applied,
            "recommended_for_today": float(
                calorie_result.training_day_calories if training_day 
                else calorie_result.rest_day_calories
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kalori hedefi hesaplama hatası: {str(e)}")


@router.get("/macro-targets")
async def get_macro_targets(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    goal: str = Query("maintain", description="Hedef (muscle_gain, cut, bulk, vb.)"),
    daily_calories: float = Query(..., description="Günlük kalori hedefi"),
    sport_type: Optional[str] = Query(None, description="Spor tipi"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Spor tipine göre makro besin hedefleri hesaplar."""
    try:
        macros = await sport_target_engine.get_sport_specific_macros(
            goal=goal,
            daily_calories=daily_calories,
            user_id=user_id,
            db=db,
            sport_type=sport_type
        )
        
        return {
            "protein_g": float(macros.protein_g),
            "carbs_g": float(macros.carbs_g),
            "fat_g": float(macros.fat_g),
            "protein_percentage": macros.protein_percentage,
            "carbs_percentage": macros.carbs_percentage,
            "fat_percentage": macros.fat_percentage,
            "sport_type": macros.sport_type,
            "goal_type": macros.goal_type,
            "rationale": macros.rationale,
            "daily_calories": daily_calories
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Makro hedef hesaplama hatası: {str(e)}")


@router.get("/daily-recommendation")
async def get_daily_recommendation(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    target_date: Optional[str] = Query(None, description="Hedef tarih (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Belirli bir gün için antrenman önerisi."""
    try:
        # Tarih parse et
        if target_date:
            try:
                parsed_date = date.fromisoformat(target_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Geçersiz tarih formatı (YYYY-MM-DD bekleniyor)")
        else:
            parsed_date = date.today()
        
        # Günlük öneri al
        recommendation = await sport_target_engine.get_daily_recommendation(
            user_id=user_id,
            target_date=parsed_date,
            db=db
        )
        
        return {
            "date": parsed_date.isoformat(),
            "is_training_day": recommendation.is_training_day,
            "recommended_calories": float(recommendation.recommended_calories),
            "macros": {
                "protein_g": float(recommendation.macros.protein_g),
                "carbs_g": float(recommendation.macros.carbs_g),
                "fat_g": float(recommendation.macros.fat_g),
                "protein_percentage": recommendation.macros.protein_percentage,
                "carbs_percentage": recommendation.macros.carbs_percentage,
                "fat_percentage": recommendation.macros.fat_percentage,
                "sport_type": recommendation.macros.sport_type,
                "goal_type": recommendation.macros.goal_type
            },
            "pre_workout_carbs": float(recommendation.pre_workout_carbs),
            "post_workout_protein": float(recommendation.post_workout_protein),
            "hydration_ml": recommendation.hydration_ml,
            "timing_notes": recommendation.timing_notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Günlük öneri hatası: {str(e)}")