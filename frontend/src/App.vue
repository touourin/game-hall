<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { WifiOff, X } from '@lucide/vue'
import {
  clearAccountToken,
  createGuestSession,
  loginAccount,
  logoutAccount,
  renamePlayer,
  selectAvatarPreset,
  registerAccount,
  rememberAccountToken,
  storedAccountToken,
  validateAccountToken,
  uploadAvatar,
  type AvatarPresetId,
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
import { useArcadeStore } from './stores/arcade'
import { gameCatalogItem } from './gameCatalog'
import type { ArcadeGameKey, GameCatalogItem } from './types/arcade'
import AccessGate from './views/AccessGate.vue'
import AccountGate from './views/AccountGate.vue'
import ArcadeHome from './views/ArcadeHome.vue'
import SettingsModal from './components/SettingsModal.vue'

const arcade = useArcadeStore()
const route = useRoute()
const router = useRouter()
const accessState = ref<'checking' | 'locked' | 'unlocked'>('checking')
const accessBusy = ref(false)
const accessError = ref<string | null>(null)
const activeAccessToken = ref('')
const accountState = ref<'checking' | 'locked' | 'authenticated'>('checking')
const accountBusy = ref(false)
const accountError = ref<string | null>(null)
const account = ref<AccountProfile | null>(null)
const showSettings = ref(false)
const selectedGame = computed(() => gameCatalogItem(route.params.gameKey))
const invitedRoomCode = computed(() => (
  route.name === 'room' && typeof route.params.roomCode === 'string'
    ? route.params.roomCode
    : ''
))
const routedRoomSnapshot = computed(() => {
  if (route.name !== 'room' || !arcade.snapshot || !selectedGame.value) return null
  return arcade.snapshot.gameKey === selectedGame.value.key &&
    arcade.snapshot.roomCode === invitedRoomCode.value
    ? arcade.snapshot
    : null
})

function openGame(game: GameCatalogItem) {
  void router.push({ name: 'game', params: { gameKey: game.key } })
}

function openHall() {
  void router.push({ name: 'hall' })
}

function openRoom(payload: { gameKey: ArcadeGameKey; roomCode: string }) {
  void router.push({
    name: 'room',
    params: { gameKey: payload.gameKey, roomCode: payload.roomCode },
  })
}

async function resumeRoom() {
  const gameKey = arcade.activeGame
  const roomCode = arcade.activeRoomCode
  if (!gameKey || !roomCode) return
  if (await arcade.returnToRoom()) openRoom({ gameKey, roomCode })
}

watch(
  () => arcade.snapshot,
  (next, previous) => {
    if (next && !previous) {
      // 房间邀请地址优先，不能被浏览器中保存的另一局自动恢复覆盖。
      if (route.name !== 'room') {
        void router.replace({
          name: 'room',
          params: { gameKey: next.gameKey, roomCode: next.roomCode },
        })
      }
      return
    }
    if (!next && previous && route.name === 'room') {
      const routeRoomCode = typeof route.params.roomCode === 'string'
        ? route.params.roomCode
        : ''
      if (routeRoomCode === previous.roomCode) {
        void router.replace({
          name: 'game',
          params: { gameKey: previous.gameKey },
        })
      }
    }
  },
)

document.title = '游戏大厅'

function enterGame(profile: AccountProfile, token: string) {
  account.value = profile
  accountState.value = 'authenticated'
  rememberAccountToken(token)
  setSocketAccountToken(token)
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
    const response = await loginAccount(activeAccessToken.value, {
      username: payload.username,
      password: payload.password,
    })
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
  playerName: string
  password: string
}) {
  accountBusy.value = true
  accountError.value = null
  try {
    const response = await registerAccount(activeAccessToken.value, {
      username: payload.username,
      player_name: payload.playerName,
      password: payload.password,
    })
    enterGame(response.account, response.token)
  } catch (caught) {
    accountError.value =
      caught instanceof Error ? caught.message : '注册失败，请稍后重试'
  } finally {
    accountBusy.value = false
  }
}

