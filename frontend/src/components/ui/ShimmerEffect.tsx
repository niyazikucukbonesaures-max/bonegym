/**
 * Shimmer Effect Component
 * Advanced shimmer loading effects with customizable patterns
 */

import React, { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import LoadingStateManager from '@/lib/loading/LoadingStateManager'

interface ShimmerEffectProps {
  width?: string | number
  height?: string | number
  borderRadius?: string | number
  className?: string
  children?: React.ReactNode
  loading?: boolean
  direction?: 'ltr' | 'rtl' | 'ttb' | 'btt'
  speed?: number
  intensity?: 'subtle' | 'medium' | 'strong'
  pattern?: 'wave' | 'pulse' | 'gradient' | 'sparkle'
}

export const ShimmerEffect: React.FC<ShimmerEffectProps> = ({
  width = '100%',
  height = '20px',
  borderRadius = '4px',
  className,
  children,
  loading = true,
  direction = 'ltr',
  speed = 2,
  intensity = 'medium',
  pattern = 'wave'
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const loadingIdRef = useRef<string | null>(null)
  const loadingManager = LoadingStateManager.getInstance()

  useEffect(() => {
    if (!containerRef.current) return

    if (loading) {
      loadingIdRef.current = loadingManager.startLoading(containerRef.current, {
        id: `shimmer-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type: 'shimmer',
        priority: 'medium'
      })
    } else {
      if (loadingIdRef.current) {
        loadingManager.completeLoading(loadingIdRef.current, true)
        loadingIdRef.current = null
      }
    }

    return () => {
      if (loadingIdRef.current) {
        loadingManager.cancelLoading(loadingIdRef.current)
      }
    }
  }, [loading])

  const getShimmerStyles = () => {
    const intensityValues = {
      subtle: { from: 0.05, to: 0.1 },
      medium: { from: 0.1, to: 0.2 },
      strong: { from: 0.2, to: 0.4 }
    }

    const { from, to } = intensityValues[intensity]

    const directions = {
      ltr: '90deg',
      rtl: '270deg',
      ttb: '180deg',
      btt: '0deg'
    }

    const patterns = {
      wave: `linear-gradient(${directions[direction]}, 
        rgba(255, 255, 255, ${from}) 0%, 
        rgba(255, 255, 255, ${to}) 50%, 
        rgba(255, 255, 255, ${from}) 100%)`,
      
      pulse: `radial-gradient(circle, 
        rgba(255, 255, 255, ${to}) 0%, 
        rgba(255, 255, 255, ${from}) 70%)`,
      
      gradient: `linear-gradient(${directions[direction]}, 
        transparent 0%, 
        rgba(255, 255, 255, ${from}) 25%, 
        rgba(255, 255, 255, ${to}) 50%, 
        rgba(255, 255, 255, ${from}) 75%, 
        transparent 100%)`,
      
      sparkle: `conic-gradient(from 0deg, 
        rgba(255, 255, 255, ${from}) 0deg, 
        rgba(255, 255, 255, ${to}) 90deg, 
        rgba(255, 255, 255, ${from}) 180deg, 
        rgba(255, 255, 255, ${to}) 270deg, 
        rgba(255, 255, 255, ${from}) 360deg)`
    }

    return {
      background: patterns[pattern],
      backgroundSize: pattern === 'wave' || pattern === 'gradient' ? '200% 100%' : '100% 100%',
      animation: `shimmer-${pattern} ${speed}s ease-in-out infinite`
    }
  }

  if (!loading && children) {
    return <>{children}</>
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'shimmer-effect bg-white/5',
        className
      )}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
        borderRadius: typeof borderRadius === 'number' ? `${borderRadius}px` : borderRadius,
        ...getShimmerStyles()
      }}
      aria-label="Loading content..."
      role="status"
    >
      {loading && (
        <div className="sr-only">Yükleniyor...</div>
      )}
    </div>
  )
}

// Preset shimmer components
export const TextShimmer: React.FC<{
  lines?: number
  className?: string
  loading?: boolean
  children?: React.ReactNode
}> = ({ lines = 3, className, loading = true, children }) => (
  <div className={cn('space-y-2', className)}>
    {Array.from({ length: lines }).map((_, index) => (
      <ShimmerEffect
        key={index}
        width={index === lines - 1 ? '60%' : '100%'}
        height="16px"
        loading={loading}
      />
    ))}
    {!loading && children}
  </div>
)

export const CardShimmer: React.FC<{
  className?: string
  loading?: boolean
  children?: React.ReactNode
}> = ({ className, loading = true, children }) => (
  <div className={cn('space-y-4', className)}>
    <ShimmerEffect
      width="100%"
      height="200px"
      borderRadius="12px"
      loading={loading}
    />
    <div className="space-y-2">
      <ShimmerEffect
        width="80%"
        height="20px"
        loading={loading}
      />
      <ShimmerEffect
        width="60%"
        height="16px"
        loading={loading}
      />
    </div>
    {!loading && children}
  </div>
)

export const AvatarShimmer: React.FC<{
  size?: number
  className?: string
  loading?: boolean
  children?: React.ReactNode
}> = ({ size = 40, className, loading = true, children }) => (
  <ShimmerEffect
    width={size}
    height={size}
    borderRadius="50%"
    className={className}
    loading={loading}
    pattern="pulse"
  >
    {children}
  </ShimmerEffect>
)

export const ButtonShimmer: React.FC<{
  width?: string | number
  className?: string
  loading?: boolean
  children?: React.ReactNode
}> = ({ width = '120px', className, loading = true, children }) => (
  <ShimmerEffect
    width={width}
    height="40px"
    borderRadius="8px"
    className={className}
    loading={loading}
    intensity="medium"
  >
    {children}
  </ShimmerEffect>
)

// Complex shimmer layouts
export const ListItemShimmer: React.FC<{
  className?: string
  loading?: boolean
  children?: React.ReactNode
}> = ({ className, loading = true, children }) => (
  <div className={cn('flex items-center space-x-3', className)}>
    <AvatarShimmer size={40} loading={loading} />
    <div className="flex-1 space-y-2">
      <ShimmerEffect
        width="60%"
        height="16px"
        loading={loading}
      />
      <ShimmerEffect
        width="40%"
        height="14px"
        loading={loading}
        intensity="subtle"
      />
    </div>
    {!loading && children}
  </div>
)

export const TableRowShimmer: React.FC<{
  columns?: number
  className?: string
  loading?: boolean
  children?: React.ReactNode
}> = ({ columns = 4, className, loading = true, children }) => (
  <div className={cn('grid gap-4', className)} style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
    {Array.from({ length: columns }).map((_, index) => (
      <ShimmerEffect
        key={index}
        width="90%"
        height="14px"
        loading={loading}
      />
    ))}
    {!loading && children}
  </div>
)

// Add CSS animations to index.css
export const shimmerAnimations = `
@keyframes shimmer-wave {
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
}

@keyframes shimmer-pulse {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

@keyframes shimmer-gradient {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

@keyframes shimmer-sparkle {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
`