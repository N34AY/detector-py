<template>
  <div class="relative w-full h-full">
    <!-- Camera Feed Container -->
    <div class="relative bg-black rounded-2xl overflow-hidden border border-white/10 shadow-2xl">
      <!-- No Camera State -->
      <div v-if="!detectorStore.currentFrame" class="aspect-video flex items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800">
        <div class="text-center p-8">
          <div class="inline-flex items-center justify-center w-20 h-20 bg-white/10 rounded-full mb-6">
            <span class="text-4xl">📹</span>
          </div>
          <h3 class="text-xl font-semibold text-white mb-2">
            {{ detectorStore.isSystemInitialized ? 'Waiting for Camera' : 'Camera Offline' }}
          </h3>
          <p class="text-white/60">
            {{ detectorStore.isSystemInitialized ? 'Connecting to camera feed...' : 'Please initialize the system to start camera' }}
          </p>
          <div v-if="detectorStore.isSystemInitialized" class="mt-4 flex items-center justify-center gap-2 text-blue-400">
            <div class="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
            <div class="w-2 h-2 bg-blue-400 rounded-full animate-pulse" style="animation-delay: 0.2s"></div>
            <div class="w-2 h-2 bg-blue-400 rounded-full animate-pulse" style="animation-delay: 0.4s"></div>
          </div>
        </div>
      </div>
      
      <!-- Live Camera Feed -->
      <div v-else class="relative group cursor-crosshair" @mousedown="startDrawingROI" @mousemove="continueDrawingROI" @mouseup="finishDrawingROI">
        <img 
          ref="cameraImage"
          :src="`data:image/jpeg;base64,${detectorStore.currentFrame}`" 
          alt="Live Camera Feed"
          class="w-full h-auto block transition-transform duration-200 group-hover:scale-[1.01]"
          @load="onImageLoad"
        />
        <canvas 
          ref="roiCanvas"
          class="absolute top-0 left-0 w-full h-full pointer-events-none z-10"
          :width="canvasSize.width"
          :height="canvasSize.height"
        ></canvas>
        
        <!-- Live indicator -->
        <div class="absolute top-4 right-4 flex items-center gap-2 bg-black/50 backdrop-blur-sm px-3 py-1 rounded-full">
          <div class="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
          <span class="text-white text-sm font-medium">LIVE</span>
        </div>
        
        <!-- ROI Drawing Hint -->
        <div class="absolute bottom-4 left-4 right-4 bg-black/50 backdrop-blur-sm rounded-lg p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <p class="text-white/90 text-sm text-center">
            <span class="font-medium">Click and drag</span> to create detection zones
          </p>
        </div>
      </div>
    </div>
    
    <!-- Instructions Panel -->
    <div v-if="detectorStore.isSystemInitialized" class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="bg-linear-to-r from-yellow-500/10 to-amber-500/10 border border-yellow-500/20 rounded-xl p-4">
        <div class="flex items-center gap-3 mb-2">
          <div class="w-3 h-3 bg-yellow-400 rounded-full"></div>
          <span class="text-yellow-300 font-medium">Monitoring Zones</span>
        </div>
        <p class="text-white/70 text-sm">Areas actively being monitored for motion</p>
      </div>
      
      <div class="bg-linear-to-r from-red-500/10 to-pink-500/10 border border-red-500/20 rounded-xl p-4">
        <div class="flex items-center gap-3 mb-2">
          <div class="w-3 h-3 bg-red-400 rounded-full animate-pulse"></div>
          <span class="text-red-300 font-medium">Motion Detected</span>
        </div>
        <p class="text-white/70 text-sm">Zones where movement has been detected</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useDetectorStore } from '@/stores/detector'

const detectorStore = useDetectorStore()
const cameraImage = ref<HTMLImageElement>()
const roiCanvas = ref<HTMLCanvasElement>()
const canvasSize = ref({ width: 640, height: 480 })

// ROI drawing state
const isDrawing = ref(false)
const startPoint = ref({ x: 0, y: 0 })
const currentPoint = ref({ x: 0, y: 0 })

const onImageLoad = async () => {
  await nextTick()
  if (cameraImage.value) {
    const rect = cameraImage.value.getBoundingClientRect()
    canvasSize.value = { width: rect.width, height: rect.height }
    drawROIs()
  }
}

const getMousePosition = (event: MouseEvent) => {
  if (!cameraImage.value) return { x: 0, y: 0 }
  
  const rect = cameraImage.value.getBoundingClientRect()
  const scaleX = cameraImage.value.naturalWidth / rect.width
  const scaleY = cameraImage.value.naturalHeight / rect.height
  
  return {
    x: (event.clientX - rect.left) * scaleX,
    y: (event.clientY - rect.top) * scaleY
  }
}