async function enterAsGuest(payload: { playerName: string }) {
  accountBusy.value = true
  accountError.value = null
  try {
    const response = await createGuestSession(
      activeAccessToken.value,
      payload.playerName,
    )
    enterGame(response.account, response.token)
  } catch (caught) {
    accountError.value =
      caught instanceof Error ? caught.message : '游客入席失败，请稍后重试'
  } finally {
    accountBusy.value = false
  }
}

async function changePlayerName(playerName: string) {
  const token = storedAccountToken()
  if (!token) return
  accountBusy.value = true
  accountError.value = null
  try {
    account.value = await renamePlayer(
      activeAccessToken.value,
      token,
      playerName,
    )
  } catch (caught) {
    accountError.value =
      caught instanceof Error ? caught.message : '修改游戏昵称失败'
  } finally {
    accountBusy.value = false
  }
}

async function changeAvatarPreset(preset: AvatarPresetId) {
  const token = storedAccountToken()
  if (!token) return
  accountBusy.value = true
  accountError.value = null
  try {
    account.value = await selectAvatarPreset(
      activeAccessToken.value,
      token,
      preset,
    )
  } catch (caught) {
    accountError.value =
      caught instanceof Error ? caught.message : '修改头像失败'
  } finally {
    accountBusy.value = false
  }
}

async function changeCustomAvatar(file: File) {
  const token = storedAccountToken()
  if (!token) return
  accountBusy.value = true
  accountError.value = null
  try {
    account.value = await uploadAvatar(
      activeAccessToken.value,
      token,
      file,
    )
  } catch (caught) {
    accountError.value =
      caught instanceof Error ? caught.message : '上传头像失败'
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
  arcade.resetForLogout()
  account.value = null
  showSettings.value = false
  accountError.value = null
  accountState.value = 'locked'
  await router.replace({ name: 'hall' })
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
      @guest="enterAsGuest"
    />

    <template v-else-if="account">
    <div v-if="!arcade.connected" class="connection-banner">
      <WifiOff :size="16" />
      正在重新连接游戏服务器…
    </div>

    <RouterView v-slot="{ Component }">
      <component
        :is="Component"
        v-if="route.name === 'hall'"
        :account="account"
        @logout="logout"
        @settings="showSettings = true"
        @select="openGame"
        @resume-room="resumeRoom"
      />
      <component
        :is="Component"
        v-else-if="route.name === 'game' && selectedGame"
        :account="account"
        :game="selectedGame"
        @back="openHall"
        @settings="showSettings = true"
        @room-entered="openRoom"
        @resume-room="resumeRoom"
      />
      <component
        :is="Component"
        v-else-if="routedRoomSnapshot"
        :snapshot="routedRoomSnapshot"
        @settings="showSettings = true"
      />
      <ArcadeHome
        v-else-if="route.name === 'room' && selectedGame"
        :account="account"
        :game="selectedGame"
        :invited-room="invitedRoomCode"
        @back="openHall"
        @settings="showSettings = true"
        @room-entered="openRoom"
        @resume-room="resumeRoom"
      />
    </RouterView>

    <SettingsModal
      v-if="showSettings"
      :account="account"
      :busy="accountBusy"
      :error="accountError"
      @close="showSettings = false"
      @rename="changePlayerName"
      @avatar-preset="changeAvatarPreset"
      @avatar-upload="changeCustomAvatar"
    />

    <div v-if="arcade.error" class="toast" role="alert">
      <span>{{ arcade.error }}</span>
      <button class="icon-button" aria-label="关闭提示" @click="arcade.clearError()">
        <X :size="18" />
      </button>
    </div>

    <div v-if="arcade.busy" class="busy-indicator" aria-label="正在处理">
      <span />
      <span />
      <span />
    </div>
    </template>
  </div>
</template>
