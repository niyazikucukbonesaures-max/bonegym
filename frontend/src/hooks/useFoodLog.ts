import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { logApi, foodsApi, type FoodLogCreate, type DailySummary, type FoodItem } from '@/lib/api'

export function useFoodLog(date: string) {
  return useQuery<DailySummary>({
    queryKey: ['foodLog', date],
    queryFn: () => logApi.getDaily(date).then(r => r.data),
    staleTime: 60 * 1000,       // 1 dakika — kalori günlüğü sık değişir
    gcTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  })
}

export function useAddFoodLog() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (entry: FoodLogCreate) => logApi.add(entry).then(r => r.data),
    onSuccess: () => {
      // Sadece ilgili cache'leri temizle
      queryClient.invalidateQueries({ queryKey: ['foodLog'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useDeleteFoodLog() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => logApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['foodLog'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useFoodSearch(q: string) {
  return useQuery<FoodItem[]>({
    queryKey: ['foodSearch', q],
    queryFn: () => foodsApi.search(q).then(r => r.data),
    enabled: q.trim().length >= 2,
    staleTime: 24 * 60 * 60 * 1000,  // 24 saat — besin DB nadiren değişir
    gcTime: 48 * 60 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
  })
}
