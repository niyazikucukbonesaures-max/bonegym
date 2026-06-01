/**
 * Performance Monitor System
 * Advanced performance monitoring and optimization for React applications
 */

export interface PerformanceThresholds {
  targetFPS: number
  maxMemoryUsage: number // MB
  maxRenderTime: number // ms
  maxComponentCount: number
  maxNetworkLatency: number // ms
}

export interface PerformanceMetrics {
  fps: number
  memoryUsage: number
  renderTime: number
  componentCount: number
  networkLatency: number
  frameDrops: number
  lastMeasurement: number
}

export interface PerformanceReport {
  timestamp: number
  metrics: PerformanceMetrics
  thresholds: PerformanceThresholds
  issues: PerformanceIssue[]
  recommendations: string[]
}

export interface PerformanceIssue {
  type: 'fps' | 'memory' | 'render' | 'network' | 'components'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  value: number
  threshold: number
}

export type PerformanceEventType = 'threshold-exceeded' | 'optimization-applied' | 'report-generated'

export interface PerformanceEvent {
  type: PerformanceEventType
  timestamp: number
  data: any
}

export type PerformanceEventListener = (event: PerformanceEvent) => void

class PerformanceMonitor {
  private static instance: PerformanceMonitor
  private isMonitoring = false
  private frameId: number | null = null
  private lastFrameTime = 0
  private frameCount = 0
  private fpsHistory: number[] = []
  private renderTimeHistory: number[] = []
  private memoryHistory: number[] = []
  private componentCountHistory: number[] = []
  
  private thresholds: PerformanceThresholds = {
    targetFPS: 60,
    maxMemoryUsage: 100, // 100MB
    maxRenderTime: 16, // 16ms for 60fps
    maxComponentCount: 1000,
    maxNetworkLatency: 1000 // 1 second
  }

  private currentMetrics: PerformanceMetrics = {
    fps: 60,
    memoryUsage: 0,
    renderTime: 0,
    componentCount: 0,
    networkLatency: 0,
    frameDrops: 0,
    lastMeasurement: 0
  }

  private eventListeners: Map<PerformanceEventType, PerformanceEventListener[]> = new Map()
  private optimizationStrategies: Map<string, () => void> = new Map()
  private reportHistory: PerformanceReport[] = []

  private constructor() {
    this.setupEventListeners()
    this.setupOptimizationStrategies()
  }

