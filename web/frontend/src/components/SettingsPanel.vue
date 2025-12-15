<template>
  <div class="space-y-6">
    <!-- Motion Detection Settings -->
    <div class="bg-white/5 border border-white/10 rounded-xl p-6">
      <h4 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span class="text-xl">🎚️</span>
        Motion Detection
      </h4>
      
      <div class="space-y-6">
        <!-- Threshold -->
        <div>
          <div class="flex justify-between items-center mb-2">
            <label class="text-white/90 font-medium">Motion Threshold</label>
            <span class="bg-white/10 px-2 py-1 rounded text-sm text-white font-mono">{{ config.threshold }}</span>
          </div>
          <input 
            type="range"
            min="100"
            max="2000"
            step="50"
            v-model.number="config.threshold"
            class="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
            @input="onConfigChange"
          />
          <p class="text-white/60 text-xs mt-1">Higher values = less sensitive to motion</p>
        </div>

        <!-- Minimum Area -->
        <div>
          <div class="flex justify-between items-center mb-2">
            <label class="text-white/90 font-medium">Minimum Area</label>
            <span class="bg-white/10 px-2 py-1 rounded text-sm text-white font-mono">{{ config.min_area }}px²</span>
          </div>
          <input 
            type="range"
            min="50"
            max="500"
            step="25"
            v-model.number="config.min_area"
            class="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
            @input="onConfigChange"
          />
          <p class="text-white/60 text-xs mt-1">Minimum size of motion to detect</p>
        </div>

        <!-- Blur Size -->
        <div>
          <div class="flex justify-between items-center mb-2">
            <label class="text-white/90 font-medium">Blur Size</label>
            <span class="bg-white/10 px-2 py-1 rounded text-sm text-white font-mono">{{ config.blur_size }}px</span>
          </div>
          <input 
            type="range"
            min="5"
            max="51"
            step="2"
            v-model.number="config.blur_size"
            class="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
            @input="onConfigChange"
          />
          <p class="text-white/60 text-xs mt-1">Noise reduction (must be odd number)</p>
        </div>

        <!-- Rain Area Threshold -->
        <div>
          <div class="flex justify-between items-center mb-2">
            <label class="text-white/90 font-medium">Rain Area Threshold</label>
            <span class="bg-white/10 px-2 py-1 rounded text-sm text-white font-mono">{{ config.rain_area_threshold }}px²</span>
          </div>
          <input 
            type="range"
            min="1000"
            max="10000"
            step="500"
            v-model.number="config.rain_area_threshold"
            class="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
            @input="onConfigChange"
          />
          <p class="text-white/60 text-xs mt-1">Rain detection sensitivity</p>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-3 pt-4 border-t border-white/10">
        <button 
          @click="saveConfig" 
          class="btn-primary-glass flex-1 justify-center"
          :disabled="loading || !hasChanges"
        >
          <span class="mr-2">{{ loading ? '⏳' : '💾' }}</span>
          {{ loading ? 'Saving...' : 'Save Settings' }}
        </button>
        
        <button 
          @click="resetConfig" 
          class="btn-danger-glass flex-1 justify-center"
          :disabled="loading"
        >
          <span class="mr-2">🔄</span>
          Reset
        </button>
      </div>

      <!-- Status Message -->
      <div v-if="message" class="mt-4 p-3 rounded-lg border" 
           :class="message.type === 'success' ? 'bg-green-500/20 border-green-500/30 text-green-300' : 'bg-red-500/20 border-red-500/30 text-red-300'">
        {{ message.text }}
      </div>
    </div>

    <!-- Settings Guide -->
    <div class="bg-white/5 border border-white/10 rounded-xl p-6">
      <h5 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span class="text-xl">ℹ️</span>
        Settings Guide
      </h5>
      <div class="space-y-3 text-sm">
        <div class="bg-white/5 rounded-lg p-3">
          <strong class="text-white/90">Motion Threshold:</strong>
          <span class="text-white/70 block mt-1">Controls sensitivity to movement. Lower = more sensitive.</span>
        </div>
        <div class="bg-white/5 rounded-lg p-3">
          <strong class="text-white/90">Minimum Area:</strong>
          <span class="text-white/70 block mt-1">Filters out small movements like leaves or insects.</span>
        </div>
        <div class="bg-white/5 rounded-lg p-3">
          <strong class="text-white/90">Blur Size:</strong>
          <span class="text-white/70 block mt-1">Reduces camera noise. Increase for noisy cameras.</span>
        </div>
        <div class="bg-white/5 rounded-lg p-3">
          <strong class="text-white/90">Rain Threshold:</strong>
          <span class="text-white/70 block mt-1">Helps distinguish between rain and actual motion.</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useDetectorStore } from '@/stores/detector'

