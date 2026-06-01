/**
 * Mevcut kullanıcının ID'sini döndürür.
 * Auth varsa token'dan alır, yoksa 1 döndürür (geriye dönük uyumluluk).
 */
import { useAuth } from '@/contexts/AuthContext'

export function useCurrentUserId(): number {
  const { user } = useAuth()
  return user?.id ?? 1
}
