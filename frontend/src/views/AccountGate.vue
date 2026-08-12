<script setup lang="ts">
import { computed, ref } from 'vue'
import { Crown, Gamepad2, LogIn, ShieldCheck, Trophy, UserPlus, UserRound, UsersRound } from '@lucide/vue'

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
    return playerName.value.trim().length >= 1
      && playerName.value.trim().length <= 12
  }
  if (
    username.value.trim().length < 2
    || username.value.trim().length > 50
    || password.value.length < 6
  ) {
    return false
  }
  if (mode.value === 'register') {
    return (
      playerName.value.trim().length >= 1
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
    <section class="account-stage">
      <aside class="surface account-intro" aria-label="游戏大厅介绍">
        <div class="account-brand">
          <span><Crown :size="30" /></span>
          <p><small>竞技大厅</small><strong>多人游戏厅</strong></p>
        </div>
        <div class="account-intro-copy">
          <p class="eyebrow">PLAY AT THE SAME TABLE</p>
          <h2>随时开桌，<br />和熟悉的人认真玩一局。</h2>
          <p>棋类、扑克、推理和个人挑战集中在一处。登录后可保留战绩，也可以直接以游客身份入席。</p>
        </div>
        <ul class="account-features">
          <li><Gamepad2 :size="18" /><span><strong>多种内置游戏</strong><small>统一大厅，一步进入房间</small></span></li>
          <li><UsersRound :size="18" /><span><strong>实时联机对局</strong><small>房间码邀请，支持断线重连</small></span></li>
          <li><Trophy :size="18" /><span><strong>独立玩家档案</strong><small>保存个人战绩与对局记录</small></span></li>
        </ul>
        <p class="account-trust"><ShieldCheck :size="15" />游客也可完整体验，无需先注册账号</p>
      </aside>

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
            maxlength="50"
            autocomplete="username"
            placeholder="2–50 个字符，可使用邮箱"
          />
        </label>

        <label v-if="mode === 'register' || mode === 'guest'" class="field">
          <span>游戏昵称</span>
          <input
            v-model="playerName"
            minlength="1"
            maxlength="12"
            autocomplete="nickname"
            :placeholder="mode === 'guest' ? '1–12 个字符，本次游客身份使用' : '1–12 个字符，对局中显示'"
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
    </section>
  </main>
</template>

<style scoped>
.account-page { width: min(100%, 1060px); }
.account-stage { width: 100%; display: grid; grid-template-columns: minmax(0, 1.08fr) minmax(390px, .92fr); align-items: stretch; gap: 12px; }
.account-intro { position: relative; min-height: 640px; display: flex; flex-direction: column; border-radius: var(--radius-lg); padding: clamp(34px, 5vw, 56px); background: radial-gradient(circle at 10% 0, color-mix(in srgb, var(--gold) 15%, transparent), transparent 35%), linear-gradient(rgba(91,225,236,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(91,225,236,.025) 1px,transparent 1px),linear-gradient(145deg,color-mix(in srgb,var(--surface-strong) 82%,var(--bg)),var(--surface)); background-size:auto,40px 40px,40px 40px,auto; overflow: hidden; }
.account-intro::after { position: absolute; right: -95px; bottom: -125px; width: 320px; aspect-ratio: 1; border: 1px solid color-mix(in srgb, var(--gold) 16%, transparent); border-radius: 50%; box-shadow: 0 0 0 36px color-mix(in srgb, var(--gold) 4%, transparent), 0 0 0 78px color-mix(in srgb, var(--gold) 3%, transparent); content: ''; pointer-events: none; }
.account-brand { position: relative; z-index: 1; display: flex; align-items: center; gap: 12px; }
.account-brand > span { width: 52px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--gold) 36%, var(--line)); border-radius: 5px; color: var(--gold); background: color-mix(in srgb, var(--gold) 9%, var(--surface-inset)); box-shadow: var(--glow-primary); }
.account-brand p,.account-brand small,.account-brand strong { margin: 0; }
.account-brand p { display: grid; gap: 2px; }
.account-brand small { color: var(--gold); font-size: 8px; font-weight: 900; letter-spacing: .2em; }
.account-brand strong { font-size: 17px; font-weight: 800; letter-spacing: .03em; }
.account-intro-copy { position: relative; z-index: 1; margin-top: auto; padding: 70px 0 38px; }
.account-intro-copy h2 { max-width: 490px; margin: 14px 0 17px; font-size: clamp(36px, 4.5vw, 52px); font-weight: 800; line-height: 1.12; letter-spacing: -.035em; }
.account-intro-copy > p:last-child { max-width: 470px; margin: 0; color: var(--muted); font-size: 13px; line-height: 1.8; }
.account-features { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 0; padding: 0; list-style: none; }
.account-features li { min-width: 0; display: grid; gap: 10px; border: 1px solid var(--line); border-radius: 4px; padding: 13px 11px; background: color-mix(in srgb, var(--surface-inset) 78%, transparent); }
.account-features svg { color: var(--gold); }
.account-features span { display: grid; gap: 4px; }
.account-features strong { font-size: 10px; }
.account-features small { color: var(--muted); font-size: 8px; line-height: 1.5; }
.account-trust { position: relative; z-index: 1; display: flex; align-items: center; gap: 7px; margin: 17px 0 0; color: var(--text-soft); font-size: 9px; }
.account-trust svg { color: var(--green); }
.account-card { z-index: 2; width: auto; display: grid; align-content: center; border-radius: var(--radius-lg); padding: clamp(32px, 5vw, 54px); }
.account-card .account-mark { display: none; }
@media (max-width: 820px) {
  .account-page { width: min(100%, 560px); }
  .account-stage { grid-template-columns: 1fr; gap: 12px; }
  .account-intro { min-height: auto; border-radius: var(--radius-lg); padding: 19px 21px; }
  .account-intro::after,.account-features,.account-trust { display: none; }
  .account-intro-copy { margin: 16px 0 0; padding: 0; }
  .account-intro-copy .eyebrow,.account-intro-copy > p:last-child { display: none; }
  .account-intro-copy h2 { margin: 0; font-size: 24px; line-height: 1.35; }
  .account-intro-copy h2 br { display: none; }
  .account-card { border-radius: var(--radius-lg); padding: clamp(24px, 7vw, 42px); }
}
@media (max-width: 520px) {
  .account-page { align-content: start; padding-top: calc(11px + env(safe-area-inset-top)); padding-right: calc(11px + env(safe-area-inset-right)); padding-bottom: calc(24px + env(safe-area-inset-bottom)); padding-left: calc(11px + env(safe-area-inset-left)); }
  .account-intro { padding: 14px 16px; border-radius: var(--radius-md); }
  .account-brand > span { width: 43px; border-radius: 4px; }
  .account-brand > span :deep(svg) { width: 25px; }
  .account-brand strong { font-size: 15px; }
  .account-intro-copy { margin-top: 11px; }
  .account-intro-copy h2 { font-size: 18px; }
  .account-card { border-radius: var(--radius-md); padding: 24px 19px; }
  .account-card h1 { font-size: 31px; }
  .account-copy { margin-bottom: 18px; font-size: 12px; }
}
</style>
