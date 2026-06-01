# Dışa Aktarma Router'ı
# GET / → CSV dışa aktarma
#   Query params: type (calories|measurements|workouts), from_date, to_date
#   Response: StreamingResponse (text/csv)

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.export_service import ExportService

router = APIRouter()
_service = ExportService()


@router.get("/")
async def export_data(
    type: str = Query(..., description="calories | measurements | workouts"),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Kullanıcı verilerini CSV formatında dışa aktarır."""
    if type == "calories":
        csv_content = await _service.export_calories(db, user_id, from_date, to_date)
        filename = "calories.csv"
    elif type == "measurements":
        csv_content = await _service.export_measurements(db, user_id, from_date, to_date)
        filename = "measurements.csv"
    elif type == "workouts":
        csv_content = await _service.export_workouts(db, from_date, to_date)
        filename = "workouts.csv"
    else:
        raise HTTPException(
            status_code=400,
            detail="Geçersiz tür. 'calories', 'measurements' veya 'workouts' olmalıdır.",
        )

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
