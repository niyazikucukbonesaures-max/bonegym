#!/usr/bin/env python3
"""
Her Zaman Cevap Test - Rastgele besinler
"""

import asyncio
import sys
import os

# Backend dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_service import LocalAIModel

async def test_always_answer():
    """Her zaman cevap verme test et."""
    
    print("🔧 Her Zaman Cevap Test Başlatılıyor...")
    
    # AI Model'i başlat
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    # Rastgele/bilinmeyen besinleri test et
    test_foods = [
        "xyz123 besin",  # Tamamen rastgele
        "alien food",    # İngilizce rastgele
        "martian pizza", # Karışık rastgele
        "unicorn meat",  # Fantastik
        "dragon egg",    # Fantastik
        "quantum soup",  # Bilimkurgu
        "hologram cake", # Teknolojik
        "virtual bread", # Sanal
        "cyber chicken",  # Siber
        "nano rice"      # Nano
    ]
    
    for food_name in test_foods:
        print(f"\n🔍 Test: '{food_name}'")
        print("-" * 40)
        
        try:
            response = await ai_model.generate_response(f"{food_name} besin değerleri")
            
            # Cevap analizi
            if "bulamadım" in response.lower() or "bulunamadı" in response.lower():
                print("❌ BAŞARISIZ: 'Bulunamadı' mesajı verdi!")
            elif "kalori" in response.lower() and "protein" in response.lower():
                print("✅ BAŞARILI: Besin değerleri verdi!")
            else:
                print("❓ Belirsiz cevap")
            
            # Response'un ilk kısmını göster
            clean_response = response.split('<!--')[0].strip()[:150]
            print(f"📝 Response: {clean_response}...")
            
        except Exception as e:
            print(f"❌ HATA: {e}")
    
    # Cleanup
    if hasattr(ai_model, 'web_searcher'):
        await ai_model.web_searcher.close_session()
    if hasattr(ai_model, 'web_scraper') and ai_model.web_scraper:
        await ai_model.web_scraper.cleanup()
    
    print("\n🔧 Test tamamlandı!")

if __name__ == "__main__":
    asyncio.run(test_always_answer())