#!/usr/bin/env python3
"""
Badem sorgusu testi
"""

import asyncio
import aiohttp
import json


async def test_badem_queries():
    """Badem ile ilgili farklı soruları test et."""
    
    print("🥜 Badem Sorgu Testleri")
    print("=" * 30)
    
    test_queries = [
        "badem kaç kalori?",
        "badem besin değerleri",
        "100 gram badem",
        "bademler protein",
        "bademi kalorisi nedir?",
        "elma kaç kalori?",
        "ceviz besin değerleri",
        "fındık protein miktarı"
    ]
    
    session_id = f"badem-test-{int(asyncio.get_event_loop().time())}"
    
    async with aiohttp.ClientSession() as session:
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {query}")
            print("-" * 25)
            
            chat_url = "http://localhost:8000/api/ai-assistant/chat"
            chat_data = {
                "message": query,
                "session_id": session_id,
                "user_id": 1
            }
            
            try:
                async with session.post(chat_url, json=chat_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        print(f"✅ Yanıt alındı")
                        
                        if result.get("nutrition_data"):
                            nutrition = result["nutrition_data"]
                            print(f"🥗 Besin: {nutrition['food_name']}")
                            print(f"🔥 Kalori: {nutrition['calories_per_100g']} kcal")
                            print(f"💪 Protein: {nutrition['protein_per_100g']} g")
                            print(f"🥑 Yağ: {nutrition['fat_per_100g']} g")
                            print(f"📊 Güven: {nutrition['confidence']}")
                        else:
                            print("ℹ️  Yapılandırılmış besin verisi bulunamadı")
                            print(f"💬 Yanıt: {result['response'][:100]}...")
                        
                    else:
                        print(f"❌ HTTP Hatası: {response.status}")
                        
            except Exception as e:
                print(f"❌ Bağlantı hatası: {e}")
            
            await asyncio.sleep(0.3)


if __name__ == "__main__":
    asyncio.run(test_badem_queries())