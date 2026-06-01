/**
 * Animation Error Handler
 * Handles animation-related errors and provides fallback mechanisms
 */

import { AnimationOptions } from '@/lib/animation/types'

export interface AnimationError extends Error {
  animationId?: string
  element?: HTMLElement
  options?: AnimationOptions
  fallbackApplied?: boolean
}

export class AnimationErrorHandler {
  private static instance: AnimationErrorHandler
  private errorCount = 0
  private maxErrors = 10
  private fallbackMode = false
  private errorCallbacks: ((error: AnimationError) => void)[] = []

  private constructor() {}

  static getInstance(): AnimationErrorHandler {
    if (!AnimationErrorHandler.instance) {
      AnimationErrorHandler.instance = new AnimationErrorHandler()
    }
    return AnimationErrorHandler.instance
  }

  /**
   * Handle animation errors with automatic fallback
   */
  handleError(error: AnimationError): void {
    this.errorCount++
    
    console.warn('Animation error occurred:', {
      message: error.message,
      animationId: error.animationId,
      element: error.element,
      errorCount: this.errorCount
    })

    // Apply fallback if error threshold reached
    if (this.errorCount >= this.maxErrors && !this.fallbackMode) {
      this.enableFallbackMode()
    }

    // Try to apply CSS fallback for the specific animation
    if (error.element && error.options) {
      this.applyCSSFallback(error.element, error.options)
      error.fallbackApplied = true
    }

    // Notify error callbacks
    this.errorCallbacks.forEach(callback => {
      try {
        callback(error)
      } catch (callbackError) {
        console.error('Error in animation error callback:', callbackError)
      }
    })
  }

  /**
   * Enable fallback mode - use CSS animations instead of JS
   */
  private enableFallbackMode(): void {
    this.fallbackMode = true
    console.warn('Animation fallback mode enabled due to repeated errors')
    
    // Add CSS class to document to enable CSS-only animations
    document.documentElement.classList.add('animation-fallback-mode')
    
    // Disable will-change properties to reduce GPU usage
    const style = document.createElement('style')
    style.textContent = `
      .animation-fallback-mode * {
        will-change: auto !important;
      }
      .animation-fallback-mode .gpu-accelerated {
        transform: none !important;
      }
    `
    document.head.appendChild(style)
  }

  /**
   * Apply CSS fallback animation
   */
  private applyCSSFallback(element: HTMLElement, options: AnimationOptions): void {
    try {
      // Remove any existing animation classes
      element.classList.remove(
        'animate-fade-in-up',
        'animate-fade-in-down',
        'animate-scale-in',
        'animate-bounce-in'
      )

      // Apply appropriate CSS animation based on options
      const animationType = this.getCSSAnimationType(options)
      if (animationType) {
        element.classList.add(animationType)
        
        // Remove class after animation completes
        setTimeout(() => {
          element.classList.remove(animationType)
        }, options.duration || 300)
      }
    } catch (fallbackError) {
      console.error('Failed to apply CSS fallback:', fallbackError)
    }
  }

  /**
   * Get appropriate CSS animation class based on options
   */
  private getCSSAnimationType(options: AnimationOptions): string | null {
    const { keyframes } = options

    if (!keyframes || keyframes.length === 0) {
      return 'animate-fade-in-up'
    }

    // Analyze keyframes to determine animation type
    const firstFrame = keyframes[0]
    const lastFrame = keyframes[keyframes.length - 1]

    // Check for scale animation
    if (firstFrame.transform?.includes('scale') || lastFrame.transform?.includes('scale')) {
      return 'animate-scale-in'
    }

    // Check for translate animation
    if (firstFrame.transform?.includes('translateY') || lastFrame.transform?.includes('translateY')) {
      const translateMatch = lastFrame.transform?.match(/translateY\(([^)]+)\)/)
      if (translateMatch) {
        const value = parseFloat(translateMatch[1])
        return value < 0 ? 'animate-fade-in-up' : 'animate-fade-in-down'
      }
    }

    // Check for opacity animation
    if (firstFrame.opacity !== undefined || lastFrame.opacity !== undefined) {
      return 'animate-fade-in-up'
    }

    return 'animate-fade-in-up'
  }

  /**
   * Check if fallback mode is enabled
   */
  isFallbackMode(): boolean {
    return this.fallbackMode
  }

  /**
   * Reset error count and disable fallback mode
   */
  reset(): void {
    this.errorCount = 0
    this.fallbackMode = false
    document.documentElement.classList.remove('animation-fallback-mode')
  }

  /**
   * Add error callback
   */
  onError(callback: (error: AnimationError) => void): void {
    this.errorCallbacks.push(callback)
  }

  /**
   * Remove error callback
   */
  offError(callback: (error: AnimationError) => void): void {
    const index = this.errorCallbacks.indexOf(callback)
    if (index > -1) {
      this.errorCallbacks.splice(index, 1)
    }
  }

  /**
   * Create animation error
   */
  createError(
    message: string,
    animationId?: string,
    element?: HTMLElement,
    options?: AnimationOptions
  ): AnimationError {
    const error = new Error(message) as AnimationError
    error.name = 'AnimationError'
    error.animationId = animationId
    error.element = element
    error.options = options
    error.fallbackApplied = false
    return error
  }

  /**
   * Validate animation options
   */
  validateOptions(options: AnimationOptions): string[] {
    const errors: string[] = []

    if (!options.element) {
      errors.push('Animation element is required')
    }

    if (!options.keyframes || options.keyframes.length === 0) {
      errors.push('Animation keyframes are required')
    }

    if (options.config?.duration && (options.config.duration < 0 || options.config.duration > 10000)) {
      errors.push('Animation duration must be between 0 and 10000ms')
    }

    if (options.config?.delay && options.config.delay < 0) {
      errors.push('Animation delay cannot be negative')
    }

    return errors
  }

  /**
   * Safe animation execution with error handling
   */
  safeAnimate(
    element: HTMLElement,
    keyframes: Keyframe[],
    options: KeyframeAnimationOptions
  ): Animation | null {
    try {
      // Validate element
      if (!element || !element.isConnected) {
        throw this.createError('Element is not connected to DOM')
      }

      // Validate keyframes
      if (!keyframes || keyframes.length === 0) {
        throw this.createError('Invalid keyframes provided')
      }

      // Create animation with error handling
      const animation = element.animate(keyframes, options)
      
      // Handle animation errors
      animation.addEventListener('error', (event) => {
        const error = this.createError(
          'Animation playback error',
          animation.id,
          element
        )
        this.handleError(error)
      })

      return animation
    } catch (error) {
      const animationError = this.createError(
        `Animation creation failed: ${(error as Error).message}`,
        undefined,
        element
      )
      this.handleError(animationError)
      return null
    }
  }

  /**
   * Get error statistics
   */
  getStats() {
    return {
      errorCount: this.errorCount,
      fallbackMode: this.fallbackMode,
      maxErrors: this.maxErrors
    }
  }
}

export default AnimationErrorHandler