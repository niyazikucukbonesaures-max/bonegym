"""
AI Response Parser
AI yanıtlarından besin değerlerini çıkaran parser servisi.
"""

import json
import re
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NutritionData:
    """Besin değerleri veri yapısı."""
    food_name: str
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    confidence: str  # 'high' | 'medium' | 'low'
    
    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye dönüştürür."""
        return {
            "food_name": self.food_name,
            "calories_per_100g": self.calories_per_100g,
            "protein_per_100g": self.protein_per_100g,
            "carbs_per_100g": self.carbs_per_100g,
            "fat_per_100g": self.fat_per_100g,
            "confidence": self.confidence
        }


class AIResponseParser:
    """AI yanıtlarından besin değerlerini çıkaran parser."""
    
    @staticmethod
    def extract_nutrition_data(ai_response: str) -> Optional[NutritionData]:
        """
        AI yanıtından besin değerlerini çıkarır.
        
        Args:
            ai_response: AI'dan gelen yanıt metni
            
        Returns:
            NutritionData: Çıkarılan besin değerleri veya None
        """
        try:
            # Önce yapılandırılmış JSON verisi ara
            structured_data = AIResponseParser._extract_structured_json(ai_response)
            if structured_data:
                return structured_data
            
            # JSON bulunamazsa metin analizi yap
            text_data = AIResponseParser._extract_from_text(ai_response)
            if text_data:
                return text_data
            
            logger.info("AI yanıtında besin değeri bulunamadı")
            return None
            
        except Exception as e:
            logger.error(f"Besin değeri çıkarma hatası: {e}")
            return None
    
    @staticmethod
    def _extract_structured_json(response: str) -> Optional[NutritionData]:
        """
        Yapılandırılmış JSON verisi çıkarır.
        
        Args:
            response: AI yanıtı
            
        Returns:
            NutritionData: Çıkarılan veriler veya None
        """
        try:
            # **NUTRITION_DATA_START** ve **NUTRITION_DATA_END** arasındaki JSON'u ara
            pattern = r'\*\*NUTRITION_DATA_START\*\*(.*?)\*\*NUTRITION_DATA_END\*\*'
            match = re.search(pattern, response, re.DOTALL)
            
            if match:
                json_str = match.group(1).strip()
                data = json.loads(json_str)
                
                # Gerekli alanları kontrol et
                required_fields = ['food_name', 'calories_per_100g', 'protein_per_100g', 
                                 'carbs_per_100g', 'fat_per_100g']
                
                if all(field in data for field in required_fields):
                    nutrition_data = NutritionData(
                        food_name=data['food_name'],
                        calories_per_100g=float(data['calories_per_100g']),
                        protein_per_100g=float(data['protein_per_100g']),
                        carbs_per_100g=float(data['carbs_per_100g']),
                        fat_per_100g=float(data['fat_per_100g']),
                        confidence=data.get('confidence', 'medium')
                    )
                    
                    # Değerleri doğrula
                    if AIResponseParser._validate_nutrition_values(nutrition_data):
                        return nutrition_data
            
            return None
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.debug(f"Yapılandırılmış JSON çıkarma hatası: {e}")
            return None
    
    @staticmethod
    def _extract_from_text(response: str) -> Optional[NutritionData]:
        """
        Serbest metinden besin değerlerini çıkarır.
        
        Args:
            response: AI yanıtı
            
        Returns:
            NutritionData: Çıkarılan veriler veya None
        """
        try:
            # Besin adını çıkar
            food_name = AIResponseParser._extract_food_name(response)
            if not food_name:
                return None
            
            # Sayısal değerleri çıkar
            calories = AIResponseParser._extract_number(response, ['kalori', 'kcal', 'cal'])
            protein = AIResponseParser._extract_number(response, ['protein'])
            carbs = AIResponseParser._extract_number(response, ['karbonhidrat', 'karb'])
            fat = AIResponseParser._extract_number(response, ['yağ', 'fat'])
            
            # En az kalori değeri bulunmalı
            if calories is None:
                return None
            
            # Eksik değerler için varsayılan değerler
            protein = protein if protein is not None else 0.0
            carbs = carbs if carbs is not None else 0.0
            fat = fat if fat is not None else 0.0
            
            nutrition_data = NutritionData(
                food_name=food_name,
                calories_per_100g=calories,
                protein_per_100g=protein,
                carbs_per_100g=carbs,
                fat_per_100g=fat,
                confidence='low'  # Metin analizinden çıkarılan veriler düşük güvenilirlik
            )
            
            # Değerleri doğrula
            if AIResponseParser._validate_nutrition_values(nutrition_data):
                return nutrition_data
            
            return None
            
        except Exception as e:
            logger.debug(f"Metin analizi hatası: {e}")
            return None
    
    @staticmethod
    def _extract_food_name(text: str) -> Optional[str]:
        """Metinden besin adını çıkarır."""
        # Yaygın kalıpları ara
        patterns = [
            r'(\w+(?:\s+\w+)*)\s+için\s+besin',
            r'(\w+(?:\s+\w+)*)\s+besin\s+değerleri',
            r'(\w+(?:\s+\w+)*)\s+100\s+gram',
            r'(\w+(?:\s+\w+)*)\s+kalori'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    @staticmethod
    def _extract_number(text: str, keywords: list) -> Optional[float]:
        """Belirli anahtar kelimeler için sayısal değer çıkarır."""
        for keyword in keywords:
            # Sayı + anahtar kelime kalıbı
            patterns = [
                rf'(\d+(?:\.\d+)?)\s*(?:g|gram|kcal|cal)?\s*{keyword}',
                rf'{keyword}[:\s]*(\d+(?:\.\d+)?)',
                rf'(\d+(?:\.\d+)?)\s*{keyword}'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        continue
        
        return None
    
    @staticmethod
    def _validate_nutrition_values(nutrition_data: NutritionData) -> bool:
        """
        Besin değerlerinin makul aralıkta olup olmadığını kontrol eder.
        
        Args:
            nutrition_data: Doğrulanacak besin değerleri
            
        Returns:
            bool: Değerler geçerli ise True
        """
        try:
            # Kalori kontrolü (0-900 kcal per 100g)
            if not (0 <= nutrition_data.calories_per_100g <= 900):
                logger.warning(f"Geçersiz kalori değeri: {nutrition_data.calories_per_100g}")
                return False
            
            # Makronutrient kontrolü (0-100g per 100g)
            macros = [
                nutrition_data.protein_per_100g,
                nutrition_data.carbs_per_100g,
                nutrition_data.fat_per_100g
            ]
            
            for macro in macros:
                if not (0 <= macro <= 100):
                    logger.warning(f"Geçersiz makronutrient değeri: {macro}")
                    return False
            
            # Güven seviyesi kontrolü
            if nutrition_data.confidence not in ['high', 'medium', 'low']:
                logger.warning(f"Geçersiz güven seviyesi: {nutrition_data.confidence}")
                return False
            
            return True
            
        except (TypeError, ValueError) as e:
            logger.warning(f"Değer doğrulama hatası: {e}")
            return False
    
    @staticmethod
    def create_fallback_response(original_response: str, food_query: str) -> str:
        """
        Parse edilemeyen yanıtlar için fallback mesajı oluşturur.
        
        Args:
            original_response: Orijinal AI yanıtı
            food_query: Kullanıcının sorgusu
            
        Returns:
            str: Fallback mesajı
        """
        return f"""
AI Asistanı Yanıtı:

{original_response}

---

ℹ️ **Not:** Bu yanıt yapılandırılmış besin değeri formatında değil. Yukarıdaki bilgileri manuel olarak değerlendirmeniz gerekebilir.

Daha kesin besin değerleri için sorgunuzu şu şekilde yeniden deneyebilirsiniz:
• "{food_query} besin değerleri nedir?"
• "{food_query} 100 gramında kaç kalori var?"
        """.strip()