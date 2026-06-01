# Akıllı Besin Arama Sistemi
# Piyasa lideri seviyesinde arama algoritması

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Arama sonucu veri yapısı."""
    food_name: str
    confidence: float
    source: str
    nutrition_data: Dict[str, Any]
    match_type: str

class SmartFoodSearcher:
    """
    Gelişmiş besin arama sistemi.
    MyFitnessPal seviyesinde akıllı arama.
    """
    
    def __init__(self):
        # Türk mutfağı özel terimleri
        self.turkish_food_patterns = {
            "börek_types": {
                "kıymalı": ["meat", "minced", "ground beef"],
                "peynirli": ["cheese", "feta", "white cheese"],
                "ıspanaklı": ["spinach", "spinach leaves"],
                "patatesli": ["potato", "potatoes"],
                "su böreği": ["layered", "water borek"]
            },
            "kebab_types": {
                "adana": ["spicy", "hot", "chili"],
                "urfa": ["mild", "medium spice"],
                "şiş": ["skewer", "grilled"],
                "döner": ["rotating", "shawarma"]
            },
            "cooking_methods": {
                "ızgara": ["grilled", "barbecue", "bbq"],
                "haşlanmış": ["boiled", "steamed"],
                "kızartma": ["fried", "deep fried"],
                "fırın": ["baked", "oven"],
                "tandır": ["clay oven", "traditional oven"]
            },
            "portion_sizes": {
                "büyük": ["large", "big", "xl"],
                "orta": ["medium", "regular"],
                "küçük": ["small", "mini"],
                "tek kişilik": ["single serving", "individual"]
            }
        }
        
        # Yaygın yazım hataları ve varyasyonları
        self.common_variations = {
            "börek": ["borek", "burek", "böreği", "boreği"],
            "döner": ["doner", "dönerci", "donerci"],
            "köfte": ["kofte", "köftesi", "koftesi"],
            "ıspanak": ["ispanak", "ıspanağı", "ispanağı"],
            "kıymalı": ["kiymali", "kıyma", "kiyma"],
            "peynirli": ["peynirli", "peynir", "peyniri"]
        }
    
    def smart_search(self, query: str) -> List[SearchResult]:
        """
        Akıllı arama algoritması.
        
        Args:
            query: Kullanıcı sorgusu
            
        Returns:
            Sıralanmış arama sonuçları
        """
        # 1. Sorguyu temizle ve analiz et
        cleaned_query = self._clean_query(query)
        search_terms = self._extract_search_terms(cleaned_query)
        
        # 2. Çoklu arama stratejisi
        results = []
        
        # Tam eşleşme arama
        exact_results = self._exact_match_search(search_terms)
        results.extend(exact_results)
        
        # Fuzzy arama
        fuzzy_results = self._fuzzy_search(search_terms)
        results.extend(fuzzy_results)
        
        # Malzeme bazlı arama
        ingredient_results = self._ingredient_based_search(search_terms)
        results.extend(ingredient_results)
        
        # Kategori bazlı arama
        category_results = self._category_search(search_terms)
        results.extend(category_results)
        
        # 3. Sonuçları skorla ve sırala
        scored_results = self._score_and_rank(results, query)
        
        return scored_results[:10]  # En iyi 10 sonuç
    
    def _clean_query(self, query: str) -> str:
        """Sorguyu temizle."""
        # Gereksiz kelimeleri kaldır
        stop_words = [
            "kaç", "kalori", "besin", "değerleri", "nedir", "hakkında",
            "için", "gram", "100", "başına", "içeriği", "miktarı"
        ]
        
        cleaned = query.lower()
        for word in stop_words:
            cleaned = re.sub(rf'\b{word}\b', '', cleaned)
        
        # Fazla boşlukları temizle
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _extract_search_terms(self, query: str) -> Dict[str, Any]:
        """Sorgudan arama terimlerini çıkar."""
        terms = {
            "main_food": None,
            "cooking_method": None,
            "portion_size": None,
            "ingredients": [],
            "modifiers": []
        }
        
        words = query.split()
        
        # Ana yemek türünü bul
        for food_type in ["börek", "kebap", "köfte", "pilav", "çorba"]:
            if food_type in query:
                terms["main_food"] = food_type
                break
        
        # Pişirme yöntemini bul
        for method, variations in self.turkish_food_patterns["cooking_methods"].items():
            if method in query or any(var in query for var in variations):
                terms["cooking_method"] = method
                break
        
        # Porsiyon boyutunu bul
        for size, variations in self.turkish_food_patterns["portion_sizes"].items():
            if size in query or any(var in query for var in variations):
                terms["portion_size"] = size
                break
        
        # Malzemeleri bul
        if "kıymalı" in query or "kıyma" in query:
            terms["ingredients"].append("meat")
        if "peynirli" in query or "peynir" in query:
            terms["ingredients"].append("cheese")
        if "ıspanaklı" in query or "ıspanak" in query:
            terms["ingredients"].append("spinach")
        
        return terms
    
    def _exact_match_search(self, terms: Dict[str, Any]) -> List[SearchResult]:
        """Tam eşleşme araması."""
        # Bu kısım gerçek veritabanı sorguları ile implement edilecek
        results = []
        # Placeholder implementation
        return results
    
    def _fuzzy_search(self, terms: Dict[str, Any]) -> List[SearchResult]:
        """Benzer eşleşme araması."""
        results = []
        # Levenshtein distance kullanarak benzer isimleri bul
        # Placeholder implementation
        return results
    
    def _ingredient_based_search(self, terms: Dict[str, Any]) -> List[SearchResult]:
        """Malzeme bazlı arama."""
        results = []
        # Malzemelere göre yemekleri bul
        # Placeholder implementation
        return results
    
    def _category_search(self, terms: Dict[str, Any]) -> List[SearchResult]:
        """Kategori bazlı arama."""
        results = []
        # Yemek kategorilerine göre ara
        # Placeholder implementation
        return results
    
    def _score_and_rank(self, results: List[SearchResult], original_query: str) -> List[SearchResult]:
        """Sonuçları skorla ve sırala."""
        # Skorlama algoritması
        for result in results:
            score = 0.0
            
            # Tam eşleşme bonusu
            if original_query.lower() in result.food_name.lower():
                score += 50
            
            # Kelime eşleşme bonusu
            query_words = set(original_query.lower().split())
            food_words = set(result.food_name.lower().split())
            common_words = query_words.intersection(food_words)
            score += len(common_words) * 10
            
            # Kaynak güvenilirlik bonusu
            source_scores = {
                "USDA": 20,
                "OpenFoodFacts": 15,
                "Local Database": 10,
                "Web Scraping": 5
            }
            score += source_scores.get(result.source, 0)
            
            # Confidence bonusu
            score += result.confidence * 10
            
            result.confidence = score
        
        # Skorlara göre sırala
        return sorted(results, key=lambda x: x.confidence, reverse=True)

# Global instance
smart_searcher = SmartFoodSearcher()