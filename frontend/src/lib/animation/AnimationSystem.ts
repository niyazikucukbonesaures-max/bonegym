/**
 * Core Animation System
 * Advanced animation engine with GPU acceleration and performance monitoring
 */

import { 
  AnimationConfig, 
  AnimationOptions, 
  AnimationInstance, 
  PerformanceMetrics, 
  AnimationSystemConfig,
  AnimationEvent,
  AnimationEventListener,
  AnimationEventType
} from './types'

class AnimationSystem {
  private static instance: AnimationSystem
  private config: AnimationSystemConfig
  private activeAnimations: Map<string, AnimationInstance> = new Map()
  private eventListeners: Map<AnimationEventType, AnimationEventListener[]> = new Map()
  private performanceMetrics: PerformanceMetrics
  private frameId: number | null = null
  private lastFrameTime = 0
  private frameCount = 0
  private fpsHistory: number[] = []
  private reducedMotionEnabled = false

  private constructor(config: Partial<AnimationSystemConfig> = {}) {
    this.config = {
      maxConcurrentAnimations: 50,
      targetFPS: 60,
      enableGPUAcceleration: true,
      respectReducedMotion: true,
      performanceMonitoring: true,
      debugMode: false,
      ...config
    }

    this.performanceMetrics = {
      fps: 60,
      frameDrops: 0,
      memoryUsage: 0,
      activeAnimations: 0,
      lastFrameTime: 0
    }

    this.init()
  }

  public static getInstance(config?: Partial<AnimationSystemConfig>): AnimationSystem {
    if (!AnimationSystem.instance) {
      AnimationSystem.instance = new AnimationSystem(config)
    }
    return AnimationSystem.instance
  }

