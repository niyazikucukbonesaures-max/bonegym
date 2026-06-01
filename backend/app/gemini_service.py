# Gemini AI Servisi
# Google Gemini API entegrasyonu — besin asistanı ve antrenman koçu için

import os
import json
import logging
import re
import time
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path
from collections import defaultdict

# .env dosyasını yükle — backend/ klasöründen ara
_env_path = Path(__file__).parent.parent / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv yoksa ortam değişkenlerini doğrudan kullan

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory cache — aynı besin sorusu tekrar sorulursa API çağrısı yapma
# ---------------------------------------------------------------------------

_response_cache: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL = 24 * 60 * 60  # 24 saat (saniye)
_MAX_CACHE_SIZE = 1000       # Maksimum cache girişi

def _cache_key(text: str) -> str:
    """Sorgu metninden cache anahtarı üret."""
    normalized = text.lower().strip()
    return hashlib.md5(normalized.encode()).hexdigest()

def _get_cached(key: str) -> Optional[Dict[str, Any]]:
    """Cache'den yanıt al, süresi dolmuşsa None döndür."""
    entry = _response_cache.get(key)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
        return entry["data"]
    if entry:
        del _response_cache[key]
    return None

def _set_cache(key: str, data: Dict[str, Any]) -> None:
    """Cache'e yanıt kaydet, boyut limitini aş."""
    if len(_response_cache) >= _MAX_CACHE_SIZE:
        # En eski girişi sil
        oldest = min(_response_cache, key=lambda k: _response_cache[k]["ts"])
        del _response_cache[oldest]
    _response_cache[key] = {"data": data, "ts": time.time()}

# ---------------------------------------------------------------------------
# Rate limiting — kullanıcı başına dakikada max istek
# ---------------------------------------------------------------------------

_rate_limit_store: Dict[str, list] = defaultdict(list)
_RATE_LIMIT_PER_MINUTE = 10  # Kullanıcı başına dakikada max AI isteği

def _check_rate_limit(user_id: int) -> bool:
    """True döndürürse istek kabul edilir, False ise reddedilir."""
    now = time.time()
    window_start = now - 60  # Son 1 dakika
    
    # Eski istekleri temizle
    _rate_limit_store[user_id] = [
        ts for ts in _rate_limit_store[user_id] if ts > window_start
    ]
    
    if len(_rate_limit_store[user_id]) >= _RATE_LIMIT_PER_MINUTE:
        return False
    
    _rate_limit_store[user_id].append(now)
    return True

# ---------------------------------------------------------------------------
# Gemini istemcisi
# ---------------------------------------------------------------------------

_gemini_client = None

# Model öncelik sırası: en az kota tüketen → en yetenekli
GEMINI_MODELS = [
    "gemini-2.0-flash-lite",   # En az kota, önce dene
    "gemini-2.5-flash-lite",   # Orta kota
    "gemini-2.5-flash",        # Yüksek kota, son çare
]

def _get_gemini_client():
    """Gemini istemcisini al veya oluştur (lazy init)."""
    global _gemini_client

    if _gemini_client is not None:
        return _gemini_client

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        logger.warning("⚠️  GEMINI_API_KEY ayarlanmamış — Gemini devre dışı")
        return None

    try:
        from google import genai
        _gemini_client = genai.Client(api_key=api_key)
        logger.info("✅ Gemini istemcisi başarıyla başlatıldı")
        return _gemini_client
    except Exception as e:
        logger.error(f"❌ Gemini başlatma hatası: {e}")
        return None


def is_gemini_available() -> bool:
    """Gemini'nin kullanılabilir olup olmadığını kontrol et."""
    return _get_gemini_client() is not None


async def _generate_with_fallback(
    contents,
    system_instruction: str,
    temperature: float = 0.3,
    max_output_tokens: int = 1024,
) -> str:
    """
    Model fallback zinciriyle içerik üret.
    429 alınca bir sonraki modele geç.
    """
    client = _get_gemini_client()
    if client is None:
        raise RuntimeError("Gemini istemcisi başlatılamadı")

    from google import genai
    from google.genai import types

    last_error = None
    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                )
            )
            logger.info(f"✅ Gemini yanıt aldı ({model_name})")
            return response.text
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                logger.warning(f"⚠️  {model_name} kota doldu, sonraki modele geçiliyor...")
                last_error = e
                continue
            else:
                raise  # 429 dışı hata — direkt fırlat

    raise RuntimeError(f"Tüm Gemini modelleri kota doldu: {last_error}")


# ---------------------------------------------------------------------------
# Besin Asistanı
# ---------------------------------------------------------------------------

