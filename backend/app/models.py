# Fitness ve Kalori Takip Uygulaması - SQLAlchemy ORM Modelleri
# SQLAlchemy 2.0 async style kullanılmaktadır.

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Timezone-aware DateTime helper
# PostgreSQL: TIMESTAMP WITH TIME ZONE
# SQLite: TIMESTAMP (naive, UTC olarak saklanır)
TZ_DATETIME = DateTime(timezone=True)


class Base(DeclarativeBase):
    """Tüm modeller için temel sınıf."""
    pass


# ---------------------------------------------------------------------------
# Besin Öğesi Tablosu
# ---------------------------------------------------------------------------

class FoodItem(Base):
    """diyetkolik.com'dan çekilen besin öğelerini saklar."""

    __tablename__ = "food_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    calories_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    protein_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())

    def __repr__(self) -> str:
        return f"<FoodItem id={self.id} name={self.name!r}>"


# ---------------------------------------------------------------------------
# Kalori Günlüğü Tablosu
# ---------------------------------------------------------------------------

class FoodLog(Base):
    """Kullanıcının günlük kalori günlüğü girişlerini saklar."""

    __tablename__ = "food_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # Besin silinse bile kayıt korunur (nullable FK)
    food_item_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("food_items.id", ondelete="SET NULL"), nullable=True
    )
    # Denormalize besin adı — besin silinse bile kayıt okunabilir kalır
    food_name: Mapped[str] = mapped_column(String, nullable=False)
    grams: Mapped[float] = mapped_column(Float, nullable=False)
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein: Mapped[float] = mapped_column(Float, nullable=False)
    carbs: Mapped[float] = mapped_column(Float, nullable=False)
    fat: Mapped[float] = mapped_column(Float, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())
    # Öğün tipi: breakfast | lunch | dinner | snack
    meal_type: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self) -> str:
        return f"<FoodLog id={self.id} food={self.food_name!r} grams={self.grams}>"


# ---------------------------------------------------------------------------
# Antrenman Programı Tablosu
# ---------------------------------------------------------------------------

class WorkoutProgram(Base):
    """Kullanıcının oluşturduğu antrenman programlarını saklar."""

    __tablename__ = "workout_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())

    # İlişki: programa ait egzersizler
    exercises: Mapped[list["Exercise"]] = relationship(
        "Exercise", back_populates="program", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<WorkoutProgram id={self.id} name={self.name!r}>"


# ---------------------------------------------------------------------------
# Egzersiz Tablosu
# ---------------------------------------------------------------------------

class Exercise(Base):
    """Bir antrenman programına ait egzersizleri saklar."""

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workout_programs.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    # Egzersizlerin program içindeki sırası
    order: Mapped[int] = mapped_column("order", Integer, nullable=False)

    # İlişki: ait olduğu program
    program: Mapped["WorkoutProgram"] = relationship("WorkoutProgram", back_populates="exercises")

    def __repr__(self) -> str:
        return f"<Exercise id={self.id} name={self.name!r} program_id={self.program_id}>"


# ---------------------------------------------------------------------------
# Antrenman Kaydı Tablosu
# ---------------------------------------------------------------------------

class WorkoutLog(Base):
    """Tamamlanan antrenman seanslarını saklar."""

    __tablename__ = "workout_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Program silinse bile kayıt korunur (nullable FK)
    program_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("workout_programs.id", ondelete="SET NULL"), nullable=True
    )
    # Denormalize program adı — program silinse bile kayıt okunabilir kalır
    program_name: Mapped[str] = mapped_column(String, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # İlişki: bu seansta gerçekleştirilen egzersiz kayıtları
    exercise_logs: Mapped[list["ExerciseLog"]] = relationship(
        "ExerciseLog", back_populates="workout_log", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<WorkoutLog id={self.id} program={self.program_name!r}>"


# ---------------------------------------------------------------------------
# Egzersiz Kaydı Tablosu
# ---------------------------------------------------------------------------

class ExerciseLog(Base):
    """Bir antrenman seansında gerçekleştirilen egzersiz detaylarını saklar."""

    __tablename__ = "exercise_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workout_log_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workout_logs.id", ondelete="CASCADE"), nullable=False
    )
    exercise_name: Mapped[str] = mapped_column(String, nullable=False)
    sets_performed: Mapped[int] = mapped_column(Integer, nullable=False)
    reps_performed: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)

    # İlişki: ait olduğu antrenman kaydı
    workout_log: Mapped["WorkoutLog"] = relationship("WorkoutLog", back_populates="exercise_logs")

    def __repr__(self) -> str:
        return f"<ExerciseLog id={self.id} exercise={self.exercise_name!r}>"


# ---------------------------------------------------------------------------
# Kreatin Dozu Tablosu
# ---------------------------------------------------------------------------

