import { useState, useMemo, useCallback } from 'react'
import { Search, Plus, Trash2, Calendar, Utensils } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { FoodSearchResults } from '@/components/FoodSearchResults'
import { useFoodLog, useAddFoodLog, useDeleteFoodLog, useFoodSearch } from '@/hooks/useFoodLog'
import { format } from 'date-fns'
import { useDebounce } from '@/hooks/useDebounce'
import { useCurrentUserId } from '@/hooks/useCurrentUserId'

const MEAL_LABELS: Record<string, string> = {
  breakfast: 'Kahvaltı',
  lunch: 'Öğle',
  dinner: 'Akşam',
  snack: 'Ara Öğün',
}

const MEAL_COLORS: Record<string, string> = {
  breakfast: 'text-amber-400',
  lunch: 'text-emerald-400',
  dinner: 'text-violet-400',
  snack: 'text-blue-400',
}

export default function FoodLog() {
  const userId = useCurrentUserId()
  const [selectedDate, setSelectedDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFood, setSelectedFood] = useState<any>(null)
  const [grams, setGrams] = useState('')
  const [mealType, setMealType] = useState('breakfast')

  const debouncedSearchQuery = useDebounce(searchQuery, 600)
  const { data: dailySummary, isLoading, error } = useFoodLog(selectedDate)
  const { data: searchResults, isLoading: isSearching } = useFoodSearch(debouncedSearchQuery)
  const addMutation = useAddFoodLog()
  const deleteMutation = useDeleteFoodLog()

  const safeSummary = dailySummary || { date: selectedDate, total_calories: 0, total_protein: 0, total_carbs: 0, total_fat: 0, entries: [] }

  const previewNutrition = useMemo(() => {
    if (!selectedFood || !grams) return null
    const g = parseFloat(grams)
    if (isNaN(g) || g <= 0) return null
    return {
      calories: Math.round((selectedFood.calories_per_100g * g) / 100),
      protein: Math.round((selectedFood.protein_per_100g * g) / 100),
      carbs: Math.round((selectedFood.carbs_per_100g * g) / 100),
      fat: Math.round((selectedFood.fat_per_100g * g) / 100),
    }
  }, [selectedFood, grams])

    const handleAddFood = useCallback(() => {
    if (!selectedFood || !grams || addMutation.isPending) return
    const gramsNum = parseFloat(grams)
    if (isNaN(gramsNum) || gramsNum <= 0) return
    
    addMutation.mutate({
      user_id: userId,
      food_item_id: selectedFood.id,
      food_name: selectedFood.name,
      grams: gramsNum,
      meal_type: mealType,
      logged_at: `${selectedDate}T12:00:00`,
    }, {
      onSuccess: () => {
        setSelectedFood(null)
        setGrams('')
        setSearchQuery('')
      }
    })
  }, [selectedFood, grams, mealType, selectedDate, addMutation])

  const handleFoodSelect = useCallback((food: any) => setSelectedFood(food), [])
  const handleDeleteFood = useCallback((id: number) => deleteMutation.mutate(id), [deleteMutation])

  // Makro yüzdeleri
  const targetCal = 2000
  const macros = [
    { label: 'Protein', value: Math.round(safeSummary.total_protein), color: 'bg-violet-500', pct: Math.min(100, Math.round((safeSummary.total_protein / (targetCal * 0.3 / 4)) * 100)) },
    { label: 'Karb', value: Math.round(safeSummary.total_carbs), color: 'bg-amber-500', pct: Math.min(100, Math.round((safeSummary.total_carbs / (targetCal * 0.4 / 4)) * 100)) },
    { label: 'Yağ', value: Math.round(safeSummary.total_fat), color: 'bg-red-500', pct: Math.min(100, Math.round((safeSummary.total_fat / (targetCal * 0.3 / 9)) * 100)) },
  ]

  return (
    <div className="p-5 space-y-4 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-white">Besin Günlüğü</h1>
          <p className="text-[12px] text-white/35 mt-0.5">Günlük kalori ve makro takibi</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-white/[0.08] bg-white/[0.03]">
          <Calendar className="w-3.5 h-3.5 text-white/35" />
          <input
            type="date"
            value={selectedDate}
            onChange={e => setSelectedDate(e.target.value)}
            className="bg-transparent text-[13px] text-white/70 focus:outline-none"
          />
        </div>
      </div>

      {error && (
        <div className="px-3 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-[12px]">
          API bağlantı hatası.
        </div>
      )}

      {/* Özet kartları */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="rounded-xl border border-white/[0.07] bg-[#13131a] p-4">
          <p className="text-[10px] text-white/35 uppercase tracking-widest font-medium">Kalori</p>
          <p className="text-xl font-semibold text-white mt-1">{Math.round(safeSummary.total_calories)}</p>
          <p className="text-[11px] text-white/25 mt-0.5">kcal</p>
        </div>
        {macros.map(m => (
          <div key={m.label} className="rounded-xl border border-white/[0.07] bg-[#13131a] p-4">
            <p className="text-[10px] text-white/35 uppercase tracking-widest font-medium">{m.label}</p>
            <p className="text-xl font-semibold text-white mt-1">{m.value}g</p>
            <div className="mt-2 h-1 rounded-full bg-white/[0.06]">
              <div className={`h-full rounded-full ${m.color} transition-all duration-500`} style={{ width: `${m.pct}%` }} />
            </div>
          </div>
        ))}
      </div>

      {/* Besin Ekleme */}
      <GlassCard className="p-5">
        <h2 className="text-[13px] font-semibold text-white mb-4">Besin Ekle</h2>
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-white/25 w-4 h-4" />
            <Input
              placeholder="Besin ara... (en az 3 karakter)"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          <FoodSearchResults
            results={searchResults || []}
            selectedFood={selectedFood}
            onFoodSelect={handleFoodSelect}
            isSearching={isSearching}
            maxResults={6}
          />

          {selectedFood && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
              <div>
                <label className="text-[11px] text-white/40 mb-1.5 block uppercase tracking-wide">Gram</label>
                <Input type="number" placeholder="100" value={grams} onChange={e => setGrams(e.target.value)} />
              </div>
              <div>
                <label className="text-[11px] text-white/40 mb-1.5 block uppercase tracking-wide">Öğün</label>
                <select
                  value={mealType}
                  onChange={e => setMealType(e.target.value)}
                  className="w-full rounded-lg px-3 py-2 text-[13px] text-white/80 bg-white/[0.05] border border-white/[0.08] focus:outline-none focus:ring-1 focus:ring-violet-500/60"
                >
                  <option value="breakfast">Kahvaltı</option>
                  <option value="lunch">Öğle</option>
                  <option value="dinner">Akşam</option>
                  <option value="snack">Ara Öğün</option>
                </select>
              </div>
              <div className="flex items-end">
                <Button onClick={handleAddFood} disabled={!grams || addMutation.isPending} className="w-full">
                  <Plus className="w-4 h-4" />
                  Ekle
                </Button>
              </div>
            </div>
          )}

          {previewNutrition && (
            <div className="grid grid-cols-4 gap-2 p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
              {[
                { label: 'Kalori', value: previewNutrition.calories, unit: 'kcal', color: 'text-white' },
                { label: 'Protein', value: previewNutrition.protein, unit: 'g', color: 'text-violet-400' },
                { label: 'Karb', value: previewNutrition.carbs, unit: 'g', color: 'text-amber-400' },
                { label: 'Yağ', value: previewNutrition.fat, unit: 'g', color: 'text-red-400' },
              ].map(item => (
                <div key={item.label} className="text-center">
                  <p className="text-[10px] text-white/30">{item.label}</p>
                  <p className={`text-sm font-semibold ${item.color}`}>{item.value}<span className="text-[10px] text-white/30 ml-0.5">{item.unit}</span></p>
                </div>
              ))}
            </div>
          )}
        </div>
      </GlassCard>

      {/* Kayıtlar */}
      <GlassCard className="p-5">
        <h2 className="text-[13px] font-semibold text-white mb-4">Günün Kayıtları</h2>
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map(i => <div key={i} className="h-14 rounded-lg bg-white/[0.04] animate-pulse" />)}
          </div>
        ) : safeSummary.entries.length === 0 ? (
          <div className="text-center py-8">
            <Utensils className="w-8 h-8 text-white/15 mx-auto mb-2" />
            <p className="text-[13px] text-white/30">Henüz kayıt yok</p>
          </div>
        ) : (
          <div className="space-y-1.5">
            {safeSummary.entries.map(entry => (
              <div key={entry.id} className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.05] transition-colors group">
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] text-white/80 font-medium truncate">{entry.food_name}</p>
                  <p className="text-[11px] text-white/30 mt-0.5">
                    <span className={MEAL_COLORS[entry.meal_type] ?? 'text-white/40'}>{MEAL_LABELS[entry.meal_type] ?? entry.meal_type}</span>
                    {' · '}{entry.grams}g{' · '}{Math.round(entry.calories)} kcal
                  </p>
                </div>
                <div className="flex items-center gap-3 ml-3">
                  <div className="hidden sm:flex items-center gap-3 text-[11px] text-white/25">
                    <span>P: {Math.round(entry.protein)}g</span>
                    <span>K: {Math.round(entry.carbs)}g</span>
                    <span>Y: {Math.round(entry.fat)}g</span>
                  </div>
                  <button
                    onClick={() => handleDeleteFood(entry.id)}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-md text-white/30 hover:text-red-400 hover:bg-red-500/10 transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  )
}
