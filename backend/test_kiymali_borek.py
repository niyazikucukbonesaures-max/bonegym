#!/usr/bin/env python3
"""
Kıymalı Börek Test
"""

import asyncio
import sys
import os

# Backend dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_service import LocalAIModel

async def test_kiymali_borek():
    """Kıymalı börek test et."""
    
    print("🔧 Kıymalı Börek Test Başlatılıyor...")
    
    # AI Model'i başlat
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    # Test sorguları
    test_queries = [
        "kıymalı börek",
        "kıymalı börek besin değerleri",
        "kıymalı börek kaç kalori",
        "kiymali borek",
        "börek kıymalı"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Test: '{query}'")
        print("-" * 50)
        
        # 1. Besin adı çıkarma
        extracted_name = ai_model._extract_food_name(query)
        print(f"📝 Çıkarılan besin adı: '{extracted_name}'")
        
        # 2. Yerel DB kontrolü
        local_result = ai_model._search_local_database(extracted_name)
        if local_result:
            print(f"✅ YEREL DB'DE VAR: {local_result['food_name']}")
        else:
            print("❌ Yerel DB'de YOK")
        
        # 3. Tam AI response test
        try:
            response = await ai_model.generate_response(query)
            
            # Kaynak analizi
            if "Yerel Veritabanı" in response:
                print("✅ BAŞARILI: Yerel DB'den geldi!")
            elif "USDA" in response:
                print("✅ BAŞARILI: USDA'dan geldi!")
            elif "OpenFoodFacts" in response:
                print("✅ BAŞARILI: OpenFoodFacts'ten geldi!")
            elif "Web Scraping" in response:
                print("✅ BAŞARILI: Web scraping'den geldi!")
            elif "bulamadım" in response.lower():
                print("❌ BAŞARISIZ: Bulunamadı mesajı!")
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
    asyncio.run(test_kiymali_borek())