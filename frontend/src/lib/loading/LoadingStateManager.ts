/**
 * Loading State Manager
 * Advanced loading state management with skeleton loaders and progressive loading
 */

export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

export interface LoadingConfig {
  id: string
  type: 'skeleton' | 'spinner' | 'progress' | 'shimmer' | 'pulse'
  duration?: number
  showProgress?: boolean
  progressValue?: number
  message?: string
  priority: 'low' | 'medium' | 'high' | 'critical'
}

export interface SkeletonConfig {
  width?: string | number
  height?: string | number
  borderRadius?: string | number
  count?: number
  className?: string
  animate?: boolean
  speed?: number
}

export interface ProgressConfig {
  total: number
  current: number
  showPercentage?: boolean
  showETA?: boolean
  color?: string
}

export interface LoadingInstance {
  id: string
  element: HTMLElement
  config: LoadingConfig
  startTime: number
  state: LoadingState
  progressConfig?: ProgressConfig
  skeletonConfig?: SkeletonConfig
}

export interface NetworkCondition {
  effectiveType: '2g' | '3g' | '4g' | 'slow-2g'
  downlink: number
  rtt: number
  saveData: boolean
}

class LoadingStateManager {
  private static instance: LoadingStateManager
  private activeLoadings: Map<string, LoadingInstance> = new Map()
  private networkCondition: NetworkCondition | null = null
  private loadingQueue: LoadingConfig[] = []
  private isProcessingQueue = false

  private constructor() {
    this.detectNetworkCondition()
    this.setupNetworkListener()
  }

  public static getInstance(): LoadingStateManager {
    if (!LoadingStateManager.instance) {
      LoadingStateManager.instance = new LoadingStateManager()
    }
    return LoadingStateManager.instance
  }

  public startLoading(element: HTMLElement, config: LoadingConfig): string {
    // Adapt config based on network conditions
    const adaptedConfig = this.adaptConfigForNetwork(config)

    // Create loading instance
    const instance: LoadingInstance = {
      id: config.id,
      element,
      config: adaptedConfig,
      startTime: performance.now(),
      state: 'loading'
    }

    // Apply loading UI based on type
    this.applyLoadingUI(instance)

    // Store instance
    this.activeLoadings.set(config.id, instance)

    return config.id
  }

  public updateProgress(id: string, current: number, total?: number): void {
    const instance = this.activeLoadings.get(id)
    if (!instance) return

    if (!instance.progressConfig) {
      instance.progressConfig = {
        total: total || 100,
        current: 0,
        showPercentage: true,
        showETA: true
      }
    }

    instance.progressConfig.current = current
    if (total !== undefined) {
      instance.progressConfig.total = total
    }

    this.updateProgressUI(instance)
  }

  public completeLoading(id: string, success: boolean = true): void {
    const instance = this.activeLoadings.get(id)
    if (!instance) return

    instance.state = success ? 'success' : 'error'

    // Show completion animation
    this.showCompletionAnimation(instance, success)

    // Clean up after animation
    setTimeout(() => {
      this.removeLoadingUI(instance)
      this.activeLoadings.delete(id)
    }, 500)
  }

  public cancelLoading(id: string): void {
    const instance = this.activeLoadings.get(id)
    if (!instance) return

    this.removeLoadingUI(instance)
    this.activeLoadings.delete(id)
  }

  public createSkeleton(element: HTMLElement, config: SkeletonConfig = {}): string {
    const id = `skeleton-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    
    const loadingConfig: LoadingConfig = {
      id,
      type: 'skeleton',
      priority: 'medium'
    }

    const instance: LoadingInstance = {
      id,
      element,
      config: loadingConfig,
      startTime: performance.now(),
      state: 'loading',
      skeletonConfig: {
        width: '100%',
        height: '20px',
        borderRadius: '4px',
        count: 1,
        animate: true,
        speed: 2,
        ...config
      }
    }

    this.applySkeletonUI(instance)
    this.activeLoadings.set(id, instance)

    return id
  }

  public createProgressLoader(element: HTMLElement, config: ProgressConfig): string {
    const id = `progress-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    
    const loadingConfig: LoadingConfig = {
      id,
      type: 'progress',
      priority: 'high',
      showProgress: true
    }

    const instance: LoadingInstance = {
      id,
      element,
      config: loadingConfig,
      startTime: performance.now(),
      state: 'loading',
      progressConfig: config
    }

    this.applyProgressUI(instance)
    this.activeLoadings.set(id, instance)

    return id
  }

