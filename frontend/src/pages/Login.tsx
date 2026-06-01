import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mail, Lock, User, Eye, EyeOff, Activity, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const [isLogin, setIsLogin] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState({ email: '', username: '', fullName: '', password: '' })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const { login, register, token, isLoading: authLoading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (token && !authLoading) navigate('/dashboard')
  }, [token, authLoading, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      if (isLogin) {
        await login(formData.email, formData.password)
      } else {
        await register(formData.email, formData.username, formData.fullName, formData.password)
      }
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Bilgilerinizi kontrol edin.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))

  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex">
      {/* Sol panel - sadece desktop */}
      <div className="hidden lg:flex flex-col justify-between w-[420px] shrink-0 bg-[#0d0d14] border-r border-white/[0.06] p-10">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <span className="text-[15px] font-semibold text-white">FitnessPro</span>
        </div>

        <div>
          <h2 className="text-2xl font-bold text-white mb-3 leading-snug">
            Fitness hedeflerine<br />ulaşmanın en kolay yolu
          </h2>
          <p className="text-white/40 text-[14px] leading-relaxed">
            Kalori takibi, antrenman planlaması ve ilerleme analizi — hepsi tek bir yerde.
          </p>

          <div className="mt-8 space-y-3">
            {[
              'Günlük kalori ve makro takibi',
              'AI destekli antrenman koçu',
              'Kilo ve ölçüm analizi',
              'Akıllı bildirim sistemi',
            ].map(item => (
              <div key={item} className="flex items-center gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-violet-500" />
                <span className="text-[13px] text-white/50">{item}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="text-[11px] text-white/20">© 2025 FitnessPro</p>
      </div>

      {/* Sağ panel - form */}
      <div className="flex-1 flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="w-full max-w-sm"
        >
          {/* Mobil logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-7 h-7 rounded-lg bg-violet-600 flex items-center justify-center">
              <Activity className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-[14px] font-semibold text-white">FitnessPro</span>
          </div>

          <div className="mb-7">
            <h1 className="text-xl font-bold text-white">
              {isLogin ? 'Giriş yap' : 'Hesap oluştur'}
            </h1>
            <p className="text-[13px] text-white/35 mt-1">
              {isLogin ? 'Hesabınıza erişin' : 'Ücretsiz başlayın'}
            </p>
          </div>

          {/* Hızlı giriş */}
          {isLogin && (
            <button
              type="button"
              onClick={() => setFormData(p => ({ ...p, email: 'admin@fitness.com', password: 'admin123' }))}
              className="w-full mb-4 px-3 py-2.5 rounded-lg border border-violet-500/20 bg-violet-500/10 text-violet-300 text-[12px] font-medium hover:bg-violet-500/15 transition-colors text-left"
            >
              Demo hesabıyla dene →
            </button>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="px-3 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-[12px]"
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-white/25 w-4 h-4" />
              <Input name="email" type="email" placeholder="E-posta" value={formData.email} onChange={handleChange} className="pl-9" required />
            </div>

            {!isLogin && (
              <>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 text-white/25 w-4 h-4" />
                  <Input name="username" type="text" placeholder="Kullanıcı adı" value={formData.username} onChange={handleChange} className="pl-9" required />
                </div>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 text-white/25 w-4 h-4" />
                  <Input name="fullName" type="text" placeholder="Ad Soyad" value={formData.fullName} onChange={handleChange} className="pl-9" required />
                </div>
              </>
            )}

            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-white/25 w-4 h-4" />
              <Input name="password" type={showPassword ? 'text' : 'password'} placeholder="Şifre" value={formData.password} onChange={handleChange} className="pl-9 pr-9" required />
              <button type="button" onClick={() => setShowPassword(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/25 hover:text-white/50 transition-colors">
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            <Button type="submit" disabled={isLoading} className="w-full mt-1 h-10">
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Yükleniyor...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  {isLogin ? 'Giriş Yap' : 'Kayıt Ol'}
                  <ArrowRight className="w-4 h-4" />
                </span>
              )}
            </Button>
          </form>

          <p className="mt-5 text-center text-[12px] text-white/30">
            {isLogin ? 'Hesabınız yok mu?' : 'Zaten hesabınız var mı?'}{' '}
            <button
              onClick={() => { setIsLogin(v => !v); setError(''); setFormData({ email: '', username: '', fullName: '', password: '' }) }}
              className="text-violet-400 hover:text-violet-300 transition-colors font-medium"
            >
              {isLogin ? 'Kayıt olun' : 'Giriş yapın'}
            </button>
          </p>
        </motion.div>
      </div>
    </div>
  )
}
