<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowLeft, Crown, Gamepad2, KeyRound, LogIn, Mail, ShieldCheck, Trophy, UserPlus, UserRound, UsersRound } from '@lucide/vue'
import { isValidAccountUsername } from '../account'
import UiButton from '../components/ui/UiButton.vue'

const props = defineProps<{
  busy: boolean
  error: string | null
  registrationEmailBusy?: boolean
  registrationEmailError?: string | null
  registrationEmailMessage?: string | null
  registrationEmailRequestedFor?: string
  passwordResetState?: 'idle' | 'code-sent' | 'complete'
  passwordResetError?: string | null
  passwordResetMessage?: string | null
}>()

const emit = defineEmits<{
  login: [payload: { username: string; password: string }]
  register: [payload: {
    username: string
    playerName: string
    password: string
    email?: string
    emailCode?: string
  }]
  registrationEmailCode: [email: string]
  guest: [payload: { playerName: string }]
  passwordResetStart: []
  passwordResetCode: [identifier: string]
  passwordResetConfirm: [payload: { identifier: string; code: string; password: string }]
}>()

const mode = ref<'login' | 'register' | 'guest' | 'reset'>('login')
const username = ref('')
const playerName = ref('')
const registrationEmail = ref('')
const registrationEmailCode = ref('')
const password = ref('')
const confirmPassword = ref('')
const resetCode = ref('')
const localError = ref<string | null>(null)
const resetState = computed(() => props.passwordResetState ?? 'idle')
const normalizedUsername = computed(() => username.value.trim())
const registrationUsernameValid = computed(() => (
  isValidAccountUsername(normalizedUsername.value)
))
const normalizedRegistrationEmail = computed(() => registrationEmail.value.trim())
const registrationEmailValid = computed(() => (
  normalizedRegistrationEmail.value === ''
  || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedRegistrationEmail.value)
))
const registrationEmailVerifiedForInput = computed(() => (
  normalizedRegistrationEmail.value !== ''
  && normalizedRegistrationEmail.value === props.registrationEmailRequestedFor
))
const canRequestRegistrationEmailCode = computed(() => (
  normalizedRegistrationEmail.value !== ''
  && registrationEmailValid.value
  && !props.registrationEmailBusy
  && !props.busy
))

const canSubmit = computed(() => {
  if (mode.value === 'guest') {
    return playerName.value.trim().length >= 1
      && playerName.value.trim().length <= 12
  }
  if (mode.value === 'reset') {
    if (resetState.value === 'complete') return false
    if (username.value.trim().length < 2) return false
    if (resetState.value === 'idle') return true
    return /^\d{6}$/.test(resetCode.value)
      && password.value.length >= 6
      && password.value === confirmPassword.value
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
      registrationUsernameValid.value
      && playerName.value.trim().length >= 1
      && password.value === confirmPassword.value
      && registrationEmailValid.value
      && (
        normalizedRegistrationEmail.value === ''
        || (
          registrationEmailVerifiedForInput.value
          && /^\d{6}$/.test(registrationEmailCode.value)
        )
      )
    )
  }
  return true
})

function switchMode(nextMode: 'login' | 'register' | 'guest') {
  mode.value = nextMode
  localError.value = null
  password.value = ''
  confirmPassword.value = ''
  resetCode.value = ''
  emit('passwordResetStart')
}

function openPasswordReset() {
  mode.value = 'reset'
  localError.value = null
  password.value = ''
  confirmPassword.value = ''
  resetCode.value = ''
  emit('passwordResetStart')
}

function returnToLogin() {
  switchMode('login')
}

function requestRegistrationCode() {
  localError.value = null
  if (!canRequestRegistrationEmailCode.value) return
  registrationEmailCode.value = ''
  emit('registrationEmailCode', normalizedRegistrationEmail.value)
}

