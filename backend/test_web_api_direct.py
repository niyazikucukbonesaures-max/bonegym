#!/usr/bin/env python3
"""
Direkt Web API Test
"""

import asyncio
import sys
import os

# Backend dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_service import WebNutritionSearcher

async def test_web_api_direct():
    """Web API'lerini direkt test et."""
    
    print("🔧 Direkt Web API Test Başlatılıyor...")
    
    # Web searcher'ı başlat
    web_searcher = WebNutritionSearcher()
    
    # Test besinleri
    test_foods = ["salmon", "tuna", "cod", "chicken breast", "beef", "pork"]
    
    for food_name in test_foods:
        print(f"\n🔍 Test: '{food_name}'")
        print("-" * 40)
        
        try:
            # Direkt web API araması
            result = await web_searcher.search_nutrition_data(food_name)
            
            if result:
                print(f"✅ BAŞARILI: {result['source']}")
                print(f"📊 {result['food_name']}: {result['calories_per_100g']} kcal")
                print(f"💪 Protein: {result['protein_per_100g']}g")
            else:
                print("❌ BAŞARISIZ: Hiçbir API'de bulunamadı")
            
        except Exception as e:
            print(f"❌ HATA: {e}")
    
    # Cleanup
    await web_searcher.close_session()
    
    print("\n🔧 Test tamamlandı!")

if __name__ == "__main__":
    asyncio.run(test_web_api_direct())