#!/usr/bin/env python3
"""
Tavuk Pilav Test - Timeout sorunu çözüldü mü?
"""

import asyncio
import logging
from app.ai_service import LocalAIModel

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def test_tavuk_pilav():
    """Tavuk pilav sorgusunu test et."""
    
    print("🍚 Tavuk Pilav Test Başlatılıyor...")
    print("=" * 50)
    
    # AI Model'i başlat
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    # Test sorguları
    test_queries = [
        "tavuk pilav kaç kalori",
        "tavuklu pilav besin değerleri",
        "tavuk pilav protein miktarı"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Test: '{query}'")
        print("-" * 30)
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # AI yanıtı al
            response = await ai_model.generate_response(query)
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            print(f"✅ BAŞARILI! ({duration:.2f} saniye)")
            print(f"📝 Yanıt:")
            print(response[:200] + "..." if len(response) > 200 else response)
            
        except Exception as e:
            print(f"❌ HATA: {e}")
    
    # Cleanup
    if hasattr(ai_model, 'web_searcher'):
        await ai_model.web_searcher.close_session()
    if hasattr(ai_model, 'web_scraper') and ai_model.web_scraper:
        await ai_model.web_scraper.cleanup()
    
    print("\n✅ Test tamamlandı!")

if __name__ == "__main__":
    asyncio.run(test_tavuk_pilav())