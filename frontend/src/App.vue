<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { WifiOff, X } from '@lucide/vue'
import {
  clearAccountToken,
  loginAccount,
  logoutAccount,
  registerAccount,
  rememberAccountToken,
  storedAccountToken,
  validateAccountToken,
  type AccountProfile,
} from './account'
import {
  clearAccessToken,
  rememberAccessToken,
  requestAccessToken,
  storedAccessToken,
  validateAccessToken,
} from './access'
import {
  setSocketAccessToken,
  setSocketAccountToken,
  socket,
} from './socket'
import { useRoomStore } from './games/avalon/store'
import { useArcadeStore } from './stores/arcade'
import type { GameCatalogItem } from './types/arcade'
import AccessGate from './views/AccessGate.vue'
import AccountGate from './views/AccountGate.vue'
import HomeView from './views/HomeView.vue'
import GameRoom from './games/avalon/GameRoom.vue'
import GameHall from './views/GameHall.vue'
import ArcadeHome from './views/ArcadeHome.vue'
import ArcadeRoom from './views/ArcadeRoom.vue'

const room = useRoomStore()
const arcade = useArcadeStore()
const accessState = ref<'checking' | 'locked' | 'unlocked'>('checking')
const accessBusy = ref(false)
const accessError = ref<string | null>(null)
const activeAccessToken = ref('')
const accountState = ref<'checking' | 'locked' | 'authenticated'>('checking')
const accountBusy = ref(false)
const accountError = ref<string | null>(null)
const account = ref<AccountProfile | null>(null)
const selectedGame = ref<GameCatalogItem | null>(initialSelectedGame())

function initialSelectedGame(): GameCatalogItem | null {
  const params = new URLSearchParams(window.location.search)
  const gameKey = params.get('game')
  const catalog: Record<string, GameCatalogItem> = {
    avalon: { key: 'avalon', name: '阿瓦隆', players: '5–10 人', description: '身份推理与团队博弈' },
    gomoku: { key: 'gomoku', name: '五子棋', players: '2 人', description: '15 路棋盘，率先连成五子' },
    xiangqi: { key: 'xiangqi', name: '中国象棋', players: '2 人', description: '楚河汉界，完整走子规则' },
    go: { key: 'go', name: '围棋', players: '2 人', description: '19 路中国规则' },
    doudizhu: { key: 'doudizhu', name: '斗地主', players: '3 人', description: '叫地主与完整牌型对战' },
  }
  if (gameKey && catalog[gameKey]) return catalog[gameKey]
  if (params.get('room')) return catalog.avalon
  return null
}

function enterGame(profile: AccountProfile, token: string) {
  account.value = profile
  accountState.value = 'authenticated'
  rememberAccountToken(token)
  setSocketAccountToken(token)
  document.title = '私人游戏大厅'
  room.init()
  arcade.init()
  if (!socket.connected) socket.connect()
}

async function continueAfterAccess(token: string) {
  activeAccessToken.value = token
  setSocketAccessToken(token)
  accessState.value = 'unlocked'
  accountState.value = 'checking'
  const savedAccountToken = storedAccountToken()
  if (savedAccountToken) {
    try {
      const profile = await validateAccountToken(token, savedAccountToken)
      if (profile) {
        enterGame(profile, savedAccountToken)
        return
      }
    } catch (caught) {
      accountError.value =
        caught instanceof Error ? caught.message : '无法验证登录状态'
    }
  }
  clearAccountToken()
  accountState.value = 'locked'
}

async function unlock(password: string) {
  accessBusy.value = true
  accessError.value = null
  try {
    const token = await requestAccessToken(password)
    rememberAccessToken(token)
    await continueAfterAccess(token)
  } catch (caught) {
    accessError.value =
      caught instanceof Error ? caught.message : '验证失败，请稍后重试'
  } finally {
    accessBusy.value = false
  }
}

async function login(payload: { username: string; password: string }) {
  accountBusy.value = true
  accountError.value = null
  try {
    const response = await loginAccount(activeAccessToken.value, payload)
    enterGame(response.account, response.token)
  } catch (caught) {
    accountError.value =
      caught instanceof Error ? caught.message : '登录失败，请稍后重试'
  } finally {
    accountBusy.value = false
  }
}

async function register(payload: {
  username: string
  password: string
  displayName: string
}) {
  accountBusy.value = true
  accountError.value = null
  try {
    const response = await registerAccount(activeAccessToken.value, {
      username: payload.username,
      password: payload.password,
      display_name: payload.displayName,
    })
    enterGame(response.account, response.token)
  } catch (caught) {
    accountError.value =
      caught instanceof Error ? caught.message : '注册失败，请稍后重试'
  } finally {
    accountBusy.value = false
  }
}

async function logout() {
  const token = storedAccountToken()
  if (token) {
    try {
      await logoutAccount(activeAccessToken.value, token)
    } catch {
      // 本地退出仍然有效，服务端会在会话过期后清理令牌。
    }
  }
  clearAccountToken()
  setSocketAccountToken('')
  socket.disconnect()
  room.resetForLogout()
  arcade.resetForLogout()
  account.value = null
  accountError.value = null
  accountState.value = 'locked'
}

onMounted(async () => {
  const token = storedAccessToken()
  if (token && (await validateAccessToken(token))) {
    await continueAfterAccess(token)
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

    <AccountGate
      v-else-if="accountState !== 'authenticated'"
      :busy="accountBusy || accountState === 'checking'"
      :error="accountError"
      @login="login"
      @register="register"
    />

    <template v-else-if="account">
    <div v-if="!room.connected" class="connection-banner">
      <WifiOff :size="16" />
      正在重新连接游戏服务器…
    </div>

    <GameRoom v-if="room.snapshot" :snapshot="room.snapshot" />
    <ArcadeRoom v-else-if="arcade.snapshot" :snapshot="arcade.snapshot" />
    <GameHall
      v-else-if="!selectedGame"
      :account="account"
      @logout="logout"
      @select="selectedGame = $event"
    />
    <HomeView
      v-else-if="selectedGame.key === 'avalon'"
      :account="account"
      @logout="logout"
      @back="selectedGame = null"
    />
    <ArcadeHome
      v-else
      :account="account"
      :game="selectedGame"
      @back="selectedGame = null"
    />

    <div v-if="room.error || arcade.error" class="toast" role="alert">
      <span>{{ room.error || arcade.error }}</span>
      <button class="icon-button" aria-label="关闭提示" @click="room.clearError(); arcade.clearError()">
        <X :size="18" />
      </button>
    </div>

    <div v-if="room.busy || arcade.busy" class="busy-indicator" aria-label="正在处理">
      <span />
      <span />
      <span />
    </div>
    </template>
  </div>
</template>
