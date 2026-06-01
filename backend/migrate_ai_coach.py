# AI Coach Veritabanı Migration Script
# Yeni AI Coach tablolarını oluşturur ve mevcut kullanıcılar için varsayılan preferences kayıtları ekler

import asyncio
import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, init_db
from app.models import AICoachPreferences

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_ai_coach_tables():
    """AI Coach tablolarını oluşturur."""
    logger.info("AI Coach tablolarını oluşturuyor...")
    
    # Veritabanını başlat (tablolar otomatik oluşturulur)
    await init_db()
    
    logger.info("AI Coach tabloları başarıyla oluşturuldu.")


async def create_default_preferences():
    """Mevcut kullanıcılar için varsayılan AI Coach preferences kayıtları oluşturur."""
    logger.info("Mevcut kullanıcılar için varsayılan preferences oluşturuluyor...")
    
    async for session in get_db():
        try:
            # Mevcut kullanıcı ID'lerini al (user_profile tablosundan)
            result = await session.execute(text("SELECT DISTINCT id FROM user_profile"))
            user_ids = [row[0] for row in result.fetchall()]
            
            if not user_ids:
                logger.info("Henüz kullanıcı profili yok, preferences oluşturulmadı.")
                return
            
            # Her kullanıcı için varsayılan preferences oluştur
            for user_id in user_ids:
                # Zaten preferences kaydı var mı kontrol et
                existing = await session.execute(
                    text("SELECT id FROM ai_coach_preferences WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                
                if existing.fetchone():
                    logger.info(f"Kullanıcı {user_id} için preferences zaten mevcut, atlanıyor.")
                    continue
                
                # Yeni preferences kaydı oluştur
                preferences = AICoachPreferences(
                    user_id=user_id,
                    preferred_workout_types=[
                        "strength_training",
                        "cardio",
                        "flexibility"
                    ],
                    preferred_duration_min=30,
                    preferred_duration_max=60,
                    preferred_intensity={
                        "low": 0.3,
                        "moderate": 0.5,
                        "high": 0.2
                    },
                    avoided_exercises=[],
                    health_conditions=[],
                    learned_patterns={
                        "workout_frequency": {},
                        "preferred_times": {},
                        "completion_patterns": {}
                    },
                    feedback_history={
                        "accepted": 0,
                        "rejected": 0,
                        "modified": 0,
                        "total_recommendations": 0
                    },
                    motivation_style="balanced",
                    safety_level="standard",
                    updated_at=datetime.utcnow()
                )
                
                session.add(preferences)
                logger.info(f"Kullanıcı {user_id} için varsayılan preferences oluşturuldu.")
            
            await session.commit()
            logger.info(f"Toplam {len(user_ids)} kullanıcı için preferences oluşturuldu.")
            
        except Exception as e:
            logger.error(f"Preferences oluşturulurken hata: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def verify_migration():
    """Migration'ın başarılı olduğunu doğrular."""
    logger.info("Migration doğrulanıyor...")
    
    async for session in get_db():
        try:
            # AI Coach tablolarının varlığını kontrol et
            tables_to_check = [
                "ai_coach_recommendations",
                "ai_coach_progress", 
                "ai_coach_preferences"
            ]
            
            for table_name in tables_to_check:
                result = await session.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                )
                if not result.fetchone():
                    raise Exception(f"Tablo {table_name} oluşturulamadı!")
                logger.info(f"✓ Tablo {table_name} başarıyla oluşturuldu.")
            
            # Preferences kayıt sayısını kontrol et
            result = await session.execute(text("SELECT COUNT(*) FROM ai_coach_preferences"))
            preferences_count = result.fetchone()[0]
            logger.info(f"✓ {preferences_count} adet preferences kaydı oluşturuldu.")
            
            logger.info("Migration başarıyla tamamlandı!")
            
        except Exception as e:
            logger.error(f"Migration doğrulanırken hata: {e}")
            raise
        finally:
            await session.close()


async def main():
    """Ana migration fonksiyonu."""
    try:
        logger.info("AI Coach Migration başlatılıyor...")
        
        # 1. Tabloları oluştur
        await create_ai_coach_tables()
        
        # 2. Varsayılan preferences kayıtları oluştur
        await create_default_preferences()
        
        # 3. Migration'ı doğrula
        await verify_migration()
        
        logger.info("AI Coach Migration başarıyla tamamlandı! 🎉")
        
    except Exception as e:
        logger.error(f"Migration sırasında hata oluştu: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())