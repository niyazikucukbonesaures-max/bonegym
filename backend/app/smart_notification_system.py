# Fitness ve Kalori Takip Uygulaması - Akıllı Bildirim Sistemi
# Kullanıcıya hatırlatma ve motivasyon bildirimleri gönderen akıllı sistem

from dataclasses import dataclass
from datetime import datetime, date, timedelta, time
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
import random

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Measurement, NotificationPreferences, UserProfile, 
    FoodLog, WorkoutLog, TrendAnalysis
)


# ---------------------------------------------------------------------------
# Enum ve Sabitler
# ---------------------------------------------------------------------------

class NotificationType(Enum):
    """Bildirim türleri."""
    WEIGHT_REMINDER = "weight_reminder"
    MEASUREMENT_REMINDER = "measurement_reminder"
    MOTIVATION_MESSAGE = "motivation_message"
    PROGRESS_REPORT = "progress_report"
    GOAL_ACHIEVEMENT = "goal_achievement"
    PLATEAU_ALERT = "plateau_alert"
    CONSISTENCY_PRAISE = "consistency_praise"


class NotificationPriority(Enum):
    """Bildirim öncelik seviyeleri."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class UserActivityPattern(Enum):
    """Kullanıcı aktivite kalıpları."""
    MORNING_PERSON = "morning_person"
    EVENING_PERSON = "evening_person"
    IRREGULAR = "irregular"
    CONSISTENT = "consistent"


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------

@dataclass
class UserPatterns:
    """Kullanıcı davranış kalıpları."""
    preferred_measurement_time: Optional[time]
    most_active_hours: List[int]
    measurement_frequency: float  # günde kaç ölçüm
    consistency_score: float  # 0-1 arası
    activity_pattern: UserActivityPattern
    last_measurement_date: Optional[date]
    average_gap_days: float


@dataclass
class ScheduledNotification:
    """Zamanlanmış bildirim."""
    notification_type: NotificationType
    title: str
    message: str
    scheduled_time: datetime
    priority: NotificationPriority
    user_id: int
    metadata: Dict[str, Any]


@dataclass
class ProgressData:
    """İlerleme verisi."""
    current_weight: Optional[float]
    target_weight: Optional[float]
    weekly_change: float
    goal_progress_percentage: float
    days_since_start: int
    consistency_score: float
    plateau_days: int
    achievements: List[str]


@dataclass
class NotificationAnalytics:
    """Bildirim analitikleri."""
    total_sent: int
    total_opened: int
    total_acted_upon: int
    open_rate: float
    action_rate: float
    best_time_to_send: time
    most_effective_type: NotificationType


# ---------------------------------------------------------------------------
# SmartNotificationSystem Sınıfı
# ---------------------------------------------------------------------------

class SmartNotificationSystem:
    """Akıllı bildirim ve hatırlatma sistemi."""
    
    # Sabitler
    MAX_DAILY_NOTIFICATIONS = 2
    MIN_HOURS_BETWEEN_NOTIFICATIONS = 4
    PLATEAU_THRESHOLD_DAYS = 14
    CONSISTENCY_THRESHOLD = 0.7
    
    # Motivasyon mesajları
    MOTIVATION_MESSAGES = {
        "weight_loss": [
            "Harika gidiyorsun! Her küçük adım büyük değişimlere yol açar 💪",
            "Hedefine yaklaşıyorsun! Kararlılığın seni başarıya götürecek 🎯",
            "Bugün de kendine yatırım yap! Ölçümlerini almayı unutma 📏",
            "İlerleme kaydediyorsun! Bu momentum'u korumaya devam et 🚀",
            "Sağlıklı yaşam yolculuğunda her gün yeni bir fırsat ✨"
        ],
        "weight_gain": [
            "Hedefine doğru ilerlemek için bugün de ölçümlerini al! 💪",
            "Sağlıklı kilo alma yolculuğunda tutarlılık çok önemli 📈",
            "Her ölçüm seni hedefe bir adım daha yaklaştırıyor 🎯",
            "Güçlü ve sağlıklı olmak için bugün de kendine odaklan! 💯",
            "İlerleme kaydetmek için düzenli takip şart! 📊"
        ],
        "maintenance": [
            "Formunu korumak için bugün de ölçümlerini kontrol et! ⚖️",
            "Sağlıklı yaşam tarzını sürdürmek harika! 🌟",
            "Dengeli yaşam için düzenli takip çok değerli 📋",
            "Mevcut formunu koruman gerçekten başarılı! 👏",
            "Sağlıklı alışkanlıkların seni güçlü kılıyor 💚"
        ],
        "plateau": [
            "Plateau dönemleri normal! Sabırlı olmaya devam et 🧘‍♀️",
            "Vücudun adapte oluyor, bu geçici bir durum 🔄",
            "Plateau'yu aşmak için rutinini gözden geçirebilirsin 🔍",
            "Her plateau'dan sonra yeni bir ilerleme dönemi gelir! 📈",
            "Sabır ve tutarlılık plateau'yu aşmanın anahtarı 🗝️"
        ]
    }
    
    async def analyze_user_patterns(
        self, 
        user_id: int, 
        db: AsyncSession
    ) -> UserPatterns:
        """Kullanıcı davranış kalıplarını analiz eder.
        
        Args:
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            
        Returns:
            UserPatterns: Kullanıcı davranış kalıpları
        """
        # Son 30 günün ölçümlerini al
        cutoff_date = datetime.now() - timedelta(days=30)
        
        stmt = (
            select(Measurement)
            .where(
                and_(
                    Measurement.user_id == user_id,
                    Measurement.measured_at >= cutoff_date
                )
            )
            .order_by(Measurement.measured_at.asc())
        )
        
        result = await db.execute(stmt)
        measurements = result.scalars().all()
        
        if not measurements:
            return UserPatterns(
                preferred_measurement_time=None,
                most_active_hours=[],
                measurement_frequency=0.0,
                consistency_score=0.0,
                activity_pattern=UserActivityPattern.IRREGULAR,
                last_measurement_date=None,
                average_gap_days=0.0
            )
        
        # Ölçüm saatlerini analiz et
        measurement_hours = [m.measured_at.hour for m in measurements]
        most_active_hours = self._find_most_active_hours(measurement_hours)
        
        # Tercih edilen ölçüm saati
        preferred_hour = max(set(measurement_hours), key=measurement_hours.count) if measurement_hours else 8
        preferred_measurement_time = time(hour=preferred_hour, minute=0)
        
        # Ölçüm sıklığı
        days_span = (measurements[-1].measured_at - measurements[0].measured_at).days or 1
        measurement_frequency = len(measurements) / days_span
        
        # Tutarlılık skoru
        consistency_score = self._calculate_consistency_score(measurements)
        
        # Aktivite kalıbı
        activity_pattern = self._determine_activity_pattern(measurement_hours, consistency_score)
        
        # Son ölçüm tarihi
        last_measurement_date = measurements[-1].measured_at.date()
        
        # Ortalama ölçüm aralığı
        if len(measurements) > 1:
            gaps = []
            for i in range(1, len(measurements)):
                gap = (measurements[i].measured_at - measurements[i-1].measured_at).days
                gaps.append(gap)
            average_gap_days = sum(gaps) / len(gaps)
        else:
            average_gap_days = 0.0
        
        return UserPatterns(
            preferred_measurement_time=preferred_measurement_time,
            most_active_hours=most_active_hours,
            measurement_frequency=measurement_frequency,
            consistency_score=consistency_score,
            activity_pattern=activity_pattern,
            last_measurement_date=last_measurement_date,
            average_gap_days=average_gap_days
        )
    
    async def get_optimal_reminder_time(
        self, 
        user_id: int, 
        db: AsyncSession
    ) -> datetime:
        """Optimal hatırlatma zamanını hesaplar.
        
        Args:
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            
        Returns:
            datetime: Optimal hatırlatma zamanı
        """
        # Kullanıcı tercihlerini al
        preferences = await self._get_notification_preferences(user_id, db)
        
        # Kullanıcı kalıplarını analiz et
        patterns = await self.analyze_user_patterns(user_id, db)
        
        # Tercih edilen saat varsa onu kullan
        if preferences and preferences.preferred_reminder_time:
            try:
                hour, minute = map(int, preferences.preferred_reminder_time.split(':'))
                preferred_time = time(hour=hour, minute=minute)
            except:
                preferred_time = patterns.preferred_measurement_time
        else:
            preferred_time = patterns.preferred_measurement_time
        
        # Varsayılan saat (sabah 8:00)
        if not preferred_time:
            preferred_time = time(hour=8, minute=0)
        
        # Sessiz saatleri kontrol et
        if preferences:
            quiet_start = self._parse_time(preferences.quiet_hours_start)
            quiet_end = self._parse_time(preferences.quiet_hours_end)
            
            if quiet_start and quiet_end:
                if self._is_in_quiet_hours(preferred_time, quiet_start, quiet_end):
                    # Sessiz saatlerin dışına çıkar
                    preferred_time = quiet_end
        
        # Bugünün tarihiyle birleştir
        today = datetime.now().date()
        optimal_time = datetime.combine(today, preferred_time)
        
        # Geçmişte ise yarına al
        if optimal_time <= datetime.now():
            optimal_time += timedelta(days=1)
        
        return optimal_time
    
    def generate_motivation_message(self, progress_data: ProgressData) -> str:
        """Motivasyon mesajı oluşturur.
        
        Args:
            progress_data: İlerleme verisi
            
        Returns:
            str: Motivasyon mesajı
        """
        # Hedef tipini belirle
        if progress_data.target_weight and progress_data.current_weight:
            if progress_data.target_weight < progress_data.current_weight:
                goal_type = "weight_loss"
            elif progress_data.target_weight > progress_data.current_weight:
                goal_type = "weight_gain"
            else:
                goal_type = "maintenance"
        else:
            goal_type = "maintenance"
        
        # Plateau kontrolü
        if progress_data.plateau_days >= self.PLATEAU_THRESHOLD_DAYS:
            goal_type = "plateau"
        
        # Mesaj kategorisinden rastgele seç
        messages = self.MOTIVATION_MESSAGES.get(goal_type, self.MOTIVATION_MESSAGES["maintenance"])
        base_message = random.choice(messages)
        
        # İlerleme bilgisi ekle
        if progress_data.goal_progress_percentage > 0:
            progress_text = f" Hedefinin %{progress_data.goal_progress_percentage:.0f}'ini tamamladın!"
            base_message += progress_text
        
        return base_message
    
    async def should_send_reminder(
        self, 
        user_id: int, 
        notification_type: str, 
        db: AsyncSession
    ) -> bool:
        """Hatırlatma gönderilip gönderilmeyeceğini kontrol eder.
        
        Args:
            user_id: Kullanıcı ID'si
            notification_type: Bildirim tipi
            db: Veritabanı oturumu
            
        Returns:
            bool: Gönderilecekse True
        """
        # Kullanıcı tercihlerini kontrol et
        preferences = await self._get_notification_preferences(user_id, db)
        
        if not preferences:
            return True  # Varsayılan: bildirimlere izin ver
        
        # Bildirim tipi kontrolü
        if notification_type == "weight_reminder" and not preferences.weight_reminders:
            return False
        elif notification_type == "measurement_reminder" and not preferences.measurement_reminders:
            return False
        elif notification_type == "motivation_message" and not preferences.motivation_messages:
            return False
        elif notification_type == "progress_report" and not preferences.progress_reports:
            return False
        
        # Günlük bildirim sınırı kontrolü
        today_notifications = await self._count_todays_notifications(user_id, db)
        max_notifications = preferences.max_daily_notifications or self.MAX_DAILY_NOTIFICATIONS
        
        if today_notifications >= max_notifications:
            return False
        
        # Son bildirim zamanı kontrolü
        last_notification_time = await self._get_last_notification_time(user_id, db)
        if last_notification_time:
            hours_since_last = (datetime.now() - last_notification_time).total_seconds() / 3600
            if hours_since_last < self.MIN_HOURS_BETWEEN_NOTIFICATIONS:
                return False
        
        # Sessiz saatler kontrolü
        current_time = datetime.now().time()
        quiet_start = self._parse_time(preferences.quiet_hours_start)
        quiet_end = self._parse_time(preferences.quiet_hours_end)
        
        if quiet_start and quiet_end:
            if self._is_in_quiet_hours(current_time, quiet_start, quiet_end):
                return False
        
        return True
    
    async def schedule_smart_reminders(
        self, 
        user_id: int, 
        db: AsyncSession
    ) -> List[ScheduledNotification]:
        """Akıllı hatırlatmaları zamanlar.
        
        Args:
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            
        Returns:
            List[ScheduledNotification]: Zamanlanmış bildirimler
        """
        scheduled_notifications = []
        
        # Kullanıcı kalıplarını analiz et
        patterns = await self.analyze_user_patterns(user_id, db)
        
        # İlerleme verilerini al
        progress_data = await self._get_progress_data(user_id, db)
        
        # 1. Kilo ölçüm hatırlatması
        if await self.should_send_reminder(user_id, "weight_reminder", db):
            days_since_last = (datetime.now().date() - patterns.last_measurement_date).days if patterns.last_measurement_date else 999
            
            if days_since_last >= 3:  # 3 gün ölçüm yoksa hatırlat
                reminder_time = await self.get_optimal_reminder_time(user_id, db)
                
                scheduled_notifications.append(ScheduledNotification(
                    notification_type=NotificationType.WEIGHT_REMINDER,
                    title="Ölçüm Zamanı! ⚖️",
                    message=f"{days_since_last} gündür ölçüm almıyorsun. Hedefine ulaşmak için düzenli takip önemli!",
                    scheduled_time=reminder_time,
                    priority=NotificationPriority.MEDIUM,
                    user_id=user_id,
                    metadata={"days_since_last": days_since_last}
                ))
        
        # 2. Motivasyon mesajı
        if await self.should_send_reminder(user_id, "motivation_message", db):
            if progress_data.goal_progress_percentage < 80:  # Hedefin %80'ini tamamlamamışsa
                motivation_message = self.generate_motivation_message(progress_data)
                motivation_time = await self.get_optimal_reminder_time(user_id, db)
                motivation_time += timedelta(hours=2)  # Ölçüm hatırlatmasından 2 saat sonra
                
                scheduled_notifications.append(ScheduledNotification(
                    notification_type=NotificationType.MOTIVATION_MESSAGE,
                    title="Motivasyon Zamanı! 💪",
                    message=motivation_message,
                    scheduled_time=motivation_time,
                    priority=NotificationPriority.LOW,
                    user_id=user_id,
                    metadata={"progress_percentage": progress_data.goal_progress_percentage}
                ))
        
        # 3. Plateau uyarısı
        if progress_data.plateau_days >= self.PLATEAU_THRESHOLD_DAYS:
            if await self.should_send_reminder(user_id, "plateau_alert", db):
                plateau_time = await self.get_optimal_reminder_time(user_id, db)
                
                scheduled_notifications.append(ScheduledNotification(
                    notification_type=NotificationType.PLATEAU_ALERT,
                    title="Plateau Fark Edildi 📊",
                    message=f"{progress_data.plateau_days} gündür kilo değişimi minimal. Rutinini gözden geçirme zamanı olabilir!",
                    scheduled_time=plateau_time,
                    priority=NotificationPriority.HIGH,
                    user_id=user_id,
                    metadata={"plateau_days": progress_data.plateau_days}
                ))
        
        # 4. Tutarlılık övgüsü
        if patterns.consistency_score >= self.CONSISTENCY_THRESHOLD:
            consistency_time = await self.get_optimal_reminder_time(user_id, db)
            consistency_time += timedelta(hours=4)
            
            scheduled_notifications.append(ScheduledNotification(
                notification_type=NotificationType.CONSISTENCY_PRAISE,
                title="Harika Tutarlılık! 🌟",
                message=f"Ölçüm tutarlılığın %{patterns.consistency_score*100:.0f}! Bu disiplin seni hedefe götürecek.",
                scheduled_time=consistency_time,
                priority=NotificationPriority.LOW,
                user_id=user_id,
                metadata={"consistency_score": patterns.consistency_score}
            ))
        
        # Günlük sınırı aş
        max_daily = await self._get_max_daily_notifications(user_id, db)
        return scheduled_notifications[:max_daily]
    
    # ------------------------------------------------------------------
    # Yardımcı Metodlar
    # ------------------------------------------------------------------
    
    async def _get_notification_preferences(
        self, 
        user_id: int, 
        db: AsyncSession
    ) -> Optional[NotificationPreferences]:
        """Kullanıcının bildirim tercihlerini getirir."""
        stmt = select(NotificationPreferences).where(NotificationPreferences.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_progress_data(self, user_id: int, db: AsyncSession) -> ProgressData:
        """İlerleme verilerini toplar."""
        # Kullanıcı profili
        user_profile = await self._get_user_profile(user_id, db)
        
        # En son ölçüm
        latest_measurement = await self._get_latest_measurement(user_id, db)
        
        # Haftalık değişim (trend analysis engine'den)
        from app.trend_analysis_engine import trend_analysis_engine
        weekly_trend = await trend_analysis_engine.calculate_weekly_average_change(user_id, db)
        
        # Plateau analizi
        plateau_analysis = await trend_analysis_engine.detect_weight_plateau(user_id, db)
        
        # Hedef ilerleme yüzdesi
        goal_progress = 0.0
        current_weight = None
        target_weight = None
        
        if latest_measurement and user_profile:
            current_weight = latest_measurement.weight_kg
            target_weight = user_profile.target_weight_kg
            
            if target_weight and user_profile.weight_kg:
                total_needed = abs(target_weight - user_profile.weight_kg)
                achieved = abs(user_profile.weight_kg - current_weight)
                if total_needed > 0:
                    goal_progress = min(100.0, (achieved / total_needed) * 100)
        
        # Tutarlılık skoru
        patterns = await self.analyze_user_patterns(user_id, db)
        
        # Başlangıç tarihi (ilk ölçüm)
        first_measurement = await self._get_first_measurement(user_id, db)
        days_since_start = 0
        if first_measurement:
            days_since_start = (datetime.now().date() - first_measurement.measured_at.date()).days
        
        return ProgressData(
            current_weight=current_weight,
            target_weight=target_weight,
            weekly_change=float(weekly_trend.average_weekly_change),
            goal_progress_percentage=goal_progress,
            days_since_start=days_since_start,
            consistency_score=patterns.consistency_score,
            plateau_days=plateau_analysis.plateau_duration_days,
            achievements=[]  # TODO: Achievement sistemi eklendiğinde doldurulacak
        )
    
    def _find_most_active_hours(self, hours: List[int]) -> List[int]:
        """En aktif saatleri bulur."""
        if not hours:
            return []
        
        # Saat frekanslarını hesapla
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # En çok kullanılan 3 saati döndür
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]
    
    def _calculate_consistency_score(self, measurements: List[Measurement]) -> float:
        """Tutarlılık skorunu hesaplar."""
        if len(measurements) < 2:
            return 0.0
        
        # Son 30 günde kaç gün ölçüm alınmış
        days_with_measurements = len(set(m.measured_at.date() for m in measurements))
        
        # 30 günde ideal ölçüm sayısı (haftada 3-4 kez = ~15 gün)
        ideal_days = 15
        
        return min(1.0, days_with_measurements / ideal_days)
    
    def _determine_activity_pattern(
        self, 
        measurement_hours: List[int], 
        consistency_score: float
    ) -> UserActivityPattern:
        """Aktivite kalıbını belirler."""
        if not measurement_hours:
            return UserActivityPattern.IRREGULAR
        
        if consistency_score < 0.3:
            return UserActivityPattern.IRREGULAR
        
        avg_hour = sum(measurement_hours) / len(measurement_hours)
        
        if avg_hour < 10:
            return UserActivityPattern.MORNING_PERSON
        elif avg_hour > 18:
            return UserActivityPattern.EVENING_PERSON
        else:
            return UserActivityPattern.CONSISTENT
    
    def _parse_time(self, time_str: Optional[str]) -> Optional[time]:
        """Zaman string'ini parse eder."""
        if not time_str:
            return None
        
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour=hour, minute=minute)
        except:
            return None
    
    def _is_in_quiet_hours(self, current_time: time, quiet_start: time, quiet_end: time) -> bool:
        """Sessiz saatlerde olup olmadığını kontrol eder."""
        if quiet_start <= quiet_end:
            # Normal aralık (örn: 22:00 - 08:00)
            return quiet_start <= current_time <= quiet_end
        else:
            # Gece yarısını geçen aralık (örn: 22:00 - 08:00)
            return current_time >= quiet_start or current_time <= quiet_end
    
    async def _count_todays_notifications(self, user_id: int, db: AsyncSession) -> int:
        """Bugün gönderilen bildirim sayısını sayar."""
        # TODO: Notification log tablosu oluşturulduğunda implement edilecek
        return 0
    
    async def _get_last_notification_time(self, user_id: int, db: AsyncSession) -> Optional[datetime]:
        """Son bildirim zamanını getirir."""
        # TODO: Notification log tablosu oluşturulduğunda implement edilecek
        return None
    
    async def _get_max_daily_notifications(self, user_id: int, db: AsyncSession) -> int:
        """Maksimum günlük bildirim sayısını getirir."""
        preferences = await self._get_notification_preferences(user_id, db)
        if preferences:
            return preferences.max_daily_notifications or self.MAX_DAILY_NOTIFICATIONS
        return self.MAX_DAILY_NOTIFICATIONS
    
    async def _get_user_profile(self, user_id: int, db: AsyncSession) -> Optional[UserProfile]:
        """Kullanıcı profilini getirir."""
        stmt = select(UserProfile).where(UserProfile.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_latest_measurement(self, user_id: int, db: AsyncSession) -> Optional[Measurement]:
        """En son ölçümü getirir."""
        stmt = (
            select(Measurement)
            .where(Measurement.user_id == user_id)
            .order_by(desc(Measurement.measured_at))
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_first_measurement(self, user_id: int, db: AsyncSession) -> Optional[Measurement]:
        """İlk ölçümü getirir."""
        stmt = (
            select(Measurement)
            .where(Measurement.user_id == user_id)
            .order_by(Measurement.measured_at.asc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Global Instance
# ---------------------------------------------------------------------------

# Singleton instance
smart_notification_system = SmartNotificationSystem()