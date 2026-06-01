#!/usr/bin/env python3
"""
Türkçe Besin Adları Test
"""

import asyncio
import sys
import os

# Backend dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_service import LocalAIModel

async def test_turkish_foods():
    """Türkçe besin adlarını test et."""
    
    print("🔧 Türkçe Besin Adları Test Başlatılıyor...")
    
    # AI Model'i başlat
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    # Türkçe besin adları - yerel DB'de olmayanlar
    test_foods = [
        "ıstakoz",           # İngilizce: lobster
        "karides",           # İngilizce: shrimp
        "yengeç",            # İngilizce: crab
        "somon",             # İngilizce: salmon
        "ton balığı",        # İngilizce: tuna
        "morina",            # İngilizce: cod
        "kuzu eti",          # İngilizce: lamb
        "geyik eti",         # İngilizce: venison
        "ördek eti",         # İngilizce: duck
        "patlıcan",          # İngilizce: eggplant
        "karnabahar",        # İngilizce: cauliflower
        "kuşkonmaz",         # İngilizce: asparagus
        "şeftali",           # İngilizce: peach
        "kayısı",            # İngilizce: apricot
        "nar"                # İngilizce: pomegranate
    ]
    
    for food_name in test_foods:
        print(f"\n🔍 Test: '{food_name}'")
        print("-" * 50)
        
        # Yerel DB kontrolü
        extracted_name = ai_model._extract_food_name(f"{food_name} besin değerleri")
        local_result = ai_model._search_local_database(extracted_name)
        
        if local_result:
            print(f"⚠️  YEREL DB'DE VAR: {local_result['food_name']}")
        else:
            print("✅ Yerel DB'de YOK - Web'e gidecek")
        
        try:
            response = await ai_model.generate_response(f"{food_name} besin değerleri")
            
            # Kaynak analizi
            if "Yerel Veritabanı" in response:
                print("📚 YEREL DB'den geldi")
            elif "USDA" in response:
                print("🌐 USDA'dan geldi (WEB)")
            elif "OpenFoodFacts" in response:
                print("🌐 OpenFoodFacts'ten geldi (WEB)")
            elif "Web Scraping" in response and "Mock" not in response:
                print("🕷️ Gerçek web scraping'den geldi (WEB)")
            elif "Mock" in response or "Tahmini" in response or "Fallback" in response:
                print("🎭 Mock/fallback veri")
            elif "bulamadım" in response.lower():
                print("❌ Bulunamadı mesajı")
            else:
                print("❓ Belirsiz kaynak")
            
            # Besin adını çıkar
            import re
            name_match = re.search(r'\*\*(.*?)\*\*', response)
            if name_match:
                found_name = name_match.group(1)
                print(f"🍽️ Bulunan besin: {found_name}")
            
            # Kalori değerini çıkar
            calorie_match = re.search(r'(\d+(?:\.\d+)?)\s*kcal', response)
            if calorie_match:
                calories = calorie_match.group(1)
                print(f"📊 Kalori: {calories} kcal")
            
        except Exception as e:
            print(f"❌ HATA: {e}")
    
    # Cleanup
    if hasattr(ai_model, 'web_searcher'):
        await ai_model.web_searcher.close_session()
    if hasattr(ai_model, 'web_scraper') and ai_model.web_scraper:
        await ai_model.web_scraper.cleanup()
    
    print("\n🔧 Test tamamlandı!")

if __name__ == "__main__":
    asyncio.run(test_turkish_foods())