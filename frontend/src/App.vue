<script setup lang="ts">
import { onMounted } from 'vue'
import { WifiOff, X } from '@lucide/vue'
import { useRoomStore } from './stores/room'
import HomeView from './views/HomeView.vue'
import GameRoom from './views/GameRoom.vue'

const room = useRoomStore()

onMounted(() => room.init())
</script>

<template>
  <div class="app-shell">
    <div v-if="!room.connected" class="connection-banner">
      <WifiOff :size="16" />
      正在重新连接游戏服务器…
    </div>

    <HomeView v-if="!room.snapshot" />
    <GameRoom v-else :snapshot="room.snapshot" />

    <div v-if="room.error" class="toast" role="alert">
      <span>{{ room.error }}</span>
      <button class="icon-button" aria-label="关闭提示" @click="room.clearError">
        <X :size="18" />
      </button>
    </div>

    <div v-if="room.busy" class="busy-indicator" aria-label="正在处理">
      <span />
      <span />
      <span />
    </div>
  </div>
</template>
