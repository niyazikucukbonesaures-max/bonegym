#!/usr/bin/env python3
"""
Kıymalı Börek Debug
"""

import asyncio
import sys
import os

# Backend dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_service import LocalAIModel

async def debug_kiymali_borek():
    """Kıymalı börek debug et."""
    
    print("🔧 Kıymalı Börek Debug Başlatılıyor...")
    
    # AI Model'i başlat
    ai_model = LocalAIModel()
    await ai_model.initialize()
    
    # Problem sorguları
    problem_queries = ["kiymali borek", "börek kıymalı"]
    
    for query in problem_queries:
        print(f"\n🔍 Debug: '{query}'")
        print("-" * 50)
        
        # 1. Besin adı çıkarma
        extracted_name = ai_model._extract_food_name(f"{query} besin değerleri")
        print(f"📝 Çıkarılan besin adı: '{extracted_name}'")
        
        # 2. Manuel arama algoritması debug
        food_database = {
            "kıymalı börek": {
                "name": "Kıymalı Börek",
                "calories": 280,
                "protein": 15.0,
                "carbs": 25.0,
                "fat": 14.0
            },
            "börek": {
                "name": "Su Böreği", 
                "calories": 195,
                "protein": 8.0,
                "carbs": 20.0,
                "fat": 9.0
            }
        }
        
        query_lower = extracted_name.lower()
        print(f"🔍 Query lower: '{query_lower}'")
        
        # Tam eşleşme test
        found_exact = None
        for food_key, food_data in food_database.items():
            if food_key == query_lower:
                found_exact = food_data
                print(f"✅ TAM EŞLEŞME: {food_key} = {query_lower}")
                break
        
        if not found_exact:
            print("❌ TAM EŞLEŞME YOK")
            
            # Kısmi eşleşme test
            found_partial = None
            for food_key, food_data in food_database.items():
                if query_lower in food_key or food_key in query_lower:
                    found_partial = food_data
                    print(f"⚠️  KISMI EŞLEŞME: {food_key} <-> {query_lower}")
                    break
            
            if not found_partial:
                print("❌ KISMI EŞLEŞME YOK")
                
                # Eş anlamlı test
                synonyms = {
                    "kıymalı börek": ["kıymalı börek", "kiymali borek", "börek kıymalı", "kıymalı", "meat börek"]
                }
                
                found_synonym = None
                for food_key, variations in synonyms.items():
                    for variation in variations:
                        if variation in query_lower:
                            if food_key in food_database:
                                found_synonym = food_database[food_key]
                                print(f"✅ EŞ ANLAMLI EŞLEŞME: {variation} -> {food_key}")
                                break
                    if found_synonym:
                        break
                
                if not found_synonym:
                    print("❌ EŞ ANLAMLI EŞLEŞME YOK")
        
        # 3. Gerçek arama sonucu
        real_result = ai_model._search_local_database(extracted_name)
        if real_result:
            print(f"🎯 GERÇEK SONUÇ: {real_result['food_name']}")
        else:
            print("🎯 GERÇEK SONUÇ: Bulunamadı")

if __name__ == "__main__":
    asyncio.run(debug_kiymali_borek())