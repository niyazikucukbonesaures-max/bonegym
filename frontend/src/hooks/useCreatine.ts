import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { creatineApi, type CreatineDoseCreate, type TodayCreatineStatus, type CreatineDose } from '@/lib/api'

export function useCreatineStatus() {
  return useQuery<TodayCreatineStatus>({
    queryKey: ['creatineStatus'],
    queryFn: () => creatineApi.getStatus().then(r => r.data),
  })
}

export function useLogCreatineDose() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreatineDoseCreate) => creatineApi.logDose(data).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['creatineStatus'] })
      queryClient.invalidateQueries({ queryKey: ['creatineHistory'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useDeleteCreatineDose() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => creatineApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['creatineStatus'] })
      queryClient.invalidateQueries({ queryKey: ['creatineHistory'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useCreatineHistory(days?: number) {
  return useQuery<CreatineDose[]>({
    queryKey: ['creatineHistory', days],
    queryFn: () => creatineApi.getHistory(days).then(r => r.data),
  })
}