  public getNetworkCondition(): NetworkCondition | null {
    return this.networkCondition
  }

  public isSlowNetwork(): boolean {
    if (!this.networkCondition) return false
    
    return (
      this.networkCondition.effectiveType === 'slow-2g' ||
      this.networkCondition.effectiveType === '2g' ||
      this.networkCondition.downlink < 1 ||
      this.networkCondition.rtt > 1000
    )
  }

  private adaptConfigForNetwork(config: LoadingConfig): LoadingConfig {
    const adaptedConfig = { ...config }

    if (this.isSlowNetwork()) {
      // Simplify loading for slow networks
      if (config.type === 'skeleton') {
        adaptedConfig.type = 'spinner'
      }
      
      // Reduce animation complexity
      adaptedConfig.duration = (config.duration || 1000) * 1.5
    }

    return adaptedConfig
  }

  private applyLoadingUI(instance: LoadingInstance): void {
    const { element, config } = instance

    switch (config.type) {
      case 'skeleton':
        this.applySkeletonUI(instance)
        break
      case 'spinner':
        this.applySpinnerUI(instance)
        break
      case 'progress':
        this.applyProgressUI(instance)
        break
      case 'shimmer':
        this.applyShimmerUI(instance)
        break
      case 'pulse':
        this.applyPulseUI(instance)
        break
    }
  }

  private applySkeletonUI(instance: LoadingInstance): void {
    const { element, skeletonConfig } = instance
    if (!skeletonConfig) return

    // Clear existing content
    const originalContent = element.innerHTML
    element.setAttribute('data-original-content', originalContent)

    // Create skeleton elements
    const skeletonContainer = document.createElement('div')
    skeletonContainer.className = 'skeleton-container space-y-2'

    for (let i = 0; i < (skeletonConfig.count || 1); i++) {
      const skeletonElement = document.createElement('div')
      skeletonElement.className = `skeleton ${skeletonConfig.className || ''}`
      
      // Apply styles
      skeletonElement.style.width = typeof skeletonConfig.width === 'number' 
        ? `${skeletonConfig.width}px` 
        : (skeletonConfig.width || '100%')
      
      skeletonElement.style.height = typeof skeletonConfig.height === 'number'
        ? `${skeletonConfig.height}px`
        : (skeletonConfig.height || '20px')
      
      skeletonElement.style.borderRadius = typeof skeletonConfig.borderRadius === 'number'
        ? `${skeletonConfig.borderRadius}px`
        : (skeletonConfig.borderRadius || '4px')

      if (skeletonConfig.animate) {
        skeletonElement.style.animationDuration = `${skeletonConfig.speed || 2}s`
      }

      skeletonContainer.appendChild(skeletonElement)
    }

    element.innerHTML = ''
    element.appendChild(skeletonContainer)
  }

  private applySpinnerUI(instance: LoadingInstance): void {
    const { element, config } = instance

    const spinner = document.createElement('div')
    spinner.className = 'loading-spinner'
    spinner.innerHTML = `
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-400"></div>
      ${config.message ? `<p class="text-white/60 text-sm mt-2">${config.message}</p>` : ''}
    `

    element.innerHTML = ''
    element.appendChild(spinner)
  }

