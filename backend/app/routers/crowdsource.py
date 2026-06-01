# Kullanıcı Katkılı Besin Veritabanı API Endpoints

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.crowdsource_system import crowdsource_system, UserContribution, FoodSuggestion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crowdsource", tags=["crowdsource"])

# Request/Response Models
class ContributionRequest(BaseModel):
    food_name: str = Field(..., min_length=3, max_length=100)
    calories_per_100g: float = Field(..., ge=0, le=900)
    protein_per_100g: float = Field(..., ge=0, le=100)
    carbs_per_100g: float = Field(..., ge=0, le=100)
    fat_per_100g: float = Field(..., ge=0, le=100)
    source: str = Field(..., pattern="^(homemade|restaurant|package)$")
    photo_url: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None

class ContributionResponse(BaseModel):
    success: bool
    message: str
    points_earned: int
    user_total_points: int

class VerificationRequest(BaseModel):
    contribution_id: int
    is_correct: bool

class SuggestionRequest(BaseModel):
    food_name: str = Field(..., min_length=3, max_length=100)

class LeaderboardEntry(BaseModel):
    user_id: int
    total_points: int
    level: int
    contributions: int
    badges: List[str]
    rank: int

class MissingFoodEntry(BaseModel):
    food_name: str
    votes: int
    suggested_by: int
    days_ago: int

class VerificationQueueEntry(BaseModel):
    id: int
    food_name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    source: str
    confidence: float
    verifications_needed: int

class UserStatsResponse(BaseModel):
    total_points: int
    level: int
    contributions: int
    verifications: int
    suggestions: int
    badges: List[str]
    rank: int

# Endpoints
@router.post("/contribute", response_model=ContributionResponse)
async def add_contribution(
    contribution: ContributionRequest,
    user_id: int = 1  # TODO: Get from auth
):
    """Yeni besin katkısı ekle."""
    try:
        # UserContribution objesi oluştur
        user_contribution = UserContribution(
            user_id=user_id,
            food_name=contribution.food_name,
            calories_per_100g=contribution.calories_per_100g,
            protein_per_100g=contribution.protein_per_100g,
            carbs_per_100g=contribution.carbs_per_100g,
            fat_per_100g=contribution.fat_per_100g,
            source=contribution.source,
            photo_url=contribution.photo_url,
            barcode=contribution.barcode,
            brand=contribution.brand
        )
        
        # Katkıyı ekle
        success = await crowdsource_system.add_user_contribution(user_contribution)
        
        if not success:
            raise HTTPException(status_code=400, detail="Katkı eklenemedi. Lütfen besin değerlerini kontrol edin.")
        
        # Kullanıcı istatistiklerini al
        user_stats = crowdsource_system.user_points.get(user_id, {
            "total_points": 0,
            "contributions": 0,
            "level": 1
        })
        
        return ContributionResponse(
            success=True,
            message=f"'{contribution.food_name}' başarıyla eklendi! 10 puan kazandınız.",
            points_earned=10,
            user_total_points=user_stats["total_points"]
        )
        
    except Exception as e:
        logger.error(f"Katkı ekleme hatası: {e}")
        raise HTTPException(status_code=500, detail="Katkı eklenirken hata oluştu.")

