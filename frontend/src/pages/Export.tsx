import { useState } from 'react'
import { Download, FileText } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { exportApi } from '@/lib/api'
import { format } from 'date-fns'

export default function Export() {
  const [exportType, setExportType] = useState('calories')
  const [fromDate, setFromDate] = useState(format(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'))
  const [toDate, setToDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [loading, setLoading] = useState(false)

  const handleExport = async () => {
    setLoading(true)
    try {
      const response = await exportApi.export(exportType, fromDate, toDate)
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${exportType}_${fromDate}_${toDate}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-white">Veri Dışa Aktar</h1>

      <GlassCard className="p-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 shrink-0">
            <FileText className="text-white" size={24} />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">CSV Dışa Aktarma</h2>
            <p className="text-sm text-white/60 mt-1">
              Verilerinizi CSV formatında indirin ve Excel'de açın
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-sm text-white/60 mb-1 block">Veri Tipi</label>
            <select
              value={exportType}
              onChange={(e) => setExportType(e.target.value)}
              className="w-full rounded-lg px-3 py-2 text-[13px] text-white/80 bg-white/[0.05] border border-white/[0.08] focus:outline-none focus:ring-1 focus:ring-violet-500/60"
            >
              <option value="calories">Kalori Günlüğü</option>
              <option value="measurements">Ölçümler</option>
              <option value="workouts">Antrenmanlar</option>
            </select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-white/60 mb-1 block">Başlangıç Tarihi</label>
              <Input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm text-white/60 mb-1 block">Bitiş Tarihi</label>
              <Input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
              />
            </div>
          </div>

          <Button onClick={handleExport} disabled={loading} className="w-full">
            <Download size={18} className="mr-2" />
            {loading ? 'İndiriliyor...' : 'CSV İndir'}
          </Button>
        </div>
      </GlassCard>

      <GlassCard className="p-6">
        <h3 className="text-lg font-semibold text-white mb-3">Dışa Aktarma Hakkında</h3>
        <ul className="space-y-2 text-sm text-white/60">
          <li>• CSV dosyaları Excel, Google Sheets ve diğer tablolama programlarında açılabilir</li>
          <li>• Kalori günlüğü: Tüm besin kayıtlarınız ve makro değerleri</li>
          <li>• Ölçümler: Kilo ve vücut ölçümü geçmişi</li>
          <li>• Antrenmanlar: Tüm antrenman kayıtlarınız ve süreleri</li>
          <li>• Tarih aralığı seçerek istediğiniz dönemi filtreleyebilirsiniz</li>
        </ul>
      </GlassCard>
    </div>
  )
}
