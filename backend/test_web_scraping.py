#!/usr/bin/env python3
"""
Web Scraping Engine Test Script
Diyetkolik.com ve diğer Türk besin sitelerinden veri çekme testi
"""

import asyncio
import logging
from app.web_scraping_engine import WebScrapingEngine

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_web_scraping():
    """Web scraping engine'i test et."""
    
    # Test besinleri
    test_foods = [
        "tavuk göğsü",
        "pirinç pilavı", 
        "mercimek çorbası",
        "döner kebap",
        "baklava",
        "köfte"
    ]
    
    engine = WebScrapingEngine()
    
    print("🕷️ Web Scraping Engine Test Başlatılıyor...")
    print("=" * 60)
    
    for food_name in test_foods:
        print(f"\n🔍 Test ediliyor: {food_name}")
        print("-" * 40)
        
        try:
            result = await engine.search_food(food_name)
            
            if result:
                print(f"✅ BULUNDU!")
                print(f"📝 Besin Adı: {result.food_name}")
                print(f"🔥 Kalori: {result.calories_per_100g} kcal/100g")
                print(f"💪 Protein: {result.protein_per_100g} g/100g")
                print(f"🍞 Karbonhidrat: {result.carbs_per_100g} g/100g")
                print(f"🥑 Yağ: {result.fat_per_100g} g/100g")
                print(f"📊 Güven: {result.confidence}")
                print(f"📍 Kaynak: {result.source}")
                print(f"🔗 URL: {result.source_url}")
            else:
                print(f"❌ BULUNAMADI")
                
        except Exception as e:
            print(f"❌ HATA: {e}")
    
    # Cleanup
    await engine.cleanup()
    print("\n🧹 Test tamamlandı, kaynaklar temizlendi.")

if __name__ == "__main__":
    asyncio.run(test_web_scraping())