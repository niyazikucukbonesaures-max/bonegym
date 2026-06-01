import React, { useState, useEffect, useCallback } from 'react'
import { Droplets, Plus, Minus } from 'lucide-react'
import { waterApi, type DailyWaterSummary, type WaterLog } from '../lib/api'

interface WaterTrackerProps {
  waterSummary?: DailyWaterSummary
  onWaterAdded?: () => void
}

const WaterTracker: React.FC<WaterTrackerProps> = ({ waterSummary, onWaterAdded }) => {
  const [optimisticTotal, setOptimisticTotal] = useState<number | null>(null)
  // Kendi içinde güncel entries listesini tut
  const [localEntries, setLocalEntries] = useState<WaterLog[]>([])

  const serverTotal = waterSummary?.total_ml ?? 0
  const goal_ml = waterSummary?.goal_ml ?? 2500

  // Sunucudan yeni veri gelince sıfırla ve entries'i güncelle
  useEffect(() => {
    setOptimisticTotal(null)
    if (waterSummary?.entries) {
      setLocalEntries(waterSummary.entries)
    }
  }, [serverTotal, waterSummary?.entries])

  const total_ml = optimisticTotal ?? serverTotal
  const remaining = Math.max(0, goal_ml - total_ml)
  const pct = Math.min(100, goal_ml > 0 ? (total_ml / goal_ml) * 100 : 0)
  const circumference = 2 * Math.PI * 44

  const handleAdd = useCallback(async (amount: number) => {
    setOptimisticTotal(prev => (prev ?? serverTotal) + amount)
    try {
      const res = await waterApi.quickAdd(amount)
      // Yeni kaydı localEntries'e ekle
      setLocalEntries(prev => [...prev, res.data])
      onWaterAdded?.()
    } catch (err) {
      console.error('Su ekleme hatası:', err)
      setOptimisticTotal(prev => (prev !== null ? Math.max(0, prev - amount) : null))
    }
  }, [serverTotal, onWaterAdded])

  const handleRemove = useCallback(async (amount: number) => {
    const current = optimisticTotal ?? serverTotal
    if (current <= 0 || localEntries.length === 0) return

    // Optimistic: anında azalt
    setOptimisticTotal(Math.max(0, current - amount))

    // En son eklenen kayıtlardan başlayarak sil
    const sorted = [...localEntries].sort(
      (a, b) => new Date(b.logged_at).getTime() - new Date(a.logged_at).getTime()
    )

    let toDelete = amount
    const deletedIds: number[] = []

    for (const entry of sorted) {
      if (toDelete <= 0) break
      deletedIds.push(entry.id)
      toDelete -= entry.amount_ml
    }

    // Optimistic: silinen kayıtları localEntries'den kaldır
    setLocalEntries(prev => prev.filter(e => !deletedIds.includes(e.id)))

    try {
      await Promise.all(deletedIds.map(id => waterApi.deleteLog(id)))
      onWaterAdded?.()
    } catch (err) {
      console.error('Su silme hatası:', err)
      // Hata: geri al
      setOptimisticTotal(current)
      setLocalEntries(waterSummary?.entries ?? [])
    }
  }, [optimisticTotal, serverTotal, localEntries, onWaterAdded, waterSummary?.entries])

  return (
    <div className="rounded-xl border border-white/[0.07] bg-[#13131a] p-5">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-9 h-9 rounded-lg bg-blue-500/15 flex items-center justify-center">
          <Droplets className="w-4 h-4 text-blue-400" />
        </div>
        <div>
          <h3 className="text-[13px] font-semibold text-white">Su Takibi</h3>
          <p className="text-[11px] text-white/35">Günlük hedef: {Math.round(goal_ml)}ml</p>
        </div>
      </div>

      {/* Progress ring */}
      <div className="flex items-center justify-center mb-5">
        <div className="relative w-28 h-28">
          <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="44" stroke="rgba(59,130,246,0.08)" strokeWidth="7" fill="none" />
            <circle
              cx="50" cy="50" r="44"
              stroke="#3b82f6"
              strokeWidth="7"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={circumference * (1 - pct / 100)}
              style={{ transition: 'stroke-dashoffset 0.4s ease' }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-xl font-bold text-white">{Math.round(pct)}%</span>
            <span className="text-[10px] text-white/35">{Math.round(total_ml / 100) / 10}L</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="text-center p-2.5 rounded-lg bg-white/[0.03]">
          <p className="text-base font-semibold text-blue-400">{Math.round(total_ml)}</p>
          <p className="text-[10px] text-white/30">ml içildi</p>
        </div>
        <div className="text-center p-2.5 rounded-lg bg-white/[0.03]">
          <p className="text-base font-semibold text-white/60">{Math.round(remaining)}</p>
          <p className="text-[10px] text-white/30">ml kaldı</p>
        </div>
      </div>

      {/* Ekle butonları */}
      <p className="text-[10px] text-white/25 uppercase tracking-widest mb-1.5">Ekle</p>
      <div className="grid grid-cols-3 gap-1.5 mb-3">
        {[250, 500, 1000].map(amount => (
          <button
            key={amount}
            onClick={() => handleAdd(amount)}
            className="flex items-center justify-center gap-1 py-2 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 active:scale-95 border border-blue-500/15 text-blue-300 text-[12px] font-medium transition-all"
          >
            <Plus className="w-3 h-3" />
            {amount >= 1000 ? '1L' : `${amount}ml`}
          </button>
        ))}
      </div>

      {/* Azalt butonları */}
      <p className="text-[10px] text-white/25 uppercase tracking-widest mb-1.5">Azalt</p>
      <div className="grid grid-cols-3 gap-1.5">
        {[250, 500, 1000].map(amount => (
          <button
            key={amount}
            onClick={() => handleRemove(amount)}
            disabled={total_ml <= 0 || localEntries.length === 0}
            className="flex items-center justify-center gap-1 py-2 rounded-lg bg-white/[0.03] hover:bg-red-500/10 active:scale-95 border border-white/[0.06] hover:border-red-500/20 text-white/35 hover:text-red-400 text-[12px] font-medium transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <Minus className="w-3 h-3" />
            {amount >= 1000 ? '1L' : `${amount}ml`}
          </button>
        ))}
      </div>

      {pct >= 100 && (
        <div className="mt-3 px-3 py-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-center">
          <p className="text-[12px] text-blue-300 font-medium">🎉 Günlük hedef tamamlandı!</p>
        </div>
      )}
    </div>
  )
}

export default WaterTracker
