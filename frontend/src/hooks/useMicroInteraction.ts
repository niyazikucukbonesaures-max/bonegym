/**
 * useMicroInteraction Hook
 * React hook for easy micro-interaction integration
 */

import { useRef, useCallback, useEffect } from 'react'
import MicroInteractionSystem, { MicroInteractionType, MicroInteractionOptions } from '@/lib/microInteractions/MicroInteractionSystem'
import { useAnimation } from '@/contexts/AnimationContext'

export interface UseMicroInteractionOptions {
  intensity?: 'subtle' | 'medium' | 'strong'
  useHaptic?: boolean
  disabled?: boolean
}

export interface MicroInteractionHandlers {
  onHover: () => void
  onHoverEnd: () => void
  onFocus: () => void
  onBlur: () => void
  onClick: () => void
  onSuccess: () => void
  onError: () => void
  onLoading: () => void
  onAdd: () => void
  onRemove: () => void
  validate: (isValid: boolean) => void
  trigger: (type: MicroInteractionType, customOptions?: Partial<MicroInteractionOptions>) => void
  clear: () => void
}

export function useMicroInteraction<T extends HTMLElement = HTMLElement>(
  options: UseMicroInteractionOptions = {}
): [React.RefObject<T>, MicroInteractionHandlers] {
  const elementRef = useRef<T>(null)
  const microInteractionSystem = MicroInteractionSystem.getInstance()
  const { isReducedMotion } = useAnimation()
  
  const {
    intensity = 'medium',
    useHaptic = true,
    disabled = false
  } = options

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (elementRef.current) {
        microInteractionSystem.clearElementInteractions(elementRef.current)
      }
    }
  }, [])

  const createHandler = useCallback((type: MicroInteractionType) => {
    return (customOptions?: Partial<MicroInteractionOptions>) => {
      if (disabled || !elementRef.current) return

      const finalOptions: MicroInteractionOptions = {
        type,
        element: elementRef.current,
        intensity,
        useHaptic,
        ...customOptions
      }

      // Adjust for reduced motion
      if (isReducedMotion) {
        finalOptions.duration = Math.min(finalOptions.duration || 300, 200)
        finalOptions.intensity = 'subtle'
      }

      microInteractionSystem.trigger(finalOptions)
    }
  }, [disabled, intensity, useHaptic, isReducedMotion])

  const handlers: MicroInteractionHandlers = {
    onHover: useCallback(() => createHandler('hover')(), [createHandler]),
    
    onHoverEnd: useCallback(() => {
      // Cancel hover animations when hover ends
      if (elementRef.current) {
        const state = microInteractionSystem.getElementState(elementRef.current)
        if (state.isHovered) {
          // Trigger a subtle reverse animation or just clear
          microInteractionSystem.clearElementInteractions(elementRef.current)
        }
      }
    }, []),

    onFocus: useCallback(() => createHandler('focus')(), [createHandler]),
    
    onBlur: useCallback(() => {
      // Clear focus state
      if (elementRef.current) {
        const state = microInteractionSystem.getElementState(elementRef.current)
        if (state.isFocused) {
          microInteractionSystem.clearElementInteractions(elementRef.current)
        }
      }
    }, []),

    onClick: useCallback(() => createHandler('click')(), [createHandler]),
    
    onSuccess: useCallback(() => createHandler('success')(), [createHandler]),
    
    onError: useCallback(() => createHandler('error')(), [createHandler]),
    
    onLoading: useCallback(() => createHandler('loading')(), [createHandler]),
    
    onAdd: useCallback(() => createHandler('add')(), [createHandler]),
    
    onRemove: useCallback(() => createHandler('remove')(), [createHandler]),
    
    validate: useCallback((isValid: boolean) => {
      createHandler(isValid ? 'success' : 'error')()
    }, [createHandler]),

    trigger: useCallback((type: MicroInteractionType, customOptions?: Partial<MicroInteractionOptions>) => {
      createHandler(type)(customOptions)
    }, [createHandler]),

    clear: useCallback(() => {
      if (elementRef.current) {
        microInteractionSystem.clearElementInteractions(elementRef.current)
      }
    }, [])
  }

  return [elementRef, handlers]
}

// Specialized hooks for common use cases

export function useButtonInteraction(options: UseMicroInteractionOptions = {}) {
  const [ref, handlers] = useMicroInteraction<HTMLButtonElement>(options)
  
  const buttonProps = {
    ref,
    onMouseEnter: handlers.onHover,
    onMouseLeave: handlers.onHoverEnd,
    onFocus: handlers.onFocus,
    onBlur: handlers.onBlur,
    onMouseDown: handlers.onClick,
    onTouchStart: handlers.onClick
  }

  return {
    ref,
    handlers,
    buttonProps
  }
}

export function useInputInteraction(options: UseMicroInteractionOptions = {}) {
  const [ref, handlers] = useMicroInteraction<HTMLInputElement>(options)
  
  const inputProps = {
    ref,
    onFocus: handlers.onFocus,
    onBlur: handlers.onBlur
  }

  return {
    ref,
    handlers,
    inputProps,
    validate: handlers.validate
  }
}

export function useCardInteraction(options: UseMicroInteractionOptions = {}) {
  const [ref, handlers] = useMicroInteraction<HTMLDivElement>({
    intensity: 'subtle',
    ...options
  })
  
  const cardProps = {
    ref,
    onMouseEnter: handlers.onHover,
    onMouseLeave: handlers.onHoverEnd
  }

  return {
    ref,
    handlers,
    cardProps
  }
}

// Hook for form validation with micro-interactions
export function useFormValidation<T extends HTMLElement = HTMLInputElement>() {
  const [ref, handlers] = useMicroInteraction<T>()
  
  const validateField = useCallback((value: any, validator: (value: any) => boolean) => {
    const isValid = validator(value)
    handlers.validate(isValid)
    return isValid
  }, [handlers])

  const showSuccess = useCallback(() => {
    handlers.onSuccess()
  }, [handlers])

  const showError = useCallback(() => {
    handlers.onError()
  }, [handlers])

  return {
    ref,
    validateField,
    showSuccess,
    showError,
    handlers
  }
}

// Hook for list item interactions (add/remove animations)
export function useListItemInteraction(options: UseMicroInteractionOptions = {}) {
  const [ref, handlers] = useMicroInteraction<HTMLLIElement>(options)
  
  const animateAdd = useCallback(() => {
    handlers.onAdd()
  }, [handlers])

  const animateRemove = useCallback(() => {
    return new Promise<void>((resolve) => {
      handlers.trigger('remove', {
        onComplete: resolve
      })
    })
  }, [handlers])

  return {
    ref,
    handlers,
    animateAdd,
    animateRemove
  }
}

// Hook for loading states with micro-interactions
export function useLoadingInteraction(options: UseMicroInteractionOptions = {}) {
  const [ref, handlers] = useMicroInteraction<HTMLDivElement>(options)
  
  const startLoading = useCallback(() => {
    handlers.onLoading()
  }, [handlers])

  const stopLoading = useCallback(() => {
    handlers.clear()
  }, [handlers])

  const completeWithSuccess = useCallback(() => {
    handlers.clear()
    setTimeout(() => handlers.onSuccess(), 100)
  }, [handlers])

  const completeWithError = useCallback(() => {
    handlers.clear()
    setTimeout(() => handlers.onError(), 100)
  }, [handlers])

  return {
    ref,
    handlers,
    startLoading,
    stopLoading,
    completeWithSuccess,
    completeWithError
  }
}