NUTRITION_SYSTEM_PROMPT = """Sen bir Türk fitness ve beslenme uzmanısın. Kullanıcıların besin değerleri hakkındaki sorularını yanıtlıyorsun.

KURALLAR:
1. Her zaman Türkçe yanıt ver
2. Besin değerlerini 100g başına ver
3. Yanıtın sonuna mutlaka JSON bloğu ekle (besin değerleri içeriyorsa)
4. JSON formatı tam olarak şu şekilde olmalı:

```json
{
  "food_name": "besin adı",
  "calories_per_100g": 000,
  "protein_per_100g": 00.0,
  "carbs_per_100g": 00.0,
  "fat_per_100g": 00.0,
  "confidence": "high"
}
```

5. confidence değeri: "high" (kesin bilgi), "medium" (tahmini), "low" (belirsiz)
6. Eğer soru besin değerleriyle ilgili değilse JSON ekleme
7. Kısa ve net yanıtlar ver, gereksiz uzatma
8. Türk mutfağı besinlerini iyi biliyorsun (köfte, pilav, börek, döner vb.)"""


async def ask_nutrition_assistant(
    message: str,
    conversation_history: list[dict] = None,
    user_id: int = 0
) -> Dict[str, Any]:
    """
    Besin asistanına soru sor.
    Cache: aynı soru 24 saat içinde tekrar sorulursa API çağrısı yapılmaz.
    Rate limit: kullanıcı başına dakikada max 10 istek.
    """
    client = _get_gemini_client()
    if client is None:
        return {
            "response": "AI servisi şu anda kullanılamıyor. API anahtarını kontrol edin.",
            "nutrition_data": None,
            "error": "Gemini API anahtarı ayarlanmamış"
        }

    # Rate limit kontrolü (sohbet geçmişi olmayan ilk sorular için)
    if user_id and not conversation_history:
        if not _check_rate_limit(user_id):
            return {
                "response": "Çok fazla istek gönderdiniz. Lütfen 1 dakika bekleyin.",
                "nutrition_data": None,
                "error": "rate_limit_exceeded"
            }

    # Cache kontrolü (sohbet geçmişi yoksa cache kullan)
    cache_key = None
    if not conversation_history:
        cache_key = _cache_key(message)
        cached = _get_cached(cache_key)
        if cached:
            logger.debug(f"Cache hit: {message[:50]}")
            return cached

    try:
        from google import genai
        from google.genai import types

        # Sohbet geçmişini oluştur
        history = conversation_history or []
        contents = []

        # Önceki mesajları ekle
        for msg in history:
            role = msg.get("role", "user")
            parts = msg.get("parts", [""])
            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=p) for p in parts]
            ))

        # Yeni kullanıcı mesajını ekle
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=message)]
        ))

        response_text = await _generate_with_fallback(
            contents=contents,
            system_instruction=NUTRITION_SYSTEM_PROMPT,
            temperature=0.3,
        )

        nutrition_data = _extract_nutrition_json(response_text)

        result = {
            "response": response_text,
            "nutrition_data": nutrition_data,
            "error": None
        }

        # Cache'e kaydet (sohbet geçmişi yoksa)
        if cache_key:
            _set_cache(cache_key, result)

        return result

    except Exception as e:
        logger.error(f"Gemini besin asistanı hatası: {e}")
        return {
            "response": "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.",
            "nutrition_data": None,
            "error": str(e)
        }


# ---------------------------------------------------------------------------
# Antrenman Koçu
# ---------------------------------------------------------------------------

COACH_SYSTEM_PROMPT = """Sen bir Türk fitness koçusun. Kullanıcının günlük kalori verilerine, profiline ve FITNESS SEVİYESİNE bakarak antrenman önerileri yapıyorsun.

KURALLAR:
1. Her zaman Türkçe yanıt ver
2. Kısa, motive edici ve pratik öneriler ver
3. Kullanıcının hedefine (kilo verme/kas kazanma/koruma) göre öner
4. **FITNESS SEVİYESİNE GÖRE UYARLA:**
   - beginner (yeni başlayan): Hafif ağırlıklar, temel hareketler, kısa süreler (20-35 dk), düşük-orta yoğunluk. Squat/deadlift gibi ağır bileşik hareketler YOK. Vücut ağırlığı ve hafif dumbbell egzersizleri.
   - intermediate (orta seviye): Orta ağırlıklar, bileşik hareketler dahil, 35-55 dk, orta-yüksek yoğunluk.
   - advanced (ileri seviye): Ağır bileşik hareketler, yüksek yoğunluk, 45-75 dk.
5. Antrenman planı önerirken JSON formatında ver:

```json
{
  "workout_type": "strength|cardio|hiit|rest|light|beginner_full_body",
  "duration_minutes": 30,
  "intensity": "low|moderate|high",
  "exercises": ["Egzersiz 1", "Egzersiz 2"],
  "motivation": "Motivasyon mesajı"
}
```

6. Eğer dinlenme günü öneriyorsan workout_type = "rest" yap
7. Kalori açığı/fazlası durumuna göre yoğunluğu ayarla
8. Yeni başlayanlar için asla ağır barbell squat, deadlift, bench press önerme"""