class CreatineDose(Base):
    """Kullanıcının günlük kreatin alım kayıtlarını saklar."""

    __tablename__ = "creatine_doses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    dose_grams: Mapped[float] = mapped_column(Float, nullable=False)
    # Faz: loading (yükleme) | maintenance (idame)
    phase: Mapped[str] = mapped_column(String, nullable=False)
    taken_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())

    def __repr__(self) -> str:
        return f"<CreatineDose id={self.id} dose={self.dose_grams}g phase={self.phase!r}>"


# ---------------------------------------------------------------------------
# Ölçüm Tablosu
# ---------------------------------------------------------------------------

class Measurement(Base):
    """Kullanıcının kilo ve vücut ölçümlerini saklar."""

    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # Tüm ölçüm alanları isteğe bağlıdır; kullanıcı yalnızca istediğini girebilir
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hip_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    chest_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    arm_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    leg_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    measured_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())
    
    # Fitness İyileştirme - Yeni alanlar
    is_validated: Mapped[bool] = mapped_column(Boolean, default=True)
    validation_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    measurement_method: Mapped[str] = mapped_column(String, default="manual")  # manual, smart_scale, estimated
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)

    def __repr__(self) -> str:
        return f"<Measurement id={self.id} user_id={self.user_id} weight={self.weight_kg}kg validated={self.is_validated}>"


# ---------------------------------------------------------------------------
# Kullanıcı Profili Tablosu
# ---------------------------------------------------------------------------

class UserProfile(Base):
    """Kullanıcının profil bilgilerini ve hedeflerini saklar."""

    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    # Cinsiyet: male | female
    gender: Mapped[str] = mapped_column(String, nullable=False)
    # Aktivite seviyesi: sedentary | light | moderate | active | very_active
    activity_level: Mapped[str] = mapped_column(String, nullable=False)
    # Hedef: lose | maintain | gain
    goal: Mapped[str] = mapped_column(String, nullable=False)
    # Haftalık antrenman hedefi (varsayılan: 4 gün)
    weekly_workout_goal: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    # Manuel kalori hedefi override (None ise hesaplanan TDEE kullanılır)
    daily_calorie_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())
    
    # Fitness İyileştirme - Yeni alanlar
    is_athlete: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_measurement_time: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    data_retention_days: Mapped[int] = mapped_column(Integer, default=365)
    privacy_level: Mapped[str] = mapped_column(String, default="standard")  # minimal, standard, detailed
    # Fitness seviyesi: beginner | intermediate | advanced
    fitness_level: Mapped[str] = mapped_column(String, default="beginner")

    def __repr__(self) -> str:
        return f"<UserProfile id={self.id} goal={self.goal!r} athlete={self.is_athlete}>"


# ---------------------------------------------------------------------------
# Su Takibi Tablosu
# ---------------------------------------------------------------------------

class WaterLog(Base):
    """Kullanıcının günlük su tüketim kayıtlarını saklar."""

    __tablename__ = "water_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_ml: Mapped[float] = mapped_column(Float, nullable=False)  # Su miktarı (ml)
    logged_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())

    def __repr__(self) -> str:
        return f"<WaterLog id={self.id} user_id={self.user_id} amount={self.amount_ml}ml>"


# ---------------------------------------------------------------------------
# Başarı Rozetleri Tablosu
# ---------------------------------------------------------------------------

class Achievement(Base):
    """Mevcut başarı rozetlerini tanımlar."""

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)  # "İlk Giriş", "7 Gün Streak"
    description: Mapped[str] = mapped_column(String, nullable=False)  # "İlk yemeğini kaydet"
    icon: Mapped[str] = mapped_column(String, nullable=False)  # "🎉", "🔥", "💪"
    category: Mapped[str] = mapped_column(String, nullable=False)  # "food", "water", "workout", "streak"
    condition_type: Mapped[str] = mapped_column(String, nullable=False)  # "count", "streak", "milestone"
    condition_value: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 7, 30
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=10)  # Rozet puanı
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())

    def __repr__(self) -> str:
        return f"<Achievement id={self.id} name={self.name!r}>"


class UserAchievement(Base):
    """Kullanıcının kazandığı başarı rozetlerini saklar."""

    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    achievement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False
    )
    earned_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())
    is_new: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # Yeni rozet bildirimi için

    # İlişki: kazanılan rozet
    achievement: Mapped["Achievement"] = relationship("Achievement")

    def __repr__(self) -> str:
        return f"<UserAchievement id={self.id} user_id={self.user_id} achievement_id={self.achievement_id}>"


# ---------------------------------------------------------------------------
# Barkod Ürün Tablosu
# ---------------------------------------------------------------------------

