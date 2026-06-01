# Bildirim Router'ı - Gelişmiş Akıllı Bildirim Sistemi
# GET    /preferences         → Bildirim tercihleri getir
# POST   /preferences         → Bildirim tercihleri güncelle
# GET    /schedule            → Zamanlanmış bildirimler
# POST   /schedule            → Akıllı hatırlatma zamanla
# GET    /patterns            → Kullanıcı davranış kalıpları
# GET    /history             → Bildirim geçmişi
# POST   /test                → Test bildirimi gönder
# GET    /                    → Aktif bildirimleri getir (eski sistem)

from typing import List, Optional
from datetime import datetime, date, timedelta, timezone

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db
from app.models import NotificationPreferences, WorkoutLog, CreatineDose, Measurement
from app.smart_notification_system import smart_notification_system
from app.schemas import NotificationPreferencesCreate, NotificationPreferencesSchema, NotificationSchema

router = APIRouter()


@router.get("/preferences", response_model=Optional[NotificationPreferencesSchema])
async def get_notification_preferences(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    db: AsyncSession = Depends(get_db),
) -> Optional[NotificationPreferencesSchema]:
    """Kullanıcının bildirim tercihlerini getirir."""
    try:
        stmt = select(NotificationPreferences).where(NotificationPreferences.user_id == user_id)
        result = await db.execute(stmt)
        preferences = result.scalar_one_or_none()
        
        if not preferences:
            return None
        
        return NotificationPreferencesSchema(
            id=preferences.id,
            user_id=preferences.user_id,
            weight_reminders=preferences.weight_reminders,
            measurement_reminders=preferences.measurement_reminders,
            motivation_messages=preferences.motivation_messages,
            progress_reports=preferences.progress_reports,
            max_daily_notifications=preferences.max_daily_notifications,
            preferred_reminder_time=preferences.preferred_reminder_time,
            quiet_hours_start=preferences.quiet_hours_start,
            quiet_hours_end=preferences.quiet_hours_end,
            created_at=preferences.created_at,
            updated_at=preferences.updated_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bildirim tercihleri getirme hatası: {str(e)}")


@router.post("/preferences", response_model=NotificationPreferencesSchema, status_code=201)
async def update_notification_preferences(
    preferences_data: NotificationPreferencesCreate,
    db: AsyncSession = Depends(get_db),
) -> NotificationPreferencesSchema:
    """Bildirim tercihlerini günceller veya oluşturur."""
    try:
        # Mevcut tercihleri kontrol et
        stmt = select(NotificationPreferences).where(NotificationPreferences.user_id == preferences_data.user_id)
        result = await db.execute(stmt)
        existing_preferences = result.scalar_one_or_none()
        
        if existing_preferences:
            # Güncelle
            existing_preferences.weight_reminders = preferences_data.weight_reminders
            existing_preferences.measurement_reminders = preferences_data.measurement_reminders
            existing_preferences.motivation_messages = preferences_data.motivation_messages
            existing_preferences.progress_reports = preferences_data.progress_reports
            existing_preferences.max_daily_notifications = preferences_data.max_daily_notifications
            existing_preferences.preferred_reminder_time = preferences_data.preferred_reminder_time
            existing_preferences.quiet_hours_start = preferences_data.quiet_hours_start
            existing_preferences.quiet_hours_end = preferences_data.quiet_hours_end
            existing_preferences.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
            await db.refresh(existing_preferences)
            preferences = existing_preferences
        else:
            # Yeni oluştur
            preferences = NotificationPreferences(
                user_id=preferences_data.user_id,
                weight_reminders=preferences_data.weight_reminders,
                measurement_reminders=preferences_data.measurement_reminders,
                motivation_messages=preferences_data.motivation_messages,
                progress_reports=preferences_data.progress_reports,
                max_daily_notifications=preferences_data.max_daily_notifications,
                preferred_reminder_time=preferences_data.preferred_reminder_time,
                quiet_hours_start=preferences_data.quiet_hours_start,
                quiet_hours_end=preferences_data.quiet_hours_end
            )
            
            db.add(preferences)
            await db.commit()
            await db.refresh(preferences)
        
        return NotificationPreferencesSchema(
            id=preferences.id,
            user_id=preferences.user_id,
            weight_reminders=preferences.weight_reminders,
            measurement_reminders=preferences.measurement_reminders,
            motivation_messages=preferences.motivation_messages,
            progress_reports=preferences.progress_reports,
            max_daily_notifications=preferences.max_daily_notifications,
            preferred_reminder_time=preferences.preferred_reminder_time,
            quiet_hours_start=preferences.quiet_hours_start,
            quiet_hours_end=preferences.quiet_hours_end,
            created_at=preferences.created_at,
            updated_at=preferences.updated_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bildirim tercihleri kaydetme hatası: {str(e)}")


@router.get("/schedule")
async def get_scheduled_notifications(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Zamanlanmış akıllı hatırlatmaları getirir."""
    try:
        scheduled_notifications = await smart_notification_system.schedule_smart_reminders(user_id, db)
        
        notifications_list = []
        for notification in scheduled_notifications:
            notifications_list.append({
                "type": notification.notification_type.value,
                "title": notification.title,
                "message": notification.message,
                "scheduled_time": notification.scheduled_time.isoformat(),
                "priority": notification.priority.value,
                "metadata": notification.metadata
            })
        
        return {
            "user_id": user_id,
            "scheduled_notifications": notifications_list,
            "total_count": len(notifications_list),
            "next_notification": notifications_list[0]["scheduled_time"] if notifications_list else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Zamanlanmış bildirimler hatası: {str(e)}")


@router.post("/schedule")
async def create_smart_reminders(
    user_id: int = Body(..., description="Kullanıcı ID'si"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Akıllı hatırlatmaları zamanlar ve oluşturur."""
    try:
        # Akıllı hatırlatmaları zamanla
        scheduled_notifications = await smart_notification_system.schedule_smart_reminders(user_id, db)
        
        # Optimal hatırlatma zamanını hesapla
        optimal_time = await smart_notification_system.get_optimal_reminder_time(user_id, db)
        
        return {
            "user_id": user_id,
            "scheduled_count": len(scheduled_notifications),
            "optimal_reminder_time": optimal_time.isoformat(),
            "next_reminders": [
                {
                    "type": n.notification_type.value,
                    "title": n.title,
                    "scheduled_time": n.scheduled_time.isoformat(),
                    "priority": n.priority.value
                }
                for n in scheduled_notifications[:3]  # İlk 3 hatırlatma
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Akıllı hatırlatma oluşturma hatası: {str(e)}")


@router.get("/patterns")
async def get_user_patterns(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Kullanıcı davranış kalıplarını analiz eder."""
    try:
        patterns = await smart_notification_system.analyze_user_patterns(user_id, db)
        
        return {
            "user_id": user_id,
            "preferred_measurement_time": patterns.preferred_measurement_time.strftime("%H:%M") if patterns.preferred_measurement_time else None,
            "most_active_hours": patterns.most_active_hours,
            "measurement_frequency": patterns.measurement_frequency,
            "consistency_score": patterns.consistency_score,
            "activity_pattern": patterns.activity_pattern.value,
            "last_measurement_date": patterns.last_measurement_date.isoformat() if patterns.last_measurement_date else None,
            "average_gap_days": patterns.average_gap_days,
            "analysis": {
                "consistency_level": "Yüksek" if patterns.consistency_score > 0.7 else "Orta" if patterns.consistency_score > 0.4 else "Düşük",
                "activity_description": {
                    "morning_person": "Sabah kişisi - erken saatlerde aktif",
                    "evening_person": "Akşam kişisi - geç saatlerde aktif", 
                    "irregular": "Düzensiz - belirli bir kalıp yok",
                    "consistent": "Tutarlı - düzenli ölçüm alışkanlığı"
                }.get(patterns.activity_pattern.value, "Bilinmiyor")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kullanıcı kalıpları analizi hatası: {str(e)}")


@router.get("/history")
async def get_notification_history(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    limit: int = Query(20, ge=1, le=100, description="Kayıt sayısı limiti"),
    notification_type: Optional[str] = Query(None, description="Bildirim tipi filtresi"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Bildirim geçmişini getirir."""
    try:
        # TODO: NotificationLog tablosu oluşturulduğunda gerçek veri dönecek
        # Şimdilik mock veri döndürüyoruz
        
        mock_history = [
            {
                "id": 1,
                "type": "weight_reminder",
                "title": "Ölçüm Zamanı! ⚖️",
                "message": "3 gündür ölçüm almıyorsun. Hedefine ulaşmak için düzenli takip önemli!",
                "sent_at": "2024-01-01T08:00:00",
                "opened": True,
                "acted_upon": True
            },
            {
                "id": 2,
                "type": "motivation_message", 
                "title": "Motivasyon Zamanı! 💪",
                "message": "Harika gidiyorsun! Her küçük adım büyük değişimlere yol açar",
                "sent_at": "2024-01-01T10:00:00",
                "opened": True,
                "acted_upon": False
            }
        ]
        
        # Tip filtresi uygula
        if notification_type:
            mock_history = [h for h in mock_history if h["type"] == notification_type]
        
        # Limit uygula
        mock_history = mock_history[:limit]
        
        return {
            "user_id": user_id,
            "notifications": mock_history,
            "total_count": len(mock_history),
            "statistics": {
                "total_sent": len(mock_history),
                "total_opened": sum(1 for h in mock_history if h["opened"]),
                "total_acted_upon": sum(1 for h in mock_history if h["acted_upon"]),
                "open_rate": sum(1 for h in mock_history if h["opened"]) / len(mock_history) if mock_history else 0,
                "action_rate": sum(1 for h in mock_history if h["acted_upon"]) / len(mock_history) if mock_history else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bildirim geçmişi hatası: {str(e)}")


@router.post("/test")
async def send_test_notification(
    user_id: int = Body(..., description="Kullanıcı ID'si"),
    notification_type: str = Body("motivation_message", description="Test bildirim tipi"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Test bildirimi gönderir."""
    try:
        # Bildirim gönderilip gönderilmeyeceğini kontrol et
        should_send = await smart_notification_system.should_send_reminder(user_id, notification_type, db)
        
        if not should_send:
            return {
                "user_id": user_id,
                "test_sent": False,
                "reason": "Bildirim tercihleri veya sınırlar nedeniyle gönderilemedi",
                "message": "Test bildirimi gönderilmedi"
            }
        
        # Test mesajı oluştur
        test_messages = {
            "weight_reminder": "Bu bir test kilo hatırlatmasıdır ⚖️",
            "motivation_message": "Bu bir test motivasyon mesajıdır 💪",
            "progress_report": "Bu bir test ilerleme raporu bildirimidir 📊",
            "plateau_alert": "Bu bir test plateau uyarısıdır 📈"
        }
        
        test_message = test_messages.get(notification_type, "Bu bir test bildirimidir 🔔")
        
        # Gerçek uygulamada burada bildirim servisi çağrılacak
        # Şimdilik başarılı response döndürüyoruz
        
        return {
            "user_id": user_id,
            "test_sent": True,
            "notification_type": notification_type,
            "message": test_message,
            "sent_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test bildirimi hatası: {str(e)}")


# Eski sistem uyumluluğu için
@router.get("/", response_model=List[NotificationSchema])
async def get_notifications(
    db: AsyncSession = Depends(get_db),
) -> List[NotificationSchema]:
    """Aktif bildirimleri getirir (eski sistem uyumluluğu)."""
    notifications = []
    now = datetime.now(timezone.utc)
    
    # 3 gün antrenman yapılmadı kontrolü
    three_days_ago = now - timedelta(days=3)
    result = await db.execute(
        select(func.max(WorkoutLog.completed_at))
    )
    last_workout = result.scalar()
    
    if not last_workout or last_workout < three_days_ago:
        notifications.append(NotificationSchema(
            id="workout_reminder",
            type="warning",
            title="Antrenman Hatırlatması",
            message="3 gündür antrenman yapmadınız. Hedeflerinize ulaşmak için düzenli antrenman önemli!",
            created_at=now
        ))
    
    # 7 gün kilo kaydı yapılmadı kontrolü
    seven_days_ago = now - timedelta(days=7)
    result = await db.execute(
        select(func.max(Measurement.measured_at))
        .where(Measurement.user_id == 1)
        .where(Measurement.weight_kg.isnot(None))
    )
    last_weight = result.scalar()
    
    if not last_weight or last_weight < seven_days_ago:
        notifications.append(NotificationSchema(
            id="weight_reminder",
            type="info",
            title="Kilo Takibi Hatırlatması",
            message="7 gündür kilo kaydı yapmadınız. İlerlemenizi takip etmek için düzenli ölçüm yapın.",
            created_at=now
        ))
    
    # Kreatin hatırlatması - bugün alındı mı?
    today = now.date()
    result = await db.execute(
        select(CreatineDose)
        .where(CreatineDose.user_id == 1)
        .where(func.date(CreatineDose.taken_at) == today)
    )
    today_dose = result.scalar_one_or_none()
    
    if not today_dose:
        notifications.append(NotificationSchema(
            id="creatine_reminder",
            type="info",
            title="Kreatin Hatırlatması",
            message="Bugün henüz kreatin almadınız. Düzenli alım için unutmayın!",
            created_at=now
        ))
    
    # Kreatin faz geçişi kontrolü
    result = await db.execute(
        select(CreatineDose)
        .where(CreatineDose.user_id == 1)
        .order_by(CreatineDose.taken_at.asc())
        .limit(1)
    )
    first_dose = result.scalar_one_or_none()
    
    if first_dose:
        days_since_start = (now.date() - first_dose.taken_at.date()).days
        if days_since_start == 7:
            notifications.append(NotificationSchema(
                id="creatine_phase_transition",
                type="success",
                title="Kreatin Faz Geçişi",
                message="Yükleme fazı tamamlandı! Artık idame fazına geçebilirsiniz (günde 3-5g).",
                created_at=now
            ))
    
    return notifications