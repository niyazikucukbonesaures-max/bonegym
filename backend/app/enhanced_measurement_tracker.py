# Fitness ve Kalori Takip Uygulaması - Gelişmiş Ölçüm Takipçisi
# Çoklu ölçüm tipi kaydetme, doğrulama entegrasyonu ve görselleştirme verisi hazırlama

from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Measurement, WeightValidation, UserProfile
from app.schemas import MeasurementCreate
from app.data_validator import data_validator, ValidationResult
from app.trend_analysis_engine import trend_analysis_engine


# ---------------------------------------------------------------------------
# Enum ve Sabitler
# ---------------------------------------------------------------------------

class MeasurementType(Enum):
    """Ölçüm türleri."""
    WEIGHT = "weight_kg"
    HEIGHT = "height_cm"
    WAIST = "waist_cm"
    HIP = "hip_cm"
    CHEST = "chest_cm"
    ARM = "arm_cm"
    LEG = "leg_cm"


class ValidationStatus(Enum):
    """Doğrulama durumları."""
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"
    PENDING = "pending"


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------

@dataclass
class MeasurementValidationResult:
    """Ölçüm doğrulama sonucu."""
    is_valid: bool
    status: ValidationStatus
    warnings: List[str]
    errors: List[str]
    suggestions: List[str]
    confidence_score: float


@dataclass
class MeasurementEntry:
    """Gelişmiş ölçüm girişi."""
    measurement_type: MeasurementType
    value: Decimal
    validation_result: MeasurementValidationResult
    previous_value: Optional[Decimal]
    change_amount: Optional[Decimal]
    change_percentage: Optional[float]
    trend_indicator: str


@dataclass
class MultiMeasurementResult:
    """Çoklu ölçüm kaydetme sonucu."""
    measurement_id: int
    entries: List[MeasurementEntry]
    overall_status: ValidationStatus
    total_warnings: int
    total_errors: int
    success_count: int
    recommendations: List[str]


@dataclass
class MeasurementVisualizationData:
    """30 günlük ölçüm görselleştirme verisi."""
    measurement_type: str
    dates: List[str]
    values: List[float]
    trend_line: List[float]
    average_value: float
    min_value: float
    max_value: float
    total_change: float
    change_percentage: float
    trend_direction: str


@dataclass
class BodyMetricsSnapshot:
    """Vücut metrikleri anlık görüntüsü."""
    bmi: Optional[float]
    waist_to_hip_ratio: Optional[float]
    body_fat_estimate: Optional[float]
    muscle_mass_estimate: Optional[float]
    metabolic_age_estimate: Optional[int]
    health_indicators: Dict[str, str]


# ---------------------------------------------------------------------------
# EnhancedMeasurementTracker Sınıfı
# ---------------------------------------------------------------------------