  public static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor()
    }
    return PerformanceMonitor.instance
  }

  public startMonitoring(): void {
    if (this.isMonitoring) return

    this.isMonitoring = true
    this.lastFrameTime = performance.now()
    this.monitorFrame()
    this.startMemoryMonitoring()
    this.startNetworkMonitoring()

    console.log('PerformanceMonitor: Monitoring started')
  }

  public stopMonitoring(): void {
    if (!this.isMonitoring) return

    this.isMonitoring = false
    
    if (this.frameId) {
      cancelAnimationFrame(this.frameId)
      this.frameId = null
    }

    console.log('PerformanceMonitor: Monitoring stopped')
  }

  public setThresholds(thresholds: Partial<PerformanceThresholds>): void {
    this.thresholds = { ...this.thresholds, ...thresholds }
  }

  public getCurrentMetrics(): PerformanceMetrics {
    return { ...this.currentMetrics }
  }

  public getReport(): PerformanceReport {
    const issues = this.analyzeIssues()
    const recommendations = this.generateRecommendations(issues)

    const report: PerformanceReport = {
      timestamp: Date.now(),
      metrics: { ...this.currentMetrics },
      thresholds: { ...this.thresholds },
      issues,
      recommendations
    }

    this.reportHistory.push(report)
    
    // Keep only last 100 reports
    if (this.reportHistory.length > 100) {
      this.reportHistory.shift()
    }

    this.emitEvent('report-generated', report)
    return report
  }

  public getReportHistory(): PerformanceReport[] {
    return [...this.reportHistory]
  }

  public addEventListener(type: PerformanceEventType, listener: PerformanceEventListener): void {
    if (!this.eventListeners.has(type)) {
      this.eventListeners.set(type, [])
    }
    this.eventListeners.get(type)!.push(listener)
  }

  public removeEventListener(type: PerformanceEventType, listener: PerformanceEventListener): void {
    const listeners = this.eventListeners.get(type)
    if (listeners) {
      const index = listeners.indexOf(listener)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  public measureRenderTime<T>(fn: () => T, componentName?: string): T {
    const startTime = performance.now()
    const result = fn()
    const endTime = performance.now()
    const renderTime = endTime - startTime

    this.renderTimeHistory.push(renderTime)
    if (this.renderTimeHistory.length > 100) {
      this.renderTimeHistory.shift()
    }

    // Update current metrics
    this.currentMetrics.renderTime = this.getAverageRenderTime()

    // Check threshold
    if (renderTime > this.thresholds.maxRenderTime) {
      this.emitEvent('threshold-exceeded', {
        type: 'render',
        value: renderTime,
        threshold: this.thresholds.maxRenderTime,
        componentName
      })
    }

    return result
  }

  public trackComponentMount(componentName: string): void {
    this.currentMetrics.componentCount++
    this.componentCountHistory.push(this.currentMetrics.componentCount)
    
    if (this.componentCountHistory.length > 100) {
      this.componentCountHistory.shift()
    }

    if (this.currentMetrics.componentCount > this.thresholds.maxComponentCount) {
      this.emitEvent('threshold-exceeded', {
        type: 'components',
        value: this.currentMetrics.componentCount,
        threshold: this.thresholds.maxComponentCount,
        componentName
      })
    }
  }

  public trackComponentUnmount(componentName: string): void {
    this.currentMetrics.componentCount = Math.max(0, this.currentMetrics.componentCount - 1)
  }

  public measureNetworkRequest(url: string, startTime: number, endTime: number): void {
    const latency = endTime - startTime
    this.currentMetrics.networkLatency = latency

    if (latency > this.thresholds.maxNetworkLatency) {
      this.emitEvent('threshold-exceeded', {
        type: 'network',
        value: latency,
        threshold: this.thresholds.maxNetworkLatency,
        url
      })
    }
  }

  private monitorFrame = (): void => {
    if (!this.isMonitoring) return

    const now = performance.now()
    const deltaTime = now - this.lastFrameTime

    if (deltaTime > 0) {
      const currentFPS = 1000 / deltaTime
      this.fpsHistory.push(currentFPS)

      // Keep only last 60 frames for FPS calculation
      if (this.fpsHistory.length > 60) {
        this.fpsHistory.shift()
      }

      // Calculate average FPS
      const avgFPS = this.fpsHistory.reduce((sum, fps) => sum + fps, 0) / this.fpsHistory.length
      this.currentMetrics.fps = Math.round(avgFPS)

      // Detect frame drops
      if (currentFPS < this.thresholds.targetFPS * 0.8) {
        this.currentMetrics.frameDrops++
      }

      // Check FPS threshold
      if (avgFPS < this.thresholds.targetFPS * 0.6) {
        this.emitEvent('threshold-exceeded', {
          type: 'fps',
          value: avgFPS,
          threshold: this.thresholds.targetFPS
        })
        
        // Apply automatic optimization
        this.applyOptimization('reduce-animations')
      }
    }

    this.lastFrameTime = now
    this.currentMetrics.lastMeasurement = now
    this.frameId = requestAnimationFrame(this.monitorFrame)
  }

  private startMemoryMonitoring(): void {
    const measureMemory = () => {
      if (!this.isMonitoring) return

      // Use performance.memory if available (Chrome)
      if ('memory' in performance) {
        const memory = (performance as any).memory
        const usedMB = memory.usedJSHeapSize / (1024 * 1024)
        
        this.currentMetrics.memoryUsage = usedMB
        this.memoryHistory.push(usedMB)

        if (this.memoryHistory.length > 100) {
          this.memoryHistory.shift()
        }

        // Check memory threshold
        if (usedMB > this.thresholds.maxMemoryUsage) {
          this.emitEvent('threshold-exceeded', {
            type: 'memory',
            value: usedMB,
            threshold: this.thresholds.maxMemoryUsage
          })

          // Apply memory optimization
          this.applyOptimization('garbage-collect')
        }
      }

      setTimeout(measureMemory, 1000) // Check every second
    }

    measureMemory()
  }

  private startNetworkMonitoring(): void {
    // Intercept fetch requests to measure network latency
    const originalFetch = window.fetch
    
    window.fetch = async (...args) => {
      const startTime = performance.now()
      
      try {
        const response = await originalFetch(...args)
        const endTime = performance.now()
        
        this.measureNetworkRequest(args[0].toString(), startTime, endTime)
        
        return response
      } catch (error) {
        const endTime = performance.now()
        this.measureNetworkRequest(args[0].toString(), startTime, endTime)
        throw error
      }
    }
  }

  private setupOptimizationStrategies(): void {
    this.optimizationStrategies.set('reduce-animations', () => {
      // Reduce animation quality or disable non-essential animations
      document.documentElement.style.setProperty('--animation-duration-multiplier', '0.5')
      console.log('PerformanceMonitor: Reduced animation duration')
    })

    this.optimizationStrategies.set('garbage-collect', () => {
      // Force garbage collection if available
      if ('gc' in window && typeof (window as any).gc === 'function') {
        (window as any).gc()
        console.log('PerformanceMonitor: Forced garbage collection')
      }
    })

    this.optimizationStrategies.set('reduce-quality', () => {
      // Reduce visual quality for better performance
      document.documentElement.style.setProperty('--blur-intensity', '0.5')
      console.log('PerformanceMonitor: Reduced visual quality')
    })
  }

  private applyOptimization(strategy: string): void {
    const optimization = this.optimizationStrategies.get(strategy)
    if (optimization) {
      optimization()
      this.emitEvent('optimization-applied', { strategy })
    }
  }

  private analyzeIssues(): PerformanceIssue[] {
    const issues: PerformanceIssue[] = []

    // FPS issues
    if (this.currentMetrics.fps < this.thresholds.targetFPS * 0.5) {
      issues.push({
        type: 'fps',
        severity: 'critical',
        message: `FPS is critically low: ${this.currentMetrics.fps}`,
        value: this.currentMetrics.fps,
        threshold: this.thresholds.targetFPS
      })
    } else if (this.currentMetrics.fps < this.thresholds.targetFPS * 0.8) {
      issues.push({
        type: 'fps',
        severity: 'high',
        message: `FPS is below target: ${this.currentMetrics.fps}`,
        value: this.currentMetrics.fps,
        threshold: this.thresholds.targetFPS
      })
    }

    // Memory issues
    if (this.currentMetrics.memoryUsage > this.thresholds.maxMemoryUsage * 1.5) {
      issues.push({
        type: 'memory',
        severity: 'critical',
        message: `Memory usage is critically high: ${this.currentMetrics.memoryUsage.toFixed(1)}MB`,
        value: this.currentMetrics.memoryUsage,
        threshold: this.thresholds.maxMemoryUsage
      })
    } else if (this.currentMetrics.memoryUsage > this.thresholds.maxMemoryUsage) {
      issues.push({
        type: 'memory',
        severity: 'high',
        message: `Memory usage exceeds threshold: ${this.currentMetrics.memoryUsage.toFixed(1)}MB`,
        value: this.currentMetrics.memoryUsage,
        threshold: this.thresholds.maxMemoryUsage
      })
    }

    // Render time issues
    if (this.currentMetrics.renderTime > this.thresholds.maxRenderTime * 2) {
      issues.push({
        type: 'render',
        severity: 'high',
        message: `Render time is too high: ${this.currentMetrics.renderTime.toFixed(1)}ms`,
        value: this.currentMetrics.renderTime,
        threshold: this.thresholds.maxRenderTime
      })
    }

    // Component count issues
    if (this.currentMetrics.componentCount > this.thresholds.maxComponentCount) {
      issues.push({
        type: 'components',
        severity: 'medium',
        message: `Too many components mounted: ${this.currentMetrics.componentCount}`,
        value: this.currentMetrics.componentCount,
        threshold: this.thresholds.maxComponentCount
      })
    }

    // Network issues
    if (this.currentMetrics.networkLatency > this.thresholds.maxNetworkLatency) {
      issues.push({
        type: 'network',
        severity: 'medium',
        message: `Network latency is high: ${this.currentMetrics.networkLatency.toFixed(0)}ms`,
        value: this.currentMetrics.networkLatency,
        threshold: this.thresholds.maxNetworkLatency
      })
    }

    return issues
  }

  private generateRecommendations(issues: PerformanceIssue[]): string[] {
    const recommendations: string[] = []

    issues.forEach(issue => {
      switch (issue.type) {
        case 'fps':
          recommendations.push('Consider reducing animation complexity or disabling non-essential animations')
          recommendations.push('Check for expensive operations in render loops')
          break
        case 'memory':
          recommendations.push('Look for memory leaks in event listeners or timers')
          recommendations.push('Consider implementing virtual scrolling for large lists')
          break
        case 'render':
          recommendations.push('Use React.memo() for expensive components')
          recommendations.push('Implement code splitting and lazy loading')
          break
        case 'components':
          recommendations.push('Implement virtualization for large component trees')
          recommendations.push('Consider component pooling for frequently mounted/unmounted components')
          break
        case 'network':
          recommendations.push('Implement request caching and debouncing')
          recommendations.push('Consider using a CDN for static assets')
          break
      }
    })

    return [...new Set(recommendations)] // Remove duplicates
  }

  private getAverageRenderTime(): number {
    if (this.renderTimeHistory.length === 0) return 0
    return this.renderTimeHistory.reduce((sum, time) => sum + time, 0) / this.renderTimeHistory.length
  }

  private setupEventListeners(): void {
    // Initialize event listener maps
    const eventTypes: PerformanceEventType[] = ['threshold-exceeded', 'optimization-applied', 'report-generated']
    eventTypes.forEach(type => {
      this.eventListeners.set(type, [])
    })
  }

  private emitEvent(type: PerformanceEventType, data: any): void {
    const event: PerformanceEvent = {
      type,
      timestamp: Date.now(),
      data
    }

    const listeners = this.eventListeners.get(type) || []
    listeners.forEach(listener => {
      try {
        listener(event)
      } catch (error) {
        console.error(`PerformanceMonitor: Error in ${type} event listener:`, error)
      }
    })
  }

  public destroy(): void {
    this.stopMonitoring()
    this.eventListeners.clear()
    this.optimizationStrategies.clear()
    this.reportHistory.length = 0

    // Restore original fetch
    // Note: In a real implementation, you'd want to store the original fetch reference
    
    PerformanceMonitor.instance = null as any
  }
}

export default PerformanceMonitor