<script setup lang="ts">
import { ref } from 'vue'
import { KeyRound, LoaderCircle, ShieldCheck } from '@lucide/vue'

defineProps<{
  checking: boolean
  busy: boolean
  error: string | null
}>()

const emit = defineEmits<{
  unlock: [password: string]
}>()

const password = ref('')

function submit() {
  if (!password.value) return
  emit('unlock', password.value)
}
</script>

<template>
  <main class="access-page page-container">
    <section class="access-card surface" aria-labelledby="access-title">
      <div class="access-mark" aria-hidden="true">
        <ShieldCheck :size="34" />
      </div>
      <p class="eyebrow">RESTRICTED ACCESS</p>
      <h1 id="access-title">访问验证</h1>
      <p class="access-copy">此页面仅供内部访问，请输入密码以继续。</p>

      <div v-if="checking" class="access-checking" role="status">
        <LoaderCircle :size="20" />
        正在验证访问状态…
      </div>

      <form v-else class="access-form" @submit.prevent="submit">
        <label for="access-password">访问密码</label>
        <div class="access-input-wrap">
          <KeyRound :size="20" aria-hidden="true" />
          <input
            id="access-password"
            v-model="password"
            type="password"
            name="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            :disabled="busy"
            autofocus
          />
        </div>
        <p v-if="error" class="access-error" role="alert">{{ error }}</p>
        <button
          class="primary-button access-submit"
          type="submit"
          :disabled="busy || !password"
        >
          <LoaderCircle v-if="busy" class="access-spinner" :size="19" />
          {{ busy ? '正在验证…' : '继续访问' }}
        </button>
      </form>
    </section>
  </main>
</template>
