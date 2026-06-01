import React from 'react'
import { cn } from '@/lib/utils'

interface GlassCardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  noblur?: boolean
  intensity?: 'subtle' | 'medium' | 'strong'
  adaptToBackground?: boolean
  useGPU?: boolean
  interactive?: boolean
  glassConfig?: Record<string, unknown>
  onClick?: () => void
}

export function GlassCard({ 
  children, 
  className, 
  hover = false, 
  noblur = false,
  interactive = false,
  onClick,
}: GlassCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-white/[0.07] bg-[#13131a]',
        noblur && 'bg-[#13131a]/80',
        hover && 'transition-all duration-200 hover:border-white/[0.12] hover:bg-[#16161f]',
        interactive && 'cursor-pointer',
        'transform-gpu',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}
