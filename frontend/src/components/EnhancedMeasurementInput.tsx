// Gelişmiş Ölçüm Girişi Bileşeni
// Çoklu ölçüm tipi, gerçek zamanlı doğrulama, otomatik tamamlama

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Scale, AlertTriangle, CheckCircle, Info, ChevronDown, ChevronUp } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAddMeasurement } from '@/hooks/useMeasurements'
import type { MeasurementCreate } from '@/lib/api'
import { useCurrentUserId } from '@/hooks/useCurrentUserId'

// ---------------------------------------------------------------------------
// Tip Tanımları
// ---------------------------------------------------------------------------

interface MeasurementField {
  key: keyof Omit<MeasurementCreate, 'user_id'>
  label: string
  placeholder: string
  unit: string
  min: number
  max: number
  icon: string
  color: string
}

interface ValidationState {
  isValid: boolean
  message: string
  type: 'success' | 'warning' | 'error' | 'info'
}

// ---------------------------------------------------------------------------
// Sabitler
// ---------------------------------------------------------------------------

const MEASUREMENT_FIELDS: MeasurementField[] = [
  { key: 'weight_kg', label: 'Kilo', placeholder: '75', unit: 'kg', min: 30, max: 300, icon: '⚖️', color: 'violet' },
  { key: 'height_cm', label: 'Boy', placeholder: '175', unit: 'cm', min: 100, max: 250, icon: '📏', color: 'blue' },
  { key: 'waist_cm', label: 'Bel', placeholder: '80', unit: 'cm', min: 40, max: 200, icon: '📐', color: 'emerald' },
  { key: 'hip_cm', label: 'Kalça', placeholder: '95', unit: 'cm', min: 50, max: 200, icon: '🔵', color: 'cyan' },
  { key: 'chest_cm', label: 'Göğüs', placeholder: '100', unit: 'cm', min: 60, max: 200, icon: '💪', color: 'amber' },
  { key: 'arm_cm', label: 'Kol', placeholder: '35', unit: 'cm', min: 15, max: 80, icon: '💪', color: 'pink' },
  { key: 'leg_cm', label: 'Bacak', placeholder: '55', unit: 'cm', min: 30, max: 120, icon: '🦵', color: 'indigo' },
]

const COLOR_MAP: Record<string, string> = {
  violet: 'border-violet-500/50 focus:ring-violet-500',
  blue: 'border-blue-500/50 focus:ring-blue-500',
  emerald: 'border-emerald-500/50 focus:ring-emerald-500',
  cyan: 'border-cyan-500/50 focus:ring-cyan-500',
  amber: 'border-amber-500/50 focus:ring-amber-500',
  pink: 'border-pink-500/50 focus:ring-pink-500',
  indigo: 'border-indigo-500/50 focus:ring-indigo-500',
}

// ---------------------------------------------------------------------------
// Yardımcı Fonksiyonlar
// ---------------------------------------------------------------------------

function validateField(field: MeasurementField, value: string): ValidationState {
  if (!value) return { isValid: true, message: '', type: 'info' }

  const num = parseFloat(value)
  if (isNaN(num)) return { isValid: false, message: 'Geçerli bir sayı girin', type: 'error' }
  if (num < field.min) return { isValid: false, message: `Minimum ${field.min} ${field.unit}`, type: 'error' }
  if (num > field.max) return { isValid: false, message: `Maksimum ${field.max} ${field.unit}`, type: 'error' }

  // Uyarı aralıkları
  if (field.key === 'weight_kg') {
    if (num < 40) return { isValid: true, message: 'Çok düşük kilo - doğru mu?', type: 'warning' }
    if (num > 200) return { isValid: true, message: 'Çok yüksek kilo - doğru mu?', type: 'warning' }
  }

  return { isValid: true, message: `✓ Geçerli değer`, type: 'success' }
}

// ---------------------------------------------------------------------------
// Ana Bileşen
// ---------------------------------------------------------------------------

