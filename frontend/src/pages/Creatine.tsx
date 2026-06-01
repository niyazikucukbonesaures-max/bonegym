import { useState } from 'react'
import { Droplets, TrendingUp, Trash2 } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { StatCard } from '@/components/ui/StatCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useCreatineStatus, useLogCreatineDose, useCreatineHistory, useDeleteCreatineDose } from '@/hooks/useCreatine'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'
import { tr } from 'date-fns/locale'
import { useCurrentUserId } from '@/hooks/useCurrentUserId'

export default function Creatine() {
  const userId = useCurrentUserId()
  const [dose, setDose] = useState('')
  const [phase, setPhase] = useState('yükleme')

  const { data: status } = useCreatineStatus()
  const { data: history } = useCreatineHistory(30)
  const logDoseMutation = useLogCreatineDose()
  const deleteDoseMutation = useDeleteCreatineDose()

  const handleLogDose = () => {
    if (!dose) return
    logDoseMutation.mutate({
      user_id: userId,
      dose_grams: parseFloat(dose),
      phase,
    }, {
      onSuccess: () => {
        setDose('')
      }
    })
  }

  const handleDeleteDose = (id: number, doseGrams: number) => {
    if (confirm(`${doseGrams}g kreatin dozunu silmek istediğinizden emin misiniz?`)) {
      deleteDoseMutation.mutate(id)
    }
  }

  const chartData = history?.map(d => ({
    date: format(new Date(d.taken_at), 'dd MMM', { locale: tr }),
    gram: d.dose_grams,
  })) || []

  const phaseBadgeColor = phase === 'yükleme' ? 'bg-amber-500' : 'bg-emerald-500'

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-white">Kreatin Takibi</h1>

      {/* Durum Kartları */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Bugün Alındı mı?"
          value={status?.taken ? 1 : 0}
          unit={status?.taken ? '✓ Evet' : '✗ Hayır'}
          icon={<Droplets className="text-white" size={22} />}
          gradient="bg-gradient-to-br from-blue-500 to-cyan-600"
        />
        <StatCard
          title="Fazdaki Gün"
          value={status?.days_in_phase || 0}
          unit="gün"
          icon={<TrendingUp className="text-white" size={22} />}
          gradient="bg-gradient-to-br from-violet-500 to-purple-600"
        />
        <StatCard
          title="Toplam Alınan"
          value={status?.total_grams || 0}
          unit="gram"
          icon={<Droplets className="text-white" size={22} />}
          gradient="bg-gradient-to-br from-emerald-500 to-teal-600"
        />
      </div>

      {/* Doz Kaydetme */}
      <GlassCard className="p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Doz Kaydet</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm text-white/60 mb-1 block">Gram</label>
            <Input
              type="number"
              placeholder="5"
              value={dose}
              onChange={(e) => setDose(e.target.value)}
            />
          </div>
          <div>
            <label className="text-sm text-white/60 mb-1 block">Faz</label>
            <select
              value={phase}
              onChange={(e) => setPhase(e.target.value)}
              className="w-full rounded-lg px-3 py-2 text-[13px] text-white/80 bg-white/[0.05] border border-white/[0.08] focus:outline-none focus:ring-1 focus:ring-violet-500/60"
            >
              <option value="yükleme">Yükleme</option>
              <option value="koruma">Koruma</option>
            </select>
          </div>
          <div className="flex items-end">
            <Button onClick={handleLogDose} disabled={!dose} className="w-full">
              Kaydet
            </Button>
          </div>
        </div>
        {status?.phase && (
          <div className="mt-4 flex items-center gap-2">
            <span className={`px-3 py-1 rounded-full text-xs font-semibold text-white ${phaseBadgeColor}`}>
              {status.phase.toUpperCase()} FAZI
            </span>
            <span className="text-sm text-white/60">
              {status.days_in_phase} gündür bu fazdasınız
            </span>
          </div>
        )}
      </GlassCard>

      {/* 30 Günlük Grafik */}
      <GlassCard className="p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Son 30 Gün</h2>
        {chartData.length === 0 ? (
          <p className="text-white/60">Henüz veri yok</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="date" stroke="rgba(255,255,255,0.6)" />
              <YAxis stroke="rgba(255,255,255,0.6)" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(0,0,0,0.8)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="gram" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </GlassCard>

      {/* Doz Geçmişi */}
      <GlassCard className="p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Doz Geçmişi</h2>
        {history?.length === 0 ? (
          <p className="text-white/60">Henüz doz kaydı yok</p>
        ) : (
          <div className="space-y-3">
            {history?.map((dose) => (
              <div
                key={dose.id}
                className="flex items-center justify-between p-4 bg-white/5 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-600/20">
                    <Droplets className="text-blue-400" size={18} />
                  </div>
                  <div>
                    <p className="text-white font-medium">{dose.dose_grams}g</p>
                    <p className="text-sm text-white/60">
                      {format(new Date(dose.taken_at), 'dd MMM yyyy HH:mm', { locale: tr })} • {dose.phase} fazı
                    </p>
                  </div>
                </div>
                <Button
                  onClick={() => handleDeleteDose(dose.id, dose.dose_grams)}
                  variant="outline"
                  size="sm"
                  className="text-red-400 hover:text-red-300 hover:bg-red-500/10 border-red-500/20"
                >
                  <Trash2 size={14} />
                </Button>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  )
}
