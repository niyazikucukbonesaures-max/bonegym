// Gelişmiş Dashboard Bileşeni
// Trend grafikleri, ilerleme metrikleri, akıllı öneriler

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp, TrendingDown, Minus, Target, Award,
  AlertCircle, CheckCircle, BarChart2, Zap, Calendar
} from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Area, AreaChart
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

// ---------------------------------------------------------------------------
// Tip Tanımları
// ---------------------------------------------------------------------------

interface WeeklyReport {
  weight_analysis: {
    total_change_kg: number | null
    average_weekly_change: number
    trend_direction: string
    confidence_score: number
    data_points: number
  }
  body_metrics: {
    bmi: number | null
    body_fat_estimate: number | null
    health_indicators: Record<string, string>
  }
  plateau_status: {
    status: string
    duration_days: number
    recommendations: string[]
  }
  insights: string[]
}

interface VisualizationData {
  dates: string[]
  values: number[]
  trend_line: number[]
  statistics: {
    average: number
    min: number
    max: number
    total_change: number
    change_percentage: number
  }
  trend_direction: string
}

interface ProgressInsight {
  type: string
  title: string
  description: string
  priority: number
  actionable: boolean
}

// ---------------------------------------------------------------------------
// Yardımcı Bileşenler
// ---------------------------------------------------------------------------

function TrendBadge({ direction, value }: { direction: string; value: number }) {
  if (direction === 'decreasing') {
    return (
      <span className="flex items-center gap-1 text-emerald-400 text-xs font-medium">
        <TrendingDown size={12} />
        {Math.abs(value).toFixed(2)} kg/hafta
      </span>
    )
  }
  if (direction === 'increasing') {
    return (
      <span className="flex items-center gap-1 text-amber-400 text-xs font-medium">
        <TrendingUp size={12} />
        +{Math.abs(value).toFixed(2)} kg/hafta
      </span>
    )
  }
  return (
    <span className="flex items-center gap-1 text-white/50 text-xs font-medium">
      <Minus size={12} />
      Stabil
    </span>
  )
}

