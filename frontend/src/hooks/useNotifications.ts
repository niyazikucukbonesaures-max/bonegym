/**
 * useNotifications Hook
 * React hook for managing notifications
 */

import { useCallback, useEffect, useState } from 'react'
import NotificationSystem, { 
  NotificationConfig, 
  NotificationInstance, 
  NotificationEvent,
  NotificationPosition,
  NotificationType
} from '@/lib/notifications/NotificationSystem'

export interface UseNotificationsOptions {
  position?: NotificationPosition
  maxNotifications?: number
  defaultDuration?: number
}

export interface NotificationHookResult {
  notifications: NotificationInstance[]
  show: (message: string, options?: Partial<NotificationConfig>) => string
  success: (message: string, options?: Partial<NotificationConfig>) => string
  error: (message: string, options?: Partial<NotificationConfig>) => string
  warning: (message: string, options?: Partial<NotificationConfig>) => string
  info: (message: string, options?: Partial<NotificationConfig>) => string
  loading: (message: string, options?: Partial<NotificationConfig>) => string
  dismiss: (id: string) => boolean
  dismissAll: () => void
  clear: () => void
  update: (id: string, updates: Partial<NotificationConfig>) => boolean
}

export function useNotifications(options: UseNotificationsOptions = {}): NotificationHookResult {
  const {
    position = 'top-right',
    maxNotifications = 5,
    defaultDuration = 4000
  } = options

  const notificationSystem = NotificationSystem.getInstance()
  const [notifications, setNotifications] = useState<NotificationInstance[]>([])

  // Update notifications list when changes occur
  useEffect(() => {
    const updateNotifications = () => {
      setNotifications(notificationSystem.getNotifications(position))
    }

    const handleNotificationEvent = (event: NotificationEvent) => {
      updateNotifications()
    }

    // Listen to all notification events
    notificationSystem.addEventListener('show', handleNotificationEvent)
    notificationSystem.addEventListener('dismiss', handleNotificationEvent)
    notificationSystem.addEventListener('timeout', handleNotificationEvent)

    // Initial load
    updateNotifications()

    return () => {
      notificationSystem.removeEventListener('show', handleNotificationEvent)
      notificationSystem.removeEventListener('dismiss', handleNotificationEvent)
      notificationSystem.removeEventListener('timeout', handleNotificationEvent)
    }
  }, [position])

  const show = useCallback((message: string, customOptions: Partial<NotificationConfig> = {}) => {
    return notificationSystem.show({
      message,
      position,
      duration: defaultDuration,
      ...customOptions
    })
  }, [position, defaultDuration])

  const success = useCallback((message: string, options: Partial<NotificationConfig> = {}) => {
    return notificationSystem.success(message, {
      position,
      duration: defaultDuration,
      ...options
    })
  }, [position, defaultDuration])

  const error = useCallback((message: string, options: Partial<NotificationConfig> = {}) => {
    return notificationSystem.error(message, {
      position,
      duration: 6000, // Longer duration for errors
      ...options
    })
  }, [position])

  const warning = useCallback((message: string, options: Partial<NotificationConfig> = {}) => {
    return notificationSystem.warning(message, {
      position,
      duration: 5000,
      ...options
    })
  }, [position])

  const info = useCallback((message: string, options: Partial<NotificationConfig> = {}) => {
    return notificationSystem.info(message, {
      position,
      duration: defaultDuration,
      ...options
    })
  }, [position, defaultDuration])

  const loading = useCallback((message: string, options: Partial<NotificationConfig> = {}) => {
    return notificationSystem.loading(message, {
      position,
      ...options
    })
  }, [position])

  const dismiss = useCallback((id: string) => {
    return notificationSystem.dismiss(id)
  }, [])

  const dismissAll = useCallback(() => {
    notificationSystem.dismissAll(position)
  }, [position])

  const clear = useCallback(() => {
    notificationSystem.clear()
  }, [])

  const update = useCallback((id: string, updates: Partial<NotificationConfig>) => {
    return notificationSystem.update(id, updates)
  }, [])

  return {
    notifications,
    show,
    success,
    error,
    warning,
    info,
    loading,
    dismiss,
    dismissAll,
    clear,
    update
  }
}

