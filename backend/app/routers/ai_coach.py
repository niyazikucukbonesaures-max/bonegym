# AI Coach Router - AI Antrenman Koçu API Endpoints
# Antrenman önerileri, geri bildirim ve ilerleme takibi

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.ai_coach_service import ai_coach_service
from app.routers.auth import require_auth
from app.schemas_auth import UserSchema

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class RecommendationResponse(BaseModel):
    """Antrenman önerisi yanıt modeli."""
    id: int
    type: str
    workout_plan: Optional[Dict] = None
    intensity: str
    duration: int
    motivation_message: str
    calorie_analysis: Dict
    created_at: str


class FeedbackRequest(BaseModel):
    """Kullanıcı geri bildirim istek modeli."""
    recommendation_id: int = Field(..., description="Öneri ID'si")
    feedback: str = Field(..., description="Geri bildirim türü", pattern="^(accepted|rejected|modified)$")
    reason: Optional[str] = Field(None, description="Geri bildirim nedeni")


class FeedbackResponse(BaseModel):
    """Geri bildirim yanıt modeli."""
    success: bool
    message: str


class ProgressResponse(BaseModel):
    """İlerleme analizi yanıt modeli."""
    weekly_stats: list
    overall_trend: str
    total_workouts: int
    consistency_score: float


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@router.get("/recommendation", response_model=RecommendationResponse)
async def get_daily_recommendation(
    current_user: UserSchema = Depends(require_auth)
) -> RecommendationResponse:
    """
    Kullanıcı için günlük antrenman önerisi getirir.
    
    Kalori dengesi analizi, kullanıcı tercihleri ve ilerleme durumuna göre
    kişiselleştirilmiş antrenman önerisi oluşturur.
    """
    try:
        recommendation = await ai_coach_service.get_daily_recommendation(current_user.id)
        return RecommendationResponse(**recommendation)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kullanıcı profili bulunamadı: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Öneri oluşturulurken hata: {str(e)}"
        )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback_data: FeedbackRequest,
    current_user: UserSchema = Depends(require_auth)
) -> FeedbackResponse:
    """
    Kullanıcı geri bildirimini işler.
    
    Kullanıcının antrenman önerisine verdiği geri bildirimi kaydeder
    ve AI öğrenme algoritmasını günceller.
    """
    try:
        success = await ai_coach_service.process_user_feedback(
            user_id=current_user.id,
            recommendation_id=feedback_data.recommendation_id,
            feedback=feedback_data.feedback,
            reason=feedback_data.reason
        )
        
        if success:
            return FeedbackResponse(
                success=True,
                message="Geri bildiriminiz başarıyla kaydedildi."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Öneri bulunamadı veya size ait değil."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geri bildirim işlenirken hata: {str(e)}"
        )


@router.get("/progress", response_model=ProgressResponse)
async def get_progress_insights(
    current_user: UserSchema = Depends(require_auth)
) -> ProgressResponse:
    """
    Kullanıcının ilerleme analizini getirir.
    
    Son 4 haftanın antrenman verilerini analiz ederek
    ilerleme istatistikleri ve öngörüler sunar.
    """
    try:
        progress_data = await ai_coach_service.get_progress_insights(current_user.id)
        return ProgressResponse(**progress_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"İlerleme analizi alınırken hata: {str(e)}"
        )


@router.get("/status")
async def get_coach_status(
    current_user: UserSchema = Depends(require_auth)
) -> Dict:
    """
    AI Coach durumu ve kullanıcı istatistiklerini getirir.
    
    Kullanıcının AI Coach ile etkileşim geçmişi ve
    genel sistem durumu bilgilerini döndürür.
    """
    try:
        # Bu endpoint gelecekte genişletilebilir
        return {
            "status": "active",
            "user_id": current_user.id,
            "last_recommendation": None,  # Son öneri tarihi
            "total_recommendations": 0,   # Toplam öneri sayısı
            "acceptance_rate": 0.0,       # Kabul oranı
            "message": "AI Coach aktif ve hazır!"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Durum bilgisi alınırken hata: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------

@router.get("/health")
async def health_check() -> Dict:
    """AI Coach servisinin sağlık durumunu kontrol eder."""
    try:
        # Basit sağlık kontrolü
        return {
            "status": "healthy",
            "service": "ai_coach",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI Coach servisi kullanılamıyor: {str(e)}"
        )