@router.post("/verify/{contribution_id}")
async def verify_contribution(
    contribution_id: int,
    verification: VerificationRequest,
    user_id: int = 1  # TODO: Get from auth
):
    """Katkıyı doğrula."""
    try:
        success = await crowdsource_system.verify_contribution(
            contribution_id, user_id, verification.is_correct
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Doğrulama yapılamadı.")
        
        points_earned = 5 if verification.is_correct else 0
        message = "Doğrulama için teşekkürler! 5 puan kazandınız." if verification.is_correct else "Doğrulama kaydedildi."
        
        return {"success": True, "message": message, "points_earned": points_earned}
        
    except Exception as e:
        logger.error(f"Doğrulama hatası: {e}")
        raise HTTPException(status_code=500, detail="Doğrulama yapılırken hata oluştu.")

@router.post("/suggest")
async def suggest_missing_food(
    suggestion: SuggestionRequest,
    user_id: int = 1  # TODO: Get from auth
):
    """Eksik besin önerisi yap."""
    try:
        success = await crowdsource_system.suggest_missing_food(user_id, suggestion.food_name)
        
        if not success:
            raise HTTPException(status_code=400, detail="Öneri eklenemedi.")
        
        return {
            "success": True,
            "message": f"'{suggestion.food_name}' önerisi eklendi! 5 puan kazandınız.",
            "points_earned": 5
        }
        
    except Exception as e:
        logger.error(f"Öneri ekleme hatası: {e}")
        raise HTTPException(status_code=500, detail="Öneri eklenirken hata oluştu.")

@router.get("/missing-foods", response_model=List[MissingFoodEntry])
async def get_missing_foods(limit: int = 20):
    """En çok istenen eksik besinleri getir."""
    try:
        missing_foods = await crowdsource_system.get_popular_missing_foods(limit)
        
        return [
            MissingFoodEntry(
                food_name=food["food_name"],
                votes=food["votes"],
                suggested_by=food["suggested_by"],
                days_ago=food["days_ago"]
            )
            for food in missing_foods
        ]
        
    except Exception as e:
        logger.error(f"Eksik besinler getirme hatası: {e}")
        raise HTTPException(status_code=500, detail="Eksik besinler getirilemedi.")

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(limit: int = 10):
    """Kullanıcı liderlik tablosu."""
    try:
        leaderboard = await crowdsource_system.get_user_leaderboard(limit)
        
        return [
            LeaderboardEntry(
                user_id=entry["user_id"],
                total_points=entry["total_points"],
                level=entry["level"],
                contributions=entry["contributions"],
                badges=entry["badges"],
                rank=idx + 1
            )
            for idx, entry in enumerate(leaderboard)
        ]
        
    except Exception as e:
        logger.error(f"Liderlik tablosu getirme hatası: {e}")
        raise HTTPException(status_code=500, detail="Liderlik tablosu getirilemedi.")

@router.get("/verification-queue", response_model=List[VerificationQueueEntry])
async def get_verification_queue(limit: int = 10):
    """Doğrulama bekleyen katkılar."""
    try:
        queue = await crowdsource_system.get_verification_queue(limit)
        
        return [
            VerificationQueueEntry(
                id=entry["id"],
                food_name=entry["food_name"],
                calories=entry["calories"],
                protein=entry["protein"],
                carbs=entry["carbs"],
                fat=entry["fat"],
                source=entry["source"],
                confidence=entry["confidence"],
                verifications_needed=entry["verifications_needed"]
            )
            for entry in queue
        ]
        
    except Exception as e:
        logger.error(f"Doğrulama kuyruğu getirme hatası: {e}")
        raise HTTPException(status_code=500, detail="Doğrulama kuyruğu getirilemedi.")

@router.get("/user-stats", response_model=UserStatsResponse)
async def get_user_stats(user_id: int = 1):  # TODO: Get from auth
    """Kullanıcı istatistikleri."""
    try:
        user_data = crowdsource_system.user_points.get(user_id, {
            "total_points": 0,
            "level": 1,
            "contributions": 0,
            "verifications": 0,
            "suggestions": 0,
            "badges": []
        })
        
        # Sıralama hesapla
        all_users = list(crowdsource_system.user_points.items())
        all_users.sort(key=lambda x: x[1]["total_points"], reverse=True)
        
        rank = 1
        for idx, (uid, _) in enumerate(all_users):
            if uid == user_id:
                rank = idx + 1
                break
        
        return UserStatsResponse(
            total_points=user_data["total_points"],
            level=user_data["level"],
            contributions=user_data["contributions"],
            verifications=user_data["verifications"],
            suggestions=user_data["suggestions"],
            badges=user_data["badges"],
            rank=rank
        )
        
    except Exception as e:
        logger.error(f"Kullanıcı istatistikleri getirme hatası: {e}")
        raise HTTPException(status_code=500, detail="Kullanıcı istatistikleri getirilemedi.")

@router.get("/daily-challenges")
async def get_daily_challenges():
    """Günlük challenge'lar."""
    try:
        challenges = await crowdsource_system.generate_daily_challenges()
        return {"challenges": challenges}
        
    except Exception as e:
        logger.error(f"Günlük challenge'lar getirme hatası: {e}")
        raise HTTPException(status_code=500, detail="Günlük challenge'lar getirilemedi.")

@router.get("/stats")
async def get_system_stats():
    """Sistem istatistikleri."""
    try:
        total_contributions = len(crowdsource_system.contributions)
        total_suggestions = len(crowdsource_system.suggestions)
        total_users = len(crowdsource_system.user_points)
        pending_verifications = len(crowdsource_system.verification_queue)
        
        return {
            "total_contributions": total_contributions,
            "total_suggestions": total_suggestions,
            "total_users": total_users,
            "pending_verifications": pending_verifications,
            "database_size": total_contributions + 385  # Mevcut veritabanı + katkılar
        }
        
    except Exception as e:
        logger.error(f"Sistem istatistikleri getirme hatası: {e}")
        raise HTTPException(status_code=500, detail="Sistem istatistikleri getirilemedi.")