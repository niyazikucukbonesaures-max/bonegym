# Fitness ve Kalori Takip Uygulaması - Pydantic v2 Şemaları
# Request ve response doğrulaması için kullanılır.

from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Besin Öğesi Şemaları
# ---------------------------------------------------------------------------

class FoodItemBase(BaseModel):
    """Besin öğesi için ortak alanlar."""
    name: str
    calories_per_100g: float = Field(gt=0)
    protein_per_100g: float = Field(ge=0)
    carbs_per_100g: float = Field(ge=0)
    fat_per_100g: float = Field(ge=0)
    source_url: Optional[str] = None


class FoodItemCreate(FoodItemBase):
    """Yeni besin öğesi oluşturma isteği."""
    pass


class FoodItemSchema(FoodItemBase):
    """Besin öğesi API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    scraped_at: datetime


# Geriye dönük uyumluluk için alias
FoodItemResponse = FoodItemSchema


# ---------------------------------------------------------------------------
# Kalori Günlüğü Şemaları
# ---------------------------------------------------------------------------

class FoodLogBase(BaseModel):
    """Kalori günlüğü girişi için ortak alanlar."""
    user_id: int
    food_item_id: Optional[int] = None
    food_name: str
    grams: float = Field(gt=0, description="Gram miktarı sıfırdan büyük olmalıdır")
    meal_type: str = Field(description="breakfast | lunch | dinner | snack")


class FoodLogCreate(FoodLogBase):
    """Yeni kalori günlüğü girişi oluşturma isteği."""
    logged_at: Optional[datetime] = None  # Belirtilmezse sunucu zamanı kullanılır
    # AI asistanından gelen besin değerleri (food_item_id yoksa kullanılır)
    calories_per_100g: Optional[float] = Field(default=None, ge=0)
    protein_per_100g: Optional[float] = Field(default=None, ge=0)
    carbs_per_100g: Optional[float] = Field(default=None, ge=0)
    fat_per_100g: Optional[float] = Field(default=None, ge=0)


class FoodLogEntrySchema(FoodLogBase):
    """Kalori günlüğü girişi API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    calories: float
    protein: float
    carbs: float
    fat: float
    logged_at: datetime


# Geriye dönük uyumluluk için alias
FoodLogResponse = FoodLogEntrySchema


class DailySummary(BaseModel):
    """Günlük kalori ve makro özeti."""
    date: str
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    entries: list[FoodLogEntrySchema]


# ---------------------------------------------------------------------------
# Antrenman Programı Şemaları
# ---------------------------------------------------------------------------

class ExerciseBase(BaseModel):
    """Egzersiz için ortak alanlar."""
    name: str
    sets: int = Field(gt=0)
    reps: int = Field(gt=0)
    weight_kg: float = Field(ge=0)
    order: int = Field(ge=0)


class ExerciseCreate(ExerciseBase):
    """Yeni egzersiz oluşturma isteği."""
    pass


class ExerciseSchema(ExerciseBase):
    """Egzersiz API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    program_id: int


# Geriye dönük uyumluluk için alias
ExerciseResponse = ExerciseSchema


class WorkoutProgramBase(BaseModel):
    """Antrenman programı için ortak alanlar."""
    name: str


class WorkoutProgramCreate(WorkoutProgramBase):
    """Yeni antrenman programı oluşturma isteği."""
    exercises: list[ExerciseCreate] = []


class WorkoutProgramSchema(WorkoutProgramBase):
    """Antrenman programı API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    exercises: list[ExerciseSchema] = []


# Geriye dönük uyumluluk için alias
WorkoutProgramResponse = WorkoutProgramSchema


# ---------------------------------------------------------------------------
# Antrenman Kaydı Şemaları
# ---------------------------------------------------------------------------

class ExerciseLogBase(BaseModel):
    """Egzersiz kaydı için ortak alanlar."""
    exercise_name: str
    sets_performed: int = Field(gt=0)
    reps_performed: int = Field(gt=0)
    weight_kg: float = Field(ge=0)


class ExerciseLogCreate(ExerciseLogBase):
    """Yeni egzersiz kaydı oluşturma isteği."""
    pass


