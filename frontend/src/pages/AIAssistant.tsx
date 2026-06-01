import { useState, useEffect, useRef, memo } from 'react'
import { Bot, Send, Loader2, AlertCircle, Plus, Users } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { CommunitySection } from '@/components/CommunitySection'
import { SkeletonLoader, TextSkeleton } from '@/components/ui/SkeletonLoader'
import { aiAssistantApi, type ChatMessage, type NutritionData } from '@/lib/api'
import { logApi } from '@/lib/api'
import { useNotifications } from '@/hooks/useNotifications'
import { usePerformanceMonitor } from '@/hooks/usePerformanceMonitor'
import { useAnimation } from '@/contexts/AnimationContext'
import { useCurrentUserId } from '@/hooks/useCurrentUserId'

// Memoized bileşenler
const MemoizedGlassCard = memo(GlassCard)
const MemoizedButton = memo(Button)
const MemoizedInput = memo(Input)

interface MessageBubbleProps {
  message: ChatMessage
  onAddToLog?: (nutrition: NutritionData, grams: number, mealType: string) => void
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onAddToLog }) => {
  const isUser = message.type === 'user'
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        {!isUser && (
          <div className="flex items-center gap-2 mb-2">
            <Bot className="text-violet-400" size={16} />
            <span className="text-xs text-white/60">AI Besin Asistanı</span>
          </div>
        )}
        
        <MemoizedGlassCard 
          className={`p-3 ${
            isUser 
              ? 'bg-violet-500/20 border-violet-500/30' 
              : 'bg-white/10 border-white/20'
          }`}
          noblur
          interactive
          intensity="subtle"
        >
          <div className="text-sm text-white whitespace-pre-wrap">
            {message.content
              .split('<!--')[0]           // Eski web scraping JSON yorumunu kaldır
              .replace(/```json[\s\S]*?```/g, '')  // Gemini JSON bloklarını kaldır
              .replace(/```[\s\S]*?```/g, '')       // Diğer kod bloklarını kaldır
              .trim()}
          </div>
          
          {message.nutrition_data && (
            <NutritionCard 
              nutrition={message.nutrition_data} 
              onAddToLog={onAddToLog}
              showAddButton={true}
            />
          )}
        </MemoizedGlassCard>
        
        <div className="text-xs text-white/40 mt-1 px-2">
          {new Date(message.timestamp).toLocaleTimeString('tr-TR', {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>
    </div>
  )
}

interface NutritionCardProps {
  nutrition: NutritionData
  onAddToLog?: (nutrition: NutritionData, grams: number, mealType: string) => void
  showAddButton: boolean
}

const NutritionCard: React.FC<NutritionCardProps> = ({ 
  nutrition, 
  onAddToLog, 
  showAddButton 
}) => {
  const [isAdding, setIsAdding] = useState(false)
  const [grams, setGrams] = useState('100')
  const [mealType, setMealType] = useState('snack')
  
  const gramsNum = parseFloat(grams) || 100
  const preview = {
    calories: Math.round(nutrition.calories_per_100g * gramsNum / 100),
    protein: Math.round(nutrition.protein_per_100g * gramsNum / 100 * 10) / 10,
    carbs: Math.round(nutrition.carbs_per_100g * gramsNum / 100 * 10) / 10,
    fat: Math.round(nutrition.fat_per_100g * gramsNum / 100 * 10) / 10,
  }
  
  const handleAddToLog = async () => {
    if (!onAddToLog) return
    
    setIsAdding(true)
    try {
      await onAddToLog(nutrition, gramsNum, mealType)
    } finally {
      setIsAdding(false)
    }
  }
  
  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high': return 'text-green-400'
      case 'medium': return 'text-yellow-400'
      case 'low': return 'text-red-400'
      default: return 'text-white/60'
    }
  }
  
  const getConfidenceText = (confidence: string) => {
    switch (confidence) {
      case 'high': return 'Yüksek Güven'
      case 'medium': return 'Orta Güven'
      case 'low': return 'Düşük Güven'
      default: return 'Bilinmiyor'
    }
  }
  
  return (
    <div className="mt-3 p-3 bg-white/5 rounded-lg border border-white/10">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-white">{nutrition.food_name}</h4>
        <span className={`text-xs ${getConfidenceColor(nutrition.confidence)}`}>
          {getConfidenceText(nutrition.confidence)}
        </span>
      </div>
      
      {/* 100g başına değerler */}
      <p className="text-[10px] text-white/40 mb-2">100g başına değerler</p>
      <div className="grid grid-cols-4 gap-2 mb-3">
        <div className="text-center">
          <p className="text-xs text-white/60">Kalori</p>
          <p className="text-sm font-semibold text-white">{nutrition.calories_per_100g}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-white/60">Protein</p>
          <p className="text-sm font-semibold text-emerald-400">{nutrition.protein_per_100g}g</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-white/60">Karb</p>
          <p className="text-sm font-semibold text-blue-400">{nutrition.carbs_per_100g}g</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-white/60">Yağ</p>
          <p className="text-sm font-semibold text-amber-400">{nutrition.fat_per_100g}g</p>
        </div>
      </div>
      
      {showAddButton && onAddToLog && (
        <>
          {/* Gram ve öğün seçimi */}
          <div className="grid grid-cols-2 gap-2 mb-2">
            <div>
              <label className="text-[10px] text-white/40 mb-1 block uppercase tracking-wide">Gram</label>
              <input
                type="number"
                value={grams}
                onChange={e => setGrams(e.target.value)}
                min={1}
                max={2000}
                className="w-full rounded-md px-2 py-1.5 text-xs text-white bg-white/[0.07] border border-white/[0.12] focus:outline-none focus:ring-1 focus:ring-violet-500/60"
              />
            </div>
            <div>
              <label className="text-[10px] text-white/40 mb-1 block uppercase tracking-wide">Öğün</label>
              <select
                value={mealType}
                onChange={e => setMealType(e.target.value)}
                className="w-full rounded-md px-2 py-1.5 text-xs text-white bg-white/[0.07] border border-white/[0.12] focus:outline-none focus:ring-1 focus:ring-violet-500/60"
              >
                <option value="breakfast">Kahvaltı</option>
                <option value="lunch">Öğle</option>
                <option value="dinner">Akşam</option>
                <option value="snack">Ara Öğün</option>
              </select>
            </div>
          </div>

          {/* Seçilen gram için önizleme */}
          {gramsNum > 0 && gramsNum !== 100 && (
            <div className="grid grid-cols-4 gap-1 mb-2 p-2 rounded-md bg-violet-500/10 border border-violet-500/20">
              <div className="text-center">
                <p className="text-[9px] text-white/40">{gramsNum}g kalori</p>
                <p className="text-xs font-semibold text-white">{preview.calories}</p>
              </div>
              <div className="text-center">
                <p className="text-[9px] text-white/40">Protein</p>
                <p className="text-xs font-semibold text-emerald-400">{preview.protein}g</p>
              </div>
              <div className="text-center">
                <p className="text-[9px] text-white/40">Karb</p>
                <p className="text-xs font-semibold text-blue-400">{preview.carbs}g</p>
              </div>
              <div className="text-center">
                <p className="text-[9px] text-white/40">Yağ</p>
                <p className="text-xs font-semibold text-amber-400">{preview.fat}g</p>
              </div>
            </div>
          )}

          <MemoizedButton
            onClick={handleAddToLog}
            disabled={isAdding || !grams || gramsNum <= 0}
            className="w-full text-xs"
            size="sm"
          >
            {isAdding ? (
              <>
                <Loader2 className="animate-spin mr-2" size={14} />
                Ekleniyor...
              </>
            ) : (
              <>
                <Plus className="mr-2" size={14} />
                {gramsNum}g Kalori Günlüğüne Ekle
              </>
            )}
          </MemoizedButton>
        </>
      )}
    </div>
  )
}

