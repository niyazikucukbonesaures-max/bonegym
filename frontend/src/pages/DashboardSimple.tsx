import { useDashboard } from '@/hooks/useDashboard'
import { GlassCard } from '@/components/ui/GlassCard'

export default function DashboardSimple() {
  const { data, isLoading, error } = useDashboard()

  if (isLoading) {
    return (
      <div className="p-6">
        <h1 className="text-3xl font-bold text-white">Yükleniyor...</h1>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-3xl font-bold text-red-400">Hata!</h1>
        <p className="text-white mt-4">{String(error)}</p>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-6">
        <h1 className="text-3xl font-bold text-white">Veri yok</h1>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-white">Dashboard</h1>
      
      <GlassCard className="p-6">
        <h2 className="text-xl font-semibold text-white mb-4">API Verisi</h2>
        <pre className="text-white text-xs overflow-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      </GlassCard>

      {data.weight_trend && data.weight_trend.length > 0 && (
        <GlassCard className="p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Son Kilo</h2>
          <p className="text-white text-2xl">
            {data.weight_trend[0].weight_kg} kg
          </p>
        </GlassCard>
      )}
    </div>
  )
}
