import { useState } from 'react'
import {
  Flame, Target, Droplets, Trophy, Plus,
  Utensils, Scale, Pill, AlertTriangle,
  Activity, ArrowUp, ArrowDown, Minus, Check, X
} from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import WaterTracker from '@/components/WaterTracker'
import AchievementBanner from '@/components/AchievementBanner'
import NotificationToast from '@/components/NotificationToast'
import { useDashboard } from '@/hooks/useDashboard'
import { useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useCurrentUserId } from '@/hooks/useCurrentUserId'

// ─── Küçük yardımcı bileşenler ────────────────────────────────────────────────

function MetricCard({
  label,
  value,
  sub,
  icon: Icon,
  color = 'violet',
  trend,
}: {
  label: string
  value: string | number
  sub?: string
  icon: React.ElementType
  color?: string
  trend?: 'up' | 'down' | 'neutral'
}) {
  const colorMap: Record<string, string> = {
    violet: 'text-violet-400 bg-violet-500/10',
    orange: 'text-orange-400 bg-orange-500/10',
    blue:   'text-blue-400   bg-blue-500/10',
    emerald:'text-emerald-400 bg-emerald-500/10',
    pink:   'text-pink-400   bg-pink-500/10',
    amber:  'text-amber-400  bg-amber-500/10',
  }
  const cls = colorMap[color] ?? colorMap.violet

  return (
    <div className="rounded-xl border border-white/[0.07] bg-[#13131a] p-4 flex items-start gap-3">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${cls}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[11px] text-white/35 uppercase tracking-widest font-medium">{label}</p>
        <p className="text-lg font-semibold text-white mt-0.5 leading-none">{value}</p>
        {sub && <p className="text-[11px] text-white/30 mt-1">{sub}</p>}
      </div>
      {trend && (
        <div className={`shrink-0 ${trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-white/30'}`}>
          {trend === 'up' ? <ArrowUp className="w-3.5 h-3.5" /> : trend === 'down' ? <ArrowDown className="w-3.5 h-3.5" /> : <Minus className="w-3.5 h-3.5" />}
        </div>
      )}
    </div>
  )
}

