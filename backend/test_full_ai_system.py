#!/usr/bin/env python3
"""
AI Besin Asistanı - Tam Sistem Testi
"""

import asyncio
import aiohttp
import json


async def test_full_ai_workflow():
    """Tam AI workflow'unu test et."""
    
    print("🧪 AI Besin Asistanı - Tam Sistem Testi")
    print("=" * 50)
    
    session_id = f"test-full-{int(asyncio.get_event_loop().time())}"
    
    # Test soruları
    test_questions = [
        "tavuk göğsü besin değerleri nedir?",
        "pirinç pilavı kaç kalori?",
        "mercimek çorbası protein miktarı?",
        "domates besin değerleri",
        "bilinmeyen bir yemek hakkında soru"
    ]
    
    async with aiohttp.ClientSession() as session:
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 Test {i}: {question}")
            print("-" * 30)
            
            # Chat isteği gönder
            chat_url = "http://localhost:8000/api/ai-assistant/chat"
            chat_data = {
                "message": question,
                "session_id": session_id,
                "user_id": 1
            }
            
            try:
                async with session.post(chat_url, json=chat_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        print(f"✅ Yanıt alındı ({len(result['response'])} karakter)")
                        
                        if result.get("nutrition_data"):
                            nutrition = result["nutrition_data"]
                            print(f"🥗 Besin verisi bulundu:")
                            print(f"   - {nutrition['food_name']}")
                            print(f"   - {nutrition['calories_per_100g']} kcal")
                            print(f"   - Güven: {nutrition['confidence']}")
                        else:
                            print("ℹ️  Yapılandırılmış besin verisi yok")
                        
                        if result.get("error"):
                            print(f"⚠️  Hata: {result['error']}")
                            
                    else:
                        print(f"❌ HTTP Hatası: {response.status}")
                        
            except Exception as e:
                print(f"❌ Bağlantı hatası: {e}")
            
            # Kısa bekleme
            await asyncio.sleep(0.5)
        
        # Oturum geçmişini kontrol et
        print(f"\n📚 Oturum Geçmişi Kontrolü")
        print("-" * 30)
        
        history_url = f"http://localhost:8000/api/ai-assistant/session/{session_id}"
        
        try:
            async with session.get(history_url) as response:
                if response.status == 200:
                    history = await response.json()
                    
                    print(f"✅ Oturum bulundu:")
                    print(f"   - Mesaj sayısı: {history['message_count']}")
                    print(f"   - Gerçek mesaj: {len(history['messages'])}")
                    
                    # Son birkaç mesajı göster
                    for msg in history['messages'][-4:]:
                        msg_type = "👤" if msg['type'] == 'user' else "🤖"
                        content_preview = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
                        print(f"   {msg_type} {content_preview}")
                        
                else:
                    print(f"❌ Geçmiş alınamadı: {response.status}")
                    
        except Exception as e:
            print(f"❌ Geçmiş hatası: {e}")
        
        # Oturumu temizle
        print(f"\n🧹 Oturum Temizleme")
        print("-" * 30)
        
        clear_url = f"http://localhost:8000/api/ai-assistant/session/{session_id}"
        
        try:
            async with session.delete(clear_url) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ {result['message']}")
                else:
                    print(f"❌ Temizleme hatası: {response.status}")
                    
        except Exception as e:
            print(f"❌ Temizleme bağlantı hatası: {e}")


async def test_turkish_language():
    """Türkçe dil desteğini test et."""
    
    print(f"\n🇹🇷 Türkçe Dil Desteği Testi")
    print("-" * 30)
    
    turkish_tests = [
        "çiğ köfte besin değerleri",
        "şeker pancarı kaç kalori?",
        "üzüm yaprağı sarması protein",
        "ğ, ı, ş, ç, ö, ü karakterli yemekler"
    ]
    
    session_id = f"turkish-test-{int(asyncio.get_event_loop().time())}"
    
    async with aiohttp.ClientSession() as session:
        for question in turkish_tests:
            print(f"📝 Soru: {question}")
            
            chat_url = "http://localhost:8000/api/ai-assistant/chat"
            chat_data = {
                "message": question,
                "session_id": session_id,
                "user_id": 1
            }
            
            try:
                async with session.post(chat_url, json=chat_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Türkçe karakter kontrolü
                        turkish_chars = ['ç', 'ğ', 'ı', 'ö', 'ş', 'ü', 'Ç', 'Ğ', 'I', 'İ', 'Ö', 'Ş', 'Ü']
                        has_turkish = any(char in result['response'] for char in turkish_chars)
                        
                        print(f"   ✅ Yanıt alındı (Türkçe: {'✓' if has_turkish else '✗'})")
                        
                    else:
                        print(f"   ❌ Hata: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Bağlantı hatası: {e}")


async def main():
    """Ana test fonksiyonu."""
    
    # Tam sistem testi
    await test_full_ai_workflow()
    
    # Türkçe dil testi
    await test_turkish_language()
    
    print(f"\n🎉 Tüm testler tamamlandı!")
    print(f"💡 Web arayüzünü test etmek için: http://localhost:5174/ai-assistant")


if __name__ == "__main__":
    asyncio.run(main())