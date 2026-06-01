import { useState, useEffect, useRef, useCallback } from 'react'

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)
  const timeoutRef = useRef<number>()

  useEffect(() => {
    // Önceki timeout'u temizle
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    // Yeni timeout ayarla
    timeoutRef.current = window.setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    // Cleanup function
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [value, delay])

  return debouncedValue
}

// Daha gelişmiş debounce hook - callback tabanlı
export function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const timeoutRef = useRef<number>()
  const callbackRef = useRef(callback)

  // Callback'i güncel tut
  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  const debouncedCallback = useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      timeoutRef.current = window.setTimeout(() => {
        callbackRef.current(...args)
      }, delay)
    },
    [delay]
  ) as T

  // Cleanup
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return debouncedCallback
}