function MacroBar({ label, current, target, color }: { label: string; current: number; target: number; color: string }) {
  const pct = target > 0 ? Math.min(100, Math.round((current / target) * 100)) : 0
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[12px] text-white/50 font-medium">{label}</span>
        <span className="text-[12px] text-white/70 font-medium">{Math.round(current)}g <span className="text-white/30">/ {Math.round(target)}g</span></span>
      </div>
      <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

// ─── Ana Bileşen ──────────────────────────────────────────────────────────────

export default function Dashboard() {
  const userId = useCurrentUserId()
  const [showQuickUpdate, setShowQuickUpdate] = useState(false)
  const [quickWeight, setQuickWeight] = useState('')
  const [weightMsg, setWeightMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [notificationAchievement, setNotificationAchievement] = useState<any>(null)

  const { data: apiData, isLoading, error, refetch } = useDashboard()
  const queryClient = useQueryClient()

  const fallbackData = {
    daily_summary: { total_calories: 0, total_protein: 0, total_carbs: 0, total_fat: 0 },
    profile: { daily_calorie_target: 2200, recommended_calories: 2200, goal: 'maintain', activity_level: 'moderate', height_cm: 175, weight_kg: 75 },
    creatine_status: { taken: false, dose_grams: 0 },
    weekly_workout_stats: { completed: 0, goal: 4 },
    weight_trend: [{ weight_kg: 75, height_cm: 175 }],
    daily_water_summary: { date: new Date().toISOString().split('T')[0], percentage: 0, total_ml: 0, target_ml: 2500, goal_ml: 2500, entries: [] },
    new_achievements: [],
  }

  const data = apiData || fallbackData

  const profile = data.profile
  const summary = data.daily_summary
  const creatine = data.creatine_status
  const workouts = data.weekly_workout_stats
  // const weightTrend = data.weight_trend ?? []  // Şu an kullanılmıyor

  const targetCalories = profile?.daily_calorie_target ?? profile?.recommended_calories ?? 2000
  const consumed = summary?.total_calories ?? 0
  const remaining = Math.max(0, targetCalories - consumed)
  const caloriePercent = targetCalories > 0 ? Math.min(100, Math.round((consumed / targetCalories) * 100)) : 0

  const isRecomp = profile?.goal === 'vucut_rekomposizyonu' || profile?.goal === 'recomp'
  const proteinTarget = (targetCalories * (isRecomp ? 0.40 : 0.30)) / 4
  const carbsTarget   = (targetCalories * (isRecomp ? 0.35 : 0.40)) / 4
  const fatTarget     = (targetCalories * (isRecomp ? 0.25 : 0.30)) / 9

  // Kilo: profil kilosunu göster (ölçümler değil)
  const currentWeight = profile?.weight_kg
  const heightCm = profile?.height_cm
  const bmi = currentWeight && heightCm ? Math.round((currentWeight / Math.pow(heightCm / 100, 2)) * 10) / 10 : null

  const goalLabel: Record<string, string> = {
    kilo_verme: 'Kilo Ver', lose: 'Kilo Ver',
    koruma: 'Koru', maintain: 'Koru',
    kas_kazanma: 'Kas Kazan', gain: 'Kas Kazan',
    vucut_rekomposizyonu: 'Rekomp', recomp: 'Rekomp',
  }

  const activityLabel: Record<string, string> = {
    sedentary: 'Hareketsiz', light: 'Az Aktif',
    moderate: 'Orta', active: 'Aktif', very_active: 'Çok Aktif',
  }

  const handleQuickWeightUpdate = async () => {
    const val = parseFloat(quickWeight)
    if (!quickWeight || isNaN(val) || val < 30 || val > 300) {
      setWeightMsg({ type: 'error', text: 'Geçerli bir kilo girin (30-300 kg)' })
      setTimeout(() => setWeightMsg(null), 3000)
      return
    }

    const currentProfile = data?.profile
    if (!currentProfile) {
      setWeightMsg({ type: 'error', text: 'Profil bulunamadı.' })
      setTimeout(() => setWeightMsg(null), 3000)
      return
    }

    try {
      // 1. Profil kilosunu güncelle (her zaman)
      await api.put('/api/profile/', {
        weight_kg: val,
        height_cm: currentProfile.height_cm,
        age: (currentProfile as any).age ?? 25,
        gender: (currentProfile as any).gender ?? 'male',
        activity_level: currentProfile.activity_level,
        goal: currentProfile.goal,
        weekly_workout_goal: (currentProfile as any).weekly_workout_goal ?? 4,
        daily_calorie_target: currentProfile.daily_calorie_target,
      })

      // 2. Ölçümler tablosuna kayıt ekle - hata olsa bile profil güncellemesi geçerli
      try {
        await api.post('/api/measurements/', {
          user_id: userId,
          weight_kg: val,
        })
      } catch {
        // Ölçüm kaydı başarısız olsa bile (örn. günlük limit) profil güncellendi
        // Sessizce devam et
      }

      setQuickWeight('')
      setShowQuickUpdate(false)
      setWeightMsg({ type: 'success', text: `✓ Kilo güncellendi: ${val} kg` })
      
      // Cache'leri temizle
      queryClient.removeQueries({ queryKey: ['dashboard'] })
      queryClient.removeQueries({ queryKey: ['profile'] })
      queryClient.removeQueries({ queryKey: ['measurements'] })
      
      // Yeniden fetch et
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['dashboard'] })
        queryClient.invalidateQueries({ queryKey: ['profile'] })
      }, 100)
      
      setTimeout(() => setWeightMsg(null), 3000)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      const msg = typeof detail === 'string' ? detail : typeof detail === 'object' && detail?.message ? detail.message : 'Güncelleme başarısız.'
      setWeightMsg({ type: 'error', text: msg })
      setTimeout(() => setWeightMsg(null), 4000)
    }
  }

  if (isLoading && !data) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-white/40 text-sm">Yükleniyor...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-5 space-y-5 max-w-7xl mx-auto">

      {/* Hata */}
      {error && !data && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>API bağlantı hatası.</span>
          <Button variant="ghost" size="sm" onClick={() => refetch()} className="ml-auto text-red-400">Tekrar dene</Button>
        </div>
      )}

      <AchievementBanner newAchievements={data?.new_achievements} onAchievementsSeen={() => refetch()} />
      <NotificationToast achievement={notificationAchievement} onClose={() => setNotificationAchievement(null)} />

      {/* ── Üst metrikler ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard label="Kalori" value={`${Math.round(consumed)}`} sub={`${Math.round(remaining)} kcal kaldı`} icon={Flame} color="orange" />
        <MetricCard label="Kilo" value={currentWeight ? `${currentWeight} kg` : '—'} sub={bmi ? `BMI ${bmi}` : undefined} icon={Scale} color="violet" />
        <MetricCard label="Su" value={`${Math.round(data?.daily_water_summary?.percentage ?? 0)}%`} sub={`${Math.round((data?.daily_water_summary?.total_ml ?? 0) / 1000 * 10) / 10}L / ${Math.round((data?.daily_water_summary?.goal_ml ?? 2500) / 1000 * 10) / 10}L`} icon={Droplets} color="blue" />
        <MetricCard label="Antrenman" value={`${workouts?.completed ?? 0} / ${workouts?.goal ?? 4}`} sub="Bu hafta" icon={Trophy} color="emerald" />
      </div>

      {/* ── Ana içerik ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Sol: Kalori & Makrolar */}
        <GlassCard className="p-5">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-[13px] font-semibold text-white">Günlük Kalori</h3>
              <p className="text-[11px] text-white/35 mt-0.5">Hedef: {Math.round(targetCalories)} kcal</p>
            </div>
            {/* Şık kalori ring - yüzde yerine sayı göster */}
            <div className="relative w-14 h-14">
              <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
                <circle cx="28" cy="28" r="22" stroke="rgba(124,58,237,0.12)" strokeWidth="4" fill="none" />
                <circle
                  cx="28" cy="28" r="22"
                  stroke="#7c3aed"
                  strokeWidth="4"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 22}`}
                  strokeDashoffset={`${2 * Math.PI * 22 * (1 - caloriePercent / 100)}`}
                  className="transition-all duration-700"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-[11px] font-bold text-white leading-none">{caloriePercent}</span>
                <span className="text-[8px] text-white/40 leading-none">%</span>
              </div>
            </div>
          </div>

          {/* Kalori özet */}
          <div className="grid grid-cols-3 gap-2 mb-5">
            {[
              { label: 'Tüketilen', value: Math.round(consumed), color: 'text-white' },
              { label: 'Kalan', value: Math.round(remaining), color: 'text-emerald-400' },
              { label: 'Hedef', value: Math.round(targetCalories), color: 'text-white/50' },
            ].map(item => (
              <div key={item.label} className="text-center p-2.5 rounded-lg bg-white/[0.04]">
                <p className={`text-base font-semibold ${item.color}`}>{item.value}</p>
                <p className="text-[10px] text-white/30 mt-0.5">{item.label}</p>
              </div>
            ))}
          </div>

          {/* Makrolar */}
          <div className="space-y-3">
            <MacroBar label="Protein" current={summary?.total_protein ?? 0} target={proteinTarget} color="bg-violet-500" />
            <MacroBar label="Karbonhidrat" current={summary?.total_carbs ?? 0} target={carbsTarget} color="bg-amber-500" />
            <MacroBar label="Yağ" current={summary?.total_fat ?? 0} target={fatTarget} color="bg-red-500" />
          </div>

          {/* Besin günlüğüne git */}
          <a
            href="/food-log"
            className="mt-4 flex items-center justify-center gap-2 w-full py-2 rounded-lg border border-white/[0.07] text-[12px] text-white/40 hover:text-white/70 hover:border-white/[0.14] transition-colors"
          >
            <Utensils className="w-3.5 h-3.5" />
            Besin Günlüğüne Git
          </a>
        </GlassCard>

        {/* Orta: Su */}
        <WaterTracker waterSummary={data?.daily_water_summary} onWaterAdded={() => refetch()} />

        {/* Sağ: Profil & Kilo */}
        <GlassCard className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[13px] font-semibold text-white">Profil & Kilo</h3>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowQuickUpdate(v => !v)}
            >
              <Plus className="w-3.5 h-3.5" />
              Güncelle
            </Button>
          </div>

          {showQuickUpdate && (
            <div className="mb-4 space-y-2">
              <div className="flex gap-2">
                <Input
                  type="number"
                  placeholder="Yeni kilo (kg)"
                  value={quickWeight}
                  onChange={e => setQuickWeight(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleQuickWeightUpdate()}
                  className="flex-1"
                  min={30}
                  max={300}
                  step={0.1}
                />
                <Button
                  size="sm"
                  onClick={handleQuickWeightUpdate}
                  disabled={!quickWeight}
                >
                  <Check className="w-4 h-4" />                </Button>
                <Button size="sm" variant="ghost" onClick={() => { setShowQuickUpdate(false); setQuickWeight('') }}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
              {weightMsg && (
                <p className={`text-[12px] font-medium ${weightMsg.type === 'success' ? 'text-emerald-400' : 'text-red-400'}`}>
                  {weightMsg.text}
                </p>
              )}
            </div>
          )}

          {/* Başarı mesajı (form kapalıyken) */}
          {!showQuickUpdate && weightMsg && (
            <div className={`mb-3 px-3 py-2 rounded-lg text-[12px] font-medium ${weightMsg.type === 'success' ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
              {weightMsg.text}
            </div>
          )}

          {/* Kilo göstergesi */}
          <div className="text-center py-4 mb-4 rounded-xl bg-white/[0.03] border border-white/[0.05]">
            <p className="text-3xl font-bold text-white">{currentWeight ?? '—'}</p>
            <p className="text-[11px] text-white/35 mt-1">kg</p>
            {bmi && (
              <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-violet-500/10 border border-violet-500/20">
                <span className="text-[11px] text-violet-300 font-medium">BMI {bmi}</span>
              </div>
            )}
          </div>

          {/* Profil bilgileri */}
          <div className="space-y-2">
            {[
              { label: 'Hedef', value: goalLabel[profile?.goal ?? ''] ?? '—', icon: Target },
              { label: 'Aktivite', value: activityLabel[profile?.activity_level ?? ''] ?? '—', icon: Activity },
              { label: 'Kreatin', value: creatine?.taken ? `Alındı (${creatine.dose_grams}g)` : 'Alınmadı', icon: Pill, ok: creatine?.taken },
            ].map(item => (
              <div key={item.label} className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-white/[0.03]">
                <div className="flex items-center gap-2">
                  <item.icon className="w-3.5 h-3.5 text-white/30" />
                  <span className="text-[12px] text-white/45">{item.label}</span>
                </div>
                <span className={`text-[12px] font-medium ${item.ok === false ? 'text-red-400' : item.ok === true ? 'text-emerald-400' : 'text-white/70'}`}>
                  {item.value}
                </span>
              </div>
            ))}

            {/* Kilo durumu */}
            {currentWeight && bmi && (() => {
              const goal = profile?.goal ?? ''
              const isLose = goal === 'lose' || goal === 'kilo_verme'
              const isGain = goal === 'gain' || goal === 'kas_kazanma'
              const isRecompGoal = goal === 'recomp' || goal === 'vucut_rekomposizyonu'

              // BMI sınıflandırması
              let weightStatus: { text: string; color: string; bg: string }
              if (bmi < 18.5) {
                weightStatus = { text: `${(18.5 * Math.pow((heightCm ?? 175) / 100, 2) - currentWeight).toFixed(1)} kg eksik`, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' }
              } else if (bmi < 25) {
                if (isLose) {
                  weightStatus = { text: 'Sağlıklı kiloda', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' }
                } else if (isGain) {
                  weightStatus = { text: 'Kas kazanmaya hazır', color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' }
                } else if (isRecompGoal) {
                  weightStatus = { text: 'Rekomp için ideal', color: 'text-violet-400', bg: 'bg-violet-500/10 border-violet-500/20' }
                } else {
                  weightStatus = { text: 'Hedef kiloda ✓', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' }
                }
              } else if (bmi < 30) {
                const excess = (currentWeight - 24.9 * Math.pow((heightCm ?? 175) / 100, 2)).toFixed(1)
                if (isLose) {
                  weightStatus = { text: `${excess} kg fazla`, color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20' }
                } else {
                  weightStatus = { text: `${excess} kg fazla`, color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20' }
                }
              } else {
                const excess = (currentWeight - 24.9 * Math.pow((heightCm ?? 175) / 100, 2)).toFixed(1)
                weightStatus = { text: `${excess} kg fazla`, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' }
              }

              return (
                <div className={`flex items-center justify-between px-3 py-2.5 rounded-lg border ${weightStatus.bg}`}>
                  <div className="flex items-center gap-2">
                    <Scale className="w-3.5 h-3.5 text-white/30" />
                    <span className="text-[12px] text-white/45">Kilo Durumu</span>
                  </div>
                  <span className={`text-[12px] font-medium ${weightStatus.color}`}>
                    {weightStatus.text}
                  </span>
                </div>
              )
            })()}
          </div>
        </GlassCard>
      </div>

      {/* Uyarı: kayıt yok */}
      {consumed === 0 && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[13px]">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>Bugün henüz yemek kaydı yok. Kalori takibini başlatmak için besin ekleyin.</span>
        </div>
      )}
    </div>
  )
}
