# Fitness ve Kalori Takip Uygulaması - Kreatin Takipçi
# Kreatin faz yönetimi, doz kayıt ve bildirimler.

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CreatineDose
from app.schemas import CreatineDoseCreate, CreatineDoseSchema, TodayCreatineStatus

# Yükleme fazı sabitleri
LOADING_PHASE_DAYS = 7
LOADING_DAILY_GRAMS = 20.0

# İdame fazı sabitleri
MAINTENANCE_MIN_GRAMS = 3.0
MAINTENANCE_MAX_GRAMS = 5.0


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------


@dataclass
class PhaseInfo:
    """Mevcut kreatin fazı bilgisi."""

    phase: str          # "loading" | "maintenance"
    days_in_phase: int  # Mevcut fazda geçen gün sayısı
    total_grams: float  # Toplam alınan kreatin miktarı (gram)


# ---------------------------------------------------------------------------
# CreatineTracker
# ---------------------------------------------------------------------------


class CreatineTracker:
    """Kreatin faz yönetimi, doz kayıt ve bildirimler."""

    # ------------------------------------------------------------------
    # Doz Kayıt
    # ------------------------------------------------------------------

    async def log_dose(
        self, db: AsyncSession, dose: CreatineDoseCreate
    ) -> CreatineDoseSchema:
        """Yeni bir kreatin dozu kaydeder.

        Args:
            db: Async veritabanı oturumu
            dose: Kaydedilecek doz verisi

        Returns:
            CreatineDoseSchema: Oluşturulan doz kaydı
        """
        db_dose = CreatineDose(
            user_id=dose.user_id,
            dose_grams=dose.dose_grams,
            phase=dose.phase,
            taken_at=datetime.now(timezone.utc),
        )
        db.add(db_dose)
        await db.flush()
        await db.refresh(db_dose)
        return CreatineDoseSchema.model_validate(db_dose)

    # ------------------------------------------------------------------
    # Doz Silme
    # ------------------------------------------------------------------

    async def delete_dose(
        self, db: AsyncSession, dose_id: int, user_id: int = 1
    ) -> bool:
        """Bir kreatin dozunu siler.

        Args:
            db: Async veritabanı oturumu
            dose_id: Silinecek doz ID'si
            user_id: Kullanıcı ID'si (güvenlik için)

        Returns:
            bool: Silme işlemi başarılı ise True
        """
        stmt = select(CreatineDose).where(
            CreatineDose.id == dose_id,
            CreatineDose.user_id == user_id
        )
        result = await db.execute(stmt)
        dose = result.scalar_one_or_none()
        
        if dose is None:
            return False
        
        await db.delete(dose)
        await db.flush()
        return True

    # ------------------------------------------------------------------
    # Faz Bilgisi
    # ------------------------------------------------------------------

    async def get_current_phase(
        self, db: AsyncSession, user_id: int = 1
    ) -> PhaseInfo:
        """Kullanıcının mevcut kreatin fazını döndürür.

        İlk kayıt yoksa varsayılan olarak yükleme fazı döndürülür.
        Yükleme fazında 7 gün geçince idame fazına geçilmiş sayılır.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si

        Returns:
            PhaseInfo: Mevcut faz, fazda geçen gün ve toplam gram
        """
        stmt = (
            select(CreatineDose)
            .where(CreatineDose.user_id == user_id)
            .order_by(CreatineDose.taken_at.asc())
        )
        result = await db.execute(stmt)
        all_doses = result.scalars().all()

        if not all_doses:
            return PhaseInfo(phase="loading", days_in_phase=0, total_grams=0.0)

        total_grams = sum(d.dose_grams for d in all_doses)

        # En son kaydın fazını kullan
        latest_dose = all_doses[-1]
        current_phase = latest_dose.phase

        # Mevcut fazda geçen gün sayısını hesapla
        # Aynı fazda olan kayıtların ilk tarihinden itibaren gün sayısı
        phase_doses = [d for d in all_doses if d.phase == current_phase]
        if phase_doses:
            first_in_phase = phase_doses[0].taken_at
            now = datetime.now(timezone.utc)
            # taken_at timezone-naive olabilir, normalize et
            if first_in_phase.tzinfo is None:
                first_in_phase = first_in_phase.replace(tzinfo=timezone.utc)
            days_in_phase = (now - first_in_phase).days
        else:
            days_in_phase = 0

        return PhaseInfo(
            phase=current_phase,
            days_in_phase=days_in_phase,
            total_grams=total_grams,
        )

    # ------------------------------------------------------------------
    # Geçmiş
    # ------------------------------------------------------------------

    async def get_history(
        self, db: AsyncSession, user_id: int = 1, days: int = 30
    ) -> list[CreatineDoseSchema]:
        """Son N günün kreatin doz kayıtlarını döndürür.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si
            days: Kaç günlük geçmiş getirileceği (varsayılan: 30)

        Returns:
            List[CreatineDoseSchema]: Doz kayıtları listesi
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(CreatineDose)
            .where(
                CreatineDose.user_id == user_id,
                CreatineDose.taken_at >= cutoff,
            )
            .order_by(CreatineDose.taken_at.desc())
        )
        result = await db.execute(stmt)
        doses = result.scalars().all()
        return [CreatineDoseSchema.model_validate(d) for d in doses]

    # ------------------------------------------------------------------
    # Faz Geçiş Kontrolü
    # ------------------------------------------------------------------

    async def check_phase_transition(
        self, db: AsyncSession, user_id: int = 1
    ) -> Optional[str]:
        """Yükleme fazı tamamlandıysa geçiş bildirimi döndürür.

        Yükleme fazında 7 gün geçince idame fazına geçiş bildirimi üretir.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si

        Returns:
            Optional[str]: Geçiş bildirimi veya None
        """
        phase_info = await self.get_current_phase(db, user_id)

        if (
            phase_info.phase == "loading"
            and phase_info.days_in_phase >= LOADING_PHASE_DAYS
        ):
            return (
                "Yükleme fazı tamamlandı! "
                "İdame fazına geçebilirsiniz (günde 3-5g)."
            )

        return None

    # ------------------------------------------------------------------
    # Bugünkü Durum
    # ------------------------------------------------------------------

    async def get_today_status(
        self, db: AsyncSession, user_id: int = 1
    ) -> TodayCreatineStatus:
        """Bugünkü kreatin alım durumunu döndürür.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si

        Returns:
            TodayCreatineStatus: Bugünkü alım durumu
        """
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        stmt = (
            select(CreatineDose)
            .where(
                CreatineDose.user_id == user_id,
                CreatineDose.taken_at >= today_start,
                CreatineDose.taken_at < today_end,
            )
            .order_by(CreatineDose.taken_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        today_dose = result.scalar_one_or_none()

        phase_info = await self.get_current_phase(db, user_id)

        if today_dose is None:
            return TodayCreatineStatus(
                taken=False,
                dose_grams=None,
                phase=phase_info.phase if phase_info.days_in_phase > 0 else None,
                days_in_phase=phase_info.days_in_phase,
                total_grams=phase_info.total_grams,
            )

        return TodayCreatineStatus(
            taken=True,
            dose_grams=today_dose.dose_grams,
            phase=today_dose.phase,
            days_in_phase=phase_info.days_in_phase,
            total_grams=phase_info.total_grams,
        )

    # ------------------------------------------------------------------
    # Bildirimler
    # ------------------------------------------------------------------

    async def get_notifications(
        self, db: AsyncSession, user_id: int = 1
    ) -> list[str]:
        """Kreatin bildirimlerini üretir.

        Bugün kreatin alınmadıysa hatırlatma bildirimi üretir.
        Yükleme fazı tamamlandıysa geçiş bildirimi ekler.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si

        Returns:
            List[str]: Bildirim mesajları listesi
        """
        notifications: list[str] = []

        today_status = await self.get_today_status(db, user_id)
        if not today_status.taken:
            notifications.append("Bugün kreatin almayı unutmayın!")

        transition_msg = await self.check_phase_transition(db, user_id)
        if transition_msg:
            notifications.append(transition_msg)

        return notifications
