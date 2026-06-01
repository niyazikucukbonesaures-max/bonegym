#!/usr/bin/env python3
# Fitness Kalori Takip İyileştirme - Veritabanı Migration Script
# Yeni tabloları oluşturur ve mevcut tabloları günceller

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Backend dizinini Python path'ine ekle
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine
from app.models import Base


async def check_table_exists(session: AsyncSession, table_name: str) -> bool:
    """Tablonun var olup olmadığını kontrol eder."""
    result = await session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
        {"table_name": table_name}
    )
    return result.fetchone() is not None


async def check_column_exists(session: AsyncSession, table_name: str, column_name: str) -> bool:
    """Kolonun var olup olmadığını kontrol eder."""
    result = await session.execute(
        text(f"PRAGMA table_info({table_name})")
    )
    columns = result.fetchall()
    return any(col[1] == column_name for col in columns)


async def create_new_tables(session: AsyncSession):
    """Yeni tabloları oluşturur."""
    print("🔧 Yeni tabloları oluşturuluyor...")
    
    # WeightValidation tablosu
    if not await check_table_exists(session, "weight_validations"):
        await session.execute(text("""
            CREATE TABLE weight_validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                weight_kg REAL NOT NULL,
                previous_weight_kg REAL,
                change_kg REAL NOT NULL,
                is_valid BOOLEAN NOT NULL,
                validation_reason TEXT,
                validated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✅ weight_validations tablosu oluşturuldu")
    else:
        print("⚠️  weight_validations tablosu zaten mevcut")
    
    # SportProfile tablosu
    if not await check_table_exists(session, "sport_profiles"):
        await session.execute(text("""
            CREATE TABLE sport_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                is_athlete BOOLEAN DEFAULT FALSE,
                sport_type TEXT,
                training_frequency INTEGER DEFAULT 3,
                training_intensity TEXT DEFAULT 'moderate',
                rest_day_calories_adjustment REAL DEFAULT 1.05,
                training_day_calories_adjustment REAL DEFAULT 1.15,
                preferred_macro_split TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✅ sport_profiles tablosu oluşturuldu")
    else:
        print("⚠️  sport_profiles tablosu zaten mevcut")
    
    # TrendAnalysis tablosu
    if not await check_table_exists(session, "trend_analyses"):
        await session.execute(text("""
            CREATE TABLE trend_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                analysis_type TEXT NOT NULL,
                period_start DATETIME NOT NULL,
                period_end DATETIME NOT NULL,
                weight_change_kg REAL,
                average_weekly_change REAL,
                trend_direction TEXT NOT NULL,
                confidence_score REAL DEFAULT 0.0,
                insights TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✅ trend_analyses tablosu oluşturuldu")
    else:
        print("⚠️  trend_analyses tablosu zaten mevcut")
    
    # NotificationPreferences tablosu
    if not await check_table_exists(session, "notification_preferences"):
        await session.execute(text("""
            CREATE TABLE notification_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                weight_reminders BOOLEAN DEFAULT TRUE,
                measurement_reminders BOOLEAN DEFAULT TRUE,
                motivation_messages BOOLEAN DEFAULT TRUE,
                progress_reports BOOLEAN DEFAULT TRUE,
                max_daily_notifications INTEGER DEFAULT 2,
                preferred_reminder_time TEXT,
                quiet_hours_start TEXT,
                quiet_hours_end TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✅ notification_preferences tablosu oluşturuldu")
    else:
        print("⚠️  notification_preferences tablosu zaten mevcut")
    
    # DataBackup tablosu
    if not await check_table_exists(session, "data_backups"):
        await session.execute(text("""
            CREATE TABLE data_backups (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                backup_type TEXT NOT NULL,
                data_encrypted TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                checksum TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL
            )
        """))
        print("✅ data_backups tablosu oluşturuldu")
    else:
        print("⚠️  data_backups tablosu zaten mevcut")


async def update_existing_tables(session: AsyncSession):
    """Mevcut tabloları günceller."""
    print("🔧 Mevcut tablolar güncelleniyor...")
    
    # UserProfile tablosuna yeni kolonlar ekle
    user_profile_columns = [
        ("is_athlete", "BOOLEAN DEFAULT FALSE"),
        ("preferred_measurement_time", "TEXT"),
        ("data_retention_days", "INTEGER DEFAULT 365"),
        ("privacy_level", "TEXT DEFAULT 'standard'")
    ]
    
    for column_name, column_def in user_profile_columns:
        if not await check_column_exists(session, "user_profile", column_name):
            await session.execute(text(f"ALTER TABLE user_profile ADD COLUMN {column_name} {column_def}"))
            print(f"✅ user_profile.{column_name} kolonu eklendi")
        else:
            print(f"⚠️  user_profile.{column_name} kolonu zaten mevcut")
    
    # Measurements tablosuna yeni kolonlar ekle
    measurements_columns = [
        ("is_validated", "BOOLEAN DEFAULT TRUE"),
        ("validation_notes", "TEXT"),
        ("measurement_method", "TEXT DEFAULT 'manual'"),
        ("confidence_score", "REAL DEFAULT 1.0")
    ]
    
    for column_name, column_def in measurements_columns:
        if not await check_column_exists(session, "measurements", column_name):
            await session.execute(text(f"ALTER TABLE measurements ADD COLUMN {column_name} {column_def}"))
            print(f"✅ measurements.{column_name} kolonu eklendi")
        else:
            print(f"⚠️  measurements.{column_name} kolonu zaten mevcut")


async def create_indexes(session: AsyncSession):
    """Performans için indexler oluşturur."""
    print("🔧 İndeksler oluşturuluyor...")
    
    indexes = [
        ("idx_weight_validations_user_id", "weight_validations", "user_id"),
        ("idx_weight_validations_validated_at", "weight_validations", "validated_at"),
        ("idx_sport_profiles_user_id", "sport_profiles", "user_id"),
        ("idx_trend_analyses_user_id", "trend_analyses", "user_id"),
        ("idx_trend_analyses_period", "trend_analyses", "period_start, period_end"),
        ("idx_notification_preferences_user_id", "notification_preferences", "user_id"),
        ("idx_data_backups_user_id", "data_backups", "user_id"),
        ("idx_data_backups_created_at", "data_backups", "created_at"),
        ("idx_measurements_user_id_measured_at", "measurements", "user_id, measured_at"),
        ("idx_measurements_weight_kg", "measurements", "weight_kg"),
    ]
    
    for index_name, table_name, columns in indexes:
        try:
            await session.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})"))
            print(f"✅ {index_name} indeksi oluşturuldu")
        except Exception as e:
            print(f"⚠️  {index_name} indeksi oluşturulamadı: {e}")


async def insert_default_data(session: AsyncSession):
    """Varsayılan verileri ekler."""
    print("🔧 Varsayılan veriler ekleniyor...")
    
    # Mevcut kullanıcılar için varsayılan bildirim tercihleri oluştur
    try:
        # Önce mevcut kullanıcıları kontrol et (user_profile tablosundan)
        result = await session.execute(text("SELECT DISTINCT id FROM user_profile"))
        user_ids = [row[0] for row in result.fetchall()]
        
        for user_id in user_ids:
            # Bu kullanıcı için bildirim tercihi var mı kontrol et
            existing = await session.execute(
                text("SELECT id FROM notification_preferences WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            
            if not existing.fetchone():
                # Varsayılan bildirim tercihleri ekle
                await session.execute(text("""
                    INSERT INTO notification_preferences 
                    (user_id, weight_reminders, measurement_reminders, motivation_messages, progress_reports, max_daily_notifications)
                    VALUES (:user_id, TRUE, TRUE, TRUE, TRUE, 2)
                """), {"user_id": user_id})
                print(f"✅ Kullanıcı {user_id} için varsayılan bildirim tercihleri eklendi")
        
        if user_ids:
            print(f"✅ {len(user_ids)} kullanıcı için varsayılan veriler eklendi")
        else:
            print("ℹ️  Henüz kullanıcı bulunamadı, varsayılan veriler atlandı")
            
    except Exception as e:
        print(f"⚠️  Varsayılan veriler eklenirken hata: {e}")


async def verify_migration(session: AsyncSession):
    """Migration'ın başarılı olduğunu doğrular."""
    print("🔍 Migration doğrulanıyor...")
    
    # Yeni tabloları kontrol et
    new_tables = ["weight_validations", "sport_profiles", "trend_analyses", "notification_preferences", "data_backups"]
    
    for table_name in new_tables:
        if await check_table_exists(session, table_name):
            # Tablo yapısını kontrol et
            result = await session.execute(text(f"PRAGMA table_info({table_name})"))
            columns = result.fetchall()
            print(f"✅ {table_name} tablosu doğrulandı ({len(columns)} kolon)")
        else:
            print(f"❌ {table_name} tablosu bulunamadı!")
            return False
    
    # Mevcut tabloların yeni kolonlarını kontrol et
    user_profile_new_columns = ["is_athlete", "preferred_measurement_time", "data_retention_days", "privacy_level"]
    measurements_new_columns = ["is_validated", "validation_notes", "measurement_method", "confidence_score"]
    
    for column in user_profile_new_columns:
        if await check_column_exists(session, "user_profile", column):
            print(f"✅ user_profile.{column} kolonu doğrulandı")
        else:
            print(f"❌ user_profile.{column} kolonu bulunamadı!")
            return False
    
    for column in measurements_new_columns:
        if await check_column_exists(session, "measurements", column):
            print(f"✅ measurements.{column} kolonu doğrulandı")
        else:
            print(f"❌ measurements.{column} kolonu bulunamadı!")
            return False
    
    print("✅ Tüm migration işlemleri başarıyla doğrulandı!")
    return True


async def main():
    """Ana migration fonksiyonu."""
    print("🚀 Fitness Kalori Takip İyileştirme Migration Başlıyor...")
    print(f"📅 Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    try:
        async with AsyncSessionLocal() as session:
            # 1. Yeni tabloları oluştur
            await create_new_tables(session)
            
            # 2. Mevcut tabloları güncelle
            await update_existing_tables(session)
            
            # 3. İndeksleri oluştur
            await create_indexes(session)
            
            # 4. Varsayılan verileri ekle
            await insert_default_data(session)
            
            # 5. Değişiklikleri kaydet
            await session.commit()
            
            # 6. Migration'ı doğrula
            success = await verify_migration(session)
            
            if success:
                print("-" * 60)
                print("🎉 Migration başarıyla tamamlandı!")
                print("✅ Tüm yeni tablolar ve kolonlar eklendi")
                print("✅ İndeksler oluşturuldu")
                print("✅ Varsayılan veriler eklendi")
                print("✅ Backward compatibility korundu")
            else:
                print("-" * 60)
                print("❌ Migration sırasında hatalar oluştu!")
                return 1
                
    except Exception as e:
        print(f"❌ Migration sırasında kritik hata: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)