class ExerciseLogSchema(ExerciseLogBase):
    """Egzersiz kaydı API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_log_id: int


# Geriye dönük uyumluluk için alias
ExerciseLogResponse = ExerciseLogSchema


class WorkoutLogBase(BaseModel):
    """Antrenman kaydı için ortak alanlar."""
    program_id: Optional[int] = None
    program_name: str
    duration_minutes: int = Field(gt=0)


class WorkoutLogCreate(WorkoutLogBase):
    """Yeni antrenman kaydı oluşturma isteği."""
    exercises_performed: list[ExerciseLogCreate] = []


class WorkoutLogSchema(WorkoutLogBase):
    """Antrenman kaydı API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    completed_at: datetime
    exercise_logs: list[ExerciseLogSchema] = []


# Geriye dönük uyumluluk için alias
WorkoutLogResponse = WorkoutLogSchema


# ---------------------------------------------------------------------------
# Kreatin Dozu Şemaları
# ---------------------------------------------------------------------------

class CreatineDoseBase(BaseModel):
    """Kreatin dozu için ortak alanlar."""
    user_id: int
    dose_grams: float = Field(gt=0)
    phase: str = Field(description="loading | maintenance")


class CreatineDoseCreate(CreatineDoseBase):
    """Yeni kreatin dozu oluşturma isteği."""
    pass


class CreatineDoseSchema(CreatineDoseBase):
    """Kreatin dozu API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    taken_at: datetime


# Geriye dönük uyumluluk için alias
CreatineDoseResponse = CreatineDoseSchema


class TodayCreatineStatus(BaseModel):
    """Bugünkü kreatin alım durumu."""
    taken: bool
    dose_grams: Optional[float] = None
    phase: Optional[str] = None
    days_in_phase: int = 0
    total_grams: float = 0.0


# ---------------------------------------------------------------------------
# Ölçüm Şemaları
# ---------------------------------------------------------------------------

class MeasurementBase(BaseModel):
    """Ölçüm için ortak alanlar."""
    user_id: int
    height_cm: Optional[float] = Field(default=None, gt=0)
    weight_kg: Optional[float] = Field(default=None, gt=0)
    waist_cm: Optional[float] = Field(default=None, gt=0)
    hip_cm: Optional[float] = Field(default=None, gt=0)
    chest_cm: Optional[float] = Field(default=None, gt=0)
    arm_cm: Optional[float] = Field(default=None, gt=0)
    leg_cm: Optional[float] = Field(default=None, gt=0)


class MeasurementCreate(MeasurementBase):
    """Yeni ölçüm oluşturma isteği."""
    pass


class MeasurementSchema(MeasurementBase):
    """Ölçüm API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    measured_at: datetime


# Geriye dönük uyumluluk için alias
MeasurementResponse = MeasurementSchema


class MeasurementDelta(BaseModel):
    """İlk ve son ölçüm arasındaki fark."""
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    waist_cm: Optional[float] = None
    hip_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    arm_cm: Optional[float] = None
    leg_cm: Optional[float] = None


# ---------------------------------------------------------------------------
# Kullanıcı Profili Şemaları
# ---------------------------------------------------------------------------

class UserProfileBase(BaseModel):
    """Kullanıcı profili için ortak alanlar."""
    weight_kg: float = Field(gt=0)
    height_cm: float = Field(gt=0)
    age: int = Field(gt=0, lt=150)
    gender: str = Field(description="male | female")
    activity_level: str = Field(description="sedentary | light | moderate | active | very_active")
    goal: str = Field(description="lose | maintain | gain | recomp")
    weekly_workout_goal: int = Field(default=4, ge=0, le=7)
    daily_calorie_target: Optional[float] = Field(default=None, gt=0)
    fitness_level: str = Field(default="beginner", description="beginner | intermediate | advanced")


class UserProfileCreate(UserProfileBase):
    """Yeni kullanıcı profili oluşturma isteği."""
    pass


class UserProfileUpdate(UserProfileBase):
    """Kullanıcı profili güncelleme isteği."""
    pass


class UserProfileSchema(UserProfileBase):
    """Kullanıcı profili API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime


# Geriye dönük uyumluluk için alias
UserProfileResponse = UserProfileSchema


class UserProfileWithStats(UserProfileSchema):
    """Hesaplanan istatistiklerle birlikte kullanıcı profili."""
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    recommended_calories: Optional[float] = None


# ---------------------------------------------------------------------------
# Scraping Meta Veri Şemaları
# ---------------------------------------------------------------------------

class ScrapeMetadataSchema(BaseModel):
    """Scraping meta verisi API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_scrape_at: datetime
    food_count: int
    status: str
    error_message: Optional[str] = None


# Geriye dönük uyumluluk için alias
ScrapeMetadataResponse = ScrapeMetadataSchema


