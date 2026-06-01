import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, AlertTriangle, Info, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface Notification {
  id: string
  type: 'info' | 'warning' | 'success' | 'error'
  title: string
  message: string
  created_at: string
}

const iconMap = {
  info: Info,
  warning: AlertTriangle,
  success: CheckCircle,
  error: AlertCircle,
}

const colorMap = {
  info: 'from-blue-500 to-cyan-500',
  warning: 'from-amber-500 to-orange-500',
  success: 'from-emerald-500 to-green-500',
  error: 'from-red-500 to-pink-500',
}

export function NotificationBanner() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchNotifications()
  }, [])

  const fetchNotifications = async () => {
    try {
      const response = await fetch('/api/notifications')
      if (response.ok) {
        const data = await response.json()
        setNotifications(data)
      }
    } catch (error) {
      console.error('Bildirimler yüklenirken hata:', error)
    }
  }

  const dismissNotification = (id: string) => {
    setDismissedIds(prev => new Set([...prev, id]))
  }

  const visibleNotifications = notifications.filter(n => !dismissedIds.has(n.id))

  if (visibleNotifications.length === 0) {
    return null
  }

  return (
    <div className="space-y-3 mb-6">
      <AnimatePresence>
        {visibleNotifications.map((notification) => {
          const Icon = iconMap[notification.type]
          const gradient = colorMap[notification.type]
          
          return (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, y: -50, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="relative overflow-hidden rounded-2xl backdrop-blur-md bg-white/10 dark:bg-white/5 border border-white/20 shadow-xl"
            >
              {/* Gradient background */}
              <div className={`absolute inset-0 bg-gradient-to-r ${gradient} opacity-10`} />
              
              <div className="relative p-4 flex items-start gap-3">
                <div className={`flex-shrink-0 p-2 rounded-full bg-gradient-to-r ${gradient}`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-white mb-1">
                    {notification.title}
                  </h3>
                  <p className="text-sm text-white/80 leading-relaxed">
                    {notification.message}
                  </p>
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => dismissNotification(notification.id)}
                  className="flex-shrink-0 text-white/60 hover:text-white hover:bg-white/10"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}