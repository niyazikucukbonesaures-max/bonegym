/**
 * Animation Context Provider
 * React context for managing the animation system throughout the application
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import AnimationSystem from '@/lib/animation/AnimationSystem'
import { 
  AnimationOptions, 
  PerformanceMetrics, 
  AnimationSystemConfig,
  AnimationEventType,
  AnimationEventListener
} from '@/lib/animation/types'

interface AnimationContextValue {
  animationSystem: AnimationSystem
  performanceMetrics: PerformanceMetrics
  isReducedMotion: boolean
  createAnimation: (options: AnimationOptions) => string
  pauseAnimation: (id: string) => boolean
  resumeAnimation: (id: string) => boolean
  cancelAnimation: (id: string) => boolean
  addEventListener: (type: AnimationEventType, listener: AnimationEventListener) => void
  removeEventListener: (type: AnimationEventType, listener: AnimationEventListener) => void
}

const AnimationContext = createContext<AnimationContextValue | null>(null)

interface AnimationProviderProps {
  children: ReactNode
  config?: Partial<AnimationSystemConfig>
}

export const AnimationProvider: React.FC<AnimationProviderProps> = ({ 
  children, 
  config = {} 
}) => {
  const [animationSystem] = useState(() => AnimationSystem.getInstance(config))
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics>(() => 
    animationSystem.getPerformanceMetrics()
  )
  const [isReducedMotion, setIsReducedMotion] = useState(() => 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )

  useEffect(() => {
    // Monitor performance metrics
    const updateMetrics = () => {
      setPerformanceMetrics(animationSystem.getPerformanceMetrics())
    }

    const metricsInterval = setInterval(updateMetrics, 1000) // Update every second

    // Listen for reduced motion changes
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    const handleReducedMotionChange = (e: MediaQueryListEvent) => {
      setIsReducedMotion(e.matches)
    }

    mediaQuery.addEventListener('change', handleReducedMotionChange)

    // Performance monitoring
    let performanceWarningShown = false
    const performanceListener = () => {
      const metrics = animationSystem.getPerformanceMetrics()
      
      // Warn if FPS drops significantly
      if (metrics.fps < 30 && !performanceWarningShown) {
        console.warn('AnimationProvider: Low FPS detected:', metrics.fps)
        performanceWarningShown = true
        
        // Reset warning after 5 seconds
        setTimeout(() => {
          performanceWarningShown = false
        }, 5000)
      }
    }

    animationSystem.addEventListener('complete', performanceListener)

    return () => {
      clearInterval(metricsInterval)
      mediaQuery.removeEventListener('change', handleReducedMotionChange)
      animationSystem.removeEventListener('complete', performanceListener)
    }
  }, [animationSystem])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Don't destroy the singleton, just clean up listeners
      // The system will be reused across component remounts
    }
  }, [])

  const contextValue: AnimationContextValue = {
    animationSystem,
    performanceMetrics,
    isReducedMotion,
    createAnimation: (options: AnimationOptions) => animationSystem.createAnimation(options),
    pauseAnimation: (id: string) => animationSystem.pauseAnimation(id),
    resumeAnimation: (id: string) => animationSystem.resumeAnimation(id),
    cancelAnimation: (id: string) => animationSystem.cancelAnimation(id),
    addEventListener: (type: AnimationEventType, listener: AnimationEventListener) => 
      animationSystem.addEventListener(type, listener),
    removeEventListener: (type: AnimationEventType, listener: AnimationEventListener) => 
      animationSystem.removeEventListener(type, listener)
  }

  return (
    <AnimationContext.Provider value={contextValue}>
      {children}
    </AnimationContext.Provider>
  )
}

// Custom hook for using animation context
export const useAnimation = (): AnimationContextValue => {
  const context = useContext(AnimationContext)
  
  if (!context) {
    // Provider dışında kullanılırsa crash yerine fallback döndür
    // Bu sayede ErrorBoundary gibi provider dışı bileşenler de çalışır
    const fallbackSystem = AnimationSystem.getInstance()
    return {
      animationSystem: fallbackSystem,
      performanceMetrics: fallbackSystem.getPerformanceMetrics(),
      isReducedMotion: false,
      createAnimation: (options: AnimationOptions) => fallbackSystem.createAnimation(options),
      pauseAnimation: (id: string) => fallbackSystem.pauseAnimation(id),
      resumeAnimation: (id: string) => fallbackSystem.resumeAnimation(id),
      cancelAnimation: (id: string) => fallbackSystem.cancelAnimation(id),
      addEventListener: (type: AnimationEventType, listener: AnimationEventListener) => 
        fallbackSystem.addEventListener(type, listener),
      removeEventListener: (type: AnimationEventType, listener: AnimationEventListener) => 
        fallbackSystem.removeEventListener(type, listener)
    }
  }
  
  return context
}

// Hook for creating animations with automatic cleanup
export const useAnimationEffect = (
  options: Omit<AnimationOptions, 'element'>,
  elementRef: React.RefObject<HTMLElement>,
  dependencies: React.DependencyList = []
): string | null => {
  const { createAnimation, cancelAnimation } = useAnimation()
  const [animationId, setAnimationId] = useState<string | null>(null)

  useEffect(() => {
    if (!elementRef.current) return

    const id = createAnimation({
      ...options,
      element: elementRef.current
    })

    setAnimationId(id)

    return () => {
      if (id) {
        cancelAnimation(id)
      }
    }
  }, [elementRef.current, ...dependencies])

  return animationId
}

// Hook for performance monitoring
export const useAnimationPerformance = () => {
  const { performanceMetrics } = useAnimation()
  const [performanceHistory, setPerformanceHistory] = useState<PerformanceMetrics[]>([])

  useEffect(() => {
    setPerformanceHistory(prev => {
      const newHistory = [...prev, performanceMetrics]
      // Keep only last 60 entries (1 minute of data)
      return newHistory.slice(-60)
    })
  }, [performanceMetrics])

  const averageFPS = performanceHistory.length > 0 
    ? performanceHistory.reduce((sum, metrics) => sum + metrics.fps, 0) / performanceHistory.length
    : 60

  const isPerformanceGood = averageFPS >= 50
  const isPerformancePoor = averageFPS < 30

  return {
    currentMetrics: performanceMetrics,
    performanceHistory,
    averageFPS: Math.round(averageFPS),
    isPerformanceGood,
    isPerformancePoor
  }
}

// Hook for reduced motion handling
export const useReducedMotion = () => {
  const { isReducedMotion } = useAnimation()
  
  return {
    isReducedMotion,
    shouldAnimate: !isReducedMotion,
    getDuration: (normalDuration: number) => isReducedMotion ? Math.min(normalDuration, 200) : normalDuration,
    getEasing: (normalEasing: string) => isReducedMotion ? 'ease-out' : normalEasing
  }
}