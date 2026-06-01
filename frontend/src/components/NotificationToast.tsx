import { useState, useEffect } from 'react'
import { Trophy, X, Star, CheckCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface Achievement {
  id: number
  name: string
  description: string
  icon: string
  points: number
  category: string
}

interface NotificationToastProps {
  achievement: Achievement | null
  onClose: () => void
}

export default function NotificationToast({ achievement, onClose }: NotificationToastProps) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    if (achievement) {
      setIsVisible(true)
      // 5 saniye sonra otomatik kapat
      const timer = setTimeout(() => {
        handleClose()
      }, 5000)
      
      return () => clearTimeout(timer)
    }
  }, [achievement])

  const handleClose = () => {
    setIsVisible(false)
    setTimeout(() => {
      onClose()
    }, 300) // Animation tamamlandıktan sonra
  }

  if (!achievement) return null

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, x: 400, scale: 0.8 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: 400, scale: 0.8 }}
          transition={{ 
            type: "spring", 
            stiffness: 300, 
            damping: 30,
            duration: 0.5
          }}
          className="fixed bottom-6 right-6 z-50 max-w-sm"
        >
          <div className="glass-card p-4 border border-yellow-500/30 shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-yellow-500 to-orange-600 rounded-lg flex items-center justify-center shadow-lg shadow-yellow-500/25">
                  <Trophy className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-semibold text-yellow-400">Rozet Kazandın!</span>
              </div>
              <button
                onClick={handleClose}
                className="text-white/50 hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Achievement Content */}
            <div className="flex items-start gap-3">
              <div className="text-3xl">{achievement.icon}</div>
              <div className="flex-1">
                <h4 className="font-semibold text-white text-base mb-1">
                  {achievement.name}
                </h4>
                <p className="text-white/70 text-sm mb-3">
                  {achievement.description}
                </p>
                
                {/* Points */}
                <div className="flex items-center gap-2 p-2 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                  <Star className="w-4 h-4 text-yellow-400" />
                  <span className="text-white font-medium text-sm">
                    +{achievement.points} puan kazandın
                  </span>
                </div>
              </div>
            </div>

            {/* Success Icon */}
            <div className="absolute -top-2 -right-2">
              <div className="w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center shadow-lg">
                <CheckCircle className="w-4 h-4 text-white" />
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mt-3">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: "100%" }}
                transition={{ duration: 5, ease: "linear" }}
                className="h-1 bg-gradient-to-r from-yellow-500 to-orange-600 rounded-full"
              />
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}