<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { WifiOff, X } from '@lucide/vue'
import {
  clearAccountToken,
  clearAccountTokenIfCurrent,
  confirmPasswordReset,
  createGuestSession,
  loginAccount,
  logoutAccount,
  renamePlayer,
  requestEmailBindingCode,
  requestEmailUnbindCode,
  requestPasswordResetCode,
  requestRegistrationEmailCode,
  selectAvatarPreset,
  registerAccount,
  rememberAccountToken,
  storedAccountToken,
  validateAccountToken,
  verifyEmailBinding,
  unbindEmail,
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
import AccountGate from './views/AccountGate.vue'
import ArcadeHome from './views/ArcadeHome.vue'
import SettingsModal from './components/SettingsModal.vue'
import UiIconButton from './components/ui/UiIconButton.vue'

const arcade = useArcadeStore()
const route = useRoute()
const router = useRouter()
const activeAccessToken = ref('')
const activeAccountToken = ref('')
const accountState = ref<'checking' | 'locked' | 'authenticated'>('checking')
const accountBusy = ref(false)
const accountError = ref<string | null>(null)
const account = ref<AccountProfile | null>(null)
const showSettings = ref(false)
const registrationEmailBusy = ref(false)
const registrationEmailError = ref<string | null>(null)
const registrationEmailMessage = ref<string | null>(null)
const registrationEmailRequestedFor = ref('')
const emailBusy = ref(false)
const emailError = ref<string | null>(null)
const emailMessage = ref<string | null>(null)
const emailCodeSent = ref(false)
const emailUnbindCodeSent = ref(false)
const emailInitialValue = ref('')
const emailRequestedFor = ref('')
const passwordResetState = ref<'idle' | 'code-sent' | 'complete'>('idle')
const passwordResetError = ref<string | null>(null)
const passwordResetMessage = ref<string | null>(null)
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

document.title = '本体大厅'

function enterGame(profile: AccountProfile, token: string) {
  account.value = profile
  activeAccountToken.value = token
  accountState.value = 'authenticated'
  rememberAccountToken(token)
  setSocketAccountToken(token)
  arcade.init()
  if (!socket.connected) socket.connect()
}

function handleAccountReplacement(payload?: { message?: string }) {
  const replacedToken = activeAccountToken.value
  clearAccountTokenIfCurrent(replacedToken)
  activeAccountToken.value = ''
  setSocketAccountToken('')
  socket.disconnect()
  arcade.resetForLogout()
  account.value = null
  showSettings.value = false
  accountState.value = 'locked'
  accountError.value = payload?.message
    ?? '账号已在其他设备登录，请重新登录'
  void router.replace({ name: 'hall' })
}

socket.on('account:replaced', handleAccountReplacement)

async function continueAfterAccess(token: string) {
  activeAccessToken.value = token
  setSocketAccessToken(token)
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
  activeAccountToken.value = ''
  accountState.value = 'locked'
}

async function ensureAccessToken(): Promise<string> {
  if (activeAccessToken.value) return activeAccessToken.value
  const saved = storedAccessToken()
  if (saved && await validateAccessToken(saved)) return saved
  clearAccessToken()
  const token = await requestAccessToken()
  rememberAccessToken(token)
  activeAccessToken.value = token
  setSocketAccessToken(token)
  return token
}

async function login(payload: { username: string; password: string }) {
  accountBusy.value = true
  accountError.value = null
  try {
    const accessToken = await ensureAccessToken()
    const response = await loginAccount(accessToken, {
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
  email?: string
  emailCode?: string
}) {
  accountBusy.value = true
  accountError.value = null
  try {
    const accessToken = await ensureAccessToken()
    const response = await registerAccount(accessToken, {
      username: payload.username,
      player_name: payload.playerName,
      password: payload.password,
      ...(payload.email
        ? { email: payload.email, email_code: payload.emailCode ?? '' }
        : {}),
    })
    enterGame(response.account, response.token)
    registrationEmailError.value = null
    registrationEmailMessage.value = null
    registrationEmailRequestedFor.value = ''
  } catch (caught) {
    accountError.value =
      caught instanceof Error ? caught.message : '注册失败，请稍后重试'
  } finally {
    accountBusy.value = false
  }
}

async function sendRegistrationEmailCode(email: string) {
  registrationEmailBusy.value = true
  accountError.value = null
  registrationEmailError.value = null
  registrationEmailMessage.value = null
  registrationEmailRequestedFor.value = email.trim()
  try {
    const accessToken = await ensureAccessToken()
    const response = await requestRegistrationEmailCode(
      accessToken,
      email,
    )
    registrationEmailMessage.value = response.message
  } catch (caught) {
    registrationEmailRequestedFor.value = ''
    registrationEmailError.value = caught instanceof Error
      ? caught.message
      : '验证码发送失败，请稍后重试'
  } finally {
    registrationEmailBusy.value = false
  }
}

function clearPasswordResetState() {
  passwordResetState.value = 'idle'
  passwordResetError.value = null
  passwordResetMessage.value = null
}

async function sendPasswordResetCode(identifier: string) {
  accountBusy.value = true
  passwordResetError.value = null
  passwordResetMessage.value = null
  passwordResetState.value = 'idle'
  try {
    const accessToken = await ensureAccessToken()
    const result = await requestPasswordResetCode(
      accessToken,
      identifier,
    )
    if (result.sent) {
      passwordResetMessage.value = result.message
      passwordResetState.value = 'code-sent'
    } else {
      passwordResetError.value = result.message
    }
  } catch (caught) {
    passwordResetError.value = caught instanceof Error
      ? caught.message
      : '验证码发送失败，请稍后重试'
  } finally {
    accountBusy.value = false
  }
}

async function resetPassword(payload: {
  identifier: string
  code: string
  password: string
}) {
  accountBusy.value = true
  passwordResetError.value = null
  passwordResetMessage.value = null
  try {
    const accessToken = await ensureAccessToken()
    passwordResetMessage.value = await confirmPasswordReset(accessToken, {
      identifier: payload.identifier,
      code: payload.code,
      newPassword: payload.password,
    })
    passwordResetState.value = 'complete'
  } catch (caught) {
    passwordResetError.value = caught instanceof Error
      ? caught.message
      : '密码重置失败，请稍后重试'
  } finally {
    accountBusy.value = false
  }
}

async function enterAsGuest(payload: { playerName: string }) {
  accountBusy.value = true
  accountError.value = null
  try {
    const accessToken = await ensureAccessToken()
    const response = await createGuestSession(
      accessToken,
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

async function sendEmailBindingCode(email: string) {
  const token = storedAccountToken()
  if (!token) return
  emailBusy.value = true
  emailError.value = null
  emailMessage.value = null
  emailCodeSent.value = false
  emailUnbindCodeSent.value = false
  emailRequestedFor.value = email.trim()
  try {
    emailMessage.value = await requestEmailBindingCode(
      activeAccessToken.value,
      token,
      email,
    )
    emailCodeSent.value = true
  } catch (caught) {
    emailRequestedFor.value = ''
    emailError.value = caught instanceof Error
      ? caught.message
      : '验证码发送失败，请稍后重试'
  } finally {
    emailBusy.value = false
  }
}

async function bindAccountEmail(payload: { email: string; code: string }) {
  const token = storedAccountToken()
  if (!token) return
  emailBusy.value = true
  emailError.value = null
  emailMessage.value = null
  try {
    const response = await verifyEmailBinding(
      activeAccessToken.value,
      token,
      payload.email,
      payload.code,
    )
    account.value = response.account
    emailMessage.value = response.message
    emailCodeSent.value = false
    emailInitialValue.value = response.account.email ?? ''
    emailRequestedFor.value = ''
  } catch (caught) {
    emailError.value = caught instanceof Error
      ? caught.message
      : '邮箱绑定失败，请检查验证码'
  } finally {
    emailBusy.value = false
  }
}

async function sendEmailUnbindCode() {
  const token = storedAccountToken()
  if (!token) return
  emailBusy.value = true
  emailError.value = null
  emailMessage.value = null
  emailCodeSent.value = false
  emailUnbindCodeSent.value = false
  try {
    const response = await requestEmailUnbindCode(
      activeAccessToken.value,
      token,
    )
    emailMessage.value = response.message
    emailUnbindCodeSent.value = true
  } catch (caught) {
    emailError.value = caught instanceof Error
      ? caught.message
      : '解绑验证码发送失败，请稍后重试'
  } finally {
    emailBusy.value = false
  }
}

async function unbindAccountEmail(code: string) {
  const token = storedAccountToken()
  if (!token) return
  emailBusy.value = true
  emailError.value = null
  emailMessage.value = null
  try {
    const response = await unbindEmail(
      activeAccessToken.value,
      token,
      code,
    )
    account.value = response.account
    emailMessage.value = response.message
    emailCodeSent.value = false
    emailUnbindCodeSent.value = false
    emailInitialValue.value = ''
    emailRequestedFor.value = ''
  } catch (caught) {
    emailError.value = caught instanceof Error
      ? caught.message
      : '邮箱解绑失败，请检查验证码'
  } finally {
    emailBusy.value = false
  }
}

function openSettings() {
  emailInitialValue.value = account.value?.email ?? ''
  emailRequestedFor.value = ''
  emailError.value = null
  emailMessage.value = null
  emailCodeSent.value = false
  emailUnbindCodeSent.value = false
  showSettings.value = true
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
  activeAccountToken.value = ''
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
  try {
    const token = await ensureAccessToken()
    await continueAfterAccess(token)
  } catch (caught) {
    accountState.value = 'locked'
    accountError.value = caught instanceof Error
      ? caught.message
      : '无法连接服务器，请稍后重试'
  }
})
</script>

<template>
  <div class="app-shell">
    <AccountGate
      v-if="accountState !== 'authenticated'"
      :busy="accountBusy || accountState === 'checking'"
      :error="accountError"
      :registration-email-busy="registrationEmailBusy"
      :registration-email-error="registrationEmailError"
      :registration-email-message="registrationEmailMessage"
      :registration-email-requested-for="registrationEmailRequestedFor"
      :password-reset-state="passwordResetState"
      :password-reset-error="passwordResetError"
      :password-reset-message="passwordResetMessage"
      @login="login"
      @register="register"
      @registration-email-code="sendRegistrationEmailCode"
      @guest="enterAsGuest"
      @password-reset-start="clearPasswordResetState"
      @password-reset-code="sendPasswordResetCode"
      @password-reset-confirm="resetPassword"
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
        @settings="openSettings"
        @select="openGame"
        @open-room="openRoom"
        @resume-room="resumeRoom"
      />
      <component
        :is="Component"
        v-else-if="route.name === 'game' && selectedGame"
        :account="account"
        :game="selectedGame"
        @back="openHall"
        @settings="openSettings"
        @room-entered="openRoom"
        @resume-room="resumeRoom"
      />
      <component
        :is="Component"
        v-else-if="routedRoomSnapshot"
        :snapshot="routedRoomSnapshot"
        @settings="openSettings"
      />
      <ArcadeHome
        v-else-if="route.name === 'room' && selectedGame"
        :account="account"
        :game="selectedGame"
        :invited-room="invitedRoomCode"
        @back="openHall"
        @settings="openSettings"
        @room-entered="openRoom"
        @resume-room="resumeRoom"
      />
    </RouterView>

    <SettingsModal
      v-if="showSettings"
      :account="account"
      :busy="accountBusy"
      :error="accountError"
      :email-busy="emailBusy"
      :email-error="emailError"
      :email-message="emailMessage"
      :email-code-sent="emailCodeSent"
      :email-unbind-code-sent="emailUnbindCodeSent"
      :initial-email="emailInitialValue"
      :email-requested-for="emailRequestedFor"
      @close="showSettings = false"
      @rename="changePlayerName"
      @avatar-preset="changeAvatarPreset"
      @avatar-upload="changeCustomAvatar"
      @request-email-code="sendEmailBindingCode"
      @verify-email="bindAccountEmail"
      @request-email-unbind-code="sendEmailUnbindCode"
      @unbind-email="unbindAccountEmail"
    />

    <div v-if="arcade.error" class="toast" role="alert">
      <span>{{ arcade.error }}</span>
      <UiIconButton compact class="toast-dismiss" aria-label="关闭提示" @click="arcade.clearError()">
        <X :size="18" />
      </UiIconButton>
    </div>

    <div v-if="arcade.busy" class="busy-indicator" aria-label="正在处理">
      <span />
      <span />
      <span />
    </div>
    </template>
  </div>
</template>