  private applyProgressUI(instance: LoadingInstance): void {
    const { element, progressConfig } = instance
    if (!progressConfig) return

    const percentage = Math.round((progressConfig.current / progressConfig.total) * 100)
    
    const progressContainer = document.createElement('div')
    progressContainer.className = 'progress-container'
    
    progressContainer.innerHTML = `
      <div class="w-full bg-white/10 rounded-full h-2 mb-2">
        <div class="bg-violet-500 h-2 rounded-full transition-all duration-300" style="width: ${percentage}%"></div>
      </div>
      ${progressConfig.showPercentage ? `<p class="text-white/60 text-sm">${percentage}%</p>` : ''}
    `

    element.innerHTML = ''
    element.appendChild(progressContainer)
  }

  private applyShimmerUI(instance: LoadingInstance): void {
    const { element } = instance

    element.classList.add('shimmer-loading')
    element.style.background = `
      linear-gradient(
        90deg,
        rgba(255, 255, 255, 0.05) 0%,
        rgba(255, 255, 255, 0.1) 50%,
        rgba(255, 255, 255, 0.05) 100%
      )
    `
    element.style.backgroundSize = '200% 100%'
    element.style.animation = 'shimmer 2s infinite'
  }

  private applyPulseUI(instance: LoadingInstance): void {
    const { element } = instance

    element.classList.add('pulse-loading')
    element.style.animation = 'pulse 2s ease-in-out infinite'
  }

  private updateProgressUI(instance: LoadingInstance): void {
    const { element, progressConfig } = instance
    if (!progressConfig) return

    const progressBar = element.querySelector('.bg-violet-500') as HTMLElement
    const progressText = element.querySelector('p') as HTMLElement

    if (progressBar) {
      const percentage = Math.round((progressConfig.current / progressConfig.total) * 100)
      progressBar.style.width = `${percentage}%`
      
      if (progressText && progressConfig.showPercentage) {
        progressText.textContent = `${percentage}%`
      }
    }
  }

  private showCompletionAnimation(instance: LoadingInstance, success: boolean): void {
    const { element } = instance

    // Add completion class for animation
    element.classList.add(success ? 'loading-success' : 'loading-error')

    // Show completion icon
    const icon = success ? '✅' : '❌'
    const message = success ? 'Tamamlandı!' : 'Hata oluştu!'

    const completionElement = document.createElement('div')
    completionElement.className = 'loading-completion text-center'
    completionElement.innerHTML = `
      <div class="text-2xl mb-2">${icon}</div>
      <p class="text-sm ${success ? 'text-green-400' : 'text-red-400'}">${message}</p>
    `

    element.innerHTML = ''
    element.appendChild(completionElement)
  }

  private removeLoadingUI(instance: LoadingInstance): void {
    const { element } = instance

    // Restore original content if it was a skeleton
    const originalContent = element.getAttribute('data-original-content')
    if (originalContent) {
      element.innerHTML = originalContent
      element.removeAttribute('data-original-content')
    } else {
      element.innerHTML = ''
    }

    // Remove loading classes
    element.classList.remove('shimmer-loading', 'pulse-loading', 'loading-success', 'loading-error')
    element.style.background = ''
    element.style.animation = ''
  }

  private detectNetworkCondition(): void {
    // Use Network Information API if available
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection

    if (connection) {
      this.networkCondition = {
        effectiveType: connection.effectiveType || '4g',
        downlink: connection.downlink || 10,
        rtt: connection.rtt || 100,
        saveData: connection.saveData || false
      }
    }
  }

  private setupNetworkListener(): void {
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection

    if (connection) {
      connection.addEventListener('change', () => {
        this.detectNetworkCondition()
        console.log('LoadingStateManager: Network condition changed', this.networkCondition)
      })
    }
  }

  public destroy(): void {
    // Cancel all active loadings
    this.activeLoadings.forEach((instance, id) => {
      this.cancelLoading(id)
    })

    this.activeLoadings.clear()
    this.loadingQueue.length = 0

    LoadingStateManager.instance = null as any
  }
}

export default LoadingStateManager