class ScrapeResult(BaseModel):
    """Scraping işlemi sonucu."""
    success: bool
    food_count: int
    message: str
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Pano Şemaları
# ---------------------------------------------------------------------------

class WeeklyWorkoutStats(BaseModel):
    """Haftalık antrenman istatistikleri."""
    completed: int
    goal: int
    percentage: float
    total_duration_minutes: int


class DashboardSnapshotSchema(BaseModel):
    """
    Tek API çağrısıyla döndürülen tüm pano verileri (canonical response schema).
    Frontend'in birden fazla istek yapmasına gerek kalmaz.
    """
    # Günlük kalori özeti
    daily_summary: Optional[DailySummary] = None
    # Kullanıcı profili ve hesaplanan değerler
    profile: Optional[UserProfileWithStats] = None
    # Bugünkü kreatin durumu
    creatine_status: Optional[TodayCreatineStatus] = None
    # Haftalık antrenman istatistikleri
    weekly_workout_stats: Optional[WeeklyWorkoutStats] = None
    # Son 7 günlük kilo değişimi
    weight_trend: list[MeasurementSchema] = []
    # Günlük su tüketim özeti
    daily_water_summary: Optional[DailyWaterSummary] = None
    # Yeni kazanılan rozetler
    new_achievements: list[UserAchievementSchema] = []
    # Rozet ilerleme durumu
    achievement_progress: list[AchievementProgress] = []
    # Bildirimler
    notifications: list[str] = []


# Geriye dönük uyumluluk için alias
DashboardSnapshot = DashboardSnapshotSchema

# ---------------------------------------------------------------------------
# Su Takibi Şemaları
# ---------------------------------------------------------------------------

class WaterLogBase(BaseModel):
    """Su takibi için ortak alanlar."""
    user_id: int
    amount_ml: float = Field(gt=0, description="Su miktarı (ml) sıfırdan büyük olmalıdır")


class WaterLogCreate(WaterLogBase):
    """Yeni su kaydı oluşturma isteği."""
    pass


class WaterLogSchema(WaterLogBase):
    """Su kaydı API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    logged_at: datetime


class DailyWaterSummary(BaseModel):
    """Günlük su tüketim özeti."""
    date: str
    total_ml: float
    goal_ml: float
    percentage: float
    entries: list[WaterLogSchema]


# ---------------------------------------------------------------------------
# Başarı Rozetleri Şemaları
# ---------------------------------------------------------------------------

class AchievementBase(BaseModel):
    """Başarı rozeti için ortak alanlar."""
    name: str
    description: str
    icon: str
    category: str = Field(description="food | water | workout | streak | milestone")
    condition_type: str = Field(description="count | streak | milestone")
    condition_value: int = Field(gt=0)
    points: int = Field(default=10, ge=0)


class AchievementCreate(AchievementBase):
    """Yeni başarı rozeti oluşturma isteği."""
    pass


class AchievementSchema(AchievementBase):
    """Başarı rozeti API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class UserAchievementSchema(BaseModel):
    """Kullanıcının kazandığı rozet API yanıtı."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    achievement_id: int
    earned_at: datetime
    is_new: bool
    achievement: AchievementSchema


class AchievementProgress(BaseModel):
    """Rozet ilerleme durumu."""
    achievement: AchievementSchema
    current_value: int
    target_value: int
    percentage: float
    is_completed: bool


# ---------------------------------------------------------------------------
# Barkod Ürün Şemaları
# ---------------------------------------------------------------------------

class BarcodeProductBase(BaseModel):
    """Barkod ürünü için ortak alanlar."""
    barcode: str
    name: str
    brand: Optional[str] = None
    calories_per_100g: float = Field(gt=0)
    protein_per_100g: float = Field(ge=0)
    carbs_per_100g: float = Field(ge=0)
    fat_per_100g: float = Field(ge=0)
    serving_size_g: Optional[float] = Field(default=None, gt=0)
    image_url: Optional[str] = None
    source: str = Field(default="openfoodfacts")


class BarcodeProductCreate(BarcodeProductBase):
    """Yeni barkod ürünü oluşturma isteği."""
    pass


class BarcodeProductSchema(BarcodeProductBase):
    """Barkod ürünü API yanıtı (canonical response schema)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class BarcodeSearchResult(BaseModel):
    """Barkod arama sonucu."""
    found: bool
    product: Optional[BarcodeProductSchema] = None
    message: str


