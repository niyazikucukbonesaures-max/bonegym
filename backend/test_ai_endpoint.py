#!/usr/bin/env python3
"""
AI Assistant Endpoint Test Script
"""

import asyncio
import aiohttp
import json


async def test_ai_chat():
    """AI chat endpoint'ini test et."""
    
    url = "http://localhost:8000/api/ai-assistant/chat"
    
    test_data = {
        "message": "tavuk göğsü besin değerleri nedir?",
        "session_id": "test-session-123",
        "user_id": 1
    }
    
    print("🧪 AI Chat Endpoint Testi")
    print("=" * 40)
    print(f"URL: {url}")
    print(f"Data: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_data) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ Başarılı yanıt:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    
                    # Besin değerleri kontrolü
                    if result.get("nutrition_data"):
                        print("\n🥗 Besin Değerleri Bulundu:")
                        nutrition = result["nutrition_data"]
                        print(f"  - Besin: {nutrition['food_name']}")
                        print(f"  - Kalori: {nutrition['calories_per_100g']} kcal")
                        print(f"  - Protein: {nutrition['protein_per_100g']} g")
                        print(f"  - Karbonhidrat: {nutrition['carbs_per_100g']} g")
                        print(f"  - Yağ: {nutrition['fat_per_100g']} g")
                        print(f"  - Güven: {nutrition['confidence']}")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Hata: {response.status}")
                    print(f"Yanıt: {error_text}")
                    
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")


async def test_session_history():
    """Oturum geçmişi endpoint'ini test et."""
    
    url = "http://localhost:8000/api/ai-assistant/session/test-session-123"
    
    print("\n🧪 Session History Endpoint Testi")
    print("=" * 40)
    print(f"URL: {url}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ Başarılı yanıt:")
                    print(f"Oturum ID: {result['session_id']}")
                    print(f"Mesaj Sayısı: {result['message_count']}")
                    print(f"Mesajlar: {len(result['messages'])} adet")
                    
                    for i, msg in enumerate(result['messages'][-3:], 1):  # Son 3 mesaj
                        print(f"\n  Mesaj {i}:")
                        print(f"    Tip: {msg['type']}")
                        print(f"    İçerik: {msg['content'][:100]}...")
                        if msg.get('nutrition_data'):
                            print(f"    Besin Verisi: ✅")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Hata: {response.status}")
                    print(f"Yanıt: {error_text}")
                    
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")


async def main():
    """Ana test fonksiyonu."""
    
    # İlk olarak chat endpoint'ini test et
    await test_ai_chat()
    
    # Sonra session history'yi test et
    await test_session_history()
    
    print("\n🎉 Test tamamlandı!")


if __name__ == "__main__":
    asyncio.run(main())