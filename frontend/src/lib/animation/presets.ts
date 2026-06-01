/**
 * Animation Presets
 * Pre-defined animation configurations for common UI interactions
 */

import { AnimationOptions, AnimationKeyframe } from './types'

export const ANIMATION_PRESETS = {
  // Button interactions
  BUTTON_PRESS: {
    keyframes: [
      { offset: 0, transform: 'scale(1)' },
      { offset: 0.5, transform: 'scale(0.95)' },
      { offset: 1, transform: 'scale(1)' }
    ] as AnimationKeyframe[],
    duration: 150,
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
  },

  BUTTON_HOVER: {
    keyframes: [
      { offset: 0, transform: 'scale(1)', boxShadow: '0 0 0 rgba(139, 92, 246, 0)' },
      { offset: 1, transform: 'scale(1.02)', boxShadow: '0 8px 25px rgba(139, 92, 246, 0.3)' }
    ] as AnimationKeyframe[],
    duration: 200,
    easing: 'ease-out'
  },

  // Card animations
  CARD_FADE_IN: {
    keyframes: [
      { offset: 0, opacity: 0, transform: 'translateY(20px)' },
      { offset: 1, opacity: 1, transform: 'translateY(0)' }
    ] as AnimationKeyframe[],
    duration: 300,
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
  },

  CARD_HOVER: {
    keyframes: [
      { offset: 0, transform: 'translateY(0) scale(1)' },
      { offset: 1, transform: 'translateY(-4px) scale(1.01)' }
    ] as AnimationKeyframe[],
    duration: 200,
    easing: 'ease-out'
  },

  // Form interactions
  INPUT_FOCUS: {
    keyframes: [
      { offset: 0, borderColor: 'rgba(255, 255, 255, 0.2)', boxShadow: '0 0 0 0 rgba(139, 92, 246, 0)' },
      { offset: 1, borderColor: 'rgba(139, 92, 246, 1)', boxShadow: '0 0 0 3px rgba(139, 92, 246, 0.2)' }
    ] as AnimationKeyframe[],
    duration: 200,
    easing: 'ease-out'
  },

  INPUT_ERROR: {
    keyframes: [
      { offset: 0, transform: 'translateX(0)', borderColor: 'rgba(239, 68, 68, 1)' },
      { offset: 0.25, transform: 'translateX(-5px)' },
      { offset: 0.75, transform: 'translateX(5px)' },
      { offset: 1, transform: 'translateX(0)' }
    ] as AnimationKeyframe[],
    duration: 400,
    easing: 'ease-in-out'
  },

  INPUT_SUCCESS: {
    keyframes: [
      { offset: 0, borderColor: 'rgba(255, 255, 255, 0.2)' },
      { offset: 0.5, borderColor: 'rgba(34, 197, 94, 1)', boxShadow: '0 0 0 3px rgba(34, 197, 94, 0.2)' },
      { offset: 1, borderColor: 'rgba(34, 197, 94, 1)' }
    ] as AnimationKeyframe[],
    duration: 300,
    easing: 'ease-out'
  },

  // Loading animations
  SKELETON_SHIMMER: {
    keyframes: [
      { offset: 0, backgroundPosition: '-200px 0' },
      { offset: 1, backgroundPosition: 'calc(200px + 100%) 0' }
    ] as AnimationKeyframe[],
    duration: 2000,
    easing: 'ease-in-out',
    iterations: 'infinite' as const
  },

  SPINNER_ROTATE: {
    keyframes: [
      { offset: 0, transform: 'rotate(0deg)' },
      { offset: 1, transform: 'rotate(360deg)' }
    ] as AnimationKeyframe[],
    duration: 1000,
    easing: 'linear',
    iterations: 'infinite' as const
  },

  PULSE: {
    keyframes: [
      { offset: 0, opacity: 1, transform: 'scale(1)' },
      { offset: 0.5, opacity: 0.7, transform: 'scale(1.05)' },
      { offset: 1, opacity: 1, transform: 'scale(1)' }
    ] as AnimationKeyframe[],
    duration: 2000,
    easing: 'ease-in-out',
    iterations: 'infinite' as const
  },

  // Notification animations
  TOAST_SLIDE_IN: {
    keyframes: [
      { offset: 0, transform: 'translateX(100%)', opacity: 0 },
      { offset: 1, transform: 'translateX(0)', opacity: 1 }
    ] as AnimationKeyframe[],
    duration: 300,
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
  },

  TOAST_SLIDE_OUT: {
    keyframes: [
      { offset: 0, transform: 'translateX(0)', opacity: 1 },
      { offset: 1, transform: 'translateX(100%)', opacity: 0 }
    ] as AnimationKeyframe[],
    duration: 200,
    easing: 'ease-in'
  },

  // Success/Error feedback
  SUCCESS_BOUNCE: {
    keyframes: [
      { offset: 0, transform: 'scale(1)' },
      { offset: 0.3, transform: 'scale(1.2)' },
      { offset: 0.6, transform: 'scale(0.9)' },
      { offset: 1, transform: 'scale(1)' }
    ] as AnimationKeyframe[],
    duration: 600,
    easing: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
  },

  ERROR_SHAKE: {
    keyframes: [
      { offset: 0, transform: 'translateX(0)' },
      { offset: 0.1, transform: 'translateX(-10px)' },
      { offset: 0.2, transform: 'translateX(10px)' },
      { offset: 0.3, transform: 'translateX(-10px)' },
      { offset: 0.4, transform: 'translateX(10px)' },
      { offset: 0.5, transform: 'translateX(-5px)' },
      { offset: 0.6, transform: 'translateX(5px)' },
      { offset: 0.7, transform: 'translateX(-5px)' },
      { offset: 0.8, transform: 'translateX(5px)' },
      { offset: 1, transform: 'translateX(0)' }
    ] as AnimationKeyframe[],
    duration: 500,
    easing: 'ease-in-out'
  },

  // Page transitions
  PAGE_FADE_IN: {
    keyframes: [
      { offset: 0, opacity: 0, transform: 'translateY(10px)' },
      { offset: 1, opacity: 1, transform: 'translateY(0)' }
    ] as AnimationKeyframe[],
    duration: 400,
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
  },

  PAGE_SLIDE_LEFT: {
    keyframes: [
      { offset: 0, transform: 'translateX(100%)' },
      { offset: 1, transform: 'translateX(0)' }
    ] as AnimationKeyframe[],
    duration: 300,
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
  },

  // Staggered animations
  STAGGER_FADE_IN: (delay: number) => ({
    keyframes: [
      { offset: 0, opacity: 0, transform: 'translateY(20px)' },
      { offset: 1, opacity: 1, transform: 'translateY(0)' }
    ] as AnimationKeyframe[],
    duration: 300,
    delay: delay * 100,
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
  }),

  // Glassmorphism effects
  GLASS_HOVER: {
    keyframes: [
      { 
        offset: 0, 
        backdropFilter: 'blur(10px)',
        borderColor: 'rgba(255, 255, 255, 0.2)'
      },
      { 
        offset: 1, 
        backdropFilter: 'blur(15px)',
        borderColor: 'rgba(255, 255, 255, 0.3)'
      }
    ] as AnimationKeyframe[],
    duration: 200,
    easing: 'ease-out'
  },

  // Achievement animations
  ACHIEVEMENT_GLOW: {
    keyframes: [
      { 
        offset: 0, 
        boxShadow: '0 0 20px rgba(255, 215, 0, 0.3)',
        transform: 'scale(1)'
      },
      { 
        offset: 0.5, 
        boxShadow: '0 0 40px rgba(255, 215, 0, 0.6)',
        transform: 'scale(1.05)'
      },
      { 
        offset: 1, 
        boxShadow: '0 0 20px rgba(255, 215, 0, 0.3)',
        transform: 'scale(1)'
      }
    ] as AnimationKeyframe[],
    duration: 2000,
    easing: 'ease-in-out',
    iterations: 'infinite' as const
  }
}

