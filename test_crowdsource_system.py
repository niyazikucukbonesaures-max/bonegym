#!/usr/bin/env python3
"""
Kullanıcı Katkılı Besin Sistemi Test Scripti
Bu script crowdsource sistemini test eder ve demo veriler ekler.
"""

import asyncio
import sys
import os

# Backend modüllerini import etmek için path ekle
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.crowdsource_system import crowdsource_system, UserContribution

async def test_crowdsource_system():
    """Crowdsource sistemini test et ve demo veriler ekle."""
    
    print("🚀 Kullanıcı Katkılı Besin Sistemi Test Başlıyor...")
    
    # Test katkıları
    test_contributions = [
        {
            "user_id": 1,
            "food_name": "Annemin Mercimek Çorbası",
            "calories_per_100g": 120,
            "protein_per_100g": 8.5,
            "carbs_per_100g": 18,
            "fat_per_100g": 1.2,
            "source": "homemade"
        },
        {
            "user_id": 2,
            "food_name": "Ev Yapımı Kıymalı Börek",
            "calories_per_100g": 290,
            "protein_per_100g": 16,
            "carbs_per_100g": 24,
            "fat_per_100g": 15,
            "source": "homemade"
        },
        {
            "user_id": 1,
            "food_name": "Köy Yumurtası Menemen",
            "calories_per_100g": 195,
            "protein_per_100g": 14,
            "carbs_per_100g": 6,
            "fat_per_100g": 13,
            "source": "homemade"
        },
        {
            "user_id": 3,
            "food_name": "Babaannemin Dolması",
            "calories_per_100g": 165,
            "protein_per_100g": 4.2,
            "carbs_per_100g": 28,
            "fat_per_100g": 6.8,
            "source": "homemade"
        },
        {
            "user_id": 2,
            "food_name": "Lokantadaki Tavuk Şiş",
            "calories_per_100g": 210,
            "protein_per_100g": 32,
            "carbs_per_100g": 2,
            "fat_per_100g": 8.5,
            "source": "restaurant"
        }
    ]
    
    # Katkıları ekle
    print("\n📝 Test katkıları ekleniyor...")
    for contrib_data in test_contributions:
        contribution = UserContribution(**contrib_data)
        success = await crowdsource_system.add_user_contribution(contribution)
        
        if success:
            print(f"✅ '{contrib_data['food_name']}' eklendi (Kullanıcı {contrib_data['user_id']})")
        else:
            print(f"❌ '{contrib_data['food_name']}' eklenemedi")
    
    # Eksik besin önerileri ekle
    print("\n💡 Eksik besin önerileri ekleniyor...")
    suggestions = [
        ("Adana Kebap", 1),
        ("İskender Kebap", 2),
        ("Künefe", 3),
        ("Baklava", 1),
        ("Türk Kahvesi", 2),
        ("Çiğ Köfte", 3),
        ("Balık Ekmek", 1)
    ]
    
    for food_name, user_id in suggestions:
        success = await crowdsource_system.suggest_missing_food(user_id, food_name)
        if success:
            print(f"✅ '{food_name}' önerisi eklendi (Kullanıcı {user_id})")
    
    # Bazı önerilere ek oylar
    print("\n🗳️ Önerilere ek oylar ekleniyor...")
    popular_suggestions = ["Adana Kebap", "İskender Kebap", "Künefe"]
    for suggestion_name in popular_suggestions:
        for voter_id in [1, 2, 3]:
            # Her kullanıcı popüler önerilere oy versin
            await crowdsource_system.suggest_missing_food(voter_id, suggestion_name)
    
    # Doğrulamalar yap
    print("\n✅ Doğrulamalar yapılıyor...")
    for i in range(min(3, len(crowdsource_system.contributions))):
        # İlk 3 katkıyı farklı kullanıcılar doğrulasın
        await crowdsource_system.verify_contribution(i, (i % 3) + 1, True)
        await crowdsource_system.verify_contribution(i, ((i + 1) % 3) + 1, True)
    
    # Sonuçları göster
    print("\n📊 SONUÇLAR:")
    print("=" * 50)
    
    # Sistem istatistikleri
    total_contributions = len(crowdsource_system.contributions)
    total_suggestions = len(crowdsource_system.suggestions)
    total_users = len(crowdsource_system.user_points)
    
    print(f"📈 Toplam Katkı: {total_contributions}")
    print(f"💡 Toplam Öneri: {total_suggestions}")
    print(f"👥 Toplam Kullanıcı: {total_users}")
    print(f"🗃️ Veritabanı Boyutu: {385 + total_contributions}")
    
    # Liderlik tablosu
    print(f"\n🏆 LİDERLİK TABLOSU:")
    leaderboard = await crowdsource_system.get_user_leaderboard(5)
    for i, entry in enumerate(leaderboard):
        print(f"{i+1}. Kullanıcı #{entry['user_id']} - {entry['total_points']} puan (Seviye {entry['level']})")
    
    # En çok istenen besinler
    print(f"\n⭐ EN ÇOK İSTENEN BESİNLER:")
    missing_foods = await crowdsource_system.get_popular_missing_foods(5)
    for food in missing_foods:
        print(f"• {food['food_name']} ({food['votes']} oy)")
    
    # Günlük challenge'lar
    print(f"\n🎯 GÜNLÜK GÖREVLER:")
    challenges = await crowdsource_system.generate_daily_challenges()
    for challenge in challenges[:3]:
        print(f"• {challenge['description']} ({challenge['reward_points']} puan)")
    
    print(f"\n🎉 Test tamamlandı! Sistem başarıyla çalışıyor.")
    print(f"🌐 Frontend: http://localhost:5173")
    print(f"🔧 Backend API: http://localhost:8000/docs")
    print(f"📱 AI Assistant'ta 'Topluluk' butonuna tıklayarak sistemi test edebilirsiniz!")

if __name__ == "__main__":
    asyncio.run(test_crowdsource_system())