import { useState } from 'react'
import { Plus, Dumbbell, Clock, Trash2 } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { AICoachWidget } from '@/components/AICoachWidget'
import { useWorkoutPrograms, useCreateWorkoutProgram, useLogWorkout, useWorkoutHistory, useDeleteWorkoutProgram, useDeleteWorkoutLog } from '@/hooks/useWorkouts'
import { format } from 'date-fns'
import { tr } from 'date-fns/locale'

export default function Workouts() {
  const [showProgramForm, setShowProgramForm] = useState(false)
  const [showLogForm, setShowLogForm] = useState(false)
  const [programName, setProgramName] = useState('')
  const [selectedProgram, setSelectedProgram] = useState<any>(null)
  const [duration, setDuration] = useState('')

  const { data: programs } = useWorkoutPrograms()
  const { data: history } = useWorkoutHistory(12)
  const createProgramMutation = useCreateWorkoutProgram()
  const logWorkoutMutation = useLogWorkout()
  const deleteProgramMutation = useDeleteWorkoutProgram()
  const deleteWorkoutLogMutation = useDeleteWorkoutLog()

  const handleCreateProgram = () => {
    if (!programName) return
    createProgramMutation.mutate({ name: programName }, {
      onSuccess: () => { setProgramName(''); setShowProgramForm(false) }
    })
  }

  const handleLogWorkout = () => {
    if (!selectedProgram || !duration) return
    logWorkoutMutation.mutate({
      program_id: selectedProgram.id,
      program_name: selectedProgram.name,
      duration_minutes: parseInt(duration),
    }, {
      onSuccess: () => { setSelectedProgram(null); setDuration(''); setShowLogForm(false) }
    })
  }

  return (
    <div className="p-5 space-y-4 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-white">Antrenman</h1>
          <p className="text-[12px] text-white/35 mt-0.5">Programlar ve antrenman takibi</p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" onClick={() => setShowProgramForm(v => !v)}>
            <Plus className="w-3.5 h-3.5" />
            Program
          </Button>
          <Button size="sm" variant="outline" onClick={() => setShowLogForm(v => !v)}>
            <Dumbbell className="w-3.5 h-3.5" />
            Kaydet
          </Button>
        </div>
      </div>

      {/* AI Koç */}
      <AICoachWidget />

      {/* Program formu */}
      {showProgramForm && (
        <GlassCard className="p-4">
          <h3 className="text-[13px] font-semibold text-white mb-3">Yeni Program</h3>
          <div className="flex gap-2">
            <Input placeholder="Program adı (örn: Push Day)" value={programName} onChange={e => setProgramName(e.target.value)} className="flex-1" />
            <Button onClick={handleCreateProgram} disabled={!programName || createProgramMutation.isPending} size="sm">Oluştur</Button>
          </div>
        </GlassCard>
      )}

      {/* Antrenman kayıt formu */}
      {showLogForm && (
        <GlassCard className="p-4">
          <h3 className="text-[13px] font-semibold text-white mb-3">Antrenman Kaydet</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="text-[11px] text-white/40 mb-1.5 block uppercase tracking-wide">Program</label>
              <select
                value={selectedProgram?.id || ''}
                onChange={e => setSelectedProgram(programs?.find(p => p.id === parseInt(e.target.value)))}
                className="w-full rounded-lg px-3 py-2 text-[13px] text-white/80 bg-white/[0.05] border border-white/[0.08] focus:outline-none focus:ring-1 focus:ring-violet-500/60"
              >
                <option value="">Seçiniz</option>
                {programs?.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[11px] text-white/40 mb-1.5 block uppercase tracking-wide">Süre (dk)</label>
              <Input type="number" placeholder="60" value={duration} onChange={e => setDuration(e.target.value)} />
            </div>
            <div className="flex items-end">
              <Button onClick={handleLogWorkout} disabled={!selectedProgram || !duration || logWorkoutMutation.isPending} className="w-full" size="sm">
                Kaydet
              </Button>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Programlar */}
      <div>
        <h2 className="text-[13px] font-semibold text-white mb-3">Programlarım</h2>
        {!programs?.length ? (
          <div className="rounded-xl border border-white/[0.07] bg-[#13131a] p-6 text-center">
            <Dumbbell className="w-7 h-7 text-white/15 mx-auto mb-2" />
            <p className="text-[13px] text-white/30">Henüz program yok</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {programs.map(program => (
              <div key={program.id} className="rounded-xl border border-white/[0.07] bg-[#13131a] p-4 flex items-center gap-3 group hover:border-white/[0.12] transition-colors">
                <div className="w-9 h-9 rounded-lg bg-violet-600/15 flex items-center justify-center shrink-0">
                  <Dumbbell className="w-4 h-4 text-violet-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] text-white/80 font-medium truncate">{program.name}</p>
                  <p className="text-[11px] text-white/30">{program.exercises?.length ?? 0} egzersiz</p>
                </div>
                <button
                  onClick={() => { if (confirm(`"${program.name}" silinsin mi?`)) deleteProgramMutation.mutate(program.id) }}
                  className="opacity-0 group-hover:opacity-100 p-1.5 rounded text-white/25 hover:text-red-400 hover:bg-red-500/10 transition-all"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Geçmiş */}
      <GlassCard className="p-5">
        <h2 className="text-[13px] font-semibold text-white mb-4">Son Antrenmanlar</h2>
        {!history?.length ? (
          <div className="text-center py-6">
            <p className="text-[13px] text-white/30">Henüz antrenman kaydı yok</p>
          </div>
        ) : (
          <div className="space-y-1.5">
            {history.map(log => (
              <div key={log.id} className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.05] transition-colors group">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-violet-600/10 flex items-center justify-center">
                    <Dumbbell className="w-3.5 h-3.5 text-violet-400" />
                  </div>
                  <div>
                    <p className="text-[13px] text-white/80 font-medium">{log.program_name}</p>
                    <p className="text-[11px] text-white/30">{format(new Date(log.completed_at), 'dd MMM yyyy', { locale: tr })}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1 text-[12px] text-white/35">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{log.duration_minutes} dk</span>
                  </div>
                  <button
                    onClick={() => { if (confirm('Silinsin mi?')) deleteWorkoutLogMutation.mutate(log.id) }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded text-white/25 hover:text-red-400 hover:bg-red-500/10 transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  )
}
