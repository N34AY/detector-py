<template>
  <div class="min-h-screen">
    <!-- Navigation Header -->
    <nav class="glass-navbar sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-6 py-4">
        <div class="flex items-center justify-between">
          <!-- Logo & Title -->
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center text-2xl">
              🎯
            </div>
            <div>
              <h1 class="text-xl font-bold text-white">Motion Detection System</h1>
              <p class="text-white/60 text-sm">AI-Powered Security Monitoring</p>
            </div>
          </div>
          
          <!-- Connection Status -->
          <div class="flex items-center gap-4">
            <div 
              class="flex items-center gap-3 px-4 py-2 rounded-full font-medium transition-all duration-300"
              :class="detectorStore.isConnected ? 'status-connected' : 'status-disconnected'"
            >
              <div class="w-3 h-3 rounded-full" 
                   :class="detectorStore.isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'">
              </div>
              <span class="text-sm">
                {{ detectorStore.isConnected ? 'Connected' : 'Disconnected' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="relative">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { RouterView } from 'vue-router'
import { useDetectorStore } from '@/stores/detector'

const detectorStore = useDetectorStore()

onMounted(async () => {
  console.log('🚀 Starting Motion Detection App...')
  
  // Connect WebSocket first
  detectorStore.connectSocket()
  
  // Wait a moment for connection to establish
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // Auto-initialize the detection system
  try {
    await detectorStore.autoInitialize()
  } catch (error) {
    console.error('Auto-initialization failed:', error)
  }
})

onUnmounted(() => {
  detectorStore.disconnectSocket()
})
</script>
