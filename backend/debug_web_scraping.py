#!/usr/bin/env python3
"""
Web Scraping Debug - Neden çalışmıyor?
"""

import asyncio
import logging
import sys
import os

# Backend dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_service import LocalAIModel

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def debug_web_scraping():
    """Web scraping neden çalışmıyor debug et."""
    
    print("🔧 Web Scraping Debug Başlatılıyor...")
    print("=" * 50)
    
    # AI Model'i başlat
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    print(f"✅ AI Model başlatıldı")
    print(f"🔧 Web scraper var mı: {ai_model.web_scraper is not None}")
    
    # Test besinleri
    test_foods = ["baklava", "künefe", "pizza"]
    
    for food_name in test_foods:
        print(f"\n🔍 Debug Test: '{food_name}'")
        print("-" * 30)
        
        # 1. Besin adı çıkarma
        extracted_name = ai_model._extract_food_name(f"{food_name} besin değerleri")
        print(f"📝 Çıkarılan besin adı: '{extracted_name}'")
        
        # 2. Yerel DB kontrolü
        local_result = ai_model._search_local_database(extracted_name)
        if local_result:
            print(f"⚠️  YEREL DB'DE VAR: {local_result['food_name']}")
            print("   → Bu yüzden web'e gitmiyor!")
            continue
        else:
            print("✅ Yerel DB'de YOK - Web'e gitmeli")
        
        # 3. Tam AI response test
        try:
            print("🤖 AI response test ediliyor...")
            response = await ai_model.generate_response(f"{food_name} besin değerleri")
            
            # Kaynak analizi
            if "Yerel Veritabani" in response:
                print("❌ SORUN: Hala yerel DB'den çekiyor!")
            elif "Diyetkolik" in response:
                print("✅ BAŞARILI: Diyetkolik'ten çekti!")
            elif "Web" in response:
                print("✅ BAŞARILI: Web'den çekti!")
            else:
                print("❓ Belirsiz kaynak")
            
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
    
    print("\n🔧 Debug tamamlandı!")

if __name__ == "__main__":
    asyncio.run(debug_web_scraping())