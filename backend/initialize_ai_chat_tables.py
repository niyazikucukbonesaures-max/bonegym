#!/usr/bin/env python3
"""
AI Chat Tables Initialization Script
AI Besin Asistanı için gerekli tabloları oluşturur.
"""

import asyncio
import sqlite3
from pathlib import Path

from app.database import engine
from app.models import Base


async def create_ai_chat_tables():
    """AI chat tablolarını oluşturur."""
    
    # SQLAlchemy ile tabloları oluştur
    async with engine.begin() as conn:
        # AI chat tablolarını oluştur
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ AI chat tabloları başarıyla oluşturuldu!")
    
    # Manuel SQL ile constraint'leri kontrol et
    db_path = Path("fitness.db")
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabloların varlığını kontrol et
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('ai_chat_sessions', 'ai_chat_messages', 'ai_generated_foods')
        """)
        tables = cursor.fetchall()
        
        print(f"📋 Oluşturulan AI chat tabloları: {[t[0] for t in tables]}")
        
        # İndeksleri oluştur (performans için)
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_chat_messages_session_id ON ai_chat_messages(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_chat_messages_timestamp ON ai_chat_messages(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_chat_sessions_user_id ON ai_chat_sessions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_chat_sessions_last_activity ON ai_chat_sessions(last_activity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_generated_foods_session_id ON ai_generated_foods(session_id)")
            
            conn.commit()
            print("📊 AI chat indeksleri oluşturuldu!")
            
        except sqlite3.Error as e:
            print(f"⚠️ İndeks oluşturma hatası: {e}")
        
        finally:
            conn.close()


if __name__ == "__main__":
    asyncio.run(create_ai_chat_tables())