import { useQuery } from '@tanstack/react-query'
import { dashboardApi, type DashboardSnapshot } from '@/lib/api'

export function useDashboard() {
  return useQuery<DashboardSnapshot>({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const response = await dashboardApi.get()
      return response.data
    },
    staleTime: 0,                    // Her zaman stale say — profil değişince anında güncelle
    gcTime: 5 * 60 * 1000,          // 5 dakika bellekte tut
    refetchOnMount: true,            // Mount'ta her zaman fetch et
    refetchOnWindowFocus: true,      // Pencere odaklandığında fetch et
    refetchOnReconnect: true,
    retry: 2,
    retryDelay: 1000,
  })
}