function submit() {
  localError.value = null
  if (mode.value === 'guest') {
    emit('guest', { playerName: playerName.value.trim() })
    return
  }
  if (mode.value === 'reset') {
    if (resetState.value === 'complete') return
    const identifier = username.value.trim()
    if (resetState.value === 'idle') {
      emit('passwordResetCode', identifier)
      return
    }
    if (password.value !== confirmPassword.value) {
      localError.value = '两次输入的新密码不一致'
      return
    }
    emit('passwordResetConfirm', {
      identifier,
      code: resetCode.value,
      password: password.value,
    })
    return
  }
  if (mode.value === 'register') {
    if (!registrationUsernameValid.value) {
      localError.value = '账号名只能使用英文字母、数字及 . _ @ + -'
      return
    }
    if (password.value !== confirmPassword.value) {
      localError.value = '两次输入的密码不一致'
      return
    }
    if (
      normalizedRegistrationEmail.value
      && (
        !registrationEmailVerifiedForInput.value
        || !/^\d{6}$/.test(registrationEmailCode.value)
      )
    ) {
      localError.value = '请先发送并输入当前邮箱的 6 位验证码'
      return
    }
    emit('register', {
      username: username.value.trim(),
      playerName: playerName.value.trim(),
      password: password.value,
      ...(normalizedRegistrationEmail.value
        ? {
            email: normalizedRegistrationEmail.value,
            emailCode: registrationEmailCode.value,
          }
        : {}),
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
      <h1>{{ mode === 'login' ? '玩家登录' : mode === 'register' ? '建立玩家档案' : mode === 'guest' ? '游客入席' : '找回账号密码' }}</h1>
      <p class="account-copy">
        {{
          mode === 'login'
            ? '使用账号名登录，继续你的战绩与对局。'
            : mode === 'register'
              ? '账号名用于登录；游戏昵称显示在大厅、对局、聊天和排行榜。'
              : mode === 'guest'
                ? '无需注册即可完整游戏；包含游客的对局不会计入任何玩家战绩。'
                : '验证码会发送到账号已经绑定的邮箱。'
        }}
      </p>

      <div v-if="mode !== 'reset'" class="segmented-control account-mode" aria-label="登录、注册或游客入席">
        <button
          type="button"
          data-ui-interaction="choice"
          :class="{ active: mode === 'login' }"
          @click="switchMode('login')"
        >
          登录
        </button>
        <button
          type="button"
          data-ui-interaction="choice"
          :class="{ active: mode === 'register' }"
          @click="switchMode('register')"
        >
          注册
        </button>
        <button
          type="button"
          data-ui-interaction="choice"
          :class="{ active: mode === 'guest' }"
          @click="switchMode('guest')"
        >
          游客
        </button>
      </div>

      <button v-else type="button" class="account-back-button" data-ui-interaction="choice" @click="returnToLogin">
        <ArrowLeft :size="15" />返回登录
      </button>

      <form class="account-form" @submit.prevent="submit">
        <label v-if="mode !== 'guest'" class="field">
          <span>{{ mode === 'reset' ? '账号名或已绑定邮箱' : '账号名' }}</span>
          <input
            v-model="username"
            minlength="2"
            :maxlength="mode === 'reset' ? 254 : 50"
            autocomplete="username"
            :pattern="mode === 'register' ? '[A-Za-z0-9._@+\\-]+' : undefined"
            :aria-invalid="mode === 'register' && normalizedUsername !== '' && !registrationUsernameValid"
            :placeholder="mode === 'reset' ? '输入账号名或绑定邮箱' : mode === 'register' ? '2–50 位英文、数字或 . _ @ + -' : '2–50 个字符，仅用于登录'"
            :disabled="mode === 'reset' && resetState !== 'idle'"
          />
          <small
            v-if="mode === 'register'"
            class="field-hint"
            :class="{ invalid: normalizedUsername !== '' && !registrationUsernameValid }"
          >仅支持英文字母、数字和 . _ @ + -，不支持中文</small>
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

        <div v-if="mode === 'register'" class="registration-email-fields">
          <label class="field">
            <span>邮箱（选填）</span>
            <input
              v-model="registrationEmail"
              type="email"
              maxlength="254"
              autocomplete="email"
              placeholder="用于找回密码"
              :disabled="registrationEmailBusy"
            />
            <small>填写邮箱时，请先在这里完成验证；留空可直接注册。</small>
          </label>
          <UiButton
            variant="secondary"
            block
            type="button"
            :disabled="!canRequestRegistrationEmailCode"
            @click="requestRegistrationCode"
          >
            <Mail :size="17" />
            {{ registrationEmailBusy ? '正在发送…' : registrationEmailVerifiedForInput ? '重新发送验证码' : '发送验证码' }}
          </UiButton>
          <label v-if="registrationEmailVerifiedForInput" class="field">
            <span>6 位邮箱验证码</span>
            <input
              v-model="registrationEmailCode"
              inputmode="numeric"
              maxlength="6"
              autocomplete="one-time-code"
              placeholder="输入邮件中的 6 位验证码"
              :disabled="registrationEmailBusy"
            />
          </label>
          <p
            v-if="registrationEmailError"
            class="account-error"
            role="alert"
          >
            {{ registrationEmailError }}
          </p>
          <p
            v-if="registrationEmailMessage && registrationEmailVerifiedForInput"
            class="account-reset-message"
            role="status"
          >
            {{ registrationEmailMessage }}
          </p>
        </div>

        <label v-if="mode === 'login' || mode === 'register'" class="field">
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

        <button
          v-if="mode === 'login'"
          type="button"
          class="forgot-password-button"
          data-ui-interaction="choice"
          @click="openPasswordReset"
        >
          忘记密码？
        </button>

        <label v-if="mode === 'reset' && resetState === 'code-sent'" class="field">
          <span>6 位邮箱验证码</span>
          <input
            v-model="resetCode"
            inputmode="numeric"
            maxlength="6"
            autocomplete="one-time-code"
            placeholder="输入邮件中的 6 位验证码"
          />
        </label>

        <label v-if="mode === 'reset' && resetState === 'code-sent'" class="field">
          <span>新密码</span>
          <input
            v-model="password"
            type="password"
            minlength="6"
            maxlength="128"
            autocomplete="new-password"
            placeholder="至少 6 个字符"
          />
        </label>

        <label v-if="mode === 'reset' && resetState === 'code-sent'" class="field">
          <span>确认新密码</span>
          <input
            v-model="confirmPassword"
            type="password"
            minlength="6"
            maxlength="128"
            autocomplete="new-password"
            placeholder="再次输入新密码"
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

        <p v-if="localError || (mode === 'reset' ? passwordResetError : error)" class="account-error" role="alert">
          {{ localError || (mode === 'reset' ? passwordResetError : error) }}
        </p>

        <p v-if="mode === 'reset' && passwordResetMessage" class="account-reset-message" role="status">
          {{ passwordResetMessage }}
        </p>

        <UiButton
          v-if="!(mode === 'reset' && resetState === 'complete')"
          variant="primary"
          block
          type="submit"
          :disabled="busy || !canSubmit"
        >
          <UserPlus v-if="mode === 'register'" :size="18" />
          <UserRound v-else-if="mode === 'guest'" :size="18" />
          <Mail v-else-if="mode === 'reset' && resetState === 'idle'" :size="18" />
          <KeyRound v-else-if="mode === 'reset'" :size="18" />
          <LogIn v-else :size="18" />
          {{ busy ? '请稍候…' : mode === 'login' ? '登录' : mode === 'register' ? '注册并进入' : mode === 'guest' ? '以游客身份进入' : resetState === 'idle' ? '发送邮箱验证码' : '确认重置密码' }}
        </UiButton>
        <UiButton
          v-else
          variant="primary"
          block
          type="button"
          @click="returnToLogin"
        >
          <LogIn :size="18" />返回登录
        </UiButton>
        <button
          v-if="mode === 'reset' && resetState === 'code-sent'"
          type="button"
          class="reset-resend-button"
          data-ui-interaction="choice"
          :disabled="busy"
          @click="$emit('passwordResetCode', username.trim())"
        >
          没收到？重新发送验证码
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
.account-stage { width: 100%; display: grid; grid-template-columns: minmax(0, 1.08fr) minmax(390px, .92fr); align-items: stretch; gap: 10px; }
.account-intro { position: relative; min-height: 640px; display: flex; flex-direction: column; border-color: color-mix(in srgb, var(--line-strong) 74%, var(--line)); border-radius: var(--radius-lg); padding: clamp(34px, 5vw, 56px); background: radial-gradient(circle at 10% 0, color-mix(in srgb, var(--accent) 13%, transparent), transparent 35%), repeating-radial-gradient(circle at 88% 85%, transparent 0 38px, var(--instrument-line) 39px 40px), var(--panel-sheen), linear-gradient(145deg,color-mix(in srgb,var(--surface-strong) 82%,var(--bg)),var(--surface)); overflow: hidden; }
.account-intro::after { position: absolute; inset: 5px; border: 1px solid color-mix(in srgb, var(--line-bright) 15%, transparent); border-radius: calc(var(--radius-panel) - 5px); box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 22%, transparent); content: ''; pointer-events: none; }
.account-brand { position: relative; z-index: 1; display: flex; align-items: center; gap: 12px; }
.account-brand > span { width: 52px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--accent) 36%, var(--line)); border-radius: var(--radius-control); color: var(--accent); background: var(--control-surface), var(--surface-inset); box-shadow: var(--glow-primary), inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 58%, transparent); }
.account-brand p,.account-brand small,.account-brand strong { margin: 0; }
.account-brand p { display: grid; gap: 2px; }
.account-brand small { color: var(--accent); font-size: 8px; font-weight: 900; letter-spacing: .2em; }
.account-brand strong { font-size: 17px; font-weight: 800; letter-spacing: .03em; }
.account-intro-copy { position: relative; z-index: 1; margin-top: auto; padding: 70px 0 38px; }
.account-intro-copy h2 { max-width: 490px; margin: 14px 0 17px; font-size: clamp(36px, 4.5vw, 52px); font-weight: 800; line-height: 1.12; letter-spacing: -.035em; }
.account-intro-copy > p:last-child { max-width: 470px; margin: 0; color: var(--muted); font-size: 13px; line-height: 1.8; }
.account-features { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 0; padding: 0; list-style: none; }
.account-features li { min-width: 0; display: grid; gap: 10px; border: 1px solid var(--line); border-radius: var(--radius-control); padding: 13px 11px; background: var(--control-surface), color-mix(in srgb, var(--surface-inset) 86%, transparent); box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 28%, transparent); }
.account-features svg { color: var(--accent); }
.account-features span { display: grid; gap: 4px; }
.account-features strong { font-size: 10px; }
.account-features small { color: var(--muted); font-size: 8px; line-height: 1.5; }
.account-trust { position: relative; z-index: 1; display: flex; align-items: center; gap: 7px; margin: 17px 0 0; color: var(--text-soft); font-size: 9px; }
.account-trust svg { color: var(--green); }
.account-card { z-index: 2; width: auto; display: grid; align-content: center; border-color: color-mix(in srgb, var(--line-strong) 62%, var(--line)); border-radius: var(--radius-lg); padding: clamp(32px, 5vw, 54px); }
.account-card::after { position: absolute; inset: 5px; border: 1px solid color-mix(in srgb, var(--line-bright) 13%, transparent); border-radius: calc(var(--radius-panel) - 5px); content: ''; pointer-events: none; }
.account-card .account-mark { display: none; }
.account-back-button,.forgot-password-button,.reset-resend-button { border: 0; padding: 0; color: var(--accent); background: transparent; font: inherit; font-size: 11px; font-weight: 800; cursor: pointer; }
.account-back-button { width: fit-content; display: inline-flex; align-items: center; gap: 5px; margin: 4px 0 16px; }
.forgot-password-button { justify-self: end; margin-top: -4px; }
.reset-resend-button { justify-self: center; }
.reset-resend-button:disabled { cursor: not-allowed; opacity: .55; }
.account-reset-message { margin: 0; border: 1px solid color-mix(in srgb, var(--green) 36%, var(--line)); border-radius: var(--radius-control); padding: 10px 12px; color: #8fe0bd; background: color-mix(in srgb, var(--green) 7%, var(--surface-inset)); font-size: 11px; font-weight: 700; line-height: 1.6; }
.registration-email-fields { display: grid; gap: 10px; }
.field-hint { margin-top: -2px; color: var(--muted); font-size: 10px; line-height: 1.5; }
.field-hint.invalid { color: var(--danger); }
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
