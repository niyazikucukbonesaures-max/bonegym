#!/usr/bin/env python3
"""
Direkt Web Scraping Test
"""

import asyncio
import sys
import os

# Backend dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_service import LocalAIModel

async def test_web_scraping():
    """Web scraping'i direkt test et."""
    
    print("🔧 Direkt Web Scraping Test Başlatılıyor...")
    
    # AI Model'i başlat
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    # Yerel DB'de olmayan besinleri test et
    test_foods = ["künefe", "pizza", "hamburger", "sushi"]
    
    for food_name in test_foods:
        print(f"\n🔍 Test: '{food_name}'")
        print("-" * 30)
        
        # 1. Yerel DB kontrolü
        extracted_name = ai_model._extract_food_name(f"{food_name} besin değerleri")
        local_result = ai_model._search_local_database(extracted_name)
        
        if local_result:
            print(f"⚠️  YEREL DB'DE VAR: {local_result['food_name']}")
            continue
        else:
            print("✅ Yerel DB'de YOK - Web scraping'e gidecek")
        
        # 2. Tam AI response test
        try:
            response = await ai_model.generate_response(f"{food_name} besin değerleri")
            
            # Kaynak analizi
            if "Yerel Veritabanı" in response:
                print("❌ SORUN: Yerel DB'den geldi!")
            elif "Web Scraping" in response or "Mock" in response:
                print("✅ BAŞARILI: Web scraping'den geldi!")
            elif "OpenFoodFacts" in response or "USDA" in response:
                print("✅ BAŞARILI: Web API'den geldi!")
            else:
                print("❓ Belirsiz kaynak")
            
            # Response'un ilk kısmını göster
            clean_response = response.split('<!--')[0].strip()[:200]
            print(f"📝 Response: {clean_response}...")
            
        except Exception as e:
            print(f"❌ HATA: {e}")
    
    # Cleanup
    if hasattr(ai_model, 'web_searcher'):
        await ai_model.web_searcher.close_session()
    if hasattr(ai_model, 'web_scraper') and ai_model.web_scraper:
        await ai_model.web_scraper.cleanup()
    
    print("\n🔧 Test tamamlandı!")

if __name__ == "__main__":
    asyncio.run(test_web_scraping())