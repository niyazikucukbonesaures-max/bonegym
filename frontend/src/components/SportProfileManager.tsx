// Spor Profili Yönetimi Bileşeni
// Spor tipi seçimi, antrenman sıklığı/yoğunluğu, kalori hedefi önizleme

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Dumbbell, Zap, Target, TrendingUp, Save, ChevronDown } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

// ---------------------------------------------------------------------------
// Tip Tanımları
// ---------------------------------------------------------------------------

interface SportProfile {
  id?: number
  user_id: number
  is_athlete: boolean
  sport_type: string | null
  training_frequency: number
  training_intensity: string
  rest_day_calories_adjustment: number
  training_day_calories_adjustment: number
  preferred_macro_split: Record<string, number> | null
}

interface CalorieTargets {
  base_calories: number
  training_day_calories: number
  rest_day_calories: number
  weekly_average: number
  training_days_per_week: number
  intensity_level: string
}

// ---------------------------------------------------------------------------
// Sabitler
// ---------------------------------------------------------------------------

const SPORT_TYPES = [
  { value: 'strength', label: '🏋️ Güç Antrenmanı', desc: 'Ağırlık, powerlifting' },
  { value: 'endurance', label: '🏃 Dayanıklılık', desc: 'Koşu, bisiklet, yüzme' },
  { value: 'bodybuilding', label: '💪 Vücut Geliştirme', desc: 'Kas kütlesi odaklı' },
  { value: 'crossfit', label: '⚡ CrossFit', desc: 'Fonksiyonel fitness' },
  { value: 'powerlifting', label: '🔥 Powerlifting', desc: 'Maksimal güç' },
  { value: 'mixed', label: '🎯 Karma', desc: 'Birden fazla spor' },
  { value: 'general', label: '🌟 Genel Fitness', desc: 'Genel sağlık ve form' },
]

const INTENSITY_LEVELS = [
  { value: 'low', label: 'Düşük', desc: 'Hafif egzersiz', multiplier: '+%10' },
  { value: 'moderate', label: 'Orta', desc: 'Standart antrenman', multiplier: '+%15' },
  { value: 'high', label: 'Yüksek', desc: 'Yoğun antrenman', multiplier: '+%20' },
  { value: 'very_high', label: 'Çok Yüksek', desc: 'Elit sporcu', multiplier: '+%25' },
]

const api = axios.create({ baseURL: 'http://localhost:8000' })

// ---------------------------------------------------------------------------
// Ana Bileşen
// ---------------------------------------------------------------------------

interface SportProfileManagerProps {
  userId?: number
  onSaved?: () => void
}

