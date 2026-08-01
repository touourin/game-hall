<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Check, Palette, Settings, UserRoundPen, X } from '@lucide/vue'
import type { AccountProfile } from '../account'
import { applyTheme, storedTheme, type ThemeName } from '../theme'

const props = defineProps<{
  account: AccountProfile
  busy: boolean
  error: string | null
}>()

const emit = defineEmits<{
  close: []
  rename: [playerName: string]
}>()

const playerName = ref(props.account.playerName)
const submittedName = ref<string | null>(null)
const savedMessage = ref<string | null>(null)
const selectedTheme = ref<ThemeName>(storedTheme())
const themes: Array<{
  id: ThemeName
  name: string
  colors: string[]
}> = [
  { id: 'avalon', name: '翡翠圆桌', colors: ['#061719', '#123b3a', '#e1bc68'] },
  { id: 'midnight', name: '午夜圣殿', colors: ['#07131f', '#102e42', '#82b9e8'] },
  { id: 'royal', name: '王室秘仪', colors: ['#160f1e', '#35233e', '#d5a8e8'] },
]

const nextRenameDate = computed(() => {
  if (!props.account.nextRenameAt) return null
  return new Date(props.account.nextRenameAt)
})

const renameLocked = computed(() =>
  nextRenameDate.value !== null && nextRenameDate.value.getTime() > Date.now(),
)

const canRename = computed(() => {
  const normalized = playerName.value.trim()
  return !renameLocked.value
    && normalized.length >= 2
    && normalized.length <= 12
    && normalized !== props.account.playerName
})

const nextRenameLabel = computed(() => {
  if (!nextRenameDate.value) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(nextRenameDate.value)
})

watch(
  () => props.account.playerName,
  (currentName) => {
    playerName.value = currentName
    if (submittedName.value === currentName) {
      savedMessage.value = `游戏昵称已改为“${currentName}”，登录账号名保持不变。`
      submittedName.value = null
    }
  },
)

function submitRename() {
  if (!canRename.value || props.busy) return
  const normalized = playerName.value.trim()
  savedMessage.value = null
  submittedName.value = normalized
  emit('rename', normalized)
}

function chooseTheme(theme: ThemeName) {
  selectedTheme.value = theme
  applyTheme(theme)
}
</script>

<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <section class="modal-card settings-modal" role="dialog" aria-modal="true">
      <button class="modal-close" type="button" aria-label="关闭设置" @click="$emit('close')">
        <X :size="20" />
      </button>
      <span class="modal-icon"><Settings :size="25" /></span>
      <h2>大厅设置</h2>
      <p>账号名用于登录；游戏昵称用于大厅、对局、聊天和排行榜。</p>

      <section class="settings-section">
        <header><UserRoundPen :size="18" /><strong>账号与游戏昵称</strong></header>
        <form @submit.prevent="submitRename">
          <label class="field">
            <span>账号名（不可修改）</span>
            <input :value="account.username" disabled autocomplete="username" />
          </label>
          <label class="field">
            <span>游戏昵称</span>
            <input
              v-model="playerName"
              minlength="2"
              maxlength="12"
              autocomplete="username"
              :disabled="renameLocked"
            />
          </label>
          <small v-if="renameLocked" class="settings-hint">
            每 30 天只能改名一次，下次可改名日期：{{ nextRenameLabel }}
          </small>
          <small v-else class="settings-hint">
            旧游戏昵称仍归你的账号保留，其他玩家不能使用。
          </small>
          <p v-if="error" class="account-error" role="alert">{{ error }}</p>
          <p v-if="savedMessage" class="settings-success" role="status">{{ savedMessage }}</p>
          <button class="primary-button wide-button" type="submit" :disabled="busy || !canRename">
            <UserRoundPen :size="17" />{{ busy ? '正在保存…' : '修改游戏昵称' }}
          </button>
        </form>
      </section>

      <section class="settings-section">
        <header><Palette :size="18" /><strong>界面主题</strong></header>
        <div class="settings-theme-list">
          <button
            v-for="theme in themes"
            :key="theme.id"
            type="button"
            :class="{ selected: selectedTheme === theme.id }"
            @click="chooseTheme(theme.id)"
          >
            <span class="theme-swatches">
              <i v-for="color in theme.colors" :key="color" :style="{ background: color }" />
            </span>
            <strong>{{ theme.name }}</strong>
            <Check v-if="selectedTheme === theme.id" :size="17" />
          </button>
        </div>
      </section>
    </section>
  </div>
</template>

<style scoped>
.settings-modal { width: min(560px, calc(100vw - 28px)); max-height: calc(100dvh - 36px); overflow-y: auto; }
.settings-section { margin-top: 20px; padding: 17px; border: 1px solid var(--line); border-radius: 17px; background: color-mix(in srgb, var(--surface) 82%, transparent); }
.settings-section > header { display: flex; align-items: center; gap: 9px; margin-bottom: 14px; color: var(--gold); }
.settings-section form { display: grid; gap: 11px; }
.settings-hint { color: var(--muted); line-height: 1.6; }
.settings-success { margin: 0; color: #8fe0bd; font-weight: 700; }
.settings-theme-list { display: grid; gap: 9px; }
.settings-theme-list button { min-height: 58px; padding: 10px 12px; display: grid; grid-template-columns: auto 1fr auto; gap: 12px; align-items: center; border: 1px solid var(--line); border-radius: 13px; color: var(--text); background: var(--surface); text-align: left; }
.settings-theme-list button.selected { border-color: var(--gold); background: color-mix(in srgb, var(--gold) 8%, var(--surface)); }
.theme-swatches { display: flex; }
.theme-swatches i { width: 18px; height: 30px; display: block; border: 1px solid #ffffff20; }
.theme-swatches i:first-child { border-radius: 8px 0 0 8px; }
.theme-swatches i:last-child { border-radius: 0 8px 8px 0; }
</style>
