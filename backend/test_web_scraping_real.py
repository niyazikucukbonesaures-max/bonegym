#!/usr/bin/env python3
"""
Gerçek Web Scraping Test - Yerel DB'de olmayan besinler
"""

import asyncio
import logging
from app.ai_service import LocalAIModel

logging.basicConfig(level=logging.INFO)

async def test_web_scraping():
    """Web scraping'i gerçek besinlerle test et."""
    
    print("🕷️ Web Scraping Test - Yerel DB'de Olmayan Besinler")
    print("=" * 60)
    
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    # Yerel DB'de OLMAYAN besinler
    test_foods = [
        "baklava",           # Türk tatlısı - yerel DB'de yok
        "künefe",            # Türk tatlısı - yerel DB'de yok  
        "sütlaç",            # Türk tatlısı - yerel DB'de yok
        "pizza margherita",  # İtalyan yemeği - yerel DB'de yok
        "hamburger",         # Fast food - yerel DB'de yok
        "çiğ köfte"          # Türk yemeği - yerel DB'de yok
    ]
    
    for food_name in test_foods:
        print(f"\n🔍 Test: '{food_name}'")
        print("-" * 40)
        
        try:
            # Önce yerel DB'de var mı kontrol et
            local_result = ai_model._search_local_database(food_name)
            
            if local_result:
                print(f"⚠️  Yerel DB'de bulundu: {local_result['name']}")
                print("   → Web scraping'e gitmeyecek!")
                continue
            else:
                print("✅ Yerel DB'de YOK - Web scraping'e gidecek")
            
            # Tam AI response'u test et
            start_time = asyncio.get_event_loop().time()
            
            response = await ai_model.generate_response(f"{food_name} besin değerleri")
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            print(f"⏱️  Süre: {duration:.2f} saniye")
            
            # Kaynak kontrolü
            if "Diyetkolik" in response:
                print("🕷️ ✅ Diyetkolik'ten çekildi!")
            elif "Beslenme.gov.tr" in response:
                print("🏛️ ✅ Beslenme.gov.tr'den çekildi!")
            elif "Yerel Veritabanı" in response:
                print("📚 Yerel veritabanından geldi")
            elif "Web Araması" in response:
                print("🌐 Web API'lerinden geldi")
            else:
                print("❓ Kaynak belirsiz")
            
            # Yanıtın ilk 200 karakterini göster
            clean_response = response.split('<!--')[0].strip()
            print(f"📝 Yanıt: {clean_response[:200]}...")
            
        except Exception as e:
            print(f"❌ HATA: {e}")
    
    # Cleanup
    if hasattr(ai_model, 'web_searcher'):
        await ai_model.web_searcher.close_session()
    if hasattr(ai_model, 'web_scraper') and ai_model.web_scraper:
        await ai_model.web_scraper.cleanup()
    
    print("\n✅ Test tamamlandı!")

if __name__ == "__main__":
    asyncio.run(test_web_scraping())