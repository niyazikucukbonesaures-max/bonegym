/**
 * Animation System - Main Export
 * Advanced animation system for React applications
 */

export { default as AnimationSystem } from './AnimationSystem'
export * from './types'
export * from './presets'

// Re-export for convenience
export { ANIMATION_PRESETS, createAnimationFromPreset, createStaggeredAnimation } from './presets'