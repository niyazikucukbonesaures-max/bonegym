# Fitness ve Kalori Takip Uygulaması - Trend Analiz Motoru
# Kilo ve ölçüm verilerindeki eğilimleri analiz eden gelişmiş sistem

from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, ROUND_HALF_UP
from statistics import mean, median, stdev
from enum import Enum
import json

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Measurement, TrendAnalysis, UserProfile


# ---------------------------------------------------------------------------
# Enum ve Sabitler
# ---------------------------------------------------------------------------

class TrendDirection(Enum):
    """Trend yönleri."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    FLUCTUATING = "fluctuating"


class AnalysisType(Enum):
    """Analiz türleri."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class PlateauStatus(Enum):
    """Plateau durumları."""
    NO_PLATEAU = "no_plateau"
    POTENTIAL_PLATEAU = "potential_plateau"
    CONFIRMED_PLATEAU = "confirmed_plateau"


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------

@dataclass
class WeeklyTrend:
    """Haftalık trend analizi sonucu."""
    period_start: date
    period_end: date
    weight_change_kg: Optional[Decimal]
    average_weekly_change: Decimal
    trend_direction: TrendDirection
    confidence_score: float
    data_points: int
    insights: List[str]


@dataclass
class PlateauAnalysis:
    """Plateau analizi sonucu."""
    status: PlateauStatus
    plateau_duration_days: int
    weight_variance_kg: Decimal
    last_significant_change: Optional[date]
    recommendations: List[str]
    confidence_score: float


@dataclass
class Timeline:
    """Hedef timeline tahmini."""
    target_weight_kg: Decimal
    current_weight_kg: Decimal
    estimated_days: int
    estimated_date: date
    weekly_rate_needed: Decimal
    current_weekly_rate: Decimal
    feasibility_score: float
    adjustments_needed: List[str]


@dataclass
class BodyComposition:
    """Vücut kompozisyonu tahmini."""
    estimated_body_fat_percentage: Optional[float]
    lean_mass_change_kg: Optional[Decimal]
    fat_mass_change_kg: Optional[Decimal]
    waist_to_hip_ratio: Optional[float]
    muscle_gain_indicator: float
    fat_loss_indicator: float
    composition_trend: str


@dataclass
class Insight:
    """İlerleme insight'ı."""
    type: str
    title: str
    description: str
    priority: int  # 1-5, 5 en yüksek
    actionable: bool
    data_support: Dict[str, Any]


# ---------------------------------------------------------------------------
# TrendAnalysisEngine Sınıfı
# ---------------------------------------------------------------------------