export default function AIAssistant() {
  const navigate = useNavigate()
  const userId = useCurrentUserId()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionId] = useState(() => `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`)
  const [showCommunity, setShowCommunity] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  
  // UX Enhancement hooks
  const { success, error: showError } = useNotifications()
  const { measureRender } = usePerformanceMonitor({
    componentName: 'AIAssistant',
    trackRenderTime: true
  })
  const { isReducedMotion } = useAnimation()
  
  // Otomatik scroll
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: isReducedMotion ? 'auto' : 'smooth' })
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  // Sayfa yüklendiğinde input'a focus
  useEffect(() => {
    inputRef.current?.focus()
  }, [])
  
  // Hoş geldin mesajı
  useEffect(() => {
    const welcomeMessage: ChatMessage = {
      id: 'welcome',
      type: 'assistant',
      content: `Merhaba! Ben AI Besin Asistanınızım. 🤖

Size besin değerleri hakkında yardımcı olabilirim. Örneğin:

• "Tavuk göğsü besin değerleri nedir?"
• "100 gram pirinç pilavı kaç kalori?"
• "Mercimek çorbası protein miktarı?"

Hangi besin hakkında bilgi almak istiyorsunuz?`,
      timestamp: new Date().toISOString()
    }
    
    setMessages([welcomeMessage])
  }, [])
  
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return
    
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString()
    }
    
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await measureRender(async () => {
        return await aiAssistantApi.chat({
          message: userMessage.content,
          session_id: sessionId,
          user_id: userId
        })
      })
      
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: response.data.response,
        timestamp: response.data.timestamp,
        nutrition_data: response.data.nutrition_data
      }
      
      setMessages(prev => [...prev, assistantMessage])
      
      if (response.data.error) {
        setError(response.data.error)
        showError('AI yanıtında hata oluştu')
      }
      
    } catch (err: any) {
      console.error('AI chat error:', err)
      setError('Bağlantı hatası. Lütfen tekrar deneyin.')
      showError('Bağlantı hatası oluştu')
      
      // Hata mesajı ekle
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        type: 'assistant',
        content: 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.',
        timestamp: new Date().toISOString()
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }
  
  const handleAddToLog = async (nutrition: NutritionData, grams: number, mealType: string) => {
    try {
      const today = new Date().toISOString().split('T')[0]
      await logApi.add({
        user_id: userId,
        food_name: nutrition.food_name,
        grams,
        meal_type: mealType,
        logged_at: `${today}T12:00:00`,
        // AI'dan gelen makro değerlerini gönder — backend bunları kullanarak hesaplar
        calories_per_100g: nutrition.calories_per_100g,
        protein_per_100g: nutrition.protein_per_100g,
        carbs_per_100g: nutrition.carbs_per_100g,
        fat_per_100g: nutrition.fat_per_100g,
      })
      
      success(`${nutrition.food_name} (${grams}g) kalori günlüğüne eklendi!`)
      
      navigate('/food-log', { 
        state: { 
          message: `${nutrition.food_name} kalori günlüğüne eklendi!` 
        }
      })
      
    } catch (error) {
      console.error('Add to log error:', error)
      setError('Kalori günlüğüne eklenirken hata oluştu.')
      showError('Kalori günlüğüne eklenirken hata oluştu')
    }
  }
  
  return (
    <div className="flex flex-col lg:flex-row gap-4 h-[calc(100vh-120px)] max-w-7xl mx-auto">
      {/* Main Chat Area */}
      <div className={`flex flex-col ${showCommunity ? 'lg:w-2/3' : 'w-full'} transition-all duration-300`}>
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Bot className="text-violet-400" size={32} />
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-white">AI Besin Asistanı</h1>
              <p className="text-sm text-white/60">Besin değerleri hakkında sorularınızı sorun</p>
            </div>
          </div>
          
          <Button
            onClick={() => setShowCommunity(!showCommunity)}
            variant={showCommunity ? 'default' : 'outline'}
            className="flex items-center gap-2"
          >
            <Users size={18} />
            <span className="hidden sm:inline">Topluluk</span>
          </Button>
        </div>
        
        {/* Error Banner */}
        {error && (
          <MemoizedGlassCard className="p-3 mb-4 bg-red-500/10 border border-red-500/20" noblur>
            <div className="flex items-center gap-2">
              <AlertCircle className="text-red-400" size={16} />
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          </MemoizedGlassCard>
        )}
        
        {/* Chat Messages */}
        <MemoizedGlassCard className="flex-1 p-4 mb-4 overflow-hidden">
          <div className="h-full overflow-y-auto pr-2 space-y-1">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onAddToLog={handleAddToLog}
              />
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="max-w-[80%]">
                  <div className="flex items-center gap-2 mb-2">
                    <Bot className="text-violet-400" size={16} />
                    <span className="text-xs text-white/60">AI Besin Asistanı</span>
                  </div>
                  <MemoizedGlassCard className="p-3 bg-white/10 border-white/20" noblur>
                    <div className="flex items-center gap-2 text-white/60">
                      <Loader2 className="animate-spin" size={16} />
                      <span className="text-sm">Düşünüyor...</span>
                    </div>
                  </MemoizedGlassCard>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </MemoizedGlassCard>
        
        {/* Input Area */}
        <MemoizedGlassCard className="p-4">
          <div className="flex gap-2">
            <MemoizedInput
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Besin hakkında soru sorun... (örn: tavuk göğsü besin değerleri)"
              className="flex-1"
              disabled={isLoading}
            />
            <MemoizedButton
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="px-4"
            >
              {isLoading ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                <Send size={18} />
              )}
            </MemoizedButton>
          </div>
          
          <div className="mt-2 text-xs text-white/40 text-center">
            AI asistanı bazen hatalı bilgi verebilir. Önemli kararlar için doğrulama yapın.
          </div>
        </MemoizedGlassCard>
      </div>

      {/* Community Sidebar */}
      {showCommunity && (
        <div className="lg:w-1/3 transition-all duration-300">
          <CommunitySection />
        </div>
      )}
    </div>
  )
}