import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { io, Socket } from 'socket.io-client'

export interface ROI {
  id: number
  x1: number
  y1: number
  x2: number
  y2: number
  width: number
  height: number
  motion_detected: boolean
}

export interface DetectorStats {
  camera_status: string
  fps: number
  total_detections: number
  active_rois: number
  motion_detected_rois: number[]
  rain_detected: boolean
}

export interface MotionConfig {
  threshold: number
  min_area: number
  blur_size: number
  rain_area_threshold: number
}

export const useDetectorStore = defineStore('detector', () => {
  // State
  const isConnected = ref(false)
  const isSystemInitialized = ref(false)
  const currentFrame = ref<string>('')
  const rois = ref<ROI[]>([])
  const stats = ref<DetectorStats>({
    camera_status: 'disconnected',
    fps: 0,
    total_detections: 0,
    active_rois: 0,
    motion_detected_rois: [],
    rain_detected: false
  })
  const config = ref<MotionConfig>({
    threshold: 800,
    min_area: 100,
    blur_size: 21,
    rain_area_threshold: 5000
  })
  
  // Sound settings
  const soundEnabled = ref(true)
  const motionSoundVolume = ref(0.5)
  
  // Socket connection
  let socket: Socket | null = null
  
  // Computed
  const activeRoisCount = computed(() => rois.value.length)
  const motionDetectedRois = computed(() => 
    rois.value.filter(roi => roi.motion_detected)
  )
  const hasMotionDetection = computed(() => motionDetectedRois.value.length > 0)
  
  // Actions
  function connectSocket() {
    if (socket?.connected) return
    
    // Use environment variables for connection, fallback to current host in production
    const socketUrl = import.meta.env.DEV 
      ? `http://${import.meta.env.WEB_HOST || 'localhost'}:${import.meta.env.WEB_PORT || 5001}`
      : window.location.origin
    
    socket = io(socketUrl, {
      transports: ['websocket', 'polling']
    })
    
    socket.on('connect', () => {
      console.log('Socket connected')
      isConnected.value = true
    })
    
    socket.on('disconnect', () => {
      console.log('Socket disconnected')
      isConnected.value = false
    })
    
    socket.on('frame_update', (data) => {
      currentFrame.value = data.frame
    })
    
    socket.on('stats_update', (data) => {
      stats.value = data
      
      // Update ROI motion status
      rois.value.forEach(roi => {
        roi.motion_detected = data.motion_detected_rois.includes(roi.id)
      })
      
      // Play sound notification
      if (hasMotionDetection.value && soundEnabled.value) {
        playMotionSound()
      }
    })
    
    socket.on('rois_update', (data) => {
      rois.value = data.rois
    })
  }
  
  function disconnectSocket() {
    if (socket) {
      socket.disconnect()
      socket = null
    }
    isConnected.value = false
  }
  
  // API calls
  async function apiCall(endpoint: string, options: RequestInit = {}) {
    try {
      const response = await fetch(`/api${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
        },
        ...options
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('API call failed:', error)
      throw error
    }
  }
  
  async function initializeSystem() {
    try {
      console.log('Making API call to /api/initialize...')
      const result = await apiCall('/initialize', { 
        method: 'POST',
        body: JSON.stringify({})
      })
      console.log('API response:', result)
      
      if (result.success) {
        isSystemInitialized.value = true
        // Refresh data after successful initialization
        await Promise.all([
          fetchROIs(),
          fetchStatus()
        ])
      }
      
      return result
    } catch (error) {
      console.error('Failed to initialize system:', error)
      throw error
    }
  }
  
  async function autoInitialize() {
    try {
      console.log('Auto-initializing system...')
      // Check if system is already initialized
      const statusResult = await fetchStatus()
      
      if (!isSystemInitialized.value) {
        const initResult = await initializeSystem()
        if (initResult.success) {
          console.log('✅ System auto-initialized successfully')
          return true
        }
      } else {
        console.log('✅ System already initialized')
        await fetchROIs() // Load ROIs if system was already initialized
        return true
      }
      
      return false
    } catch (error) {
      console.error('❌ Auto-initialization failed:', error)
      return false
    }
  }
  
  async function stopSystem() {
    try {
      const result = await apiCall('/stop', { 
        method: 'POST',
        body: JSON.stringify({})
      })
      if (result.success) {
        isSystemInitialized.value = false
      }
      return result
    } catch (error) {
      console.error('Failed to stop system:', error)
      throw error
    }
  }
  
  async function fetchROIs() {
    try {
      const result = await apiCall('/rois')
      rois.value = result.rois || []
      return result
    } catch (error) {
      console.error('Failed to fetch ROIs:', error)
      throw error
    }
  }
  
  async function addROI(x1: number, y1: number, x2: number, y2: number) {
    try {
      const result = await apiCall('/rois', {
        method: 'POST',
        body: JSON.stringify({ x1, y1, x2, y2 })
      })
      
      if (result.success) {
        await fetchROIs()
      }
      
      return result
    } catch (error) {
      console.error('Failed to add ROI:', error)
      throw error
    }
  }
  
  async function deleteROI(roiId: number) {
    try {
      const result = await apiCall(`/rois/${roiId}`, {
        method: 'DELETE'
      })
      
      if (result.success) {
        await fetchROIs()
      }
      
      return result
    } catch (error) {
      console.error('Failed to delete ROI:', error)
      throw error
    }
  }
  
  async function clearROIs() {
    try {
      const result = await apiCall('/rois/clear', { 
        method: 'DELETE',
        body: JSON.stringify({})
      })
      
      if (result.success) {
        rois.value = []
      }
      
      return result
    } catch (error) {
      console.error('Failed to clear ROIs:', error)
      throw error
    }
  }
  
  async function saveROIs() {
    try {
      const result = await apiCall('/rois/save', { 
        method: 'POST',
        body: JSON.stringify({})
      })
      return result
    } catch (error) {
      console.error('Failed to save ROIs:', error)
      throw error
    }
  }
  
  async function loadROIs() {
    try {
      const result = await apiCall('/rois/load', { 
        method: 'POST',
        body: JSON.stringify({})
      })
      
      if (result.success) {
        await fetchROIs()
      }
      
      return result
    } catch (error) {
      console.error('Failed to load ROIs:', error)
      throw error
    }
  }
  
  async function updateMotionConfig() {
    try {
      const result = await apiCall('/motion-config', {
        method: 'POST',
        body: JSON.stringify(config.value)
      })
      
      return result
    } catch (error) {
      console.error('Failed to update motion config:', error)
      throw error
    }
  }
  
  async function fetchMotionConfig() {
    try {
      const result = await apiCall('/motion-config')
      if (result.config) {
        config.value = result.config
      }
      return result
    } catch (error) {
      console.error('Failed to fetch motion config:', error)
      throw error
    }
  }
  
  async function fetchStatus() {
    try {
      const result = await apiCall('/status')
      stats.value = result.stats || stats.value
      isSystemInitialized.value = result.initialized || false
      return result
    } catch (error) {
      console.error('Failed to fetch status:', error)
      throw error
    }
  }
  
  // Sound notification
  function playMotionSound() {
    try {
      const audioContext = new AudioContext()
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)
      
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime)
      oscillator.frequency.setValueAtTime(400, audioContext.currentTime + 0.1)
      
      gainNode.gain.setValueAtTime(motionSoundVolume.value, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.3)
      
      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + 0.3)
    } catch (error) {
      console.error('Failed to play sound:', error)
    }
  }
  
  return {
    // State
    isConnected,
    isSystemInitialized,
    currentFrame,
    rois,
    stats,
    config,
    soundEnabled,
    motionSoundVolume,
    
    // Computed
    activeRoisCount,
    motionDetectedRois,
    hasMotionDetection,
    
    // Actions
    connectSocket,
    disconnectSocket,
    initializeSystem,
    autoInitialize,
    stopSystem,
    fetchROIs,
    addROI,
    deleteROI,
    clearROIs,
    saveROIs,
    loadROIs,
    updateMotionConfig,
    fetchMotionConfig,
    fetchStatus,
    playMotionSound
  }
})