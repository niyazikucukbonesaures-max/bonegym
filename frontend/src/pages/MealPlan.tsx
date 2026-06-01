import { useState } from 'react'
import { Calendar, ShoppingCart, ChefHat, Download } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { mealPlanApi, type WeeklyMealPlan } from '@/lib/api'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'

export default function MealPlan() {
  const [selectedDay, setSelectedDay] = useState(0)
  const [showShoppingList, setShowShoppingList] = useState(false)
  
  const { data: mealPlan, isLoading, error, refetch } = useQuery<WeeklyMealPlan>({
    queryKey: ['mealPlan'],
    queryFn: () => mealPlanApi.getWeekly().then(r => r.data),
    staleTime: 1000 * 60 * 60, // 1 saat cache
    retry: 1, // Sadece 1 kez tekrar dene
  })

  // FALLBACK DATA - API çalışmazsa
  const fallbackPlan: WeeklyMealPlan = {
    days: [],
    shopping_list: {},
    goal_info: undefined
  }

  const safeMealPlan = mealPlan || fallbackPlan

  const getMealTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      breakfast: 'Kahvaltı',
      lunch: 'Öğle Yemeği',
      dinner: 'Akşam Yemeği',
      snack: 'Atıştırmalık'
    }
    return labels[type] || type
  }

  const getMealTypeIcon = (type: string) => {
    switch (type) {
      case 'breakfast': return '🍳'
      case 'lunch': return '🍽️'
      case 'dinner': return '🍲'
      case 'snack': return '🍎'
      default: return '🍴'
    }
  }

  const getDayName = (dateStr: string) => {
    const date = new Date(dateStr)
    const days = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi']
    return days[date.getDay()]
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('tr-TR', { day: 'numeric', month: 'long' })
  }

  const getGoalColor = (goal: string) => {
    switch (goal) {
      case 'kilo_verme': return 'text-orange-400'
      case 'kas_kazanma': return 'text-emerald-400'
      case 'vucut_rekomposizyonu': return 'text-violet-400'
      default: return 'text-cyan-400'
    }
  }

  const getGoalIcon = (goal: string) => {
    switch (goal) {
      case 'kilo_verme': return '🔥'
      case 'kas_kazanma': return '💪'
      case 'vucut_rekomposizyonu': return '⚡'
      default: return '🎯'
    }
  }

  const getGoalDescription = (goal: string) => {
    switch (goal) {
      case 'kilo_verme': 
        return 'Yağ yakma odaklı, kas koruyucu beslenme planı'
      case 'kas_kazanma': 
        return 'Kilo alma ve kas yapma odaklı, yüksek kalorili plan'
      case 'vucut_rekomposizyonu': 
        return 'Yağ yakma + kas koruma dengeli, yüksek proteinli plan'
      default: 
        return 'Dengeli ve sürdürülebilir beslenme planı'
    }
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-violet-500" />
        </div>
      </div>
    )
  }

  if (error || !safeMealPlan || safeMealPlan.days.length === 0) {
    return (
      <div className="p-6 space-y-6">
        <GlassCard className="p-6">
          <p className="text-white mb-2">⚠️ Plan oluşturulamadı.</p>
          <p className="text-white/60 text-sm mb-4">
            {error ? 'API bağlantı hatası. Backend çalışmıyor olabilir.' : 'Profil bilgilerinizi kontrol edin.'}
          </p>
          <Button onClick={() => refetch()} className="mt-4">Yeniden Dene</Button>
        </GlassCard>
      </div>
    )
  }

  const currentDay = safeMealPlan.days[selectedDay]
  const goalInfo = safeMealPlan.goal_info

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <ChefHat className="text-violet-400" size={32} />
            Yemek Planlayıcı
          </h1>
          <p className="text-white/60 mt-1">Hedefine uygun haftalık menü</p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={() => setShowShoppingList(!showShoppingList)}
            variant="outline"
            className="border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/10"
          >
            <ShoppingCart size={18} className="mr-2" />
            Alışveriş Listesi
          </Button>
          <Button
            onClick={() => refetch()}
            className="bg-gradient-to-r from-violet-500 to-purple-600"
          >
            <Calendar size={18} className="mr-2" />
            Yeni Plan Oluştur
          </Button>
        </div>
      </div>

      {/* Hedef Uyarısı (BMI bazlı) */}
      {goalInfo?.goal_warning && (
        <GlassCard className={`p-6 border-2 ${
          goalInfo.goal_warning.type === 'error' 
            ? 'bg-red-500/10 border-red-500/50' 
            : 'bg-orange-500/10 border-orange-500/50'
        }`}>
          <div className="flex items-start gap-4">
            <div className="text-4xl">
              {goalInfo.goal_warning.type === 'error' ? '🚨' : '⚠️'}
            </div>
            <div className="flex-1">
              <h3 className={`text-xl font-bold mb-2 ${
                goalInfo.goal_warning.type === 'error' ? 'text-red-400' : 'text-orange-400'
              }`}>
                {goalInfo.goal_warning.title}
              </h3>
              <p className="text-white/90 mb-4 leading-relaxed">
                {goalInfo.goal_warning.message}
              </p>
              <div className="flex items-center gap-3">
                <Button
                  onClick={() => {
                    // Profil sayfasına yönlendir
                    window.location.href = '/profile'
                  }}
                  className="bg-gradient-to-r from-violet-500 to-purple-600"
                >
                  Hedefimi Değiştir
                </Button>
                <span className="text-white/60 text-sm">
                  Önerilen: {goalInfo.goal_warning.recommended_goal_name}
                </span>
              </div>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Hedef Bilgisi */}
      {goalInfo && (
        <GlassCard className="p-6 bg-gradient-to-r from-violet-500/10 to-purple-500/10 border-violet-500/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="text-4xl">{getGoalIcon(goalInfo.goal)}</div>
              <div>
                <h3 className={`text-xl font-bold ${getGoalColor(goalInfo.goal)}`}>
                  {goalInfo.goal_name}
                </h3>
                <p className="text-white/70 text-sm mt-1">
                  {getGoalDescription(goalInfo.goal)}
                </p>
                <div className="flex items-center gap-4 mt-2">
                  <p className="text-white/50 text-xs">
                    Günlük hedef: {Math.round(goalInfo.daily_calories)} kalori
                  </p>
                  {goalInfo.bmi && (
                    <p className="text-white/50 text-xs">
                      • BMI: {goalInfo.bmi}
                    </p>
                  )}
                </div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-6 text-center">
              <div>
                <p className="text-white/60 text-xs uppercase tracking-wider mb-1">Protein</p>
                <p className="text-emerald-400 font-bold text-lg">
                  {Math.round(goalInfo.protein_ratio * 100)}%
                </p>
                <p className="text-white/50 text-xs">{Math.round(goalInfo.daily_protein)}g/gün</p>
              </div>
              <div>
                <p className="text-white/60 text-xs uppercase tracking-wider mb-1">Karb</p>
                <p className="text-orange-400 font-bold text-lg">
                  {Math.round(goalInfo.carbs_ratio * 100)}%
                </p>
                <p className="text-white/50 text-xs">{Math.round(goalInfo.daily_carbs)}g/gün</p>
              </div>
              <div>
                <p className="text-white/60 text-xs uppercase tracking-wider mb-1">Yağ</p>
                <p className="text-red-400 font-bold text-lg">
                  {Math.round(goalInfo.fat_ratio * 100)}%
                </p>
                <p className="text-white/50 text-xs">{Math.round(goalInfo.daily_fat)}g/gün</p>
              </div>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Alışveriş Listesi Modal */}
      {showShoppingList && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <GlassCard className="p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                <ShoppingCart className="text-emerald-400" />
                Haftalık Alışveriş Listesi
              </h3>
              <Button
                onClick={() => setShowShoppingList(false)}
                variant="outline"
                size="sm"
              >
                Kapat
              </Button>
            </div>
            <div className="space-y-2">
              {Object.entries(safeMealPlan.shopping_list)
                .sort(([a], [b]) => a.localeCompare(b, 'tr'))
                .map(([food, grams]) => (
                  <div
                    key={food}
                    className="flex items-center justify-between p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
                  >
                    <span className="text-white">{food}</span>
                    <span className="text-violet-400 font-semibold">
                      {Math.round(grams)}g
                    </span>
                  </div>
                ))}
            </div>
            <Button
              onClick={() => {
                // TODO: PDF export
                alert('PDF export özelliği yakında eklenecek!')
              }}
              className="w-full mt-4"
            >
              <Download size={18} className="mr-2" />
              PDF İndir
            </Button>
          </GlassCard>
        </div>
      )}

      {/* Gün Seçici */}
      <div className="grid grid-cols-7 gap-2">
        {safeMealPlan.days.map((day, index) => (
          <button
            key={day.date}
            onClick={() => setSelectedDay(index)}
            className={`p-3 rounded-xl transition-all ${
              selectedDay === index
                ? 'bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-lg scale-105'
                : 'bg-white/5 text-white/60 hover:bg-white/10'
            }`}
          >
            <div className="text-xs font-medium">{getDayName(day.date)}</div>
            <div className="text-lg font-bold mt-1">
              {new Date(day.date).getDate()}
            </div>
          </button>
        ))}
      </div>

      {/* Günlük Özet */}
      <GlassCard className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">
            {getDayName(currentDay.date)} - {formatDate(currentDay.date)}
          </h2>
          <div className="flex gap-4 text-sm">
            <div className="text-center">
              <p className="text-white/60">Kalori</p>
              <p className="text-white font-semibold">{Math.round(currentDay.total_calories)}</p>
            </div>
            <div className="text-center">
              <p className="text-white/60">Protein</p>
              <p className="text-emerald-400 font-semibold">{Math.round(currentDay.total_protein)}g</p>
            </div>
            <div className="text-center">
              <p className="text-white/60">Karb</p>
              <p className="text-orange-400 font-semibold">{Math.round(currentDay.total_carbs)}g</p>
            </div>
            <div className="text-center">
              <p className="text-white/60">Yağ</p>
              <p className="text-red-400 font-semibold">{Math.round(currentDay.total_fat)}g</p>
            </div>
            {currentDay.protein_percentage && (
              <div className="text-center">
                <p className="text-white/60">Protein %</p>
                <p className="text-violet-400 font-semibold">{Math.round(currentDay.protein_percentage)}%</p>
              </div>
            )}
          </div>
        </div>

        {/* Öğünler */}
        <div className="space-y-4">
          {['breakfast', 'lunch', 'dinner', 'snack'].map(mealType => {
            const meals = currentDay.meals.filter(m => m.meal_type === mealType)
            if (meals.length === 0) return null

            return (
              <div key={mealType} className="bg-white/5 rounded-xl p-4">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  <span>{getMealTypeIcon(mealType)}</span>
                  {getMealTypeLabel(mealType)}
                </h3>
                <div className="space-y-2">
                  {meals.map((meal, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
                    >
                      <div className="flex-1">
                        <p className="text-white font-medium">{meal.food_name}</p>
                        <p className="text-white/60 text-sm">{Math.round(meal.grams)}g</p>
                      </div>
                      <div className="flex gap-4 text-sm">
                        <div className="text-right">
                          <p className="text-white/60">Kalori</p>
                          <p className="text-white font-semibold">{Math.round(meal.calories)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-white/60">Protein</p>
                          <p className="text-emerald-400 font-semibold">{Math.round(meal.protein)}g</p>
                        </div>
                        {meal.protein_ratio && (
                          <div className="text-right">
                            <p className="text-white/60">P%</p>
                            <p className="text-violet-400 font-semibold">{Math.round(meal.protein_ratio)}%</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </GlassCard>
    </div>
  )
}
