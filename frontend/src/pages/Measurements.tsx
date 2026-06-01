import { GlassCard } from '@/components/ui/GlassCard'
import { Trash2, TrendingUp, TrendingDown, Minus, Scale } from 'lucide-react'
import { useMeasurements, useDeleteMeasurement, useMeasurementDelta } from '@/hooks/useMeasurements'
import { format } from 'date-fns'
import { tr } from 'date-fns/locale'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { EnhancedMeasurementInput } from '@/components/EnhancedMeasurementInput'
import { EnhancedDashboard } from '@/components/EnhancedDashboard'

function DeltaBadge({ value, unit }: { value: number; unit: string }) {
  if (value === 0) return <span className="text-[11px] text-white/30 flex items-center gap-0.5"><Minus className="w-3 h-3" />0{unit}</span>
  const positive = value > 0
  return (
    <span className={`text-[11px] flex items-center gap-0.5 font-medium ${positive ? 'text-emerald-400' : 'text-red-400'}`}>
      {positive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
      {positive ? '+' : ''}{value.toFixed(1)}{unit}
    </span>
  )
}

export default function Measurements() {
  const { data: measurements } = useMeasurements()
  const { data: delta } = useMeasurementDelta()
  const deleteMutation = useDeleteMeasurement()

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
    <div className="p-5 space-y-4 max-w-5xl mx-auto">
      <div>
        <h1 className="text-lg font-semibold text-white">Ölçümler</h1>
        <p className="text-[12px] text-white/35 mt-0.5">Vücut ölçümlerini takip et</p>
      </div>

      {/* Delta kartları */}
      {delta && (
        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
          {deltaFields.map(f => {
            const val = (delta as any)[f.key]
            if (val === undefined || val === null) return null
            return (
              <div key={f.key} className="rounded-xl border border-white/[0.07] bg-[#13131a] p-3 text-center">
                <p className="text-[10px] text-white/35 uppercase tracking-widest">{f.label}</p>
                <div className="mt-1.5 flex justify-center">
                  <DeltaBadge value={val} unit={f.unit} />
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Ölçüm girişi */}
      <EnhancedMeasurementInput />

      {/* Kilo grafiği */}
      {weightChartData.length > 1 && (
        <GlassCard className="p-5">
          <h2 className="text-[13px] font-semibold text-white mb-4">Kilo Trendi</h2>
          <ResponsiveContainer width="100%" height={200}>
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

      {/* Analiz */}
      <EnhancedDashboard userId={1} />

      {/* Geçmiş */}
      <GlassCard className="p-5">
        <h2 className="text-[13px] font-semibold text-white mb-4">Geçmiş Ölçümler</h2>
        {!measurements?.length ? (
          <div className="text-center py-8">
            <Scale className="w-8 h-8 text-white/15 mx-auto mb-2" />
            <p className="text-[13px] text-white/30">Henüz ölçüm yok</p>
          </div>
        ) : (
          <div className="space-y-2">
            {measurements.map(m => (
              <div key={m.id} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 group">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[11px] text-white/35">{format(new Date(m.measured_at), 'dd MMMM yyyy, HH:mm', { locale: tr })}</p>
                  <button
                    onClick={() => { if (confirm('Silinsin mi?')) deleteMutation.mutate(m.id) }}
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
    </div>
  )
}