export function SportProfileManager({ userId = 1, onSaved }: SportProfileManagerProps) {
  const queryClient = useQueryClient()
  const [isExpanded, setIsExpanded] = useState(false)
  const [saveStatus, setSaveStatus] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const [isAthlete, setIsAthlete] = useState(false)
  const [sportType, setSportType] = useState('general')
  const [frequency, setFrequency] = useState(3)
  const [intensity, setIntensity] = useState('moderate')

  // Mevcut profili yükle
  const { data: existingProfile } = useQuery<SportProfile | null>({
    queryKey: ['sportProfile', userId],
    queryFn: async () => {
      try {
        const res = await api.get(`/api/sport-profiles/?user_id=${userId}`)
        return res.data
      } catch {
        return null
      }
    },
  })

  // Kalori hedeflerini yükle
  const { data: calorieTargets } = useQuery<CalorieTargets>({
    queryKey: ['calorieTargets', userId, frequency, intensity, isAthlete],
    queryFn: async () => {
      const res = await api.get(`/api/sport-profiles/calorie-targets`, {
        params: { user_id: userId, training_day: true, custom_intensity: intensity }
      })
      return res.data
    },
    enabled: isAthlete,
    retry: false,
  })

  // Mevcut profil yüklenince formu doldur
  useEffect(() => {
    if (existingProfile) {
      setIsAthlete(existingProfile.is_athlete)
      setSportType(existingProfile.sport_type || 'general')
      setFrequency(existingProfile.training_frequency)
      setIntensity(existingProfile.training_intensity)
    }
  }, [existingProfile])

  const saveMutation = useMutation({
    mutationFn: async (data: SportProfile) => {
      // localStorage'a kaydet (AICoachWidget okuyacak)
      localStorage.setItem('sport_profile', JSON.stringify({
        sport_type: data.sport_type,
        training_frequency: data.training_frequency,
        training_intensity: data.training_intensity,
        is_athlete: data.is_athlete,
      }))
      // API'ye de kaydet
      try {
        const res = await api.post('/api/sport-profiles/', data)
        return res.data
      } catch {
        return data // API başarısız olsa bile localStorage kaydı yeterli
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sportProfile'] })
      queryClient.invalidateQueries({ queryKey: ['calorieTargets'] })
      setSaveStatus({ type: 'success', text: '✅ Spor profili kaydedildi!' })
      setTimeout(() => setSaveStatus(null), 3000)
      onSaved?.()
    },
    onError: () => {
      setSaveStatus({ type: 'error', text: '❌ Kayıt sırasında hata oluştu.' })
      setTimeout(() => setSaveStatus(null), 4000)
    }
  })

  const handleSave = () => {
    saveMutation.mutate({
      user_id: userId,
      is_athlete: isAthlete,
      sport_type: isAthlete ? sportType : null,
      training_frequency: frequency,
      training_intensity: intensity,
      rest_day_calories_adjustment: 1.05,
      training_day_calories_adjustment: intensity === 'low' ? 1.10 : intensity === 'moderate' ? 1.15 : intensity === 'high' ? 1.20 : 1.25,
      preferred_macro_split: null,
    })
  }

  const selectedSport = SPORT_TYPES.find(s => s.value === sportType)
  const selectedIntensity = INTENSITY_LEVELS.find(i => i.value === intensity)

  return (
    <GlassCard className="overflow-hidden">
      {/* Header - tıklanabilir */}
      <button
        onClick={() => setIsExpanded(prev => !prev)}
        className="w-full p-5 flex items-center justify-between hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
            <Dumbbell size={20} className="text-white" />
          </div>
          <div className="text-left">
            <h3 className="text-base font-semibold text-white">Spor Profili</h3>
            <p className="text-xs text-white/50">
              {isAthlete
                ? `${selectedSport?.label} • Haftada ${frequency} gün • ${selectedIntensity?.label}`
                : 'Sporcu modu kapalı'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isAthlete && (
            <span className="px-2 py-0.5 bg-violet-500/20 text-violet-300 text-xs rounded-full border border-violet-500/30">
              Aktif
            </span>
          )}
          <ChevronDown
            size={18}
            className={`text-white/40 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          />
        </div>
      </button>

      {/* İçerik */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 space-y-5 border-t border-white/10 pt-4">

              {/* Sporcu modu toggle */}
              <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                <div>
                  <p className="text-sm font-medium text-white">Sporcu Modu</p>
                  <p className="text-xs text-white/50">Antrenman günlerine göre kalori ayarla</p>
                </div>
                <button
                  onClick={() => setIsAthlete(prev => !prev)}
                  className={`relative flex-shrink-0 w-11 h-6 rounded-full transition-colors duration-200 ${isAthlete ? 'bg-violet-500' : 'bg-white/20'}`}
                >
                  <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${isAthlete ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </div>

              <AnimatePresence>
                {isAthlete && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="space-y-4"
                  >
                    {/* Spor tipi seçimi */}
                    <div>
                      <label className="text-xs text-white/60 mb-2 block">Spor Türü</label>
                      <div className="grid grid-cols-2 gap-2">
                        {SPORT_TYPES.map(sport => (
                          <button
                            key={sport.value}
                            onClick={() => setSportType(sport.value)}
                            className={`p-2.5 rounded-xl text-left transition-all ${
                              sportType === sport.value
                                ? 'bg-violet-500/30 border border-violet-500/50 text-white'
                                : 'bg-white/5 border border-white/10 text-white/60 hover:bg-white/10'
                            }`}
                          >
                            <p className="text-xs font-medium">{sport.label}</p>
                            <p className="text-xs opacity-60">{sport.desc}</p>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Antrenman sıklığı */}
                    <div>
                      <label className="text-xs text-white/60 mb-2 block">
                        Haftalık Antrenman: <span className="text-white font-medium">{frequency} gün</span>
                      </label>
                      <input
                        type="range"
                        min={1}
                        max={7}
                        value={frequency}
                        onChange={e => setFrequency(parseInt(e.target.value))}
                        className="w-full accent-violet-500"
                      />
                      <div className="flex justify-between text-xs text-white/30 mt-1">
                        <span>1 gün</span>
                        <span>7 gün</span>
                      </div>
                    </div>

                    {/* Antrenman yoğunluğu */}
                    <div>
                      <label className="text-xs text-white/60 mb-2 block">Antrenman Yoğunluğu</label>
                      <div className="grid grid-cols-2 gap-2">
                        {INTENSITY_LEVELS.map(level => (
                          <button
                            key={level.value}
                            onClick={() => setIntensity(level.value)}
                            className={`p-2.5 rounded-xl text-left transition-all ${
                              intensity === level.value
                                ? 'bg-emerald-500/30 border border-emerald-500/50 text-white'
                                : 'bg-white/5 border border-white/10 text-white/60 hover:bg-white/10'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <p className="text-xs font-medium">{level.label}</p>
                              <span className="text-xs text-emerald-400">{level.multiplier}</span>
                            </div>
                            <p className="text-xs opacity-60">{level.desc}</p>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Kalori önizleme */}
                    {calorieTargets && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="p-3 bg-gradient-to-r from-violet-500/10 to-purple-500/10 rounded-xl border border-violet-500/20"
                      >
                        <div className="flex items-center gap-2 mb-3">
                          <Target size={14} className="text-violet-400" />
                          <p className="text-xs font-medium text-violet-300">Kalori Hedefi Önizleme</p>
                        </div>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="text-center">
                            <p className="text-xs text-white/50">Antrenman</p>
                            <p className="text-sm font-bold text-emerald-400">
                              {Math.round(calorieTargets.training_day_calories)}
                            </p>
                            <p className="text-xs text-white/30">kcal</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-white/50">Dinlenme</p>
                            <p className="text-sm font-bold text-blue-400">
                              {Math.round(calorieTargets.rest_day_calories)}
                            </p>
                            <p className="text-xs text-white/30">kcal</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-white/50">Haftalık Ort.</p>
                            <p className="text-sm font-bold text-amber-400">
                              {Math.round(calorieTargets.weekly_average)}
                            </p>
                            <p className="text-xs text-white/30">kcal</p>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Kaydet butonu */}
              <Button
                onClick={handleSave}
                disabled={saveMutation.isPending}
                className="w-full"
              >
                {saveMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Kaydediliyor...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Save size={16} />
                    Spor Profilini Kaydet
                  </span>
                )}
              </Button>

              <AnimatePresence>
                {saveStatus && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    className={`p-3 rounded-lg text-sm font-medium ${
                      saveStatus.type === 'success'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'bg-red-500/20 text-red-300 border border-red-500/30'
                    }`}
                  >
                    {saveStatus.text}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </GlassCard>
  )
}
