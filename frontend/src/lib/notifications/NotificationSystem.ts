/**
 * Advanced Notification System
 * Toast notifications with stacking, auto-dismiss, and swipe-to-dismiss
 */

export type NotificationType = 'success' | 'error' | 'warning' | 'info' | 'loading'

export interface NotificationConfig {
  id: string
  type: NotificationType
  title?: string
  message: string
  duration?: number
  persistent?: boolean
  actions?: NotificationAction[]
  icon?: string
  position?: NotificationPosition
  priority?: 'low' | 'medium' | 'high' | 'critical'
  showProgress?: boolean
  allowDismiss?: boolean
  hapticFeedback?: boolean
}

export interface NotificationAction {
  label: string
  action: () => void
  style?: 'primary' | 'secondary' | 'danger'
}

export type NotificationPosition = 
  | 'top-left' 
  | 'top-center' 
  | 'top-right'
  | 'bottom-left' 
  | 'bottom-center' 
  | 'bottom-right'
  | 'center'

export interface NotificationInstance {
  id: string
  config: NotificationConfig
  element: HTMLElement
  startTime: number
  timeoutId?: NodeJS.Timeout
  progressInterval?: NodeJS.Timeout
  isVisible: boolean
  isDismissing: boolean
}

export type NotificationEventType = 'show' | 'hide' | 'dismiss' | 'action' | 'timeout'

export interface NotificationEvent {
  type: NotificationEventType
  notification: NotificationInstance
  timestamp: number
  data?: any
}

export type NotificationEventListener = (event: NotificationEvent) => void

class NotificationSystem {
  private static instance: NotificationSystem
  private notifications: Map<string, NotificationInstance> = new Map()
  private containers: Map<NotificationPosition, HTMLElement> = new Map()
  private eventListeners: Map<NotificationEventType, NotificationEventListener[]> = new Map()
  private maxNotifications = 5
  private defaultDuration = 4000
  private stackSpacing = 8

  private constructor() {
    this.setupContainers()
    this.setupEventListeners()
    this.setupSwipeHandlers()
  }

  public static getInstance(): NotificationSystem {
    if (!NotificationSystem.instance) {
      NotificationSystem.instance = new NotificationSystem()
    }
    return NotificationSystem.instance
  }

