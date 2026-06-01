#!/usr/bin/env python3
"""
Kullanıcı Akışı Demo - AI Besin Asistanı'nda web scraping nasıl çalışır
"""

import asyncio
import json
from datetime import datetime

# Simüle edilmiş kullanıcı sorgusu
async def simulate_user_query():
    """Kullanıcı 'baklava besin değerleri' sorusunu soruyor."""
    
    print("👤 Kullanıcı: 'baklava besin değerleri'")
    print("=" * 50)
    
    # 1. AI Service sorguyu alır
    print("🤖 AI Service: Sorgu işleniyor...")
    
    # 2. Besin adını çıkarır
    food_name = "baklava"
    print(f"📝 Çıkarılan besin adı: {food_name}")
    
    # 3. Arama sırası başlar
    print("\n🔍 Arama Sırası:")
    print("   1️⃣ Yerel veritabanı kontrol ediliyor...")
    print("   ❌ Yerel veritabanında 'baklava' bulunamadı")
    
    print("   2️⃣ Web API'leri kontrol ediliyor...")
    print("   ❌ USDA/OpenFoodFacts'te 'baklava' bulunamadı")
    
    print("   3️⃣ Web Scraping başlatılıyor...")
    
    # 4. Web Scraping süreci
    await simulate_web_scraping(food_name)

async def simulate_web_scraping(food_name):
    """Web scraping sürecini simüle et."""
    
    print(f"\n🕷️ Web Scraping: {food_name}")
    print("-" * 30)
    
    # Diyetkolik scraping
    print("🔍 Diyetkolik.com'da aranıyor...")
    await asyncio.sleep(1)  # Rate limiting simülasyonu
    
    print("   📄 Arama sayfası: https://www.diyetkolik.com/besin-degerleri?q=baklava")
    print("   🎯 3 sonuç bulundu")
    print("   📋 En iyi eşleşme: 'Baklava (Fıstıklı)'")
    
    print("   📄 Detay sayfası çekiliyor...")
    await asyncio.sleep(1)
    
    # Simüle edilmiş scraping sonucu
    scraping_result = {
        "food_name": "Baklava (Fıstıklı)",
        "calories_per_100g": 417,
        "protein_per_100g": 9.1,
        "carbs_per_100g": 63.0,
        "fat_per_100g": 16.9,
        "confidence": "medium",
        "source": "Diyetkolik.com",
        "source_url": "https://www.diyetkolik.com/besin-degerleri/baklava-fistikli"
    }
    
    print("   ✅ Besin değerleri çıkarıldı!")
    print(f"   📊 Kalori: {scraping_result['calories_per_100g']} kcal")
    print(f"   📊 Protein: {scraping_result['protein_per_100g']} g")
    
    # 5. AI Response oluştur
    await simulate_ai_response(scraping_result)

async def simulate_ai_response(nutrition_data):
    """AI yanıtı oluşturma sürecini simüle et."""
    
    print(f"\n🤖 AI Response Oluşturuluyor...")
    print("-" * 30)
    
    # Türkçe yanıt formatla
    ai_response = f"""🔍 **{nutrition_data['food_name']}** için besin değerleri:

🔥 **Kalori**: {nutrition_data['calories_per_100g']} kcal (100g başına)
💪 **Protein**: {nutrition_data['protein_per_100g']} g
🍞 **Karbonhidrat**: {nutrition_data['carbs_per_100g']} g  
🥑 **Yağ**: {nutrition_data['fat_per_100g']} g

📍 **Kaynak**: {nutrition_data['source']}

Bu değerler 100 gram ürün için geçerlidir. Tükettiğiniz miktara göre hesaplama yapabilirsiniz.

<!--BESIN_DEĞERLERI_JSON:{{
    "food_name": "{nutrition_data['food_name']}",
    "calories_per_100g": {nutrition_data['calories_per_100g']},
    "protein_per_100g": {nutrition_data['protein_per_100g']},
    "carbs_per_100g": {nutrition_data['carbs_per_100g']},
    "fat_per_100g": {nutrition_data['fat_per_100g']},
    "confidence": "{nutrition_data['confidence']}",
    "source": "{nutrition_data['source']}"
}}-->"""

    print("📝 Oluşturulan AI Yanıtı:")
    print(ai_response)
    
    # 6. Frontend'e gönder
    await simulate_frontend_display(nutrition_data, ai_response)