interface EnhancedMeasurementInputProps {
  onSuccess?: () => void
  compact?: boolean
}

export function EnhancedMeasurementInput({ onSuccess, compact = false }: EnhancedMeasurementInputProps) {
  const userId = useCurrentUserId()
  const [values, setValues] = useState<Record<string, string>>({})
  const [validations, setValidations] = useState<Record<string, ValidationState>>({})
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [saveStatus, setSaveStatus] = useState<{ type: 'success' | 'error' | 'warning'; text: string } | null>(null)
  const [bmiPreview, setBmiPreview] = useState<{ bmi: number; category: string; color: string } | null>(null)

  const addMutation = useAddMeasurement()

  // BMI önizleme hesaplama
  useEffect(() => {
    const weight = parseFloat(values['weight_kg'] || '')
    const height = parseFloat(values['height_cm'] || '')

    if (weight > 0 && height > 0) {
      const heightM = height / 100
      const bmi = weight / (heightM * heightM)
      const rounded = Math.round(bmi * 10) / 10

      let category = ''
      let color = ''
      if (bmi < 18.5) { category = 'Zayıf'; color = 'text-blue-400' }
      else if (bmi < 25) { category = 'Normal'; color = 'text-emerald-400' }
      else if (bmi < 30) { category = 'Fazla Kilolu'; color = 'text-amber-400' }
      else { category = 'Obez'; color = 'text-red-400' }

      setBmiPreview({ bmi: rounded, category, color })
    } else {
      setBmiPreview(null)
    }
  }, [values['weight_kg'], values['height_cm']])

  const handleChange = useCallback((key: string, value: string, field: MeasurementField) => {
    setValues(prev => ({ ...prev, [key]: value }))
    const validation = validateField(field, value)
    setValidations(prev => ({ ...prev, [key]: validation }))
  }, [])

  const hasAnyValue = Object.values(values).some(v => v.trim() !== '')
  const hasErrors = Object.values(validations).some(v => !v.isValid)

  const handleSave = useCallback(() => {
    if (!hasAnyValue || hasErrors) return

    const data: MeasurementCreate = { user_id: userId }
    MEASUREMENT_FIELDS.forEach(field => {
      const val = values[field.key]
      if (val && val.trim()) {
        const num = parseFloat(val)
        if (!isNaN(num)) {
          (data as any)[field.key] = num
        }
      }
    })

    addMutation.mutate(data, {
      onSuccess: (result: any) => {
        const warnings = result?.data?.total_warnings ?? result?.total_warnings ?? 0
        if (warnings > 0) {
          setSaveStatus({ type: 'warning', text: '⚠️ Kaydedildi, ancak bazı değerler beklenmedik görünüyor.' })
        } else {
          setSaveStatus({ type: 'success', text: '✅ Ölçümler başarıyla kaydedildi!' })
        }
        setValues({})
        setValidations({})
        setBmiPreview(null)
        setTimeout(() => setSaveStatus(null), 3000)
        onSuccess?.()
      },
      onError: (error: any) => {
        const detail = error?.response?.data?.detail
        let msg = 'Kayıt sırasında hata oluştu.'
        if (typeof detail === 'object' && detail?.message) msg = detail.message
        else if (typeof detail === 'string') msg = detail
        setSaveStatus({ type: 'error', text: `❌ ${msg}` })
        setTimeout(() => setSaveStatus(null), 5000)
      }
    })
  }, [values, hasAnyValue, hasErrors, addMutation, onSuccess])

  // Compact mod: sadece kilo girişi
  const visibleFields = compact
    ? MEASUREMENT_FIELDS.slice(0, 1)
    : showAdvanced
    ? MEASUREMENT_FIELDS
    : MEASUREMENT_FIELDS.slice(0, 4)

  return (
    <GlassCard className="p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Scale className="text-violet-400" size={20} />
          <h2 className="text-lg font-semibold text-white">
            {compact ? 'Kilo Güncelle' : 'Ölçüm Ekle'}
          </h2>
        </div>
        {bmiPreview && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-2 px-3 py-1 bg-white/10 rounded-full"
          >
            <span className="text-xs text-white/60">BMI:</span>
            <span className={`text-sm font-bold ${bmiPreview.color}`}>{bmiPreview.bmi}</span>
            <span className={`text-xs ${bmiPreview.color}`}>{bmiPreview.category}</span>
          </motion.div>
        )}
      </div>

      <div className={`grid gap-3 ${compact ? 'grid-cols-1' : 'grid-cols-2 md:grid-cols-4'}`}>
        {visibleFields.map(field => {
          const validation = validations[field.key]
          const value = values[field.key] || ''
          const colorClass = COLOR_MAP[field.color] || ''

          return (
            <div key={field.key} className="space-y-1">
              <label className="text-xs text-white/60 flex items-center gap-1">
                <span>{field.icon}</span>
                <span>{field.label}</span>
                <span className="text-white/40">({field.unit})</span>
              </label>
              <div className="relative">
                <Input
                  type="number"
                  placeholder={field.placeholder}
                  value={value}
                  onChange={e => handleChange(field.key, e.target.value, field)}
                  className={`pr-8 ${value && validation ? (
                    validation.isValid ? 'border-emerald-500/50' : 'border-red-500/50'
                  ) : colorClass}`}
                  min={field.min}
                  max={field.max}
                  step="0.1"
                />
                {value && validation && (
                  <div className="absolute right-2 top-1/2 -translate-y-1/2">
                    {validation.isValid
                      ? <CheckCircle size={14} className="text-emerald-400" />
                      : <AlertTriangle size={14} className="text-red-400" />
                    }
                  </div>
                )}
              </div>
              <AnimatePresence>
                {value && validation && validation.message && (
                  <motion.p
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className={`text-xs ${
                      validation.type === 'error' ? 'text-red-400' :
                      validation.type === 'warning' ? 'text-amber-400' :
                      validation.type === 'success' ? 'text-emerald-400' :
                      'text-white/50'
                    }`}
                  >
                    {validation.message}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>
          )
        })}
      </div>

      {/* Gelişmiş alanlar toggle - sadece compact değilse */}
      {!compact && (
        <button
          onClick={() => setShowAdvanced(prev => !prev)}
          className="mt-3 flex items-center gap-1 text-xs text-white/50 hover:text-white/80 transition-colors"
        >
          {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          {showAdvanced ? 'Daha az göster' : 'Kol ve bacak ölçümleri'}
        </button>
      )}

      {/* Kaydet butonu */}
      <div className="mt-4 flex items-center gap-3">
        <Button
          onClick={handleSave}
          disabled={!hasAnyValue || hasErrors || addMutation.isPending}
          className="flex-1"
        >
          {addMutation.isPending ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Kaydediliyor...
            </span>
          ) : 'Kaydet'}
        </Button>

        {hasAnyValue && (
          <button
            onClick={() => { setValues({}); setValidations({}); setBmiPreview(null) }}
            className="text-xs text-white/40 hover:text-white/70 transition-colors"
          >
            Temizle
          </button>
        )}
      </div>

      {/* Durum mesajı */}
      <AnimatePresence>
        {saveStatus && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className={`mt-3 p-3 rounded-lg text-sm font-medium ${
              saveStatus.type === 'success' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
              saveStatus.type === 'warning' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
              'bg-red-500/20 text-red-300 border border-red-500/30'
            }`}
          >
            {saveStatus.text}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bilgi notu */}
      {!compact && (
        <div className="mt-3 flex items-start gap-2 p-2 bg-white/5 rounded-lg">
          <Info size={13} className="text-white/40 mt-0.5 shrink-0" />
          <p className="text-xs text-white/40">
            Tüm alanları doldurmak zorunda değilsiniz. Sadece ölçmek istediğiniz değerleri girin.
          </p>
        </div>
      )}
    </GlassCard>
  )
}
