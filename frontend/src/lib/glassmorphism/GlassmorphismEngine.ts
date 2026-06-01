/**
 * Glassmorphism Engine
 * Advanced glassmorphism effects with dynamic blur and contrast management
 */

import { GlassmorphismConfig } from '@/lib/animation/types'

export interface GlassElement {
  element: HTMLElement
  config: GlassmorphismConfig
  observer?: IntersectionObserver
  resizeObserver?: ResizeObserver
}

export interface BackgroundAnalysis {
  averageBrightness: number
  dominantColor: string
  contrast: number
  hasComplexBackground: boolean
}

export interface GlassTheme {
  name: string
  blur: number
  opacity: number
  borderOpacity: number
  shadowIntensity: number
  backgroundTint: string
}

class GlassmorphismEngine {
  private static instance: GlassmorphismEngine
  private glassElements: Map<HTMLElement, GlassElement> = new Map()
  private currentTheme: 'light' | 'dark' = 'dark'
  private performanceMode: 'high' | 'medium' | 'low' = 'high'
  private canvas: HTMLCanvasElement
  private ctx: CanvasRenderingContext2D

  // Predefined themes
  private themes: Record<string, GlassTheme> = {
    'dark-subtle': {
      name: 'Dark Subtle',
      blur: 8,
      opacity: 0.1,
      borderOpacity: 0.2,
      shadowIntensity: 0.3,
      backgroundTint: 'rgba(255, 255, 255, 0.05)'
    },
    'dark-medium': {
      name: 'Dark Medium',
      blur: 12,
      opacity: 0.15,
      borderOpacity: 0.25,
      shadowIntensity: 0.4,
      backgroundTint: 'rgba(255, 255, 255, 0.08)'
    },
    'dark-strong': {
      name: 'Dark Strong',
      blur: 16,
      opacity: 0.2,
      borderOpacity: 0.3,
      shadowIntensity: 0.5,
      backgroundTint: 'rgba(255, 255, 255, 0.12)'
    },
    'light-subtle': {
      name: 'Light Subtle',
      blur: 8,
      opacity: 0.15,
      borderOpacity: 0.3,
      shadowIntensity: 0.2,
      backgroundTint: 'rgba(0, 0, 0, 0.05)'
    },
    'light-medium': {
      name: 'Light Medium',
      blur: 12,
      opacity: 0.2,
      borderOpacity: 0.35,
      shadowIntensity: 0.3,
      backgroundTint: 'rgba(0, 0, 0, 0.08)'
    },
    'light-strong': {
      name: 'Light Strong',
      blur: 16,
      opacity: 0.25,
      borderOpacity: 0.4,
      shadowIntensity: 0.4,
      backgroundTint: 'rgba(0, 0, 0, 0.12)'
    }
  }

  private constructor() {
    this.canvas = document.createElement('canvas')
    this.ctx = this.canvas.getContext('2d')!
    this.detectTheme()
    this.detectPerformanceMode()
    this.setupThemeListener()
  }

  public static getInstance(): GlassmorphismEngine {
    if (!GlassmorphismEngine.instance) {
      GlassmorphismEngine.instance = new GlassmorphismEngine()
    }
    return GlassmorphismEngine.instance
  }

  public applyGlass(element: HTMLElement, config: Partial<GlassmorphismConfig> = {}): void {
    const finalConfig: GlassmorphismConfig = {
      blur: 12,
      opacity: 0.1,
      borderOpacity: 0.2,
      shadowIntensity: 0.3,
      adaptToBackground: true,
      useGPU: true,
      ...config
    }

    // Analyze background if adaptation is enabled
    if (finalConfig.adaptToBackground) {
      this.adaptToBackground(element, finalConfig)
    }

    // Apply glassmorphism styles
    this.applyStyles(element, finalConfig)

    // Create glass element entry
    const glassElement: GlassElement = {
      element,
      config: finalConfig
    }

    // Set up observers for dynamic adaptation
    if (finalConfig.adaptToBackground) {
      this.setupObservers(glassElement)
    }

    // Enable GPU acceleration if requested
    if (finalConfig.useGPU) {
      this.enableGPUAcceleration(element)
    }

    // Store element
    this.glassElements.set(element, glassElement)
  }