// Specialized hooks for common use cases

export function useToast() {
  const { success, error, warning, info } = useNotifications({
    position: 'top-right',
    defaultDuration: 3000
  })

  return {
    toast: {
      success,
      error,
      warning,
      info
    }
  }
}

export function useLoadingNotification() {
  const { loading, success, error, update, dismiss } = useNotifications()

  const showLoading = useCallback((message: string) => {
    return loading(message, {
      persistent: true,
      allowDismiss: false,
      showProgress: false
    })
  }, [loading])

  const completeLoading = useCallback((id: string, successMessage?: string, errorMessage?: string) => {
    if (successMessage) {
      update(id, {
        type: 'success',
        message: successMessage,
        persistent: false,
        duration: 3000,
        allowDismiss: true
      })
    } else if (errorMessage) {
      update(id, {
        type: 'error',
        message: errorMessage,
        persistent: false,
        duration: 5000,
        allowDismiss: true
      })
    } else {
      dismiss(id)
    }
  }, [update, dismiss])

  return {
    showLoading,
    completeLoading,
    dismiss
  }
}

export function useFormNotifications() {
  const { success, error, warning } = useNotifications({
    position: 'top-center',
    defaultDuration: 4000
  })

  const showValidationError = useCallback((message: string) => {
    return error(message, {
      title: 'Doğrulama Hatası',
      hapticFeedback: true
    })
  }, [error])

  const showSaveSuccess = useCallback((message: string = 'Başarıyla kaydedildi!') => {
    return success(message, {
      title: 'Başarılı',
      hapticFeedback: true
    })
  }, [success])

  const showSaveError = useCallback((message: string = 'Kaydetme sırasında hata oluştu.') => {
    return error(message, {
      title: 'Kaydetme Hatası',
      duration: 6000
    })
  }, [error])

  const showUnsavedChanges = useCallback(() => {
    return warning('Kaydedilmemiş değişiklikleriniz var.', {
      title: 'Uyarı',
      persistent: true,
      actions: [
        {
          label: 'Kaydet',
          action: () => {
            // This should be handled by the component
          },
          style: 'primary'
        },
        {
          label: 'Vazgeç',
          action: () => {
            // This should be handled by the component
          },
          style: 'secondary'
        }
      ]
    })
  }, [warning])

  return {
    showValidationError,
    showSaveSuccess,
    showSaveError,
    showUnsavedChanges
  }
}

export function useNetworkNotifications() {
  const { error, success, warning, dismiss } = useNotifications({
    position: 'bottom-center'
  })

  const [offlineNotificationId, setOfflineNotificationId] = useState<string | null>(null)

  useEffect(() => {
    const handleOnline = () => {
      if (offlineNotificationId) {
        dismiss(offlineNotificationId)
        setOfflineNotificationId(null)
      }
      
      success('İnternet bağlantısı yeniden kuruldu!', {
        duration: 2000
      })
    }

    const handleOffline = () => {
      const id = error('İnternet bağlantısı kesildi. Çevrimdışı modda çalışıyorsunuz.', {
        persistent: true,
        allowDismiss: false
      })
      setOfflineNotificationId(id)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [offlineNotificationId, dismiss, success, error])

  const showNetworkError = useCallback((message: string = 'Ağ hatası oluştu. Lütfen tekrar deneyin.') => {
    return error(message, {
      title: 'Bağlantı Hatası',
      duration: 5000
    })
  }, [error])

  const showSlowConnection = useCallback(() => {
    return warning('Yavaş internet bağlantısı tespit edildi.', {
      title: 'Yavaş Bağlantı',
      duration: 3000
    })
  }, [warning])

  return {
    showNetworkError,
    showSlowConnection
  }
}