class EnhancedMeasurementTracker:
    """Gelişmiş ölçüm takip sistemi."""
    
    def __init__(self):
        """Bağımlılıkları başlat."""
        self.validator = data_validator
        self.trend_engine = trend_analysis_engine
    
    # ------------------------------------------------------------------
    # Ana Ölçüm Kaydetme Metodları
    # ------------------------------------------------------------------
    
    async def record_multiple_measurements(
        self, 
        measurement_data: MeasurementCreate,
        db: AsyncSession
    ) -> MultiMeasurementResult:
        """Çoklu ölçüm tipi kaydetme.
        
        Args:
            measurement_data: Ölçüm verisi
            db: Veritabanı oturumu
            
        Returns:
            MultiMeasurementResult: Kaydetme sonucu
        """
        entries = []
        warnings = []
        errors = []
        recommendations = []
        
        # Her ölçüm tipini işle
        measurement_fields = {
            MeasurementType.WEIGHT: measurement_data.weight_kg,
            MeasurementType.HEIGHT: measurement_data.height_cm,
            MeasurementType.WAIST: measurement_data.waist_cm,
            MeasurementType.HIP: measurement_data.hip_cm,
            MeasurementType.CHEST: measurement_data.chest_cm,
            MeasurementType.ARM: measurement_data.arm_cm,
            MeasurementType.LEG: measurement_data.leg_cm
        }
        
        for measurement_type, value in measurement_fields.items():
            if value is not None:
                entry = await self._process_single_measurement(
                    measurement_type, value, measurement_data.user_id, db
                )
                entries.append(entry)
                
                if entry.validation_result.status == ValidationStatus.WARNING:
                    warnings.extend(entry.validation_result.warnings)
                elif entry.validation_result.status == ValidationStatus.INVALID:
                    errors.extend(entry.validation_result.errors)
        
        # Genel durumu belirle
        if errors:
            overall_status = ValidationStatus.INVALID
        elif warnings:
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.VALID
        
        # Ölçümü kaydet (geçerli olanları)
        measurement_id = None
        success_count = 0
        
        if overall_status != ValidationStatus.INVALID:
            measurement = await self._save_measurement(measurement_data, entries, db)
            measurement_id = measurement.id
            success_count = len([e for e in entries if e.validation_result.is_valid])
            
            # Kilo doğrulama kaydı oluştur
            if measurement_data.weight_kg is not None:
                await self._create_weight_validation_record(
                    measurement_data.user_id, 
                    measurement_data.weight_kg,
                    entries,
                    db
                )
        
        # Önerileri oluştur
        recommendations = await self._generate_measurement_recommendations(
            entries, measurement_data.user_id, db
        )
        
        return MultiMeasurementResult(
            measurement_id=measurement_id or 0,
            entries=entries,
            overall_status=overall_status,
            total_warnings=len(warnings),
            total_errors=len(errors),
            success_count=success_count,
            recommendations=recommendations
        )
    
    async def get_measurement_visualization_data(
        self, 
        user_id: int, 
        measurement_type: str,
        db: AsyncSession,
        days: int = 30
    ) -> MeasurementVisualizationData:
        """30 günlük ölçüm değişim görselleştirme verisi hazırlama.
        
        Args:
            user_id: Kullanıcı ID'si
            measurement_type: Ölçüm tipi
            db: Veritabanı oturumu
            days: Gün sayısı
            
        Returns:
            MeasurementVisualizationData: Görselleştirme verisi
        """
        # Tarih aralığı
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Ölçümleri al
        measurements = await self._get_measurements_by_type(
            user_id, measurement_type, start_date, end_date, db
        )
        
        if not measurements:
            return MeasurementVisualizationData(
                measurement_type=measurement_type,
                dates=[],
                values=[],
                trend_line=[],
                average_value=0.0,
                min_value=0.0,
                max_value=0.0,
                total_change=0.0,
                change_percentage=0.0,
                trend_direction="no_data"
            )
        
        # Veri hazırlama
        dates = [m.measured_at.strftime("%Y-%m-%d") for m in measurements]
        values = [float(getattr(m, measurement_type)) for m in measurements]
        
        # İstatistikler
        average_value = sum(values) / len(values)
        min_value = min(values)
        max_value = max(values)
        total_change = values[-1] - values[0] if len(values) > 1 else 0.0
        change_percentage = (total_change / values[0] * 100) if values[0] != 0 else 0.0
        
        # Trend çizgisi (basit linear regression)
        trend_line = self._calculate_trend_line(values)
        
        # Trend yönü
        if len(trend_line) > 1:
            if trend_line[-1] > trend_line[0]:
                trend_direction = "increasing"
            elif trend_line[-1] < trend_line[0]:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"
        
        return MeasurementVisualizationData(
            measurement_type=measurement_type,
            dates=dates,
            values=values,
            trend_line=trend_line,
            average_value=average_value,
            min_value=min_value,
            max_value=max_value,
            total_change=total_change,
            change_percentage=change_percentage,
            trend_direction=trend_direction
        )
    
    async def calculate_body_metrics(
        self, 
        user_id: int, 
        db: AsyncSession
    ) -> BodyMetricsSnapshot:
        """Vücut metrikleri hesaplama.
        
        Args:
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            
        Returns:
            BodyMetricsSnapshot: Vücut metrikleri
        """
        # En son ölçümleri al
        latest_measurement = await self._get_latest_measurement(user_id, db)
        user_profile = await self._get_user_profile(user_id, db)
        
        if not latest_measurement or not user_profile:
            return BodyMetricsSnapshot(
                bmi=None,
                waist_to_hip_ratio=None,
                body_fat_estimate=None,
                muscle_mass_estimate=None,
                metabolic_age_estimate=None,
                health_indicators={}
            )
        
        # BMI hesapla
        bmi = None
        if latest_measurement.weight_kg and latest_measurement.height_cm:
            height_m = latest_measurement.height_cm / 100
            bmi = latest_measurement.weight_kg / (height_m ** 2)
        
        # Bel/kalça oranı
        waist_to_hip_ratio = None
        if latest_measurement.waist_cm and latest_measurement.hip_cm:
            waist_to_hip_ratio = latest_measurement.waist_cm / latest_measurement.hip_cm
        
        # Vücut yağ oranı tahmini (Navy formülü yaklaşımı)
        body_fat_estimate = None
        if (latest_measurement.waist_cm and latest_measurement.height_cm and 
            user_profile.gender and user_profile.age):
            body_fat_estimate = self._estimate_body_fat(
                latest_measurement, user_profile
            )
        
        # Kas kütlesi tahmini
        muscle_mass_estimate = None
        if latest_measurement.weight_kg and body_fat_estimate:
            muscle_mass_estimate = latest_measurement.weight_kg * (1 - body_fat_estimate / 100)
        
        # Metabolik yaş tahmini
        metabolic_age_estimate = self._estimate_metabolic_age(
            user_profile, bmi, body_fat_estimate
        )
        
        # Sağlık göstergeleri
        health_indicators = self._generate_health_indicators(
            bmi, waist_to_hip_ratio, body_fat_estimate, user_profile
        )
        
        return BodyMetricsSnapshot(
            bmi=bmi,
            waist_to_hip_ratio=waist_to_hip_ratio,
            body_fat_estimate=body_fat_estimate,
            muscle_mass_estimate=muscle_mass_estimate,
            metabolic_age_estimate=metabolic_age_estimate,
            health_indicators=health_indicators
        )
    
    # ------------------------------------------------------------------
    # Yardımcı Metodlar
    # ------------------------------------------------------------------
    
    async def _process_single_measurement(
        self, 
        measurement_type: MeasurementType, 
        value: float,
        user_id: int,
        db: AsyncSession
    ) -> MeasurementEntry:
        """Tek ölçüm işleme."""
        value_decimal = Decimal(str(value))
        
        # Önceki değeri al
        previous_value = await self._get_previous_measurement_value(
            user_id, measurement_type.value, db
        )
        
        # Değişim hesapla
        change_amount = None
        change_percentage = None
        if previous_value is not None:
            change_amount = value_decimal - Decimal(str(previous_value))
            change_percentage = float((change_amount / Decimal(str(previous_value))) * 100)
        
        # Doğrulama yap
        if measurement_type == MeasurementType.WEIGHT:
            validation = await self.validator.validate_weight(value, user_id, db)
        else:
            # Diğer ölçümler için genel doğrulama
            validation = await self._validate_general_measurement(
                measurement_type, value, user_id, db
            )
        
        # Validation result'ı dönüştür
        validation_result = self._convert_validation_result(validation)
        
        # Trend göstergesi
        trend_indicator = self._determine_trend_indicator(change_amount, measurement_type)
        
        return MeasurementEntry(
            measurement_type=measurement_type,
            value=value_decimal,
            validation_result=validation_result,
            previous_value=Decimal(str(previous_value)) if previous_value else None,
            change_amount=change_amount,
            change_percentage=change_percentage,
            trend_indicator=trend_indicator
        )
    
    async def _save_measurement(
        self, 
        measurement_data: MeasurementCreate,
        entries: List[MeasurementEntry],
        db: AsyncSession
    ) -> Measurement:
        """Ölçümü veritabanına kaydet."""
        # Doğrulama durumunu belirle
        has_warnings = any(e.validation_result.status == ValidationStatus.WARNING for e in entries)
        is_validated = not has_warnings
        
        # Validation notları oluştur
        validation_notes = []
        for entry in entries:
            if entry.validation_result.warnings:
                validation_notes.extend(entry.validation_result.warnings)
        
        measurement = Measurement(
            user_id=measurement_data.user_id,
            height_cm=measurement_data.height_cm,
            weight_kg=measurement_data.weight_kg,
            waist_cm=measurement_data.waist_cm,
            hip_cm=measurement_data.hip_cm,
            chest_cm=measurement_data.chest_cm,
            arm_cm=measurement_data.arm_cm,
            leg_cm=measurement_data.leg_cm,
            is_validated=is_validated,
            validation_notes="; ".join(validation_notes) if validation_notes else None,
            measurement_method="manual",
            confidence_score=1.0 if is_validated else 0.7
        )
        
        db.add(measurement)
        await db.flush()
        await db.refresh(measurement)
        
        return measurement
    
    async def _create_weight_validation_record(
        self,
        user_id: int,
        weight_kg: float,
        entries: List[MeasurementEntry],
        db: AsyncSession
    ):
        """Kilo doğrulama kaydı oluştur."""
        # Kilo entry'sini bul
        weight_entry = None
        for entry in entries:
            if entry.measurement_type == MeasurementType.WEIGHT:
                weight_entry = entry
                break
        
        if not weight_entry:
            return
        
        # Önceki kilo
        previous_weight = float(weight_entry.previous_value) if weight_entry.previous_value else None
        
        # Değişim
        change_kg = float(weight_entry.change_amount) if weight_entry.change_amount else 0.0
        
        # Doğrulama nedeni
        validation_reason = None
        if not weight_entry.validation_result.is_valid:
            validation_reason = "; ".join(weight_entry.validation_result.errors)
        elif weight_entry.validation_result.warnings:
            validation_reason = "; ".join(weight_entry.validation_result.warnings)
        
        validation_record = WeightValidation(
            user_id=user_id,
            weight_kg=weight_kg,
            previous_weight_kg=previous_weight,
            change_kg=change_kg,
            is_valid=weight_entry.validation_result.is_valid,
            validation_reason=validation_reason
        )
        
        db.add(validation_record)
        await db.flush()
    
    async def _get_measurements_by_type(
        self,
        user_id: int,
        measurement_type: str,
        start_date: date,
        end_date: date,
        db: AsyncSession
    ) -> List[Measurement]:
        """Belirli tipte ölçümleri al."""
        field = getattr(Measurement, measurement_type, None)
        if field is None:
            return []
        
        stmt = (
            select(Measurement)
            .where(
                and_(
                    Measurement.user_id == user_id,
                    field.isnot(None),
                    Measurement.measured_at >= datetime.combine(start_date, datetime.min.time()),
                    Measurement.measured_at <= datetime.combine(end_date, datetime.max.time())
                )
            )
            .order_by(Measurement.measured_at.asc())
        )
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def _get_latest_measurement(self, user_id: int, db: AsyncSession) -> Optional[Measurement]:
        """En son ölçümü al."""
        stmt = (
            select(Measurement)
            .where(Measurement.user_id == user_id)
            .order_by(desc(Measurement.measured_at))
            .limit(1)
        )
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_user_profile(self, user_id: int, db: AsyncSession) -> Optional[UserProfile]:
        """Kullanıcı profilini al."""
        stmt = select(UserProfile).where(UserProfile.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_previous_measurement_value(
        self, 
        user_id: int, 
        measurement_type: str, 
        db: AsyncSession
    ) -> Optional[float]:
        """Önceki ölçüm değerini al."""
        field = getattr(Measurement, measurement_type, None)
        if field is None:
            return None
        
        stmt = (
            select(field)
            .where(
                and_(
                    Measurement.user_id == user_id,
                    field.isnot(None)
                )
            )
            .order_by(desc(Measurement.measured_at))
            .limit(1)
        )
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    def _calculate_trend_line(self, values: List[float]) -> List[float]:
        """Basit linear regression ile trend çizgisi hesapla."""
        if len(values) < 2:
            return values
        
        n = len(values)
        x = list(range(n))
        
        # Linear regression
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        # Slope ve intercept
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n
        
        # Trend çizgisi
        return [intercept + slope * xi for xi in x]
    
    def _convert_validation_result(self, validation: ValidationResult) -> MeasurementValidationResult:
        """ValidationResult'ı MeasurementValidationResult'a dönüştür."""
        if validation.is_valid:
            status = ValidationStatus.VALID
            errors = []
            warnings = []
        else:
            if validation.confidence_score > 0.5:
                status = ValidationStatus.WARNING
                warnings = [validation.reason] if validation.reason else []
                errors = []
            else:
                status = ValidationStatus.INVALID
                errors = [validation.reason] if validation.reason else []
                warnings = []
        
        suggestions = []
        if validation.suggested_value is not None:
            suggestions.append(f"Önerilen değer: {validation.suggested_value}")
        
        return MeasurementValidationResult(
            is_valid=validation.is_valid,
            status=status,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions,
            confidence_score=validation.confidence_score
        )
    
    def _determine_trend_indicator(
        self, 
        change_amount: Optional[Decimal], 
        measurement_type: MeasurementType
    ) -> str:
        """Trend göstergesini belirle."""
        if change_amount is None:
            return "first_measurement"
        
        if abs(change_amount) < Decimal("0.1"):
            return "stable"
        elif change_amount > 0:
            if measurement_type == MeasurementType.WEIGHT:
                return "increasing"  # Kilo artışı
            else:
                return "growing"     # Ölçü artışı
        else:
            if measurement_type == MeasurementType.WEIGHT:
                return "decreasing"  # Kilo azalışı
            else:
                return "shrinking"   # Ölçü azalışı
    
    async def _validate_general_measurement(
        self,
        measurement_type: MeasurementType,
        value: float,
        user_id: int,
        db: AsyncSession
    ) -> ValidationResult:
        """Genel ölçüm doğrulama."""
        # Basit aralık kontrolü
        ranges = {
            MeasurementType.HEIGHT: (100.0, 250.0),
            MeasurementType.WAIST: (40.0, 200.0),
            MeasurementType.HIP: (50.0, 200.0),
            MeasurementType.CHEST: (60.0, 200.0),
            MeasurementType.ARM: (15.0, 80.0),
            MeasurementType.LEG: (30.0, 120.0)
        }
        
        if measurement_type in ranges:
            min_val, max_val = ranges[measurement_type]
            if not (min_val <= value <= max_val):
                return ValidationResult(
                    is_valid=False,
                    reason=f"{measurement_type.value} değeri {min_val}-{max_val} aralığında olmalıdır",
                    confidence_score=0.0
                )
        
        # Değişim kontrolü
        change_validation = await self.validator.validate_measurement_change(
            user_id, measurement_type.value, value, db
        )
        
        return change_validation
    
    def _estimate_body_fat(self, measurement: Measurement, profile: UserProfile) -> Optional[float]:
        """Vücut yağ oranı tahmini (basitleştirilmiş Navy formülü)."""
        if not (measurement.waist_cm and measurement.height_cm):
            return None
        
        # Basitleştirilmiş hesaplama
        if profile.gender == "male":
            # Erkekler için
            body_fat = 495 / (1.0324 - 0.19077 * (measurement.waist_cm / 2.54) + 0.15456 * (profile.height_cm / 2.54)) - 450
        else:
            # Kadınlar için (kalça ölçüsü gerekli, yoksa yaklaşık hesaplama)
            hip_cm = measurement.hip_cm or (measurement.waist_cm * 1.1)  # Yaklaşık
            body_fat = 495 / (1.29579 - 0.35004 * (measurement.waist_cm / 2.54) + 0.22100 * (hip_cm / 2.54) - 0.35004 * (profile.height_cm / 2.54)) - 450
        
        # Sınırları kontrol et
        return max(5.0, min(50.0, body_fat))
    
    def _estimate_metabolic_age(
        self, 
        profile: UserProfile, 
        bmi: Optional[float], 
        body_fat: Optional[float]
    ) -> Optional[int]:
        """Metabolik yaş tahmini."""
        if not bmi:
            return None
        
        # Basit metabolik yaş tahmini
        metabolic_age = profile.age
        
        # BMI düzeltmesi
        if bmi > 25:
            metabolic_age += int((bmi - 25) * 2)
        elif bmi < 20:
            metabolic_age -= int((20 - bmi) * 1)
        
        # Vücut yağ oranı düzeltmesi
        if body_fat:
            ideal_body_fat = 15 if profile.gender == "male" else 25
            if body_fat > ideal_body_fat:
                metabolic_age += int((body_fat - ideal_body_fat) * 0.5)
        
        return max(18, min(80, metabolic_age))
    
    def _generate_health_indicators(
        self,
        bmi: Optional[float],
        waist_to_hip_ratio: Optional[float],
        body_fat: Optional[float],
        profile: UserProfile
    ) -> Dict[str, str]:
        """Sağlık göstergelerini oluştur."""
        indicators = {}
        
        # BMI göstergesi
        if bmi:
            if bmi < 18.5:
                indicators["bmi"] = "Zayıf"
            elif bmi < 25:
                indicators["bmi"] = "Normal"
            elif bmi < 30:
                indicators["bmi"] = "Fazla Kilolu"
            else:
                indicators["bmi"] = "Obez"
        
        # Bel/kalça oranı
        if waist_to_hip_ratio:
            if profile.gender == "male":
                threshold = 0.9
            else:
                threshold = 0.8
            
            if waist_to_hip_ratio > threshold:
                indicators["waist_hip_ratio"] = "Risk"
            else:
                indicators["waist_hip_ratio"] = "Normal"
        
        # Vücut yağ oranı
        if body_fat:
            if profile.gender == "male":
                if body_fat < 10:
                    indicators["body_fat"] = "Çok Düşük"
                elif body_fat < 20:
                    indicators["body_fat"] = "Normal"
                else:
                    indicators["body_fat"] = "Yüksek"
            else:
                if body_fat < 16:
                    indicators["body_fat"] = "Çok Düşük"
                elif body_fat < 30:
                    indicators["body_fat"] = "Normal"
                else:
                    indicators["body_fat"] = "Yüksek"
        
        return indicators
    
    async def _generate_measurement_recommendations(
        self,
        entries: List[MeasurementEntry],
        user_id: int,
        db: AsyncSession
    ) -> List[str]:
        """Ölçüm önerilerini oluştur."""
        recommendations = []
        
        # Doğrulama uyarıları varsa
        for entry in entries:
            if entry.validation_result.suggestions:
                recommendations.extend(entry.validation_result.suggestions)
        
        # Genel öneriler
        if len(entries) == 1:
            recommendations.append("Daha kapsamlı analiz için diğer ölçümleri de ekleyin")
        
        # Trend bazlı öneriler
        weight_entry = next((e for e in entries if e.measurement_type == MeasurementType.WEIGHT), None)
        if weight_entry and weight_entry.change_percentage:
            if abs(weight_entry.change_percentage) > 5:
                recommendations.append("Büyük kilo değişimi - hedeflerinizi gözden geçirin")
        
        return recommendations[:3]  # En fazla 3 öneri


# ---------------------------------------------------------------------------
# Global Instance
# ---------------------------------------------------------------------------

# Singleton instance
enhanced_measurement_tracker = EnhancedMeasurementTracker()