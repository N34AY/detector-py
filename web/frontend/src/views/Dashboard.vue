<template>
  <div class="container mx-auto px-6 py-6 space-y-8">
    <!-- System Controls -->
    <div class="glass-card">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-white flex items-center gap-3">
          <span class="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center text-xl">🎮</span>
          System Controls
        </h2>
        <div class="flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium" :class="detectorStore.isSystemInitialized ? 'bg-green-500/20 text-green-300 border border-green-500/30' : 'bg-red-500/20 text-red-300 border border-red-500/30'">
          <div class="w-2 h-2 rounded-full" :class="detectorStore.isSystemInitialized ? 'bg-green-400' : 'bg-red-400'"></div>
          {{ detectorStore.isSystemInitialized ? 'Active' : 'Inactive' }}
        </div>
      </div>
      
      <div class="flex gap-4 flex-wrap mb-6">
        <button 
          v-if="!detectorStore.isSystemInitialized" 
          @click="initializeSystem"
          class="btn-primary-glass flex-1 sm:flex-none"
          :disabled="loading"
        >
          <span class="mr-2">{{ loading ? '⏳' : '🚀' }}</span>
          {{ loading ? 'Initializing...' : 'Start System' }}
        </button>
        
        <button 
          v-if="detectorStore.isSystemInitialized" 
          @click="stopSystem"
          class="btn-danger-glass flex-1 sm:flex-none"
          :disabled="loading"
        >
          <span class="mr-2">{{ loading ? '⏳' : '⏹️' }}</span>
          {{ loading ? 'Stopping...' : 'Stop System' }}
        </button>
        
        <button @click="refreshData" class="btn-success-glass flex-1 sm:flex-none" :disabled="loading">
          <span class="mr-2">🔄</span>
          Refresh
        </button>
      </div>
      
      <div v-if="alert" class="alert-glass" :class="`alert-${alert.type}`">
        <div class="flex items-center gap-2">
          <span class="text-lg">{{ alert.type === 'success' ? '✅' : alert.type === 'danger' ? '❌' : 'ℹ️' }}</span>
          {{ alert.message }}
        </div>
      </div>
      
      <!-- Auto-initialization status -->
      <div v-if="!detectorStore.isSystemInitialized && !showManualControls" class="text-center p-8 bg-linear-to-r from-blue-500/10 to-purple-500/10 rounded-2xl border border-white/10">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-white/10 rounded-full mb-4">
          <div class="text-3xl animate-spin">⏳</div>
        </div>
        <h3 class="text-xl font-semibold text-white mb-2">Initializing System</h3>
        <p class="text-white/70 mb-4">Please wait while we start the detection system...</p>
        <button @click="showManualControls = true" class="btn-glass">
          Switch to Manual Control
        </button>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
      <!-- Camera Feed - Takes 2/3 width on large screens -->
      <div class="xl:col-span-2">
        <div class="glass-card h-full">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-2xl font-bold text-white flex items-center gap-3">
              <span class="w-10 h-10 bg-linear-to-br from-green-400 to-blue-500 rounded-lg flex items-center justify-center text-xl">📹</span>
              Camera Feed
            </h3>
            <div class="flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30">
              <div class="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></div>
              Live
            </div>
          </div>
          <CameraFeed />
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-8">
        <!-- System Stats -->
        <div class="glass-card">
          <h3 class="text-xl font-bold text-white mb-6 flex items-center gap-3">
            <span class="w-8 h-8 bg-linear-to-br from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center text-lg">📊</span>
            System Status
          </h3>
          <SystemStats />
        </div>

        <!-- ROI Management -->
        <div class="glass-card">
          <h3 class="text-xl font-bold text-white mb-6 flex items-center gap-3">
            <span class="w-8 h-8 bg-linear-to-br from-red-400 to-pink-500 rounded-lg flex items-center justify-center text-lg">🎯</span>
            Detection Zones
          </h3>
          <ROIManager />
        </div>

        <!-- Settings -->
        <div class="glass-card">
          <h3 class="text-xl font-bold text-white mb-6 flex items-center gap-3">
            <span class="w-8 h-8 bg-linear-to-br from-purple-400 to-indigo-500 rounded-lg flex items-center justify-center text-lg">⚙️</span>
            Settings
          </h3>
          <SettingsPanel />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useDetectorStore } from '@/stores/detector'
import CameraFeed from '@/components/CameraFeed.vue'
import SystemStats from '@/components/SystemStats.vue'
import ROIManager from '@/components/ROIManager.vue'
import SettingsPanel from '@/components/SettingsPanel.vue'

const detectorStore = useDetectorStore()
const loading = ref(false)
const alert = ref<{ type: string; message: string } | null>(null)
const showManualControls = ref(false)

const showAlert = (type: string, message: string) => {
  alert.value = { type, message }
  setTimeout(() => {
    alert.value = null
  }, 5000)
}

// Watch for initialization changes
watch(() => detectorStore.isSystemInitialized, (newValue) => {
  if (newValue) {
    showManualControls.value = true // Show controls once initialized
  }
})

const initializeSystem = async () => {
  loading.value = true
  try {
    console.log('Starting system initialization...')
    const result = await detectorStore.initializeSystem()
    console.log('Initialization result:', result)
    
    if (result.success) {
      showAlert('success', 'System initialized successfully!')
      showManualControls.value = true
    } else {
      const errorMsg = result.message || result.error || 'Failed to initialize system'
      console.error('Initialization failed:', errorMsg)
      showAlert('danger', `Initialization failed: ${errorMsg}`)
    }
  } catch (error) {
    console.error('Initialization error:', error)
    showAlert('danger', `Failed to initialize system: ${error}`)
  } finally {
    loading.value = false
  }
}

const stopSystem = async () => {
  loading.value = true
  try {
    const result = await detectorStore.stopSystem()
    if (result.success) {
      showAlert('success', 'System stopped successfully!')
    } else {
      showAlert('danger', result.message || 'Failed to stop system')
    }
  } catch (error) {
    showAlert('danger', 'Failed to stop system')
    console.error(error);
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      detectorStore.fetchStatus(),
      detectorStore.fetchROIs(),
      detectorStore.fetchMotionConfig()
    ])
    showAlert('success', 'Data refreshed successfully!')
  } catch (error) {
    showAlert('danger', 'Failed to refresh data')
    console.error(error);
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // Auto-initialization is handled by App.vue
  // Just show manual controls after a delay if not initialized
  setTimeout(() => {
    if (!detectorStore.isSystemInitialized) {
      showManualControls.value = true
    }
  }, 3000) // Show manual controls after 3 seconds if auto-init hasn't worked
})
</script>

<style scoped>
/* Custom animations for Vue components */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 2s linear infinite;
}

/* Button disabled styles */
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

button:disabled:hover {
  transform: none !important;
}
</style>