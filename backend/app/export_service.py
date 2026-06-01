"""
Dışa Aktarma Servisi — CSV üretimi için.

Kalori günlüğü, ölçüm geçmişi ve antrenman geçmişini
in-memory CSV string olarak döndürür.
"""

import csv
import io
from datetime import date, datetime, time, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import FoodLog, Measurement, WorkoutLog


def _end_of_day(d: date) -> datetime:
    """Bir tarihin bir sonraki günün başlangıcını döndürür (to_date dahil filtresi için)."""
    return datetime.combine(d + timedelta(days=1), time.min)


class ExportService:
    """Kullanıcı verilerini CSV formatında dışa aktarır."""

    async def export_calories(
        self,
        db: AsyncSession,
        user_id: int = 1,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> str:
        """
        Kalori günlüğünü CSV string olarak döndürür.

        Sütunlar: id, food_name, grams, calories, protein, carbs, fat, meal_type, logged_at
        """
        stmt = select(FoodLog).where(FoodLog.user_id == user_id)

        if from_date is not None:
            stmt = stmt.where(FoodLog.logged_at >= datetime.combine(from_date, time.min))
        if to_date is not None:
            stmt = stmt.where(FoodLog.logged_at < _end_of_day(to_date))

        result = await db.execute(stmt)
        rows = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "food_name", "grams", "calories", "protein", "carbs", "fat", "meal_type", "logged_at"])

        for row in rows:
            writer.writerow([
                row.id,
                row.food_name,
                row.grams,
                row.calories,
                row.protein,
                row.carbs,
                row.fat,
                row.meal_type,
                row.logged_at.isoformat() if row.logged_at else "",
            ])

        return output.getvalue()

    async def export_measurements(
        self,
        db: AsyncSession,
        user_id: int = 1,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> str:
        """
        Ölçüm geçmişini CSV string olarak döndürür.

        Sütunlar: id, weight_kg, waist_cm, hip_cm, chest_cm, arm_cm, leg_cm, measured_at
        """
        stmt = select(Measurement).where(Measurement.user_id == user_id)

        if from_date is not None:
            stmt = stmt.where(Measurement.measured_at >= datetime.combine(from_date, time.min))
        if to_date is not None:
            stmt = stmt.where(Measurement.measured_at < _end_of_day(to_date))

        result = await db.execute(stmt)
        rows = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "weight_kg", "waist_cm", "hip_cm", "chest_cm", "arm_cm", "leg_cm", "measured_at"])

        for row in rows:
            writer.writerow([
                row.id,
                row.weight_kg if row.weight_kg is not None else "",
                row.waist_cm if row.waist_cm is not None else "",
                row.hip_cm if row.hip_cm is not None else "",
                row.chest_cm if row.chest_cm is not None else "",
                row.arm_cm if row.arm_cm is not None else "",
                row.leg_cm if row.leg_cm is not None else "",
                row.measured_at.isoformat() if row.measured_at else "",
            ])

        return output.getvalue()

    async def export_workouts(
        self,
        db: AsyncSession,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> str:
        """
        Antrenman geçmişini CSV string olarak döndürür.

        Sütunlar: id, program_name, completed_at, duration_minutes
        """
        stmt = select(WorkoutLog)

        if from_date is not None:
            stmt = stmt.where(WorkoutLog.completed_at >= datetime.combine(from_date, time.min))
        if to_date is not None:
            stmt = stmt.where(WorkoutLog.completed_at < _end_of_day(to_date))

        result = await db.execute(stmt)
        rows = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "program_name", "completed_at", "duration_minutes"])

        for row in rows:
            writer.writerow([
                row.id,
                row.program_name,
                row.completed_at.isoformat() if row.completed_at else "",
                row.duration_minutes,
            ])

        return output.getvalue()