  public updateGlass(element: HTMLElement, config: Partial<GlassmorphismConfig>): void {
    const glassElement = this.glassElements.get(element)
    if (!glassElement) return

    // Update config
    glassElement.config = { ...glassElement.config, ...config }

    // Re-apply styles
    this.applyStyles(element, glassElement.config)
  }

  public removeGlass(element: HTMLElement): void {
    const glassElement = this.glassElements.get(element)
    if (!glassElement) return

    // Clean up observers
    if (glassElement.observer) {
      glassElement.observer.disconnect()
    }
    if (glassElement.resizeObserver) {
      glassElement.resizeObserver.disconnect()
    }

    // Remove styles
    this.removeStyles(element)

    // Remove from map
    this.glassElements.delete(element)
  }

  public setTheme(theme: 'light' | 'dark'): void {
    this.currentTheme = theme
    this.updateAllElements()
  }

  public setPerformanceMode(mode: 'high' | 'medium' | 'low'): void {
    this.performanceMode = mode
    this.updateAllElements()
  }

  public getTheme(intensity: 'subtle' | 'medium' | 'strong' = 'medium'): GlassTheme {
    const themeKey = `${this.currentTheme}-${intensity}`
    return this.themes[themeKey] || this.themes[`${this.currentTheme}-medium`]
  }

  private applyStyles(element: HTMLElement, config: GlassmorphismConfig): void {
    const theme = this.getTheme()
    
    // Adjust values based on performance mode
    const adjustedBlur = this.adjustForPerformance(config.blur)
    const adjustedOpacity = config.opacity
    const adjustedBorderOpacity = config.borderOpacity
    const adjustedShadowIntensity = config.shadowIntensity

    // Apply backdrop filter
    element.style.backdropFilter = `blur(${adjustedBlur}px)`
    (element.style as any).webkitBackdropFilter = `blur(${adjustedBlur}px)` // Safari support

    // Apply background with opacity
    const backgroundTint = this.currentTheme === 'dark' 
      ? `rgba(255, 255, 255, ${adjustedOpacity})`
      : `rgba(0, 0, 0, ${adjustedOpacity})`
    
    element.style.backgroundColor = backgroundTint

    // Apply border
    const borderColor = this.currentTheme === 'dark'
      ? `rgba(255, 255, 255, ${adjustedBorderOpacity})`
      : `rgba(0, 0, 0, ${adjustedBorderOpacity})`
    
    element.style.border = `1px solid ${borderColor}`

    // Apply shadow
    const shadowColor = this.currentTheme === 'dark'
      ? `rgba(0, 0, 0, ${adjustedShadowIntensity})`
      : `rgba(0, 0, 0, ${adjustedShadowIntensity * 0.5})`
    
    element.style.boxShadow = `0 8px 32px ${shadowColor}`

    // Ensure proper border radius
    if (!element.style.borderRadius) {
      element.style.borderRadius = '16px'
    }

    // Add transition for smooth changes
    element.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
  }

  private adaptToBackground(element: HTMLElement, config: GlassmorphismConfig): void {
    const analysis = this.analyzeBackground(element)
    
    // Adjust blur based on background complexity
    if (analysis.hasComplexBackground) {
      config.blur = Math.max(config.blur * 1.5, 16)
    }

    // Adjust opacity based on brightness
    if (analysis.averageBrightness > 0.7) {
      // Bright background - increase opacity for better visibility
      config.opacity = Math.min(config.opacity * 1.3, 0.3)
      config.borderOpacity = Math.min(config.borderOpacity * 1.2, 0.4)
    } else if (analysis.averageBrightness < 0.3) {
      // Dark background - decrease opacity
      config.opacity = Math.max(config.opacity * 0.8, 0.05)
      config.borderOpacity = Math.max(config.borderOpacity * 0.9, 0.1)
    }

    // Adjust shadow based on contrast
    if (analysis.contrast < 0.3) {
      config.shadowIntensity = Math.min(config.shadowIntensity * 1.5, 0.6)
    }
  }