async def ask_workout_coach(
    user_profile: Dict[str, Any],
    daily_calories: float,
    target_calories: float,
    message: str = None
) -> Dict[str, Any]:
    """Antrenman koçuna sor."""
    client = _get_gemini_client()
    if client is None:
        return {
            "response": "AI koç servisi şu anda kullanılamıyor.",
            "workout_plan": None,
            "error": "Gemini API anahtarı ayarlanmamış"
        }

    try:
        goal_map = {
            "lose": "kilo verme", "kilo_verme": "kilo verme",
            "gain": "kas kazanma", "kas_kazanma": "kas kazanma",
            "maintain": "kilo koruma", "koruma": "kilo koruma",
            "recomp": "vücut rekomposizyonu", "vucut_rekomposizyonu": "vücut rekomposizyonu",
        }
        goal = goal_map.get(user_profile.get("goal", "maintain"), "kilo koruma")
        calorie_diff = daily_calories - target_calories
        calorie_status = (
            f"{abs(calorie_diff):.0f} kcal açık" if calorie_diff < -50
            else f"{calorie_diff:.0f} kcal fazla" if calorie_diff > 50
            else "hedefe yakın"
        )

        fitness_level = user_profile.get("fitness_level", "beginner")
        fitness_level_map = {
            "beginner": "Yeni başlayan (0-6 ay deneyim)",
            "intermediate": "Orta seviye (6 ay - 2 yıl deneyim)",
            "advanced": "İleri seviye (2+ yıl deneyim)",
        }
        fitness_label = fitness_level_map.get(fitness_level, "Yeni başlayan")

        context = f"""Kullanıcı profili:
- Hedef: {goal}
- Fitness seviyesi: {fitness_label}
- Kilo: {user_profile.get('weight_kg', '?')} kg
- Boy: {user_profile.get('height_cm', '?')} cm
- Aktivite: {user_profile.get('activity_level', 'moderate')}
- Bugünkü kalori: {daily_calories:.0f} kcal (hedef: {target_calories:.0f} kcal, durum: {calorie_status})

{message or 'Bugün için antrenman önerisi ver. Fitness seviyesine uygun egzersizler seç.'}"""

        response_text = await _generate_with_fallback(
            contents=context,
            system_instruction=COACH_SYSTEM_PROMPT,
            temperature=0.4,
        )

        workout_plan = _extract_workout_json(response_text)

        return {
            "response": response_text,
            "workout_plan": workout_plan,
            "error": None
        }

    except Exception as e:
        logger.error(f"Gemini antrenman koçu hatası: {e}")
        return {
            "response": "Antrenman önerisi alınırken hata oluştu.",
            "workout_plan": None,
            "error": str(e)
        }


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def _extract_nutrition_json(text: str) -> Optional[Dict[str, Any]]:
    """Yanıt metninden besin değerleri JSON'ını çıkar."""
    try:
        # ```json ... ``` bloğunu ara
        pattern = r'```json\s*([\s\S]*?)\s*```'
        match = re.search(pattern, text)
        if match:
            data = json.loads(match.group(1))
            # Gerekli alanları kontrol et
            required = ["food_name", "calories_per_100g", "protein_per_100g",
                       "carbs_per_100g", "fat_per_100g"]
            if all(k in data for k in required):
                # Değerleri float'a çevir
                return {
                    "food_name": str(data["food_name"]),
                    "calories_per_100g": float(data["calories_per_100g"]),
                    "protein_per_100g": float(data["protein_per_100g"]),
                    "carbs_per_100g": float(data["carbs_per_100g"]),
                    "fat_per_100g": float(data["fat_per_100g"]),
                    "confidence": str(data.get("confidence", "medium")),
                    "source": "gemini_ai"
                }
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.debug(f"JSON çıkarma hatası: {e}")
    return None


def _extract_workout_json(text: str) -> Optional[Dict[str, Any]]:
    """Yanıt metninden antrenman planı JSON'ını çıkar."""
    try:
        pattern = r'```json\s*([\s\S]*?)\s*```'
        match = re.search(pattern, text)
        if match:
            data = json.loads(match.group(1))
            if "workout_type" in data:
                return data
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.debug(f"Antrenman JSON çıkarma hatası: {e}")
    return None
