"""
Test verisi ekler - antrenman, kreatin ve ölçüm kayıtları
"""
import asyncio
from datetime import datetime, timedelta
from app.database import get_db, init_db
from app.models import WorkoutProgram, WorkoutLog, CreatineDose, Measurement, UserProfile

async def add_test_data():
    """Test verilerini ekler."""
    await init_db()
    
    async for db in get_db():
        now = datetime.utcnow()
        
        # Kullanıcı profili ekle
        profile = UserProfile(
            weight_kg=75,
            height_cm=175,
            age=25,
            gender="male",
            activity_level="moderate",
            goal="maintain",
            weekly_workout_goal=4
        )
        db.add(profile)
        
        # Antrenman programı ekle
        program = WorkoutProgram(
            name="Push Pull Legs"
        )
        db.add(program)
        await db.flush()  # ID'yi al
        
        # 5 gün önce antrenman kaydı ekle
        workout = WorkoutLog(
            program_id=program.id,
            program_name=program.name,
            completed_at=now - timedelta(days=5),
            duration_minutes=60
        )
        db.add(workout)
        
        # 10 gün önce kilo ölçümü ekle
        measurement = Measurement(
            user_id=1,
            weight_kg=75.5,
            measured_at=now - timedelta(days=10)
        )
        db.add(measurement)
        
        # 2 gün önce kreatin dozu ekle
        creatine = CreatineDose(
            user_id=1,
            dose_grams=5.0,
            phase="loading",
            taken_at=now - timedelta(days=2)
        )
        db.add(creatine)
        
        await db.commit()
        print("✅ Test verileri eklendi!")
        break

if __name__ == "__main__":
    asyncio.run(add_test_data())