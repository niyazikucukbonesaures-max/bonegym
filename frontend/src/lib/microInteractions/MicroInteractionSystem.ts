/**
 * Micro-Interaction System
 * Provides visual feedback for user interactions
 */

import AnimationSystem from '@/lib/animation/AnimationSystem'
import { ANIMATION_PRESETS, createAnimationFromPreset } from '@/lib/animation/presets'
import { MicroInteractionConfig } from '@/lib/animation/types'

export type MicroInteractionType = 
  | 'hover' 
  | 'focus' 
  | 'click' 
  | 'success' 
  | 'error' 
  | 'loading'
  | 'add'
  | 'remove'
  | 'validate'

export interface MicroInteractionOptions {
  type: MicroInteractionType
  element: HTMLElement
  intensity?: 'subtle' | 'medium' | 'strong'
  duration?: number
  useHaptic?: boolean
  onComplete?: () => void
}

export interface InteractionState {
  isHovered: boolean
  isFocused: boolean
  isPressed: boolean
  isLoading: boolean
  hasError: boolean
  isSuccess: boolean
}

class MicroInteractionSystem {
  private static instance: MicroInteractionSystem
  private animationSystem: AnimationSystem
  private activeInteractions: Map<HTMLElement, Set<string>> = new Map()
  private elementStates: Map<HTMLElement, InteractionState> = new Map()

  private constructor() {
    this.animationSystem = AnimationSystem.getInstance()
  }

  public static getInstance(): MicroInteractionSystem {
    if (!MicroInteractionSystem.instance) {
      MicroInteractionSystem.instance = new MicroInteractionSystem()
    }
    return MicroInteractionSystem.instance
  }

  public trigger(options: MicroInteractionOptions): string {
    const { type, element, intensity = 'medium', duration, useHaptic = false, onComplete } = options

    // Update element state
    this.updateElementState(element, type, true)

    // Get animation configuration based on type and intensity
    const animationConfig = this.getAnimationConfig(type, intensity, duration)
    
    if (!animationConfig) {
      console.warn(`MicroInteractionSystem: No animation config found for type: ${type}`)
      return ''
    }

    // Create animation
    const animationOptions = createAnimationFromPreset(
      animationConfig.preset as keyof typeof ANIMATION_PRESETS,
      element,
      {
        duration: animationConfig.duration,
        easing: animationConfig.easing,
        onComplete: () => {
          this.updateElementState(element, type, false)
          if (onComplete) onComplete()
        }
      }
    )

    const animationId = this.animationSystem.createAnimation(animationOptions)

    // Track active interaction
    this.trackInteraction(element, animationId)

    // Trigger haptic feedback if enabled and supported
    if (useHaptic && this.isHapticSupported()) {
      this.triggerHapticFeedback(type, intensity)
    }

    return animationId
  }

  public hover(element: HTMLElement, intensity: 'subtle' | 'medium' | 'strong' = 'medium'): string {
    return this.trigger({ type: 'hover', element, intensity })
  }

  public focus(element: HTMLElement, intensity: 'subtle' | 'medium' | 'strong' = 'medium'): string {
    return this.trigger({ type: 'focus', element, intensity })
  }

  public click(element: HTMLElement, intensity: 'subtle' | 'medium' | 'strong' = 'medium'): string {
    return this.trigger({ type: 'click', element, intensity, useHaptic: true })
  }

  public success(element: HTMLElement, intensity: 'subtle' | 'medium' | 'strong' = 'strong'): string {
    return this.trigger({ type: 'success', element, intensity, useHaptic: true })
  }

  public error(element: HTMLElement, intensity: 'subtle' | 'medium' | 'strong' = 'strong'): string {
    return this.trigger({ type: 'error', element, intensity, useHaptic: true })
  }

  public loading(element: HTMLElement): string {
    return this.trigger({ type: 'loading', element, intensity: 'medium' })
  }

  public add(element: HTMLElement, intensity: 'subtle' | 'medium' | 'strong' = 'medium'): string {
    return this.trigger({ type: 'add', element, intensity })
  }

  public remove(element: HTMLElement, intensity: 'subtle' | 'medium' | 'strong' = 'medium'): string {
    return this.trigger({ type: 'remove', element, intensity })
  }

  public validate(element: HTMLElement, isValid: boolean): string {
    return this.trigger({ 
      type: isValid ? 'success' : 'error', 
      element, 
      intensity: 'medium' 
    })
  }

  public getElementState(element: HTMLElement): InteractionState {
    return this.elementStates.get(element) || {
      isHovered: false,
      isFocused: false,
      isPressed: false,
      isLoading: false,
      hasError: false,
      isSuccess: false
    }
  }

  public clearElementInteractions(element: HTMLElement): void {
    const interactions = this.activeInteractions.get(element)
    if (interactions) {
      interactions.forEach(animationId => {
        this.animationSystem.cancelAnimation(animationId)
      })
      this.activeInteractions.delete(element)
    }
    this.elementStates.delete(element)
  }

