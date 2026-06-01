import { useState, useEffect } from 'react'
import { Trophy, Star, ChevronLeft, ChevronRight, X } from 'lucide-react'
import { achievementsApi, type UserAchievement, type AchievementProgress } from '../lib/api'

interface AchievementBannerProps {
  newAchievements?: UserAchievement[]
  achievementProgress?: AchievementProgress[]
  onAchievementsSeen?: () => void
}

export default function AchievementBanner({ 
  newAchievements = [], 
  onAchievementsSeen 
}: AchievementBannerProps) {
  const [showNewAchievements, setShowNewAchievements] = useState(false)
  const [currentAchievementIndex, setCurrentAchievementIndex] = useState(0)

  // Yeni rozetler varsa banner'ı göster
  useEffect(() => {
    if (newAchievements.length > 0) {
      setShowNewAchievements(true)
      setCurrentAchievementIndex(0)
    }
  }, [newAchievements])

  const handleDismiss = async () => {
    setShowNewAchievements(false)
    
    // Rozetleri görüldü olarak işaretle
    if (newAchievements.length > 0) {
      try {
        await achievementsApi.markAsSeen(1) // Şu an tek kullanıcı
        onAchievementsSeen?.()
      } catch (error) {
        console.error('Rozetler işaretlenirken hata:', error)
      }
    }
  }

  const nextAchievement = () => {
    if (currentAchievementIndex < newAchievements.length - 1) {
      setCurrentAchievementIndex(currentAchievementIndex + 1)
    } else {
      handleDismiss()
    }
  }

  const prevAchievement = () => {
    if (currentAchievementIndex > 0) {
      setCurrentAchievementIndex(currentAchievementIndex - 1)
    }
  }

  // Yeni rozet banner'ı
  if (showNewAchievements && newAchievements.length > 0) {
    const achievement = newAchievements[currentAchievementIndex]
    
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="glass-card p-8 max-w-md w-full text-center animate-pulse-glow">
          <div className="text-6xl mb-4">{achievement.achievement.icon}</div>
          
          <div className="flex items-center justify-center gap-2 mb-2">
            <Trophy className="w-6 h-6 text-yellow-400" />
            <h2 className="text-2xl font-bold text-white">
              Rozet Kazandın!
            </h2>
          </div>
          
          <h3 className="text-xl font-semibold text-purple-300 mb-3">
            {achievement.achievement.name}
          </h3>
          
          <p className="text-gray-300 mb-4">
            {achievement.achievement.description}
          </p>
          
          <div className="flex items-center justify-center gap-2 mb-6 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
            <Star className="w-5 h-5 text-yellow-400" />
            <span className="text-white font-medium">
              +{achievement.achievement.points} puan
            </span>
          </div>
          
          {/* Navigation */}
          <div className="flex items-center justify-between">
            <button
              onClick={prevAchievement}
              disabled={currentAchievementIndex === 0}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600/50 hover:bg-gray-600/70 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              <ChevronLeft size={16} />
              Önceki
            </button>
            
            <span className="text-gray-400 text-sm">
              {currentAchievementIndex + 1} / {newAchievements.length}
            </span>
            
            <button
              onClick={nextAchievement}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-all duration-200"
            >
              {currentAchievementIndex < newAchievements.length - 1 ? (
                <>Sonraki <ChevronRight size={16} /></>
              ) : (
                <>Tamam <X size={16} /></>
              )}
            </button>
          </div>
        </div>
      </div>
    )
  }

  // İlerleme göstergesi artık gösterilmiyor - ayrı sayfada
  return null
}