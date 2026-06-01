/**
 * Enhanced Error Boundary
 * Advanced error boundary with recovery strategies and user-friendly error messages
 */

import React, { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  showReportButton?: boolean
  enableRecovery?: boolean
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  retryCount: number
  isRecovering: boolean
}

export class EnhancedErrorBoundary extends Component<Props, State> {
  private retryTimeoutId: NodeJS.Timeout | null = null
  private maxRetries = 3
  private retryDelay = 1000

  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
      isRecovering: false
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('EnhancedErrorBoundary caught an error:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo
    })

    // Call custom error handler
    this.props.onError?.(error, errorInfo)

    // Report error to monitoring service
    this.reportError(error, errorInfo)

    // Attempt automatic recovery for certain error types
    if (this.props.enableRecovery && this.shouldAttemptRecovery(error)) {
      this.attemptRecovery()
    }
  }

  private shouldAttemptRecovery(error: Error): boolean {
    // Don't retry for certain critical errors
    const criticalErrors = [
      'ChunkLoadError',
      'SecurityError',
      'QuotaExceededError'
    ]

    return !criticalErrors.some(criticalError => 
      error.name.includes(criticalError) || error.message.includes(criticalError)
    )
  }

  private attemptRecovery = () => {
    if (this.state.retryCount >= this.maxRetries) {
      return
    }

    this.setState({ isRecovering: true })

    this.retryTimeoutId = setTimeout(() => {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1,
        isRecovering: false
      }))
    }, this.retryDelay * (this.state.retryCount + 1))
  }

  private handleManualRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
      isRecovering: false
    })
  }

  private handleGoHome = () => {
    window.location.href = '/'
  }

  private handleReportError = () => {
    const { error, errorInfo } = this.state
    
    // Create error report
    const errorReport = {
      message: error?.message || 'Unknown error',
      stack: error?.stack || 'No stack trace',
      componentStack: errorInfo?.componentStack || 'No component stack',
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    }

    // Copy to clipboard
    navigator.clipboard.writeText(JSON.stringify(errorReport, null, 2))
      .then(() => {
        alert('Hata raporu panoya kopyalandı. Destek ekibiyle paylaşabilirsiniz.')
      })
      .catch(() => {
        console.error('Failed to copy error report to clipboard')
      })
  }

  private reportError(error: Error, errorInfo: ErrorInfo) {
    // Report to error monitoring service (e.g., Sentry, LogRocket)
    try {
      // Example: Sentry.captureException(error, { contexts: { react: errorInfo } })
      console.error('Error reported:', {
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack
      })
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError)
    }
  }

  private getErrorMessage(error: Error): string {
    // Provide user-friendly error messages
    if (error.name === 'ChunkLoadError') {
      return 'Uygulama güncellemesi algılandı. Sayfayı yenileyin.'
    }
    
    if (error.message.includes('Network Error')) {
      return 'İnternet bağlantınızı kontrol edin ve tekrar deneyin.'
    }
    
    if (error.message.includes('Permission denied')) {
      return 'Bu işlem için yetkiniz bulunmuyor.'
    }
    
    if (error.message.includes('Quota exceeded')) {
      return 'Depolama alanı dolu. Lütfen bazı verileri temizleyin.'
    }

    return 'Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.'
  }

  private getErrorSeverity(error: Error): 'low' | 'medium' | 'high' {
    if (error.name === 'ChunkLoadError') return 'medium'
    if (error.message.includes('Network Error')) return 'medium'
    if (error.message.includes('Permission denied')) return 'high'
    if (error.message.includes('Quota exceeded')) return 'high'
    return 'medium'
  }

  componentWillUnmount() {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId)
    }
  }

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback
      }

      const { error } = this.state
      const errorMessage = error ? this.getErrorMessage(error) : 'Bilinmeyen hata'
      const severity = error ? this.getErrorSeverity(error) : 'medium'
      const canRetry = this.state.retryCount < this.maxRetries

      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
          <GlassCard className="max-w-md w-full p-6 text-center" intensity="medium">
            <div className="mb-6">
              <div className={`mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-4 ${
                severity === 'high' ? 'bg-red-500/20' :
                severity === 'medium' ? 'bg-amber-500/20' :
                'bg-blue-500/20'
              }`}>
                <AlertTriangle className={`w-8 h-8 ${
                  severity === 'high' ? 'text-red-400' :
                  severity === 'medium' ? 'text-amber-400' :
                  'text-blue-400'
                }`} />
              </div>
              
              <h2 className="text-xl font-bold text-white mb-2">
                Bir Sorun Oluştu
              </h2>
              
              <p className="text-white/70 text-sm mb-4">
                {errorMessage}
              </p>

              {this.state.isRecovering && (
                <div className="flex items-center justify-center gap-2 text-violet-400 text-sm mb-4">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Otomatik düzeltme deneniyor...</span>
                </div>
              )}

              {error && (
                <details className="text-left text-xs text-white/50 bg-white/5 rounded p-2 mb-4">
                  <summary className="cursor-pointer hover:text-white/70">
                    Teknik Detaylar
                  </summary>
                  <div className="mt-2 font-mono">
                    <div className="mb-1">
                      <strong>Hata:</strong> {error.name}
                    </div>
                    <div className="mb-1">
                      <strong>Mesaj:</strong> {error.message}
                    </div>
                    {this.state.retryCount > 0 && (
                      <div>
                        <strong>Deneme Sayısı:</strong> {this.state.retryCount}/{this.maxRetries}
                      </div>
                    )}
                  </div>
                </details>
              )}
            </div>

            <div className="space-y-3">
              {canRetry && !this.state.isRecovering && (
                <Button
                  onClick={this.handleManualRetry}
                  className="w-full"
                  variant="default"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Tekrar Dene
                </Button>
              )}

              <Button
                onClick={this.handleGoHome}
                variant="outline"
                className="w-full"
              >
                <Home className="w-4 h-4 mr-2" />
                Ana Sayfaya Dön
              </Button>

              {this.props.showReportButton && (
                <Button
                  onClick={this.handleReportError}
                  variant="ghost"
                  size="sm"
                  className="w-full text-white/60 hover:text-white/80"
                >
                  <Bug className="w-4 h-4 mr-2" />
                  Hata Raporunu Kopyala
                </Button>
              )}
            </div>

            <div className="mt-6 text-xs text-white/40">
              Sorun devam ederse, sayfayı yenileyin veya destek ekibiyle iletişime geçin.
            </div>
          </GlassCard>
        </div>
      )
    }

    return this.props.children
  }
}

// Hook for using error boundary in functional components
export const useErrorHandler = () => {
  const [error, setError] = React.useState<Error | null>(null)

  const resetError = React.useCallback(() => {
    setError(null)
  }, [])

  const captureError = React.useCallback((error: Error) => {
    setError(error)
  }, [])

  React.useEffect(() => {
    if (error) {
      throw error
    }
  }, [error])

  return { captureError, resetError }
}

// Higher-order component for wrapping components with error boundary
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) => {
  const WrappedComponent = (props: P) => (
    <EnhancedErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </EnhancedErrorBoundary>
  )

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`
  
  return WrappedComponent
}