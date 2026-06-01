#!/usr/bin/env python3
"""
Köfte test - basit
"""

import asyncio
import sys
import os

# Backend dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_service import LocalAIModel

async def test_kofte():
    """Köfte test et."""
    
    print("🔧 Köfte Test Başlatılıyor...")
    
    # AI Model'i başlat
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    # Köfte test
    extracted_name = ai_model._extract_food_name("köfte besin değerleri")
    print(f"📝 Çıkarılan besin adı: '{extracted_name}'")
    
    local_result = ai_model._search_local_database(extracted_name)
    if local_result:
        print(f"✅ YEREL DB'DE VAR: {local_result['food_name']} - {local_result['calories_per_100g']} kcal")
    else:
        print("❌ Yerel DB'de YOK")
    
    # Tam AI response test
    response = await ai_model.generate_response("köfte besin değerleri")
    print(f"📝 Response: {response[:150]}...")
    
    # Cleanup
    if hasattr(ai_model, 'web_searcher'):
        await ai_model.web_searcher.close_session()
    if hasattr(ai_model, 'web_scraper') and ai_model.web_scraper:
        await ai_model.web_scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(test_kofte())