# Fitness ve Kalori Takip Uygulaması - Veritabanı bağlantısı
# PostgreSQL (Supabase) + SQLite fallback desteği

import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base
from app.models_auth import User, UserSession  # Auth modellerini import et

# .env dosyasını yükle
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

# ---------------------------------------------------------------------------
# Veritabanı URL — PostgreSQL öncelikli, SQLite fallback
# ---------------------------------------------------------------------------

_pg_url = os.getenv("DATABASE_URL")

# Production guard — DATABASE_URL zorunlu
if not _pg_url and os.getenv("ENVIRONMENT") == "production":
    print(
        "HATA: DATABASE_URL ortam değişkeni eksik. Fly.io secrets kontrol edin.\n"
        "  fly secrets set DATABASE_URL='postgresql://...' --app kalorispor-backend",
        file=sys.stderr,
    )
    sys.exit(1)

if _pg_url:
    # PostgreSQL (Supabase) — asyncpg driver
    # postgresql:// → postgresql+asyncpg://
    DATABASE_URL = _pg_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    _IS_POSTGRES = True
else:
    # SQLite fallback (geliştirme ortamı)
    DB_PATH = Path(__file__).parent.parent / "fitness.db"
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
    _IS_POSTGRES = False

# ---------------------------------------------------------------------------
# Async engine
# ---------------------------------------------------------------------------

if _IS_POSTGRES:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )
else:
    from sqlalchemy.pool import NullPool
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=NullPool,
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Veritabanı başlangıç kurulumu
# ---------------------------------------------------------------------------

async def init_db() -> None:
    """Tüm tabloları oluşturur. PostgreSQL ve SQLite için ayrı optimizasyonlar."""
    async with engine.begin() as conn:
        if _IS_POSTGRES:
            # PostgreSQL — sadece tabloları oluştur
            await conn.run_sync(Base.metadata.create_all)

            # PostgreSQL performans indeksleri
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_food_log_user_date ON food_log(user_id, logged_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_measurements_user_date ON measurements(user_id, measured_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_water_logs_user_date ON water_logs(user_id, logged_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_workout_logs_date ON workout_logs(completed_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_creatine_user_date ON creatine_doses(user_id, taken_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_food_items_name ON food_items(name);",
                "CREATE INDEX IF NOT EXISTS idx_ai_chat_sessions_user ON ai_chat_sessions(user_id, last_activity DESC);",
                "CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements(user_id, earned_at DESC);",
            ]
            for idx_sql in indices:
                try:
                    await conn.exec_driver_sql(idx_sql)
                except Exception:
                    pass  # İndeks zaten varsa devam et
        else:
            # SQLite — WAL modu ve optimizasyonlar
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            await conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
            await conn.exec_driver_sql("PRAGMA cache_size=-64000;")
            await conn.exec_driver_sql("PRAGMA temp_store=MEMORY;")
            await conn.exec_driver_sql("PRAGMA mmap_size=268435456;")

            await conn.run_sync(Base.metadata.create_all)

            # FTS5 sanal tablosu (sadece SQLite)
            try:
                await conn.exec_driver_sql(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS food_search "
                    "USING fts5(name, content=food_items, content_rowid=id);"
                )
            except Exception:
                pass

            # SQLite indeksleri
            sqlite_indices = [
                "CREATE INDEX IF NOT EXISTS idx_food_log_user_date ON food_log(user_id, logged_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_measurements_user_date ON measurements(user_id, measured_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_water_logs_user_date ON water_logs(user_id, logged_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_workout_logs_date ON workout_logs(completed_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_creatine_user_date ON creatine_doses(user_id, taken_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_food_items_name ON food_items(name);",
            ]
            for idx_sql in sqlite_indices:
                try:
                    await conn.exec_driver_sql(idx_sql)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Dependency injection için async session generator
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency injection için async veritabanı oturumu sağlar."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