async def simulate_frontend_display(nutrition_data, ai_response):
    """Frontend'te nasıl gösterileceğini simüle et."""
    
    print(f"\n💻 Frontend Display")
    print("-" * 30)
    
    # Chat mesajı
    chat_message = {
        "id": f"assistant-{int(datetime.now().timestamp())}",
        "type": "assistant",
        "content": ai_response.split("<!--")[0].strip(),  # JSON kısmını çıkar
        "timestamp": datetime.now().isoformat(),
        "nutrition_data": {
            "food_name": nutrition_data['food_name'],
            "calories_per_100g": nutrition_data['calories_per_100g'],
            "protein_per_100g": nutrition_data['protein_per_100g'],
            "carbs_per_100g": nutrition_data['carbs_per_100g'],
            "fat_per_100g": nutrition_data['fat_per_100g'],
            "confidence": nutrition_data['confidence'],
            "source": nutrition_data['source']
        }
    }
    
    print("📱 Chat Arayüzünde Görünen:")
    print(f"   🤖 AI Besin Asistanı")
    print(f"   💬 {chat_message['content']}")
    
    print("\n🎴 Nutrition Card Bileşeni:")
    print(f"   📝 {nutrition_data['food_name']}")
    print(f"   🔥 Kalori: {nutrition_data['calories_per_100g']}")
    print(f"   💪 Protein: {nutrition_data['protein_per_100g']}g")
    print(f"   🍞 Karbonhidrat: {nutrition_data['carbs_per_100g']}g")
    print(f"   🥑 Yağ: {nutrition_data['fat_per_100g']}g")
    print(f"   📊 Güven: {get_confidence_text(nutrition_data['confidence'])}")
    print(f"   [➕ Kalori Günlüğüne Ekle] ← Buton")

def get_confidence_text(confidence):
    """Güven seviyesini Türkçe'ye çevir."""
    confidence_map = {
        'high': 'Yüksek Güven',
        'medium': 'Orta Güven', 
        'low': 'Düşük Güven'
    }
    return confidence_map.get(confidence, 'Bilinmiyor')

async def simulate_add_to_log():
    """Kalori günlüğüne ekleme sürecini simüle et."""
    
    print(f"\n➕ Kullanıcı 'Kalori Günlüğüne Ekle' butonuna tıkladı")
    print("-" * 40)
    
    print("📝 Food Log API'sine gönderilen veri:")
    log_entry = {
        "user_id": 1,
        "food_name": "Baklava (Fıstıklı)",
        "grams": 100,
        "meal_type": "ara"
    }
    print(json.dumps(log_entry, indent=2, ensure_ascii=False))
    
    print("✅ Kalori günlüğüne eklendi!")
    print("🔄 Kullanıcı food-log sayfasına yönlendiriliyor...")

async def main():
    """Ana demo akışı."""
    
    print("🎭 AI Besin Asistanı - Kullanıcı Akışı Demo")
    print("=" * 60)
    
    # Tam kullanıcı akışını simüle et
    await simulate_user_query()
    
    print("\n" + "=" * 60)
    await simulate_add_to_log()
    
    print(f"\n✨ Demo Tamamlandı!")
    print("\n💡 Önemli Noktalar:")
    print("   🔍 Otomatik fallback: Yerel DB → API → Scraping")
    print("   📊 Güven skoru ile kaynak güvenilirliği")
    print("   🎴 Structured data ile UI bileşenleri")
    print("   ➕ Tek tıkla kalori günlüğüne ekleme")
    print("   🔄 Seamless user experience")

if __name__ == "__main__":
    asyncio.run(main())