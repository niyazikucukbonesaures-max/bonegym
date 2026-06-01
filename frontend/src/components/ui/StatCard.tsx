import { useEffect } from 'react'
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatCardProps {
  title: string
  value: number
  unit?: string
  icon?: React.ReactNode
  gradient?: string
  trend?: number
  info?: string
}

function AnimatedNumber({ value }: { value: number }) {
  const motionValue = useMotionValue(0)
  const spring = useSpring(motionValue, { stiffness: 100, damping: 20 })
  const display = useTransform(spring, (v) => Math.round(v).toLocaleString())

  useEffect(() => {
    motionValue.set(value)
  }, [value, motionValue])

  return <motion.span>{display}</motion.span>
}

export function StatCard({ title, value, unit, icon, gradient, trend, info }: StatCardProps) {
  const hasTrend = trend !== undefined && trend !== null

  return (
    <div className="rounded-xl border border-white/[0.07] bg-[#13131a] p-4 hover:border-white/[0.12] transition-colors duration-200">
      <div className="flex items-start justify-between gap-3">
        {icon && (
          <div className={cn(
            'flex items-center justify-center w-9 h-9 rounded-lg shrink-0',
            gradient ?? 'bg-violet-600/20'
          )}>
            {icon}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-[11px] font-medium text-white/40 uppercase tracking-widest truncate">{title}</p>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-xl font-semibold text-white">
              <AnimatedNumber value={value} />
            </span>
            {unit && <span className="text-xs text-white/40 font-medium">{unit}</span>}
          </div>
          {info && <p className="text-[11px] text-white/30 mt-0.5">{info}</p>}
        </div>
        {hasTrend && (
          <div className={cn(
            'flex items-center gap-0.5 text-[11px] font-semibold shrink-0',
            trend >= 0 ? 'text-emerald-400' : 'text-red-400'
          )}>
            {trend >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            <span>{Math.abs(trend)}%</span>
          </div>
        )}
      </div>
    </div>
  )
}