  private getAnimationConfig(
    type: MicroInteractionType, 
    intensity: 'subtle' | 'medium' | 'strong',
    customDuration?: number
  ) {
    const configs = {
      hover: {
        preset: intensity === 'subtle' ? 'CARD_HOVER' : 'BUTTON_HOVER',
        duration: customDuration || (intensity === 'subtle' ? 150 : intensity === 'medium' ? 200 : 250),
        easing: 'ease-out'
      },
      focus: {
        preset: 'INPUT_FOCUS',
        duration: customDuration || (intensity === 'subtle' ? 150 : intensity === 'medium' ? 200 : 250),
        easing: 'ease-out'
      },
      click: {
        preset: 'BUTTON_PRESS',
        duration: customDuration || (intensity === 'subtle' ? 100 : intensity === 'medium' ? 150 : 200),
        easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
      },
      success: {
        preset: 'SUCCESS_BOUNCE',
        duration: customDuration || (intensity === 'subtle' ? 400 : intensity === 'medium' ? 600 : 800),
        easing: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
      },
      error: {
        preset: 'ERROR_SHAKE',
        duration: customDuration || (intensity === 'subtle' ? 300 : intensity === 'medium' ? 500 : 700),
        easing: 'ease-in-out'
      },
      loading: {
        preset: 'PULSE',
        duration: customDuration || 2000,
        easing: 'ease-in-out'
      },
      add: {
        preset: 'SUCCESS_BOUNCE',
        duration: customDuration || (intensity === 'subtle' ? 300 : intensity === 'medium' ? 400 : 500),
        easing: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
      },
      remove: {
        preset: 'TOAST_SLIDE_OUT',
        duration: customDuration || (intensity === 'subtle' ? 200 : intensity === 'medium' ? 300 : 400),
        easing: 'ease-in'
      },
      validate: {
        preset: 'INPUT_SUCCESS',
        duration: customDuration || 300,
        easing: 'ease-out'
      }
    }

    return configs[type] || null
  }

  private updateElementState(element: HTMLElement, type: MicroInteractionType, isActive: boolean): void {
    const currentState = this.getElementState(element)
    const newState = { ...currentState }

    switch (type) {
      case 'hover':
        newState.isHovered = isActive
        break
      case 'focus':
        newState.isFocused = isActive
        break
      case 'click':
        newState.isPressed = isActive
        break
      case 'loading':
        newState.isLoading = isActive
        break
      case 'error':
        newState.hasError = isActive
        newState.isSuccess = false
        break
      case 'success':
        newState.isSuccess = isActive
        newState.hasError = false
        break
    }

    this.elementStates.set(element, newState)
  }

  private trackInteraction(element: HTMLElement, animationId: string): void {
    if (!this.activeInteractions.has(element)) {
      this.activeInteractions.set(element, new Set())
    }
    this.activeInteractions.get(element)!.add(animationId)

    // Clean up when animation completes
    this.animationSystem.addEventListener('complete', (event) => {
      if (event.animationId === animationId) {
        const interactions = this.activeInteractions.get(element)
        if (interactions) {
          interactions.delete(animationId)
          if (interactions.size === 0) {
            this.activeInteractions.delete(element)
          }
        }
      }
    })
  }

  private isHapticSupported(): boolean {
    return 'vibrate' in navigator
  }

  private triggerHapticFeedback(type: MicroInteractionType, intensity: 'subtle' | 'medium' | 'strong'): void {
    if (!this.isHapticSupported()) return

    const patterns = {
      subtle: {
        click: [10],
        success: [20, 10, 20],
        error: [50, 30, 50, 30, 50],
        hover: [5],
        focus: [8],
        loading: [15],
        add: [15, 10, 15],
        remove: [30],
        validate: [12]
      },
      medium: {
        click: [15],
        success: [30, 15, 30],
        error: [70, 40, 70, 40, 70],
        hover: [8],
        focus: [12],
        loading: [20],
        add: [20, 15, 20],
        remove: [40],
        validate: [18]
      },
      strong: {
        click: [25],
        success: [50, 25, 50],
        error: [100, 50, 100, 50, 100],
        hover: [12],
        focus: [18],
        loading: [30],
        add: [30, 20, 30],
        remove: [60],
        validate: [25]
      }
    }

    const pattern = patterns[intensity][type]
    if (pattern) {
      navigator.vibrate(pattern)
    }
  }

  public destroy(): void {
    // Cancel all active interactions
    this.activeInteractions.forEach((interactions, element) => {
      interactions.forEach(animationId => {
        this.animationSystem.cancelAnimation(animationId)
      })
    })

    // Clear all data
    this.activeInteractions.clear()
    this.elementStates.clear()

    // Reset instance
    MicroInteractionSystem.instance = null as any
  }
}

export default MicroInteractionSystem