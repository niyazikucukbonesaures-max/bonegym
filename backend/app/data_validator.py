# Fitness ve Kalori Takip Uygulaması - Veri Doğrulama Sistemi
# Kilo ve ölçüm verilerinin doğruluğunu kontrol eden sistem

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from statistics import median, stdev

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Measurement
from app.schemas import MeasurementCreate


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Veri doğrulama sonucu."""
    is_valid: bool
    reason: Optional[str] = None
    suggested_value: Optional[float] = None
    confidence_score: float = 1.0


@dataclass
class OutlierDetectionResult:
    """Aykırı değer tespit sonucu."""
    outlier_indices: List[int]
    outlier_values: List[float]
    median_value: float
    std_deviation: float


# ---------------------------------------------------------------------------
# DataValidator Sınıfı
# ---------------------------------------------------------------------------

class DataValidator:
    """Veri doğrulama ve tutarlılık kontrolü sistemi."""
    
    # Doğrulama aralıkları (kg/cm)
    WEIGHT_RANGE = (30.0, 300.0)
    HEIGHT_RANGE = (100.0, 250.0)
    WAIST_RANGE = (40.0, 200.0)
    HIP_RANGE = (50.0, 200.0)
    CHEST_RANGE = (60.0, 200.0)
    ARM_RANGE = (15.0, 80.0)
    LEG_RANGE = (30.0, 120.0)
    
    # Günlük değişim limitleri
    DAILY_WEIGHT_CHANGE_LIMIT = 0.5  # kg
    MEASUREMENT_CHANGE_THRESHOLD = 0.20  # %20
    
    # Aykırı değer tespiti için parametreler
    OUTLIER_STD_MULTIPLIER = 2.0  # Standart sapmanın kaç katı aykırı sayılır
    MIN_DATA_POINTS = 3  # Aykırı değer tespiti için minimum veri sayısı

    async def validate_weight(
        self, 
        weight_kg: float, 
        user_id: int, 
        db: AsyncSession
    ) -> ValidationResult:
        """Kilo değerini doğrular.
        
        Args:
            weight_kg: Doğrulanacak kilo değeri (kg)
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            
        Returns:
            ValidationResult: Doğrulama sonucu
        """
        # Temel aralık kontrolü
        if not (self.WEIGHT_RANGE[0] <= weight_kg <= self.WEIGHT_RANGE[1]):
            return ValidationResult(
                is_valid=False,
                reason=f"Kilo değeri {self.WEIGHT_RANGE[0]}-{self.WEIGHT_RANGE[1]} kg aralığında olmalıdır",
                confidence_score=0.0
            )
        
        # Günlük değişim kontrolü - uyarı ver ama reddetme (kullanıcı birden fazla güncelleme yapabilir)
        daily_change_valid = await self.check_daily_weight_change(user_id, weight_kg, db)
        if not daily_change_valid:
            # Son kilo değerini al
            last_weight = await self._get_last_weight(user_id, db)
            if last_weight:
                change = abs(weight_kg - last_weight)
                # Geçerli kabul et ama düşük güven skoru ile uyar
                return ValidationResult(
                    is_valid=True,
                    reason=f"Günlük kilo değişimi {change:.1f} kg normalden fazla",
                    confidence_score=0.7
                )
        
        # Aykırı değer kontrolü - sadece çok büyük sapmalar için uyar
        recent_weights = await self._get_recent_weights(user_id, db, days=30)
        if len(recent_weights) >= self.MIN_DATA_POINTS:
            outlier_result = self.detect_outliers(recent_weights + [weight_kg])
            if len(outlier_result.outlier_indices) > 0 and (len(recent_weights)) in outlier_result.outlier_indices:
                # Geçerli kabul et ama uyar
                return ValidationResult(
                    is_valid=True,
                    reason=f"Değer normalden farklı görünüyor (medyan: {outlier_result.median_value:.1f} kg)",
                    confidence_score=0.6
                )
        
        return ValidationResult(is_valid=True, confidence_score=1.0)

    async def validate_measurement(self, measurement: MeasurementCreate) -> ValidationResult:
        """Ölçüm değerlerini doğrular.
        
        Args:
            measurement: Doğrulanacak ölçüm verisi
            
        Returns:
            ValidationResult: Doğrulama sonucu
        """
        # Her ölçüm tipini kontrol et
        validations = []
        
        if measurement.height_cm is not None:
            validations.append(self._validate_range(
                measurement.height_cm, 
                self.HEIGHT_RANGE, 
                "Boy"
            ))
        
        if measurement.weight_kg is not None:
            validations.append(self._validate_range(
                measurement.weight_kg, 
                self.WEIGHT_RANGE, 
                "Kilo"
            ))
        
        if measurement.waist_cm is not None:
            validations.append(self._validate_range(
                measurement.waist_cm, 
                self.WAIST_RANGE, 
                "Bel"
            ))
        
        if measurement.hip_cm is not None:
            validations.append(self._validate_range(
                measurement.hip_cm, 
                self.HIP_RANGE, 
                "Kalça"
            ))
        
        if measurement.chest_cm is not None:
            validations.append(self._validate_range(
                measurement.chest_cm, 
                self.CHEST_RANGE, 
                "Göğüs"
            ))
        
        if measurement.arm_cm is not None:
            validations.append(self._validate_range(
                measurement.arm_cm, 
                self.ARM_RANGE, 
                "Kol"
            ))
        
        if measurement.leg_cm is not None:
            validations.append(self._validate_range(
                measurement.leg_cm, 
                self.LEG_RANGE, 
                "Bacak"
            ))
        
        # Geçersiz olan varsa ilkini döndür
        for validation in validations:
            if not validation.is_valid:
                return validation
        
        return ValidationResult(is_valid=True, confidence_score=1.0)

    async def check_daily_weight_change(
        self, 
        user_id: int, 
        new_weight: float, 
        db: AsyncSession
    ) -> bool:
        """Günlük kilo değişim limitini kontrol eder.
        
        Args:
            user_id: Kullanıcı ID'si
            new_weight: Yeni kilo değeri
            db: Veritabanı oturumu
            
        Returns:
            bool: Değişim limit içindeyse True
        """
        # Bugünkü son ölçümü al
        today = datetime.now().date()
        today_start = datetime(today.year, today.month, today.day, 0, 0, 0)
        today_end = datetime(today.year, today.month, today.day, 23, 59, 59)
        
        stmt = (
            select(Measurement.weight_kg)
            .where(
                Measurement.user_id == user_id,
                Measurement.weight_kg.isnot(None),
                Measurement.measured_at >= today_start,
                Measurement.measured_at <= today_end
            )
            .order_by(Measurement.measured_at.desc())
            .limit(1)
        )
        
        result = await db.execute(stmt)
        last_today_weight = result.scalar_one_or_none()
        
        if last_today_weight is not None:
            change = abs(new_weight - last_today_weight)
            return change <= self.DAILY_WEIGHT_CHANGE_LIMIT
        
        # Bugün ölçüm yoksa dünkü son ölçümü kontrol et
        yesterday = today - timedelta(days=1)
        yesterday_start = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)
        yesterday_end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
        
        stmt = (
            select(Measurement.weight_kg)
            .where(
                Measurement.user_id == user_id,
                Measurement.weight_kg.isnot(None),
                Measurement.measured_at >= yesterday_start,
                Measurement.measured_at <= yesterday_end
            )
            .order_by(Measurement.measured_at.desc())
            .limit(1)
        )
        
        result = await db.execute(stmt)
        last_yesterday_weight = result.scalar_one_or_none()
        
        if last_yesterday_weight is not None:
            change = abs(new_weight - last_yesterday_weight)
            return change <= self.DAILY_WEIGHT_CHANGE_LIMIT
        
        # Hiç önceki ölçüm yoksa geçerli kabul et
        return True

    def detect_outliers(self, measurements: List[float]) -> OutlierDetectionResult:
        """Ölçüm serisindeki aykırı değerleri tespit eder.
        
        Args:
            measurements: Ölçüm değerleri listesi
            
        Returns:
            OutlierDetectionResult: Aykırı değer tespit sonucu
        """
        if len(measurements) < self.MIN_DATA_POINTS:
            return OutlierDetectionResult(
                outlier_indices=[],
                outlier_values=[],
                median_value=0.0,
                std_deviation=0.0
            )
        
        # İstatistiksel değerleri hesapla
        median_val = median(measurements)
        
        if len(measurements) < 2:
            return OutlierDetectionResult(
                outlier_indices=[],
                outlier_values=[],
                median_value=median_val,
                std_deviation=0.0
            )
        
        std_dev = stdev(measurements)
        
        # Aykırı değerleri tespit et (medyandan 2 standart sapma uzakta olanlar)
        outlier_indices = []
        outlier_values = []
        
        for i, value in enumerate(measurements):
            deviation = abs(value - median_val)
            if deviation > (self.OUTLIER_STD_MULTIPLIER * std_dev):
                outlier_indices.append(i)
                outlier_values.append(value)
        
        return OutlierDetectionResult(
            outlier_indices=outlier_indices,
            outlier_values=outlier_values,
            median_value=median_val,
            std_deviation=std_dev
        )

    async def validate_measurement_change(
        self, 
        user_id: int, 
        measurement_type: str, 
        new_value: float, 
        db: AsyncSession
    ) -> ValidationResult:
        """Ölçüm değişiminin %20 limitini kontrol eder.
        
        Args:
            user_id: Kullanıcı ID'si
            measurement_type: Ölçüm tipi (weight_kg, waist_cm, vb.)
            new_value: Yeni ölçüm değeri
            db: Veritabanı oturumu
            
        Returns:
            ValidationResult: Doğrulama sonucu
        """
        # Son ölçümü al
        last_value = await self._get_last_measurement_value(user_id, measurement_type, db)
        
        if last_value is None:
            return ValidationResult(is_valid=True, confidence_score=1.0)
        
        # Yüzde değişimi hesapla
        change_percent = abs(new_value - last_value) / last_value
        
        if change_percent > self.MEASUREMENT_CHANGE_THRESHOLD:
            return ValidationResult(
                is_valid=False,
                reason=f"{measurement_type} değişimi %{change_percent*100:.1f}, limit %{self.MEASUREMENT_CHANGE_THRESHOLD*100}",
                suggested_value=last_value,
                confidence_score=0.4
            )
        
        return ValidationResult(is_valid=True, confidence_score=1.0)

    # ------------------------------------------------------------------
    # Yardımcı Metodlar
    # ------------------------------------------------------------------

    def _validate_range(
        self, 
        value: float, 
        range_tuple: Tuple[float, float], 
        field_name: str
    ) -> ValidationResult:
        """Değerin belirtilen aralıkta olup olmadığını kontrol eder."""
        min_val, max_val = range_tuple
        
        if not (min_val <= value <= max_val):
            return ValidationResult(
                is_valid=False,
                reason=f"{field_name} değeri {min_val}-{max_val} aralığında olmalıdır",
                confidence_score=0.0
            )
        
        return ValidationResult(is_valid=True, confidence_score=1.0)

    async def _get_last_weight(self, user_id: int, db: AsyncSession) -> Optional[float]:
        """Kullanıcının son kilo ölçümünü getirir."""
        stmt = (
            select(Measurement.weight_kg)
            .where(
                Measurement.user_id == user_id,
                Measurement.weight_kg.isnot(None)
            )
            .order_by(Measurement.measured_at.desc())
            .limit(1)
        )
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_recent_weights(
        self, 
        user_id: int, 
        db: AsyncSession, 
        days: int = 30
    ) -> List[float]:
        """Son N gündeki kilo ölçümlerini getirir."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stmt = (
            select(Measurement.weight_kg)
            .where(
                Measurement.user_id == user_id,
                Measurement.weight_kg.isnot(None),
                Measurement.measured_at >= cutoff_date
            )
            .order_by(Measurement.measured_at.asc())
        )
        
        result = await db.execute(stmt)
        weights = result.scalars().all()
        return [float(w) for w in weights if w is not None]

    async def _get_last_measurement_value(
        self, 
        user_id: int, 
        measurement_type: str, 
        db: AsyncSession
    ) -> Optional[float]:
        """Belirtilen ölçüm tipinin son değerini getirir."""
        # Measurement modelindeki alan adını al
        field = getattr(Measurement, measurement_type, None)
        if field is None:
            return None
        
        stmt = (
            select(field)
            .where(
                Measurement.user_id == user_id,
                field.isnot(None)
            )
            .order_by(Measurement.measured_at.desc())
            .limit(1)
        )
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Global Instance
# ---------------------------------------------------------------------------

# Singleton instance
data_validator = DataValidator()