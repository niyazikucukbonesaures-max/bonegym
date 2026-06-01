import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { 
  Users, 
  Plus, 
  Trophy, 
  Star, 
  ThumbsUp, 
  CheckCircle, 
  TrendingUp,
  Award,
  Target,
  Clock,
  Zap,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { SkeletonLoader, TextSkeleton } from '@/components/ui/SkeletonLoader'
import { 
  crowdsourceApi, 
  type ContributionRequest, 
  type LeaderboardEntry, 
  type MissingFoodEntry,
  type UserStats,
  type DailyChallenge,
  type SystemStats
} from '@/lib/api'
import { useNotifications } from '@/hooks/useNotifications'
import { usePerformanceMonitor } from '@/hooks/usePerformanceMonitor'
import { useAnimation } from '@/contexts/AnimationContext'
import { 
  useMicroInteraction, 
  useCardInteraction, 
  useFormValidation,
  useListItemInteraction,
  useLoadingInteraction
} from '@/hooks/useMicroInteraction'

interface CommunitySectionProps {
  className?: string
}

// Memoized components for performance
const MemoizedGlassCard = React.memo(GlassCard)
const MemoizedButton = React.memo(Button)
const MemoizedInput = React.memo(Input)

// Leaderboard Entry Component with micro-interactions
const LeaderboardEntry: React.FC<{ 
  entry: LeaderboardEntry
  index: number
  onEntryClick?: (entry: LeaderboardEntry) => void
}> = React.memo(({ entry, index, onEntryClick }) => {
  const [cardRef, cardHandlers] = useCardInteraction({ intensity: 'subtle' })
  
  const getRankColor = (index: number) => {
    switch (index) {
      case 0: return 'bg-yellow-500/20 text-yellow-400'
      case 1: return 'bg-gray-500/20 text-gray-400'
      case 2: return 'bg-amber-600/20 text-amber-400'
      default: return 'bg-white/10 text-white/60'
    }
  }

  const handleClick = useCallback(() => {
    cardHandlers.onClick()
    onEntryClick?.(entry)
  }, [entry, onEntryClick, cardHandlers])

  return (
    <div 
      ref={cardRef}
      className="flex items-center justify-between p-3 bg-white/5 rounded-lg cursor-pointer transition-all duration-200 hover:bg-white/10"
      onClick={handleClick}
      {...cardHandlers.cardProps}
    >
      <div className="flex items-center gap-3">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${getRankColor(index)}`}>
          {index + 1}
        </div>
        <div>
          <div className="text-white font-medium">Kullanıcı #{entry.user_id}</div>
          <div className="text-xs text-white/60">
            {entry.contributions} katkı • Seviye {entry.level}
          </div>
        </div>
      </div>
      
      <div className="text-right">
        <div className="text-violet-400 font-bold">{entry.total_points}</div>
        <div className="text-xs text-white/60">puan</div>
      </div>
    </div>
  )
})

// Missing Food Item Component with micro-interactions
const MissingFoodItem: React.FC<{ 
  food: MissingFoodEntry
  onVote?: (foodName: string) => void
}> = React.memo(({ food, onVote }) => {
  const [itemRef, itemHandlers] = useListItemInteraction({ intensity: 'subtle' })
  const [isVoting, setIsVoting] = useState(false)

  const handleVote = useCallback(async () => {
    if (isVoting) return
    
    setIsVoting(true)
    itemHandlers.onClick()
    
    try {
      await onVote?.(food.food_name)
      itemHandlers.onSuccess()
    } catch (error) {
      itemHandlers.onError()
    } finally {
      setIsVoting(false)
    }
  }, [food.food_name, onVote, itemHandlers, isVoting])

  return (
    <div 
      ref={itemRef}
      className="flex items-center justify-between p-2 bg-white/5 rounded-lg hover:bg-white/8 transition-all duration-200"
    >
      <div className="flex items-center gap-2">
        <button
          onClick={handleVote}
          disabled={isVoting}
          className="p-1 rounded hover:bg-emerald-500/20 transition-colors duration-200"
        >
          {isVoting ? (
            <Loader2 size={14} className="text-emerald-400 animate-spin" />
          ) : (
            <ThumbsUp size={14} className="text-emerald-400" />
          )}
        </button>
        <span className="text-white text-sm">{food.food_name}</span>
      </div>
      <div className="flex items-center gap-2 text-xs text-white/60">
        <span>{food.votes} oy</span>
        <Clock size={12} />
        <span>{food.days_ago}g önce</span>
      </div>
    </div>
  )
})

// Stats Card Component with animations
const StatsCard: React.FC<{
  value: string | number
  label: string
  color: string
  icon?: React.ReactNode
}> = React.memo(({ value, label, color, icon }) => {
  const [cardRef, cardHandlers] = useCardInteraction({ intensity: 'subtle' })

  return (
    <div 
      ref={cardRef}
      className="text-center p-3 bg-white/5 rounded-lg hover:bg-white/8 transition-all duration-200"
      {...cardHandlers.cardProps}
    >
      {icon && (
        <div className="flex justify-center mb-1">
          {icon}
        </div>
      )}
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-white/60">{label}</div>
    </div>
  )
})

export const CommunitySection: React.FC<CommunitySectionProps> = ({ className = '' }) => {
  const [activeTab, setActiveTab] = useState<'contribute' | 'leaderboard' | 'missing' | 'stats'>('contribute')
  const [userStats, setUserStats] = useState<UserStats | null>(null)
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null)
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [missingFoods, setMissingFoods] = useState<MissingFoodEntry[]>([])
  const [dailyChallenges, setDailyChallenges] = useState<DailyChallenge[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // UX Enhancement hooks
  const { success, error: showError, info } = useNotifications()
  const { measureRender } = usePerformanceMonitor({
    componentName: 'CommunitySection',
    trackRenderTime: true
  })
  const { isReducedMotion } = useAnimation()
  
  // Micro-interaction hooks
  const [headerRef, headerHandlers] = useMicroInteraction<HTMLDivElement>({ intensity: 'subtle' })
  const [tabsRef, tabsHandlers] = useMicroInteraction<HTMLDivElement>({ intensity: 'medium' })
  const { ref: formRef, validateField, showSuccess, showError: showFormError } = useFormValidation<HTMLFormElement>()
  const { ref: loadingRef, startLoading, stopLoading, completeWithSuccess, completeWithError } = useLoadingInteraction()

  // Form states with validation
  const [contributionForm, setContributionForm] = useState<ContributionRequest>({
    food_name: '',
    calories_per_100g: 0,
    protein_per_100g: 0,
    carbs_per_100g: 0,
    fat_per_100g: 0,
    source: 'homemade',
    brand: ''
  })
  const [suggestionForm, setSuggestionForm] = useState('')
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})

  // Memoized computed values
  const isFormValid = useMemo(() => {
    return contributionForm.food_name.trim().length > 0 &&
           contributionForm.calories_per_100g > 0 &&
           contributionForm.protein_per_100g >= 0 &&
           contributionForm.carbs_per_100g >= 0 &&
           contributionForm.fat_per_100g >= 0
  }, [contributionForm])

  const totalNutrients = useMemo(() => {
    return contributionForm.protein_per_100g + contributionForm.carbs_per_100g + contributionForm.fat_per_100g
  }, [contributionForm.protein_per_100g, contributionForm.carbs_per_100g, contributionForm.fat_per_100g])

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = useCallback(async () => {
    try {
      setLoading(true)
      startLoading()
      
      const loadData = async () => {
        const [userStatsRes, systemStatsRes, leaderboardRes, missingRes, challengesRes] = await Promise.all([
          crowdsourceApi.getUserStats(),
          crowdsourceApi.getSystemStats(),
          crowdsourceApi.getLeaderboard(5),
          crowdsourceApi.getMissingFoods(10),
          crowdsourceApi.getDailyChallenges()
        ])

        return {
          userStats: userStatsRes.data,
          systemStats: systemStatsRes.data,
          leaderboard: leaderboardRes.data,
          missingFoods: missingRes.data,
          dailyChallenges: challengesRes.data.challenges
        }
      }

      const data = await measureRender(loadData)
      
      setUserStats(data.userStats)
      setSystemStats(data.systemStats)
      setLeaderboard(data.leaderboard)
      setMissingFoods(data.missingFoods)
      setDailyChallenges(data.dailyChallenges)
      
      completeWithSuccess()
      setError(null)
    } catch (err: any) {
      setError('Veriler yüklenirken hata oluştu')
      showError('Topluluk verileri yüklenemedi')
      completeWithError()
      console.error('Community data loading error:', err)
    } finally {
      setLoading(false)
      stopLoading()
    }
  }, [measureRender, startLoading, stopLoading, completeWithSuccess, completeWithError, showError])

  // Form validation functions
  const validateFoodName = useCallback((name: string) => {
    if (!name.trim()) {
      setFormErrors(prev => ({ ...prev, food_name: 'Besin adı gerekli' }))
      return false
    }
    if (name.length < 3) {
      setFormErrors(prev => ({ ...prev, food_name: 'Besin adı en az 3 karakter olmalı' }))
      return false
    }
    setFormErrors(prev => ({ ...prev, food_name: '' }))
    return true
  }, [])

  const validateNutrients = useCallback((calories: number, protein: number, carbs: number, fat: number) => {
    const errors: Record<string, string> = {}
    
    if (calories <= 0 || calories > 900) {
      errors.calories = 'Kalori 1-900 arasında olmalı'
    }
    if (protein < 0 || protein > 100) {
      errors.protein = 'Protein 0-100g arasında olmalı'
    }
    if (carbs < 0 || carbs > 100) {
      errors.carbs = 'Karbonhidrat 0-100g arasında olmalı'
    }
    if (fat < 0 || fat > 100) {
      errors.fat = 'Yağ 0-100g arasında olmalı'
    }
    
    // Check if total nutrients make sense
    const totalNutrients = protein + carbs + fat
    if (totalNutrients > 120) {
      errors.total = 'Toplam besin değerleri çok yüksek görünüyor'
    }
    
    setFormErrors(prev => ({ ...prev, ...errors }))
    return Object.keys(errors).length === 0
  }, [])

  const handleContribution = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!contributionForm.food_name.trim()) {
      showFormError()
      return
    }

    // Validate form
    const isNameValid = validateFoodName(contributionForm.food_name)
    const areNutrientsValid = validateNutrients(
      contributionForm.calories_per_100g,
      contributionForm.protein_per_100g,
      contributionForm.carbs_per_100g,
      contributionForm.fat_per_100g
    )

    if (!isNameValid || !areNutrientsValid) {
      showFormError()
      return
    }

    try {
      setLoading(true)
      startLoading()
      
      const response = await measureRender(async () => {
        return await crowdsourceApi.addContribution(contributionForm)
      })
      
      if (response.data.success) {
        // Form'u temizle
        setContributionForm({
          food_name: '',
          calories_per_100g: 0,
          protein_per_100g: 0,
          carbs_per_100g: 0,
          fat_per_100g: 0,
          source: 'homemade',
          brand: ''
        })
        setFormErrors({})
        
        // Verileri yenile
        await loadInitialData()
        
        // Başarı animasyonu ve bildirimi
        showSuccess()
        success(`✅ ${response.data.message}`)
        completeWithSuccess()
      }
    } catch (err: any) {
      setError('Katkı eklenirken hata oluştu')
      showError('Katkı eklenirken hata oluştu')
      showFormError()
      completeWithError()
      console.error('Contribution error:', err)
    } finally {
      setLoading(false)
      stopLoading()
    }
  }, [contributionForm, validateFoodName, validateNutrients, measureRender, startLoading, stopLoading, completeWithSuccess, completeWithError, showSuccess, showFormError, success, showError, loadInitialData])

  const handleSuggestion = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (!suggestionForm.trim()) return

    try {
      setLoading(true)
      startLoading()
      
      await measureRender(async () => {
        return await crowdsourceApi.suggestMissingFood(suggestionForm)
      })
      
      setSuggestionForm('')
      await loadInitialData()
      
      success('✅ Öneri eklendi! 5 puan kazandınız.')
      completeWithSuccess()
    } catch (err: any) {
      setError('Öneri eklenirken hata oluştu')
      showError('Öneri eklenirken hata oluştu')
      completeWithError()
      console.error('Suggestion error:', err)
    } finally {
      setLoading(false)
      stopLoading()
    }
  }, [suggestionForm, measureRender, startLoading, stopLoading, completeWithSuccess, completeWithError, success, showError, loadInitialData])

  const handleTabChange = useCallback((newTab: typeof activeTab) => {
    tabsHandlers.onClick()
    setActiveTab(newTab)
  }, [tabsHandlers])

  const handleVoteMissingFood = useCallback(async (foodName: string) => {
    try {
      await crowdsourceApi.voteMissingFood(foodName)
      await loadInitialData()
      info(`${foodName} için oy verildi!`)
    } catch (error) {
      showError('Oy verirken hata oluştu')
    }
  }, [loadInitialData, info, showError])

  const getLevelColor = (level: number) => {
    if (level >= 10) return 'text-purple-400'
    if (level >= 5) return 'text-blue-400'
    if (level >= 3) return 'text-green-400'
    return 'text-yellow-400'
  }

  const getBadgeEmoji = (badge: string) => {
    const badgeMap: Record<string, string> = {
      'contributor': '🌟',
      'verifier': '✅',
      'level_5': '🏆',
      'level_10': '👑',
      'first_contribution': '🎯'
    }
    return badgeMap[badge] || '🏅'
  }

  if (loading && !userStats) {
    return (
      <MemoizedGlassCard className={`p-6 ${className}`}>
        <div className="space-y-4">
          <SkeletonLoader className="h-16 w-full" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <SkeletonLoader className="h-12 w-full" />
            <SkeletonLoader className="h-12 w-full" />
            <SkeletonLoader className="h-12 w-full" />
            <SkeletonLoader className="h-12 w-full" />
          </div>
          <div className="flex gap-2">
            <SkeletonLoader className="h-8 w-20" />
            <SkeletonLoader className="h-8 w-20" />
            <SkeletonLoader className="h-8 w-20" />
            <SkeletonLoader className="h-8 w-20" />
          </div>
          <SkeletonLoader className="h-32 w-full" />
        </div>
      </MemoizedGlassCard>
    )
  }

  return (
    <div className={`space-y-4 ${className}`} ref={loadingRef}>
      {/* Header with User Stats */}
      <MemoizedGlassCard className="p-4" interactive intensity="subtle">
        <div 
          ref={headerRef}
          className="flex items-center justify-between mb-4"
          {...headerHandlers}
        >
          <div className="flex items-center gap-3">
            <Users className="text-violet-400" size={24} />
            <div>
              <h3 className="text-lg font-semibold text-white">Topluluk</h3>
              <p className="text-sm text-white/60">Besin veritabanını birlikte büyütelim</p>
            </div>
          </div>
          
          {userStats && (
            <div className="flex items-center gap-4 text-sm">
              <div className="text-center">
                <div className={`font-bold ${getLevelColor(userStats.level)}`}>
                  Seviye {userStats.level}
                </div>
                <div className="text-white/60">{userStats.total_points} puan</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-emerald-400">#{userStats.rank}</div>
                <div className="text-white/60">sıralama</div>
              </div>
            </div>
          )}
        </div>

        {/* System Stats */}
        {systemStats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <StatsCard
              value={systemStats.database_size}
              label="Toplam Besin"
              color="text-violet-400"
            />
            <StatsCard
              value={systemStats.total_contributions}
              label="Katkı"
              color="text-emerald-400"
            />
            <StatsCard
              value={systemStats.total_users}
              label="Kullanıcı"
              color="text-blue-400"
            />
            <StatsCard
              value={systemStats.pending_verifications}
              label="Bekleyen"
              color="text-amber-400"
            />
          </div>
        )}

        {/* Tabs */}
        <div ref={tabsRef} className="flex gap-2 mb-4">
          {[
            { id: 'contribute', label: 'Besin Ekle', icon: Plus },
            { id: 'leaderboard', label: 'Liderlik', icon: Trophy },
            { id: 'missing', label: 'Eksikler', icon: Star },
            { id: 'stats', label: 'İstatistik', icon: TrendingUp }
          ].map(tab => (
            <MemoizedButton
              key={tab.id}
              onClick={() => handleTabChange(tab.id as any)}
              variant={activeTab === tab.id ? 'default' : 'outline'}
              size="sm"
              className="flex items-center gap-1"
              interactive
              intensity="medium"
            >
              <tab.icon size={14} />
              <span className="hidden sm:inline">{tab.label}</span>
            </MemoizedButton>
          ))}
        </div>
      </MemoizedGlassCard>

      {/* Tab Content */}
      {activeTab === 'contribute' && (
        <MemoizedGlassCard className="p-4" interactive intensity="subtle">
          <h4 className="text-md font-semibold text-white mb-4 flex items-center gap-2">
            <Plus size={18} />
            Yeni Besin Ekle
          </h4>
          
          <form ref={formRef} onSubmit={handleContribution} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <MemoizedInput
                  placeholder="Besin adı (örn: Ev yapımı mercimek çorbası)"
                  value={contributionForm.food_name}
                  onChange={(e) => {
                    setContributionForm(prev => ({ ...prev, food_name: e.target.value }))
                    validateFoodName(e.target.value)
                  }}
                  required
                  interactive
                  intensity="medium"
                />
                {formErrors.food_name && (
                  <p className="text-red-400 text-xs mt-1">{formErrors.food_name}</p>
                )}
              </div>
              
              <select
                className="w-full px-3 py-2 rounded-lg text-[13px] text-white/80 bg-white/[0.05] border border-white/[0.08] focus:outline-none focus:ring-1 focus:ring-violet-500/60 transition-colors"
                value={contributionForm.source}
                onChange={(e) => setContributionForm(prev => ({ ...prev, source: e.target.value as any }))}
              >
                <option value="homemade">Ev Yapımı</option>
                <option value="restaurant">Restoran</option>
                <option value="package">Paketli Ürün</option>
              </select>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <MemoizedInput
                  type="number"
                  placeholder="Kalori"
                  min="0"
                  max="900"
                  value={contributionForm.calories_per_100g || ''}
                  onChange={(e) => {
                    const value = Number(e.target.value)
                    setContributionForm(prev => ({ ...prev, calories_per_100g: value }))
                    validateNutrients(value, contributionForm.protein_per_100g, contributionForm.carbs_per_100g, contributionForm.fat_per_100g)
                  }}
                  required
                  interactive
                />
                {formErrors.calories && (
                  <p className="text-red-400 text-xs mt-1">{formErrors.calories}</p>
                )}
              </div>
              <div>
                <MemoizedInput
                  type="number"
                  placeholder="Protein (g)"
                  min="0"
                  max="100"
                  step="0.1"
                  value={contributionForm.protein_per_100g || ''}
                  onChange={(e) => {
                    const value = Number(e.target.value)
                    setContributionForm(prev => ({ ...prev, protein_per_100g: value }))
                    validateNutrients(contributionForm.calories_per_100g, value, contributionForm.carbs_per_100g, contributionForm.fat_per_100g)
                  }}
                  required
                  interactive
                />
                {formErrors.protein && (
                  <p className="text-red-400 text-xs mt-1">{formErrors.protein}</p>
                )}
              </div>
              <div>
                <MemoizedInput
                  type="number"
                  placeholder="Karbonhidrat (g)"
                  min="0"
                  max="100"
                  step="0.1"
                  value={contributionForm.carbs_per_100g || ''}
                  onChange={(e) => {
                    const value = Number(e.target.value)
                    setContributionForm(prev => ({ ...prev, carbs_per_100g: value }))
                    validateNutrients(contributionForm.calories_per_100g, contributionForm.protein_per_100g, value, contributionForm.fat_per_100g)
                  }}
                  required
                  interactive
                />
                {formErrors.carbs && (
                  <p className="text-red-400 text-xs mt-1">{formErrors.carbs}</p>
                )}
              </div>
              <div>
                <MemoizedInput
                  type="number"
                  placeholder="Yağ (g)"
                  min="0"
                  max="100"
                  step="0.1"
                  value={contributionForm.fat_per_100g || ''}
                  onChange={(e) => {
                    const value = Number(e.target.value)
                    setContributionForm(prev => ({ ...prev, fat_per_100g: value }))
                    validateNutrients(contributionForm.calories_per_100g, contributionForm.protein_per_100g, contributionForm.carbs_per_100g, value)
                  }}
                  required
                  interactive
                />
                {formErrors.fat && (
                  <p className="text-red-400 text-xs mt-1">{formErrors.fat}</p>
                )}
              </div>
            </div>

            {formErrors.total && (
              <div className="p-2 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <div className="flex items-center gap-2">
                  <AlertCircle className="text-amber-400" size={16} />
                  <p className="text-amber-400 text-sm">{formErrors.total}</p>
                </div>
              </div>
            )}

            {contributionForm.source === 'package' && (
              <MemoizedInput
                placeholder="Marka (opsiyonel)"
                value={contributionForm.brand || ''}
                onChange={(e) => setContributionForm(prev => ({ ...prev, brand: e.target.value }))}
                interactive
              />
            )}

            <MemoizedButton 
              type="submit" 
              disabled={loading || !isFormValid} 
              className="w-full"
              interactive
              intensity="strong"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin mr-2" size={16} />
                  Ekleniyor...
                </>
              ) : (
                '🍽️ Besin Ekle ve 10 Puan Kazan!'
              )}
            </MemoizedButton>
          </form>

          {/* Quick Suggestion */}
          <div className="mt-6 pt-4 border-t border-white/10">
            <h5 className="text-sm font-semibold text-white mb-2">Hızlı Öneri</h5>
            <form onSubmit={handleSuggestion} className="flex gap-2">
              <MemoizedInput
                placeholder="Eksik besin öner (örn: Adana kebap)"
                value={suggestionForm}
                onChange={(e) => setSuggestionForm(e.target.value)}
                className="flex-1"
                interactive
              />
              <MemoizedButton 
                type="submit" 
                disabled={loading || !suggestionForm.trim()} 
                size="sm"
                interactive
              >
                <Star size={14} />
              </MemoizedButton>
            </form>
          </div>
        </MemoizedGlassCard>
      )}

      {activeTab === 'leaderboard' && (
        <MemoizedGlassCard className="p-4" interactive intensity="subtle">
          <h4 className="text-md font-semibold text-white mb-4 flex items-center gap-2">
            <Trophy size={18} />
            Liderlik Tablosu
          </h4>
          
          <div className="space-y-3">
            {leaderboard.map((entry, index) => (
              <LeaderboardEntry
                key={entry.user_id}
                entry={entry}
                index={index}
                onEntryClick={(entry) => {
                  info(`Kullanıcı #${entry.user_id} - ${entry.total_points} puan`)
                }}
              />
            ))}
          </div>
        </MemoizedGlassCard>
      )}

      {activeTab === 'missing' && (
        <MemoizedGlassCard className="p-4" interactive intensity="subtle">
          <h4 className="text-md font-semibold text-white mb-4 flex items-center gap-2">
            <Star size={18} />
            En Çok İstenen Besinler
          </h4>
          
          <div className="space-y-2">
            {missingFoods.slice(0, 8).map((food, index) => (
              <MissingFoodItem
                key={index}
                food={food}
                onVote={handleVoteMissingFood}
              />
            ))}
          </div>
        </MemoizedGlassCard>
      )}

      {activeTab === 'stats' && userStats && (
        <MemoizedGlassCard className="p-4" interactive intensity="subtle">
          <h4 className="text-md font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp size={18} />
            Kişisel İstatistikler
          </h4>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <StatsCard
              value={userStats.contributions}
              label="Katkı"
              color="text-violet-400"
              icon={<Plus size={16} className="text-violet-400" />}
            />
            <StatsCard
              value={userStats.verifications}
              label="Doğrulama"
              color="text-emerald-400"
              icon={<CheckCircle size={16} className="text-emerald-400" />}
            />
            <StatsCard
              value={userStats.suggestions}
              label="Öneri"
              color="text-blue-400"
              icon={<Star size={16} className="text-blue-400" />}
            />
            <StatsCard
              value={userStats.level}
              label="Seviye"
              color={getLevelColor(userStats.level)}
              icon={<Award size={16} className={getLevelColor(userStats.level)} />}
            />
          </div>

          {/* Badges */}
          {userStats.badges.length > 0 && (
            <div>
              <h5 className="text-sm font-semibold text-white mb-2">Rozetler</h5>
              <div className="flex flex-wrap gap-2">
                {userStats.badges.map((badge, index) => (
                  <div key={index} className="flex items-center gap-1 px-2 py-1 bg-white/10 rounded-full text-xs hover:bg-white/15 transition-colors duration-200">
                    <span>{getBadgeEmoji(badge)}</span>
                    <span className="text-white/80">{badge}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Daily Challenges */}
          {dailyChallenges.length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <h5 className="text-sm font-semibold text-white mb-2 flex items-center gap-1">
                <Target size={14} />
                Günlük Görevler
              </h5>
              <div className="space-y-2">
                {dailyChallenges.slice(0, 2).map((challenge, index) => (
                  <div key={index} className="p-2 bg-white/5 rounded-lg hover:bg-white/8 transition-colors duration-200">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-white">{challenge.description}</span>
                      <div className="flex items-center gap-1 text-xs text-amber-400">
                        <Zap size={12} />
                        {challenge.reward_points}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </MemoizedGlassCard>
      )}

      {error && (
        <MemoizedGlassCard className="p-3 bg-red-500/10 border border-red-500/20" noblur>
          <div className="flex items-center gap-2">
            <AlertCircle className="text-red-400" size={16} />
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        </MemoizedGlassCard>
      )}
    </div>
  )
}