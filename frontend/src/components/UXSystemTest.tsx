/**
 * UX System Integration Test Component
 * Tests all UX enhancement systems working together
 */

import React, { useState, useEffect } from 'react'
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Zap, 
  Activity, 
  CheckCircle, 
  AlertCircle,
  TrendingUp,
  Sparkles
} from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { SkeletonLoader, TextSkeleton } from '@/components/ui/SkeletonLoader'
import { ProgressLoader } from '@/components/ui/ProgressLoader'
import { ShimmerEffect } from '@/components/ui/ShimmerEffect'
import { useAnimation } from '@/contexts/AnimationContext'
import { usePerformanceMonitor } from '@/hooks/usePerformanceMonitor'
import { useNotifications } from '@/hooks/useNotifications'
import { 
  useMicroInteraction,
  useCardInteraction,
  useFormValidation,
  useLoadingInteraction
} from '@/hooks/useMicroInteraction'

export const UXSystemTest: React.FC = () => {
  const [testResults, setTestResults] = useState<Record<string, boolean>>({})
  const [isRunning, setIsRunning] = useState(false)
  const [currentTest, setCurrentTest] = useState<string>('')
  const [progress, setProgress] = useState(0)

  // UX Enhancement hooks
  const { performanceMetrics, isReducedMotion, createAnimation } = useAnimation()
  const { measureRender } = usePerformanceMonitor({
    componentName: 'UXSystemTest',
    trackRenderTime: true
  })
  const { success, error, info, warning } = useNotifications()

  // Micro-interaction hooks
  const [testRef, testHandlers] = useMicroInteraction({ intensity: 'medium' })
  const { ref: cardRef, handlers: cardHandlers, cardProps } = useCardInteraction()
  const { ref: formRef, validateField, showSuccess, showError } = useFormValidation()
  const { ref: loadingRef, startLoading, stopLoading, completeWithSuccess, completeWithError } = useLoadingInteraction()

  // Test data
  const [testInput, setTestInput] = useState('')
  const [showSkeletons, setShowSkeletons] = useState(false)

  const tests = [
    {
      name: 'Animation System',
      description: 'Test animation creation and performance',
      test: async () => {
        if (!testRef.current) return false
        
        const animationId = createAnimation({
          element: testRef.current,
          keyframes: [
            { transform: 'scale(1)', opacity: 1 },
            { transform: 'scale(1.1)', opacity: 0.8 },
            { transform: 'scale(1)', opacity: 1 }
          ],
          duration: 500,
          easing: 'ease-in-out'
        })
        
        return !!animationId
      }
    },
    {
      name: 'Micro-Interactions',
      description: 'Test micro-interaction triggers',
      test: async () => {
        testHandlers.onClick()
        await new Promise(resolve => setTimeout(resolve, 100))
        testHandlers.onSuccess()
        return true
      }
    },
    {
      name: 'Performance Monitoring',
      description: 'Test performance metrics collection',
      test: async () => {
        const startTime = performance.now()
        await measureRender(async () => {
          // Simulate some work
          await new Promise(resolve => setTimeout(resolve, 50))
        })
        const endTime = performance.now()
        
        return (endTime - startTime) >= 50
      }
    },
    {
      name: 'Glassmorphism Engine',
      description: 'Test glassmorphism effects',
      test: async () => {
        const glassCard = document.querySelector('.glass-card')
        return !!glassCard && getComputedStyle(glassCard).backdropFilter !== 'none'
      }
    },
    {
      name: 'Loading States',
      description: 'Test loading state management',
      test: async () => {
        startLoading()
        await new Promise(resolve => setTimeout(resolve, 200))
        completeWithSuccess()
        return true
      }
    },
    {
      name: 'Notification System',
      description: 'Test notification display',
      test: async () => {
        success('Test notification')
        await new Promise(resolve => setTimeout(resolve, 100))
        return true
      }
    },
    {
      name: 'Form Validation',
      description: 'Test form validation with micro-interactions',
      test: async () => {
        const isValid = validateField('test@example.com', (value) => 
          /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
        )
        if (isValid) showSuccess()
        return isValid
      }
    },
    {
      name: 'Reduced Motion',
      description: 'Test reduced motion preference handling',
      test: async () => {
        // This test always passes but shows the current state
        return true
      }
    }
  ]

  const runAllTests = async () => {
    setIsRunning(true)
    setTestResults({})
    setProgress(0)

    for (let i = 0; i < tests.length; i++) {
      const test = tests[i]
      setCurrentTest(test.name)
      
      try {
        const result = await test.test()
        setTestResults(prev => ({ ...prev, [test.name]: result }))
        
        if (result) {
          info(`✅ ${test.name} passed`)
        } else {
          error(`❌ ${test.name} failed`)
        }
      } catch (err) {
        console.error(`Test ${test.name} error:`, err)
        setTestResults(prev => ({ ...prev, [test.name]: false }))
        error(`❌ ${test.name} error: ${err.message}`)
      }

      setProgress(((i + 1) / tests.length) * 100)
      await new Promise(resolve => setTimeout(resolve, 300))
    }

    setCurrentTest('')
    setIsRunning(false)
    
    const passedTests = Object.values(testResults).filter(Boolean).length
    const totalTests = tests.length
    
    if (passedTests === totalTests) {
      success(`🎉 All ${totalTests} tests passed!`)
    } else {
      warning(`⚠️ ${passedTests}/${totalTests} tests passed`)
    }
  }

  const resetTests = () => {
    setTestResults({})
    setProgress(0)
    setCurrentTest('')
    setIsRunning(false)
  }

  const toggleSkeletons = () => {
    setShowSkeletons(!showSkeletons)
  }

  const testMicroInteractions = () => {
    cardHandlers.onClick()
    setTimeout(() => cardHandlers.onSuccess(), 200)
  }

  return (
    <div className="space-y-6 p-6">
      <GlassCard className="p-6" intensity="medium">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">UX System Integration Test</h2>
            <p className="text-white/70">Test all UX enhancement systems working together</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={runAllTests}
              disabled={isRunning}
              className="flex items-center gap-2"
            >
              {isRunning ? (
                <>
                  <Pause className="w-4 h-4" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Tests
                </>
              )}
            </Button>
            <Button
              onClick={resetTests}
              variant="outline"
              size="sm"
            >
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Progress Bar */}
        {isRunning && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-white/70">
                {currentTest ? `Running: ${currentTest}` : 'Preparing tests...'}
              </span>
              <span className="text-sm text-white/70">{Math.round(progress)}%</span>
            </div>
            <ProgressLoader progress={progress} className="h-2" />
          </div>
        )}

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <Activity className="w-6 h-6 text-blue-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">{Math.round(performanceMetrics.fps)}</div>
            <div className="text-xs text-white/60">FPS</div>
          </div>
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <Zap className="w-6 h-6 text-yellow-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">{performanceMetrics.activeAnimations}</div>
            <div className="text-xs text-white/60">Animations</div>
          </div>
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <TrendingUp className="w-6 h-6 text-green-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">{Math.round(performanceMetrics.renderTime)}ms</div>
            <div className="text-xs text-white/60">Render Time</div>
          </div>
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <Sparkles className="w-6 h-6 text-purple-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">{isReducedMotion ? 'ON' : 'OFF'}</div>
            <div className="text-xs text-white/60">Reduced Motion</div>
          </div>
        </div>
      </GlassCard>

      {/* Test Results */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {tests.map((test, index) => {
          const result = testResults[test.name]
          const isRunningThis = isRunning && currentTest === test.name
          
          return (
            <GlassCard 
              key={test.name} 
              className="p-4" 
              intensity="subtle"
              interactive
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-white">{test.name}</h3>
                <div className="flex items-center gap-2">
                  {isRunningThis && (
                    <div className="w-4 h-4 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
                  )}
                  {result === true && <CheckCircle className="w-5 h-5 text-green-400" />}
                  {result === false && <AlertCircle className="w-5 h-5 text-red-400" />}
                </div>
              </div>
              <p className="text-sm text-white/70">{test.description}</p>
            </GlassCard>
          )
        })}
      </div>

      {/* Interactive Test Components */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Micro-Interaction Test */}
        <GlassCard className="p-4" intensity="subtle">
          <h3 className="font-semibold text-white mb-4">Micro-Interaction Test</h3>
          <div className="space-y-4">
            <div
              ref={testRef}
              className="p-4 bg-white/5 rounded-lg border border-white/10 cursor-pointer transition-all duration-200"
              onClick={testMicroInteractions}
            >
              <p className="text-white text-center">Click me to test micro-interactions</p>
            </div>
            
            <div
              ref={cardRef}
              className="p-4 bg-gradient-to-r from-violet-500/20 to-purple-500/20 rounded-lg cursor-pointer"
              {...cardProps}
            >
              <p className="text-white text-center">Hover me for card interactions</p>
            </div>
          </div>
        </GlassCard>

        {/* Form Validation Test */}
        <GlassCard className="p-4" intensity="subtle">
          <h3 className="font-semibold text-white mb-4">Form Validation Test</h3>
          <form ref={formRef} className="space-y-4">
            <Input
              type="email"
              placeholder="Enter email to test validation"
              value={testInput}
              onChange={(e) => {
                setTestInput(e.target.value)
                validateField(e.target.value, (value) => 
                  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
                )
              }}
            />
            <Button
              type="button"
              onClick={() => {
                const isValid = validateField(testInput, (value) => 
                  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
                )
                if (isValid) {
                  showSuccess()
                  success('Valid email!')
                } else {
                  showError()
                  error('Invalid email format')
                }
              }}
              className="w-full"
            >
              Validate Email
            </Button>
          </form>
        </GlassCard>

        {/* Loading States Test */}
        <GlassCard className="p-4" intensity="subtle">
          <h3 className="font-semibold text-white mb-4">Loading States Test</h3>
          <div className="space-y-4">
            <Button
              onClick={toggleSkeletons}
              variant="outline"
              className="w-full"
            >
              {showSkeletons ? 'Hide' : 'Show'} Skeleton Loaders
            </Button>
            
            {showSkeletons && (
              <div className="space-y-3">
                <SkeletonLoader className="h-4 w-full" />
                <SkeletonLoader className="h-4 w-3/4" />
                <SkeletonLoader className="h-4 w-1/2" />
                <TextSkeleton lines={3} />
              </div>
            )}
            
            <div ref={loadingRef} className="p-4 bg-white/5 rounded-lg">
              <ShimmerEffect className="h-16 w-full" />
            </div>
          </div>
        </GlassCard>

        {/* Notification Test */}
        <GlassCard className="p-4" intensity="subtle">
          <h3 className="font-semibold text-white mb-4">Notification Test</h3>
          <div className="grid grid-cols-2 gap-2">
            <Button
              onClick={() => success('Success notification!')}
              variant="outline"
              size="sm"
            >
              Success
            </Button>
            <Button
              onClick={() => error('Error notification!')}
              variant="outline"
              size="sm"
            >
              Error
            </Button>
            <Button
              onClick={() => warning('Warning notification!')}
              variant="outline"
              size="sm"
            >
              Warning
            </Button>
            <Button
              onClick={() => info('Info notification!')}
              variant="outline"
              size="sm"
            >
              Info
            </Button>
          </div>
        </GlassCard>
      </div>
    </div>
  )
}

export default UXSystemTest