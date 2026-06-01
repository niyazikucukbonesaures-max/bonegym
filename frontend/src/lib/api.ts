// Fitness ve Kalori Takip Uygulaması - API İstemcisi
// Axios instance ve tüm API çağrı fonksiyonları

import axios from 'axios'

// ---------------------------------------------------------------------------
// TypeScript Tip Tanımları
// ---------------------------------------------------------------------------

export interface FoodItem {
  id: number
  name: string
  calories_per_100g: number
  protein_per_100g: number
  carbs_per_100g: number
  fat_per_100g: number
  source_url?: string
  scraped_at: string
}

export interface FoodLogCreate {
  user_id: number
  food_item_id?: number
  food_name: string
  grams: number
  meal_type: string
  logged_at?: string  // ISO datetime string, belirtilmezse sunucu zamanı kullanılır
  // AI asistanından gelen makro değerleri (food_item_id yoksa kullanılır)
  calories_per_100g?: number
  protein_per_100g?: number
  carbs_per_100g?: number
  fat_per_100g?: number
}

export interface FoodLogEntry {
  id: number
  user_id: number
  food_item_id?: number
  food_name: string
  grams: number
  meal_type: string
  calories: number
  protein: number
  carbs: number
  fat: number
  logged_at: string
}

export interface DailySummary {
  date: string
  total_calories: number
  total_protein: number
  total_carbs: number
  total_fat: number
  entries: FoodLogEntry[]
}

export interface ExerciseCreate {
  name: string
  sets: number
  reps: number
  weight_kg: number
  order: number
}

export interface Exercise extends ExerciseCreate {
  id: number
  program_id: number
}

export interface WorkoutProgramCreate {
  name: string
  exercises?: ExerciseCreate[]
}

export interface WorkoutProgram {
  id: number
  name: string
  created_at: string
  exercises: Exercise[]
}

export interface ExerciseLogCreate {
  exercise_name: string
  sets_performed: number
  reps_performed: number
  weight_kg: number
}

export interface WorkoutLogCreate {
  program_id?: number
  program_name: string
  duration_minutes: number
  exercises_performed?: ExerciseLogCreate[]
}

export interface WorkoutLog {
  id: number
  program_id?: number
  program_name: string
  duration_minutes: number
  completed_at: string
  exercise_logs: ExerciseLogCreate[]
}

export interface CreatineDoseCreate {
  user_id: number
  dose_grams: number
  phase: string
}

export interface CreatineDose {
  id: number
  user_id: number
  dose_grams: number
  phase: string
  taken_at: string
}

export interface TodayCreatineStatus {
  taken: boolean
  dose_grams?: number
  phase?: string
  days_in_phase: number
  total_grams: number
}

export interface MeasurementCreate {
  user_id: number
  height_cm?: number
  weight_kg?: number
  waist_cm?: number
  hip_cm?: number
  chest_cm?: number
  arm_cm?: number
  leg_cm?: number
}

export interface Measurement extends MeasurementCreate {
  id: number
  measured_at: string
}

export interface MeasurementDelta {
  height_cm?: number
  weight_kg?: number
  waist_cm?: number
  hip_cm?: number
  chest_cm?: number
  arm_cm?: number
  leg_cm?: number
}

export interface UserProfileUpdate {
  weight_kg: number
  height_cm: number
  age: number
  gender: string
  activity_level: string
  goal: string
  weekly_workout_goal?: number
  daily_calorie_target?: number
  fitness_level?: string
}

export interface UserProfile extends UserProfileUpdate {
  id: number
  updated_at: string
  bmr?: number
  tdee?: number
  recommended_calories?: number
}

export interface WeeklyWorkoutStats {
  completed: number
  goal: number
  percentage: number
  total_duration_minutes: number
}

export interface DashboardSnapshot {
  daily_summary?: DailySummary
  profile?: UserProfile
  creatine_status?: TodayCreatineStatus
  weekly_workout_stats?: WeeklyWorkoutStats
  weight_trend: Measurement[]
  daily_water_summary?: DailyWaterSummary
  new_achievements: UserAchievement[]
  achievement_progress: AchievementProgress[]
  notifications: string[]
}

