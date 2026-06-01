import { useState, useEffect } from 'react'
import { Trash2, Save, Scale, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { profileApi, measurementsApi, type UserProfile } from '@/lib/api'
import { SportProfileManager } from '@/components/SportProfileManager'
import { NotificationManager } from '@/components/NotificationManager'
import { useMeasurements, useDeleteMeasurement, useMeasurementDelta } from '@/hooks/useMeasurements'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'
import { tr } from 'date-fns/locale'
import { useCurrentUserId } from '@/hooks/useCurrentUserId'

const ACTIVITY_OPTIONS = [
  { value: 'sedentary', label: 'Hareketsiz', desc: 'Masa başı iş, egzersiz yok' },
  { value: 'light', label: 'Az Aktif', desc: 'Haftada 1-3 gün hafif egzersiz' },
  { value: 'moderate', label: 'Orta Aktif', desc: 'Haftada 3-5 gün orta egzersiz' },
  { value: 'active', label: 'Aktif', desc: 'Haftada 6-7 gün yoğun egzersiz' },
  { value: 'very_active', label: 'Çok Aktif', desc: 'Günde 2 antrenman veya ağır iş' },
]

const GOAL_OPTIONS = [
  { value: 'lose', label: 'Kilo Ver', desc: 'Kalori açığı ile yağ yak', color: 'text-red-400' },
  { value: 'maintain', label: 'Koru', desc: 'Mevcut kilonu koru', color: 'text-emerald-400' },
  { value: 'gain', label: 'Kas Kazan', desc: 'Kalori fazlası ile kas yap', color: 'text-blue-400' },
  { value: 'recomp', label: 'Rekomp', desc: 'Yağ yak, kas koru', color: 'text-violet-400' },
]

// Temel bilgiler (profil API'sine gider)
const BASIC_FIELDS = [
  { label: 'Kilo (kg)', key: 'weight', placeholder: '75', type: 'number', step: '0.1' },
  { label: 'Boy (cm)', key: 'height', placeholder: '175', type: 'number', step: '1' },
  { label: 'Yaş', key: 'age', placeholder: '25', type: 'number', step: '1' },
  { label: 'Haftalık Antrenman', key: 'weeklyWorkoutGoal', placeholder: '4', type: 'number', step: '1' },
]

// Vücut ölçümleri (ölçüm API'sine gider)
const BODY_FIELDS = [
  { label: 'Bel (cm)', key: 'waist', placeholder: '80', min: 40, max: 200 },
  { label: 'Kalça (cm)', key: 'hip', placeholder: '95', min: 50, max: 200 },
  { label: 'Göğüs (cm)', key: 'chest', placeholder: '100', min: 60, max: 200 },
  { label: 'Kol (cm)', key: 'arm', placeholder: '35', min: 15, max: 80 },
  { label: 'Bacak (cm)', key: 'leg', placeholder: '55', min: 30, max: 120 },
]

export default function Profile() {
  const userId = useCurrentUserId()
  const queryClient = useQueryClient()
  const [saveMsg, setSaveMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  const { data: profile } = useQuery<UserProfile>({
    queryKey: ['profile'],
    queryFn: () => profileApi.get().then(r => r.data),
  })

  const { data: measurements } = useMeasurements()
  const { data: delta } = useMeasurementDelta()
  const deleteMeasurementMutation = useDeleteMeasurement()

  const [form, setForm] = useState({
    // Profil alanları
    weight: '', height: '', age: '',
    gender: 'male', activityLevel: 'moderate', goal: 'maintain', weeklyWorkoutGoal: '',
    fitnessLevel: 'beginner',
    // Manuel kalori hedefi
    manualCalorieTarget: '',
    useManualCalorie: false,
    // Vücut ölçüm alanları
    waist: '', hip: '', chest: '', arm: '', leg: '',
  })

  // Profil yüklenince form'u doldur
  useEffect(() => {
    if (!profile) return
    const actMap: Record<string, string> = {
      sedentary: 'sedentary', light: 'light', moderate: 'moderate',
      active: 'active', very_active: 'very_active',
    }
    const goalMap: Record<string, string> = {
      lose: 'lose', maintain: 'maintain', gain: 'gain', recomp: 'recomp',
      kilo_verme: 'lose', koruma: 'maintain', kas_kazanma: 'gain', vucut_rekomposizyonu: 'recomp',
    }
    setForm(prev => ({
      ...prev,
      weight: profile.weight_kg?.toString() ?? '',
      height: profile.height_cm?.toString() ?? '',
      age: profile.age?.toString() ?? '',
      gender: profile.gender === 'female' ? 'female' : 'male',
      activityLevel: actMap[profile.activity_level] ?? 'moderate',
      goal: goalMap[profile.goal] ?? 'maintain',
      weeklyWorkoutGoal: profile.weekly_workout_goal?.toString() ?? '',
      fitnessLevel: profile.fitness_level ?? 'beginner',
      manualCalorieTarget: profile.daily_calorie_target?.toString() ?? '',
      useManualCalorie: !!profile.daily_calorie_target,
    }))
  }, [profile])

  // En son ölçümden vücut ölçümlerini doldur
  useEffect(() => {
    if (!measurements?.length) return
    const latest = measurements[0]
    setForm(prev => ({
      ...prev,
      waist: latest.waist_cm?.toString() ?? prev.waist,
      hip: latest.hip_cm?.toString() ?? prev.hip,
      chest: latest.chest_cm?.toString() ?? prev.chest,
      arm: latest.arm_cm?.toString() ?? prev.arm,
      leg: latest.leg_cm?.toString() ?? prev.leg,
    }))
  }, [measurements])

  const updateMutation = useMutation({
    mutationFn: (data: any) => profileApi.update(data).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: () => {
      setSaveMsg({ type: 'error', text: 'Profil güncellenemedi.' })
      setTimeout(() => setSaveMsg(null), 4000)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => profileApi.delete(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      setShowDeleteConfirm(false)
    },
  })

  const handleSave = async () => {
    // 1. Profil güncelle (kilo, boy, yaş, cinsiyet, aktivite, hedef)
    const profileData: import('@/lib/api').UserProfileUpdate = {
      weight_kg: parseFloat(form.weight),
      height_cm: parseFloat(form.height),
      age: parseInt(form.age),
      gender: form.gender,
      activity_level: form.activityLevel,
      goal: form.goal,
      weekly_workout_goal: parseInt(form.weeklyWorkoutGoal) || 4,
      fitness_level: form.fitnessLevel,
      daily_calorie_target: form.useManualCalorie && form.manualCalorieTarget
        ? parseFloat(form.manualCalorieTarget)
        : undefined,
    }

    // 2. Vücut ölçümleri varsa ölçüm tablosuna kaydet
    const measurementData: import('@/lib/api').MeasurementCreate = { user_id: userId }
    if (form.weight) measurementData.weight_kg = parseFloat(form.weight)
    if (form.height) measurementData.height_cm = parseFloat(form.height)
    if (form.waist) measurementData.waist_cm = parseFloat(form.waist)
    if (form.hip) measurementData.hip_cm = parseFloat(form.hip)
    if (form.chest) measurementData.chest_cm = parseFloat(form.chest)
    if (form.arm) measurementData.arm_cm = parseFloat(form.arm)
    if (form.leg) measurementData.leg_cm = parseFloat(form.leg)

    try {
      // Profil güncelle
      await profileApi.update(profileData)

      // Ölçüm kaydet (kilo/boy her zaman, diğerleri varsa)
      await measurementsApi.add(measurementData)

      queryClient.invalidateQueries({ queryKey: ['profile'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['measurements'] })
      queryClient.invalidateQueries({ queryKey: ['measurementDelta'] })

      setSaveMsg({ type: 'success', text: 'Profil ve ölçümler güncellendi.' })
      setTimeout(() => setSaveMsg(null), 3000)
    } catch {
      setSaveMsg({ type: 'error', text: 'Güncelleme başarısız.' })
      setTimeout(() => setSaveMsg(null), 4000)
    }
  }

  const bmr = profile
    ? form.gender === 'male'
      ? 10 * parseFloat(form.weight || '0') + 6.25 * parseFloat(form.height || '0') - 5 * parseInt(form.age || '0') + 5
      : 10 * parseFloat(form.weight || '0') + 6.25 * parseFloat(form.height || '0') - 5 * parseInt(form.age || '0') - 161
    : null

  const activityMultiplier = ({ sedentary: 1.2, light: 1.375, moderate: 1.55, active: 1.725, very_active: 1.9 } as Record<string, number>)[form.activityLevel] ?? 1.55
  const goalAdjustment = ({ lose: -500, maintain: 0, gain: 300, recomp: -250 } as Record<string, number>)[form.goal] ?? 0
  const calculatedTarget = bmr ? Math.round(bmr * activityMultiplier + goalAdjustment) : 0
  const effectiveTarget = form.useManualCalorie && form.manualCalorieTarget
    ? parseFloat(form.manualCalorieTarget)
    : calculatedTarget

  const weightChartData = measurements?.filter(m => m.weight_kg).map(m => ({
    date: format(new Date(m.measured_at), 'dd MMM', { locale: tr }),
    kilo: m.weight_kg,
  })) || []

  const deltaFields = [
    { key: 'weight_kg', label: 'Kilo', unit: 'kg' },
    { key: 'waist_cm', label: 'Bel', unit: 'cm' },
    { key: 'hip_cm', label: 'Kalça', unit: 'cm' },
    { key: 'chest_cm', label: 'Göğüs', unit: 'cm' },
    { key: 'arm_cm', label: 'Kol', unit: 'cm' },
    { key: 'leg_cm', label: 'Bacak', unit: 'cm' },
  ]

  return (
    <div className="p-5 space-y-4 max-w-3xl mx-auto">
      <div>
        <h1 className="text-lg font-semibold text-white">Profil</h1>
        <p className="text-[12px] text-white/35 mt-0.5">Kişisel bilgiler, hedefler ve vücut ölçümleri</p>
      </div>

      {/* BMR / TDEE kartları */}
      {bmr && bmr > 0 && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'BMR', value: Math.round(bmr), unit: 'kcal/gün', desc: 'Bazal metabolizma' },
            { label: 'TDEE', value: Math.round(bmr * activityMultiplier), unit: 'kcal/gün', desc: 'Günlük harcama' },
            { label: form.useManualCalorie ? 'Manuel Hedef' : 'Hesaplanan Hedef', value: Math.round(effectiveTarget), unit: 'kcal/gün', desc: form.useManualCalorie ? 'Manuel girilen' : 'Önerilen kalori', highlight: form.useManualCalorie },
          ].map(item => (
            <div key={item.label} className={`rounded-xl border p-4 ${(item as any).highlight ? 'border-violet-500/30 bg-violet-500/10' : 'border-white/[0.07] bg-[#13131a]'}`}>
              <p className="text-[10px] text-white/35 uppercase tracking-widest">{item.label}</p>
              <p className={`text-xl font-semibold mt-1 ${(item as any).highlight ? 'text-violet-300' : 'text-white'}`}>{item.value}</p>
              <p className="text-[10px] text-white/25 mt-0.5">{item.desc}</p>
            </div>
          ))}
        </div>
      )}

      {/* ── Kişisel Bilgiler Formu ── */}
      <GlassCard className="p-5">
        <h2 className="text-[13px] font-semibold text-white mb-4">Kişisel Bilgiler</h2>

        {/* Temel bilgiler */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
          {BASIC_FIELDS.map(f => (
            <div key={f.key}>
              <label className="text-[11px] text-white/40 mb-1.5 block uppercase tracking-wide">{f.label}</label>
              <Input
                type={f.type}
                placeholder={f.placeholder}
                step={f.step}
                value={(form as any)[f.key]}
                onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
              />
            </div>
          ))}
          <div>
            <label className="text-[11px] text-white/40 mb-1.5 block uppercase tracking-wide">Cinsiyet</label>
            <select
              value={form.gender}
              onChange={e => setForm(p => ({ ...p, gender: e.target.value }))}
              className="w-full rounded-lg px-3 py-2 text-[13px] text-white/80 bg-white/[0.05] border border-white/[0.08] focus:outline-none focus:ring-1 focus:ring-violet-500/60"
            >
              <option value="male">Erkek</option>
              <option value="female">Kadın</option>
            </select>
          </div>
        </div>

        {/* Vücut ölçümleri */}
        <div className="mb-4">
          <label className="text-[11px] text-white/40 mb-2 block uppercase tracking-wide">
            Vücut Ölçümleri
            <span className="ml-2 text-white/20 normal-case tracking-normal">(opsiyonel)</span>
          </label>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {BODY_FIELDS.map(f => (
              <div key={f.key}>
                <label className="text-[11px] text-white/30 mb-1.5 block">{f.label}</label>
                <Input
                  type="number"
                  placeholder={f.placeholder}
                  step="0.1"
                  min={f.min}
                  max={f.max}
                  value={(form as any)[f.key]}
                  onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                />
              </div>
            ))}
          </div>
          <p className="text-[10px] text-white/20 mt-2">Kaydettiğinizde bu değerler ölçüm geçmişine de eklenir.</p>
        </div>

        {/* Aktivite */}
        <div className="mb-4">
          <label className="text-[11px] text-white/40 mb-2 block uppercase tracking-wide">Aktivite Seviyesi</label>
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-1.5">
            {ACTIVITY_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => setForm(p => ({ ...p, activityLevel: opt.value }))}
                className={`px-3 py-2.5 rounded-lg text-left transition-all ${form.activityLevel === opt.value ? 'bg-violet-600/20 border border-violet-500/30 text-violet-300' : 'bg-white/[0.03] border border-white/[0.06] text-white/45 hover:text-white/70 hover:bg-white/[0.06]'}`}
              >
                <p className="text-[12px] font-medium">{opt.label}</p>
                <p className="text-[10px] opacity-60 mt-0.5 hidden sm:block">{opt.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Hedef */}
        <div className="mb-5">
          <label className="text-[11px] text-white/40 mb-2 block uppercase tracking-wide">Hedef</label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-1.5">
            {GOAL_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => setForm(p => ({ ...p, goal: opt.value }))}
                className={`px-3 py-2.5 rounded-lg text-left transition-all ${form.goal === opt.value ? 'bg-violet-600/20 border border-violet-500/30' : 'bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.06]'}`}
              >
                <p className={`text-[12px] font-medium ${form.goal === opt.value ? opt.color : 'text-white/60'}`}>{opt.label}</p>
                <p className="text-[10px] text-white/30 mt-0.5">{opt.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Fitness Seviyesi */}
        <div className="mb-5">
          <label className="text-[11px] text-white/40 mb-2 block uppercase tracking-wide">Fitness Seviyesi</label>
          <div className="grid grid-cols-3 gap-1.5">
            {[
              { value: 'beginner', label: '🌱 Yeni Başlayan', desc: '0-6 ay deneyim', color: 'text-emerald-400' },
              { value: 'intermediate', label: '💪 Orta Seviye', desc: '6 ay - 2 yıl', color: 'text-yellow-400' },
              { value: 'advanced', label: '🔥 İleri Seviye', desc: '2+ yıl deneyim', color: 'text-red-400' },
            ].map(opt => (
              <button
                key={opt.value}
                onClick={() => setForm(p => ({ ...p, fitnessLevel: opt.value }))}
                className={`px-3 py-2.5 rounded-lg text-left transition-all ${form.fitnessLevel === opt.value ? 'bg-violet-600/20 border border-violet-500/30' : 'bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.06]'}`}
              >
                <p className={`text-[12px] font-medium ${form.fitnessLevel === opt.value ? opt.color : 'text-white/60'}`}>{opt.label}</p>
                <p className="text-[10px] text-white/30 mt-0.5">{opt.desc}</p>
              </button>
            ))}
          </div>
          {form.fitnessLevel === 'beginner' && (
            <p className="text-[11px] text-emerald-400/70 mt-2">
              🌱 AI Koç sana hafif ağırlıklı, temel hareketlerden oluşan programlar önerecek.
            </p>
          )}
        </div>

        {/* Manuel Kalori Hedefi */}
        <div className="mb-5 p-4 rounded-xl border border-white/[0.06] bg-white/[0.02]">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-[12px] font-medium text-white">Manuel Kalori Hedefi</p>
              <p className="text-[11px] text-white/35 mt-0.5">
                {form.useManualCalorie
                  ? 'Kendi belirlediğin hedef kullanılıyor'
                  : `Sistem hesabı kullanılıyor: ${calculatedTarget} kcal/gün`}
              </p>
            </div>
            <button
              onClick={() => setForm(p => ({ ...p, useManualCalorie: !p.useManualCalorie }))}
              className={`relative flex-shrink-0 w-11 h-6 rounded-full transition-colors duration-200 ${form.useManualCalorie ? 'bg-violet-500' : 'bg-white/20'}`}
            >
              <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200 ${form.useManualCalorie ? 'translate-x-5' : 'translate-x-0'}`} />
            </button>
          </div>
          {form.useManualCalorie && (
            <div className="flex items-center gap-3">
              <Input
                type="number"
                placeholder={`Önerilen: ${calculatedTarget}`}
                value={form.manualCalorieTarget}
                onChange={e => setForm(p => ({ ...p, manualCalorieTarget: e.target.value }))}
                min={500}
                max={10000}
                step={50}
                className="flex-1"
              />
              <span className="text-[12px] text-white/40 shrink-0">kcal/gün</span>
            </div>
          )}
        </div>

        {saveMsg && (
          <div className={`mb-3 px-3 py-2.5 rounded-lg text-[12px] font-medium ${saveMsg.type === 'success' ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
            {saveMsg.text}
          </div>
        )}

        <div className="flex gap-2">
          <Button onClick={handleSave} disabled={updateMutation.isPending} className="flex-1">
            <Save className="w-4 h-4" />
            Kaydet
          </Button>
          <Button variant="outline" onClick={() => setShowDeleteConfirm(true)} className="text-red-400 border-red-500/20 hover:bg-red-500/10">
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </GlassCard>

      {/* Spor Profili */}
      <SportProfileManager userId={userId} />

      {/* Bildirimler */}
      <NotificationManager userId={userId} />

      {/* ── Ölçüm Geçmişi ── */}
      {/* Delta kartları */}
      {delta && (() => {
        const hasAnyDelta = deltaFields.some(f => (delta as any)[f.key] !== undefined && (delta as any)[f.key] !== null)
        if (!hasAnyDelta) return null
        return (
          <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
            {deltaFields.map(f => {
              const val = (delta as any)[f.key]
              if (val === undefined || val === null) return null
              const positive = val > 0
              return (
                <div key={f.key} className="rounded-xl border border-white/[0.07] bg-[#13131a] p-3 text-center">
                  <p className="text-[10px] text-white/35 uppercase tracking-widest">{f.label}</p>
                  <div className="mt-1.5 flex justify-center">
                    {val === 0
                      ? <span className="text-[11px] text-white/30 flex items-center gap-0.5"><Minus className="w-3 h-3" />0{f.unit}</span>
                      : <span className={`text-[11px] flex items-center gap-0.5 font-medium ${positive ? 'text-emerald-400' : 'text-red-400'}`}>
                          {positive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          {positive ? '+' : ''}{val.toFixed(1)}{f.unit}
                        </span>
                    }
                  </div>
                </div>
              )
            })}
          </div>
        )
      })()}

      {/* Kilo grafiği */}
      {weightChartData.length > 1 && (
        <GlassCard className="p-5">
          <h2 className="text-[13px] font-semibold text-white mb-4">Kilo Trendi</h2>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={weightChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 11 }} tickLine={false} />
              <YAxis stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 11 }} tickLine={false} width={32} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ backgroundColor: '#13131a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', fontSize: '12px' }}
                labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
                formatter={(v: any) => [`${v} kg`, 'Kilo']}
              />
              <Line type="monotone" dataKey="kilo" stroke="#7c3aed" strokeWidth={2} dot={{ r: 3, fill: '#7c3aed', strokeWidth: 0 }} activeDot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </GlassCard>
      )}

      {/* Geçmiş ölçümler */}
      <GlassCard className="p-5">
        <h2 className="text-[13px] font-semibold text-white mb-4">Ölçüm Geçmişi</h2>
        {!measurements?.length ? (
          <div className="text-center py-8">
            <Scale className="w-8 h-8 text-white/15 mx-auto mb-2" />
            <p className="text-[13px] text-white/30">Henüz ölçüm yok</p>
            <p className="text-[11px] text-white/20 mt-1">Profili kaydettiğinizde ölçümler buraya eklenir</p>
          </div>
        ) : (
          <div className="space-y-2">
            {measurements.map(m => (
              <div key={m.id} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 group">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[11px] text-white/35">{format(new Date(m.measured_at), 'dd MMMM yyyy, HH:mm', { locale: tr })}</p>
                  <button
                    onClick={() => { if (confirm('Silinsin mi?')) deleteMeasurementMutation.mutate(m.id) }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded text-white/25 hover:text-red-400 hover:bg-red-500/10 transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1">
                  {[
                    { label: 'Kilo', value: m.weight_kg, unit: 'kg' },
                    { label: 'Boy', value: m.height_cm, unit: 'cm' },
                    { label: 'Bel', value: m.waist_cm, unit: 'cm' },
                    { label: 'Kalça', value: m.hip_cm, unit: 'cm' },
                    { label: 'Göğüs', value: m.chest_cm, unit: 'cm' },
                    { label: 'Kol', value: m.arm_cm, unit: 'cm' },
                    { label: 'Bacak', value: m.leg_cm, unit: 'cm' },
                  ].filter(f => f.value).map(f => (
                    <div key={f.label}>
                      <span className="text-[10px] text-white/25">{f.label}: </span>
                      <span className="text-[12px] text-white/70 font-medium">{f.value}{f.unit}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Silme onayı */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="rounded-xl border border-white/[0.08] bg-[#13131a] p-6 max-w-sm w-full">
            <h3 className="text-[15px] font-semibold text-white mb-2">Profili Sil</h3>
            <p className="text-[13px] text-white/45 mb-5">Bu işlem geri alınamaz.</p>
            <div className="flex gap-2">
              <Button onClick={() => deleteMutation.mutate()} className="flex-1 bg-red-600 hover:bg-red-500" disabled={deleteMutation.isPending}>
                {deleteMutation.isPending ? 'Siliniyor...' : 'Sil'}
              </Button>
              <Button variant="outline" onClick={() => setShowDeleteConfirm(false)} className="flex-1">İptal</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
