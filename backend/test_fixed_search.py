#!/usr/bin/env python3
"""
Düzeltilmiş Arama Algoritması Test
"""

import asyncio
import logging
from app.ai_service import LocalAIModel

logging.basicConfig(level=logging.INFO)

async def test_search_algorithm():
    """Arama algoritmasını test et."""
    
    print("🔍 Düzeltilmiş Arama Algoritması Test")
    print("=" * 50)
    
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    # Test sorguları
    test_cases = [
        ("tavuk pilav kaç kalori", "Tavuklu Pilav"),
        ("tavuklu pilav besin değerleri", "Tavuklu Pilav"),
        ("tavuk göğsü protein", "Tavuk Göğsü"),
        ("pilav kalori", "Pirinç Pilavı"),
        ("mercimek çorbası", "Mercimek Çorbası")
    ]
    
    for query, expected in test_cases:
        print(f"\n🔍 Test: '{query}'")
        print(f"🎯 Beklenen: {expected}")
        
        try:
            # Besin adını çıkar
            food_name = ai_model._extract_food_name(query.lower())
            print(f"📝 Çıkarılan: '{food_name}'")
            
            # Yerel DB'de ara
            result = ai_model._search_local_database(food_name)
            
            if result:
                found_name = result['name']
                print(f"✅ Bulundu: {found_name}")
                
                if expected in found_name:
                    print("🎉 DOĞRU EŞLEŞME!")
                else:
                    print(f"❌ YANLIŞ EŞLEŞME! Beklenen: {expected}")
            else:
                print("❌ BULUNAMADI")
                
        except Exception as e:
            print(f"❌ HATA: {e}")
    
    print("\n✅ Test tamamlandı!")

if __name__ == "__main__":
    asyncio.run(test_search_algorithm())