  private analyzeBackground(element: HTMLElement): BackgroundAnalysis {
    const rect = element.getBoundingClientRect()
    const parentElement = element.parentElement || document.body

    // Set canvas size
    this.canvas.width = Math.min(rect.width, 200)
    this.canvas.height = Math.min(rect.height, 200)

    // Try to capture background
    try {
      // This is a simplified analysis - in a real implementation,
      // you might use more sophisticated background detection
      const computedStyle = window.getComputedStyle(parentElement)
      const backgroundColor = computedStyle.backgroundColor
      const backgroundImage = computedStyle.backgroundImage

      // Analyze background color
      const brightness = this.calculateBrightness(backgroundColor)
      const hasComplexBackground = backgroundImage !== 'none'

      return {
        averageBrightness: brightness,
        dominantColor: backgroundColor,
        contrast: brightness > 0.5 ? 1 - brightness : brightness,
        hasComplexBackground
      }
    } catch (error) {
      // Fallback analysis
      return {
        averageBrightness: 0.5,
        dominantColor: 'rgba(0, 0, 0, 0)',
        contrast: 0.5,
        hasComplexBackground: false
      }
    }
  }

  private calculateBrightness(color: string): number {
    // Parse RGB values from color string
    const rgb = color.match(/\d+/g)
    if (!rgb || rgb.length < 3) return 0.5

    const r = parseInt(rgb[0]) / 255
    const g = parseInt(rgb[1]) / 255
    const b = parseInt(rgb[2]) / 255

    // Calculate relative luminance
    return 0.299 * r + 0.587 * g + 0.114 * b
  }

  private setupObservers(glassElement: GlassElement): void {
    const { element, config } = glassElement

    // Intersection observer for visibility changes
    glassElement.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          // Re-analyze background when element becomes visible
          this.adaptToBackground(element, config)
          this.applyStyles(element, config)
        }
      })
    })

    glassElement.observer.observe(element)

    // Resize observer for size changes
    glassElement.resizeObserver = new ResizeObserver(() => {
      // Re-analyze background when element size changes
      this.adaptToBackground(element, config)
      this.applyStyles(element, config)
    })

    glassElement.resizeObserver.observe(element)
  }

  private enableGPUAcceleration(element: HTMLElement): void {
    element.style.willChange = 'backdrop-filter, background-color, border-color, box-shadow'
    element.style.transform = element.style.transform || 'translateZ(0)'
  }

  private removeStyles(element: HTMLElement): void {
    element.style.backdropFilter = ''
    (element.style as any).webkitBackdropFilter = ''
    element.style.backgroundColor = ''
    element.style.border = ''
    element.style.boxShadow = ''
    element.style.willChange = ''
    
    // Only remove transform if it was just for GPU acceleration
    if (element.style.transform === 'translateZ(0)') {
      element.style.transform = ''
    }
  }

  private detectTheme(): void {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    this.currentTheme = prefersDark ? 'dark' : 'light'
  }

  private detectPerformanceMode(): void {
    // Detect device performance capabilities
    const connection = (navigator as any).connection
    const hardwareConcurrency = navigator.hardwareConcurrency || 4
    const memory = (performance as any).memory?.usedJSHeapSize || 0

    if (connection?.effectiveType === '4g' && hardwareConcurrency >= 8) {
      this.performanceMode = 'high'
    } else if (connection?.effectiveType === '3g' || hardwareConcurrency >= 4) {
      this.performanceMode = 'medium'
    } else {
      this.performanceMode = 'low'
    }
  }

  private adjustForPerformance(value: number): number {
    switch (this.performanceMode) {
      case 'low':
        return Math.max(value * 0.5, 4) // Minimum 4px blur
      case 'medium':
        return Math.max(value * 0.75, 6) // Minimum 6px blur
      case 'high':
      default:
        return value
    }
  }

  private setupThemeListener(): void {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      this.currentTheme = e.matches ? 'dark' : 'light'
      this.updateAllElements()
    })
  }

  private updateAllElements(): void {
    this.glassElements.forEach((glassElement, element) => {
      if (glassElement.config.adaptToBackground) {
        this.adaptToBackground(element, glassElement.config)
      }
      this.applyStyles(element, glassElement.config)
    })
  }

  public destroy(): void {
    // Clean up all elements
    this.glassElements.forEach((glassElement, element) => {
      this.removeGlass(element)
    })

    // Clear canvas
    this.canvas.remove()

    // Reset instance
    GlassmorphismEngine.instance = null as any
  }
}

export default GlassmorphismEngine
