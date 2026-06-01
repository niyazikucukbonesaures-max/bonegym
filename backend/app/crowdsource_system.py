# Kullanıcı Katkılı Besin Veritabanı Sistemi
# API gerektirmeyen, topluluk bazlı veri toplama

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class UserContribution:
    """Kullanıcı katkısı veri yapısı."""
    user_id: int
    food_name: str
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    source: str  # "homemade", "restaurant", "package"
    photo_url: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    verified_by: List[int] = None  # Doğrulayan kullanıcı ID'leri
    confidence_score: float = 0.0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.verified_by is None:
            self.verified_by = []

@dataclass
class FoodSuggestion:
    """Besin önerisi veri yapısı."""
    food_name: str
    suggested_by: int
    votes: int = 0
    voters: List[int] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.voters is None:
            self.voters = []

class CrowdsourceSystem:
    """
    Kullanıcı katkılı besin veritabanı sistemi.
    API gerektirmeyen, topluluk bazlı veri toplama.
    """
    
    def __init__(self):
        self.contributions = []
        self.suggestions = []
        self.verification_queue = []
        
        # Gamification sistemi
        self.user_points = {}
        self.leaderboard = []
        
        # Popüler eksik besinler listesi
        self.missing_foods_requests = {}
        
        # Türk mutfağı kategorileri
        self.turkish_categories = {
            "börek_çeşitleri": [
                "kıymalı börek", "peynirli börek", "ıspanaklı börek", 
                "patatesli börek", "mantarlı börek", "pıtrıklı börek"
            ],
            "kebap_çeşitleri": [
                "adana kebap", "urfa kebap", "beyti kebap", "şiş kebap",
                "döner kebap", "iskender kebap", "ali nazik kebap"
            ],
            "çorba_çeşitleri": [
                "mercimek çorbası", "yayla çorbası", "tarhana çorbası",
                "ezogelin çorbası", "domates çorbası", "tavuk çorbası"
            ],
            "tatlı_çeşitleri": [
                "baklava", "künefe", "tulumba", "lokma", "revani",
                "sütlaç", "muhallebi", "kazandibi", "aşure"
            ],
            "ev_yemekleri": [
                "karnıyarık", "imam bayıldı", "dolma", "sarma",
                "menemen", "çılbır", "sucuklu yumurta", "türlü"
            ]
        }
    
    async def add_user_contribution(self, contribution: UserContribution) -> bool:
        """Kullanıcı katkısı ekle."""
        try:
            # Temel validasyon
            if not self._validate_contribution(contribution):
                return False
            
            # Benzer katkı var mı kontrol et
            existing = await self._find_similar_contribution(contribution)
            if existing:
                # Mevcut katkıyı güncelle
                await self._merge_contributions(existing, contribution)
            else:
                # Yeni katkı ekle
                self.contributions.append(contribution)
            
            # Kullanıcıya puan ver
            await self._award_points(contribution.user_id, "contribution", 10)
            
            # Doğrulama kuyruğuna ekle
            self.verification_queue.append(contribution)
            
            logger.info(f"✅ Kullanıcı katkısı eklendi: {contribution.food_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Katkı ekleme hatası: {e}")
            return False
    
    def _validate_contribution(self, contribution: UserContribution) -> bool:
        """Katkıyı doğrula."""
        # Besin değerleri makul aralıkta mı?
        if not (0 <= contribution.calories_per_100g <= 900):
            return False
        if not (0 <= contribution.protein_per_100g <= 100):
            return False
        if not (0 <= contribution.carbs_per_100g <= 100):
            return False
        if not (0 <= contribution.fat_per_100g <= 100):
            return False
        
        # Besin adı geçerli mi?
        if not contribution.food_name or len(contribution.food_name.strip()) < 3:
            return False
        
        return True
    
    async def _find_similar_contribution(self, contribution: UserContribution) -> Optional[UserContribution]:
        """Benzer katkı bul."""
        food_name_lower = contribution.food_name.lower()
        
        for existing in self.contributions:
            existing_name_lower = existing.food_name.lower()
            
            # Tam eşleşme
            if food_name_lower == existing_name_lower:
                return existing
            
            # Benzer isim (Levenshtein distance < 3)
            if self._calculate_similarity(food_name_lower, existing_name_lower) > 0.8:
                return existing
        
        return None
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """İki string arasındaki benzerlik oranını hesapla."""
        # Basit Jaccard similarity
        set1 = set(str1.split())
        set2 = set(str2.split())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0
    
    async def _merge_contributions(self, existing: UserContribution, new: UserContribution):
        """İki katkıyı birleştir."""
        # Ortalama değerleri hesapla
        weight_existing = len(existing.verified_by) + 1
        weight_new = 1
        total_weight = weight_existing + weight_new
        
        existing.calories_per_100g = (
            existing.calories_per_100g * weight_existing + 
            new.calories_per_100g * weight_new
        ) / total_weight
        
        existing.protein_per_100g = (
            existing.protein_per_100g * weight_existing + 
            new.protein_per_100g * weight_new
        ) / total_weight
        
        existing.carbs_per_100g = (
            existing.carbs_per_100g * weight_existing + 
            new.carbs_per_100g * weight_new
        ) / total_weight
        
        existing.fat_per_100g = (
            existing.fat_per_100g * weight_existing + 
            new.fat_per_100g * weight_new
        ) / total_weight
        
        # Confidence score'u artır
        existing.confidence_score = min(existing.confidence_score + 0.1, 1.0)
    
    async def verify_contribution(self, contribution_id: int, verifier_user_id: int, is_correct: bool) -> bool:
        """Katkıyı doğrula."""
        try:
            contribution = self.contributions[contribution_id]
            
            # Kullanıcı daha önce doğrulamış mı?
            if verifier_user_id in contribution.verified_by:
                return False
            
            if is_correct:
                contribution.verified_by.append(verifier_user_id)
                contribution.confidence_score += 0.2
                
                # Doğrulayıcıya puan ver
                await self._award_points(verifier_user_id, "verification", 5)
                
                # Katkı sahibine bonus puan
                await self._award_points(contribution.user_id, "verified_contribution", 5)
            else:
                # Yanlış doğrulama - confidence score düşür
                contribution.confidence_score = max(contribution.confidence_score - 0.1, 0)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Doğrulama hatası: {e}")
            return False
    
    async def suggest_missing_food(self, user_id: int, food_name: str) -> bool:
        """Eksik besin önerisi yap."""
        try:
            # Mevcut önerilerde var mı?
            for suggestion in self.suggestions:
                if suggestion.food_name.lower() == food_name.lower():
                    # Oy ver
                    if user_id not in suggestion.voters:
                        suggestion.votes += 1
                        suggestion.voters.append(user_id)
                        await self._award_points(user_id, "vote", 2)
                    return True
            
            # Yeni öneri oluştur
            suggestion = FoodSuggestion(
                food_name=food_name,
                suggested_by=user_id,
                votes=1,
                voters=[user_id]
            )
            
            self.suggestions.append(suggestion)
            await self._award_points(user_id, "suggestion", 5)
            
            logger.info(f"✅ Yeni besin önerisi: {food_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Öneri ekleme hatası: {e}")
            return False
    
    async def _award_points(self, user_id: int, action: str, points: int):
        """Kullanıcıya puan ver."""
        if user_id not in self.user_points:
            self.user_points[user_id] = {
                "total_points": 0,
                "contributions": 0,
                "verifications": 0,
                "suggestions": 0,
                "level": 1,
                "badges": []
            }
        
        user_data = self.user_points[user_id]
        user_data["total_points"] += points
        
        # Aksiyon tipine göre sayaç artır
        if action == "contribution":
            user_data["contributions"] += 1
        elif action == "verification":
            user_data["verifications"] += 1
        elif action == "suggestion":
            user_data["suggestions"] += 1
        
        # Seviye hesapla
        new_level = min(user_data["total_points"] // 100 + 1, 10)
        if new_level > user_data["level"]:
            user_data["level"] = new_level
            await self._award_badge(user_id, f"level_{new_level}")
        
        # Özel rozetler
        if user_data["contributions"] >= 10 and "contributor" not in user_data["badges"]:
            await self._award_badge(user_id, "contributor")
        
        if user_data["verifications"] >= 50 and "verifier" not in user_data["badges"]:
            await self._award_badge(user_id, "verifier")
    
    async def _award_badge(self, user_id: int, badge: str):
        """Kullanıcıya rozet ver."""
        if user_id in self.user_points:
            self.user_points[user_id]["badges"].append(badge)
            logger.info(f"🏆 Kullanıcı {user_id} '{badge}' rozeti kazandı!")
    
    async def get_popular_missing_foods(self, limit: int = 20) -> List[Dict[str, Any]]:
        """En çok istenen eksik besinleri getir."""
        # Önerileri oy sayısına göre sırala
        sorted_suggestions = sorted(
            self.suggestions, 
            key=lambda x: x.votes, 
            reverse=True
        )
        
        return [
            {
                "food_name": s.food_name,
                "votes": s.votes,
                "suggested_by": s.suggested_by,
                "days_ago": (datetime.now() - s.created_at).days
            }
            for s in sorted_suggestions[:limit]
        ]
    
    async def get_user_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Kullanıcı liderlik tablosu."""
        # Puanlara göre sırala
        sorted_users = sorted(
            self.user_points.items(),
            key=lambda x: x[1]["total_points"],
            reverse=True
        )
        
        return [
            {
                "user_id": user_id,
                "total_points": data["total_points"],
                "level": data["level"],
                "contributions": data["contributions"],
                "badges": data["badges"]
            }
            for user_id, data in sorted_users[:limit]
        ]
    
    async def get_verification_queue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Doğrulama bekleyen katkılar."""
        # Confidence score'u düşük olanları öncelikle
        queue = sorted(
            self.verification_queue,
            key=lambda x: x.confidence_score
        )
        
        return [
            {
                "id": i,
                "food_name": contrib.food_name,
                "calories": contrib.calories_per_100g,
                "protein": contrib.protein_per_100g,
                "carbs": contrib.carbs_per_100g,
                "fat": contrib.fat_per_100g,
                "source": contrib.source,
                "confidence": contrib.confidence_score,
                "verifications_needed": max(3 - len(contrib.verified_by), 0)
            }
            for i, contrib in enumerate(queue[:limit])
        ]
    
    async def generate_daily_challenges(self) -> List[Dict[str, Any]]:
        """Günlük challenge'lar üret."""
        challenges = []
        
        # Popüler kategorilerden eksik besinler
        for category, foods in self.turkish_categories.items():
            missing_foods = []
            for food in foods:
                # Bu besin veritabanında var mı kontrol et
                exists = any(
                    contrib.food_name.lower() == food.lower() 
                    for contrib in self.contributions
                )
                if not exists:
                    missing_foods.append(food)
            
            if missing_foods:
                challenges.append({
                    "type": "add_missing_food",
                    "category": category,
                    "food_suggestions": missing_foods[:3],
                    "reward_points": 20,
                    "description": f"{category.replace('_', ' ').title()} kategorisinden eksik besinleri ekle"
                })
        
        # Doğrulama challenge'ı
        if len(self.verification_queue) > 5:
            challenges.append({
                "type": "verify_contributions",
                "target": 5,
                "reward_points": 15,
                "description": "5 besin katkısını doğrula"
            })
        
        return challenges[:3]  # En fazla 3 challenge

# Global instance
crowdsource_system = CrowdsourceSystem()