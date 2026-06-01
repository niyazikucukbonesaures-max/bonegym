# Analiz ve Raporlama Router'ı
# GET    /reports/weekly      → Haftalık rapor
# GET    /reports/monthly     → Aylık rapor
# GET    /reports/quarterly   → Üç aylık rapor
# GET    /trends/weight       → Kilo trend analizi
# GET    /trends/plateau      → Plateau analizi
# GET    /trends/timeline     → Hedef timeline tahmini
# GET    /insights            → İlerleme insights
# GET    /performance         → Performans metrikleri

from typing import List, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.trend_analysis_engine import trend_analysis_engine
from app.enhanced_measurement_tracker import enhanced_measurement_tracker

router = APIRouter()


@router.get("/reports/weekly")
async def get_weekly_report(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    weeks: int = Query(4, ge=1, le=12, description="Hafta sayısı"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Haftalık ilerleme raporu oluşturur."""
    try:
        # Haftalık trend analizi
        weekly_trend = await trend_analysis_engine.calculate_weekly_average_change(user_id, db, weeks)
        
        # Vücut metrikleri
        body_metrics = await enhanced_measurement_tracker.calculate_body_metrics(user_id, db)
        
        # Plateau analizi
        plateau_analysis = await trend_analysis_engine.detect_weight_plateau(user_id, db)
        
        return {
            "report_type": "weekly",
            "period": {
                "weeks": weeks,
                "start_date": weekly_trend.period_start.isoformat(),
                "end_date": weekly_trend.period_end.isoformat()
            },
            "weight_analysis": {
                "total_change_kg": float(weekly_trend.weight_change_kg) if weekly_trend.weight_change_kg else None,
                "average_weekly_change": float(weekly_trend.average_weekly_change),
                "trend_direction": weekly_trend.trend_direction.value,
                "confidence_score": weekly_trend.confidence_score,
                "data_points": weekly_trend.data_points
            },
            "body_metrics": {
                "bmi": body_metrics.bmi,
                "waist_to_hip_ratio": body_metrics.waist_to_hip_ratio,
                "body_fat_estimate": body_metrics.body_fat_estimate,
                "muscle_mass_estimate": body_metrics.muscle_mass_estimate,
                "health_indicators": body_metrics.health_indicators
            },
            "plateau_status": {
                "status": plateau_analysis.status.value,
                "duration_days": plateau_analysis.plateau_duration_days,
                "recommendations": plateau_analysis.recommendations
            },
            "insights": weekly_trend.insights,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Haftalık rapor hatası: {str(e)}")


@router.get("/reports/monthly")
async def get_monthly_report(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    months: int = Query(3, ge=1, le=12, description="Ay sayısı"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Aylık ilerleme raporu oluşturur."""
    try:
        # Aylık trend (haftalık analizi genişletilmiş)
        weeks_in_months = months * 4
        monthly_trend = await trend_analysis_engine.calculate_weekly_average_change(user_id, db, weeks_in_months)
        
        # İlerleme insights
        insights = await trend_analysis_engine.generate_progress_insights(user_id, db)
        
        # Son 30 günün ölçüm verisi
        recent_measurements = await enhanced_measurement_tracker.get_measurement_visualization_data(
            user_id, "weight_kg", db, days=30
        )
        
        return {
            "report_type": "monthly",
            "period": {
                "months": months,
                "start_date": monthly_trend.period_start.isoformat(),
                "end_date": monthly_trend.period_end.isoformat()
            },
            "progress_summary": {
                "total_change_kg": float(monthly_trend.weight_change_kg) if monthly_trend.weight_change_kg else None,
                "monthly_average_change": float(monthly_trend.average_weekly_change) * 4,  # Haftalık * 4
                "trend_direction": monthly_trend.trend_direction.value,
                "consistency_score": monthly_trend.confidence_score
            },
            "measurement_statistics": {
                "total_measurements": len(recent_measurements.values),
                "average_value": recent_measurements.average_value,
                "min_value": recent_measurements.min_value,
                "max_value": recent_measurements.max_value,
                "total_change": recent_measurements.total_change,
                "change_percentage": recent_measurements.change_percentage
            },
            "insights": [
                {
                    "type": insight.type,
                    "title": insight.title,
                    "description": insight.description,
                    "priority": insight.priority,
                    "actionable": insight.actionable
                }
                for insight in insights
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aylık rapor hatası: {str(e)}")


@router.get("/reports/quarterly")
async def get_quarterly_report(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Üç aylık kapsamlı ilerleme raporu oluşturur."""
    try:
        # 12 haftalık trend analizi
        quarterly_trend = await trend_analysis_engine.calculate_weekly_average_change(user_id, db, 12)
        
        # Tüm ölçüm tiplerinin görselleştirme verisi
        measurement_types = ["weight_kg", "waist_cm", "hip_cm", "chest_cm", "arm_cm"]
        measurement_data = {}
        
        for measurement_type in measurement_types:
            try:
                data = await enhanced_measurement_tracker.get_measurement_visualization_data(
                    user_id, measurement_type, db, days=90
                )
                if data.values:  # Veri varsa ekle
                    measurement_data[measurement_type] = {
                        "total_change": data.total_change,
                        "change_percentage": data.change_percentage,
                        "trend_direction": data.trend_direction,
                        "data_points": len(data.values)
                    }
            except:
                continue  # Veri yoksa atla
        
        # Vücut kompozisyonu analizi
        body_metrics = await enhanced_measurement_tracker.calculate_body_metrics(user_id, db)
        
        # İlerleme insights
        insights = await trend_analysis_engine.generate_progress_insights(user_id, db)
        
        return {
            "report_type": "quarterly",
            "period": {
                "weeks": 12,
                "start_date": quarterly_trend.period_start.isoformat(),
                "end_date": quarterly_trend.period_end.isoformat()
            },
            "overall_progress": {
                "total_weight_change_kg": float(quarterly_trend.weight_change_kg) if quarterly_trend.weight_change_kg else None,
                "average_weekly_change": float(quarterly_trend.average_weekly_change),
                "trend_direction": quarterly_trend.trend_direction.value,
                "confidence_score": quarterly_trend.confidence_score,
                "data_quality": "Yüksek" if quarterly_trend.data_points > 20 else "Orta" if quarterly_trend.data_points > 10 else "Düşük"
            },
            "body_measurements": measurement_data,
            "body_composition": {
                "bmi": body_metrics.bmi,
                "waist_to_hip_ratio": body_metrics.waist_to_hip_ratio,
                "body_fat_estimate": body_metrics.body_fat_estimate,
                "muscle_mass_estimate": body_metrics.muscle_mass_estimate,
                "metabolic_age_estimate": body_metrics.metabolic_age_estimate,
                "health_indicators": body_metrics.health_indicators
            },
            "key_insights": [
                {
                    "type": insight.type,
                    "title": insight.title,
                    "description": insight.description,
                    "priority": insight.priority,
                    "actionable": insight.actionable,
                    "data_support": insight.data_support
                }
                for insight in insights[:3]  # En önemli 3 insight
            ],
            "recommendations": quarterly_trend.insights,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Üç aylık rapor hatası: {str(e)}")


@router.get("/trends/weight")
async def get_weight_trend_analysis(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    weeks: int = Query(8, ge=2, le=52, description="Analiz edilecek hafta sayısı"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Detaylı kilo trend analizi."""
    try:
        # Haftalık trend
        weekly_trend = await trend_analysis_engine.calculate_weekly_average_change(user_id, db, weeks)
        
        # Görselleştirme verisi
        visualization_data = await enhanced_measurement_tracker.get_measurement_visualization_data(
            user_id, "weight_kg", db, days=weeks*7
        )
        
        return {
            "analysis_period": {
                "weeks": weeks,
                "start_date": weekly_trend.period_start.isoformat(),
                "end_date": weekly_trend.period_end.isoformat()
            },
            "trend_analysis": {
                "direction": weekly_trend.trend_direction.value,
                "average_weekly_change": float(weekly_trend.average_weekly_change),
                "total_change": float(weekly_trend.weight_change_kg) if weekly_trend.weight_change_kg else None,
                "confidence_score": weekly_trend.confidence_score,
                "data_points": weekly_trend.data_points
            },
            "visualization_data": {
                "dates": visualization_data.dates,
                "values": visualization_data.values,
                "trend_line": visualization_data.trend_line,
                "statistics": {
                    "average": visualization_data.average_value,
                    "min": visualization_data.min_value,
                    "max": visualization_data.max_value,
                    "variance": visualization_data.max_value - visualization_data.min_value
                }
            },
            "insights": weekly_trend.insights,
            "analysis_quality": {
                "data_density": len(visualization_data.values) / (weeks * 7),
                "reliability": "Yüksek" if weekly_trend.confidence_score > 0.8 else "Orta" if weekly_trend.confidence_score > 0.5 else "Düşük"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kilo trend analizi hatası: {str(e)}")


@router.get("/trends/plateau")
async def get_plateau_analysis(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Detaylı plateau analizi."""
    try:
        plateau_analysis = await trend_analysis_engine.detect_weight_plateau(user_id, db)
        
        return {
            "plateau_status": plateau_analysis.status.value,
            "duration_days": plateau_analysis.plateau_duration_days,
            "weight_variance_kg": float(plateau_analysis.weight_variance_kg),
            "last_significant_change": plateau_analysis.last_significant_change.isoformat() if plateau_analysis.last_significant_change else None,
            "confidence_score": plateau_analysis.confidence_score,
            "analysis": {
                "is_plateau": plateau_analysis.status.value in ["potential_plateau", "confirmed_plateau"],
                "severity": "Yüksek" if plateau_analysis.plateau_duration_days > 21 else "Orta" if plateau_analysis.plateau_duration_days > 14 else "Düşük",
                "action_needed": plateau_analysis.status.value == "confirmed_plateau"
            },
            "recommendations": plateau_analysis.recommendations,
            "next_steps": [
                "Kalori alımınızı gözden geçirin",
                "Antrenman rutininizi değiştirin",
                "Stres seviyenizi kontrol edin",
                "Uyku kalitesini iyileştirin"
            ] if plateau_analysis.status.value == "confirmed_plateau" else []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plateau analizi hatası: {str(e)}")


@router.get("/trends/timeline")
async def get_goal_timeline_prediction(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    target_weight: float = Query(..., description="Hedef kilo (kg)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Hedef timeline tahmini."""
    try:
        timeline = await trend_analysis_engine.predict_goal_timeline(user_id, target_weight, db)
        
        return {
            "goal_analysis": {
                "current_weight_kg": float(timeline.current_weight_kg),
                "target_weight_kg": float(timeline.target_weight_kg),
                "weight_difference_kg": float(timeline.target_weight_kg - timeline.current_weight_kg),
                "goal_type": "weight_loss" if timeline.target_weight_kg < timeline.current_weight_kg else "weight_gain"
            },
            "timeline_prediction": {
                "estimated_days": timeline.estimated_days,
                "estimated_weeks": round(timeline.estimated_days / 7, 1),
                "estimated_date": timeline.estimated_date.isoformat(),
                "feasibility_score": timeline.feasibility_score
            },
            "rate_analysis": {
                "current_weekly_rate_kg": float(timeline.current_weekly_rate),
                "needed_weekly_rate_kg": float(timeline.weekly_rate_needed),
                "rate_adjustment_needed": abs(float(timeline.weekly_rate_needed - timeline.current_weekly_rate)) > 0.1
            },
            "feasibility_assessment": {
                "level": "Yüksek" if timeline.feasibility_score > 0.8 else "Orta" if timeline.feasibility_score > 0.5 else "Düşük",
                "realistic": timeline.feasibility_score > 0.6,
                "adjustments_needed": timeline.adjustments_needed
            },
            "recommendations": timeline.adjustments_needed
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline tahmini hatası: {str(e)}")


@router.get("/insights")
async def get_progress_insights(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """İlerleme insights'larını getirir."""
    try:
        insights = await trend_analysis_engine.generate_progress_insights(user_id, db)
        
        # Insights'ları kategorilere ayır
        categorized_insights = {
            "trend": [],
            "plateau": [],
            "consistency": [],
            "composition": [],
            "other": []
        }
        
        for insight in insights:
            category = insight.type if insight.type in categorized_insights else "other"
            categorized_insights[category].append({
                "title": insight.title,
                "description": insight.description,
                "priority": insight.priority,
                "actionable": insight.actionable,
                "data_support": insight.data_support
            })
        
        return {
            "user_id": user_id,
            "total_insights": len(insights),
            "insights_by_category": categorized_insights,
            "priority_insights": [
                {
                    "title": insight.title,
                    "description": insight.description,
                    "priority": insight.priority,
                    "actionable": insight.actionable
                }
                for insight in sorted(insights, key=lambda x: x.priority, reverse=True)[:3]
            ],
            "actionable_count": sum(1 for insight in insights if insight.actionable),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İlerleme insights hatası: {str(e)}")


@router.get("/performance")
async def get_performance_metrics(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Performans metrikleri ve KPI'ları getirir."""
    try:
        # Haftalık trend
        weekly_trend = await trend_analysis_engine.calculate_weekly_average_change(user_id, db, 4)
        
        # Plateau analizi
        plateau_analysis = await trend_analysis_engine.detect_weight_plateau(user_id, db)
        
        # Vücut metrikleri
        body_metrics = await enhanced_measurement_tracker.calculate_body_metrics(user_id, db)
        
        # Son 30 günün ölçüm verisi
        recent_data = await enhanced_measurement_tracker.get_measurement_visualization_data(
            user_id, "weight_kg", db, days=30
        )
        
        # KPI hesaplamaları
        consistency_score = len(recent_data.values) / 30.0  # Son 30 günde ölçüm yoğunluğu
        progress_score = min(100, abs(float(weekly_trend.average_weekly_change)) * 100)  # Haftalık değişim skoru
        health_score = 85 if body_metrics.bmi and 18.5 <= body_metrics.bmi <= 25 else 70  # BMI bazlı sağlık skoru
        
        return {
            "user_id": user_id,
            "performance_period": "Son 30 gün",
            "key_metrics": {
                "consistency_score": round(consistency_score * 100, 1),
                "progress_score": round(progress_score, 1),
                "health_score": health_score,
                "overall_score": round((consistency_score * 100 + progress_score + health_score) / 3, 1)
            },
            "trend_metrics": {
                "weekly_change_kg": float(weekly_trend.average_weekly_change),
                "trend_direction": weekly_trend.trend_direction.value,
                "confidence_level": round(weekly_trend.confidence_score * 100, 1),
                "data_quality": weekly_trend.data_points
            },
            "plateau_metrics": {
                "plateau_risk": plateau_analysis.status.value,
                "plateau_duration": plateau_analysis.plateau_duration_days,
                "weight_stability": float(plateau_analysis.weight_variance_kg)
            },
            "measurement_metrics": {
                "total_measurements": len(recent_data.values),
                "measurement_frequency": round(len(recent_data.values) / 30, 2),
                "data_completeness": round(len(recent_data.values) / 30 * 100, 1)
            },
            "health_indicators": body_metrics.health_indicators,
            "performance_grade": {
                "overall": "A" if consistency_score > 0.8 and progress_score > 50 else "B" if consistency_score > 0.6 else "C",
                "consistency": "A" if consistency_score > 0.8 else "B" if consistency_score > 0.6 else "C",
                "progress": "A" if progress_score > 70 else "B" if progress_score > 40 else "C"
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performans metrikleri hatası: {str(e)}")