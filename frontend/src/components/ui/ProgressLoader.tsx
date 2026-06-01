/**
 * Progress Loader Component
 * Advanced progress indicators with ETA and network adaptation
 */

import React, { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import LoadingStateManager, { ProgressConfig } from '@/lib/loading/LoadingStateManager'

interface ProgressLoaderProps {
  value: number
  max?: number
  showPercentage?: boolean
  showETA?: boolean
  color?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'linear' | 'circular' | 'radial'
  className?: string
  label?: string
  animated?: boolean
  striped?: boolean
}

export const ProgressLoader: React.FC<ProgressLoaderProps> = ({
  value,
  max = 100,
  showPercentage = true,
  showETA = false,
  color = 'violet',
  size = 'md',
  variant = 'linear',
  className,
  label,
  animated = true,
  striped = false
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const loadingIdRef = useRef<string | null>(null)
  const [startTime] = useState(Date.now())
  const [eta, setEta] = useState<string>('')
  const loadingManager = LoadingStateManager.getInstance()

  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  // Calculate ETA
  useEffect(() => {
    if (showETA && value > 0 && value < max) {
      const elapsed = Date.now() - startTime
      const rate = value / elapsed
      const remaining = max - value
      const etaMs = remaining / rate
      
      if (etaMs > 0 && isFinite(etaMs)) {
        const etaSeconds = Math.round(etaMs / 1000)
        if (etaSeconds < 60) {
          setEta(`${etaSeconds}s kaldı`)
        } else {
          const minutes = Math.floor(etaSeconds / 60)
          const seconds = etaSeconds % 60
          setEta(`${minutes}m ${seconds}s kaldı`)
        }
      }
    }
  }, [value, max, showETA, startTime])

  // Initialize progress loader
  useEffect(() => {
    if (!containerRef.current) return

    const config: ProgressConfig = {
      total: max,
      current: value,
      showPercentage,
      showETA,
      color
    }

    loadingIdRef.current = loadingManager.createProgressLoader(containerRef.current, config)

    return () => {
      if (loadingIdRef.current) {
        loadingManager.cancelLoading(loadingIdRef.current)
      }
    }
  }, [])

  // Update progress
  useEffect(() => {
    if (loadingIdRef.current) {
      loadingManager.updateProgress(loadingIdRef.current, value, max)
    }
  }, [value, max])

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  }

  const colorClasses = {
    violet: 'bg-violet-500',
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    red: 'bg-red-500',
    yellow: 'bg-yellow-500',
    indigo: 'bg-indigo-500'
  }

  if (variant === 'circular') {
    return (
      <div className={cn('relative inline-flex items-center justify-center', className)}>
        <svg
          className="transform -rotate-90"
          width="120"
          height="120"
          viewBox="0 0 120 120"
        >
          {/* Background circle */}
          <circle
            cx="60"
            cy="60"
            r="54"
            stroke="currentColor"
            strokeWidth="12"
            fill="transparent"
            className="text-white/10"
          />
          {/* Progress circle */}
          <circle
            cx="60"
            cy="60"
            r="54"
            stroke="currentColor"
            strokeWidth="12"
            fill="transparent"
            strokeDasharray={`${2 * Math.PI * 54}`}
            strokeDashoffset={`${2 * Math.PI * 54 * (1 - percentage / 100)}`}
            className={cn(
              colorClasses[color as keyof typeof colorClasses] || colorClasses.violet,
              animated && 'transition-all duration-300 ease-out'
            )}
            strokeLinecap="round"
          />
        </svg>
        
        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {showPercentage && (
            <span className="text-2xl font-bold text-white">
              {Math.round(percentage)}%
            </span>
          )}
          {label && (
            <span className="text-sm text-white/60 mt-1">{label}</span>
          )}
          {showETA && eta && (
            <span className="text-xs text-white/40 mt-1">{eta}</span>
          )}
        </div>
      </div>
    )
  }

  if (variant === 'radial') {
    const radius = 45
    const circumference = 2 * Math.PI * radius
    const strokeDashoffset = circumference - (percentage / 100) * circumference

    return (
      <div className={cn('relative inline-flex items-center justify-center', className)}>
        <svg className="w-32 h-32 transform -rotate-90">
          <circle
            cx="64"
            cy="64"
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            className="text-white/10"
          />
          <circle
            cx="64"
            cy="64"
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className={cn(
              colorClasses[color as keyof typeof colorClasses] || colorClasses.violet,
              animated && 'transition-all duration-500 ease-out'
            )}
            strokeLinecap="round"
          />
        </svg>
        
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {showPercentage && (
            <span className="text-xl font-bold text-white">
              {Math.round(percentage)}%
            </span>
          )}
          {label && (
            <span className="text-xs text-white/60">{label}</span>
          )}
        </div>
      </div>
    )
  }

  // Linear variant (default)
  return (
    <div className={cn('w-full', className)}>
      {(label || showPercentage || showETA) && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-white/80">{label}</span>
          <div className="flex items-center gap-2 text-sm text-white/60">
            {showPercentage && <span>{Math.round(percentage)}%</span>}
            {showETA && eta && <span>{eta}</span>}
          </div>
        </div>
      )}
      
      <div
        ref={containerRef}
        className={cn(
          'w-full bg-white/10 rounded-full overflow-hidden',
          sizeClasses[size]
        )}
      >
        <div
          className={cn(
            'h-full rounded-full transition-all duration-300 ease-out',
            colorClasses[color as keyof typeof colorClasses] || colorClasses.violet,
            striped && 'bg-gradient-to-r from-transparent via-white/20 to-transparent bg-[length:20px_100%]',
            animated && striped && 'animate-pulse'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

// Specialized progress components
export const FileUploadProgress: React.FC<{
  fileName: string
  progress: number
  size?: string
  className?: string
}> = ({ fileName, progress, size, className }) => (
  <div className={cn('space-y-2', className)}>
    <div className="flex items-center justify-between">
      <span className="text-sm text-white/80 truncate">{fileName}</span>
      <span className="text-xs text-white/60">{size}</span>
    </div>
    <ProgressLoader
      value={progress}
      showPercentage
      showETA
      color="green"
      size="sm"
    />
  </div>
)

export const LoadingProgress: React.FC<{
  steps: string[]
  currentStep: number
  className?: string
}> = ({ steps, currentStep, className }) => (
  <div className={cn('space-y-4', className)}>
    <ProgressLoader
      value={currentStep}
      max={steps.length}
      showPercentage
      label="İlerleme"
      color="violet"
    />
    
    <div className="space-y-2">
      {steps.map((step, index) => (
        <div
          key={index}
          className={cn(
            'flex items-center gap-2 text-sm',
            index < currentStep && 'text-green-400',
            index === currentStep && 'text-violet-400',
            index > currentStep && 'text-white/40'
          )}
        >
          <div className={cn(
            'w-2 h-2 rounded-full',
            index < currentStep && 'bg-green-400',
            index === currentStep && 'bg-violet-400 animate-pulse',
            index > currentStep && 'bg-white/20'
          )} />
          {step}
        </div>
      ))}
    </div>
  </div>
)