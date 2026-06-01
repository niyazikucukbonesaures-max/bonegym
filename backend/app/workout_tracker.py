# Fitness ve Kalori Takip Uygulaması - Spor Takipçi
# Antrenman programı CRUD, geçmiş kayıt, ilerleme takibi ve bildirimler.

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Exercise, ExerciseLog, WorkoutLog, WorkoutProgram
from app.schemas import (
    ExerciseLogSchema,
    WorkoutLogCreate,
    WorkoutLogSchema,
    WorkoutProgramCreate,
    WorkoutProgramSchema,
)


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------


@dataclass
class ProgressPoint:
    """Belirli bir egzersiz için tek bir ilerleme noktası."""

    date: datetime
    weight_kg: float
    reps_performed: int
    sets_performed: int


@dataclass
class WeeklyStats:
    """Haftalık antrenman istatistikleri."""

    completed_count: int
    total_duration_minutes: int
    workout_days: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# WorkoutTracker
# ---------------------------------------------------------------------------


class WorkoutTracker:
    """Antrenman programı ve geçmiş yönetimi."""

    # ------------------------------------------------------------------
    # Program Yönetimi
    # ------------------------------------------------------------------

    async def create_program(
        self, db: AsyncSession, program: WorkoutProgramCreate
    ) -> WorkoutProgramSchema:
        """Yeni bir antrenman programı ve egzersizlerini oluşturur.

        Args:
            db: Async veritabanı oturumu
            program: Oluşturulacak program verisi

        Returns:
            WorkoutProgramSchema: Oluşturulan program
        """
        db_program = WorkoutProgram(
            name=program.name,
            created_at=datetime.now(timezone.utc),
        )
        db.add(db_program)
        await db.flush()

        for ex in program.exercises:
            db_exercise = Exercise(
                program_id=db_program.id,
                name=ex.name,
                sets=ex.sets,
                reps=ex.reps,
                weight_kg=ex.weight_kg,
                order=ex.order,
            )
            db.add(db_exercise)

        await db.flush()
        await db.refresh(db_program)

        # İlişkili egzersizleri yükle
        stmt = (
            select(WorkoutProgram)
            .options(selectinload(WorkoutProgram.exercises))
            .where(WorkoutProgram.id == db_program.id)
        )
        result = await db.execute(stmt)
        db_program = result.scalar_one()

        return WorkoutProgramSchema.model_validate(db_program)

    async def delete_program(self, db: AsyncSession, program_id: int) -> bool:
        """Bir antrenman programını ve ilişkili egzersizleri siler.

        Args:
            db: Async veritabanı oturumu
            program_id: Silinecek program ID'si

        Returns:
            bool: Silme işlemi başarılı ise True
        """
        stmt = select(WorkoutProgram).where(WorkoutProgram.id == program_id)
        result = await db.execute(stmt)
        program = result.scalar_one_or_none()
        
        if program is None:
            return False
        
        await db.delete(program)
        await db.flush()
        return True

    async def list_programs(self, db: AsyncSession) -> list[WorkoutProgramSchema]:
        """Tüm antrenman programlarını egzersizleriyle birlikte döndürür.

        Args:
            db: Async veritabanı oturumu

        Returns:
            List[WorkoutProgramSchema]: Program listesi
        """
        stmt = (
            select(WorkoutProgram)
            .options(selectinload(WorkoutProgram.exercises))
            .order_by(WorkoutProgram.created_at.desc())
        )
        result = await db.execute(stmt)
        programs = result.scalars().all()
        return [WorkoutProgramSchema.model_validate(p) for p in programs]

    # ------------------------------------------------------------------
    # Antrenman Kaydı
    # ------------------------------------------------------------------

    async def log_workout(
        self, db: AsyncSession, log: WorkoutLogCreate
    ) -> WorkoutLogSchema:
        """Tamamlanan bir antrenman seansını kaydeder.

        Args:
            db: Async veritabanı oturumu
            log: Kaydedilecek antrenman verisi

        Returns:
            WorkoutLogSchema: Oluşturulan antrenman kaydı
        """
        db_log = WorkoutLog(
            program_id=log.program_id,
            program_name=log.program_name,
            completed_at=datetime.now(timezone.utc),
            duration_minutes=log.duration_minutes,
        )
        db.add(db_log)
        await db.flush()

        for ex in log.exercises_performed:
            db_ex_log = ExerciseLog(
                workout_log_id=db_log.id,
                exercise_name=ex.exercise_name,
                sets_performed=ex.sets_performed,
                reps_performed=ex.reps_performed,
                weight_kg=ex.weight_kg,
            )
            db.add(db_ex_log)

        await db.flush()

        # İlişkili egzersiz kayıtlarını yükle
        stmt = (
            select(WorkoutLog)
            .options(selectinload(WorkoutLog.exercise_logs))
            .where(WorkoutLog.id == db_log.id)
        )
        result = await db.execute(stmt)
        db_log = result.scalar_one()

        return WorkoutLogSchema.model_validate(db_log)

    async def delete_workout_log(self, db: AsyncSession, log_id: int) -> bool:
        """Bir antrenman kaydını ve ilişkili egzersiz kayıtlarını siler.

        Args:
            db: Async veritabanı oturumu
            log_id: Silinecek antrenman kaydı ID'si

        Returns:
            bool: Silme işlemi başarılı ise True
        """
        stmt = select(WorkoutLog).where(WorkoutLog.id == log_id)
        result = await db.execute(stmt)
        workout_log = result.scalar_one_or_none()
        
        if workout_log is None:
            return False
        
        await db.delete(workout_log)
        await db.flush()
        return True

    # ------------------------------------------------------------------
    # Geçmiş ve İstatistikler
    # ------------------------------------------------------------------

    async def get_history(
        self, db: AsyncSession, weeks: int = 12
    ) -> list[WorkoutLogSchema]:
        """Son N haftanın antrenman kayıtlarını döndürür.

        Args:
            db: Async veritabanı oturumu
            weeks: Kaç haftalık geçmiş getirileceği (varsayılan: 12)

        Returns:
            List[WorkoutLogSchema]: Antrenman kayıtları listesi
        """
        cutoff = datetime.utcnow() - timedelta(weeks=weeks)

        stmt = (
            select(WorkoutLog)
            .options(selectinload(WorkoutLog.exercise_logs))
            .where(WorkoutLog.completed_at >= cutoff)
            .order_by(WorkoutLog.completed_at.desc())
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()
        return [WorkoutLogSchema.model_validate(log) for log in logs]

    async def get_exercise_progress(
        self, db: AsyncSession, exercise_name: str
    ) -> list[ProgressPoint]:
        """Belirli bir egzersiz için ağırlık/tekrar ilerlemesini döndürür.

        Args:
            db: Async veritabanı oturumu
            exercise_name: Egzersiz adı

        Returns:
            List[ProgressPoint]: Tarih sıralı ilerleme noktaları
        """
        stmt = (
            select(ExerciseLog, WorkoutLog.completed_at)
            .join(WorkoutLog, ExerciseLog.workout_log_id == WorkoutLog.id)
            .where(ExerciseLog.exercise_name == exercise_name)
            .order_by(WorkoutLog.completed_at.asc())
        )
        result = await db.execute(stmt)
        rows = result.all()

        return [
            ProgressPoint(
                date=completed_at,
                weight_kg=ex_log.weight_kg,
                reps_performed=ex_log.reps_performed,
                sets_performed=ex_log.sets_performed,
            )
            for ex_log, completed_at in rows
        ]

    async def get_weekly_stats(
        self, db: AsyncSession, user_id: int = 1, week_offset: int = 0
    ) -> WeeklyStats:
        """Belirli bir haftanın antrenman istatistiklerini döndürür.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si (şu an tek kullanıcı destekleniyor)
            week_offset: Kaç hafta geriye gidileceği (0 = bu hafta)

        Returns:
            WeeklyStats: Haftalık tamamlanan antrenman sayısı, toplam süre ve günler
        """
        now = datetime.now(timezone.utc)
        # Haftanın başı (Pazartesi)
        days_since_monday = now.weekday()
        week_start = (now - timedelta(days=days_since_monday + week_offset * 7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        week_end = week_start + timedelta(days=7)

        stmt = (
            select(WorkoutLog)
            .where(
                WorkoutLog.completed_at >= week_start,
                WorkoutLog.completed_at < week_end,
            )
            .order_by(WorkoutLog.completed_at.asc())
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()

        completed_count = len(logs)
        total_duration = sum(log.duration_minutes for log in logs)

        # Benzersiz antrenman günlerini topla (YYYY-MM-DD formatında)
        workout_days = sorted(
            {log.completed_at.strftime("%Y-%m-%d") for log in logs}
        )

        return WeeklyStats(
            completed_count=completed_count,
            total_duration_minutes=total_duration,
            workout_days=workout_days,
        )

    # ------------------------------------------------------------------
    # Bildirimler
    # ------------------------------------------------------------------

    async def get_notifications(
        self, db: AsyncSession, user_id: int = 1
    ) -> list[str]:
        """Antrenman bildirimlerini üretir.

        3 gün veya daha uzun süre antrenman yapılmadıysa hatırlatma bildirimi üretir.

        Args:
            db: Async veritabanı oturumu
            user_id: Kullanıcı ID'si

        Returns:
            List[str]: Bildirim mesajları listesi
        """
        notifications: list[str] = []

        cutoff = datetime.now(timezone.utc) - timedelta(days=3)

        stmt = (
            select(WorkoutLog)
            .where(WorkoutLog.completed_at >= cutoff)
            .order_by(WorkoutLog.completed_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        recent_log = result.scalar_one_or_none()

        if recent_log is None:
            notifications.append(
                "3 gündür antrenman yapmadınız! Bugün antrenmana başlayın."
            )

        return notifications