class BarcodeProduct(Base):
    """Barkod ile taranan ürünlerin bilgilerini saklar."""

    __tablename__ = "barcode_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    barcode: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    calories_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    protein_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    serving_size_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Porsiyon boyutu
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="openfoodfacts")  # Veri kaynağı
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())

    def __repr__(self) -> str:
        return f"<BarcodeProduct id={self.id} barcode={self.barcode!r} name={self.name!r}>"


# ---------------------------------------------------------------------------
# AI Chat Sessions Tablosu
# ---------------------------------------------------------------------------

class AIChatSession(Base):
    """AI besin asistanı sohbet oturumlarını saklar."""

    __tablename__ = "ai_chat_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())
    last_activity: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # İlişki: oturuma ait mesajlar
    messages: Mapped[list["AIChatMessage"]] = relationship(
        "AIChatMessage", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AIChatSession id={self.id!r} user_id={self.user_id} messages={self.message_count}>"


# ---------------------------------------------------------------------------
# AI Chat Messages Tablosu
# ---------------------------------------------------------------------------

class AIChatMessage(Base):
    """AI sohbet mesajlarını saklar."""

    __tablename__ = "ai_chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"), nullable=False)
    message_type: Mapped[str] = mapped_column(String, nullable=False)  # 'user' | 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    nutrition_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    timestamp: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())

    # İlişki: ait olduğu oturum
    session: Mapped["AIChatSession"] = relationship("AIChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<AIChatMessage id={self.id!r} type={self.message_type!r} session_id={self.session_id!r}>"


# ---------------------------------------------------------------------------
# AI Generated Foods Tablosu
# ---------------------------------------------------------------------------

class AIGeneratedFood(Base):
    """AI tarafından önerilen besin değerlerini saklar."""

    __tablename__ = "ai_generated_foods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"), nullable=False)
    message_id: Mapped[str] = mapped_column(String, nullable=False)
    food_name: Mapped[str] = mapped_column(String, nullable=False)
    calories_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    protein_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[str] = mapped_column(String, nullable=False)  # 'high' | 'medium' | 'low'
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())

    def __repr__(self) -> str:
        return f"<AIGeneratedFood id={self.id} food_name={self.food_name!r} confidence={self.confidence!r}>"


# ---------------------------------------------------------------------------
# Scraping Meta Veri Tablosu
# ---------------------------------------------------------------------------

class ScrapeMetadata(Base):
    """Web scraping işlemlerinin meta verilerini saklar."""

    __tablename__ = "scrape_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    last_scrape_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False)
    food_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # Durum: success | failed
    status: Mapped[str] = mapped_column(String, nullable=False)
    # Hata mesajı (yalnızca status="failed" durumunda dolu olur)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ScrapeMetadata id={self.id} status={self.status!r} count={self.food_count}>"


# ---------------------------------------------------------------------------
# AI Coach Recommendation Tablosu
# ---------------------------------------------------------------------------

class AICoachRecommendation(Base):
    """AI Coach tarafından oluşturulan antrenman önerilerini saklar."""

    __tablename__ = "ai_coach_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Öneri türü: workout | rest | light_activity
    recommendation_type: Mapped[str] = mapped_column(String, nullable=False)
    
    # Antrenman detayları (JSON format)
    workout_plan: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Kalori dengesi analizi
    calorie_balance: Mapped[float] = mapped_column(Float, nullable=False)
    calorie_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Antrenman parametreleri
    intensity_level: Mapped[str] = mapped_column(String, nullable=False)  # low | moderate | high
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Motivasyon mesajı
    motivation_message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Kullanıcı geri bildirimi
    user_feedback: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # accepted | rejected | modified
    feedback_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Öneri durumu
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")  # pending | accepted | rejected | completed
    
    # Zaman damgaları
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())
    accepted_at: Mapped[Optional[datetime]] = mapped_column(TZ_DATETIME, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TZ_DATETIME, nullable=True)

    def __repr__(self) -> str:
        return f"<AICoachRecommendation id={self.id} user_id={self.user_id} type={self.recommendation_type!r}>"


# ---------------------------------------------------------------------------
# AI Coach Progress Tablosu
# ---------------------------------------------------------------------------

class AICoachProgress(Base):
    """AI Coach tarafından takip edilen kullanıcı ilerlemesini saklar."""

    __tablename__ = "ai_coach_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # İlerleme dönemi (haftalık analiz)
    week_start_date: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False)
    week_end_date: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False)
    
    # Performans metrikleri
    workouts_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    workouts_recommended: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Ortalama antrenman süresi
    avg_workout_duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Yoğunluk dağılımı (JSON format)
    intensity_distribution: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # İlerleme skoru (0-100)
    progress_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Adaptasyon önerileri
    adaptation_needed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    adaptation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Hedef başarımı
    goals_achieved: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())

    def __repr__(self) -> str:
        return f"<AICoachProgress id={self.id} user_id={self.user_id} score={self.progress_score}>"


