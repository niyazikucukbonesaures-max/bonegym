import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { measurementsApi, type MeasurementCreate, type Measurement, type MeasurementDelta } from '@/lib/api'

export function useMeasurements() {
  return useQuery<Measurement[]>({
    queryKey: ['measurements'],
    queryFn: () => measurementsApi.getHistory().then(r => r.data),
  })
}

export function useAddMeasurement() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: MeasurementCreate) => measurementsApi.add(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['measurements'] })
      queryClient.invalidateQueries({ queryKey: ['measurementTrend'] })
      queryClient.invalidateQueries({ queryKey: ['measurementDelta'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: (error: any) => {
      console.error('Ölçüm eklenirken hata:', error?.response?.data || error.message)
    }
  })
}
export function useDeleteMeasurement() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => measurementsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['measurements'] })
      queryClient.invalidateQueries({ queryKey: ['measurementTrend'] })
      queryClient.invalidateQueries({ queryKey: ['measurementDelta'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useMeasurementTrend(days?: number) {
  return useQuery<Measurement[]>({
    queryKey: ['measurementTrend', days],
    queryFn: () => measurementsApi.getTrend(days).then(r => r.data),
  })
}

export function useMeasurementDelta() {
  return useQuery<MeasurementDelta>({
    queryKey: ['measurementDelta'],
    queryFn: () => measurementsApi.getDelta().then(r => r.data),
  })
}