  private init(): void {
    // Check for reduced motion preference
    if (this.config.respectReducedMotion) {
      this.reducedMotionEnabled = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      
      // Listen for changes
      window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
        this.reducedMotionEnabled = e.matches
        if (this.reducedMotionEnabled) {
          this.cancelAllAnimations()
        }
      })
    }

    // Start performance monitoring
    if (this.config.performanceMonitoring) {
      this.startPerformanceMonitoring()
    }

    // Initialize event listener maps
    const eventTypes: AnimationEventType[] = ['start', 'complete', 'cancel', 'pause', 'resume']
    eventTypes.forEach(type => {
      this.eventListeners.set(type, [])
    })
  }

  public createAnimation(options: AnimationOptions): string {
    // Respect reduced motion preference
    if (this.reducedMotionEnabled && options.config.duration > 200) {
      options.config.duration = 200
      options.config.easing = 'ease-out'
    }

    // Check concurrent animation limit
    if (this.activeAnimations.size >= this.config.maxConcurrentAnimations) {
      this.cleanupCompletedAnimations()
      
      if (this.activeAnimations.size >= this.config.maxConcurrentAnimations) {
        console.warn('AnimationSystem: Maximum concurrent animations reached')
        return ''
      }
    }

    const element = options.element
    if (!element) {
      console.error('AnimationSystem: Element is required for animation')
      return ''
    }

    // Apply GPU acceleration if enabled
    if (this.config.enableGPUAcceleration && options.useGPU !== false) {
      this.enableGPUAcceleration(element)
    }

    // Create Web Animation
    const animation = element.animate(options.keyframes, {
      duration: options.config.duration,
      delay: options.config.delay || 0,
      easing: options.config.easing || 'ease-out',
      direction: options.config.direction || 'normal',
      fill: options.config.fillMode || 'forwards',
      iterations: options.config.iterations || 1
    })

    // Create animation instance
    const instance: AnimationInstance = {
      id: options.config.id,
      element,
      animation,
      config: options.config,
      startTime: performance.now(),
      isRunning: true,
      isPaused: false
    }

    // Store animation
    this.activeAnimations.set(options.config.id, instance)

    // Set up event handlers
    animation.addEventListener('finish', () => {
      this.handleAnimationComplete(instance)
    })

    animation.addEventListener('cancel', () => {
      this.handleAnimationCancel(instance)
    })

    // Emit start event
    this.emitEvent('start', {
      type: 'start',
      animationId: options.config.id,
      timestamp: performance.now(),
      element
    })

    // Call start callback
    if (options.config.onStart) {
      options.config.onStart()
    }

    return options.config.id
  }

  public pauseAnimation(id: string): boolean {
    const instance = this.activeAnimations.get(id)
    if (!instance || instance.isPaused) return false

    instance.animation.pause()
    instance.isPaused = true
    instance.isRunning = false

    this.emitEvent('pause', {
      type: 'pause',
      animationId: id,
      timestamp: performance.now(),
      element: instance.element
    })

    return true
  }

  public resumeAnimation(id: string): boolean {
    const instance = this.activeAnimations.get(id)
    if (!instance || !instance.isPaused) return false

    instance.animation.play()
    instance.isPaused = false
    instance.isRunning = true

    this.emitEvent('resume', {
      type: 'resume',
      animationId: id,
      timestamp: performance.now(),
      element: instance.element
    })

    return true
  }

  public cancelAnimation(id: string): boolean {
    const instance = this.activeAnimations.get(id)
    if (!instance) return false

    instance.animation.cancel()
    this.handleAnimationCancel(instance)
    return true
  }

  public cancelAllAnimations(): void {
    const animationIds = Array.from(this.activeAnimations.keys())
    animationIds.forEach(id => this.cancelAnimation(id))
  }

  public getActiveAnimationCount(): number {
    return this.activeAnimations.size
  }

  public getPerformanceMetrics(): PerformanceMetrics {
    return { ...this.performanceMetrics }
  }

  public addEventListener(type: AnimationEventType, listener: AnimationEventListener): void {
    const listeners = this.eventListeners.get(type) || []
    listeners.push(listener)
    this.eventListeners.set(type, listeners)
  }

  public removeEventListener(type: AnimationEventType, listener: AnimationEventListener): void {
    const listeners = this.eventListeners.get(type) || []
    const index = listeners.indexOf(listener)
    if (index > -1) {
      listeners.splice(index, 1)
    }
  }

  private enableGPUAcceleration(element: HTMLElement): void {
    element.style.willChange = 'transform, opacity'
    element.style.transform = element.style.transform || 'translateZ(0)'
  }

  private disableGPUAcceleration(element: HTMLElement): void {
    element.style.willChange = 'auto'
    if (element.style.transform === 'translateZ(0)') {
      element.style.transform = ''
    }
  }

  private handleAnimationComplete(instance: AnimationInstance): void {
    instance.isRunning = false
    
    // Disable GPU acceleration
    if (this.config.enableGPUAcceleration) {
      this.disableGPUAcceleration(instance.element)
    }

    // Emit complete event
    this.emitEvent('complete', {
      type: 'complete',
      animationId: instance.id,
      timestamp: performance.now(),
      element: instance.element
    })

    // Call complete callback
    if (instance.config.onComplete) {
      instance.config.onComplete()
    }

    // Remove from active animations
    this.activeAnimations.delete(instance.id)
  }

  private handleAnimationCancel(instance: AnimationInstance): void {
    instance.isRunning = false
    
    // Disable GPU acceleration
    if (this.config.enableGPUAcceleration) {
      this.disableGPUAcceleration(instance.element)
    }

    // Emit cancel event
    this.emitEvent('cancel', {
      type: 'cancel',
      animationId: instance.id,
      timestamp: performance.now(),
      element: instance.element
    })

    // Call cancel callback
    if (instance.config.onCancel) {
      instance.config.onCancel()
    }

    // Remove from active animations
    this.activeAnimations.delete(instance.id)
  }

  private emitEvent(type: AnimationEventType, event: AnimationEvent): void {
    const listeners = this.eventListeners.get(type) || []
    listeners.forEach(listener => {
      try {
        listener(event)
      } catch (error) {
        console.error(`AnimationSystem: Error in ${type} event listener:`, error)
      }
    })
  }

  private cleanupCompletedAnimations(): void {
    const completedAnimations: string[] = []
    
    this.activeAnimations.forEach((instance, id) => {
      if (!instance.isRunning && !instance.isPaused) {
        completedAnimations.push(id)
      }
    })

    completedAnimations.forEach(id => {
      this.activeAnimations.delete(id)
    })
  }

  private startPerformanceMonitoring(): void {
    const monitor = () => {
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
        
        // Update metrics
        this.performanceMetrics.fps = Math.round(avgFPS)
        this.performanceMetrics.activeAnimations = this.activeAnimations.size
        this.performanceMetrics.lastFrameTime = now
        
        // Detect frame drops
        if (currentFPS < this.config.targetFPS * 0.8) {
          this.performanceMetrics.frameDrops++
        }
        
        // Auto-optimize if performance is poor
        if (avgFPS < this.config.targetFPS * 0.6 && this.activeAnimations.size > 10) {
          this.optimizePerformance()
        }
      }
      
      this.lastFrameTime = now
      this.frameId = requestAnimationFrame(monitor)
    }
    
    this.frameId = requestAnimationFrame(monitor)
  }

  private optimizePerformance(): void {
    // Cancel low-priority animations if performance is poor
    const lowPriorityAnimations: string[] = []
    
    this.activeAnimations.forEach((instance, id) => {
      // Consider animations with long duration as low priority
      if (instance.config.duration > 1000) {
        lowPriorityAnimations.push(id)
      }
    })
    
    // Cancel up to half of low-priority animations
    const toCancel = lowPriorityAnimations.slice(0, Math.ceil(lowPriorityAnimations.length / 2))
    toCancel.forEach(id => this.cancelAnimation(id))
    
    if (this.config.debugMode) {
      console.log(`AnimationSystem: Optimized performance by canceling ${toCancel.length} animations`)
    }
  }

  public destroy(): void {
    // Cancel all animations
    this.cancelAllAnimations()
    
    // Stop performance monitoring
    if (this.frameId) {
      cancelAnimationFrame(this.frameId)
      this.frameId = null
    }
    
    // Clear event listeners
    this.eventListeners.clear()
    
    // Reset instance
    AnimationSystem.instance = null as any
  }
}

export default AnimationSystem