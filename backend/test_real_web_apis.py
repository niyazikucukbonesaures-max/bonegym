#!/usr/bin/env python3
"""
Gerçek Web API Test - Doğru eşleştirme
"""

import asyncio
import sys
import os

# Backend dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_service import LocalAIModel

async def test_real_web_apis():
    """Gerçek web API'lerini test et."""
    
    print("🔧 Gerçek Web API Test Başlatılıyor...")
    
    # AI Model'i başlat
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    # Gerçek besinleri test et - yerel DB'de olmayanlar
    test_foods = [
        "apple",         # İngilizce meyve
        "banana",        # İngilizce meyve
        "broccoli",      # İngilizce sebze
        "salmon",        # İngilizce balık
        "quinoa",        # Süper gıda
        "avocado",       # Meyve
        "spinach",       # Sebze
        "almonds",       # Kuruyemiş
        "oats",          # Tahıl
        "greek yogurt"   # Süt ürünü
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
        
        try:
            response = await ai_model.generate_response(f"{food_name} besin değerleri")
            
            # Kaynak analizi
            if "USDA" in response:
                print("✅ BAŞARILI: USDA'dan geldi!")
            elif "OpenFoodFacts" in response:
                print("✅ BAŞARILI: OpenFoodFacts'ten geldi!")
            elif "Web Scraping" in response and "Mock" not in response:
                print("✅ BAŞARILI: Gerçek web scraping'den geldi!")
            elif "Mock" in response or "Tahmini" in response:
                print("❌ BAŞARISIZ: Mock/tahmini veri verdi!")
            elif "bulamadım" in response.lower():
                print("❌ BAŞARISIZ: Bulunamadı mesajı verdi!")
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
    asyncio.run(test_real_web_apis())