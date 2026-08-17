<script setup lang="ts">
import { computed, ref } from 'vue'
import { LogOut, ShieldAlert, UserRoundPen } from '@lucide/vue'
import { isValidAccountUsername } from '../account'
import BaseModal from './ui/BaseModal.vue'
import UiButton from './ui/UiButton.vue'

const props = defineProps<{
  currentUsername: string
  busy: boolean
  error: string | null
}>()

const emit = defineEmits<{
  migrate: [username: string]
  logout: []
}>()

const username = ref('')
const normalizedUsername = computed(() => username.value.trim())
const usernameValid = computed(() => (
  isValidAccountUsername(normalizedUsername.value)
))

function submit() {
  if (!usernameValid.value || props.busy) return
  emit('migrate', normalizedUsername.value)
}
</script>

<template>
  <BaseModal
    title="请更新登录账号名"
    description="当前账号名不再符合新的账号规则，完成修改后才能进入游戏大厅。"
    panel-class="username-migration-modal"
    :closable="false"
    :close-on-backdrop="false"
  >
    <template #icon><ShieldAlert :size="28" /></template>

    <form class="username-migration-form" @submit.prevent="submit">
      <div class="legacy-username">
        <span>当前账号名</span>
        <strong>{{ currentUsername }}</strong>
      </div>

      <label class="field">
        <span>新登录账号名</span>
        <input
          v-model="username"
          minlength="2"
          maxlength="50"
          pattern="[A-Za-z0-9._@+\-]+"
          autocomplete="username"
          placeholder="2–50 位英文、数字或 . _ @ + -"
          :aria-invalid="normalizedUsername !== '' && !usernameValid"
        />
        <small :class="{ invalid: normalizedUsername !== '' && !usernameValid }">
          仅支持英文字母、数字和 . _ @ + -，不支持中文
        </small>
      </label>

      <p class="migration-warning">
        保存后请使用新账号名登录；本次迁移完成后，账号名不能再次修改。
      </p>
      <p v-if="error" class="account-error" role="alert">{{ error }}</p>

      <UiButton variant="primary" block type="submit" :disabled="busy || !usernameValid">
        <UserRoundPen :size="17" />{{ busy ? '正在更新…' : '更新账号名并进入大厅' }}
      </UiButton>
      <UiButton variant="secondary" block type="button" :disabled="busy" @click="emit('logout')">
        <LogOut :size="16" />退出登录
      </UiButton>
    </form>
  </BaseModal>
</template>

<style scoped>
:global(.modal-card.username-migration-modal) { width: min(500px, calc(100vw - 28px)); }
.username-migration-form { display: grid; gap: 12px; margin-top: 18px; }
.legacy-username { display: flex; align-items: center; justify-content: space-between; gap: 14px; border: 1px solid var(--line); border-radius: var(--radius-control); padding: 11px 13px; background: var(--surface-inset); }
.legacy-username span { color: var(--muted); font-size: 11px; }
.legacy-username strong { min-width: 0; overflow-wrap: anywhere; font-size: 13px; }
.username-migration-form .field { margin: 0; }
.username-migration-form .field small { margin-top: -2px; color: var(--muted); font-size: 10px; line-height: 1.5; }
.username-migration-form .field small.invalid { color: var(--danger); }
.migration-warning { margin: 0; border-left: 2px solid var(--accent); padding-left: 10px; color: var(--text-soft); font-size: 11px; line-height: 1.65; }
</style>
