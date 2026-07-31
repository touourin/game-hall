<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { WifiOff, X } from '@lucide/vue'
import {
  clearAccessToken,
  rememberAccessToken,
  requestAccessToken,
  storedAccessToken,
  validateAccessToken,
} from './access'
import { setSocketAccessToken } from './socket'
import { useRoomStore } from './stores/room'
import AccessGate from './views/AccessGate.vue'
import HomeView from './views/HomeView.vue'
import GameRoom from './views/GameRoom.vue'

const room = useRoomStore()
const accessState = ref<'checking' | 'locked' | 'unlocked'>('checking')
const accessBusy = ref(false)
const accessError = ref<string | null>(null)

function enterGame(token: string) {
  setSocketAccessToken(token)
  accessState.value = 'unlocked'
  document.title = '圆桌密令 · 阿瓦隆'
  room.init()
}

async function unlock(password: string) {
  accessBusy.value = true
  accessError.value = null
  try {
    const token = await requestAccessToken(password)
    rememberAccessToken(token)
    enterGame(token)
  } catch (caught) {
    accessError.value =
      caught instanceof Error ? caught.message : '验证失败，请稍后重试'
  } finally {
    accessBusy.value = false
  }
}

onMounted(async () => {
  const token = storedAccessToken()
  if (token && (await validateAccessToken(token))) {
    enterGame(token)
    return
  }
  clearAccessToken()
  accessState.value = 'locked'
})
</script>

<template>
  <div class="app-shell">
    <AccessGate
      v-if="accessState !== 'unlocked'"
      :checking="accessState === 'checking'"
      :busy="accessBusy"
      :error="accessError"
      @unlock="unlock"
    />

    <template v-else>
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
    </template>
  </div>
</template>
