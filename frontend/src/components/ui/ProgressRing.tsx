import { motion } from 'framer-motion'

interface ProgressRingProps {
  value: number
  size?: number
  strokeWidth?: number
  color?: string
  label?: string
  sublabel?: string
}

export function ProgressRing({
  value,
  size = 120,
  strokeWidth = 10,
  color = '#8b5cf6',
  label,
  sublabel,
}: ProgressRingProps) {
  const clampedValue = Math.min(100, Math.max(0, value))
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const center = size / 2

  return (
    <div className="relative inline-flex items-center justify-center hover:scale-110 transition-transform duration-300" style={{ width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Track */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={strokeWidth}
        />
        {/* Progress */}
        <motion.circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: clampedValue / 100 }}
          transition={{ duration: 1.5, ease: 'easeOut' }}
          style={{ 
            strokeDashoffset: 0,
            filter: 'drop-shadow(0 0 8px rgba(139, 92, 246, 0.5))'
          }}
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-2xl font-bold text-white">{clampedValue}%</span>
        {label && <span className="text-xs font-medium text-white/80 mt-1 uppercase tracking-wider">{label}</span>}
        {sublabel && <span className="text-xs text-white/50">{sublabel}</span>}
      </div>
    </div>
  )
}
