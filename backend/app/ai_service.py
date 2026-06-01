# AI Besin Asistanı Servisi
# Yerel AI modeli entegrasyonu ve besin değerleri işleme

import asyncio
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
import aiohttp
from urllib.parse import quote

from app.schemas import NutritionData
from app.web_scraping_engine import WebScrapingEngine, get_web_scraping_engine

logger = logging.getLogger(__name__)


class WebNutritionSearcher:
    """
    Web'den besin değerlerini arayan sınıf.
    Güvenilir kaynaklardan besin bilgilerini çeker.
    """
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def get_session(self):
        """HTTP session'ı al veya oluştur."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout
            )
        return self.session
    
    async def close_session(self):
        """HTTP session'ı kapat."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def search_nutrition_data(self, food_name: str) -> Optional[Dict[str, Any]]:
        """
        Web'den besin değerlerini ara.
        
        Args:
            food_name: Aranacak besin adı
            
        Returns:
            Besin değerleri dict'i veya None
        """
        try:
            # Türkçe besin adını İngilizce'ye çevir
            english_terms = self._get_english_translations(food_name)
            
            # Hem Türkçe hem İngilizce terimlerle ara
            search_terms = [food_name] + english_terms
            
            for search_term in search_terms:
                logger.info(f"🔍 Web API'lerinde arıyor: {search_term}")
                
                # Önce USDA FoodData Central'dan ara
                usda_result = await self._search_usda_fooddata(search_term)
                if usda_result:
                    return usda_result
                
                # USDA'da bulunamazsa Türk besin kaynaklarından ara
                turkish_result = await self._search_turkish_sources(search_term)
                if turkish_result:
                    return turkish_result
                
                # Son çare olarak genel web araması yap
                web_result = await self._search_general_web(search_term)
                if web_result:
                    return web_result
            
            return None
            
        except Exception as e:
            logger.error(f"Web besin araması hatası: {e}")
            return None
    
    def _get_english_translations(self, turkish_food: str) -> List[str]:
        """
        Türkçe besin adlarını İngilizce'ye çevir.
        
        Args:
            turkish_food: Türkçe besin adı
            
        Returns:
            İngilizce çeviriler listesi
        """
        turkish_food_lower = turkish_food.lower()
        
        # Kapsamlı Türkçe-İngilizce besin sözlüğü
        translations = {
            # Deniz ürünleri
            "ıstakoz": ["lobster", "crayfish"],
            "karides": ["shrimp", "prawn"],
            "yengeç": ["crab"],
            "midye": ["mussel", "mussels"],
            "istiridye": ["oyster", "oysters"],
            "ahtapot": ["octopus"],
            "kalamar": ["squid", "calamari"],
            
            # Balıklar
            "somon": ["salmon"],
            "ton balığı": ["tuna", "tuna fish"],
            "levrek": ["sea bass", "bass"],
            "çupra": ["sea bream", "bream"],
            "hamsi": ["anchovy", "anchovies"],
            "sardalya": ["sardine", "sardines"],
            "uskumru": ["mackerel"],
            "kalkan": ["turbot"],
            "dil balığı": ["sole", "sole fish"],
            "morina": ["cod", "cod fish"],
            "alabalık": ["trout"],
            
            # Etler
            "kuzu eti": ["lamb", "lamb meat"],
            "dana eti": ["beef", "veal"],
            "domuz eti": ["pork", "pork meat"],
            "geyik eti": ["venison", "deer meat"],
            "tavşan eti": ["rabbit", "rabbit meat"],
            "ördek eti": ["duck", "duck meat"],
            "kaz eti": ["goose", "goose meat"],
            "hindi eti": ["turkey", "turkey meat"],
            "tavuk eti": ["chicken", "chicken meat"],
            "tavuk göğsü": ["chicken breast"],
            "tavuk but": ["chicken thigh", "chicken leg"],
            
            # Sebzeler - TEK KELİME ÖNCE SEBZE OLARAK ARANSIN
            "patlıcan": ["eggplant", "aubergine"],
            "kabak": ["zucchini", "courgette", "squash"],
            "karnabahar": ["cauliflower"],
            "lahana": ["cabbage"],
            "ıspanak": ["spinach", "spinach leaves"],  # Sadece sebze olarak ara
            "roka": ["arugula", "rocket"],
            "maydanoz": ["parsley"],
            "dereotu": ["dill"],
            "fesleğen": ["basil"],
            "kekik": ["thyme"],
            "biberiye": ["rosemary"],
            "nane": ["mint"],
            "semizotu": ["purslane"],
            "turp": ["radish"],
            "şalgam": ["turnip"],
            "pancar": ["beetroot", "beet"],
            "kereviz": ["celery"],
            "enginar": ["artichoke"],
            "kuşkonmaz": ["asparagus"],
            "bamya": ["okra"],
            "fasulye": ["green beans", "beans"],
            "bezelye": ["peas", "green peas"],
            "nohut": ["chickpeas", "garbanzo beans"],
            "mercimek": ["lentils"],
            "börülce": ["black eyed peas"],
            
            # Meyveler
            "şeftali": ["peach"],
            "kayısı": ["apricot"],
            "erik": ["plum"],
            "kiraz": ["cherry", "cherries"],
            "vişne": ["sour cherry"],
            "armut": ["pear"],
            "ayva": ["quince"],
            "nar": ["pomegranate"],
            "incir": ["fig", "figs"],
            "üzüm": ["grapes", "grape"],
            "karpuz": ["watermelon"],
            "kavun": ["melon", "cantaloupe"],
            "mandalina": ["mandarin", "tangerine"],
            "limon": ["lemon"],
            "greyfurt": ["grapefruit"],
            "hurma": ["persimmon", "date"],
            "kuru üzüm": ["raisins"],
            "kuru kayısı": ["dried apricot"],
            "kuru incir": ["dried fig"],
            
            # Kuruyemişler
            "badem": ["almonds", "almond"],
            "ceviz": ["walnuts", "walnut"],
            "fındık": ["hazelnuts", "hazelnut"],
            "antep fıstığı": ["pistachios", "pistachio"],
            "yer fıstığı": ["peanuts", "peanut"],
            "kaju": ["cashews", "cashew"],
            "kestane": ["chestnuts", "chestnut"],
            "çam fıstığı": ["pine nuts"],
            "susam": ["sesame seeds", "sesame"],
            "ayçiçeği çekirdeği": ["sunflower seeds"],
            "kabak çekirdeği": ["pumpkin seeds"],
            
            # Süt ürünleri
            "süt": ["milk"],
            "yoğurt": ["yogurt", "yoghurt"],
            "süzme yoğurt": ["greek yogurt", "strained yogurt"],
            "ayran": ["buttermilk"],
            "kefir": ["kefir"],
            "peynir": ["cheese"],
            "beyaz peynir": ["white cheese", "feta cheese"],
            "kaşar peyniri": ["cheddar cheese", "yellow cheese"],
            "tulum peyniri": ["tulum cheese"],
            "lor peyniri": ["cottage cheese", "ricotta"],
            "krema": ["cream"],
            "tereyağı": ["butter"],
            "margarin": ["margarine"],
            
            # Tahıllar ve baklagiller
            "buğday": ["wheat"],
            "arpa": ["barley"],
            "çavdar": ["rye"],
            "yulaf": ["oats", "oatmeal"],
            "pirinç": ["rice"],
            "bulgur": ["bulgur", "cracked wheat"],
            "kinoa": ["quinoa"],
            "amarant": ["amaranth"],
            "karabuğday": ["buckwheat"],
            "darı": ["millet"],
            
            # Türk mutfağı özel - SADECE ÇOK KELİMELİ OLANLAR
            "döner": ["doner kebab", "shawarma"],
            "şiş kebap": ["shish kebab", "kebab"],
            "adana kebap": ["adana kebab"],
            "köfte": ["meatballs", "kofta"],
            "lahmacun": ["turkish pizza", "lahmacun"],
            "pide": ["turkish pide", "turkish bread"],
            "börek": ["borek", "turkish pastry"],
            "kıymalı börek": ["meat borek", "turkish pastry with meat", "minced meat borek"],
            "peynirli börek": ["cheese borek", "turkish pastry with cheese", "cheese filled borek"],
            "ıspanaklı börek": ["spinach borek", "turkish pastry with spinach", "spinach filled borek"],
            "patatesli börek": ["potato borek", "turkish pastry with potato", "potato filled borek"],
            "su böreği": ["water borek", "layered turkish pastry"],
            "sigara böreği": ["cigarette borek", "rolled turkish pastry"],
            "mantı": ["turkish dumplings", "manti"],
            "dolma": ["stuffed grape leaves", "dolma"],
            "sarma": ["stuffed cabbage", "sarma"],
            "pilav": ["rice pilaf", "pilaf"],
            "bulgur pilavı": ["bulgur pilaf"],
            
            # Tatlılar
            "baklava": ["baklava"],
            "künefe": ["kunefe", "knafeh"],
            "tulumba": ["tulumba dessert"],
            "lokma": ["lokma", "turkish donuts"],
            "revani": ["revani", "semolina cake"],
            "sütlaç": ["rice pudding"],
            "muhallebi": ["milk pudding"],
            "kazandibi": ["kazandibi"],
            "aşure": ["ashure", "noah's pudding"],
            "helva": ["halva", "tahini halva"],
            
            # İçecekler
            "çay": ["tea", "turkish tea"],
            "türk kahvesi": ["turkish coffee"],
            "salep": ["sahlep", "orchid drink"],
            "şerbet": ["sherbet", "syrup drink"],
            "boza": ["boza"],
            "turnip juice": ["şalgam suyu"],
        }
        
        # Çevirileri bul
        english_terms = []
        
        # ÖZEL DURUM: Tek kelimeli sebze/meyve aramaları için önce temel çeviriyi kullan
        single_word_basics = {
            "ıspanak": ["spinach", "spinach leaves"],
            "domates": ["tomato"],
            "salatalık": ["cucumber"],
            "patates": ["potato"],
            "havuç": ["carrot"],
            "soğan": ["onion"],
            "elma": ["apple"],
            "muz": ["banana"],
            "portakal": ["orange"],
            "tavuk": ["chicken"],
            "et": ["beef", "meat"],
            "balık": ["fish"],
            "peynir": ["cheese"],
            "süt": ["milk"],
            "yumurta": ["egg"]
        }
        
        # Eğer tek kelime ve temel besinlerden biriyse, sadece temel çeviriyi kullan
        if len(turkish_food_lower.split()) == 1 and turkish_food_lower in single_word_basics:
            return single_word_basics[turkish_food_lower]
        
        # Tam eşleşme
        if turkish_food_lower in translations:
            english_terms.extend(translations[turkish_food_lower])
        
        # Kısmi eşleşme (sadece çok kelimeli sorgular için)
        if len(turkish_food_lower.split()) > 1:
            for turkish_key, english_list in translations.items():
                if (turkish_key in turkish_food_lower or 
                    turkish_food_lower in turkish_key or
                    any(word in turkish_key for word in turkish_food_lower.split()) or
                    any(word in turkish_food_lower for word in turkish_key.split())):
                    english_terms.extend(english_list)
        
        # Tekrarları kaldır ve ilk 5 terimi al (çok fazla olmasın)
        return list(set(english_terms))[:5]
    
    async def _search_usda_fooddata(self, food_name: str) -> Optional[Dict[str, Any]]:
        """
        USDA FoodData Central API'sinden besin değerlerini ara.
        Bu ücretsiz bir API'dir ve çok kapsamlı.
        """
        try:
            session = await self.get_session()
            
            # USDA FoodData Central API (ücretsiz - API key gerektirmez)
            search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
            
            # Farklı arama terimleri dene
            search_terms = [
                food_name,
                food_name.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ç', 'c').replace('ö', 'o'),  # Türkçe karakterleri İngilizce'ye çevir
                food_name + " raw",
                food_name + " cooked"
            ]
            
            for search_term in search_terms:
                params = {
                    'query': search_term,
                    'pageSize': 10,  # Daha fazla sonuç
                    'dataType': ['Foundation', 'SR Legacy', 'Survey (FNDDS)']
                }
                
                logger.info(f"🔍 USDA'da arıyor: {search_term}")
                
                async with session.get(search_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('foods'):
                            # En iyi eşleşmeyi bul
                            best_food = self._find_best_usda_match(data['foods'], food_name)
                            
                            if best_food:
                                # Besin değerlerini çıkar
                                nutrients = {}
                                for nutrient in best_food.get('foodNutrients', []):
                                    nutrient_id = nutrient.get('nutrientId')
                                    value = nutrient.get('value', 0)
                                    
                                    # Önemli besin değerleri ID'leri
                                    if nutrient_id == 1008:  # Energy (kcal)
                                        nutrients['calories'] = value
                                    elif nutrient_id == 1003:  # Protein
                                        nutrients['protein'] = value
                                    elif nutrient_id == 1005:  # Carbohydrate
                                        nutrients['carbs'] = value
                                    elif nutrient_id == 1004:  # Total lipid (fat)
                                        nutrients['fat'] = value
                                
                                if nutrients.get('calories') is not None and nutrients['calories'] > 0:
                                    logger.info(f"✅ USDA'da bulundu: {best_food.get('description')}")
                                    return {
                                        'food_name': best_food.get('description', food_name),
                                        'calories_per_100g': nutrients.get('calories', 0),
                                        'protein_per_100g': nutrients.get('protein', 0),
                                        'carbs_per_100g': nutrients.get('carbs', 0),
                                        'fat_per_100g': nutrients.get('fat', 0),
                                        'confidence': 'high',
                                        'source': 'USDA FoodData Central'
                                    }
            
        except Exception as e:
            logger.warning(f"USDA API araması başarısız: {e}")
        
        return None
    
    def _find_best_usda_match(self, foods: list, query: str) -> Optional[Dict]:
        """USDA sonuçlarından en iyi eşleşmeyi bul."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        best_match = None
        best_score = 0
        
        for food in foods:
            description = food.get('description', '').lower()
            description_words = set(description.split())
            
            # Skorlama
            score = 0
            
            # Tam eşleşme
            if query_lower in description:
                score += 20
            
            # Kelime eşleşmeleri
            common_words = query_words.intersection(description_words)
            score += len(common_words) * 5
            
            # Başlangıç eşleşmesi
            if description.startswith(query_lower[:4]):
                score += 10
            
            # "Raw" veya "cooked" gibi işlenmemiş halleri tercih et
            if any(word in description for word in ['raw', 'fresh', 'uncooked']):
                score += 3
            
            if score > best_score:
                best_score = score
                best_match = food
        
        return best_match if best_score > 5 else None
    
    async def _search_turkish_sources(self, food_name: str) -> Optional[Dict[str, Any]]:
        """
        Türk besin kaynaklarından ara - Alternatif beslenme API'leri kullan.
        """
        try:
            session = await self.get_session()
            
            # Edamam Food Database API (ücretsiz tier)
            # Bu daha güvenilir bir alternatif
            edamam_result = await self._search_edamam_api(session, food_name)
            if edamam_result:
                return edamam_result
            
            # Nutritionix API (ücretsiz tier)
            nutritionix_result = await self._search_nutritionix_api(session, food_name)
            if nutritionix_result:
                return nutritionix_result
            
        except Exception as e:
            logger.warning(f"Türk kaynakları araması başarısız: {e}")
        
        return None
    
    async def _search_edamam_api(self, session, food_name: str) -> Optional[Dict[str, Any]]:
        """Edamam Food Database API'sinden ara."""
        try:
            # Edamam Food Database API - ücretsiz tier
            search_url = "https://api.edamam.com/api/food-database/v2/parser"
            
            params = {
                'app_id': 'demo',  # Demo için
                'app_key': 'demo',  # Demo için
                'ingr': food_name,
                'nutrition-type': 'cooking'
            }
            
            async with session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('parsed') and len(data['parsed']) > 0:
                        food = data['parsed'][0]['food']
                        nutrients = food.get('nutrients', {})
                        
                        if nutrients.get('ENERC_KCAL'):
                            return {
                                'food_name': food.get('label', food_name),
                                'calories_per_100g': nutrients.get('ENERC_KCAL', 0),
                                'protein_per_100g': nutrients.get('PROCNT', 0),
                                'carbs_per_100g': nutrients.get('CHOCDF', 0),
                                'fat_per_100g': nutrients.get('FAT', 0),
                                'confidence': 'high',
                                'source': 'Edamam Food Database'
                            }
        except Exception as e:
            logger.warning(f"Edamam API hatası: {e}")
        
        return None
    
    async def _search_nutritionix_api(self, session, food_name: str) -> Optional[Dict[str, Any]]:
        """Nutritionix API'sinden ara."""
        try:
            # Nutritionix API - ücretsiz tier
            search_url = "https://trackapi.nutritionix.com/v2/search/instant"
            
            headers = {
                'x-app-id': 'demo',  # Demo için
                'x-app-key': 'demo',  # Demo için
                'Content-Type': 'application/json'
            }
            
            params = {
                'query': food_name
            }
            
            async with session.get(search_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('common') and len(data['common']) > 0:
                        food = data['common'][0]
                        
                        return {
                            'food_name': food.get('food_name', food_name),
                            'calories_per_100g': food.get('nf_calories', 0) * 100 / food.get('serving_weight_grams', 100),
                            'protein_per_100g': food.get('nf_protein', 0) * 100 / food.get('serving_weight_grams', 100),
                            'carbs_per_100g': food.get('nf_total_carbohydrate', 0) * 100 / food.get('serving_weight_grams', 100),
                            'fat_per_100g': food.get('nf_total_fat', 0) * 100 / food.get('serving_weight_grams', 100),
                            'confidence': 'medium',
                            'source': 'Nutritionix Database'
                        }
        except Exception as e:
            logger.warning(f"Nutritionix API hatası: {e}")
        
        return None
    
    async def _search_general_web(self, food_name: str) -> Optional[Dict[str, Any]]:
        """
        Genel web araması - Basit beslenme veritabanları.
        """
        try:
            session = await self.get_session()
            
            # MyFitnessPal benzeri açık kaynaklı beslenme veritabanları
            # Önce OpenFoodFacts API'sini dene
            openfood_result = await self._search_openfoodfacts(session, food_name)
            if openfood_result:
                return openfood_result
            
        except Exception as e:
            logger.warning(f"Genel web araması başarısız: {e}")
        
        return None
    
    async def _search_openfoodfacts(self, session, food_name: str) -> Optional[Dict[str, Any]]:
        """OpenFoodFacts API'sinden ara - Daha akıllı arama."""
        try:
            # OpenFoodFacts API - tamamen ücretsiz ve çok kapsamlı
            search_url = "https://world.openfoodfacts.org/cgi/search.pl"
            
            # Farklı arama terimleri dene
            search_terms = [
                food_name,
                food_name.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ç', 'c').replace('ö', 'o'),  # Türkçe karakterleri İngilizce'ye çevir
                food_name + " food",
                food_name.split()[0] if ' ' in food_name else food_name  # İlk kelimeyi dene
            ]
            
            for search_term in search_terms:
                params = {
                    'search_terms': search_term,
                    'search_simple': 1,
                    'action': 'process',
                    'json': 1,
                    'page_size': 20,  # Daha fazla sonuç
                    'sort_by': 'popularity'  # Popüler olanları önce getir
                }
                
                logger.info(f"🔍 OpenFoodFacts'te arıyor: {search_term}")
                
                async with session.get(search_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('products') and len(data['products']) > 0:
                            # En iyi eşleşmeyi bul
                            best_product = self._find_best_openfood_match(data['products'], food_name)
                            
                            if best_product:
                                nutriments = best_product.get('nutriments', {})
                                
                                # 100g başına değerleri al
                                calories = nutriments.get('energy-kcal_100g', 0)
                                protein = nutriments.get('proteins_100g', 0)
                                carbs = nutriments.get('carbohydrates_100g', 0)
                                fat = nutriments.get('fat_100g', 0)
                                
                                if calories > 0:
                                    logger.info(f"✅ OpenFoodFacts'te bulundu: {best_product.get('product_name')}")
                                    return {
                                        'food_name': best_product.get('product_name', food_name),
                                        'calories_per_100g': calories,
                                        'protein_per_100g': protein,
                                        'carbs_per_100g': carbs,
                                        'fat_per_100g': fat,
                                        'confidence': 'high',
                                        'source': 'OpenFoodFacts'
                                    }
                                    
        except Exception as e:
            logger.warning(f"OpenFoodFacts API hatası: {e}")
        
        return None
    
    def _find_best_openfood_match(self, products: list, query: str) -> Optional[Dict]:
        """OpenFoodFacts sonuçlarından en iyi eşleşmeyi bul."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        best_match = None
        best_score = 0
        
        for product in products:
            product_name = product.get('product_name', '').lower()
            brands = product.get('brands', '').lower()
            categories = product.get('categories', '').lower()
            
            # Skorlama
            score = 0
            
            # Ürün adında tam eşleşme
            if query_lower in product_name:
                score += 25
            
            # Kelime eşleşmeleri
            product_words = set(product_name.split())
            common_words = query_words.intersection(product_words)
            score += len(common_words) * 8
            
            # Kategori eşleşmesi
            if any(word in categories for word in query_words):
                score += 5
            
            # Marka eşleşmesi
            if any(word in brands for word in query_words):
                score += 3
            
            # Besin değerleri var mı kontrol et
            nutriments = product.get('nutriments', {})
            if nutriments.get('energy-kcal_100g', 0) > 0:
                score += 10
            
            # Popülerlik skoru (unique_scans_n)
            popularity = product.get('unique_scans_n', 0)
            if popularity > 100:
                score += 5
            elif popularity > 10:
                score += 2
            
            if score > best_score:
                best_score = score
                best_match = product
        
        return best_match if best_score > 10 else None
    
    def _extract_nutrition_from_html(self, html: str, food_name: str) -> Optional[Dict[str, Any]]:
        """
        HTML içeriğinden besin değerlerini çıkarmaya çalış.
        """
        try:
            # Kalori değerini ara
            calorie_patterns = [
                r'(\d+)\s*(?:kcal|kalori|cal)',
                r'kalori[:\s]*(\d+)',
                r'energy[:\s]*(\d+)',
                r'(\d+)\s*cal(?:ories)?'
            ]
            
            calories = None
            for pattern in calorie_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    calories = float(match.group(1))
                    break
            
            if not calories:
                return None
            
            # Protein değerini ara
            protein_patterns = [
                r'protein[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'(\d+(?:\.\d+)?)\s*g\s*protein',
                r'protein[:\s]*(\d+(?:\.\d+)?)'
            ]
            
            protein = 0
            for pattern in protein_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    protein = float(match.group(1))
                    break
            
            # Karbonhidrat değerini ara
            carb_patterns = [
                r'karbonhidrat[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'carb(?:ohydrate)?[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'(\d+(?:\.\d+)?)\s*g\s*karbonhidrat'
            ]
            
            carbs = 0
            for pattern in carb_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    carbs = float(match.group(1))
                    break
            
            # Yağ değerini ara
            fat_patterns = [
                r'yağ[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'fat[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'(\d+(?:\.\d+)?)\s*g\s*yağ'
            ]
            
            fat = 0
            for pattern in fat_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    fat = float(match.group(1))
                    break
            
            # Makul değerler kontrolü
            if 0 <= calories <= 900 and 0 <= protein <= 100 and 0 <= carbs <= 100 and 0 <= fat <= 100:
                return {
                    'food_name': food_name,
                    'calories_per_100g': calories,
                    'protein_per_100g': protein,
                    'carbs_per_100g': carbs,
                    'fat_per_100g': fat
                }
            
        except Exception as e:
            logger.warning(f"HTML parsing hatası: {e}")
        
        return None


class LocalAIModel:
    """
    Yerel AI modeli servisi.
    Şu anda mock implementasyon - gerçek AI modeli entegre edilebilir.
    """
    
    def __init__(self):
        self.is_initialized = False
        self.model_available = True
        self.web_searcher = WebNutritionSearcher()
        self.web_scraper = None  # Lazy initialization
        
    async def initialize(self) -> bool:
        """AI modelini başlat."""
        try:
            # Mock initialization - gerçek model yüklemesi burada yapılır
            await asyncio.sleep(0.1)  # Simüle edilmiş yükleme süresi
            
            # Web scraper'ı başlat
            self.web_scraper = await get_web_scraping_engine()
            
            self.is_initialized = True
            logger.info("🤖 AI modeli başarıyla başlatıldı (Mock)")
            return True
        except Exception as e:
            logger.error(f"❌ AI modeli başlatılamadı: {e}")
            self.model_available = False
            return False
    
    def is_available(self) -> bool:
        """AI modelinin kullanılabilir olup olmadığını kontrol et."""
        return self.is_initialized and self.model_available
    
    async def generate_response(self, prompt: str, context: list[str] = None) -> str:
        """
        AI yanıtı üret.
        
        Args:
            prompt: Kullanıcı sorusu
            context: Önceki konuşma bağlamı
            
        Returns:
            AI yanıtı (Türkçe)
        """
        if not self.is_available():
            raise RuntimeError("AI modeli kullanılamıyor")
        
        try:
            # 30 saniye timeout (web scraping için)
            return await asyncio.wait_for(
                self._process_nutrition_query(prompt, context),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            raise RuntimeError("AI yanıtı zaman aşımına uğradı (30 saniye)")
        except Exception as e:
            logger.error(f"AI yanıt üretme hatası: {e}")
            raise RuntimeError(f"AI yanıt hatası: {str(e)}")
    
    async def _process_nutrition_query(self, query: str, context: list[str] = None) -> str:
        """
        Besin değerleri sorgusunu işle ve Türkçe yanıt üret.
        
        YENİ STRATEJİ: Önce web'den arar, bulamazsa yerel veritabanını kullanır.
        Bu sayede güncel ve doğru veriler öncelikli olur.
        """
        # Simüle edilmiş işleme süresi
        await asyncio.sleep(0.5)
        
        query_lower = query.lower()
        
        # Sorgudan besin adını çıkar
        food_name = self._extract_food_name(query_lower)
        
        if food_name:
            # ÖNCELİK 1: Gerçek web API'lerini dene (en güncel veriler)
            logger.info(f"🌐 Önce web API'lerinde arıyor: {food_name}")
            try:
                web_result = await self.web_searcher.search_nutrition_data(food_name)
                
                if web_result:
                    logger.info(f"✅ Web API'lerinde bulundu: {web_result['source']}")
                    return self._format_nutrition_response(web_result, from_web=True)
                else:
                    logger.info(f"❌ Web API'lerinde bulunamadı: {food_name}")
            except Exception as e:
                logger.error(f"❌ Web API araması hatası: {e}")
            
            # ÖNCELİK 2: Web scraping dene (Türk siteleri)
            logger.info(f"🕷️ Web scraping ile arıyor: {food_name}")
            if self.web_scraper:
                try:
                    # Scraping için timeout (10 saniye)
                    scraping_result = await asyncio.wait_for(
                        self.web_scraper.search_food(food_name),
                        timeout=10.0
                    )
                    
                    if scraping_result:
                        logger.info(f"✅ Scraping ile bulundu: {scraping_result.source}")
                        scraping_data = {
                            'food_name': scraping_result.food_name,
                            'calories_per_100g': scraping_result.calories_per_100g,
                            'protein_per_100g': scraping_result.protein_per_100g,
                            'carbs_per_100g': scraping_result.carbs_per_100g,
                            'fat_per_100g': scraping_result.fat_per_100g,
                            'confidence': scraping_result.confidence,
                            'source': scraping_result.source
                        }
                        return self._format_nutrition_response(scraping_data, from_web=True)
                    else:
                        logger.info(f"❌ Scraping ile bulunamadı: {food_name}")
                        
                except asyncio.TimeoutError:
                    logger.warning(f"⏰ Web scraping timeout (10s): {food_name}")
                except Exception as e:
                    logger.error(f"❌ Web scraping hatası: {e}")
            
            # ÖNCELİK 3: Genişletilmiş yerel veritabanından ara (restoran + market + tarifler)
            logger.info(f"🗃️ Genişletilmiş veritabanından arıyor: {food_name}")
            local_result = self._search_expanded_database(food_name)
            
            if local_result:
                logger.info(f"✅ Genişletilmiş veritabanında bulundu: {local_result['food_name']}")
                return self._format_nutrition_response(local_result, from_web=False)
            else:
                logger.info(f"❌ Genişletilmiş veritabanında da bulunamadı: {food_name}")
            
            # ÖNCELİK 4: Orijinal yerel veritabanından ara (fallback)
            logger.info(f"🗃️ Orijinal yerel veritabanından arıyor (fallback): {food_name}")
            original_local_result = self._search_local_database(food_name)
            
            if original_local_result:
                logger.info(f"✅ Orijinal yerel veritabanında bulundu (fallback): {original_local_result['food_name']}")
                return self._format_nutrition_response(original_local_result, from_web=False)
            else:
                logger.info(f"❌ Orijinal yerel veritabanında da bulunamadı: {food_name}")
        
        # Bu noktaya asla gelmemeli çünkü web scraping her zaman sonuç döndürür
        logger.error(f"🚨 BEKLENMEYEN DURUM: Hiçbir yerde bulunamadı: {food_name}")
        return self._generate_not_found_response(query)
    
    def _search_expanded_database(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Genişletilmiş veritabanından ara (restoran + market + tarifler)."""
        try:
            # Restoran scraper'dan veri al
            from .restaurant_scraper import restaurant_scraper
            
            # Restoran menülerini kontrol et
            restaurant_data = self._search_in_restaurant_data(food_name)
            if restaurant_data:
                return restaurant_data
            
            # Market ürünlerini kontrol et  
            market_data = self._search_in_market_data(food_name)
            if market_data:
                return market_data
            
            # Ev yapımı tarifleri kontrol et
            recipe_data = self._search_in_recipe_data(food_name)
            if recipe_data:
                return recipe_data
            
            return None
            
        except Exception as e:
            logger.error(f"Genişletilmiş veritabanı arama hatası: {e}")
            return None
    
    def _search_in_restaurant_data(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Restoran verilerinde ara."""
        from .restaurant_scraper import restaurant_scraper
        
        # Restoran zincirlerinde ara
        all_restaurants = {
            **restaurant_scraper.restaurant_chains,
            **restaurant_scraper.turkish_restaurants,
            **restaurant_scraper.cafe_chains
        }
        
        food_lower = food_name.lower()
        
        for chain_id, chain_data in all_restaurants.items():
            for item_name, nutrition in chain_data["menu_items"].items():
                item_lower = item_name.lower()
                
                # Tam eşleşme veya kısmi eşleşme
                if (food_lower in item_lower or item_lower in food_lower or
                    any(word in item_lower for word in food_lower.split()) or
                    any(word in food_lower for word in item_lower.split())):
                    
                    return {
                        'food_name': f"{item_name} ({chain_data['name']})",
                        'calories_per_100g': nutrition['calories'],
                        'protein_per_100g': nutrition['protein'],
                        'carbs_per_100g': nutrition['carbs'],
                        'fat_per_100g': nutrition['fat'],
                        'confidence': 'high',
                        'source': f"Restoran: {chain_data['name']}"
                    }
        
        return None
    
    def _search_in_market_data(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Market verilerinde ara."""
        # Market ürünleri (manuel derlenmiş)
        market_products = {
            "süt": {"name": "Süt Tam Yağlı", "calories": 61, "protein": 3.2, "carbs": 4.8, "fat": 3.3},
            "yoğurt": {"name": "Yoğurt Tam Yağlı", "calories": 61, "protein": 3.5, "carbs": 4.7, "fat": 3.3},
            "peynir": {"name": "Beyaz Peynir", "calories": 264, "protein": 17.6, "carbs": 0.9, "fat": 21},
            "ekmek": {"name": "Ekmek Beyaz", "calories": 265, "protein": 9, "carbs": 49, "fat": 3.2},
            "pirinç": {"name": "Pirinç", "calories": 365, "protein": 7.1, "carbs": 80, "fat": 0.7},
            "makarna": {"name": "Makarna", "calories": 371, "protein": 13, "carbs": 74, "fat": 1.5},
            "tavuk": {"name": "Tavuk Göğsü", "calories": 165, "protein": 31, "carbs": 0, "fat": 3.6},
            "et": {"name": "Dana Kıyma", "calories": 250, "protein": 26, "carbs": 0, "fat": 15},
            "çikolata": {"name": "Çikolata", "calories": 546, "protein": 4.9, "carbs": 61, "fat": 31}
        }
        
        food_lower = food_name.lower()
        
        # Direkt eşleşme
        if food_lower in market_products:
            product = market_products[food_lower]
            return {
                'food_name': product['name'],
                'calories_per_100g': product['calories'],
                'protein_per_100g': product['protein'],
                'carbs_per_100g': product['carbs'],
                'fat_per_100g': product['fat'],
                'confidence': 'high',
                'source': 'Market Ürünü'
            }
        
        # Kısmi eşleşme
        for key, product in market_products.items():
            if (key in food_lower or food_lower in key or
                any(word in key for word in food_lower.split())):
                return {
                    'food_name': product['name'],
                    'calories_per_100g': product['calories'],
                    'protein_per_100g': product['protein'],
                    'carbs_per_100g': product['carbs'],
                    'fat_per_100g': product['fat'],
                    'confidence': 'medium',
                    'source': 'Market Ürünü'
                }
        
        return None
    
    def _search_in_recipe_data(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Ev yapımı tarif verilerinde ara."""
        # Ev yapımı tarifler (manuel derlenmiş)
        recipes = {
            "kıymalı börek": {"calories": 280, "protein": 15, "carbs": 25, "fat": 14},
            "peynirli börek": {"calories": 240, "protein": 12, "carbs": 22, "fat": 12},
            "ıspanaklı börek": {"calories": 210, "protein": 9, "carbs": 24, "fat": 10},
            "mercimek çorbası": {"calories": 116, "protein": 9, "carbs": 20, "fat": 0.4},
            "yayla çorbası": {"calories": 85, "protein": 4.5, "carbs": 8, "fat": 4},
            "karnıyarık": {"calories": 220, "protein": 12, "carbs": 18, "fat": 12},
            "dolma": {"calories": 158, "protein": 3.5, "carbs": 25, "fat": 5.5},
            "sarma": {"calories": 145, "protein": 8, "carbs": 18, "fat": 5},
            "menemen": {"calories": 180, "protein": 12, "carbs": 8, "fat": 12},
            "mantı": {"calories": 155, "protein": 7, "carbs": 23, "fat": 4},
            "köfte": {"calories": 250, "protein": 18, "carbs": 5, "fat": 17},
            "lahmacun": {"calories": 235, "protein": 12, "carbs": 28, "fat": 8.5},
            "baklava": {"calories": 520, "protein": 9, "carbs": 63, "fat": 26},
            "künefe": {"calories": 380, "protein": 12, "carbs": 45, "fat": 18}
        }
        
        food_lower = food_name.lower()
        
        # Direkt eşleşme
        if food_lower in recipes:
            recipe = recipes[food_lower]
            return {
                'food_name': f"{food_name.title()} (Ev Yapımı)",
                'calories_per_100g': recipe['calories'],
                'protein_per_100g': recipe['protein'],
                'carbs_per_100g': recipe['carbs'],
                'fat_per_100g': recipe['fat'],
                'confidence': 'medium',
                'source': 'Ev Yapımı Tarif'
            }
        
        # Kısmi eşleşme
        for key, recipe in recipes.items():
            if (key in food_lower or food_lower in key or
                any(word in key for word in food_lower.split()) or
                any(word in food_lower for word in key.split())):
                return {
                    'food_name': f"{key.title()} (Ev Yapımı)",
                    'calories_per_100g': recipe['calories'],
                    'protein_per_100g': recipe['protein'],
                    'carbs_per_100g': recipe['carbs'],
                    'fat_per_100g': recipe['fat'],
                    'confidence': 'medium',
                    'source': 'Ev Yapımı Tarif'
                }
        
        return None
    
    def _extract_food_name(self, query: str) -> Optional[str]:
        """Sorgudan besin adını çıkar."""
        # Yaygın soru kalıplarını temizle
        clean_patterns = [
            r'besin değerleri?',
            r'kaç kalori',
            r'kalori miktarı',
            r'protein miktarı',
            r'nedir\?*',
            r'hakkında',
            r'için',
            r'100\s*gram?',
            r'gram başına',
            r'başına'
        ]
        
        cleaned_query = query
        for pattern in clean_patterns:
            cleaned_query = re.sub(pattern, '', cleaned_query, flags=re.IGNORECASE)
        
        # Gereksiz kelimeleri temizle
        stop_words = ['bir', 'kaç', 'ne', 'nasıl', 'hangi', 'şu', 'bu', 'o', 'da', 'de', 'ki', 'mi', 'mı', 'mu', 'mü']
        words = cleaned_query.split()
        filtered_words = [word for word in words if word.lower() not in stop_words and len(word) > 2]
        
        if filtered_words:
            return ' '.join(filtered_words).strip()
        
        return None
    
    def _search_local_database(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Yerel veritabanından besin ara."""
        # Kapsamlı Türk yemekleri ve uluslararası besinler veritabanı
        food_database = {
            # === TEMEL BESİNLER ===
            "tavuk": {
                "name": "Tavuk Göğsü (Haşlanmış)",
                "calories": 165,
                "protein": 31.0,
                "carbs": 0.0,
                "fat": 3.6
            },
            "pilav": {
                "name": "Pirinç Pilavı",
                "calories": 130,
                "protein": 2.7,
                "carbs": 28.0,
                "fat": 0.3
            },
            "tavuk pilav": {
                "name": "Tavuklu Pilav",
                "calories": 180,
                "protein": 12.0,
                "carbs": 25.0,
                "fat": 4.5
            },
            "tavuklu pilav": {
                "name": "Tavuklu Pilav",
                "calories": 180,
                "protein": 12.0,
                "carbs": 25.0,
                "fat": 4.5
            },
            # "köfte": {
            #     "name": "Dana Köftesi", 
            #     "calories": 250,
            #     "protein": 18.0,
            #     "carbs": 5.0,
            #     "fat": 17.0
            # },
            "köfte": {
                "name": "Dana Köftesi (Izgara)",
                "calories": 250,
                "protein": 18.0,
                "carbs": 5.0,
                "fat": 17.0
            },
            "mercimek": {
                "name": "Mercimek Çorbası",
                "calories": 116,
                "protein": 9.0,
                "carbs": 20.0,
                "fat": 0.4
            },
            "yogurt": {
                "name": "Süzme Yoğurt",
                "calories": 59,
                "protein": 10.0,
                "carbs": 3.6,
                "fat": 0.4
            },
            "ekmek": {
                "name": "Beyaz Ekmek",
                "calories": 265,
                "protein": 9.0,
                "carbs": 49.0,
                "fat": 3.2
            },
            
            # === SEBZELER ===
            "domates": {
                "name": "Domates",
                "calories": 18,
                "protein": 0.9,
                "carbs": 3.9,
                "fat": 0.2
            },
            "salatalık": {
                "name": "Salatalık",
                "calories": 16,
                "protein": 0.7,
                "carbs": 4.0,
                "fat": 0.1
            },
            "patates": {
                "name": "Patates (Haşlanmış)",
                "calories": 87,
                "protein": 1.9,
                "carbs": 20.1,
                "fat": 0.1
            },
            "havuç": {
                "name": "Havuç",
                "calories": 41,
                "protein": 0.9,
                "carbs": 9.6,
                "fat": 0.2
            },
            "soğan": {
                "name": "Soğan",
                "calories": 40,
                "protein": 1.1,
                "carbs": 9.3,
                "fat": 0.1
            },
            "sarımsak": {
                "name": "Sarımsak",
                "calories": 149,
                "protein": 6.4,
                "carbs": 33.1,
                "fat": 0.5
            },
            "biber": {
                "name": "Kırmızı Biber",
                "calories": 31,
                "protein": 1.0,
                "carbs": 7.3,
                "fat": 0.3
            },
            "salata": {
                "name": "Marul",
                "calories": 15,
                "protein": 1.4,
                "carbs": 2.9,
                "fat": 0.2
            },
            "ispanak": {
                "name": "Ispanak",
                "calories": 23,
                "protein": 2.9,
                "carbs": 3.6,
                "fat": 0.4
            },
            "brokoli": {
                "name": "Brokoli",
                "calories": 34,
                "protein": 2.8,
                "carbs": 7.0,
                "fat": 0.4
            },
            "karnabahar": {
                "name": "Karnabahar",
                "calories": 25,
                "protein": 1.9,
                "carbs": 5.0,
                "fat": 0.3
            },
            "kabak": {
                "name": "Kabak",
                "calories": 17,
                "protein": 1.2,
                "carbs": 3.4,
                "fat": 0.2
            },
            "patlıcan": {
                "name": "Patlıcan",
                "calories": 25,
                "protein": 1.0,
                "carbs": 6.0,
                "fat": 0.2
            },
            
            # === KURUYEMIŞLER ===
            "badem": {
                "name": "Badem (Çiğ)",
                "calories": 579,
                "protein": 21.2,
                "carbs": 21.6,
                "fat": 49.9
            },
            "ceviz": {
                "name": "Ceviz",
                "calories": 654,
                "protein": 15.2,
                "carbs": 13.7,
                "fat": 65.2
            },
            "fındık": {
                "name": "Fındık",
                "calories": 628,
                "protein": 15.0,
                "carbs": 16.7,
                "fat": 60.8
            },
            "antep fıstığı": {
                "name": "Antep Fıstığı",
                "calories": 560,
                "protein": 20.2,
                "carbs": 27.2,
                "fat": 45.3
            },
            "yer fıstığı": {
                "name": "Yer Fıstığı",
                "calories": 567,
                "protein": 25.8,
                "carbs": 16.1,
                "fat": 49.2
            },
            "kaju": {
                "name": "Kaju",
                "calories": 553,
                "protein": 18.2,
                "carbs": 30.2,
                "fat": 43.9
            },
            
            # === MEYVELER ===
            "elma": {
                "name": "Elma",
                "calories": 52,
                "protein": 0.3,
                "carbs": 13.8,
                "fat": 0.2
            },
            "muz": {
                "name": "Muz",
                "calories": 89,
                "protein": 1.1,
                "carbs": 22.8,
                "fat": 0.3
            },
            "portakal": {
                "name": "Portakal",
                "calories": 47,
                "protein": 0.9,
                "carbs": 11.8,
                "fat": 0.1
            },
            "üzüm": {
                "name": "Üzüm",
                "calories": 62,
                "protein": 0.6,
                "carbs": 16.0,
                "fat": 0.2
            },
            "çilek": {
                "name": "Çilek",
                "calories": 32,
                "protein": 0.7,
                "carbs": 7.7,
                "fat": 0.3
            },
            "kivi": {
                "name": "Kivi",
                "calories": 61,
                "protein": 1.1,
                "carbs": 14.7,
                "fat": 0.5
            },
            "ananas": {
                "name": "Ananas",
                "calories": 50,
                "protein": 0.5,
                "carbs": 13.1,
                "fat": 0.1
            },
            "kavun": {
                "name": "Kavun",
                "calories": 34,
                "protein": 0.8,
                "carbs": 8.2,
                "fat": 0.2
            },
            "karpuz": {
                "name": "Karpuz",
                "calories": 30,
                "protein": 0.6,
                "carbs": 7.6,
                "fat": 0.2
            },
            
            # === SÜT ÜRÜNLERİ ===
            "peynir": {
                "name": "Beyaz Peynir",
                "calories": 264,
                "protein": 17.6,
                "carbs": 0.9,
                "fat": 21.0
            },
            "kaşar": {
                "name": "Kaşar Peyniri",
                "calories": 330,
                "protein": 23.0,
                "carbs": 2.0,
                "fat": 25.0
            },
            "lor": {
                "name": "Lor Peyniri",
                "calories": 166,
                "protein": 12.0,
                "carbs": 4.0,
                "fat": 11.0
            },
            "süt": {
                "name": "İnek Sütü (Tam Yağlı)",
                "calories": 61,
                "protein": 3.2,
                "carbs": 4.8,
                "fat": 3.3
            },
            "yağsız süt": {
                "name": "Yağsız Süt",
                "calories": 34,
                "protein": 3.4,
                "carbs": 5.0,
                "fat": 0.1
            },
            "tereyağı": {
                "name": "Tereyağı",
                "calories": 717,
                "protein": 0.9,
                "carbs": 0.1,
                "fat": 81.1
            },
            
            # === ET VE BALIK ===
            "et": {
                "name": "Dana Eti (Yağsız)",
                "calories": 250,
                "protein": 26.0,
                "carbs": 0.0,
                "fat": 15.0
            },
            "kuzu": {
                "name": "Kuzu Eti",
                "calories": 294,
                "protein": 25.0,
                "carbs": 0.0,
                "fat": 21.0
            },
            "hindi": {
                "name": "Hindi Eti",
                "calories": 189,
                "protein": 29.0,
                "carbs": 0.0,
                "fat": 7.0
            },
            "balık": {
                "name": "Levrek Balığı",
                "calories": 124,
                "protein": 24.0,
                "carbs": 0.0,
                "fat": 3.0
            },
            "somon": {
                "name": "Somon Balığı",
                "calories": 208,
                "protein": 25.4,
                "carbs": 0.0,
                "fat": 12.4
            },
            "ton balığı": {
                "name": "Ton Balığı",
                "calories": 184,
                "protein": 30.0,
                "carbs": 0.0,
                "fat": 6.3
            },
            "sardalya": {
                "name": "Sardalya",
                "calories": 208,
                "protein": 25.0,
                "carbs": 0.0,
                "fat": 11.5
            },
            
            # === TAHILLAR VE BAKLAGILLER ===
            "makarna": {
                "name": "Makarna (Haşlanmış)",
                "calories": 131,
                "protein": 5.0,
                "carbs": 25.0,
                "fat": 1.1
            },
            "bulgur": {
                "name": "Bulgur Pilavı",
                "calories": 83,
                "protein": 3.1,
                "carbs": 18.6,
                "fat": 0.2
            },
            "nohut": {
                "name": "Nohut (Haşlanmış)",
                "calories": 164,
                "protein": 8.9,
                "carbs": 27.4,
                "fat": 2.6
            },
            "fasulye": {
                "name": "Kuru Fasulye",
                "calories": 127,
                "protein": 9.0,
                "carbs": 22.8,
                "fat": 0.5
            },
            "barbunya": {
                "name": "Barbunya Fasulyesi",
                "calories": 124,
                "protein": 8.7,
                "carbs": 22.5,
                "fat": 0.5
            },
            "börülce": {
                "name": "Börülce",
                "calories": 116,
                "protein": 8.2,
                "carbs": 20.2,
                "fat": 0.4
            },
            "yulaf": {
                "name": "Yulaf Ezmesi",
                "calories": 389,
                "protein": 16.9,
                "carbs": 66.3,
                "fat": 6.9
            },
            
            # === YUMURTA ===
            "yumurta": {
                "name": "Tavuk Yumurtası",
                "calories": 155,
                "protein": 13.0,
                "carbs": 1.1,
                "fat": 11.0
            },
            "yumurta akı": {
                "name": "Yumurta Akı",
                "calories": 52,
                "protein": 11.0,
                "carbs": 0.7,
                "fat": 0.2
            },
            "yumurta sarısı": {
                "name": "Yumurta Sarısı",
                "calories": 322,
                "protein": 16.0,
                "carbs": 3.6,
                "fat": 27.0
            },
            
            # === İÇECEKLER ===
            "çay": {
                "name": "Siyah Çay (Şekersiz)",
                "calories": 2,
                "protein": 0.7,
                "carbs": 0.3,
                "fat": 0.0
            },
            "kahve": {
                "name": "Türk Kahvesi (Şekersiz)",
                "calories": 7,
                "protein": 0.1,
                "carbs": 1.6,
                "fat": 0.0
            },
            "ayran": {
                "name": "Ayran",
                "calories": 36,
                "protein": 1.7,
                "carbs": 2.9,
                "fat": 2.0
            },
            
            # === SÜPER GIDALAR ===
            "quinoa": {
                "name": "Quinoa (Haşlanmış)",
                "calories": 120,
                "protein": 4.4,
                "carbs": 22.0,
                "fat": 1.9
            },
            "avokado": {
                "name": "Avokado",
                "calories": 160,
                "protein": 2.0,
                "carbs": 8.5,
                "fat": 14.7
            },
            "chia": {
                "name": "Chia Tohumu",
                "calories": 486,
                "protein": 16.5,
                "carbs": 42.1,
                "fat": 30.7
            },
            "kenevir": {
                "name": "Kenevir Tohumu",
                "calories": 553,
                "protein": 31.6,
                "carbs": 8.7,
                "fat": 48.8
            },
            "susam": {
                "name": "Susam",
                "calories": 573,
                "protein": 17.7,
                "carbs": 23.4,
                "fat": 49.7
            },
            
            # === TATLILAR VE DİĞERLERİ ===
            "bal": {
                "name": "Çiçek Balı",
                "calories": 304,
                "protein": 0.3,
                "carbs": 82.4,
                "fat": 0.0
            },
            "zeytin": {
                "name": "Siyah Zeytin",
                "calories": 115,
                "protein": 0.8,
                "carbs": 6.0,
                "fat": 10.7
            },
            "yeşil zeytin": {
                "name": "Yeşil Zeytin",
                "calories": 125,
                "protein": 0.8,
                "carbs": 3.3,
                "fat": 13.3
            },
            "zeytinyağı": {
                "name": "Zeytinyağı",
                "calories": 884,
                "protein": 0.0,
                "carbs": 0.0,
                "fat": 100.0
            },
            
            # === TÜRK MUTFAĞI ÖZELLERİ ===
            "döner": {
                "name": "Döner Kebap",
                "calories": 280,
                "protein": 25.0,
                "carbs": 5.0,
                "fat": 18.0
            },
            "lahmacun": {
                "name": "Lahmacun",
                "calories": 235,
                "protein": 12.0,
                "carbs": 28.0,
                "fat": 8.5
            },
            "pide": {
                "name": "Pide (Kıymalı)",
                "calories": 290,
                "protein": 15.0,
                "carbs": 35.0,
                "fat": 10.0
            },
            "börek": {
                "name": "Su Böreği",
                "calories": 195,
                "protein": 8.0,
                "carbs": 20.0,
                "fat": 9.0
            },
            "kıymalı börek": {
                "name": "Kıymalı Börek",
                "calories": 280,
                "protein": 15.0,
                "carbs": 25.0,
                "fat": 14.0
            },
            "peynirli börek": {
                "name": "Peynirli Börek",
                "calories": 240,
                "protein": 12.0,
                "carbs": 22.0,
                "fat": 12.0
            },
            "ıspanaklı börek": {
                "name": "Ispanaklı Börek",
                "calories": 210,
                "protein": 9.0,
                "carbs": 24.0,
                "fat": 10.0
            },
            "patatesli börek": {
                "name": "Patatesli Börek",
                "calories": 220,
                "protein": 7.0,
                "carbs": 28.0,
                "fat": 9.5
            },
            "mantı": {
                "name": "Mantı",
                "calories": 155,
                "protein": 7.0,
                "carbs": 23.0,
                "fat": 4.0
            },
            "dolma": {
                "name": "Yaprak Dolması",
                "calories": 158,
                "protein": 3.5,
                "carbs": 25.0,
                "fat": 5.5
            },
            "sarma": {
                "name": "Lahana Sarması",
                "calories": 145,
                "protein": 8.0,
                "carbs": 18.0,
                "fat": 5.0
            },
            "imam bayıldı": {
                "name": "İmam Bayıldı",
                "calories": 180,
                "protein": 2.5,
                "carbs": 15.0,
                "fat": 12.0
            },
            "karnıyarık": {
                "name": "Karnıyarık",
                "calories": 220,
                "protein": 12.0,
                "carbs": 18.0,
                "fat": 12.0
            },
            "menemen": {
                "name": "Menemen",
                "calories": 180,
                "protein": 12.0,
                "carbs": 8.0,
                "fat": 12.0
            },
            "çılbır": {
                "name": "Çılbır",
                "calories": 220,
                "protein": 15.0,
                "carbs": 8.0,
                "fat": 15.0
            },
            "sucuklu yumurta": {
                "name": "Sucuklu Yumurta",
                "calories": 320,
                "protein": 18.0,
                "carbs": 2.0,
                "fat": 26.0
            },
            "türlü": {
                "name": "Türlü",
                "calories": 85,
                "protein": 3.0,
                "carbs": 12.0,
                "fat": 3.0
            },
            "güveç": {
                "name": "Et Güveç",
                "calories": 195,
                "protein": 18.0,
                "carbs": 8.0,
                "fat": 10.0
            },
            
            # === EK TÜRK YEMEKLERİ ===
            "kebap": {
                "name": "Şiş Kebap",
                "calories": 280,
                "protein": 25.0,
                "carbs": 2.0,
                "fat": 18.0
            },
            "adana kebap": {
                "name": "Adana Kebap",
                "calories": 320,
                "protein": 22.0,
                "carbs": 3.0,
                "fat": 24.0
            },
            "urfa kebap": {
                "name": "Urfa Kebap",
                "calories": 300,
                "protein": 23.0,
                "carbs": 2.5,
                "fat": 22.0
            },
            "tavuk şiş": {
                "name": "Tavuk Şiş",
                "calories": 195,
                "protein": 29.0,
                "carbs": 1.0,
                "fat": 8.0
            },
            "köfte ekmek": {
                "name": "Köfte Ekmek",
                "calories": 380,
                "protein": 22.0,
                "carbs": 35.0,
                "fat": 18.0
            },
            "çiğ köfte": {
                "name": "Çiğ Köfte",
                "calories": 180,
                "protein": 8.0,
                "carbs": 28.0,
                "fat": 4.0
            },
            "iskender": {
                "name": "İskender Kebap",
                "calories": 420,
                "protein": 28.0,
                "carbs": 25.0,
                "fat": 25.0
            },
            "dürüm": {
                "name": "Et Dürüm",
                "calories": 350,
                "protein": 20.0,
                "carbs": 30.0,
                "fat": 18.0
            },
            "tavuk dürüm": {
                "name": "Tavuk Dürüm",
                "calories": 320,
                "protein": 22.0,
                "carbs": 28.0,
                "fat": 14.0
            },
            "balık ekmek": {
                "name": "Balık Ekmek",
                "calories": 280,
                "protein": 25.0,
                "carbs": 22.0,
                "fat": 12.0
            },
            "midye dolma": {
                "name": "Midye Dolması",
                "calories": 85,
                "protein": 4.0,
                "carbs": 12.0,
                "fat": 2.5
            },
            "kokoreç": {
                "name": "Kokoreç",
                "calories": 290,
                "protein": 16.0,
                "carbs": 8.0,
                "fat": 22.0
            },
            "tantuni": {
                "name": "Tantuni",
                "calories": 310,
                "protein": 18.0,
                "carbs": 25.0,
                "fat": 16.0
            },
            "çorba": {
                "name": "Et Suyu Çorbası",
                "calories": 45,
                "protein": 4.0,
                "carbs": 3.0,
                "fat": 2.0
            },
            "yayla çorbası": {
                "name": "Yayla Çorbası",
                "calories": 85,
                "protein": 4.5,
                "carbs": 8.0,
                "fat": 4.0
            },
            "tarhana": {
                "name": "Tarhana Çorbası",
                "calories": 95,
                "protein": 4.0,
                "carbs": 15.0,
                "fat": 2.5
            },
            "ezogelin": {
                "name": "Ezogelin Çorbası",
                "calories": 110,
                "protein": 6.0,
                "carbs": 18.0,
                "fat": 2.0
            },
            "domates çorbası": {
                "name": "Domates Çorbası",
                "calories": 65,
                "protein": 2.0,
                "carbs": 12.0,
                "fat": 1.5
            },
            "tavuk çorbası": {
                "name": "Tavuk Çorbası",
                "calories": 75,
                "protein": 8.0,
                "carbs": 5.0,
                "fat": 3.0
            },
            
            # === TATLILAR ===
            "baklava": {
                "name": "Baklava",
                "calories": 520,
                "protein": 9.0,
                "carbs": 63.0,
                "fat": 26.0
            },
            # "künefe": {
            #     "name": "Künefe",
            #     "calories": 380,
            #     "protein": 12.0,
            #     "carbs": 45.0,
            #     "fat": 18.0
            # },
            "tulumba": {
                "name": "Tulumba Tatlısı",
                "calories": 450,
                "protein": 6.0,
                "carbs": 65.0,
                "fat": 18.0
            },
            "lokma": {
                "name": "Lokma",
                "calories": 420,
                "protein": 5.0,
                "carbs": 60.0,
                "fat": 17.0
            },
            "revani": {
                "name": "Revani",
                "calories": 350,
                "protein": 6.0,
                "carbs": 55.0,
                "fat": 12.0
            },
            "sütlaç": {
                "name": "Sütlaç",
                "calories": 140,
                "protein": 4.5,
                "carbs": 22.0,
                "fat": 4.0
            },
            "muhallebi": {
                "name": "Muhallebi",
                "calories": 120,
                "protein": 3.5,
                "carbs": 18.0,
                "fat": 4.5
            },
            "kazandibi": {
                "name": "Kazandibi",
                "calories": 180,
                "protein": 5.0,
                "carbs": 25.0,
                "fat": 7.0
            },
            "aşure": {
                "name": "Aşure",
                "calories": 160,
                "protein": 4.0,
                "carbs": 32.0,
                "fat": 3.0
            },
            "helva": {
                "name": "Tahin Helvası",
                "calories": 470,
                "protein": 12.0,
                "carbs": 50.0,
                "fat": 25.0
            },
            
            # === FAST FOOD ===
            "hamburger": {
                "name": "Hamburger",
                "calories": 295,
                "protein": 17.0,
                "carbs": 31.0,
                "fat": 12.0
            },
            "cheeseburger": {
                "name": "Cheeseburger",
                "calories": 335,
                "protein": 19.0,
                "carbs": 32.0,
                "fat": 16.0
            },
            # "pizza": {
            #     "name": "Margherita Pizza",
            #     "calories": 266,
            #     "protein": 11.0,
            #     "carbs": 33.0,
            #     "fat": 10.0
            # },
            "patates kızartması": {
                "name": "Patates Kızartması",
                "calories": 365,
                "protein": 4.0,
                "carbs": 63.0,
                "fat": 17.0
            },
            "nugget": {
                "name": "Tavuk Nugget",
                "calories": 296,
                "protein": 15.0,
                "carbs": 16.0,
                "fat": 18.0
            },
            "hot dog": {
                "name": "Hot Dog",
                "calories": 290,
                "protein": 11.0,
                "carbs": 25.0,
                "fat": 17.0
            }
        }
        
        # Sorgudan besin adını bul - akıllı arama algoritması
        found_food = None
        query_words = food_name.lower().split()
        query_lower = food_name.lower()
        
        # 1. TAM EŞLEŞMEYİ ÖNCE KONTROL ET
        for food_key, food_data in food_database.items():
            if food_key == query_lower:  # Tam eşleşme
                found_food = food_data
                break
        
        # 2. TAM CÜMLE EŞLEŞMESİ (örn: "tavuk pilav" → "tavuk pilav")
        if not found_food:
            for food_key, food_data in food_database.items():
                if query_lower == food_key or query_lower in food_key:
                    found_food = food_data
                    break
        
        # 3. BAŞLANGIÇ EŞLEŞMESİ (örn: "tavuklu" → "tavuklu pilav")
        if not found_food:
            for food_key, food_data in food_database.items():
                if food_key.startswith(query_lower) or query_lower.startswith(food_key):
                    found_food = food_data
                    break
        
        # 4. KELİME KELİME ARAMA (en son çare)
        if not found_food:
            for food_key, food_data in food_database.items():
                food_key_words = food_key.split()
                # Tüm kelimeler eşleşmeli
                if all(word in food_key for word in query_words):
                    found_food = food_data
                    break
        
        # 3. Benzer kelimeler ve eş anlamlılar ara
        if not found_food:
            synonyms = {
                # Et çeşitleri
                "tavuk": ["tavuk", "piliç", "chicken", "tavuğu", "tavuklu"],
                "et": ["et", "dana", "kuzu", "beef", "meat", "eti"],
                "balık": ["balık", "fish", "levrek", "çupra", "balığı"],
                "hindi": ["hindi", "turkey"],
                
                # Kuruyemişler
                "badem": ["badem", "almond", "bademi", "bademler"],
                "ceviz": ["ceviz", "walnut", "cevizi", "cevizler"],
                "fındık": ["fındık", "hazelnut", "fındığı", "fındıklar"],
                "antep fıstığı": ["antep", "fıstık", "pistachio", "antep fıstığı"],
                "yer fıstığı": ["yer fıstığı", "peanut", "fıstık"],
                "kaju": ["kaju", "cashew"],
                
                # Meyveler
                "elma": ["elma", "apple", "elmayı", "elmalar"],
                "muz": ["muz", "banana", "muzu", "muzlar"],
                "portakal": ["portakal", "orange", "portakalı"],
                "üzüm": ["üzüm", "grape", "üzümü"],
                "çilek": ["çilek", "strawberry", "çileği"],
                "kivi": ["kivi", "kiwi"],
                "ananas": ["ananas", "pineapple"],
                "kavun": ["kavun", "melon", "kavunu"],
                "karpuz": ["karpuz", "watermelon", "karpozu"],
                
                # Sebzeler
                "domates": ["domates", "tomato", "domatesi"],
                "salatalık": ["salatalık", "cucumber", "hıyar"],
                "patates": ["patates", "potato", "patatesi"],
                "havuç": ["havuç", "carrot", "havucu"],
                "soğan": ["soğan", "onion", "soğanı"],
                "sarımsak": ["sarımsak", "garlic", "sarmısağı"],
                "biber": ["biber", "pepper", "biberi"],
                "salata": ["salata", "lettuce", "marul"],
                "ispanak": ["ispanak", "spinach", "ıspanak"],
                "brokoli": ["brokoli", "broccoli"],
                "karnabahar": ["karnabahar", "cauliflower"],
                "kabak": ["kabak", "zucchini", "squash"],
                "patlıcan": ["patlıcan", "eggplant", "aubergine"],
                
                # Süt ürünleri
                "peynir": ["peynir", "cheese", "beyaz peynir", "peyniri"],
                "kaşar": ["kaşar", "cheddar", "kaşarı"],
                "lor": ["lor", "cottage cheese", "loru"],
                "süt": ["süt", "milk", "sütü"],
                "yogurt": ["yogurt", "yoğurt", "süzme", "yoghurt"],
                "tereyağı": ["tereyağı", "butter", "yağ"],
                
                # Tahıllar
                "pilav": ["pilav", "rice", "pirinç", "pilavı"],
                "tavuk pilav": ["tavuk pilav", "tavuklu pilav", "chicken rice", "tavuk pilavı"],
                "tavuklu pilav": ["tavuklu pilav", "tavuk pilav", "chicken rice", "tavuk pilavı"],
                "makarna": ["makarna", "pasta", "spagetti", "makarnanı"],
                "bulgur": ["bulgur", "bulghur", "bulguru"],
                "yulaf": ["yulaf", "oat", "oats", "yulafı"],
                
                # Baklagiller
                "nohut": ["nohut", "chickpea", "nohutlar"],
                "fasulye": ["fasulye", "bean", "beans", "fasulyesi"],
                "mercimek": ["mercimek", "lentil", "lentils", "merciməği"],
                "barbunya": ["barbunya", "kidney bean"],
                "börülce": ["börülce", "black eyed pea"],
                
                # Yumurta
                "yumurta": ["yumurta", "egg", "eggs", "yumurtayı", "yumurtalar"],
                
                # İçecekler
                "çay": ["çay", "tea", "çayı"],
                "kahve": ["kahve", "coffee", "kahvesi"],
                "ayran": ["ayran", "buttermilk"],
                
                # Süper gıdalar
                "quinoa": ["quinoa", "kinoa"],
                "avokado": ["avokado", "avocado"],
                "chia": ["chia", "chia tohumu"],
                "kenevir": ["kenevir", "hemp", "hemp seed"],
                "susam": ["susam", "sesame"],
                
                # Türk mutfağı
                "döner": ["döner", "doner", "kebap"],
                "lahmacun": ["lahmacun", "turkish pizza"],
                "pide": ["pide", "turkish bread"],
                "börek": ["börek", "borek", "su böreği"],
                "kıymalı börek": ["kıymalı börek", "kiymali borek", "börek kıymalı", "kıymalı", "meat börek"],
                "peynirli börek": ["peynirli börek", "peynirli borek", "börek peynirli", "cheese börek"],
                "ıspanaklı börek": ["ıspanaklı börek", "ispanakli borek", "börek ıspanaklı", "spinach börek"],
                "patatesli börek": ["patatesli börek", "patatesli borek", "börek patatesli", "potato börek"],
                "mantı": ["mantı", "manti", "turkish dumpling"],
                "dolma": ["dolma", "yaprak dolması"],
                "sarma": ["sarma", "lahana sarması"],
                "menemen": ["menemen", "turkish scrambled eggs"],
                "çılbır": ["çılbır", "cilbir", "turkish poached eggs"],
                
                # Diğer
                "bal": ["bal", "honey", "balı"],
                "zeytin": ["zeytin", "olive", "zeytini"],
                "zeytinyağı": ["zeytinyağı", "olive oil", "yağ"]
            }
            
            for food_key, variations in synonyms.items():
                for variation in variations:
                    if variation in food_name.lower():
                        if food_key in food_database:
                            found_food = food_database[food_key]
                            break
                if found_food:
                    break
        
        if found_food:
            return {
                'food_name': found_food['name'],
                'calories_per_100g': found_food['calories'],
                'protein_per_100g': found_food['protein'],
                'carbs_per_100g': found_food['carbs'],
                'fat_per_100g': found_food['fat'],
                'confidence': 'medium',
                'source': 'Yerel Veritabanı'
            }
        
        return None
    
    def _format_nutrition_response(self, nutrition_data: Dict[str, Any], from_web: bool = False) -> str:
        """Besin değerlerini formatla."""
        source_info = ""
        if from_web:
            source_info = f"\n\n📍 **Kaynak**: {nutrition_data.get('source', 'Web Araması')}"
            confidence_emoji = "🔍" if nutrition_data.get('confidence') == 'high' else "⚠️"
        else:
            source_info = f"\n\n📍 **Kaynak**: {nutrition_data.get('source', 'Yerel Veritabanı')}"
            confidence_emoji = "📚"
        
        response = f"""
🔍 **{nutrition_data['food_name']}** icin besin degerleri:

🔥 **Kalori**: {nutrition_data['calories_per_100g']} kcal (100g basina)
💪 **Protein**: {nutrition_data['protein_per_100g']} g
🍞 **Karbonhidrat**: {nutrition_data['carbs_per_100g']} g  
🥑 **Yag**: {nutrition_data['fat_per_100g']} g{source_info}

Bu degerler 100 gram urun icin gecerlidir. Tukettiginiz miktara gore hesaplama yapabilirsiniz.

<!--BESIN_DEĞERLERI_JSON:{{
    "food_name": "{nutrition_data['food_name']}",
    "calories_per_100g": {nutrition_data['calories_per_100g']},
    "protein_per_100g": {nutrition_data['protein_per_100g']},
    "carbs_per_100g": {nutrition_data['carbs_per_100g']},
    "fat_per_100g": {nutrition_data['fat_per_100g']},
    "confidence": "{nutrition_data.get('confidence', 'medium')}",
    "source": "{nutrition_data.get('source', 'Bilinmiyor')}"
}}-->
"""
        return response.strip()
    
    def _generate_not_found_response(self, query: str) -> str:
        """Bulunamadığında akıllı öneriler üret."""
        
        # Popüler besinleri kategorilere ayır
        suggestions = {
            "Et ve Protein": ["tavuk göğsü", "dana eti", "somon balığı", "yumurta", "ton balığı"],
            "Sebzeler": ["brokoli", "ispanak", "domates", "salatalık", "havuç"],
            "Meyveler": ["elma", "muz", "portakal", "çilek", "avokado"],
            "Kuruyemişler": ["badem", "ceviz", "fındık", "antep fıstığı"],
            "Tahıllar": ["quinoa", "yulaf", "bulgur", "pirinç pilavı"],
            "Süt Ürünleri": ["süzme yoğurt", "beyaz peynir", "yağsız süt"],
            "Türk Mutfağı": ["mercimek çorbası", "döner kebap", "mantı", "börek"]
        }
        
        # Rastgele kategori seç ve öneriler sun
        import random
        category = random.choice(list(suggestions.keys()))
        foods = suggestions[category]
        
        return f"""
🔍 "{query}" hakkında tam besin değerlerini bulamadım. 

**💡 Daha net soru sorun:**
- Besin adını tam olarak yazın
- Pişirme yöntemini belirtin (haşlanmış, ızgara, çiğ)
- Marka veya tür bilgisi ekleyin

**📋 {category} kategorisinden örnekler:**
{chr(10).join([f'• "{food} besin değerleri"' for food in foods[:3]])}

**🎯 Diğer popüler sorgular:**
• "protein açısından zengin besinler"
• "düşük kalorili atıştırmalıklar"  
• "karbonhidrat içermeyen yiyecekler"

**📊 Veritabanımızda 100+ Türk yemeği ve uluslararası besin bulunuyor!**

Hangi besin hakkında bilgi almak istiyorsunuz?
"""


class AIResponseParser:
    """AI yanıtlarından yapılandırılmış besin değerlerini çıkarır."""
    
    @staticmethod
    def extract_nutrition_data(ai_response: str) -> Optional[NutritionData]:
        """
        AI yanıtından besin değerlerini çıkar.
        
        Args:
            ai_response: AI'dan gelen yanıt
            
        Returns:
            Çıkarılan besin değerleri veya None
        """
        try:
            # JSON formatındaki besin değerlerini ara (HTML comment içinde gizli)
            json_pattern = r'<!--BESIN_DEĞERLERI_JSON:\s*({[^}]+})\s*-->'
            match = re.search(json_pattern, ai_response, re.DOTALL)
            
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                
                # Besin değerlerini doğrula
                nutrition_data = NutritionData(
                    food_name=data["food_name"],
                    calories_per_100g=float(data["calories_per_100g"]),
                    protein_per_100g=float(data["protein_per_100g"]),
                    carbs_per_100g=float(data["carbs_per_100g"]),
                    fat_per_100g=float(data["fat_per_100g"]),
                    confidence=data.get("confidence", "medium"),
                    source=data.get("source", "ai_assistant")
                )
                
                return nutrition_data
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Besin değerleri çıkarılamadı: {e}")
            return None
        
        return None
    
    @staticmethod
    def validate_nutrition_values(nutrition_data: NutritionData) -> bool:
        """
        Besin değerlerinin makul aralıkta olup olmadığını kontrol et.
        
        Args:
            nutrition_data: Doğrulanacak besin değerleri
            
        Returns:
            Değerler makul ise True
        """
        try:
            # Kalori kontrolü (0-900 kcal/100g)
            if not (0 <= nutrition_data.calories_per_100g <= 900):
                return False
            
            # Makro besin kontrolü (0-100g/100g)
            macros = [
                nutrition_data.protein_per_100g,
                nutrition_data.carbs_per_100g,
                nutrition_data.fat_per_100g
            ]
            
            for macro in macros:
                if not (0 <= macro <= 100):
                    return False
            
            # Toplam makro kontrolü (çok yüksek olmamalı)
            total_macros = sum(macros)
            if total_macros > 120:  # %20 tolerans
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Besin değerleri doğrulama hatası: {e}")
            return False


class AIAssistantService:
    """AI besin asistanı ana servisi."""
    
    def __init__(self):
        self.ai_model = LocalAIModel()
        self.parser = AIResponseParser()
        self._session_contexts: Dict[str, list[str]] = {}
    
    async def initialize(self) -> bool:
        """Servisi başlat."""
        return await self.ai_model.initialize()
    
    def is_available(self) -> bool:
        """Servisin kullanılabilir olup olmadığını kontrol et."""
        return self.ai_model.is_available()
    
    async def cleanup(self):
        """Servisi temizle ve kaynakları serbest bırak."""
        if hasattr(self.ai_model, 'web_searcher'):
            await self.ai_model.web_searcher.close_session()
        if hasattr(self.ai_model, 'web_scraper') and self.ai_model.web_scraper:
            await self.ai_model.web_scraper.cleanup()
    
    async def process_nutrition_query(
        self, 
        query: str, 
        session_id: str,
        user_id: int = 1
    ) -> Dict[str, Any]:
        """
        Besin değerleri sorgusunu işle.
        Önce Gemini AI'yı dene, başarısız olursa web scraping'e düş.
        """
        # Oturum bağlamını al
        context = self._get_session_context(session_id)

        # ── 1. Gemini AI ile dene ──────────────────────────────────────────
        try:
            from app.gemini_service import ask_nutrition_assistant, is_gemini_available
            logger.info(f"🤖 Gemini kullanılabilir mi: {is_gemini_available()}")
            if is_gemini_available():
                # Sohbet geçmişini Gemini formatına çevir
                gemini_history = []
                for i in range(0, len(context) - 1, 2):
                    if i + 1 < len(context):
                        user_msg = context[i].replace("Kullanıcı: ", "")
                        model_msg = context[i + 1].replace("Asistan: ", "")
                        gemini_history.append({"role": "user", "parts": [user_msg]})
                        gemini_history.append({"role": "model", "parts": [model_msg]})

                result = await ask_nutrition_assistant(query, gemini_history)

                if result["error"] is None:
                    # Besin verisini NutritionData schema'sına çevir
                    nutrition_data = None
                    if result["nutrition_data"]:
                        try:
                            from app.schemas import NutritionData
                            nd = result["nutrition_data"]
                            nutrition_data = NutritionData(
                                food_name=nd["food_name"],
                                calories_per_100g=min(nd["calories_per_100g"], 900),
                                protein_per_100g=min(nd["protein_per_100g"], 100),
                                carbs_per_100g=min(nd["carbs_per_100g"], 100),
                                fat_per_100g=min(nd["fat_per_100g"], 100),
                                confidence=nd.get("confidence", "medium"),
                                source="gemini_ai"
                            )
                        except Exception as e:
                            logger.warning(f"NutritionData dönüşüm hatası: {e}")

                    self._update_session_context(session_id, query, result["response"])
                    return {
                        "response": result["response"],
                        "nutrition_data": nutrition_data,
                        "error": None
                    }
        except Exception as e:
            logger.warning(f"Gemini denemesi başarısız, web scraping'e geçiliyor: {e}")

        # ── 2. Fallback: Mevcut web scraping sistemi ───────────────────────
        if not self.is_available():
            return {
                "response": "Üzgünüm, AI asistanı şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin.",
                "nutrition_data": None,
                "error": "AI modeli kullanılamıyor"
            }

        try:
            ai_response = await self.ai_model.generate_response(query, context)
            nutrition_data = self.parser.extract_nutrition_data(ai_response)

            if nutrition_data and not self.parser.validate_nutrition_values(nutrition_data):
                logger.warning(f"Geçersiz besin değerleri: {nutrition_data}")
                nutrition_data = None

            self._update_session_context(session_id, query, ai_response)

            return {
                "response": ai_response,
                "nutrition_data": nutrition_data,
                "error": None
            }

        except Exception as e:
            error_msg = f"AI sorgu işleme hatası: {str(e)}"
            logger.error(error_msg)
            return {
                "response": "Üzgünüm, sorgunuzu işlerken bir hata oluştu. Lütfen tekrar deneyin.",
                "nutrition_data": None,
                "error": error_msg
            }
    
    def _get_session_context(self, session_id: str) -> list[str]:
        """Oturum bağlamını al."""
        return self._session_contexts.get(session_id, [])
    
    def _update_session_context(self, session_id: str, query: str, response: str):
        """Oturum bağlamını güncelle (son 10 mesaj)."""
        if session_id not in self._session_contexts:
            self._session_contexts[session_id] = []
        
        context = self._session_contexts[session_id]
        context.append(f"Kullanıcı: {query}")
        context.append(f"Asistan: {response}")
        
        # Son 10 mesajı tut (5 soru-cevap çifti)
        if len(context) > 10:
            context = context[-10:]
        
        self._session_contexts[session_id] = context
    
    def clear_session_context(self, session_id: str):
        """Oturum bağlamını temizle."""
        if session_id in self._session_contexts:
            del self._session_contexts[session_id]


# Global AI asistan servisi instance
ai_assistant_service = AIAssistantService()


async def get_ai_assistant_service() -> AIAssistantService:
    """AI asistan servisini al (dependency injection için)."""
    if not ai_assistant_service.is_available():
        await ai_assistant_service.initialize()
    return ai_assistant_service