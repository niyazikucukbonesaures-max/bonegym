import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workoutsApi, type WorkoutProgramCreate, type WorkoutLogCreate, type WorkoutProgram, type WorkoutLog, type WeeklyWorkoutStats } from '@/lib/api'

export function useWorkoutPrograms() {
  return useQuery<WorkoutProgram[]>({
    queryKey: ['workoutPrograms'],
    queryFn: () => workoutsApi.listPrograms().then(r => r.data),
  })
}

export function useCreateWorkoutProgram() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: WorkoutProgramCreate) => workoutsApi.createProgram(data).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workoutPrograms'] })
    },
  })
}

export function useDeleteWorkoutProgram() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => workoutsApi.deleteProgram(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workoutPrograms'] })
    },
  })
}

export function useLogWorkout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: WorkoutLogCreate) => workoutsApi.logWorkout(data).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workoutHistory'] })
      queryClient.invalidateQueries({ queryKey: ['weeklyStats'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useDeleteWorkoutLog() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => workoutsApi.deleteWorkoutLog(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workoutHistory'] })
      queryClient.invalidateQueries({ queryKey: ['weeklyStats'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useWorkoutHistory(weeks?: number) {
  return useQuery<WorkoutLog[]>({
    queryKey: ['workoutHistory', weeks],
    queryFn: () => workoutsApi.getHistory(weeks).then(r => r.data),
  })
}

export function useExerciseProgress(exerciseName: string) {
  return useQuery({
    queryKey: ['exerciseProgress', exerciseName],
    queryFn: () => workoutsApi.getProgress(exerciseName).then(r => r.data),
    enabled: exerciseName.trim().length > 0,
  })
}

export function useWeeklyStats() {
  return useQuery<WeeklyWorkoutStats>({
    queryKey: ['weeklyStats'],
    queryFn: () => workoutsApi.getStats().then(r => r.data),
  })
}
