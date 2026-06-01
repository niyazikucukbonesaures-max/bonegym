# Fitness ve Kalori Takip Uygulaması - Ölçüm Takipçi
# Kilo ve vücut ölçümü CRUD, trend hesaplama ve bildirimler.

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Measurement
from app.schemas import MeasurementCreate, MeasurementDelta, MeasurementSchema


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------


@dataclass
class TrendData:
    """Belirli bir süre için ölçüm trend verisi."""

    measurements: List[MeasurementSchema]
    days: int


# ---------------------------------------------------------------------------
# MeasurementTracker
# ---------------------------------------------------------------------------


class MeasurementTracker:
    """Kilo ve vücut ölçümü CRUD, trend hesaplama ve bildirimler."""

    # ------------------------------------------------------------------
    # Ölçüm Ekleme
    # ------------------------------------------------------------------

    async def add_measurement(
        self, db: AsyncSession, m: MeasurementCreate
    ) -> MeasurementSchema:
        """Yeni bir ölçüm kaydeder. measured_at otomatik olarak şimdiki zaman ile doldurulur.

        Args:
            db: Async veritabanı oturumu
            m: Kaydedilecek ölçüm verisi

        Returns:
            MeasurementSchema: Oluşturulan ölçüm kaydı
        """
        db_measurement = Measurement(
            user_id=m.user_id,
            height_cm=m.height_cm,
            weight_kg=m.weight_kg,
            waist_cm=m.waist_cm,
            hip_cm=m.hip_cm,
            chest_cm=m.chest_cm,
            arm_cm=m.arm_cm,
            leg_cm=m.leg_cm,
            measured_at=datetime.now(timezone.utc),
        )
        db.add(db_measurement)
        await db.flush()
        await db.refresh(db_measurement)
        return MeasurementSchema.model_validate(db_measurement)

    # ------------------------------------------------------------------
    # Ölçüm Silme
    # ------------------------------------------------------------------

    async def delete_measurement(
        self, db: AsyncSession, measurement_id: int, user_id: int = 1
    ) -> bool:
        """Bir ölçümü siler.

        Args:
            db: Async veritabanı oturumu
            measurement_id: Silinecek ölçüm ID'si
            user_id: Kullanıcı ID'si (güvenlik için)

        Returns:
            bool: Silme işlemi başarılı ise True
        """
        stmt = select(Measurement).where(
            Measurement.id == measurement_id,
            Measurement.user_id == user_id
        )
        result = await db.execute(stmt)
        measurement = result.scalar_one_or_none()
        
        if measurement is None:
            return False
        
        await db.delete(measurement)
        await db.flush()
        return True

    # ------------------------------------------------------------------
    # Geçmiş
    # ------------------------------------------------------------------

    async def get_history(
        self, db: AsyncSession, user_id: int = 1,
        limit: int = 20, offset: int = 0
    ) -> List[MeasurementSchema]:
        """Kullanıcının ölçüm geçmişini sayfalı döndürür.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si
            limit: Sayfa başına kayıt sayısı (varsayılan: 20)
            offset: Başlangıç noktası (varsayılan: 0)

        Returns:
            List[MeasurementSchema]: Ölçüm kayıtları listesi (en yeniden eskiye)
        """
        stmt = (
            select(Measurement)
            .where(Measurement.user_id == user_id)
            .order_by(Measurement.measured_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        measurements = result.scalars().all()
        return [MeasurementSchema.model_validate(m) for m in measurements]

    # ------------------------------------------------------------------
    # Trend
    # ------------------------------------------------------------------

    async def get_trend(
        self, db: AsyncSession, user_id: int = 1, days: int = 30
    ) -> TrendData:
        """Son N günün ölçüm trend verisini döndürür.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si
            days: Kaç günlük trend getirileceği (varsayılan: 30)

        Returns:
            TrendData: Ölçümler ve gün sayısı
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(Measurement)
            .where(
                Measurement.user_id == user_id,
                Measurement.measured_at >= cutoff,
            )
            .order_by(Measurement.measured_at.asc())
        )
        result = await db.execute(stmt)
        measurements = result.scalars().all()
        schemas = [MeasurementSchema.model_validate(m) for m in measurements]
        return TrendData(measurements=schemas, days=days)

    # ------------------------------------------------------------------
    # Delta (İlk - Son Fark)
    # ------------------------------------------------------------------

    async def get_delta(
        self, db: AsyncSession, user_id: int = 1
    ) -> MeasurementDelta:
        """İlk kayıt ile son kayıt arasındaki farkı hesaplar.

        Her alan için: delta = son_değer - ilk_değer
        Kayıt yoksa veya tek kayıt varsa tüm alanlar None döner.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si

        Returns:
            MeasurementDelta: Ölçüm farkları
        """
        stmt = (
            select(Measurement)
            .where(Measurement.user_id == user_id)
            .order_by(Measurement.measured_at.asc())
        )
        result = await db.execute(stmt)
        measurements = result.scalars().all()

        if len(measurements) < 2:
            return MeasurementDelta()

        first = measurements[0]
        last = measurements[-1]

        def _delta(a: Optional[float], b: Optional[float]) -> Optional[float]:
            if a is None or b is None:
                return None
            return round(b - a, 2)

        return MeasurementDelta(
            height_cm=_delta(first.height_cm, last.height_cm),
            weight_kg=_delta(first.weight_kg, last.weight_kg),
            waist_cm=_delta(first.waist_cm, last.waist_cm),
            hip_cm=_delta(first.hip_cm, last.hip_cm),
            chest_cm=_delta(first.chest_cm, last.chest_cm),
            arm_cm=_delta(first.arm_cm, last.arm_cm),
            leg_cm=_delta(first.leg_cm, last.leg_cm),
        )

    # ------------------------------------------------------------------
    # Bildirimler
    # ------------------------------------------------------------------

    async def get_notifications(
        self, db: AsyncSession, user_id: int = 1
    ) -> List[str]:
        """Ölçüm bildirimlerini üretir.

        Son 7 günde kilo kaydı yoksa hatırlatma bildirimi üretir.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si

        Returns:
            List[str]: Bildirim mesajları listesi
        """
        notifications: List[str] = []

        cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        stmt = (
            select(Measurement)
            .where(
                Measurement.user_id == user_id,
                Measurement.measured_at >= cutoff,
                Measurement.weight_kg.isnot(None),
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        recent_weight = result.scalar_one_or_none()

        if recent_weight is None:
            notifications.append(
                "7 gündür kilo kaydı yapmadınız! Ölçümlerinizi güncelleyin."
            )

        return notifications