# ---------------------------------------------------------------------------
# AI Coach Preferences Tablosu
# ---------------------------------------------------------------------------

class AICoachPreferences(Base):
    """Kullanıcının AI Coach tercihlerini ve öğrenilen davranışları saklar."""

    __tablename__ = "ai_coach_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    
    # Tercih edilen antrenman türleri (JSON array)
    preferred_workout_types: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    
    # Tercih edilen antrenman süreleri
    preferred_duration_min: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    preferred_duration_max: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    
    # Tercih edilen yoğunluk seviyeleri
    preferred_intensity: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Kaçınılacak egzersizler (yaralanma geçmişi)
    avoided_exercises: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    
    # Sağlık durumu ve kısıtlamalar
    health_conditions: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    
    # Öğrenilen davranış kalıpları
    learned_patterns: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Geri bildirim geçmişi analizi
    feedback_history: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Motivasyon tercihleri
    motivation_style: Mapped[str] = mapped_column(String, nullable=False, default="balanced")  # encouraging | challenging | balanced
    
    # Güvenlik ayarları
    safety_level: Mapped[str] = mapped_column(String, nullable=False, default="standard")  # conservative | standard | aggressive
    
    # Son güncelleme
    updated_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False, default=func.now())

    def __repr__(self) -> str:
        return f"<AICoachPreferences id={self.id} user_id={self.user_id} safety={self.safety_level!r}>"


# ---------------------------------------------------------------------------
# Fitness İyileştirme - Yeni Veri Modelleri
# ---------------------------------------------------------------------------

class WeightValidation(Base):
    """Kilo doğrulama kayıtları."""
    __tablename__ = "weight_validations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    previous_weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    change_kg: Mapped[float] = mapped_column(Float, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    validation_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    validated_at: Mapped[datetime] = mapped_column(TZ_DATETIME, default=func.now())

    def __repr__(self) -> str:
        return f"<WeightValidation id={self.id} user_id={self.user_id} weight={self.weight_kg}kg valid={self.is_valid}>"


class SportProfile(Base):
    """Spor yapan kullanıcılar için özelleştirilmiş profil."""
    __tablename__ = "sport_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    is_athlete: Mapped[bool] = mapped_column(Boolean, default=False)
    sport_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # strength, endurance, mixed
    training_frequency: Mapped[int] = mapped_column(Integer, default=3)  # haftalık antrenman sayısı
    training_intensity: Mapped[str] = mapped_column(String, default="moderate")  # low, moderate, high
    rest_day_calories_adjustment: Mapped[float] = mapped_column(Float, default=1.05)
    training_day_calories_adjustment: Mapped[float] = mapped_column(Float, default=1.15)
    preferred_macro_split: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TZ_DATETIME, default=func.now())

    def __repr__(self) -> str:
        return f"<SportProfile id={self.id} user_id={self.user_id} athlete={self.is_athlete} type={self.sport_type!r}>"


class TrendAnalysis(Base):
    """Trend analizi sonuçları."""
    __tablename__ = "trend_analyses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    analysis_type: Mapped[str] = mapped_column(String, nullable=False)  # weekly, monthly, quarterly
    period_start: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False)
    period_end: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False)
    weight_change_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    average_weekly_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trend_direction: Mapped[str] = mapped_column(String, nullable=False)  # increasing, decreasing, stable
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    insights: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, default=func.now())

    def __repr__(self) -> str:
        return f"<TrendAnalysis id={self.id} user_id={self.user_id} type={self.analysis_type!r} direction={self.trend_direction!r}>"


class NotificationPreferences(Base):
    """Kullanıcı bildirim tercihleri."""
    __tablename__ = "notification_preferences"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    weight_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    measurement_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    motivation_messages: Mapped[bool] = mapped_column(Boolean, default=True)
    progress_reports: Mapped[bool] = mapped_column(Boolean, default=True)
    max_daily_notifications: Mapped[int] = mapped_column(Integer, default=2)
    preferred_reminder_time: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # HH:MM format
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TZ_DATETIME, default=func.now())

    def __repr__(self) -> str:
        return f"<NotificationPreferences id={self.id} user_id={self.user_id} max_daily={self.max_daily_notifications}>"


class DataBackup(Base):
    """Veri yedekleme kayıtları."""
    __tablename__ = "data_backups"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    backup_type: Mapped[str] = mapped_column(String, nullable=False)  # full, incremental
    data_encrypted: Mapped[str] = mapped_column(Text, nullable=False)  # Şifrelenmiş JSON
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TZ_DATETIME, default=func.now())
    expires_at: Mapped[datetime] = mapped_column(TZ_DATETIME, nullable=False)

    def __repr__(self) -> str:
        return f"<DataBackup id={self.id!r} user_id={self.user_id} type={self.backup_type!r} size={self.file_size_bytes}>"
