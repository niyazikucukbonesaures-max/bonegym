/**
 * Performance Error Handler
 * Handles performance-related errors and provides automatic optimization
 */

import { PerformanceMetrics } from '@/lib/animation/types'

export interface PerformanceError extends Error {
  metric?: string
  value?: number
  threshold?: number
  component?: string
  timestamp?: number
}

export interface PerformanceThresholds {
  fps: number
  memoryUsage: number
  renderTime: number
  animationCount: number
}

export class PerformanceErrorHandler {
  private static instance: PerformanceErrorHandler
  private errorCount = 0
  private optimizationLevel = 0 // 0: none, 1: light, 2: aggressive
  private errorCallbacks: ((error: PerformanceError) => void)[] = []
  private performanceObserver: PerformanceObserver | null = null
  private memoryCheckInterval: NodeJS.Timeout | null = null

  private thresholds: PerformanceThresholds = {
    fps: 30,
    memoryUsage: 100 * 1024 * 1024, // 100MB
    renderTime: 16, // 16ms for 60fps
    animationCount: 20
  }

  private constructor() {
    this.initializePerformanceMonitoring()
  }

  static getInstance(): PerformanceErrorHandler {
    if (!PerformanceErrorHandler.instance) {
      PerformanceErrorHandler.instance = new PerformanceErrorHandler()
    }
    return PerformanceErrorHandler.instance
  }

