<template>
  <div class="space-y-6">
    <!-- Stats Grid -->
    <div class="grid grid-cols-2 gap-4">
      <!-- Camera Status -->
      <div class="bg-linear-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/20 rounded-xl p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-blue-300 text-sm font-medium">Camera Status</span>
          <span class="text-2xl">📷</span>
        </div>
        <div class="text-xl font-bold" :class="cameraStatusClass">
          {{ detectorStore.stats.camera_status }}
        </div>
      </div>

      <!-- FPS -->
      <div class="bg-linear-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-xl p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-green-300 text-sm font-medium">FPS</span>
          <span class="text-2xl">⚡</span>
        </div>
        <div class="text-xl font-bold text-white">
          {{ Math.round(detectorStore.stats.fps) }}
        </div>
      </div>

      <!-- Active ROIs -->
      <div class="bg-linear-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-xl p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-purple-300 text-sm font-medium">Active ROIs</span>
          <span class="text-2xl">🎯</span>
        </div>
        <div class="text-xl font-bold" :class="roiStatusClass">
          {{ detectorStore.activeRoisCount }}
        </div>
      </div>

      <!-- Total Detections -->
      <div class="bg-linear-to-r from-orange-500/10 to-red-500/10 border border-orange-500/20 rounded-xl p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-orange-300 text-sm font-medium">Detections</span>
          <span class="text-2xl">🚨</span>
        </div>
        <div class="text-xl font-bold text-white">
          {{ detectorStore.stats.total_detections }}
        </div>
      </div>
    </div>

    <!-- Motion Alert -->
    <div v-if="detectorStore.hasMotionDetection" class="bg-linear-to-r from-red-500/20 to-pink-500/20 border-2 border-red-500/40 rounded-2xl p-6 animate-pulse">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 bg-red-500/30 rounded-full flex items-center justify-center">
          <span class="text-2xl">🚨</span>
        </div>
        <div>
          <h3 class="text-xl font-bold text-red-200 mb-1">Motion Detected!</h3>
          <p class="text-red-300/80">
            Movement detected in {{ detectorStore.motionDetectedRois.length }} zone(s): 
            <span class="font-semibold">{{ detectorStore.stats.motion_detected_rois.join(', ') }}</span>
          </p>
        </div>
      </div>
    </div>

    <!-- Rain Detection Alert -->
    <div v-if="detectorStore.stats.rain_detected" class="bg-linear-to-r from-blue-500/20 to-indigo-500/20 border border-blue-500/30 rounded-xl p-4">
      <div class="flex items-center gap-3">
        <span class="text-2xl">🌧️</span>
        <div>
          <h4 class="text-blue-200 font-semibold">Rain Detected</h4>
          <p class="text-blue-300/70 text-sm">Motion sensitivity automatically adjusted</p>
        </div>
      </div>
    </div>

    <!-- Sound Controls -->
    <div class="bg-white/5 border border-white/10 rounded-xl p-6">
      <h4 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span class="text-xl">🔊</span>
        Sound Settings
      </h4>
      
      <div class="space-y-4">
        <label class="flex items-center gap-3 cursor-pointer">
          <div class="relative">
            <input 
              type="checkbox" 
              v-model="detectorStore.soundEnabled"
              class="sr-only peer"
            />
            <div class="w-11 h-6 bg-white/20 rounded-full peer peer-checked:bg-blue-500 transition-colors"></div>
            <div class="absolute left-[2px] top-[2px] w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
          </div>
          <span class="text-white/90 font-medium">Enable sound notifications</span>
        </label>
        
        <div v-if="detectorStore.soundEnabled" class="pl-14">
          <label class="block text-white/70 text-sm mb-2">Volume</label>
          <input 
            type="range" 
            min="0" 
            max="1" 
            step="0.1"
            v-model.number="detectorStore.motionSoundVolume"
            class="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
          />
          <div class="flex justify-between text-xs text-white/60 mt-1">
            <span>0%</span>
            <span class="font-medium text-white/80">{{ Math.round(detectorStore.motionSoundVolume * 100) }}%</span>
            <span>100%</span>
          </div>
        </div>
        
        <button 
          @click="testSound" 
          class="btn-primary-glass w-full justify-center"
          :disabled="!detectorStore.soundEnabled"
        >
          <span class="mr-2">🎵</span>
          Test Sound
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDetectorStore } from '@/stores/detector'

const detectorStore = useDetectorStore()

const cameraStatusClass = computed(() => {
  const status = detectorStore.stats.camera_status
  if (status === 'connected') return 'text-green-400'
  if (status === 'disconnected') return 'text-red-400'
  return 'text-yellow-400'
})

const roiStatusClass = computed(() => {
  return detectorStore.activeRoisCount > 0 ? 'text-green-400' : 'text-yellow-400'
})

const testSound = () => {
  detectorStore.playMotionSound()
}
</script>

<style scoped>
/* Custom range slider styling */
input[type="range"]::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid #1e40af;
}

input[type="range"]::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid #1e40af;
}
</style>