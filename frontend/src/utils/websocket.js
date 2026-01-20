/**
 * WebSocket封装
 * WebSocket wrapper for real-time data
 */
import { ElMessage } from 'element-plus'

let ws = null
let reconnectTimer = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY = 3000

class WebSocketClient {
  constructor(url) {
    this.url = url
    this.ws = null
    this.messageHandlers = new Map()
    this.connectAttempts = 0
    this.shouldReconnect = true
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url)
      this.setupEventListeners()
    } catch (error) {
      console.error('WebSocket connection error:', error)
      this.handleReconnect()
    }
  }

  setupEventListeners() {
    this.ws.onopen = (event) => {
      console.log('WebSocket connected:', this.url)
      this.connectAttempts = 0
      this.emit('open', event)
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.emit('message', data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.emit('error', error)
    }

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason)
      this.emit('close', event)

      if (this.shouldReconnect) {
        this.handleReconnect()
      }
    }
  }

  handleReconnect() {
    if (this.connectAttempts < MAX_RECONNECT_ATTEMPTS) {
      this.connectAttempts++
      console.log(`Reconnecting to WebSocket... Attempt ${this.connectAttempts}/${MAX_RECONNECT_ATTEMPTS}`)

      setTimeout(() => {
        this.connect()
      }, RECONNECT_DELAY)
    } else {
      console.error('Max reconnect attempts reached')
      ElMessage.error('WebSocket连接失败，请刷新页面重试')
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  close() {
    this.shouldReconnect = false
    if (this.ws) {
      this.ws.close()
    }
    this.clearReconnectTimer()
  }

  clearReconnectTimer() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  on(event, handler) {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, [])
    }
    this.messageHandlers.get(event).push(handler)
  }

  off(event, handler) {
    if (this.messageHandlers.has(event)) {
      const handlers = this.messageHandlers.get(event)
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  emit(event, data) {
    if (this.messageHandlers.has(event)) {
      this.messageHandlers.get(event).forEach(handler => {
        handler(data)
      })
    }
  }
}

// 创建实时数据WebSocket实例
export function createRealtimeWebSocket(deviceId = null) {
  const baseUrl = import.meta.env.VITE_WS_BASE_URL
  const url = deviceId ? `${baseUrl}/realtime/${deviceId}/` : `${baseUrl}/realtime/`
  return new WebSocketClient(url)
}

// 创建告警WebSocket实例
export function createAlarmWebSocket() {
  const url = `${import.meta.env.VITE_WS_BASE_URL}/alarms/`
  return new WebSocketClient(url)
}

export default WebSocketClient
