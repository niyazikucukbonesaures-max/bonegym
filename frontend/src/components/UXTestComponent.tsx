/**
 * UX Test Component
 * Test component to verify all UX enhancement systems are working
 */

import React, { useState } from 'react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { usePerformanceMonitor } from '@/hooks/usePerformanceMonitor'
import { useAnimation } from '@/contexts/AnimationContext'

export const UXTestComponent: React.FC = () => {
  const [inputValue, setInputValue] = useState('')
  const [showSuccess, setShowSuccess] = useState(false)
  
  const { metrics, isMonitoring, startMonitoring, stopMonitoring } = usePerformanceMonitor({
    componentName: 'UXTestComponent',
    trackRenderTime: true,
    trackMounts: true
  })

  const { performanceMetrics, isReducedMotion } = useAnimation()

  const handleTestSuccess = () => {
    setShowSuccess(true)
    setTimeout(() => setShowSuccess(false), 2000)
  }

  return (
    <div className="p-6 space-y-6">
      <GlassCard className="p-6" interactive intensity="medium">
        <h2 className="text-xl font-bold text-white mb-4">UX Enhancement Test</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Animation System Test */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Animation System</h3>
            <div className="space-y-2">
              <Button onClick={handleTestSuccess} intensity="medium">
                Test Success Animation
              </Button>
              <Button variant="destructive" intensity="strong">
                Test Error Animation
              </Button>
              <Button variant="outline" intensity="subtle">
                Test Subtle Animation
              </Button>
            </div>
            
            <div className="text-sm text-white/60">
              <p>Reduced Motion: {isReducedMotion ? 'Enabled' : 'Disabled'}</p>
              <p>Active Animations: {performanceMetrics.activeAnimations}</p>
            </div>
          </div>

          {/* Glassmorphism Test */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Glassmorphism</h3>
            <div className="space-y-2">
              <GlassCard className="p-4" intensity="subtle">
                <p className="text-white text-sm">Subtle Glass Effect</p>
              </GlassCard>
              <GlassCard className="p-4" intensity="medium">
                <p className="text-white text-sm">Medium Glass Effect</p>
              </GlassCard>
              <GlassCard className="p-4" intensity="strong">
                <p className="text-white text-sm">Strong Glass Effect</p>
              </GlassCard>
            </div>
          </div>

          {/* Micro-Interactions Test */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Micro-Interactions</h3>
            <div className="space-y-2">
              <Input
                placeholder="Test input interactions..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                interactive
                intensity="medium"
              />
              <div className="flex gap-2">
                <Button size="sm" intensity="subtle">Hover Me</Button>
                <Button size="sm" variant="outline" intensity="medium">Focus Me</Button>
                <Button size="sm" variant="ghost" intensity="strong">Click Me</Button>
              </div>
            </div>
          </div>

          {/* Performance Monitor Test */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Performance Monitor</h3>
            <div className="space-y-2">
              <div className="flex gap-2">
                <Button 
                  size="sm" 
                  onClick={isMonitoring ? stopMonitoring : startMonitoring}
                  variant={isMonitoring ? 'destructive' : 'default'}
                >
                  {isMonitoring ? 'Stop' : 'Start'} Monitoring
                </Button>
              </div>
              
              <div className="text-sm text-white/60 space-y-1">
                <p>FPS: {metrics.fps}</p>
                <p>Memory: {metrics.memoryUsage.toFixed(1)}MB</p>
                <p>Components: {metrics.componentCount}</p>
                <p>Frame Drops: {metrics.frameDrops}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Success Indicator */}
        {showSuccess && (
          <div className="mt-4 p-3 bg-green-500/20 border border-green-500/30 rounded-lg">
            <p className="text-green-400 text-sm font-medium">
              ✅ UX Enhancement Systems Working!
            </p>
          </div>
        )}
      </GlassCard>
    </div>
  )
}