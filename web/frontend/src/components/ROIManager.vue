<template>
  <div class="space-y-4">
    <!-- Empty State -->
    <div v-if="detectorStore.rois.length === 0" class="text-center py-12">
      <div class="inline-flex items-center justify-center w-16 h-16 bg-white/10 rounded-full mb-4">
        <span class="text-3xl">🎯</span>
      </div>
      <h3 class="text-lg font-semibold text-white mb-2">No Detection Zones</h3>
      <p class="text-white/60 mb-4">Create detection zones by drawing on the camera feed</p>
      <div class="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-300 text-sm">
        <span>💡</span>
        Click and drag on the camera feed above
      </div>
    </div>

    <!-- ROI List -->
    <div v-else class="space-y-3">
      <div 
        v-for="roi in detectorStore.rois" 
        :key="roi.id"
        class="bg-white/5 border rounded-xl p-4 transition-all duration-200 hover:bg-white/10"
        :class="roi.motion_detected ? 'border-red-500/50 bg-red-500/5' : 'border-white/10'"
      >
        <!-- ROI Header -->
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg flex items-center justify-center" 
                 :class="roi.motion_detected ? 'bg-red-500/20' : 'bg-yellow-500/20'">
              <span class="text-lg">{{ roi.motion_detected ? '🔴' : '🟡' }}</span>
            </div>
            <div>
              <h4 class="font-semibold text-white">Zone {{ roi.id }}</h4>
              <p class="text-xs text-white/60">{{ roi.width }} × {{ roi.height }} pixels</p>
            </div>
          </div>
          <button 
            @click="deleteROI(roi.id)" 
            class="w-8 h-8 bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 rounded-lg flex items-center justify-center text-red-400 hover:text-red-300 transition-colors"
            title="Delete Zone"
          >
            🗑️
          </button>
        </div>
        
        <!-- ROI Status -->
        <div class="flex items-center justify-between">
          <div class="text-xs text-white/70">
            Position: ({{ roi.x1 }}, {{ roi.y1 }})
          </div>
          <div class="px-3 py-1 rounded-full text-xs font-medium" 
               :class="roi.motion_detected ? 'bg-red-500/20 text-red-300 border border-red-500/30' : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'">
            {{ roi.motion_detected ? 'Motion Detected!' : 'Monitoring' }}
          </div>
        </div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="mt-6 pt-4 border-t border-white/10">
      <div class="flex gap-4 flex-wrap">
        <button 
          @click="clearAllROIs" 
          class="btn-danger-glass flex-1 min-w-32 justify-center"
          :disabled="detectorStore.rois.length === 0 || loading"
        >
          <span class="mr-2">🗑️</span>
          Clear All
        </button>
        
        <button 
          @click="saveROIs" 
          class="btn-success-glass flex-1 min-w-32 justify-center"
          :disabled="detectorStore.rois.length === 0 || loading"
        >
          <span class="mr-2">💾</span>
          Save ROIs
        </button>
        
        <button 
          @click="loadROIs" 
          class="btn-primary-glass flex-1 min-w-32 justify-center"
          :disabled="loading"
        >
          <span class="mr-2">📁</span>
          Load ROIs
        </button>
      </div>
      
      <div v-if="actionMessage" class="mt-4 p-3 rounded-lg border text-sm" 
           :class="{
             'bg-green-500/20 border-green-500/30 text-green-300': actionMessage.type === 'success',
             'bg-yellow-500/20 border-yellow-500/30 text-yellow-300': actionMessage.type === 'warning', 
             'bg-red-500/20 border-red-500/30 text-red-300': actionMessage.type === 'danger'
           }">
        {{ actionMessage.text }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDetectorStore } from '@/stores/detector'

const detectorStore = useDetectorStore()
const loading = ref(false)
const actionMessage = ref<{ type: string; text: string } | null>(null)

const showMessage = (type: string, text: string) => {
  actionMessage.value = { type, text }
  setTimeout(() => {
    actionMessage.value = null
  }, 3000)
}

const deleteROI = async (roiId: number) => {
  loading.value = true
  try {
    const result = await detectorStore.deleteROI(roiId)
    if (result.success) {
      showMessage('success', `ROI ${roiId} deleted successfully`)
    } else {
      showMessage('danger', result.message || 'Failed to delete ROI')
    }
  } catch (error) {
    console.error(error);
    showMessage('danger', 'Failed to delete ROI')
  } finally {
    loading.value = false
  }
}

const clearAllROIs = async () => {
  if (!confirm('Are you sure you want to clear all ROIs?')) return
  
  loading.value = true
  try {
    const result = await detectorStore.clearROIs()
    if (result.success) {
      showMessage('success', 'All ROIs cleared successfully')
    } else {
      showMessage('danger', result.message || 'Failed to clear ROIs')
    }
  } catch (error) {
    console.error(error);
    showMessage('danger', 'Failed to clear ROIs')
  } finally {
    loading.value = false
  }
}

const saveROIs = async () => {
  loading.value = true
  try {
    const result = await detectorStore.saveROIs()
    if (result.success) {
      showMessage('success', `Saved ${detectorStore.rois.length} ROIs successfully`)
    } else {
      showMessage('danger', result.message || 'Failed to save ROIs')
    }
  } catch (error) {
    console.error(error);
    showMessage('danger', 'Failed to save ROIs')
  } finally {
    loading.value = false
  }
}

const loadROIs = async () => {
  loading.value = true
  try {
    const result = await detectorStore.loadROIs()
    if (result.success) {
      showMessage('success', `Loaded ${detectorStore.rois.length} ROIs successfully`)
    } else {
      showMessage('warning', result.message || 'No saved ROIs found')
    }
  } catch (error) {
    console.error(error);
    showMessage('danger', 'Failed to load ROIs')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.roi-manager {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.no-rois {
  text-align: center;
  padding: 2rem;
  color: rgba(255, 255, 255, 0.7);
}

.no-rois-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.hint {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 0.5rem;
}

.roi-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.roi-item {
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.roi-item.roi-motion {
  border-color: rgba(244, 67, 54, 0.5);
  background: rgba(244, 67, 54, 0.1);
  animation: pulse 2s infinite;
}

.roi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.roi-id {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: white;
  font-size: 1rem;
}

.roi-icon {
  font-size: 1.2rem;
}

.btn-delete {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.btn-delete:hover {
  background: rgba(244, 67, 54, 0.2);
  transform: scale(1.1);
}

.roi-details {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 1rem;
}

.roi-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.info-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.info-value {
  color: white;
  font-weight: 500;
  font-size: 0.9rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge.status-success {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.status-badge.status-danger {
  background: rgba(244, 67, 54, 0.2);
  color: #f44336;
  border: 1px solid rgba(244, 67, 54, 0.3);
}

.roi-actions {
  margin-top: auto;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.action-buttons .btn {
  flex: 1;
  min-width: 120px;
}

.action-message {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
}

.action-message.message-success {
  background: rgba(76, 175, 80, 0.1);
  border: 1px solid rgba(76, 175, 80, 0.3);
  color: #4caf50;
}

.action-message.message-warning {
  background: rgba(255, 152, 0, 0.1);
  border: 1px solid rgba(255, 152, 0, 0.3);
  color: #ff9800;
}

.action-message.message-danger {
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  color: #f44336;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Scrollbar styling */
.roi-list::-webkit-scrollbar {
  width: 6px;
}

.roi-list::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.roi-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.roi-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

@media (max-width: 600px) {
  .roi-details {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .action-buttons .btn {
    width: 100%;
  }
}
</style>