function InsightCard({ insight }: { insight: ProgressInsight }) {
  const iconMap: Record<string, React.ReactNode> = {
    trend: <TrendingUp size={16} className="text-emerald-400" />,
    plateau: <AlertCircle size={16} className="text-amber-400" />,
    consistency: <CheckCircle size={16} className="text-blue-400" />,
    composition: <Award size={16} className="text-violet-400" />,
  }

  const bgMap: Record<string, string> = {
    trend: 'bg-emerald-500/10 border-emerald-500/20',
    plateau: 'bg-amber-500/10 border-amber-500/20',
    consistency: 'bg-blue-500/10 border-blue-500/20',
    composition: 'bg-violet-500/10 border-violet-500/20',
  }

  return (
    <div className={`p-3 rounded-xl border ${bgMap[insight.type] || 'bg-white/5 border-white/10'}`}>
      <div className="flex items-start gap-2">
        <div className="mt-0.5">{iconMap[insight.type] || <Zap size={16} className="text-white/50" />}</div>
        <div>
          <p className="text-sm font-medium text-white">{insight.title}</p>
          <p className="text-xs text-white/60 mt-0.5">{insight.description}</p>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Ana Bileşen
// ---------------------------------------------------------------------------

interface EnhancedDashboardProps {
  userId?: number
}

const api = axios.create({ baseURL: 'http://localhost:8000' })

export function EnhancedDashboard({ userId = 1 }: EnhancedDashboardProps) {
  const [activeTab, setActiveTab] = useState<'weight' | 'body'>('weight')

  // Haftalık rapor
  const { data: weeklyReport, isLoading: reportLoading } = useQuery<WeeklyReport>({
    queryKey: ['weeklyReport', userId],
    queryFn: async () => {
      const res = await api.get('/api/analytics/reports/weekly', { params: { user_id: userId } })
      return res.data
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  // Kilo görselleştirme verisi
  const { data: weightViz } = useQuery<VisualizationData>({
    queryKey: ['weightVisualization', userId],
    queryFn: async () => {
      const res = await api.get('/api/measurements/visualization/weight_kg', {
        params: { user_id: userId, days: 30 }
      })
      return res.data
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  // İlerleme insights
  const { data: insightsData } = useQuery<{ insights_by_category: Record<string, ProgressInsight[]>; priority_insights: ProgressInsight[] }>({
    queryKey: ['progressInsights', userId],
    queryFn: async () => {
      const res = await api.get('/api/analytics/insights', { params: { user_id: userId } })
      return res.data
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  // Grafik verisi hazırla
  const chartData = weightViz?.dates.map((date, i) => ({
    date: date.slice(5), // MM-DD formatı
    kilo: weightViz.values[i],
    trend: weightViz.trend_line[i] ? Math.round(weightViz.trend_line[i] * 10) / 10 : null,
  })) || []

  const allInsights = insightsData?.priority_insights || []

  if (reportLoading) {
    return (
      <GlassCard className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <BarChart2 size={20} className="text-violet-400" />
          <h2 className="text-lg font-semibold text-white">İlerleme Analizi</h2>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-white/5 rounded-xl animate-pulse" />
          ))}
        </div>
      </GlassCard>
    )
  }

  return (
    <div className="space-y-4">
      {/* Özet Metrikler */}
      {weeklyReport && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {/* Haftalık Değişim */}
          <GlassCard className="p-4" noblur>
            <p className="text-xs text-white/50 mb-1">Haftalık Değişim</p>
            <TrendBadge
              direction={weeklyReport.weight_analysis.trend_direction}
              value={weeklyReport.weight_analysis.average_weekly_change}
            />
            <p className="text-xs text-white/30 mt-1">
              {weeklyReport.weight_analysis.data_points} ölçüm
            </p>
          </GlassCard>

          {/* BMI */}
          <GlassCard className="p-4" noblur>
            <p className="text-xs text-white/50 mb-1">BMI</p>
            <p className="text-xl font-bold text-white">
              {weeklyReport.body_metrics.bmi?.toFixed(1) || '—'}
            </p>
            <p className="text-xs text-white/40">
              {weeklyReport.body_metrics.health_indicators?.bmi || 'Veri yok'}
            </p>
          </GlassCard>

          {/* Plateau Durumu */}
          <GlassCard className="p-4" noblur>
            <p className="text-xs text-white/50 mb-1">Plateau</p>
            <p className={`text-sm font-semibold ${
              weeklyReport.plateau_status.status === 'confirmed_plateau' ? 'text-amber-400' :
              weeklyReport.plateau_status.status === 'potential_plateau' ? 'text-yellow-400' :
              'text-emerald-400'
            }`}>
              {weeklyReport.plateau_status.status === 'confirmed_plateau' ? '⚠️ Tespit Edildi' :
               weeklyReport.plateau_status.status === 'potential_plateau' ? '⚡ Olası' :
               '✅ Yok'}
            </p>
            {weeklyReport.plateau_status.duration_days > 0 && (
              <p className="text-xs text-white/30">{weeklyReport.plateau_status.duration_days} gün</p>
            )}
          </GlassCard>

          {/* Güven Skoru */}
          <GlassCard className="p-4" noblur>
            <p className="text-xs text-white/50 mb-1">Analiz Güveni</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-violet-500 to-purple-400 rounded-full"
                  style={{ width: `${(weeklyReport.weight_analysis.confidence_score * 100).toFixed(0)}%` }}
                />
              </div>
              <span className="text-xs text-white/60">
                {(weeklyReport.weight_analysis.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
            <p className="text-xs text-white/30 mt-1">Veri kalitesi</p>
          </GlassCard>
        </div>
      )}

      {/* Trend Grafiği */}
      {chartData.length > 0 && (
        <GlassCard className="p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BarChart2 size={18} className="text-violet-400" />
              <h3 className="text-base font-semibold text-white">30 Günlük Kilo Trendi</h3>
            </div>
            {weightViz && (
              <div className="flex items-center gap-3 text-xs text-white/50">
                <span>Min: <span className="text-white">{weightViz.statistics.min.toFixed(1)}</span></span>
                <span>Max: <span className="text-white">{weightViz.statistics.max.toFixed(1)}</span></span>
                <span>Ort: <span className="text-white">{weightViz.statistics.average.toFixed(1)}</span></span>
              </div>
            )}
          </div>

          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
              <defs>
                <linearGradient id="weightGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis
                dataKey="date"
                stroke="rgba(255,255,255,0.3)"
                tick={{ fontSize: 10 }}
                tickLine={false}
              />
              <YAxis
                stroke="rgba(255,255,255,0.3)"
                tick={{ fontSize: 10 }}
                tickLine={false}
                domain={['auto', 'auto']}
                width={35}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15,15,30,0.95)',
                  border: '1px solid rgba(139,92,246,0.3)',
                  borderRadius: '10px',
                  fontSize: '12px',
                }}
                labelStyle={{ color: 'rgba(255,255,255,0.7)' }}
                formatter={(value: any, name: string) => [
                  `${value} kg`,
                  name === 'kilo' ? 'Kilo' : 'Trend'
                ]}
              />
              <Area
                type="monotone"
                dataKey="kilo"
                stroke="#8b5cf6"
                strokeWidth={2}
                fill="url(#weightGradient)"
                dot={{ r: 3, fill: '#8b5cf6', strokeWidth: 0 }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="trend"
                stroke="#f59e0b"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>

          <div className="flex items-center gap-4 mt-2 text-xs text-white/40">
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-violet-500 inline-block" />
              Gerçek kilo
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-amber-400 inline-block border-dashed" style={{ borderTop: '1px dashed' }} />
              Trend çizgisi
            </span>
          </div>
        </GlassCard>
      )}

      {/* İlerleme Insights */}
      {allInsights.length > 0 && (
        <GlassCard className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Zap size={18} className="text-amber-400" />
            <h3 className="text-base font-semibold text-white">Akıllı Öneriler</h3>
          </div>
          <div className="space-y-2">
            {allInsights.slice(0, 4).map((insight, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <InsightCard insight={insight} />
              </motion.div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Plateau Önerileri */}
      {weeklyReport?.plateau_status.status === 'confirmed_plateau' && (
        <GlassCard className="p-5 border border-amber-500/20 bg-amber-500/5">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle size={18} className="text-amber-400" />
            <h3 className="text-base font-semibold text-amber-300">Plateau Tespit Edildi</h3>
          </div>
          <p className="text-sm text-white/60 mb-3">
            {weeklyReport.plateau_status.duration_days} gündür kilo değişimi minimal. İşte öneriler:
          </p>
          <ul className="space-y-1.5">
            {weeklyReport.plateau_status.recommendations.map((rec, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-white/70">
                <span className="w-1.5 h-1.5 bg-amber-400 rounded-full shrink-0" />
                {rec}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      {/* Veri yetersizse bilgi */}
      {!weeklyReport && !reportLoading && (
        <GlassCard className="p-6 text-center">
          <Calendar size={32} className="text-white/20 mx-auto mb-3" />
          <p className="text-white/50 text-sm">Analiz için daha fazla ölçüm gerekli</p>
          <p className="text-white/30 text-xs mt-1">En az 3 kilo ölçümü ekleyin</p>
        </GlassCard>
      )}
    </div>
  )
}
