#!/usr/bin/env python3
"""
Web Öncelik Test - Yerel DB vs Web karşılaştırması
"""

import asyncio
import sys
import os

# Backend dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_service import LocalAIModel

async def test_web_priority():
    """Web öncelik sistemini test et."""
    
    print("🔧 Web Öncelik Test Başlatılıyor...")
    
    # AI Model'i başlat
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    # Test sorguları - yerel DB'de kısmi eşleşme olan ama web'de daha iyi olabilecek
    test_queries = [
        "kiymali borek",      # Yerel: Su Böreği, Web: daha iyi eşleşme olabilir
        "börek kıymalı",      # Yerel: Su Böreği, Web: daha iyi eşleşme olabilir
        "salmon fish",        # Yerel: Levrek Balığı, Web: Salmon olabilir
        "tuna fish",          # Yerel: Levrek Balığı, Web: Tuna olabilir
        "chicken breast",     # Yerel: Tavuk Göğsü, Web: daha spesifik olabilir
        "greek yogurt",       # Yerel: Süzme Yoğurt, Web: Greek Yogurt olabilir
    ]
    
    for query in test_queries:
        print(f"\n🔍 Test: '{query}'")
        print("-" * 50)
        
        try:
            response = await ai_model.generate_response(f"{query} besin değerleri")
            
            # Kaynak analizi
            if "Yerel Veritabanı" in response:
                print("📚 YEREL DB'den geldi")
            elif "USDA" in response:
                print("🌐 USDA'dan geldi (WEB)")
            elif "OpenFoodFacts" in response:
                print("🌐 OpenFoodFacts'ten geldi (WEB)")
            elif "Web Scraping" in response and "Mock" not in response:
                print("🕷️ Gerçek web scraping'den geldi (WEB)")
            elif "Mock" in response or "Tahmini" in response:
                print("🎭 Mock/tahmini veri (FALLBACK)")
            else:
                print("❓ Belirsiz kaynak")
            
            # Besin adını çıkar
            import re
            name_match = re.search(r'\*\*(.*?)\*\*', response)
            if name_match:
                food_name = name_match.group(1)
                print(f"🍽️ Bulunan besin: {food_name}")
            
            # Kalori değerini çıkar
            calorie_match = re.search(r'(\d+(?:\.\d+)?)\s*kcal', response)
            if calorie_match:
                calories = calorie_match.group(1)
                print(f"📊 Kalori: {calories} kcal")
            
        except Exception as e:
            print(f"❌ HATA: {e}")
    
    # Cleanup
    if hasattr(ai_model, 'web_searcher'):
        await ai_model.web_searcher.close_session()
    if hasattr(ai_model, 'web_scraper') and ai_model.web_scraper:
        await ai_model.web_scraper.cleanup()
    
    print("\n🔧 Test tamamlandı!")

if __name__ == "__main__":
    asyncio.run(test_web_priority())