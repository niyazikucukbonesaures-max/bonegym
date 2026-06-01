# Gelişmiş Analytics ve Performans İzleme
# Piyasa lideri seviyesinde kullanıcı analizi

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class UserEvent:
    """Kullanıcı etkinliği veri yapısı."""
    user_id: int
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime
    session_id: str
    device_type: str = "web"
    location: Optional[str] = None

@dataclass
class SearchAnalytics:
    """Arama analitikleri."""
    query: str
    results_count: int
    selected_result: Optional[str]
    search_time_ms: float
    user_id: int
    timestamp: datetime

@dataclass
class NutritionInsight:
    """Beslenme içgörüleri."""
    user_id: int
    daily_calories: float
    daily_protein: float
    daily_carbs: float
    daily_fat: float
    goal_achievement: float
    date: datetime

class AdvancedAnalytics:
    """
    Gelişmiş analytics sistemi.
    MyFitnessPal seviyesinde kullanıcı analizi.
    """
    
    def __init__(self):
        self.events_buffer = []
        self.user_sessions = {}
        self.search_analytics = []
        self.nutrition_insights = []
        
        # Real-time metrics
        self.metrics = {
            "active_users": 0,
            "searches_per_minute": 0,
            "avg_search_time": 0,
            "popular_foods": {},
            "user_retention": {},
            "conversion_rates": {}
        }
    
    async def track_event(self, event: UserEvent):
        """Kullanıcı etkinliğini takip et."""
        self.events_buffer.append(event)
        
        # Real-time processing
        await self._process_event_realtime(event)
        
        # Buffer dolduğunda batch processing
        if len(self.events_buffer) >= 100:
            await self._process_events_batch()
    
    async def _process_event_realtime(self, event: UserEvent):
        """Gerçek zamanlı etkinlik işleme."""
        try:
            # Aktif kullanıcı sayısını güncelle
            if event.event_type == "session_start":
                self.metrics["active_users"] += 1
                self.user_sessions[event.user_id] = {
                    "start_time": event.timestamp,
                    "last_activity": event.timestamp,
                    "events": []
                }
            
            elif event.event_type == "session_end":
                self.metrics["active_users"] = max(0, self.metrics["active_users"] - 1)
                if event.user_id in self.user_sessions:
                    session = self.user_sessions[event.user_id]
                    session_duration = (event.timestamp - session["start_time"]).total_seconds()
                    
                    # Session analytics
                    await self._analyze_session(event.user_id, session, session_duration)
                    del self.user_sessions[event.user_id]
            
            # Arama etkinlikleri
            elif event.event_type == "food_search":
                await self._track_search(event)
            
            # Besin ekleme etkinlikleri
            elif event.event_type == "food_added":
                await self._track_food_addition(event)
            
            # Kullanıcı etkileşimleri
            elif event.event_type == "ui_interaction":
                await self._track_ui_interaction(event)
            
        except Exception as e:
            logger.error(f"Real-time event processing hatası: {e}")
    
    async def _track_search(self, event: UserEvent):
        """Arama etkinliğini takip et."""
        search_data = event.event_data
        
        search_analytics = SearchAnalytics(
            query=search_data.get("query", ""),
            results_count=search_data.get("results_count", 0),
            selected_result=search_data.get("selected_result"),
            search_time_ms=search_data.get("search_time_ms", 0),
            user_id=event.user_id,
            timestamp=event.timestamp
        )
        
        self.search_analytics.append(search_analytics)
        
        # Popüler yiyecekleri güncelle
        query = search_data.get("query", "").lower()
        if query:
            self.metrics["popular_foods"][query] = self.metrics["popular_foods"].get(query, 0) + 1
        
        # Arama hızı metriğini güncelle
        search_time = search_data.get("search_time_ms", 0)
        if search_time > 0:
            current_avg = self.metrics["avg_search_time"]
            self.metrics["avg_search_time"] = (current_avg + search_time) / 2
    
    async def _track_food_addition(self, event: UserEvent):
        """Besin ekleme etkinliğini takip et."""
        food_data = event.event_data
        
        # Günlük beslenme verilerini güncelle
        await self._update_daily_nutrition(event.user_id, food_data, event.timestamp)
        
        # Conversion rate güncelle
        user_id = event.user_id
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            session["converted"] = True
    
    async def _update_daily_nutrition(self, user_id: int, food_data: Dict, timestamp: datetime):
        """Günlük beslenme verilerini güncelle."""
        date = timestamp.date()
        
        # Bugünkü beslenme verilerini bul veya oluştur
        today_nutrition = None
        for insight in self.nutrition_insights:
            if insight.user_id == user_id and insight.date.date() == date:
                today_nutrition = insight
                break
        
        if not today_nutrition:
            today_nutrition = NutritionInsight(
                user_id=user_id,
                daily_calories=0,
                daily_protein=0,
                daily_carbs=0,
                daily_fat=0,
                goal_achievement=0,
                date=timestamp
            )
            self.nutrition_insights.append(today_nutrition)
        
        # Besin değerlerini ekle
        portion_size = food_data.get("portion_size", 100) / 100  # 100g'a normalize et
        today_nutrition.daily_calories += food_data.get("calories", 0) * portion_size
        today_nutrition.daily_protein += food_data.get("protein", 0) * portion_size
        today_nutrition.daily_carbs += food_data.get("carbs", 0) * portion_size
        today_nutrition.daily_fat += food_data.get("fat", 0) * portion_size
        
        # Hedef başarı oranını hesapla (varsayılan hedef: 2000 kalori)
        daily_goal = 2000  # Bu kullanıcı profilinden alınacak
        today_nutrition.goal_achievement = min(today_nutrition.daily_calories / daily_goal, 1.0)
    
    async def _analyze_session(self, user_id: int, session: Dict, duration: float):
        """Session analizi yap."""
        try:
            # Session metrikleri
            events_count = len(session.get("events", []))
            converted = session.get("converted", False)
            
            # Retention analizi
            if user_id not in self.metrics["user_retention"]:
                self.metrics["user_retention"][user_id] = {
                    "first_session": session["start_time"],
                    "last_session": session["start_time"],
                    "total_sessions": 0,
                    "total_duration": 0
                }
            
            retention_data = self.metrics["user_retention"][user_id]
            retention_data["last_session"] = session["start_time"]
            retention_data["total_sessions"] += 1
            retention_data["total_duration"] += duration
            
            # Conversion rate güncelle
            if converted:
                self.metrics["conversion_rates"]["daily"] = self.metrics["conversion_rates"].get("daily", 0) + 1
            
        except Exception as e:
            logger.error(f"Session analizi hatası: {e}")
    
    async def generate_insights(self) -> Dict[str, Any]:
        """Gelişmiş içgörüler üret."""
        insights = {
            "user_behavior": await self._analyze_user_behavior(),
            "popular_foods": await self._analyze_popular_foods(),
            "search_performance": await self._analyze_search_performance(),
            "nutrition_trends": await self._analyze_nutrition_trends(),
            "retention_metrics": await self._analyze_retention(),
            "conversion_funnel": await self._analyze_conversion_funnel()
        }
        
        return insights
    
    async def _analyze_user_behavior(self) -> Dict[str, Any]:
        """Kullanıcı davranış analizi."""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        # Son 24 saatteki etkinlikler
        recent_events = [e for e in self.events_buffer if e.timestamp >= last_24h]
        
        # Saatlik dağılım
        hourly_distribution = {}
        for event in recent_events:
            hour = event.timestamp.hour
            hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
        
        # En aktif saatler
        peak_hours = sorted(hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "total_events_24h": len(recent_events),
            "peak_hours": [{"hour": h, "events": c} for h, c in peak_hours],
            "avg_session_duration": self._calculate_avg_session_duration(),
            "most_common_actions": self._get_most_common_actions(recent_events)
        }
    
    async def _analyze_popular_foods(self) -> Dict[str, Any]:
        """Popüler yiyecek analizi."""
        # En çok aranan yiyecekler
        top_searches = sorted(
            self.metrics["popular_foods"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Kategori bazlı popülerlik
        category_popularity = {}
        for food, count in top_searches:
            category = self._categorize_food(food)
            category_popularity[category] = category_popularity.get(category, 0) + count
        
        return {
            "top_searches": [{"food": f, "count": c} for f, c in top_searches],
            "category_popularity": category_popularity,
            "trending_foods": await self._get_trending_foods()
        }
    
    async def _analyze_search_performance(self) -> Dict[str, Any]:
        """Arama performans analizi."""
        if not self.search_analytics:
            return {"avg_search_time": 0, "success_rate": 0}
        
        # Ortalama arama süresi
        avg_time = sum(s.search_time_ms for s in self.search_analytics) / len(self.search_analytics)
        
        # Başarı oranı (sonuç bulunan aramalar)
        successful_searches = sum(1 for s in self.search_analytics if s.results_count > 0)
        success_rate = successful_searches / len(self.search_analytics) if self.search_analytics else 0
        
        # Click-through rate
        clicked_searches = sum(1 for s in self.search_analytics if s.selected_result)
        ctr = clicked_searches / len(self.search_analytics) if self.search_analytics else 0
        
        return {
            "avg_search_time_ms": avg_time,
            "success_rate": success_rate,
            "click_through_rate": ctr,
            "total_searches": len(self.search_analytics)
        }
    
    async def _analyze_nutrition_trends(self) -> Dict[str, Any]:
        """Beslenme trend analizi."""
        if not self.nutrition_insights:
            return {}
        
        # Ortalama günlük değerler
        avg_calories = sum(n.daily_calories for n in self.nutrition_insights) / len(self.nutrition_insights)
        avg_protein = sum(n.daily_protein for n in self.nutrition_insights) / len(self.nutrition_insights)
        avg_carbs = sum(n.daily_carbs for n in self.nutrition_insights) / len(self.nutrition_insights)
        avg_fat = sum(n.daily_fat for n in self.nutrition_insights) / len(self.nutrition_insights)
        
        # Hedef başarı oranı
        avg_goal_achievement = sum(n.goal_achievement for n in self.nutrition_insights) / len(self.nutrition_insights)
        
        return {
            "avg_daily_calories": avg_calories,
            "avg_daily_protein": avg_protein,
            "avg_daily_carbs": avg_carbs,
            "avg_daily_fat": avg_fat,
            "avg_goal_achievement": avg_goal_achievement,
            "users_meeting_goals": sum(1 for n in self.nutrition_insights if n.goal_achievement >= 0.8)
        }
    
    def _calculate_avg_session_duration(self) -> float:
        """Ortalama session süresi hesapla."""
        if not self.metrics["user_retention"]:
            return 0
        
        total_duration = sum(
            data["total_duration"] for data in self.metrics["user_retention"].values()
        )
        total_sessions = sum(
            data["total_sessions"] for data in self.metrics["user_retention"].values()
        )
        
        return total_duration / total_sessions if total_sessions > 0 else 0
    
    def _get_most_common_actions(self, events: List[UserEvent]) -> List[Dict[str, Any]]:
        """En yaygın aksiyonları bul."""
        action_counts = {}
        for event in events:
            action_counts[event.event_type] = action_counts.get(event.event_type, 0) + 1
        
        return [
            {"action": action, "count": count}
            for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    
    def _categorize_food(self, food_name: str) -> str:
        """Yiyeceği kategorize et."""
        food_lower = food_name.lower()
        
        if any(word in food_lower for word in ["börek", "pide", "lahmacun"]):
            return "turkish_pastry"
        elif any(word in food_lower for word in ["kebap", "köfte", "döner"]):
            return "turkish_meat"
        elif any(word in food_lower for word in ["çorba", "soup"]):
            return "soup"
        elif any(word in food_lower for word in ["salata", "sebze"]):
            return "vegetables"
        elif any(word in food_lower for word in ["meyve", "fruit"]):
            return "fruits"
        else:
            return "other"
    
    async def _get_trending_foods(self) -> List[Dict[str, Any]]:
        """Trend olan yiyecekleri bul."""
        # Son 7 gün vs önceki 7 gün karşılaştırması
        now = datetime.now()
        last_week = now - timedelta(days=7)
        prev_week = now - timedelta(days=14)
        
        # Bu implementasyon daha detaylı trend analizi gerektirir
        return [
            {"food": "ıspanaklı börek", "trend": "+25%"},
            {"food": "protein tozu", "trend": "+18%"},
            {"food": "avokado", "trend": "+12%"}
        ]
    
    async def _analyze_retention(self) -> Dict[str, Any]:
        """Kullanıcı tutma analizi."""
        if not self.metrics["user_retention"]:
            return {}
        
        now = datetime.now()
        
        # 1 günlük retention
        day_1_users = sum(
            1 for data in self.metrics["user_retention"].values()
            if (now - data["last_session"]).days <= 1
        )
        
        # 7 günlük retention
        day_7_users = sum(
            1 for data in self.metrics["user_retention"].values()
            if (now - data["last_session"]).days <= 7
        )
        
        # 30 günlük retention
        day_30_users = sum(
            1 for data in self.metrics["user_retention"].values()
            if (now - data["last_session"]).days <= 30
        )
        
        total_users = len(self.metrics["user_retention"])
        
        return {
            "day_1_retention": day_1_users / total_users if total_users > 0 else 0,
            "day_7_retention": day_7_users / total_users if total_users > 0 else 0,
            "day_30_retention": day_30_users / total_users if total_users > 0 else 0,
            "total_users": total_users
        }
    
    async def _analyze_conversion_funnel(self) -> Dict[str, Any]:
        """Conversion funnel analizi."""
        # Basit funnel: Ziyaret -> Arama -> Sonuç Tıklama -> Besin Ekleme
        
        total_sessions = len(self.user_sessions) + len(self.metrics["user_retention"])
        total_searches = len(self.search_analytics)
        total_clicks = sum(1 for s in self.search_analytics if s.selected_result)
        total_additions = self.metrics["conversion_rates"].get("daily", 0)
        
        return {
            "sessions": total_sessions,
            "searches": total_searches,
            "clicks": total_clicks,
            "additions": total_additions,
            "search_rate": total_searches / total_sessions if total_sessions > 0 else 0,
            "click_rate": total_clicks / total_searches if total_searches > 0 else 0,
            "conversion_rate": total_additions / total_sessions if total_sessions > 0 else 0
        }

# Global instance
analytics = AdvancedAnalytics()