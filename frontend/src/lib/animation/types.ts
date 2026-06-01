/**
 * Animation System Types
 * Core type definitions for the advanced animation system
 */

export type AnimationEasing = 
  | 'linear'
  | 'ease'
  | 'ease-in'
  | 'ease-out'
  | 'ease-in-out'
  | 'cubic-bezier'
  | string

export type AnimationDirection = 'normal' | 'reverse' | 'alternate' | 'alternate-reverse'

export type AnimationFillMode = 'none' | 'forwards' | 'backwards' | 'both'

export interface AnimationConfig {
  id: string
  duration: number
  delay?: number
  easing?: AnimationEasing
  direction?: AnimationDirection
  fillMode?: AnimationFillMode
  iterations?: number | 'infinite'
  playbackRate?: number
  onStart?: () => void
  onComplete?: () => void
  onCancel?: () => void
}

export interface AnimationKeyframe {
  offset: number
  [property: string]: any
}

export interface AnimationOptions {
  keyframes: AnimationKeyframe[]
  config: AnimationConfig
  element?: HTMLElement
  useGPU?: boolean
  respectReducedMotion?: boolean
}

export interface AnimationInstance {
  id: string
  element: HTMLElement
  animation: Animation
  config: AnimationConfig
  startTime: number
  isRunning: boolean
  isPaused: boolean
}

export interface PerformanceMetrics {
  fps: number
  frameDrops: number
  memoryUsage: number
  activeAnimations: number
  lastFrameTime: number
}

export interface AnimationSystemConfig {
  maxConcurrentAnimations: number
  targetFPS: number
  enableGPUAcceleration: boolean
  respectReducedMotion: boolean
  performanceMonitoring: boolean
  debugMode: boolean
}

export type AnimationEventType = 'start' | 'complete' | 'cancel' | 'pause' | 'resume'

export interface AnimationEvent {
  type: AnimationEventType
  animationId: string
  timestamp: number
  element: HTMLElement
}

export type AnimationEventListener = (event: AnimationEvent) => void

export interface MicroInteractionConfig {
  type: 'hover' | 'focus' | 'click' | 'success' | 'error' | 'loading'
  intensity: 'subtle' | 'medium' | 'strong'
  duration: number
  useHaptic?: boolean
}

export interface GlassmorphismConfig {
  blur: number
  opacity: number
  borderOpacity: number
  shadowIntensity: number
  adaptToBackground: boolean
  useGPU: boolean
}