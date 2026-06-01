import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import api, { setupInterceptors } from '@/lib/api'

interface User {
  id: number
  email: string
  username: string
  full_name: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  last_login?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, fullName: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false) // FALSE - hızlı başlat

  // Initialize axios interceptors on mount
  useEffect(() => {
    setupInterceptors()
  }, [])

  // Token'ı localStorage'dan yükle - BASİTLEŞTİRİLDİ
  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token')
    
    if (savedToken && savedToken !== 'fake-admin-token') {
      setToken(savedToken)
      api.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
      fetchUser()
    }
  }, [])

  const fetchUser = async () => {
    try {
      const response = await api.get('/api/auth/me')
      setUser(response.data)
    } catch (error) {
      console.error('Kullanıcı bilgileri alınamadı:', error)
      // Token geçersizse temizle
      localStorage.removeItem('auth_token')
      setToken(null)
      setUser(null)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const response = await api.post('/api/auth/login', { email, password })
      const { access_token, user: userData } = response.data
      
      setToken(access_token)
      setUser(userData)
      
      // Token'ı kaydet
      localStorage.setItem('auth_token', access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Giriş başarısız')
    }
  }

  const register = async (email: string, username: string, fullName: string, password: string) => {
    try {
      const response = await api.post('/api/auth/register', {
        email,
        username,
        full_name: fullName,
        password
      })
      const { access_token, user: userData } = response.data
      
      setToken(access_token)
      setUser(userData)
      
      // Token'ı kaydet
      localStorage.setItem('auth_token', access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Kayıt başarısız')
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('auth_token')
    delete api.defaults.headers.common['Authorization']
    
    // Backend'e logout isteği gönder (opsiyonel)
    if (token) {
      api.post('/api/auth/logout').catch(() => {
        // Hata olsa da devam et
      })
    }
  }

  const value = {
    user,
    token,
    login,
    register,
    logout,
    isLoading
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}