  /**
   * Initialize performance monitoring
   */
  private initializePerformanceMonitoring(): void {
    // Monitor long tasks
    if ('PerformanceObserver' in window) {
      try {
        this.performanceObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          entries.forEach((entry) => {
            if (entry.duration > 50) { // Tasks longer than 50ms
              const error = this.createError(
                `Long task detected: ${entry.duration.toFixed(2)}ms`,
                'longTask',
                entry.duration,
                50
              )
              this.handleError(error)
            }
          })
        })

        this.performanceObserver.observe({ entryTypes: ['longtask'] })
      } catch (error) {
        console.warn('Performance observer not supported:', error)
      }
    }

    // Monitor memory usage
    this.startMemoryMonitoring()
  }

  /**
   * Start memory monitoring
   */
  private startMemoryMonitoring(): void {
    if ('memory' in performance) {
      this.memoryCheckInterval = setInterval(() => {
        const memory = (performance as any).memory
        if (memory.usedJSHeapSize > this.thresholds.memoryUsage) {
          const error = this.createError(
            `High memory usage: ${(memory.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`,
            'memoryUsage',
            memory.usedJSHeapSize,
            this.thresholds.memoryUsage
          )
          this.handleError(error)
        }
      }, 5000) // Check every 5 seconds
    }
  }

  /**
   * Handle performance errors with automatic optimization
   */
  handleError(error: PerformanceError): void {
    this.errorCount++
    
    console.warn('Performance error occurred:', {
      message: error.message,
      metric: error.metric,
      value: error.value,
      threshold: error.threshold,
      component: error.component,
      errorCount: this.errorCount
    })

    // Apply optimizations based on error type and count
    this.applyOptimizations(error)

    // Notify error callbacks
    this.errorCallbacks.forEach(callback => {
      try {
        callback(error)
      } catch (callbackError) {
        console.error('Error in performance error callback:', callbackError)
      }
    })
  }

  /**
   * Apply performance optimizations
   */
  private applyOptimizations(error: PerformanceError): void {
    // Increase optimization level based on error frequency
    if (this.errorCount > 5 && this.optimizationLevel < 1) {
      this.enableLightOptimizations()
    } else if (this.errorCount > 15 && this.optimizationLevel < 2) {
      this.enableAggressiveOptimizations()
    }

    // Apply specific optimizations based on error type
    switch (error.metric) {
      case 'fps':
        this.optimizeFPS()
        break
      case 'memoryUsage':
        this.optimizeMemory()
        break
      case 'renderTime':
        this.optimizeRendering()
        break
      case 'longTask':
        this.optimizeLongTasks()
        break
    }
  }

  /**
   * Enable light performance optimizations
   */
  private enableLightOptimizations(): void {
    this.optimizationLevel = 1
    console.info('Enabling light performance optimizations')

    // Reduce animation quality
    document.documentElement.classList.add('perf-optimize-light')
    
    // Add CSS optimizations
    this.addOptimizationStyles(`
      .perf-optimize-light .animate-spin {
        animation-duration: 1.5s !important;
      }
      .perf-optimize-light .skeleton {
        animation-duration: 3s !important;
      }
      .perf-optimize-light .hover-scale:hover {
        transform: scale(1.02) !important;
      }
    `)
  }

  /**
   * Enable aggressive performance optimizations
   */
  private enableAggressiveOptimizations(): void {
    this.optimizationLevel = 2
    console.info('Enabling aggressive performance optimizations')

    // Disable most animations
    document.documentElement.classList.add('perf-optimize-aggressive')
    
    // Add aggressive CSS optimizations
    this.addOptimizationStyles(`
      .perf-optimize-aggressive * {
        animation-duration: 0.1s !important;
        transition-duration: 0.1s !important;
      }
      .perf-optimize-aggressive .skeleton {
        animation: none !important;
        background: rgba(255, 255, 255, 0.1) !important;
      }
      .perf-optimize-aggressive .hover-scale:hover {
        transform: none !important;
      }
      .perf-optimize-aggressive .glass-card:hover {
        transform: none !important;
      }
    `)
  }

  /**
   * Add optimization styles to document
   */
  private addOptimizationStyles(css: string): void {
    const styleId = `perf-optimization-${this.optimizationLevel}`
    let style = document.getElementById(styleId) as HTMLStyleElement
    
    if (!style) {
      style = document.createElement('style')
      style.id = styleId
      document.head.appendChild(style)
    }
    
    style.textContent = css
  }

  /**
   * Optimize FPS performance
   */
  private optimizeFPS(): void {
    // Reduce concurrent animations
    const animations = document.getAnimations()
    if (animations.length > this.thresholds.animationCount) {
      // Pause some animations
      animations.slice(this.thresholds.animationCount).forEach(animation => {
        animation.pause()
      })
    }

    // Enable GPU acceleration for critical elements
    const criticalElements = document.querySelectorAll('.glass-card, .animate-spin')
    criticalElements.forEach(element => {
      (element as HTMLElement).style.willChange = 'transform'
      ;(element as HTMLElement).style.transform = 'translateZ(0)'
    })
  }

  /**
   * Optimize memory usage
   */
  private optimizeMemory(): void {
    // Force garbage collection if available
    if ('gc' in window && typeof (window as any).gc === 'function') {
      try {
        ;(window as any).gc()
      } catch (error) {
        console.warn('Manual garbage collection failed:', error)
      }
    }

    // Clear unused animations
    const animations = document.getAnimations()
    animations.forEach(animation => {
      if (animation.playState === 'finished') {
        animation.cancel()
      }
    })

    // Remove unused event listeners
    this.cleanupEventListeners()
  }

  /**
   * Optimize rendering performance
   */
  private optimizeRendering(): void {
    // Reduce blur effects
    const blurElements = document.querySelectorAll('[class*="backdrop-blur"]')
    blurElements.forEach(element => {
      element.classList.remove('backdrop-blur-lg', 'backdrop-blur-md')
      element.classList.add('backdrop-blur-sm')
    })

    // Simplify shadows
    const shadowElements = document.querySelectorAll('.shadow-xl, .shadow-2xl')
    shadowElements.forEach(element => {
      element.classList.remove('shadow-xl', 'shadow-2xl')
      element.classList.add('shadow-lg')
    })
  }

  /**
   * Optimize long tasks
   */
  private optimizeLongTasks(): void {
    // Break up long-running operations using requestIdleCallback
    if ('requestIdleCallback' in window) {
      // Schedule non-critical work during idle time
      requestIdleCallback(() => {
        this.performMaintenanceTasks()
      })
    }
  }

  /**
   * Perform maintenance tasks during idle time
   */
  private performMaintenanceTasks(): void {
    // Clean up finished animations
    const animations = document.getAnimations()
    animations.forEach(animation => {
      if (animation.playState === 'finished') {
        animation.cancel()
      }
    })

    // Clean up unused DOM elements
    const unusedElements = document.querySelectorAll('[data-cleanup="true"]')
    unusedElements.forEach(element => element.remove())
  }

  /**
   * Clean up event listeners
   */
  private cleanupEventListeners(): void {
    // This is a placeholder - in a real implementation,
    // you would track and clean up specific event listeners
    console.info('Cleaning up unused event listeners')
  }

  /**
   * Monitor component performance
   */
  monitorComponent(componentName: string, renderTime: number): void {
    if (renderTime > this.thresholds.renderTime) {
      const error = this.createError(
        `Slow component render: ${componentName} took ${renderTime.toFixed(2)}ms`,
        'renderTime',
        renderTime,
        this.thresholds.renderTime,
        componentName
      )
      this.handleError(error)
    }
  }

  /**
   * Monitor FPS
   */
  monitorFPS(fps: number): void {
    if (fps < this.thresholds.fps) {
      const error = this.createError(
        `Low FPS detected: ${fps.toFixed(1)} fps`,
        'fps',
        fps,
        this.thresholds.fps
      )
      this.handleError(error)
    }
  }

  /**
   * Create performance error
   */
  createError(
    message: string,
    metric?: string,
    value?: number,
    threshold?: number,
    component?: string
  ): PerformanceError {
    const error = new Error(message) as PerformanceError
    error.name = 'PerformanceError'
    error.metric = metric
    error.value = value
    error.threshold = threshold
    error.component = component
    error.timestamp = Date.now()
    return error
  }

  /**
   * Add error callback
   */
  onError(callback: (error: PerformanceError) => void): void {
    this.errorCallbacks.push(callback)
  }

  /**
   * Remove error callback
   */
  offError(callback: (error: PerformanceError) => void): void {
    const index = this.errorCallbacks.indexOf(callback)
    if (index > -1) {
      this.errorCallbacks.splice(index, 1)
    }
  }

  /**
   * Update performance thresholds
   */
  updateThresholds(thresholds: Partial<PerformanceThresholds>): void {
    this.thresholds = { ...this.thresholds, ...thresholds }
  }

  /**
   * Reset optimizations
   */
  reset(): void {
    this.errorCount = 0
    this.optimizationLevel = 0
    document.documentElement.classList.remove('perf-optimize-light', 'perf-optimize-aggressive')
    
    // Remove optimization styles
    const styles = document.querySelectorAll('[id^="perf-optimization-"]')
    styles.forEach(style => style.remove())
  }

  /**
   * Get performance statistics
   */
  getStats() {
    return {
      errorCount: this.errorCount,
      optimizationLevel: this.optimizationLevel,
      thresholds: this.thresholds
    }
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    if (this.performanceObserver) {
      this.performanceObserver.disconnect()
      this.performanceObserver = null
    }

    if (this.memoryCheckInterval) {
      clearInterval(this.memoryCheckInterval)
      this.memoryCheckInterval = null
    }

    this.errorCallbacks = []
  }
}

export default PerformanceErrorHandler