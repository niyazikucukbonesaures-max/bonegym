#!/usr/bin/env python3
"""
Final Sistem Test - Yerel DB'de olmayan gerçek besinler
"""

import asyncio
import sys
import os

# Backend dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_service import LocalAIModel

async def test_final_system():
    """Final sistemi test et."""
    
    print("🔧 Final Sistem Test Başlatılıyor...")
    
    # AI Model'i başlat
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    # Yerel DB'de kesinlikle olmayan besinleri test et
    test_foods = [
        "salmon fish",    # Balık
        "tuna fish",      # Balık
        "cod fish",       # Balık
        "lobster",        # Deniz ürünü
        "shrimp",         # Karides
        "crab",           # Yengeç
        "duck meat",      # Ördek eti
        "lamb chops",     # Kuzu pirzola
        "venison",        # Geyik eti
        "rabbit meat"     # Tavşan eti
    ]
    
    for food_name in test_foods:
        print(f"\n🔍 Test: '{food_name}'")
        print("-" * 40)
        
        # Yerel DB kontrolü
        extracted_name = ai_model._extract_food_name(f"{food_name} besin değerleri")
        local_result = ai_model._search_local_database(extracted_name)
        
        if local_result:
            print(f"⚠️  YEREL DB'DE VAR: {local_result['food_name']}")
            continue
        else:
            print("✅ Yerel DB'de YOK - Web'e gidecek")
        
        try:
            response = await ai_model.generate_response(f"{food_name} besin değerleri")
            
            # Kaynak analizi
            if "USDA" in response:
                print("✅ MÜKEMMEL: USDA'dan gerçek veri!")
            elif "OpenFoodFacts" in response:
                print("✅ İYİ: OpenFoodFacts'ten gerçek veri!")
            elif "Web Scraping" in response and "Fallback" not in response and "Mock" not in response:
                print("✅ İYİ: Gerçek web scraping'den veri!")
            elif "Fallback" in response or "Mock" in response or "Tahmini" in response:
                print("⚠️  ORTA: Fallback/mock veri (gerçek bulunamadı)")
            elif "bulamadım" in response.lower():
                print("❌ KÖTÜ: Bulunamadı mesajı!")
            else:
                print("❓ Belirsiz kaynak")
            
            # Kalori değerini çıkar
            import re
            calorie_match = re.search(r'(\d+(?:\.\d+)?)\s*kcal', response)
            if calorie_match:
                calories = calorie_match.group(1)
                print(f"📊 Kalori: {calories} kcal")
            
            # Response'un ilk kısmını göster
            clean_response = response.split('<!--')[0].strip()[:150]
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
    asyncio.run(test_final_system())