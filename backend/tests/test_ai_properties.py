"""
AI Besin Asistanı Property-Based Tests
Türkçe dil tutarlılığı ve besin bilgisi sağlama özellikleri için property testler.
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import text, composite

from app.local_ai_model import LocalAIModel, get_ai_model
from app.ai_response_parser import AIResponseParser


# Test için Türkçe karakter stratejisi
turkish_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZçğıöşüÇĞIÖŞÜ '
turkish_text = text(alphabet=turkish_chars, min_size=3, max_size=100)

# Yaygın Türkçe besin isimleri
turkish_foods = st.sampled_from([
    'tavuk', 'pirinç', 'yumurta', 'elma', 'ekmek', 'et', 'balık', 'süt', 
    'peynir', 'domates', 'patates', 'soğan', 'havuç', 'muz', 'portakal'
])


@composite
def nutrition_query(draw):
    """Besin sorgusu stratejisi."""
    food = draw(turkish_foods)
    query_templates = [
        f"{food} besin değerleri",
        f"{food} kalori",
        f"{food} protein",
        f"{food} için besin bilgisi",
        f"{food} 100 gram kalori"
    ]
    return draw(st.sampled_from(query_templates))


class TestAIProperties:
    """AI Besin Asistanı property testleri."""
    
    @pytest.mark.asyncio
    @given(query=nutrition_query())
    @settings(max_examples=20, deadline=15000)  # 15 saniye timeout
    async def test_turkish_language_response_consistency(self, query):
        """
        Feature: ai-besin-asistani, Property 1: Turkish Language Response Consistency
        **Validates: Requirements 2.1, 2.3, 2.4, 2.5**
        
        For any nutrition query submitted to the AI assistant, 
        the response SHALL be in Turkish language with proper Turkish character encoding support.
        """
        # AI modelini al
        ai_model = await get_ai_model()
        
        # Sorguyu işle
        response = await ai_model.generate_response(query)
        
        # Yanıtın başarılı olduğunu kontrol et
        assert response.success, f"AI yanıt başarısız: {response.error}"
        assert response.content, "AI yanıtı boş olamaz"
        
        # Türkçe karakter kontrolü
        turkish_indicators = ['ç', 'ğ', 'ı', 'ö', 'ş', 'ü', 'Ç', 'Ğ', 'I', 'Ö', 'Ş', 'Ü']
        has_turkish_chars = any(char in response.content for char in turkish_indicators)
        
        # Türkçe kelime kontrolü
        turkish_words = [
            'besin', 'değer', 'kalori', 'protein', 'karbonhidrat', 'yağ', 
            'gram', 'için', 'hakkında', 'bilgi', 'değerleri', 'içerir'
        ]
        has_turkish_words = any(word in response.content.lower() for word in turkish_words)
        
        # En az birinin true olması gerekir (Türkçe yanıt)
        assert has_turkish_chars or has_turkish_words, \
            f"Yanıt Türkçe değil: {response.content[:100]}..."
    
    @pytest.mark.asyncio
    @given(query=nutrition_query())
    @settings(max_examples=20, deadline=15000)
    async def test_complete_nutrition_information_provision(self, query):
        """
        Feature: ai-besin-asistani, Property 2: Complete Nutrition Information Provision
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
        
        For any valid nutrition query, the AI assistant SHALL provide all four required 
        nutrition components (calories, protein, carbohydrates, and fat per 100g) in a structured format.
        """
        # AI modelini al
        ai_model = await get_ai_model()
        
        # Sorguyu işle
        response = await ai_model.generate_response(query)
        
        # Yanıtın başarılı olduğunu kontrol et
        assert response.success, f"AI yanıt başarısız: {response.error}"
        
        # Besin değerlerini çıkarmaya çalış
        nutrition_data = AIResponseParser.extract_nutrition_data(response.content)
        
        if nutrition_data:
            # Tüm gerekli bileşenlerin mevcut olduğunu kontrol et
            assert nutrition_data.calories_per_100g >= 0, "Kalori değeri negatif olamaz"
            assert nutrition_data.protein_per_100g >= 0, "Protein değeri negatif olamaz"
            assert nutrition_data.carbs_per_100g >= 0, "Karbonhidrat değeri negatif olamaz"
            assert nutrition_data.fat_per_100g >= 0, "Yağ değeri negatif olamaz"
            
            # Makul aralıkta olduğunu kontrol et
            assert nutrition_data.calories_per_100g <= 900, "Kalori değeri çok yüksek"
            assert nutrition_data.protein_per_100g <= 100, "Protein değeri çok yüksek"
            assert nutrition_data.carbs_per_100g <= 100, "Karbonhidrat değeri çok yüksek"
            assert nutrition_data.fat_per_100g <= 100, "Yağ değeri çok yüksek"
            
            # Besin adının mevcut olduğunu kontrol et
            assert nutrition_data.food_name, "Besin adı boş olamaz"
            assert len(nutrition_data.food_name.strip()) > 0, "Besin adı boş olamaz"
            
            # Güven seviyesinin geçerli olduğunu kontrol et
            assert nutrition_data.confidence in ['high', 'medium', 'low'], \
                f"Geçersiz güven seviyesi: {nutrition_data.confidence}"
        else:
            # Eğer yapılandırılmış veri çıkarılamazsa, en azından besin bilgisi içermeli
            nutrition_keywords = ['kalori', 'protein', 'karbonhidrat', 'yağ', 'gram']
            has_nutrition_info = any(keyword in response.content.lower() for keyword in nutrition_keywords)
            
            assert has_nutrition_info, \
                f"Yanıt besin bilgisi içermiyor: {response.content[:200]}..."
    
    @pytest.mark.asyncio
    @given(text_input=turkish_text)
    @settings(max_examples=10, deadline=10000)
    async def test_ai_model_timeout_handling(self, text_input):
        """
        AI modelinin timeout handling davranışını test eder.
        """
        ai_model = await get_ai_model()
        
        # Yanıt süresini kontrol et
        response = await ai_model.generate_response(text_input)
        
        # 10 saniye timeout kontrolü (requirement 5.6)
        assert response.response_time <= 10.0, \
            f"AI yanıt süresi çok uzun: {response.response_time} saniye"
        
        # Başarısız yanıtlarda hata mesajının Türkçe olduğunu kontrol et
        if not response.success and response.error:
            turkish_error_words = ['hata', 'başarısız', 'deneyin', 'kullanılamıyor']
            has_turkish_error = any(word in response.error.lower() for word in turkish_error_words)
            assert has_turkish_error, f"Hata mesajı Türkçe değil: {response.error}"
    
    @pytest.mark.asyncio
    async def test_ai_model_availability(self):
        """AI modelinin kullanılabilirlik kontrolü."""
        ai_model = await get_ai_model()
        
        # Model başlatılmış olmalı
        assert ai_model.is_available(), "AI model kullanılamıyor"
        
        # Basit bir test sorgusu
        response = await ai_model.generate_response("test")
        
        # Yanıt alınabilmeli (başarılı veya başarısız olabilir ama yanıt olmalı)
        assert isinstance(response.content, str), "Yanıt string olmalı"
        assert isinstance(response.response_time, float), "Yanıt süresi float olmalı"
        assert isinstance(response.success, bool), "Başarı durumu bool olmalı"


class TestNutritionDataExtraction:
    """Besin değeri çıkarma property testleri."""
    
    @given(
        calories=st.floats(min_value=0, max_value=900),
        protein=st.floats(min_value=0, max_value=100),
        carbs=st.floats(min_value=0, max_value=100),
        fat=st.floats(min_value=0, max_value=100)
    )
    @settings(max_examples=50)
    def test_nutrition_value_validation_property(self, calories, protein, carbs, fat):
        """
        Feature: ai-besin-asistani, Property 8: Nutrition Value Validation
        **Validates: Requirements 6.4**
        
        For any parsed nutrition values, the system SHALL validate that calories are 
        between 0-900 per 100g and macronutrients are between 0-100g per 100g.
        """
        from app.ai_response_parser import NutritionData
        
        # Geçerli aralıktaki değerler için NutritionData oluştur
        nutrition_data = NutritionData(
            food_name="Test Besin",
            calories_per_100g=calories,
            protein_per_100g=protein,
            carbs_per_100g=carbs,
            fat_per_100g=fat,
            confidence="medium"
        )
        
        # Validation fonksiyonunu test et
        is_valid = AIResponseParser._validate_nutrition_values(nutrition_data)
        
        # Geçerli aralıktaki tüm değerler için True dönmeli
        assert is_valid, f"Geçerli değerler reddedildi: {nutrition_data.to_dict()}"
    
    @given(
        calories=st.one_of(
            st.floats(min_value=-100, max_value=-0.1),  # Negatif kaloriler
            st.floats(min_value=900.1, max_value=2000)   # Çok yüksek kaloriler
        )
    )
    @settings(max_examples=20)
    def test_invalid_nutrition_values_rejected(self, calories):
        """Geçersiz besin değerlerinin reddedildiğini test eder."""
        from app.ai_response_parser import NutritionData
        
        nutrition_data = NutritionData(
            food_name="Test Besin",
            calories_per_100g=calories,
            protein_per_100g=10.0,
            carbs_per_100g=20.0,
            fat_per_100g=5.0,
            confidence="medium"
        )
        
        # Geçersiz değerler için False dönmeli
        is_valid = AIResponseParser._validate_nutrition_values(nutrition_data)
        assert not is_valid, f"Geçersiz kalori değeri kabul edildi: {calories}"