// Helper function to create animation options from presets
export function createAnimationFromPreset(
  presetName: keyof typeof ANIMATION_PRESETS,
  element: HTMLElement,
  customConfig: Partial<AnimationOptions['config']> = {}
): AnimationOptions {
  const preset = ANIMATION_PRESETS[presetName]
  
  if (typeof preset === 'function') {
    throw new Error(`Preset ${presetName} requires parameters. Use createStaggeredAnimation instead.`)
  }

  return {
    keyframes: preset.keyframes,
    config: {
      id: `${presetName}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      duration: preset.duration,
      easing: preset.easing,
      iterations: preset.iterations || 1,
      ...customConfig
    },
    element,
    useGPU: true,
    respectReducedMotion: true
  }
}

// Helper for staggered animations
export function createStaggeredAnimation(
  elements: HTMLElement[],
  baseDelay: number = 100
): AnimationOptions[] {
  return elements.map((element, index) => {
    const preset = ANIMATION_PRESETS.STAGGER_FADE_IN(index)
    return {
      keyframes: preset.keyframes,
      config: {
        id: `stagger-${index}-${Date.now()}`,
        duration: preset.duration,
        delay: preset.delay,
        easing: preset.easing
      },
      element,
      useGPU: true,
      respectReducedMotion: true
    }
  })
}