const detectorStore = useDetectorStore()
const loading = ref(false)
const message = ref<{ type: string; text: string } | null>(null)

// Local config copy for editing
const config = reactive({
  threshold: 800,
  min_area: 100,
  blur_size: 21,
  rain_area_threshold: 5000
})

// Original config for comparison
const originalConfig = ref({ ...config })

const hasChanges = computed(() => {
  return JSON.stringify(config) !== JSON.stringify(originalConfig.value)
})

// Watch for store changes and update local config
watch(() => detectorStore.config, (newConfig) => {
  Object.assign(config, newConfig)
  originalConfig.value = { ...newConfig }
}, { immediate: true, deep: true })

// Ensure blur_size is always odd
watch(() => config.blur_size, (newValue) => {
  if (newValue % 2 === 0) {
    config.blur_size = newValue + 1
  }
})

const showMessage = (type: string, text: string) => {
  message.value = { type, text }
  setTimeout(() => {
    message.value = null
  }, 3000)
}

const onConfigChange = () => {
  // Debounced auto-save could go here
}

const saveConfig = async () => {
  loading.value = true
  try {
    // Update store config
    Object.assign(detectorStore.config, config)
    
    // Send to backend
    const result = await detectorStore.updateMotionConfig()
    
    if (result.success) {
      originalConfig.value = { ...config }
      showMessage('success', 'Settings saved successfully!')
    } else {
      showMessage('danger', result.message || 'Failed to save settings')
    }
  } catch (error) {
    showMessage('danger', 'Failed to save settings')
  } finally {
    loading.value = false
  }
}

const resetConfig = () => {
  if (!confirm('Reset all settings to default values?')) return
  
  const defaults = {
    threshold: 800,
    min_area: 100,
    blur_size: 21,
    rain_area_threshold: 5000
  }
  
  Object.assign(config, defaults)
  showMessage('info', 'Settings reset to defaults')
}
</script>

<style scoped>
.settings-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.settings-title {
  color: white;
  margin-bottom: 0;
  font-size: 1rem;
  font-weight: 600;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  font-size: 0.9rem;
}

.form-range {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  outline: none;
  accent-color: #667eea;
  cursor: pointer;
}

.form-range::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.form-range::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.range-value {
  color: #667eea;
  font-weight: 600;
  text-align: right;
  font-size: 0.9rem;
}

.field-help {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.8rem;
  font-style: italic;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.form-actions .btn {
  flex: 1;
}

.settings-message {
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
  text-align: center;
}

.settings-message.message-success {
  background: rgba(76, 175, 80, 0.1);
  border: 1px solid rgba(76, 175, 80, 0.3);
  color: #4caf50;
}

.settings-message.message-info {
  background: rgba(33, 150, 243, 0.1);
  border: 1px solid rgba(33, 150, 243, 0.3);
  color: #2196f3;
}

.settings-message.message-danger {
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  color: #f44336;
}

.settings-info {
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.info-title {
  color: white;
  margin-bottom: 1rem;
  font-size: 0.95rem;
  font-weight: 600;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-item {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.85rem;
  line-height: 1.4;
}

.info-item strong {
  color: #667eea;
  font-weight: 600;
}

@media (max-width: 600px) {
  .form-actions {
    flex-direction: column;
  }
  
  .form-actions .btn {
    width: 100%;
  }
}
</style>