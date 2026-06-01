# Antrenman Router'ı
# GET    /programs                    → Program listesi
# POST   /programs                    → Yeni program
# DELETE /programs/{id}               → Program sil
# POST   /log                         → Antrenman kaydı
# DELETE /log/{id}                    → Antrenman kaydı sil
# GET    /history                     → Geçmiş (weeks=12)
# GET    /progress/{exercise_name}    → Egzersiz ilerlemesi
# GET    /stats                       → Haftalık istatistik

from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import WeeklyWorkoutStats, WorkoutLogCreate, WorkoutLogSchema, WorkoutProgramCreate, WorkoutProgramSchema
from app.workout_tracker import WorkoutTracker

router = APIRouter()
_tracker = WorkoutTracker()


@router.get("/programs", response_model=List[WorkoutProgramSchema])
async def list_programs(
    db: AsyncSession = Depends(get_db),
) -> List[WorkoutProgramSchema]:
    """Tüm antrenman programlarını döndürür."""
    return await _tracker.list_programs(db)


@router.post("/programs", response_model=WorkoutProgramSchema, status_code=201)
async def create_program(
    program: WorkoutProgramCreate,
    db: AsyncSession = Depends(get_db),
) -> WorkoutProgramSchema:
    """Yeni bir antrenman programı oluşturur."""
    return await _tracker.create_program(db, program)


@router.delete("/programs/{program_id}")
async def delete_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Bir antrenman programını siler."""
    success = await _tracker.delete_program(db, program_id)
    if not success:
        raise HTTPException(status_code=404, detail="Program bulunamadı")
    return {"message": "Program başarıyla silindi"}


@router.post("/log", response_model=WorkoutLogSchema, status_code=201)
async def log_workout(
    log: WorkoutLogCreate,
    db: AsyncSession = Depends(get_db),
) -> WorkoutLogSchema:
    """Tamamlanan bir antrenman seansını kaydeder."""
    return await _tracker.log_workout(db, log)


@router.delete("/log/{log_id}")
async def delete_workout_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Bir antrenman kaydını siler."""
    success = await _tracker.delete_workout_log(db, log_id)
    if not success:
        raise HTTPException(status_code=404, detail="Antrenman kaydı bulunamadı")
    return {"message": "Antrenman kaydı başarıyla silindi"}


@router.get("/history", response_model=List[WorkoutLogSchema])
async def get_history(
    weeks: int = Query(default=12, ge=1, le=52),
    db: AsyncSession = Depends(get_db),
) -> List[WorkoutLogSchema]:
    """Son N haftanın antrenman geçmişini döndürür."""
    return await _tracker.get_history(db, weeks)


@router.get("/progress/{exercise_name}")
async def get_exercise_progress(
    exercise_name: str,
    db: AsyncSession = Depends(get_db),
) -> list:
    """Belirli bir egzersiz için ilerleme verilerini döndürür."""
    points = await _tracker.get_exercise_progress(db, exercise_name)
    return [
        {
            "date": p.date.isoformat(),
            "weight_kg": p.weight_kg,
            "reps_performed": p.reps_performed,
            "sets_performed": p.sets_performed,
        }
        for p in points
    ]


@router.get("/stats", response_model=WeeklyWorkoutStats)
async def get_weekly_stats(
    user_id: int = 1,
    week_offset: int = Query(default=0, ge=0),
    weekly_goal: int = Query(default=4, ge=1, le=7),
    db: AsyncSession = Depends(get_db),
) -> WeeklyWorkoutStats:
    """Haftalık antrenman istatistiklerini döndürür."""
    stats = await _tracker.get_weekly_stats(db, user_id, week_offset)
    return WeeklyWorkoutStats(
        completed=stats.completed_count,
        goal=weekly_goal,
        percentage=(
            round(stats.completed_count / weekly_goal * 100, 1)
            if weekly_goal > 0
            else 0.0
        ),
        total_duration_minutes=stats.total_duration_minutes,
    )