  public show(config: Partial<NotificationConfig> & { message: string }): string {
    const id = config.id || `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    
    const finalConfig: NotificationConfig = {
      id,
      type: 'info',
      duration: this.defaultDuration,
      persistent: false,
      position: 'top-right',
      priority: 'medium',
      showProgress: true,
      allowDismiss: true,
      hapticFeedback: true,
      ...config
    }

    // Check if notification with same ID already exists
    if (this.notifications.has(id)) {
      this.update(id, finalConfig)
      return id
    }

    // Limit number of notifications
    this.enforceMaxNotifications(finalConfig.position!)

    // Create notification element
    const element = this.createElement(finalConfig)
    const container = this.getContainer(finalConfig.position!)
    
    // Create notification instance
    const instance: NotificationInstance = {
      id,
      config: finalConfig,
      element,
      startTime: Date.now(),
      isVisible: false,
      isDismissing: false
    }

    // Add to container
    container.appendChild(element)
    
    // Store instance
    this.notifications.set(id, instance)

    // Show with animation
    requestAnimationFrame(() => {
      this.showNotification(instance)
    })

    // Set up auto-dismiss
    if (!finalConfig.persistent && finalConfig.duration! > 0) {
      this.setupAutoDismiss(instance)
    }

    // Trigger haptic feedback
    if (finalConfig.hapticFeedback && this.isHapticSupported()) {
      this.triggerHapticFeedback(finalConfig.type)
    }

    // Emit show event
    this.emitEvent('show', instance)

    return id
  }

  public success(message: string, options: Partial<NotificationConfig> = {}): string {
    return this.show({ ...options, message, type: 'success' })
  }

  public error(message: string, options: Partial<NotificationConfig> = {}): string {
    return this.show({ ...options, message, type: 'error', duration: 6000 })
  }

  public warning(message: string, options: Partial<NotificationConfig> = {}): string {
    return this.show({ ...options, message, type: 'warning', duration: 5000 })
  }

  public info(message: string, options: Partial<NotificationConfig> = {}): string {
    return this.show({ ...options, message, type: 'info' })
  }

  public loading(message: string, options: Partial<NotificationConfig> = {}): string {
    return this.show({ 
      ...options, 
      message, 
      type: 'loading', 
      persistent: true,
      showProgress: false,
      allowDismiss: false
    })
  }

  public update(id: string, updates: Partial<NotificationConfig>): boolean {
    const instance = this.notifications.get(id)
    if (!instance) return false

    // Update config
    instance.config = { ...instance.config, ...updates }

    // Update element
    this.updateElement(instance)

    return true
  }

  public dismiss(id: string): boolean {
    const instance = this.notifications.get(id)
    if (!instance || instance.isDismissing) return false

    this.dismissNotification(instance)
    return true
  }

  public dismissAll(position?: NotificationPosition): void {
    const notifications = Array.from(this.notifications.values())
    
    notifications.forEach(instance => {
      if (!position || instance.config.position === position) {
        this.dismissNotification(instance)
      }
    })
  }

  public clear(): void {
    this.dismissAll()
  }

  public getNotifications(position?: NotificationPosition): NotificationInstance[] {
    const notifications = Array.from(this.notifications.values())
    
    if (position) {
      return notifications.filter(n => n.config.position === position)
    }
    
    return notifications
  }

  public addEventListener(type: NotificationEventType, listener: NotificationEventListener): void {
    if (!this.eventListeners.has(type)) {
      this.eventListeners.set(type, [])
    }
    this.eventListeners.get(type)!.push(listener)
  }

  public removeEventListener(type: NotificationEventType, listener: NotificationEventListener): void {
    const listeners = this.eventListeners.get(type)
    if (listeners) {
      const index = listeners.indexOf(listener)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  private setupContainers(): void {
    const positions: NotificationPosition[] = [
      'top-left', 'top-center', 'top-right',
      'bottom-left', 'bottom-center', 'bottom-right',
      'center'
    ]

    positions.forEach(position => {
      const container = document.createElement('div')
      container.className = `notification-container notification-${position}`
      container.style.cssText = this.getContainerStyles(position)
      
      document.body.appendChild(container)
      this.containers.set(position, container)
    })
  }

  private getContainerStyles(position: NotificationPosition): string {
    const baseStyles = `
      position: fixed;
      z-index: 9999;
      pointer-events: none;
      display: flex;
      flex-direction: column;
      gap: ${this.stackSpacing}px;
      max-width: 400px;
      padding: 16px;
    `

    const positionStyles = {
      'top-left': 'top: 0; left: 0;',
      'top-center': 'top: 0; left: 50%; transform: translateX(-50%);',
      'top-right': 'top: 0; right: 0;',
      'bottom-left': 'bottom: 0; left: 0; flex-direction: column-reverse;',
      'bottom-center': 'bottom: 0; left: 50%; transform: translateX(-50%); flex-direction: column-reverse;',
      'bottom-right': 'bottom: 0; right: 0; flex-direction: column-reverse;',
      'center': 'top: 50%; left: 50%; transform: translate(-50%, -50%);'
    }

    return baseStyles + positionStyles[position]
  }

  private createElement(config: NotificationConfig): HTMLElement {
    const element = document.createElement('div')
    element.className = `notification notification-${config.type}`
    element.style.cssText = `
      pointer-events: auto;
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      transform: translateX(100%);
      opacity: 0;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      cursor: pointer;
      user-select: none;
      max-width: 100%;
      word-wrap: break-word;
    `

    // Add type-specific styling
    const typeColors = {
      success: 'rgba(34, 197, 94, 0.2)',
      error: 'rgba(239, 68, 68, 0.2)',
      warning: 'rgba(245, 158, 11, 0.2)',
      info: 'rgba(59, 130, 246, 0.2)',
      loading: 'rgba(139, 92, 246, 0.2)'
    }

    element.style.borderColor = typeColors[config.type]

    // Create content
    const content = this.createContent(config)
    element.appendChild(content)

    // Add progress bar if enabled
    if (config.showProgress && !config.persistent) {
      const progressBar = this.createProgressBar(config)
      element.appendChild(progressBar)
    }

    // Add event listeners
    this.setupElementEventListeners(element, config)

    return element
  }

  private createContent(config: NotificationConfig): HTMLElement {
    const content = document.createElement('div')
    content.className = 'notification-content'
    content.style.cssText = 'display: flex; align-items: flex-start; gap: 12px;'

    // Icon
    const icon = document.createElement('div')
    icon.className = 'notification-icon'
    icon.style.cssText = 'flex-shrink: 0; font-size: 20px;'
    icon.textContent = this.getIcon(config.type, config.icon)
    content.appendChild(icon)

    // Text content
    const textContent = document.createElement('div')
    textContent.className = 'notification-text'
    textContent.style.cssText = 'flex: 1; min-width: 0;'

    if (config.title) {
      const title = document.createElement('div')
      title.className = 'notification-title'
      title.style.cssText = 'font-weight: 600; color: white; margin-bottom: 4px; font-size: 14px;'
      title.textContent = config.title
      textContent.appendChild(title)
    }

    const message = document.createElement('div')
    message.className = 'notification-message'
    message.style.cssText = 'color: rgba(255, 255, 255, 0.8); font-size: 13px; line-height: 1.4;'
    message.textContent = config.message
    textContent.appendChild(message)

    content.appendChild(textContent)

    // Actions
    if (config.actions && config.actions.length > 0) {
      const actions = document.createElement('div')
      actions.className = 'notification-actions'
      actions.style.cssText = 'display: flex; gap: 8px; margin-top: 12px;'

      config.actions.forEach(action => {
        const button = document.createElement('button')
        button.className = `notification-action notification-action-${action.style || 'secondary'}`
        button.style.cssText = `
          padding: 6px 12px;
          border-radius: 6px;
          border: none;
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          ${action.style === 'primary' ? 
            'background: rgba(139, 92, 246, 0.8); color: white;' :
            action.style === 'danger' ?
            'background: rgba(239, 68, 68, 0.8); color: white;' :
            'background: rgba(255, 255, 255, 0.1); color: rgba(255, 255, 255, 0.8);'
          }
        `
        button.textContent = action.label
        button.onclick = (e) => {
          e.stopPropagation()
          action.action()
          this.emitEvent('action', this.notifications.get(config.id)!, { action })
        }
        actions.appendChild(button)
      })

      textContent.appendChild(actions)
    }

    // Dismiss button
    if (config.allowDismiss) {
      const dismissButton = document.createElement('button')
      dismissButton.className = 'notification-dismiss'
      dismissButton.style.cssText = `
        position: absolute;
        top: 8px;
        right: 8px;
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.6);
        cursor: pointer;
        font-size: 16px;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        transition: all 0.2s;
      `
      dismissButton.innerHTML = '×'
      dismissButton.onclick = (e) => {
        e.stopPropagation()
        this.dismiss(config.id)
      }
      
      // Position content relative for dismiss button
      content.style.position = 'relative'
      content.appendChild(dismissButton)
    }

    return content
  }

  private createProgressBar(config: NotificationConfig): HTMLElement {
    const progressContainer = document.createElement('div')
    progressContainer.className = 'notification-progress'
    progressContainer.style.cssText = `
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 0 0 12px 12px;
      overflow: hidden;
    `

    const progressBar = document.createElement('div')
    progressBar.className = 'notification-progress-bar'
    progressBar.style.cssText = `
      height: 100%;
      background: rgba(255, 255, 255, 0.6);
      width: 100%;
      transform: translateX(-100%);
      transition: transform linear;
      transition-duration: ${config.duration}ms;
    `

    progressContainer.appendChild(progressBar)
    return progressContainer
  }

  private getIcon(type: NotificationType, customIcon?: string): string {
    if (customIcon) return customIcon

    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️',
      loading: '⏳'
    }

    return icons[type]
  }

  private setupElementEventListeners(element: HTMLElement, config: NotificationConfig): void {
    // Click to dismiss
    element.addEventListener('click', () => {
      if (config.allowDismiss) {
        this.dismiss(config.id)
      }
    })

    // Swipe to dismiss
    let startX = 0
    let currentX = 0
    let isDragging = false

    element.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX
      isDragging = true
    })

    element.addEventListener('touchmove', (e) => {
      if (!isDragging) return
      
      currentX = e.touches[0].clientX
      const deltaX = currentX - startX
      
      if (Math.abs(deltaX) > 10) {
        element.style.transform = `translateX(${deltaX}px)`
        element.style.opacity = `${Math.max(0.3, 1 - Math.abs(deltaX) / 200)}`
      }
    })

    element.addEventListener('touchend', () => {
      if (!isDragging) return
      
      const deltaX = currentX - startX
      
      if (Math.abs(deltaX) > 100) {
        this.dismiss(config.id)
      } else {
        element.style.transform = ''
        element.style.opacity = ''
      }
      
      isDragging = false
    })
  }

  private showNotification(instance: NotificationInstance): void {
    instance.element.style.transform = 'translateX(0)'
    instance.element.style.opacity = '1'
    instance.isVisible = true

    // Start progress animation
    const progressBar = instance.element.querySelector('.notification-progress-bar') as HTMLElement
    if (progressBar) {
      requestAnimationFrame(() => {
        progressBar.style.transform = 'translateX(0)'
      })
    }
  }

  private dismissNotification(instance: NotificationInstance): void {
    if (instance.isDismissing) return

    instance.isDismissing = true

    // Clear timers
    if (instance.timeoutId) {
      clearTimeout(instance.timeoutId)
    }
    if (instance.progressInterval) {
      clearInterval(instance.progressInterval)
    }

    // Animate out
    instance.element.style.transform = 'translateX(100%)'
    instance.element.style.opacity = '0'

    // Remove after animation
    setTimeout(() => {
      if (instance.element.parentNode) {
        instance.element.parentNode.removeChild(instance.element)
      }
      this.notifications.delete(instance.id)
    }, 300)

    // Emit dismiss event
    this.emitEvent('dismiss', instance)
  }

  private setupAutoDismiss(instance: NotificationInstance): void {
    instance.timeoutId = setTimeout(() => {
      this.dismissNotification(instance)
      this.emitEvent('timeout', instance)
    }, instance.config.duration)
  }

  private updateElement(instance: NotificationInstance): void {
    // Update content
    const messageElement = instance.element.querySelector('.notification-message')
    if (messageElement) {
      messageElement.textContent = instance.config.message
    }

    const titleElement = instance.element.querySelector('.notification-title')
    if (titleElement && instance.config.title) {
      titleElement.textContent = instance.config.title
    }
  }

  private enforceMaxNotifications(position: NotificationPosition): void {
    const notifications = this.getNotifications(position)
    
    if (notifications.length >= this.maxNotifications) {
      // Dismiss oldest notifications
      const toRemove = notifications
        .sort((a, b) => a.startTime - b.startTime)
        .slice(0, notifications.length - this.maxNotifications + 1)
      
      toRemove.forEach(notification => {
        this.dismissNotification(notification)
      })
    }
  }

  private getContainer(position: NotificationPosition): HTMLElement {
    return this.containers.get(position)!
  }

  private setupEventListeners(): void {
    const eventTypes: NotificationEventType[] = ['show', 'hide', 'dismiss', 'action', 'timeout']
    eventTypes.forEach(type => {
      this.eventListeners.set(type, [])
    })
  }

  private setupSwipeHandlers(): void {
    // Global swipe handler setup is done per element
  }

  private emitEvent(type: NotificationEventType, instance: NotificationInstance, data?: any): void {
    const event: NotificationEvent = {
      type,
      notification: instance,
      timestamp: Date.now(),
      data
    }

    const listeners = this.eventListeners.get(type) || []
    listeners.forEach(listener => {
      try {
        listener(event)
      } catch (error) {
        console.error(`NotificationSystem: Error in ${type} event listener:`, error)
      }
    })
  }

  private isHapticSupported(): boolean {
    return 'vibrate' in navigator
  }

  private triggerHapticFeedback(type: NotificationType): void {
    if (!this.isHapticSupported()) return

    const patterns = {
      success: [20, 10, 20],
      error: [50, 30, 50, 30, 50],
      warning: [30, 20, 30],
      info: [15],
      loading: [10]
    }

    const pattern = patterns[type]
    if (pattern) {
      navigator.vibrate(pattern)
    }
  }

  public destroy(): void {
    // Dismiss all notifications
    this.dismissAll()

    // Remove containers
    this.containers.forEach(container => {
      if (container.parentNode) {
        container.parentNode.removeChild(container)
      }
    })

    // Clear data
    this.notifications.clear()
    this.containers.clear()
    this.eventListeners.clear()

    NotificationSystem.instance = null as any
  }
}

export default NotificationSystem