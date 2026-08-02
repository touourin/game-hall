<script setup lang="ts">
import { computed, ref } from 'vue'
import { Crown, LogIn, UserPlus, UserRound } from '@lucide/vue'

defineProps<{
  busy: boolean
  error: string | null
}>()

const emit = defineEmits<{
  login: [payload: { username: string; password: string }]
  register: [payload: { username: string; playerName: string; password: string }]
  guest: [payload: { playerName: string }]
}>()

const mode = ref<'login' | 'register' | 'guest'>('login')
const username = ref('')
const playerName = ref('')
const password = ref('')
const confirmPassword = ref('')
const localError = ref<string | null>(null)

const canSubmit = computed(() => {
  if (mode.value === 'guest') {
    return playerName.value.trim().length >= 2
      && playerName.value.trim().length <= 12
  }
  if (username.value.trim().length < 2 || password.value.length < 6) {
    return false
  }
  if (mode.value === 'register') {
    return (
      playerName.value.trim().length >= 2
      && password.value === confirmPassword.value
    )
  }
  return true
})

function switchMode(nextMode: 'login' | 'register' | 'guest') {
  mode.value = nextMode
  localError.value = null
  password.value = ''
  confirmPassword.value = ''
}

function submit() {
  localError.value = null
  if (mode.value === 'guest') {
    emit('guest', { playerName: playerName.value.trim() })
    return
  }
  if (mode.value === 'register') {
    if (password.value !== confirmPassword.value) {
      localError.value = '两次输入的密码不一致'
      return
    }
    emit('register', {
      username: username.value.trim(),
      playerName: playerName.value.trim(),
      password: password.value,
    })
    return
  }
  emit('login', {
    username: username.value.trim(),
    password: password.value,
  })
}
</script>

<template>
  <main class="account-page page-container">
    <section class="surface account-card">
      <span class="account-mark"><Crown :size="29" /></span>
      <p class="eyebrow">PLAYER PROFILE</p>
      <h1>{{ mode === 'login' ? '玩家登录' : mode === 'register' ? '建立玩家档案' : '游客入席' }}</h1>
      <p class="account-copy">
        {{
          mode === 'login'
            ? '使用账号名登录，继续你的战绩与对局。'
            : mode === 'register'
              ? '账号名用于登录；游戏昵称显示在大厅、对局、聊天和排行榜。'
              : '无需注册即可完整游戏；包含游客的对局不会计入任何玩家战绩。'
        }}
      </p>

      <div class="segmented-control account-mode" aria-label="登录、注册或游客入席">
        <button
          type="button"
          :class="{ active: mode === 'login' }"
          @click="switchMode('login')"
        >
          登录
        </button>
        <button
          type="button"
          :class="{ active: mode === 'register' }"
          @click="switchMode('register')"
        >
          注册
        </button>
        <button
          type="button"
          :class="{ active: mode === 'guest' }"
          @click="switchMode('guest')"
        >
          游客
        </button>
      </div>

      <form class="account-form" @submit.prevent="submit">
        <label v-if="mode !== 'guest'" class="field">
          <span>账号名</span>
          <input
            v-model="username"
            minlength="2"
            maxlength="20"
            autocomplete="username"
            placeholder="2–20 个字符，用于登录"
          />
        </label>

        <label v-if="mode === 'register' || mode === 'guest'" class="field">
          <span>游戏昵称</span>
          <input
            v-model="playerName"
            minlength="2"
            maxlength="12"
            autocomplete="nickname"
            :placeholder="mode === 'guest' ? '2–12 个字符，本次游客身份使用' : '2–12 个字符，对局中显示'"
          />
        </label>

        <label v-if="mode !== 'guest'" class="field">
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            minlength="6"
            maxlength="128"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            placeholder="至少 6 个字符"
          />
        </label>

        <label v-if="mode === 'register'" class="field">
          <span>确认密码</span>
          <input
            v-model="confirmPassword"
            type="password"
            minlength="6"
            maxlength="128"
            autocomplete="new-password"
            placeholder="再次输入密码"
          />
        </label>

        <p v-if="localError || error" class="account-error" role="alert">
          {{ localError || error }}
        </p>

        <button
          class="primary-button wide-button"
          type="submit"
          :disabled="busy || !canSubmit"
        >
          <UserPlus v-if="mode === 'register'" :size="18" />
          <UserRound v-else-if="mode === 'guest'" :size="18" />
          <LogIn v-else :size="18" />
          {{ busy ? '请稍候…' : mode === 'login' ? '登录' : mode === 'register' ? '注册并进入' : '以游客身份进入' }}
        </button>
        <small v-if="mode === 'guest'" class="guest-account-note">
          游客身份保留 7 天，可断线重连；个人战绩、比赛历史和排行榜成绩不会记录。
        </small>
      </form>
    </section>
  </main>
</template>