class TrendAnalysisEngine:
    """Gelişmiş trend analizi ve tahminleme motoru."""
    
    # Sabitler
    MIN_DATA_POINTS = 3
    PLATEAU_THRESHOLD_KG = 0.5  # kg
    PLATEAU_MIN_DAYS = 14
    SIGNIFICANT_CHANGE_THRESHOLD = 0.3  # kg
    
    async def calculate_weekly_average_change(
        self, 
        user_id: int, 
        db: AsyncSession,
        weeks: int = 4
    ) -> WeeklyTrend:
        """Haftalık ortalama kilo değişimini hesaplar.
        
        Args:
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            weeks: Analiz edilecek hafta sayısı
            
        Returns:
            WeeklyTrend: Haftalık trend analizi
        """
        # Tarih aralığını belirle
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Kilo ölçümlerini al
        measurements = await self._get_weight_measurements(
            user_id, db, start_date, end_date
        )
        
        if len(measurements) < self.MIN_DATA_POINTS:
            return WeeklyTrend(
                period_start=start_date,
                period_end=end_date,
                weight_change_kg=None,
                average_weekly_change=Decimal("0"),
                trend_direction=TrendDirection.STABLE,
                confidence_score=0.0,
                data_points=len(measurements),
                insights=["Yetersiz veri - daha fazla ölçüm gerekli"]
            )
        
        # Haftalık değişimleri hesapla
        weekly_changes = []
        weights = [m.weight_kg for m in measurements]
        dates = [m.measured_at.date() for m in measurements]
        
        # Her hafta için ortalama kilo hesapla
        weekly_averages = self._calculate_weekly_averages(weights, dates, start_date, weeks)
        
        # Haftalık değişimleri hesapla
        for i in range(1, len(weekly_averages)):
            if weekly_averages[i-1] is not None and weekly_averages[i] is not None:
                change = weekly_averages[i] - weekly_averages[i-1]
                weekly_changes.append(change)
        
        # İstatistikleri hesapla
        if weekly_changes:
            avg_weekly_change = Decimal(str(mean(weekly_changes)))
            total_change = weights[-1] - weights[0] if len(weights) >= 2 else 0
        else:
            avg_weekly_change = Decimal("0")
            total_change = 0
        
        # Trend yönünü belirle
        trend_direction = self._determine_trend_direction(weekly_changes)
        
        # Güven skorunu hesapla
        confidence_score = self._calculate_confidence_score(
            len(measurements), len(weekly_changes), weeks
        )
        
        # Insights oluştur
        insights = self._generate_weekly_insights(
            avg_weekly_change, trend_direction, len(measurements)
        )
        
        return WeeklyTrend(
            period_start=start_date,
            period_end=end_date,
            weight_change_kg=Decimal(str(total_change)) if total_change else None,
            average_weekly_change=avg_weekly_change,
            trend_direction=trend_direction,
            confidence_score=confidence_score,
            data_points=len(measurements),
            insights=insights
        )
    
    async def detect_weight_plateau(
        self, 
        user_id: int, 
        db: AsyncSession
    ) -> PlateauAnalysis:
        """Kilo plateau'sunu tespit eder.
        
        Args:
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            
        Returns:
            PlateauAnalysis: Plateau analizi sonucu
        """
        # Son 8 haftanın verilerini al
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=8)
        
        measurements = await self._get_weight_measurements(
            user_id, db, start_date, end_date
        )
        
        if len(measurements) < self.MIN_DATA_POINTS:
            return PlateauAnalysis(
                status=PlateauStatus.NO_PLATEAU,
                plateau_duration_days=0,
                weight_variance_kg=Decimal("0"),
                last_significant_change=None,
                recommendations=["Daha fazla veri gerekli"],
                confidence_score=0.0
            )
        
        weights = [m.weight_kg for m in measurements]
        dates = [m.measured_at.date() for m in measurements]
        
        # Varyansı hesapla
        weight_variance = Decimal(str(stdev(weights))) if len(weights) > 1 else Decimal("0")
        
        # Son önemli değişikliği bul
        last_significant_change = self._find_last_significant_change(weights, dates)
        
        # Plateau durumunu belirle
        plateau_days = 0
        if last_significant_change:
            plateau_days = (end_date - last_significant_change).days
        
        # Plateau statusunu belirle
        if weight_variance <= Decimal(str(self.PLATEAU_THRESHOLD_KG)):
            if plateau_days >= self.PLATEAU_MIN_DAYS:
                status = PlateauStatus.CONFIRMED_PLATEAU
            else:
                status = PlateauStatus.POTENTIAL_PLATEAU
        else:
            status = PlateauStatus.NO_PLATEAU
        
        # Önerileri oluştur
        recommendations = self._generate_plateau_recommendations(status, plateau_days)
        
        # Güven skorunu hesapla
        confidence_score = min(len(measurements) / 10.0, 1.0)
        
        return PlateauAnalysis(
            status=status,
            plateau_duration_days=plateau_days,
            weight_variance_kg=weight_variance,
            last_significant_change=last_significant_change,
            recommendations=recommendations,
            confidence_score=confidence_score
        )
    
    async def predict_goal_timeline(
        self, 
        user_id: int, 
        target_weight: float, 
        db: AsyncSession
    ) -> Timeline:
        """Hedef timeline'ını tahmin eder.
        
        Args:
            user_id: Kullanıcı ID'si
            target_weight: Hedef kilo
            db: Veritabanı oturumu
            
        Returns:
            Timeline: Timeline tahmini
        """
        # Mevcut kilo ve trend al
        current_measurement = await self._get_latest_weight(user_id, db)
        if not current_measurement:
            raise ValueError("Mevcut kilo ölçümü bulunamadı")
        
        current_weight = Decimal(str(current_measurement.weight_kg))
        target_weight_decimal = Decimal(str(target_weight))
        
        # Haftalık trend hesapla
        weekly_trend = await self.calculate_weekly_average_change(user_id, db, weeks=6)
        current_weekly_rate = weekly_trend.average_weekly_change
        
        # Hedef farkı
        weight_difference = target_weight_decimal - current_weight
        
        # Timeline hesapla
        if abs(current_weekly_rate) < Decimal("0.01"):  # Çok yavaş değişim
            estimated_days = 365  # 1 yıl varsayılan
            weekly_rate_needed = weight_difference / Decimal("52")  # Yıllık dağıtım
            feasibility_score = 0.3
        else:
            estimated_weeks = abs(weight_difference / current_weekly_rate)
            estimated_days = int(estimated_weeks * 7)
            weekly_rate_needed = current_weekly_rate
            
            # Feasibility skorunu hesapla
            feasibility_score = self._calculate_feasibility_score(
                current_weekly_rate, weight_difference
            )
        
        # Maksimum süre sınırı (2 yıl)
        if estimated_days > 730:
            estimated_days = 730
            weekly_rate_needed = weight_difference / Decimal("104")  # 2 yıllık dağıtım
            feasibility_score = min(feasibility_score, 0.5)
        
        estimated_date = datetime.now().date() + timedelta(days=estimated_days)
        
        # Ayarlamaları belirle
        adjustments_needed = self._generate_timeline_adjustments(
            current_weekly_rate, weekly_rate_needed, feasibility_score
        )
        
        return Timeline(
            target_weight_kg=target_weight_decimal,
            current_weight_kg=current_weight,
            estimated_days=estimated_days,
            estimated_date=estimated_date,
            weekly_rate_needed=weekly_rate_needed,
            current_weekly_rate=current_weekly_rate,
            feasibility_score=feasibility_score,
            adjustments_needed=adjustments_needed
        )
    
    async def calculate_body_composition_estimate(
        self, 
        measurements: List[Measurement]
    ) -> BodyComposition:
        """Vücut kompozisyonu tahmini hesaplar.
        
        Args:
            measurements: Ölçüm listesi
            
        Returns:
            BodyComposition: Vücut kompozisyonu tahmini
        """
        if len(measurements) < 2:
            return BodyComposition(
                estimated_body_fat_percentage=None,
                lean_mass_change_kg=None,
                fat_mass_change_kg=None,
                waist_to_hip_ratio=None,
                muscle_gain_indicator=0.0,
                fat_loss_indicator=0.0,
                composition_trend="insufficient_data"
            )
        
        # En son ve en eski ölçümleri al
        latest = measurements[-1]
        earliest = measurements[0]
        
        # Bel/kalça oranı hesapla
        waist_to_hip_ratio = None
        if latest.waist_cm and latest.hip_cm:
            waist_to_hip_ratio = latest.waist_cm / latest.hip_cm
        
        # Kilo değişimi
        weight_change = latest.weight_kg - earliest.weight_kg if earliest.weight_kg else 0
        
        # Bel ölçüsü değişimi (yağ kaybı göstergesi)
        waist_change = 0
        if latest.waist_cm and earliest.waist_cm:
            waist_change = latest.waist_cm - earliest.waist_cm
        
        # Kol ölçüsü değişimi (kas kazanımı göstergesi)
        arm_change = 0
        if latest.arm_cm and earliest.arm_cm:
            arm_change = latest.arm_cm - earliest.arm_cm
        
        # Göstergeler hesapla
        fat_loss_indicator = max(0, -waist_change * 2)  # Bel azalması = yağ kaybı
        muscle_gain_indicator = max(0, arm_change * 3)  # Kol artışı = kas kazanımı
        
        # Kompozisyon trendi belirle
        if weight_change > 0 and waist_change < 0:
            composition_trend = "lean_gain"  # Kilo artışı + bel azalması = kas kazanımı
        elif weight_change < 0 and waist_change < 0:
            composition_trend = "fat_loss"   # Kilo kaybı + bel azalması = yağ kaybı
        elif weight_change > 0 and waist_change > 0:
            composition_trend = "weight_gain"  # Genel kilo artışı
        elif weight_change < 0:
            composition_trend = "weight_loss"  # Genel kilo kaybı
        else:
            composition_trend = "maintenance"  # Stabil
        
        # Tahmini lean/fat mass değişimi
        lean_mass_change = None
        fat_mass_change = None
        
        if composition_trend == "lean_gain":
            lean_mass_change = Decimal(str(weight_change * 0.7))  # %70 kas
            fat_mass_change = Decimal(str(weight_change * 0.3))   # %30 yağ
        elif composition_trend == "fat_loss":
            fat_mass_change = Decimal(str(weight_change * 0.8))   # %80 yağ kaybı
            lean_mass_change = Decimal(str(weight_change * 0.2))  # %20 kas kaybı
        
        return BodyComposition(
            estimated_body_fat_percentage=None,  # Daha karmaşık hesaplama gerekir
            lean_mass_change_kg=lean_mass_change,
            fat_mass_change_kg=fat_mass_change,
            waist_to_hip_ratio=waist_to_hip_ratio,
            muscle_gain_indicator=muscle_gain_indicator,
            fat_loss_indicator=fat_loss_indicator,
            composition_trend=composition_trend
        )
    
    async def generate_progress_insights(
        self, 
        user_id: int, 
        db: AsyncSession
    ) -> List[Insight]:
        """İlerleme insights'ları oluşturur.
        
        Args:
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            
        Returns:
            List[Insight]: İlerleme insights listesi
        """
        insights = []
        
        # Haftalık trend analizi
        weekly_trend = await self.calculate_weekly_average_change(user_id, db)
        
        # Plateau analizi
        plateau_analysis = await self.detect_weight_plateau(user_id, db)
        
        # Son ölçümler
        recent_measurements = await self._get_recent_measurements(user_id, db, days=30)
        
        # Trend insight'ı
        if weekly_trend.confidence_score > 0.7:
            if weekly_trend.trend_direction == TrendDirection.DECREASING:
                insights.append(Insight(
                    type="trend",
                    title="Pozitif Kilo Kaybı Trendi",
                    description=f"Son {len(weekly_trend.insights)} haftada ortalama {abs(float(weekly_trend.average_weekly_change)):.1f} kg/hafta kilo kaybı",
                    priority=4,
                    actionable=True,
                    data_support={"weekly_change": float(weekly_trend.average_weekly_change)}
                ))
            elif weekly_trend.trend_direction == TrendDirection.INCREASING:
                insights.append(Insight(
                    type="trend",
                    title="Kilo Artış Trendi",
                    description=f"Son haftalarda ortalama {float(weekly_trend.average_weekly_change):.1f} kg/hafta artış",
                    priority=3,
                    actionable=True,
                    data_support={"weekly_change": float(weekly_trend.average_weekly_change)}
                ))
        
        # Plateau insight'ı
        if plateau_analysis.status == PlateauStatus.CONFIRMED_PLATEAU:
            insights.append(Insight(
                type="plateau",
                title="Kilo Plateau'su Tespit Edildi",
                description=f"{plateau_analysis.plateau_duration_days} gündür kilo değişimi minimal",
                priority=5,
                actionable=True,
                data_support={"plateau_days": plateau_analysis.plateau_duration_days}
            ))
        
        # Tutarlılık insight'ı
        if len(recent_measurements) >= 10:
            consistency_score = len(recent_measurements) / 30.0  # Son 30 günde kaç ölçüm
            if consistency_score > 0.8:
                insights.append(Insight(
                    type="consistency",
                    title="Mükemmel Ölçüm Tutarlılığı",
                    description="Düzenli ölçüm alışkanlığınız harika!",
                    priority=2,
                    actionable=False,
                    data_support={"consistency_score": consistency_score}
                ))
            elif consistency_score < 0.3:
                insights.append(Insight(
                    type="consistency",
                    title="Ölçüm Sıklığını Artırın",
                    description="Daha sık ölçüm almak trend analizini iyileştirir",
                    priority=3,
                    actionable=True,
                    data_support={"consistency_score": consistency_score}
                ))
        
        # Vücut kompozisyonu insight'ı
        if len(recent_measurements) >= 5:
            body_comp = await self.calculate_body_composition_estimate(recent_measurements)
            if body_comp.composition_trend == "lean_gain":
                insights.append(Insight(
                    type="composition",
                    title="Kas Kazanımı Göstergeleri",
                    description="Ölçümler kas kazanımı olduğunu gösteriyor",
                    priority=4,
                    actionable=False,
                    data_support={"trend": body_comp.composition_trend}
                ))
        
        # Önceliğe göre sırala
        insights.sort(key=lambda x: x.priority, reverse=True)
        
        return insights[:5]  # En önemli 5 insight
    
    # ------------------------------------------------------------------
    # Yardımcı Metodlar
    # ------------------------------------------------------------------
    
    async def _get_weight_measurements(
        self, 
        user_id: int, 
        db: AsyncSession, 
        start_date: date, 
        end_date: date
    ) -> List[Measurement]:
        """Belirtilen tarih aralığındaki kilo ölçümlerini getirir."""
        stmt = (
            select(Measurement)
            .where(
                and_(
                    Measurement.user_id == user_id,
                    Measurement.weight_kg.isnot(None),
                    Measurement.measured_at >= datetime.combine(start_date, datetime.min.time()),
                    Measurement.measured_at <= datetime.combine(end_date, datetime.max.time())
                )
            )
            .order_by(Measurement.measured_at.asc())
        )
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def _get_recent_measurements(
        self, 
        user_id: int, 
        db: AsyncSession, 
        days: int = 30
    ) -> List[Measurement]:
        """Son N gündeki tüm ölçümleri getirir."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
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
        return result.scalars().all()
    
    async def _get_latest_weight(self, user_id: int, db: AsyncSession) -> Optional[Measurement]:
        """En son kilo ölçümünü getirir."""
        stmt = (
            select(Measurement)
            .where(
                and_(
                    Measurement.user_id == user_id,
                    Measurement.weight_kg.isnot(None)
                )
            )
            .order_by(Measurement.measured_at.desc())
            .limit(1)
        )
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    def _calculate_weekly_averages(
        self, 
        weights: List[float], 
        dates: List[date], 
        start_date: date, 
        weeks: int
    ) -> List[Optional[float]]:
        """Haftalık ortalama kiloları hesaplar."""
        weekly_averages = []
        
        for week in range(weeks):
            week_start = start_date + timedelta(weeks=week)
            week_end = week_start + timedelta(days=6)
            
            week_weights = []
            for i, measurement_date in enumerate(dates):
                if week_start <= measurement_date <= week_end:
                    week_weights.append(weights[i])
            
            if week_weights:
                weekly_averages.append(mean(week_weights))
            else:
                weekly_averages.append(None)
        
        return weekly_averages
    
    def _determine_trend_direction(self, weekly_changes: List[float]) -> TrendDirection:
        """Haftalık değişimlerden trend yönünü belirler."""
        if not weekly_changes:
            return TrendDirection.STABLE
        
        avg_change = mean(weekly_changes)
        change_variance = stdev(weekly_changes) if len(weekly_changes) > 1 else 0
        
        # Yüksek varyans = dalgalanma
        if change_variance > 0.5:
            return TrendDirection.FLUCTUATING
        
        # Ortalama değişime göre trend
        if avg_change > 0.1:
            return TrendDirection.INCREASING
        elif avg_change < -0.1:
            return TrendDirection.DECREASING
        else:
            return TrendDirection.STABLE
    
    def _calculate_confidence_score(
        self, 
        total_measurements: int, 
        weekly_changes: int, 
        weeks: int
    ) -> float:
        """Güven skorunu hesaplar."""
        # Veri yoğunluğu skoru
        density_score = min(total_measurements / (weeks * 2), 1.0)  # Haftada 2 ölçüm ideal
        
        # Haftalık değişim skoru
        change_score = min(weekly_changes / (weeks - 1), 1.0) if weeks > 1 else 0
        
        # Genel güven skoru
        return (density_score + change_score) / 2
    
    def _generate_weekly_insights(
        self, 
        avg_change: Decimal, 
        direction: TrendDirection, 
        data_points: int
    ) -> List[str]:
        """Haftalık trend için insights oluşturur."""
        insights = []
        
        if data_points < 5:
            insights.append("Daha güvenilir analiz için daha sık ölçüm alın")
        
        if direction == TrendDirection.DECREASING:
            insights.append(f"Haftalık {abs(float(avg_change)):.1f} kg kilo kaybı trendi")
        elif direction == TrendDirection.INCREASING:
            insights.append(f"Haftalık {float(avg_change):.1f} kg kilo artış trendi")
        elif direction == TrendDirection.STABLE:
            insights.append("Kilo stabil seyrediyor")
        else:
            insights.append("Kilo dalgalanma gösteriyor")
        
        return insights
    
    def _find_last_significant_change(
        self, 
        weights: List[float], 
        dates: List[date]
    ) -> Optional[date]:
        """Son önemli kilo değişikliğinin tarihini bulur."""
        if len(weights) < 2:
            return None
        
        for i in range(len(weights) - 1, 0, -1):
            change = abs(weights[i] - weights[i-1])
            if change >= self.SIGNIFICANT_CHANGE_THRESHOLD:
                return dates[i]
        
        return None
    
    def _generate_plateau_recommendations(
        self, 
        status: PlateauStatus, 
        plateau_days: int
    ) -> List[str]:
        """Plateau durumuna göre öneriler oluşturur."""
        recommendations = []
        
        if status == PlateauStatus.CONFIRMED_PLATEAU:
            recommendations.extend([
                "Kalori alımınızı gözden geçirin",
                "Antrenman rutininizi değiştirin",
                "Cheat meal düşünebilirsiniz",
                "Stres seviyenizi kontrol edin"
            ])
        elif status == PlateauStatus.POTENTIAL_PLATEAU:
            recommendations.extend([
                "Birkaç gün daha bekleyin",
                "Ölçüm tutarlılığınızı artırın"
            ])
        else:
            recommendations.append("İlerleme devam ediyor")
        
        return recommendations
    
    def _calculate_feasibility_score(
        self, 
        current_rate: Decimal, 
        weight_difference: Decimal
    ) -> float:
        """Timeline feasibility skorunu hesaplar."""
        # Sağlıklı kilo kaybı/kazanımı: 0.5-1 kg/hafta
        healthy_rate_min = Decimal("0.5")
        healthy_rate_max = Decimal("1.0")
        
        abs_current_rate = abs(current_rate)
        
        if healthy_rate_min <= abs_current_rate <= healthy_rate_max:
            return 1.0  # Mükemmel
        elif abs_current_rate < healthy_rate_min:
            return 0.7  # Yavaş ama güvenli
        elif abs_current_rate > healthy_rate_max * 2:
            return 0.3  # Çok hızlı, sürdürülemez
        else:
            return 0.5  # Orta
    
    def _generate_timeline_adjustments(
        self, 
        current_rate: Decimal, 
        needed_rate: Decimal, 
        feasibility: float
    ) -> List[str]:
        """Timeline için ayarlama önerileri oluşturur."""
        adjustments = []
        
        rate_difference = abs(needed_rate - current_rate)
        
        if feasibility < 0.5:
            adjustments.append("Hedef tarihi daha gerçekçi olarak ayarlayın")
        
        if rate_difference > Decimal("0.3"):
            if needed_rate > current_rate:
                adjustments.append("Kalori açığını artırın")
                adjustments.append("Antrenman sıklığını artırın")
            else:
                adjustments.append("Daha yavaş ilerleme hedefleyin")
        
        if not adjustments:
            adjustments.append("Mevcut yaklaşımınızı sürdürün")
        
        return adjustments


# ---------------------------------------------------------------------------
# Global Instance
# ---------------------------------------------------------------------------

# Singleton instance
trend_analysis_engine = TrendAnalysisEngine()