# ---------------------------------------------------------------------------
# AI Chat Şemaları
# ---------------------------------------------------------------------------

class NutritionData(BaseModel):
    """AI tarafından sağlanan besin değerleri."""
    food_name: str
    calories_per_100g: float = Field(ge=0, le=900, description="100g başına kalori (0-900)")
    protein_per_100g: float = Field(ge=0, le=100, description="100g başına protein (0-100g)")
    carbs_per_100g: float = Field(ge=0, le=100, description="100g başına karbonhidrat (0-100g)")
    fat_per_100g: float = Field(ge=0, le=100, description="100g başına yağ (0-100g)")
    confidence: Literal["high", "medium", "low"] = Field(description="AI güven seviyesi")
    source: str = Field(default="ai_assistant", description="Veri kaynağı")


class ChatMessageBase(BaseModel):
    """Chat mesajı için ortak alanlar."""
    content: str = Field(min_length=1, description="Mesaj içeriği boş olamaz")


class ChatRequest(BaseModel):
    """AI chat isteği."""
    message: str = Field(min_length=1, description="Kullanıcı mesajı")
    session_id: str = Field(description="Oturum ID'si")
    user_id: int = Field(default=1, description="Kullanıcı ID'si")


class ChatMessageSchema(BaseModel):
    """Chat mesajı API yanıtı."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["user", "assistant"]
    content: str
    timestamp: datetime
    nutrition_data: Optional[NutritionData] = None


class ChatResponse(BaseModel):
    """AI chat yanıtı."""
    response: str
    nutrition_data: Optional[NutritionData] = None
    session_id: str
    timestamp: datetime
    error: Optional[str] = None


class SessionHistory(BaseModel):
    """Oturum geçmişi."""
    session_id: str
    messages: list[ChatMessageSchema]
    created_at: datetime
    last_activity: datetime
    message_count: int


class AIChatSessionSchema(BaseModel):
    """AI chat oturumu API yanıtı."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    created_at: datetime
    last_activity: datetime
    message_count: int


class AIGeneratedFoodSchema(BaseModel):
    """AI tarafından üretilen besin API yanıtı."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    message_id: str
    food_name: str
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    confidence: str
    created_at: datetime


class StatusResponse(BaseModel):
    """Genel durum yanıtı."""
    success: bool
    message: str


# ---------------------------------------------------------------------------
# Bildirim Şemaları
# ---------------------------------------------------------------------------

class NotificationSchema(BaseModel):
    """Bildirim şeması."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    type: Literal["info", "warning", "success", "error"]
    title: str
    message: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Gelişmiş Fitness İyileştirme Şemaları
# ---------------------------------------------------------------------------

class SportProfileBase(BaseModel):
    """Spor profili için ortak alanlar."""
    user_id: int
    is_athlete: bool = False
    sport_type: Optional[str] = Field(default=None, description="strength | endurance | powerlifting | bodybuilding | crossfit | mixed | general")
    training_frequency: int = Field(default=3, ge=0, le=7, description="Haftalık antrenman günü sayısı")
    training_intensity: str = Field(default="moderate", description="low | moderate | high | very_high")
    rest_day_calories_adjustment: float = Field(default=1.05, ge=1.0, le=1.2)
    training_day_calories_adjustment: float = Field(default=1.15, ge=1.0, le=1.5)
    preferred_macro_split: Optional[dict] = Field(default=None, description="Tercih edilen makro oranları")


class SportProfileCreate(SportProfileBase):
    """Yeni spor profili oluşturma isteği."""
    pass


class SportProfileSchema(SportProfileBase):
    """Spor profili API yanıtı."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class NotificationPreferencesBase(BaseModel):
    """Bildirim tercihleri için ortak alanlar."""
    user_id: int
    weight_reminders: bool = True
    measurement_reminders: bool = True
    motivation_messages: bool = True
    progress_reports: bool = True
    max_daily_notifications: int = Field(default=2, ge=0, le=10)
    preferred_reminder_time: Optional[str] = Field(default=None, description="HH:MM formatında")
    quiet_hours_start: Optional[str] = Field(default=None, description="HH:MM formatında")
    quiet_hours_end: Optional[str] = Field(default=None, description="HH:MM formatında")


class NotificationPreferencesCreate(NotificationPreferencesBase):
    """Yeni bildirim tercihleri oluşturma isteği."""
    pass


class NotificationPreferencesSchema(NotificationPreferencesBase):
    """Bildirim tercihleri API yanıtı."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime