// Bildirim Yönetimi Bileşeni
// Bildirim tercihleri, hatırlatma zamanı, kullanıcı kalıpları

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bell, BellOff, Clock, ChevronDown, Save, BarChart2, CheckCircle } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

// ---------------------------------------------------------------------------
// Tip Tanımları
// ---------------------------------------------------------------------------

interface NotificationPreferences {
  id?: number
  user_id: number
  weight_reminders: boolean
  measurement_reminders: boolean
  motivation_messages: boolean
  progress_reports: boolean
  max_daily_notifications: number
  preferred_reminder_time: string | null
  quiet_hours_start: string | null
  quiet_hours_end: string | null
}

interface UserPatterns {
  preferred_measurement_time: string | null
  most_active_hours: number[]
  measurement_frequency: number
  consistency_score: number
  activity_pattern: string
  last_measurement_date: string | null
  average_gap_days: number
  analysis: {
    consistency_level: string
    activity_description: string
  }
}

// ---------------------------------------------------------------------------
// Sabitler
// ---------------------------------------------------------------------------

const NOTIFICATION_TYPES = [
  {
    key: 'weight_reminders' as const,
    label: 'Kilo Hatırlatmaları',
    desc: '3 gün ölçüm yapılmadığında hatırlat',
    icon: '⚖️',
  },
  {
    key: 'measurement_reminders' as const,
    label: 'Ölçüm Hatırlatmaları',
    desc: 'Düzenli ölçüm için hatırlatma',
    icon: '📏',
  },
  {
    key: 'motivation_messages' as const,
    label: 'Motivasyon Mesajları',
    desc: 'İlerleme durumuna göre motivasyon',
    icon: '💪',
  },
  {
    key: 'progress_reports' as const,
    label: 'İlerleme Raporları',
    desc: 'Haftalık özet bildirimleri',
    icon: '📊',
  },
]

const ACTIVITY_PATTERN_LABELS: Record<string, string> = {
  morning_person: '🌅 Sabah Kişisi',
  evening_person: '🌙 Akşam Kişisi',
  irregular: '🔀 Düzensiz',
  consistent: '✅ Tutarlı',
}

const api = axios.create({ baseURL: 'http://localhost:8000' })

// ---------------------------------------------------------------------------
// Ana Bileşen
// ---------------------------------------------------------------------------

interface NotificationManagerProps {
  userId?: number
}

export function NotificationManager({ userId = 1 }: NotificationManagerProps) {
  const queryClient = useQueryClient()
  const [isExpanded, setIsExpanded] = useState(false)
  const [saveStatus, setSaveStatus] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const [prefs, setPrefs] = useState<NotificationPreferences>({
    user_id: userId,
    weight_reminders: true,
    measurement_reminders: true,
    motivation_messages: true,
    progress_reports: true,
    max_daily_notifications: 2,
    preferred_reminder_time: '08:00',
    quiet_hours_start: '22:00',
    quiet_hours_end: '07:00',
  })

  // Mevcut tercihleri yükle
  const { data: existingPrefs } = useQuery<NotificationPreferences | null>({
    queryKey: ['notificationPrefs', userId],
    queryFn: async () => {
      try {
        const res = await api.get('/api/notifications/preferences', { params: { user_id: userId } })
        return res.data
      } catch {
        return null
      }
    },
  })

  // Kullanıcı kalıplarını yükle
  const { data: patterns } = useQuery<UserPatterns>({
    queryKey: ['userPatterns', userId],
    queryFn: async () => {
      const res = await api.get('/api/notifications/patterns', { params: { user_id: userId } })
      return res.data
    },
    retry: false,
    staleTime: 10 * 60 * 1000,
  })

  // Mevcut tercihler yüklenince formu doldur
  useEffect(() => {
    if (existingPrefs) {
      setPrefs(existingPrefs)
    }
  }, [existingPrefs])

  const saveMutation = useMutation({
    mutationFn: async (data: NotificationPreferences) => {
      const res = await api.post('/api/notifications/preferences', data)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notificationPrefs'] })
      setSaveStatus({ type: 'success', text: '✅ Bildirim tercihleri kaydedildi!' })
      setTimeout(() => setSaveStatus(null), 3000)
    },
    onError: () => {
      setSaveStatus({ type: 'error', text: '❌ Kayıt sırasında hata oluştu.' })
      setTimeout(() => setSaveStatus(null), 4000)
    }
  })

  const togglePref = (key: keyof NotificationPreferences) => {
    setPrefs(prev => ({ ...prev, [key]: !prev[key as keyof typeof prev] }))
  }

  const activeCount = NOTIFICATION_TYPES.filter(t => prefs[t.key]).length

  return (
    <GlassCard className="overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(prev => !prev)}
        className="w-full p-5 flex items-center justify-between hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center">
            <Bell size={20} className="text-white" />
          </div>
          <div className="text-left">
            <h3 className="text-base font-semibold text-white">Bildirimler</h3>
            <p className="text-xs text-white/50">
              {activeCount} bildirim aktif • Günde maks. {prefs.max_daily_notifications}
            </p>
          </div>
        </div>
        <ChevronDown
          size={18}
          className={`text-white/40 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        />
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

              {/* Kullanıcı Kalıpları */}
              {patterns && (
                <div className="p-3 bg-white/5 rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <BarChart2 size={14} className="text-blue-400" />
                    <p className="text-xs font-medium text-white/70">Ölçüm Alışkanlıklarınız</p>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="text-center">
                      <p className="text-xs text-white/40">Kalıp</p>
                      <p className="text-xs font-medium text-white">
                        {ACTIVITY_PATTERN_LABELS[patterns.activity_pattern] || patterns.activity_pattern}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-white/40">Tutarlılık</p>
                      <p className={`text-xs font-medium ${
                        patterns.analysis.consistency_level === 'Yüksek' ? 'text-emerald-400' :
                        patterns.analysis.consistency_level === 'Orta' ? 'text-amber-400' :
                        'text-red-400'
                      }`}>
                        {patterns.analysis.consistency_level}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-white/40">Tercih Saati</p>
                      <p className="text-xs font-medium text-white">
                        {patterns.preferred_measurement_time || '—'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Bildirim Tipleri */}
              <div className="space-y-2">
                <p className="text-xs text-white/50 font-medium">Bildirim Türleri</p>
                {NOTIFICATION_TYPES.map(type => (
                  <div
                    key={type.key}
                    className="flex items-center justify-between p-3 bg-white/5 rounded-xl"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-base">{type.icon}</span>
                      <div>
                        <p className="text-sm text-white">{type.label}</p>
                        <p className="text-xs text-white/40">{type.desc}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => togglePref(type.key)}
                      className={`relative flex-shrink-0 w-11 h-6 rounded-full transition-colors duration-200 ${prefs[type.key] ? 'bg-blue-500' : 'bg-white/20'}`}
                    >
                      <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${prefs[type.key] ? 'translate-x-5' : 'translate-x-0'}`} />
                    </button>
                  </div>
                ))}
              </div>

              {/* Günlük Limit */}
              <div>
                <label className="text-xs text-white/50 mb-2 block">
                  Günlük Maksimum Bildirim: <span className="text-white font-medium">{prefs.max_daily_notifications}</span>
                </label>
                <input
                  type="range"
                  min={1}
                  max={5}
                  value={prefs.max_daily_notifications}
                  onChange={e => setPrefs(prev => ({ ...prev, max_daily_notifications: parseInt(e.target.value) }))}
                  className="w-full accent-blue-500"
                />
                <div className="flex justify-between text-xs text-white/30 mt-1">
                  <span>1</span>
                  <span>5</span>
                </div>
              </div>

              {/* Tercih Edilen Saat */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-white/50 mb-1 block flex items-center gap-1">
                    <Clock size={11} />
                    Hatırlatma Saati
                  </label>
                  <input
                    type="time"
                    value={prefs.preferred_reminder_time || '08:00'}
                    onChange={e => setPrefs(prev => ({ ...prev, preferred_reminder_time: e.target.value }))}
                    className="w-full rounded-lg px-3 py-2 text-sm text-white bg-white/10 border border-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-white/50 mb-1 block">Sessiz Saatler</label>
                  <div className="flex items-center gap-1">
                    <input
                      type="time"
                      value={prefs.quiet_hours_start || '22:00'}
                      onChange={e => setPrefs(prev => ({ ...prev, quiet_hours_start: e.target.value }))}
                      className="flex-1 rounded-lg px-2 py-2 text-xs text-white bg-white/10 border border-white/20 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                    <span className="text-white/30 text-xs">-</span>
                    <input
                      type="time"
                      value={prefs.quiet_hours_end || '07:00'}
                      onChange={e => setPrefs(prev => ({ ...prev, quiet_hours_end: e.target.value }))}
                      className="flex-1 rounded-lg px-2 py-2 text-xs text-white bg-white/10 border border-white/20 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Kaydet */}
              <Button
                onClick={() => saveMutation.mutate(prefs)}
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
                    Tercihleri Kaydet
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
