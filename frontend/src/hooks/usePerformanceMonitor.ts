/**
 * usePerformanceMonitor Hook
 * React hook for component-level performance monitoring
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import PerformanceMonitor, { 
  PerformanceMetrics, 
  PerformanceReport, 
  PerformanceEvent,
  PerformanceThresholds
} from '@/lib/performance/PerformanceMonitor'

export interface UsePerformanceMonitorOptions {
  componentName?: string
  trackRenderTime?: boolean
  trackMounts?: boolean
  autoStart?: boolean
  reportInterval?: number // ms
}

export interface PerformanceHookResult {
  metrics: PerformanceMetrics
  report: PerformanceReport | null
  isMonitoring: boolean
  startMonitoring: () => void
  stopMonitoring: () => void
  measureRender: <T>(fn: () => T) => T
  generateReport: () => PerformanceReport
  setThresholds: (thresholds: Partial<PerformanceThresholds>) => void
}

export function usePerformanceMonitor(options: UsePerformanceMonitorOptions = {}): PerformanceHookResult {
  const {
    componentName = 'UnknownComponent',
    trackRenderTime = true,
    trackMounts = true,
    autoStart = true,
    reportInterval = 5000 // 5 seconds
  } = options

  const performanceMonitor = PerformanceMonitor.getInstance()
  const [metrics, setMetrics] = useState<PerformanceMetrics>(() => 
    performanceMonitor.getCurrentMetrics()
  )
  const [report, setReport] = useState<PerformanceReport | null>(null)
  const [isMonitoring, setIsMonitoring] = useState(false)
  const reportIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const renderCountRef = useRef(0)

  // Track component mounts/unmounts
  useEffect(() => {
    if (trackMounts) {
      performanceMonitor.trackComponentMount(componentName)
      
      return () => {
        performanceMonitor.trackComponentUnmount(componentName)
      }
    }
  }, [componentName, trackMounts])

  // Auto-start monitoring
  useEffect(() => {
    if (autoStart) {
      startMonitoring()
    }

    return () => {
      stopMonitoring()
    }
  }, [autoStart])

  // Update metrics periodically
  useEffect(() => {
    if (!isMonitoring) return

    const updateMetrics = () => {
      setMetrics(performanceMonitor.getCurrentMetrics())
    }

    const interval = setInterval(updateMetrics, 1000) // Update every second

    return () => clearInterval(interval)
  }, [isMonitoring])

  // Generate reports periodically
  useEffect(() => {
    if (!isMonitoring || !reportInterval) return

    const generatePeriodicReport = () => {
      const newReport = performanceMonitor.getReport()
      setReport(newReport)
    }

    reportIntervalRef.current = setInterval(generatePeriodicReport, reportInterval)

    return () => {
      if (reportIntervalRef.current) {
        clearInterval(reportIntervalRef.current)
        reportIntervalRef.current = null
      }
    }
  }, [isMonitoring, reportInterval])

  const startMonitoring = useCallback(() => {
    if (isMonitoring) return

    performanceMonitor.startMonitoring()
    setIsMonitoring(true)
  }, [isMonitoring])

  const stopMonitoring = useCallback(() => {
    if (!isMonitoring) return

    performanceMonitor.stopMonitoring()
    setIsMonitoring(false)

    if (reportIntervalRef.current) {
      clearInterval(reportIntervalRef.current)
      reportIntervalRef.current = null
    }
  }, [isMonitoring])

  const measureRender = useCallback(<T>(fn: () => T): T => {
    if (!trackRenderTime) return fn()

    renderCountRef.current++
    return performanceMonitor.measureRenderTime(fn, `${componentName}-render-${renderCountRef.current}`)
  }, [componentName, trackRenderTime])

  const generateReport = useCallback(() => {
    const newReport = performanceMonitor.getReport()
    setReport(newReport)
    return newReport
  }, [])

  const setThresholds = useCallback((thresholds: Partial<PerformanceThresholds>) => {
    performanceMonitor.setThresholds(thresholds)
  }, [])

  return {
    metrics,
    report,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    measureRender,
    generateReport,
    setThresholds
  }
}

// Hook for measuring specific operations
export function usePerformanceMeasure(operationName: string) {
  const performanceMonitor = PerformanceMonitor.getInstance()

  const measure = useCallback(<T>(fn: () => T): T => {
    return performanceMonitor.measureRenderTime(fn, operationName)
  }, [operationName])

  return { measure }
}

// Hook for performance alerts
export function usePerformanceAlerts() {
  const [alerts, setAlerts] = useState<PerformanceEvent[]>([])
  const performanceMonitor = PerformanceMonitor.getInstance()

  useEffect(() => {
    const handleThresholdExceeded = (event: PerformanceEvent) => {
      setAlerts(prev => {
        const newAlerts = [...prev, event]
        // Keep only last 10 alerts
        return newAlerts.slice(-10)
      })
    }

    performanceMonitor.addEventListener('threshold-exceeded', handleThresholdExceeded)

    return () => {
      performanceMonitor.removeEventListener('threshold-exceeded', handleThresholdExceeded)
    }
  }, [])

  const clearAlerts = useCallback(() => {
    setAlerts([])
  }, [])

  const dismissAlert = useCallback((timestamp: number) => {
    setAlerts(prev => prev.filter(alert => alert.timestamp !== timestamp))
  }, [])

  return {
    alerts,
    clearAlerts,
    dismissAlert,
    hasAlerts: alerts.length > 0,
    criticalAlerts: alerts.filter(alert => 
      alert.data.severity === 'critical'
    ).length
  }
}

// Hook for performance optimization suggestions
export function usePerformanceOptimization() {
  const [optimizations, setOptimizations] = useState<PerformanceEvent[]>([])
  const performanceMonitor = PerformanceMonitor.getInstance()

  useEffect(() => {
    const handleOptimizationApplied = (event: PerformanceEvent) => {
      setOptimizations(prev => {
        const newOptimizations = [...prev, event]
        // Keep only last 5 optimizations
        return newOptimizations.slice(-5)
      })
    }

    performanceMonitor.addEventListener('optimization-applied', handleOptimizationApplied)

    return () => {
      performanceMonitor.removeEventListener('optimization-applied', handleOptimizationApplied)
    }
  }, [])

  return {
    optimizations,
    lastOptimization: optimizations[optimizations.length - 1] || null,
    optimizationCount: optimizations.length
  }
}

// Hook for component performance tracking
export function useComponentPerformance(componentName: string) {
  const renderTimeRef = useRef<number[]>([])
  const mountTimeRef = useRef<number>(0)
  const performanceMonitor = PerformanceMonitor.getInstance()

  useEffect(() => {
    mountTimeRef.current = performance.now()
    performanceMonitor.trackComponentMount(componentName)

    return () => {
      performanceMonitor.trackComponentUnmount(componentName)
    }
  }, [componentName])

  const trackRender = useCallback(() => {
    const startTime = performance.now()
    
    return () => {
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      renderTimeRef.current.push(renderTime)
      
      // Keep only last 10 render times
      if (renderTimeRef.current.length > 10) {
        renderTimeRef.current.shift()
      }

      performanceMonitor.measureRenderTime(() => {}, `${componentName}-render`)
    }
  }, [componentName])

  const getAverageRenderTime = useCallback(() => {
    if (renderTimeRef.current.length === 0) return 0
    return renderTimeRef.current.reduce((sum, time) => sum + time, 0) / renderTimeRef.current.length
  }, [])

  const getMountDuration = useCallback(() => {
    return performance.now() - mountTimeRef.current
  }, [])

  return {
    trackRender,
    getAverageRenderTime,
    getMountDuration,
    renderCount: renderTimeRef.current.length,
    lastRenderTime: renderTimeRef.current[renderTimeRef.current.length - 1] || 0
  }
}

// Hook for network performance monitoring
export function useNetworkPerformance() {
  const [networkMetrics, setNetworkMetrics] = useState({
    averageLatency: 0,
    requestCount: 0,
    errorCount: 0,
    slowRequests: 0
  })

  const performanceMonitor = PerformanceMonitor.getInstance()

  useEffect(() => {
    let requestCount = 0
    let totalLatency = 0
    let errorCount = 0
    let slowRequests = 0

    const handleNetworkEvent = (event: PerformanceEvent) => {
      if (event.data.type === 'network') {
        requestCount++
        totalLatency += event.data.value
        
        if (event.data.value > 1000) { // Slow request threshold
          slowRequests++
        }

        setNetworkMetrics({
          averageLatency: totalLatency / requestCount,
          requestCount,
          errorCount,
          slowRequests
        })
      }
    }

    performanceMonitor.addEventListener('threshold-exceeded', handleNetworkEvent)

    return () => {
      performanceMonitor.removeEventListener('threshold-exceeded', handleNetworkEvent)
    }
  }, [])

  return networkMetrics
}