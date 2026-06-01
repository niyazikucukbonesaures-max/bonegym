import { useState, useEffect } from 'react'
import { 
  Trophy, Star, Award, Target, Flame, Droplets, 
  Zap, CheckCircle, Lock, BarChart3, Calendar,
  TrendingUp, Users, Medal
} from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { achievementsApi, type UserAchievement, type AchievementProgress } from '@/lib/api'

interface AchievementsData {
  userAchievements: UserAchievement[]
  achievementProgress: AchievementProgress[]
}

export default function Achievements() {
  const [data, setData] = useState<AchievementsData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'earned' | 'progress'>('progress')

  useEffect(() => {
    loadAchievements()
  }, [])

  const loadAchievements = async () => {
    try {
      setIsLoading(true)
      const [userAchievements, achievementProgress] = await Promise.all([
        achievementsApi.getUserAchievements(1).catch(() => ({ data: [] })),
        achievementsApi.getProgress(1).catch(() => ({ data: [] }))
      ])
      
      setData({
        userAchievements: userAchievements.data || [],
        achievementProgress: achievementProgress.data || []
      })
    } catch (error) {
      console.error('Rozetler yüklenirken hata:', error)
      // FALLBACK - Boş data
      setData({
        userAchievements: [],
        achievementProgress: []
      })
    } finally {
      setIsLoading(false)
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'food': return <Flame className="w-5 h-5" />
      case 'water': return <Droplets className="w-5 h-5" />
      case 'workout': return <Zap className="w-5 h-5" />
      case 'creatine': return <Target className="w-5 h-5" />
      case 'streak': return <Calendar className="w-5 h-5" />
      case 'milestone': return <TrendingUp className="w-5 h-5" />
      default: return <Award className="w-5 h-5" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'food': return 'from-orange-500 to-red-600'
      case 'water': return 'from-blue-500 to-cyan-600'
      case 'workout': return 'from-purple-500 to-violet-600'
      case 'creatine': return 'from-pink-500 to-rose-600'
      case 'streak': return 'from-emerald-500 to-teal-600'
      case 'milestone': return 'from-yellow-500 to-orange-600'
      default: return 'from-gray-500 to-gray-600'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('tr-TR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    })
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-6 max-w-6xl mx-auto">
        <div className="h-12 w-64 bg-white/10 rounded-lg skeleton" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-48 bg-white/10 rounded-2xl skeleton" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-orange-600 rounded-xl flex items-center justify-center shadow-lg shadow-yellow-500/25">
            <Trophy className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">Başarı Rozetleri</h1>
        </div>
        <p className="text-white/70 max-w-2xl mx-auto">
          Fitness yolculuğundaki başarılarını takip et ve yeni hedeflere ulaş!
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassCard className="p-4 text-center" noblur>
          <div className="w-10 h-10 bg-gradient-to-br from-yellow-500 to-orange-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
            <Medal className="w-5 h-5 text-white" />
          </div>
          <p className="text-2xl font-bold text-white">{data?.userAchievements.length || 0}</p>
          <p className="text-xs text-white/60">Kazanılan Rozet</p>
        </GlassCard>
        
        <GlassCard className="p-4 text-center" noblur>
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <p className="text-2xl font-bold text-white">{data?.achievementProgress.length || 0}</p>
          <p className="text-xs text-white/60">Devam Eden</p>
        </GlassCard>
        
        <GlassCard className="p-4 text-center" noblur>
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
            <Star className="w-5 h-5 text-white" />
          </div>
          <p className="text-2xl font-bold text-white">
            {data?.userAchievements.reduce((sum, ua) => sum + ua.achievement.points, 0) || 0}
          </p>
          <p className="text-xs text-white/60">Toplam Puan</p>
        </GlassCard>
        
        <GlassCard className="p-4 text-center" noblur>
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-violet-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
            <Users className="w-5 h-5 text-white" />
          </div>
          <p className="text-2xl font-bold text-white">
            {Math.round(((data?.userAchievements.length || 0) / ((data?.userAchievements.length || 0) + (data?.achievementProgress.length || 1))) * 100)}%
          </p>
          <p className="text-xs text-white/60">Tamamlama</p>
        </GlassCard>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center justify-center">
        <div className="flex bg-white/5 rounded-xl p-1">
          <Button
            onClick={() => setActiveTab('progress')}
            variant={activeTab === 'progress' ? 'default' : 'ghost'}
            size="sm"
            className={`${activeTab === 'progress' ? 'bg-purple-600 text-white' : 'text-white/70 hover:text-white'}`}
          >
            <Target className="w-4 h-4 mr-2" />
            İlerleme ({data?.achievementProgress.length || 0})
          </Button>
          <Button
            onClick={() => setActiveTab('earned')}
            variant={activeTab === 'earned' ? 'default' : 'ghost'}
            size="sm"
            className={`${activeTab === 'earned' ? 'bg-purple-600 text-white' : 'text-white/70 hover:text-white'}`}
          >
            <Trophy className="w-4 h-4 mr-2" />
            Kazanılan ({data?.userAchievements.length || 0})
          </Button>
        </div>
      </div>

      {/* Content */}
      {activeTab === 'progress' ? (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <Target className="w-5 h-5" />
            Devam Eden Rozetler
          </h2>
          
          {data?.achievementProgress.length === 0 ? (
            <GlassCard className="p-8 text-center" noblur>
              <Lock className="w-12 h-12 text-white/30 mx-auto mb-4" />
              <p className="text-white/70">Tüm rozetleri kazandın! 🎉</p>
            </GlassCard>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data?.achievementProgress.map((progress) => (
                <GlassCard key={progress.achievement.id} className="p-6 hover:scale-105 transition-all duration-300" noblur>
                  <div className="flex items-start gap-4 mb-4">
                    <div className={`w-12 h-12 bg-gradient-to-br ${getCategoryColor(progress.achievement.category)} rounded-xl flex items-center justify-center shadow-lg`}>
                      {getCategoryIcon(progress.achievement.category)}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-white text-lg">{progress.achievement.name}</h3>
                      <p className="text-white/70 text-sm mt-1">{progress.achievement.description}</p>
                    </div>
                  </div>
                  
                  {/* Progress Bar */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-white/70">İlerleme</span>
                      <span className="text-white font-medium">
                        {progress.current_value} / {progress.target_value}
                      </span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full bg-gradient-to-r ${getCategoryColor(progress.achievement.category)} transition-all duration-500`}
                        style={{ width: `${Math.min(progress.percentage, 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-white/50">
                        {Math.round(progress.percentage)}% tamamlandı
                      </span>
                      <div className="flex items-center gap-1 text-yellow-400">
                        <Star className="w-3 h-3" />
                        <span className="text-xs font-medium">+{progress.achievement.points}</span>
                      </div>
                    </div>
                  </div>
                </GlassCard>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <Trophy className="w-5 h-5" />
            Kazanılan Rozetler
          </h2>
          
          {data?.userAchievements.length === 0 ? (
            <GlassCard className="p-8 text-center" noblur>
              <Trophy className="w-12 h-12 text-white/30 mx-auto mb-4" />
              <p className="text-white/70">Henüz rozet kazanmadın. Hadi başlayalım! 💪</p>
            </GlassCard>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data?.userAchievements.map((userAchievement) => (
                <GlassCard key={userAchievement.id} className="p-6 hover:scale-105 transition-all duration-300 border border-yellow-500/20" noblur>
                  <div className="flex items-start gap-4 mb-4">
                    <div className={`w-12 h-12 bg-gradient-to-br ${getCategoryColor(userAchievement.achievement.category)} rounded-xl flex items-center justify-center shadow-lg shadow-yellow-500/25`}>
                      {getCategoryIcon(userAchievement.achievement.category)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-white text-lg">{userAchievement.achievement.name}</h3>
                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                      </div>
                      <p className="text-white/70 text-sm">{userAchievement.achievement.description}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between pt-4 border-t border-white/10">
                    <div className="flex items-center gap-2">
                      <Star className="w-4 h-4 text-yellow-400" />
                      <span className="text-white font-medium">+{userAchievement.achievement.points} puan</span>
                    </div>
                    <span className="text-xs text-white/50">
                      {formatDate(userAchievement.earned_at)}
                    </span>
                  </div>
                </GlassCard>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}