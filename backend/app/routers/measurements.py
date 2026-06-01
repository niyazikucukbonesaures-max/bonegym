# Gelişmiş Ölçüm Router'ı
# GET    /                    → Geçmiş
# POST   /                    → Yeni ölçüm (gelişmiş doğrulama)
# DELETE /{id}                → Ölçüm sil
# GET    /trend               → Trend (days=30)
# GET    /delta               → İlk-son fark
# GET    /visualization/{type} → Görselleştirme verisi
# GET    /body-metrics        → Vücut metrikleri
# GET    /validation-history  → Doğrulama geçmişi

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.measurement_tracker import MeasurementTracker
from app.enhanced_measurement_tracker import enhanced_measurement_tracker
from app.schemas import MeasurementCreate, MeasurementDelta, MeasurementSchema
from app.cache import cache, invalidate_measurements_cache

router = APIRouter()
_tracker = MeasurementTracker()
_enhanced_tracker = enhanced_measurement_tracker


@router.get("/", response_model=List[MeasurementSchema])
async def get_history(
    limit: int = Query(default=20, ge=1, le=100, description="Sayfa başına kayıt"),
    offset: int = Query(default=0, ge=0, description="Başlangıç noktası"),
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
) -> List[MeasurementSchema]:
    """Ölçüm geçmişini sayfalı döndürür (varsayılan: son 20 kayıt)."""
    cache_key = f"measurements:{user_id}:history:{limit}:{offset}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    result = await _tracker.get_history(db, user_id, limit=limit, offset=offset)
    await cache.set(cache_key, result, ttl=60)  # 1 dakika
    return result


@router.post("/", status_code=201)
async def add_measurement(
    measurement: MeasurementCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Yeni bir ölçüm kaydeder (gelişmiş doğrulama ile)."""
    try:
        # Gelişmiş ölçüm kaydetme
        result = await _enhanced_tracker.record_multiple_measurements(measurement, db)
        
        if result.overall_status.value == "invalid":
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Ölçüm doğrulama başarısız",
                    "errors": [entry.validation_result.errors for entry in result.entries if entry.validation_result.errors],
                    "suggestions": result.recommendations
                }
            )
        
        # Başarılı kayıt
        response = {
            "measurement_id": result.measurement_id,
            "status": result.overall_status.value,
            "success_count": result.success_count,
            "total_warnings": result.total_warnings,
            "recommendations": result.recommendations
        }
        
        # Uyarılar varsa ekle
        if result.total_warnings > 0:
            response["warnings"] = [
                entry.validation_result.warnings 
                for entry in result.entries 
                if entry.validation_result.warnings
            ]
        
        # Cache'i temizle (measurements + dashboard)
        await invalidate_measurements_cache(measurement.user_id)
        await cache.delete(f"dashboard:{measurement.user_id}")
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ölçüm kaydetme hatası: {str(e)}")


@router.get("/visualization/{measurement_type}")
async def get_visualization_data(
    measurement_type: str = Path(..., description="Ölçüm tipi (weight_kg, waist_cm, vb.)"),
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    days: int = Query(30, ge=7, le=365, description="Gün sayısı"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """30 günlük ölçüm değişim görselleştirme verisi."""
    try:
        visualization_data = await _enhanced_tracker.get_measurement_visualization_data(
            user_id, measurement_type, db, days
        )
        
        return {
            "measurement_type": visualization_data.measurement_type,
            "period_days": days,
            "data_points": len(visualization_data.values),
            "dates": visualization_data.dates,
            "values": visualization_data.values,
            "trend_line": visualization_data.trend_line,
            "statistics": {
                "average": visualization_data.average_value,
                "min": visualization_data.min_value,
                "max": visualization_data.max_value,
                "total_change": visualization_data.total_change,
                "change_percentage": visualization_data.change_percentage
            },
            "trend_direction": visualization_data.trend_direction
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Görselleştirme verisi hatası: {str(e)}")


@router.get("/body-metrics")
async def get_body_metrics(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Vücut metrikleri hesaplama."""
    try:
        body_metrics = await _enhanced_tracker.calculate_body_metrics(user_id, db)
        
        return {
            "bmi": body_metrics.bmi,
            "waist_to_hip_ratio": body_metrics.waist_to_hip_ratio,
            "body_fat_estimate": body_metrics.body_fat_estimate,
            "muscle_mass_estimate": body_metrics.muscle_mass_estimate,
            "metabolic_age_estimate": body_metrics.metabolic_age_estimate,
            "health_indicators": body_metrics.health_indicators,
            "calculated_at": "2024-01-01T00:00:00"  # Şu anki zaman
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vücut metrikleri hesaplama hatası: {str(e)}")


@router.get("/validation-history")
async def get_validation_history(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    limit: int = Query(20, ge=1, le=100, description="Kayıt sayısı limiti"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Kilo doğrulama geçmişi."""
    try:
        from sqlalchemy import select, desc
        from app.models import WeightValidation
        
        stmt = (
            select(WeightValidation)
            .where(WeightValidation.user_id == user_id)
            .order_by(desc(WeightValidation.validated_at))
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        validations = result.scalars().all()
        
        validation_list = []
        for validation in validations:
            validation_list.append({
                "id": validation.id,
                "weight_kg": validation.weight_kg,
                "previous_weight_kg": validation.previous_weight_kg,
                "change_kg": validation.change_kg,
                "is_valid": validation.is_valid,
                "validation_reason": validation.validation_reason,
                "validated_at": validation.validated_at.isoformat()
            })
        
        return {
            "validations": validation_list,
            "total_count": len(validation_list),
            "valid_count": sum(1 for v in validations if v.is_valid),
            "invalid_count": sum(1 for v in validations if not v.is_valid)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Doğrulama geçmişi hatası: {str(e)}")


@router.delete("/{measurement_id}")
async def delete_measurement(
    measurement_id: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Bir ölçümü siler."""
    success = await _tracker.delete_measurement(db, measurement_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ölçüm bulunamadı")
    
    # Cache'i temizle
    await invalidate_measurements_cache(user_id)
    
    return {"message": "Ölçüm başarıyla silindi"}


@router.get("/trend")
async def get_trend(
    user_id: int = 1,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Son N günün ölçüm trend verisini döndürür."""
    trend = await _tracker.get_trend(db, user_id, days)
    return {
        "days": trend.days,
        "measurements": [m.model_dump() for m in trend.measurements],
    }


@router.get("/delta", response_model=MeasurementDelta)
async def get_delta(
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
) -> MeasurementDelta:
    """İlk ve son ölçüm arasındaki farkı döndürür."""
    return await _tracker.get_delta(db, user_id)