const startDrawingROI = (event: MouseEvent) => {
  if (!detectorStore.isSystemInitialized) return
  
  const pos = getMousePosition(event)
  startPoint.value = pos
  currentPoint.value = pos
  isDrawing.value = true
  event.preventDefault()
}

const continueDrawingROI = (event: MouseEvent) => {
  if (!isDrawing.value) return
  
  currentPoint.value = getMousePosition(event)
  drawTemporaryROI()
}

const finishDrawingROI = async (event: MouseEvent) => {
  if (!isDrawing.value) return
  
  const endPoint = getMousePosition(event)
  isDrawing.value = false
  
  // Check if ROI is large enough
  const width = Math.abs(endPoint.x - startPoint.value.x)
  const height = Math.abs(endPoint.y - startPoint.value.y)
  
  if (width > 50 && height > 50) {
    try {
      await detectorStore.addROI(
        Math.min(startPoint.value.x, endPoint.x),
        Math.min(startPoint.value.y, endPoint.y),
        Math.max(startPoint.value.x, endPoint.x),
        Math.max(startPoint.value.y, endPoint.y)
      )
    } catch (error) {
      console.error('Failed to add ROI:', error)
    }
  }
  
  drawROIs()
}

const drawTemporaryROI = () => {
  if (!roiCanvas.value || !isDrawing.value) return
  
  const ctx = roiCanvas.value.getContext('2d')
  if (!ctx || !cameraImage.value) return
  
  drawROIs() // Clear and redraw existing ROIs
  
  // Draw temporary ROI
  const rect = cameraImage.value.getBoundingClientRect()
  const scaleX = rect.width / cameraImage.value.naturalWidth
  const scaleY = rect.height / cameraImage.value.naturalHeight
  
  const x1 = startPoint.value.x * scaleX
  const y1 = startPoint.value.y * scaleY
  const x2 = currentPoint.value.x * scaleX
  const y2 = currentPoint.value.y * scaleY
  
  ctx.strokeStyle = '#00ff00'
  ctx.lineWidth = 3
  ctx.setLineDash([5, 5])
  ctx.strokeRect(
    Math.min(x1, x2),
    Math.min(y1, y2),
    Math.abs(x2 - x1),
    Math.abs(y2 - y1)
  )
  
  ctx.fillStyle = '#00ff00'
  ctx.font = '14px Arial'
  ctx.fillText('New ROI', Math.min(x1, x2), Math.min(y1, y2) - 5)
}

const drawROIs = () => {
  if (!roiCanvas.value || !cameraImage.value) return
  
  const ctx = roiCanvas.value.getContext('2d')
  if (!ctx) return
  
  // Clear canvas
  ctx.clearRect(0, 0, roiCanvas.value.width, roiCanvas.value.height)
  
  // Get scaling factors
  const rect = cameraImage.value.getBoundingClientRect()
  const scaleX = rect.width / cameraImage.value.naturalWidth
  const scaleY = rect.height / cameraImage.value.naturalHeight
  
  // Draw each ROI
  detectorStore.rois.forEach(roi => {
    const x1 = roi.x1 * scaleX
    const y1 = roi.y1 * scaleY
    const x2 = roi.x2 * scaleX
    const y2 = roi.y2 * scaleY
    
    // Color based on motion detection
    const color = roi.motion_detected ? '#ff0000' : '#ffff00'
    const label = roi.motion_detected ? `ROI ${roi.id} - MOTION!` : `ROI ${roi.id}`
    
    ctx.strokeStyle = color
    ctx.lineWidth = roi.motion_detected ? 3 : 2
    ctx.setLineDash([])
    
    // Draw rectangle
    ctx.strokeRect(
      Math.min(x1, x2),
      Math.min(y1, y2),
      Math.abs(x2 - x1),
      Math.abs(y2 - y1)
    )
    
    // Draw label with background
    ctx.fillStyle = color
    ctx.font = '14px Arial'
    const textMetrics = ctx.measureText(label)
    const textX = Math.min(x1, x2)
    const textY = Math.min(y1, y2) - 5
    
    ctx.fillRect(textX, textY - 18, textMetrics.width + 10, 20)
    ctx.fillStyle = '#000000'
    ctx.fillText(label, textX + 5, textY - 5)
  })
}

// Watch for ROI updates to redraw
watch(() => detectorStore.rois, drawROIs, { deep: true })
watch(() => detectorStore.currentFrame, () => {
  nextTick(() => {
    if (cameraImage.value) {
      onImageLoad()
    }
  })
})
</script>