// ---------------------------------------------------------------------------
// Axios Instance
// ---------------------------------------------------------------------------

// Base URL - Capacitor mobil + web desteği
// Mobilde Capacitor native context'te çalışırken localhost yerine gerçek IP/domain kullan
function getBaseUrl(): string {
  // Production ortamı — environment variable varsa kullan
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  // Capacitor native context (Android/iOS app)
  if (typeof window !== 'undefined' && (window as any).Capacitor?.isNativePlatform?.()) {
    // Geliştirme: bilgisayarın IP'si (aynı WiFi'da olmalı)
    // Production: gerçek domain
    return import.meta.env.VITE_API_URL_NATIVE || 'http://10.0.2.2:8000' // Android emülatör için
  }
  // Web geliştirme — Vite proxy kullanır
  return ''
}

const api = axios.create({ 
  baseURL: getBaseUrl(),
  headers: {
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  }
})

// ---------------------------------------------------------------------------
// Interceptor Setup Function
// ---------------------------------------------------------------------------

// Setup function to initialize axios interceptors
// This ensures interceptors are properly configured when the app starts
export function setupInterceptors() {
  // ---------------------------------------------------------------------------
  // Request Interceptor - Token Injection
  // ---------------------------------------------------------------------------

  // Add request interceptor to automatically inject authentication token
  api.interceptors.request.use(
    (config) => {
      // Get token from localStorage
      const token = localStorage.getItem('auth_token')
      
      // If token exists, add to Authorization header
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // ---------------------------------------------------------------------------
  // Response Interceptor - 401 Error Handling
  // ---------------------------------------------------------------------------

  // Add response interceptor to handle 401 Unauthorized errors
  api.interceptors.response.use(
    (response) => {
      // On successful response, return response as-is
      return response
    },
    (error) => {
      // Check if error status is 401 Unauthorized
      if (error.response && error.response.status === 401) {
        // Clear token from localStorage
        localStorage.removeItem('auth_token')
        
        // Redirect to login page
        window.location.href = '/login'
      }
      
      // For other errors, return rejected promise
      return Promise.reject(error)
    }
  )
}

// ---------------------------------------------------------------------------
// Besin API'leri
// ---------------------------------------------------------------------------

export const foodsApi = {
  search: (q: string) => api.get<FoodItem[]>('/api/foods/search', { params: { q } }),
  scrape: () => api.post('/api/foods/scrape'),
}

// ---------------------------------------------------------------------------
// Kalori Günlüğü API'leri
// ---------------------------------------------------------------------------

export const logApi = {
  getDaily: (date: string) => api.get<DailySummary>(`/api/log/${date}`),
  add: (entry: FoodLogCreate) => api.post<FoodLogEntry>('/api/log/', entry),
  delete: (id: number) => api.delete(`/api/log/${id}`),
}

// ---------------------------------------------------------------------------
// Profil API'leri
// ---------------------------------------------------------------------------

export const profileApi = {
  get: () => api.get<UserProfile>('/api/profile/'),
  update: (data: UserProfileUpdate) => api.put<UserProfile>('/api/profile/', data),
  delete: () => api.delete('/api/profile/'),
}

// ---------------------------------------------------------------------------
// Antrenman API'leri
// ---------------------------------------------------------------------------

export const workoutsApi = {
  listPrograms: () => api.get<WorkoutProgram[]>('/api/workouts/programs'),
  createProgram: (data: WorkoutProgramCreate) => api.post<WorkoutProgram>('/api/workouts/programs', data),
  deleteProgram: (id: number) => api.delete(`/api/workouts/programs/${id}`),
  logWorkout: (data: WorkoutLogCreate) => api.post<WorkoutLog>('/api/workouts/log', data),
  deleteWorkoutLog: (id: number) => api.delete(`/api/workouts/log/${id}`),
  getHistory: (weeks?: number) => api.get<WorkoutLog[]>('/api/workouts/history', { params: { weeks } }),
  getProgress: (exerciseName: string) => api.get(`/api/workouts/progress/${exerciseName}`),
  getStats: () => api.get<WeeklyWorkoutStats>('/api/workouts/stats'),
}

// ---------------------------------------------------------------------------
// Kreatin API'leri
// ---------------------------------------------------------------------------

export const creatineApi = {
  getStatus: () => api.get<TodayCreatineStatus>('/api/creatine/status'),
  logDose: (data: CreatineDoseCreate) => api.post<CreatineDose>('/api/creatine/log', data),
  delete: (id: number) => api.delete(`/api/creatine/${id}`),
  getHistory: (days?: number) => api.get<CreatineDose[]>('/api/creatine/history', { params: { days } }),
}

// ---------------------------------------------------------------------------
// Ölçüm API'leri
// ---------------------------------------------------------------------------

export const measurementsApi = {
  getHistory: () => api.get<Measurement[]>('/api/measurements/'),
  add: (data: MeasurementCreate) => api.post<Measurement>('/api/measurements/', data),
  delete: (id: number) => api.delete(`/api/measurements/${id}`),
  getTrend: (days?: number) => api.get<Measurement[]>('/api/measurements/trend', { params: { days } }),
  getDelta: () => api.get<MeasurementDelta>('/api/measurements/delta'),
}

// ---------------------------------------------------------------------------
// Pano API'si
// ---------------------------------------------------------------------------

export const dashboardApi = {
  get: () => api.get<DashboardSnapshot>('/api/dashboard/', {
    params: { _t: Date.now() }, // Cache busting timestamp
    headers: {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache'
    }
  }),
}

// ---------------------------------------------------------------------------
// Yemek Planlayıcı API'si
// ---------------------------------------------------------------------------

export interface MealSuggestion {
  meal_type: string
  food_name: string
  grams: number
  calories: number
  protein: number
  carbs: number
  fat: number
  protein_ratio?: number  // Protein oranı (%)
}

export interface DayPlan {
  date: string
  meals: MealSuggestion[]
  total_calories: number
  total_protein: number
  total_carbs: number
  total_fat: number
  protein_percentage?: number  // Günlük protein yüzdesi
}

export interface GoalInfo {
  goal: string
  goal_name: string
  daily_calories: number
  daily_protein: number
  daily_carbs: number
  daily_fat: number
  protein_ratio: number
  carbs_ratio: number
  fat_ratio: number
  bmi?: number
  goal_warning?: {
    type: string
    title: string
    message: string
    recommended_goal: string
    recommended_goal_name: string
  }
}

export interface WeeklyMealPlan {
  goal_info?: GoalInfo
  days: DayPlan[]
  shopping_list: Record<string, number>
}

// ---------------------------------------------------------------------------
// Su Takibi Tip Tanımları
// ---------------------------------------------------------------------------

export interface WaterLogCreate {
  user_id: number
  amount_ml: number
}

export interface WaterLog {
  id: number
  user_id: number
  amount_ml: number
  logged_at: string
}

export interface DailyWaterSummary {
  date: string
  total_ml: number
  goal_ml: number
  percentage: number
  entries: WaterLog[]
}

// ---------------------------------------------------------------------------
// Başarı Rozetleri Tip Tanımları
// ---------------------------------------------------------------------------

export interface Achievement {
  id: number
  name: string
  description: string
  icon: string
  category: string
  condition_type: string
  condition_value: number
  points: number
  created_at: string
}

export interface UserAchievement {
  id: number
  user_id: number
  achievement_id: number
  earned_at: string
  is_new: boolean
  achievement: Achievement
}

export interface AchievementProgress {
  achievement: Achievement
  current_value: number
  target_value: number
  percentage: number
  is_completed: boolean
}

export const mealPlanApi = {
  getWeekly: () => api.get<WeeklyMealPlan>('/api/meal-plan/weekly'),
}

// ---------------------------------------------------------------------------
// Su Takibi API'leri
// ---------------------------------------------------------------------------

export const waterApi = {
  getDailySummary: (userId: number = 1, targetDate?: string) => 
    api.get<DailyWaterSummary>('/api/water/daily-summary', { 
      params: { user_id: userId, target_date: targetDate } 
    }),
  addLog: (data: WaterLogCreate) => api.post<WaterLog>('/api/water/log', data),
  getLogs: (userId: number = 1, startDate?: string, endDate?: string) =>
    api.get<WaterLog[]>('/api/water/logs', { 
      params: { user_id: userId, start_date: startDate, end_date: endDate } 
    }),
  deleteLog: (logId: number, userId: number = 1) =>
    api.delete(`/api/water/log/${logId}`, { params: { user_id: userId } }),
  getWeeklyStats: (userId: number = 1) =>
    api.get('/api/water/weekly-stats', { params: { user_id: userId } }),
  quickAdd: (amountMl: number, userId: number = 1) =>
    api.post<WaterLog>(`/api/water/quick-add/${amountMl}`, {}, { params: { user_id: userId } }),
}

// ---------------------------------------------------------------------------
// Başarı Rozetleri API'leri
// ---------------------------------------------------------------------------

export const achievementsApi = {
  getAll: () => api.get<Achievement[]>('/api/achievements/'),
  getUserAchievements: (userId: number) => 
    api.get<UserAchievement[]>(`/api/achievements/user/${userId}`),
  getProgress: (userId: number) => 
    api.get<AchievementProgress[]>(`/api/achievements/progress/${userId}`),
  markAsSeen: (userId: number) => 
    api.post(`/api/achievements/mark-seen/${userId}`),
  manualCheck: (userId: number, activityType: string = 'manual') =>
    api.post(`/api/achievements/check/${userId}`, {}, { params: { activity_type: activityType } }),
  getStats: (userId: number) =>
    api.get(`/api/achievements/stats/${userId}`),
  initialize: () => api.post('/api/achievements/initialize'),
}

// ---------------------------------------------------------------------------
// Dışa Aktarma API'si
// ---------------------------------------------------------------------------

export const exportApi = {
  export: (type: string, fromDate?: string, toDate?: string) =>
    api.get('/api/export/', {
      params: { type, from_date: fromDate, to_date: toDate },
      responseType: 'blob',
    }),
}

// ---------------------------------------------------------------------------
// AI Besin Asistanı API'leri
// ---------------------------------------------------------------------------

export interface NutritionData {
  food_name: string
  calories_per_100g: number
  protein_per_100g: number
  carbs_per_100g: number
  fat_per_100g: number
  confidence: 'high' | 'medium' | 'low'
  source: string
}

export interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: string
  nutrition_data?: NutritionData
}

export interface ChatRequest {
  message: string
  session_id: string
  user_id: number
}

export interface ChatResponse {
  response: string
  nutrition_data?: NutritionData
  session_id: string
  timestamp: string
  error?: string
}

export interface SessionHistory {
  session_id: string
  messages: ChatMessage[]
  created_at: string
  last_activity: string
  message_count: number
}

export const aiAssistantApi = {
  chat: (data: ChatRequest) => api.post<ChatResponse>('/api/ai-assistant/chat', data),
  getSessionHistory: (sessionId: string) => api.get<SessionHistory>(`/api/ai-assistant/session/${sessionId}`),
  clearSession: (sessionId: string) => api.delete(`/api/ai-assistant/session/${sessionId}`),
}

// ---------------------------------------------------------------------------
// Kullanıcı Katkılı Besin Veritabanı API'leri
// ---------------------------------------------------------------------------

export interface ContributionRequest {
  food_name: string
  calories_per_100g: number
  protein_per_100g: number
  carbs_per_100g: number
  fat_per_100g: number
  source: 'homemade' | 'restaurant' | 'package'
  photo_url?: string
  barcode?: string
  brand?: string
}

export interface ContributionResponse {
  success: boolean
  message: string
  points_earned: number
  user_total_points: number
}

export interface LeaderboardEntry {
  user_id: number
  total_points: number
  level: number
  contributions: number
  badges: string[]
  rank: number
}

export interface MissingFoodEntry {
  food_name: string
  votes: number
  suggested_by: number
  days_ago: number
}

export interface VerificationQueueEntry {
  id: number
  food_name: string
  calories: number
  protein: number
  carbs: number
  fat: number
  source: string
  confidence: number
  verifications_needed: number
}

export interface UserStats {
  total_points: number
  level: number
  contributions: number
  verifications: number
  suggestions: number
  badges: string[]
  rank: number
}

export interface DailyChallenge {
  type: string
  category?: string
  food_suggestions?: string[]
  target?: number
  reward_points: number
  description: string
}

export interface SystemStats {
  total_contributions: number
  total_suggestions: number
  total_users: number
  pending_verifications: number
  database_size: number
}

export const crowdsourceApi = {
  // Katkı ekleme
  addContribution: (data: ContributionRequest) => 
    api.post<ContributionResponse>('/api/crowdsource/contribute', data),
  
  // Doğrulama
  verifyContribution: (contributionId: number, isCorrect: boolean) =>
    api.post(`/api/crowdsource/verify/${contributionId}`, { contribution_id: contributionId, is_correct: isCorrect }),
  
  // Eksik besin önerisi
  suggestMissingFood: (foodName: string) =>
    api.post('/api/crowdsource/suggest', { food_name: foodName }),
  
  // Listeler
  getMissingFoods: (limit: number = 20) =>
    api.get<MissingFoodEntry[]>('/api/crowdsource/missing-foods', { params: { limit } }),
  
  getLeaderboard: (limit: number = 10) =>
    api.get<LeaderboardEntry[]>('/api/crowdsource/leaderboard', { params: { limit } }),
  
  getVerificationQueue: (limit: number = 10) =>
    api.get<VerificationQueueEntry[]>('/api/crowdsource/verification-queue', { params: { limit } }),
  
  // Kullanıcı istatistikleri
  getUserStats: (userId: number = 1) =>
    api.get<UserStats>('/api/crowdsource/user-stats', { params: { user_id: userId } }),
  
  // Challenge'lar
  getDailyChallenges: () =>
    api.get<{ challenges: DailyChallenge[] }>('/api/crowdsource/daily-challenges'),
  
  // Sistem istatistikleri
  getSystemStats: () =>
    api.get<SystemStats>('/api/crowdsource/stats'),
}

// ---------------------------------------------------------------------------
// AI Coach API'leri
// ---------------------------------------------------------------------------

export interface WorkoutRecommendation {
  id: number
  type: string
  workout_plan?: {
    exercises: Array<{
      name: string
      sets?: number
      reps?: string
      duration?: number
      intensity?: string
      rest?: number
    }>
    warm_up: string
    cool_down: string
    total_duration: number
    notes: string
  }
  intensity: string
  duration: number
  motivation_message: string
  calorie_analysis: {
    daily_calories: number
    target_calories: number
    calorie_balance: number
    calorie_percentage: number
    status: string
  }
  created_at: string
}

export interface FeedbackRequest {
  recommendation_id: number
  feedback: 'accepted' | 'rejected' | 'modified'
  reason?: string
}

export interface FeedbackResponse {
  success: boolean
  message: string
}

export interface ProgressInsights {
  weekly_stats: Array<{
    week: string
    workouts: number
    avg_duration: number
  }>
  overall_trend: string
  total_workouts: number
  consistency_score: number
}

export interface CoachStatus {
  status: string
  user_id: number
  last_recommendation?: string
  total_recommendations: number
  acceptance_rate: number
  message: string
}

export const aiCoachApi = {
  getRecommendation: () => api.get<WorkoutRecommendation>('/api/ai-coach/recommendation'),
  submitFeedback: (data: FeedbackRequest) => api.post<FeedbackResponse>('/api/ai-coach/feedback', data),
  getProgress: () => api.get<ProgressInsights>('/api/ai-coach/progress'),
  getStatus: () => api.get<CoachStatus>('/api/ai-coach/status'),
  healthCheck: () => api.get('/api/ai-coach/health'),
}

export default api
