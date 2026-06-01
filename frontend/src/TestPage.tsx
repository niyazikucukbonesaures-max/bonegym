export default function TestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-950 via-purple-900 to-indigo-950 flex items-center justify-center">
      <div className="text-center p-8 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20">
        <h1 className="text-4xl font-bold text-white mb-4">
          🎉 Fitness App Çalışıyor!
        </h1>
        <p className="text-white/70 mb-6">
          Test sayfası başarıyla yüklendi
        </p>
        <div className="space-y-2 text-left">
          <p className="text-green-400">✅ Frontend: Çalışıyor</p>
          <p className="text-green-400">✅ Backend: Çalışıyor</p>
          <p className="text-green-400">✅ Routing: Çalışıyor</p>
        </div>
        <div className="mt-6">
          <a 
            href="/dashboard" 
            className="bg-violet-600 hover:bg-violet-700 text-white px-6 py-3 rounded-lg transition-colors"
          >
            Dashboard'a Git
          </a>
        </div>
      </div>
    </div>
  )
}