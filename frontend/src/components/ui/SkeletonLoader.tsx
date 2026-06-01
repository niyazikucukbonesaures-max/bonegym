/**
 * Skeleton Loader Component
 * Advanced skeleton loading with smart content detection
 */

import React, { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import LoadingStateManager, { SkeletonConfig } from '@/lib/loading/LoadingStateManager'

interface SkeletonLoaderProps {
  width?: string | number
  height?: string | number
  borderRadius?: string | number
  count?: number
  className?: string
  animate?: boolean
  speed?: number
  children?: React.ReactNode
  loading?: boolean
  variant?: 'text' | 'avatar' | 'card' | 'button' | 'custom'
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  width,
  height,
  borderRadius,
  count = 1,
  className,
  animate = true,
  speed = 2,
  children,
  loading = true,
  variant = 'custom'
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const loadingIdRef = useRef<string | null>(null)
  const loadingManager = LoadingStateManager.getInstance()

  // Preset configurations for different variants
  const getVariantConfig = (): Partial<SkeletonConfig> => {
    switch (variant) {
      case 'text':
        return {
          width: width || '100%',
          height: height || '16px',
          borderRadius: borderRadius || '4px',
          count: count
        }
      case 'avatar':
        return {
          width: width || '40px',
          height: height || '40px',
          borderRadius: borderRadius || '50%',
          count: 1
        }
      case 'card':
        return {
          width: width || '100%',
          height: height || '200px',
          borderRadius: borderRadius || '12px',
          count: 1
        }
      case 'button':
        return {
          width: width || '120px',
          height: height || '40px',
          borderRadius: borderRadius || '8px',
          count: 1
        }
      default:
        return {
          width: width || '100%',
          height: height || '20px',
          borderRadius: borderRadius || '4px',
          count: count
        }
    }
  }

  useEffect(() => {
    if (!containerRef.current) return

    if (loading) {
      const config: SkeletonConfig = {
        ...getVariantConfig(),
        animate,
        speed,
        className
      }

      loadingIdRef.current = loadingManager.createSkeleton(containerRef.current, config)
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
  }, [loading, width, height, borderRadius, count, animate, speed, className, variant])

  if (!loading && children) {
    return <>{children}</>
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'skeleton-loader',
        !loading && 'hidden',
        className
      )}
      aria-label="Loading content..."
      role="status"
    >
      {/* Fallback skeleton for non-JS environments */}
      <noscript>
        <div className="bg-white/10 animate-pulse rounded" style={{
          width: typeof width === 'number' ? `${width}px` : (width || '100%'),
          height: typeof height === 'number' ? `${height}px` : (height || '20px'),
          borderRadius: typeof borderRadius === 'number' ? `${borderRadius}px` : (borderRadius || '4px')
        }} />
      </noscript>
    </div>
  )
}

// Preset skeleton components
export const TextSkeleton: React.FC<{
  lines?: number
  className?: string
  loading?: boolean
  children?: React.ReactNode
}> = ({ lines = 3, className, loading = true, children }) => (
  <SkeletonLoader
    variant="text"
    count={lines}
    className={className}
    loading={loading}
  >
    {children}
  </SkeletonLoader>
)

export const AvatarSkeleton: React.FC<{
  size?: number
  className?: string
  loading?: boolean
  children?: React.ReactNode
}> = ({ size = 40, className, loading = true, children }) => (
  <SkeletonLoader
    variant="avatar"
    width={size}
    height={size}
    className={className}
    loading={loading}
  >
    {children}
  </SkeletonLoader>
)

export const CardSkeleton: React.FC<{
  width?: string | number
  height?: string | number
  className?: string
  loading?: boolean
  children?: React.ReactNode
}> = ({ width, height, className, loading = true, children }) => (
  <SkeletonLoader
    variant="card"
    width={width}
    height={height}
    className={className}
    loading={loading}
  >
    {children}
  </SkeletonLoader>
)

export const ButtonSkeleton: React.FC<{
  width?: string | number
  className?: string
  loading?: boolean
  children?: React.ReactNode
}> = ({ width, className, loading = true, children }) => (
  <SkeletonLoader
    variant="button"
    width={width}
    className={className}
    loading={loading}
  >
    {children}
  </SkeletonLoader>
)

// Complex skeleton layouts
export const ListSkeleton: React.FC<{
  items?: number
  itemHeight?: number
  className?: string
  loading?: boolean
  children?: React.ReactNode
}> = ({ items = 5, itemHeight = 60, className, loading = true, children }) => {
  if (!loading && children) {
    return <>{children}</>
  }

  return (
    <div className={cn('space-y-3', className)}>
      {Array.from({ length: items }).map((_, index) => (
        <div key={index} className="flex items-center space-x-3">
          <AvatarSkeleton size={40} loading={loading} />
          <div className="flex-1 space-y-2">
            <SkeletonLoader
              variant="text"
              width="60%"
              height="16px"
              loading={loading}
            />
            <SkeletonLoader
              variant="text"
              width="40%"
              height="14px"
              loading={loading}
            />
          </div>
        </div>
      ))}
      {!loading && children}
    </div>
  )
}

export const TableSkeleton: React.FC<{
  rows?: number
  columns?: number
  className?: string
  loading?: boolean
  children?: React.ReactNode
}> = ({ rows = 5, columns = 4, className, loading = true, children }) => {
  if (!loading && children) {
    return <>{children}</>
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* Header */}
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, index) => (
          <SkeletonLoader
            key={`header-${index}`}
            variant="text"
            width="80%"
            height="16px"
            loading={loading}
          />
        ))}
      </div>
      
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={`row-${rowIndex}`}
          className="grid gap-4"
          style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <SkeletonLoader
              key={`cell-${rowIndex}-${colIndex}`}
              variant="text"
              width="90%"
              height="14px"
              loading={loading}
            />
          ))}
        </div>
      ))}
      
      {!loading && children}
    </div>
  )
}