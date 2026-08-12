<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  Check,
  ImagePlus,
  Palette,
  Settings,
  Upload,
  UserRound,
  UserRoundPen,
} from '@lucide/vue'
import {
  ACCEPTED_AVATAR_TYPES,
  AVATAR_PRESETS,
  MAX_AVATAR_UPLOAD_BYTES,
  type AccountProfile,
  type AvatarPresetId,
} from '../account'
import { applyTheme, storedTheme, type ThemeName } from '../theme'
import AvatarCropModal from './AvatarCropModal.vue'
import AvatarImage from './AvatarImage.vue'
import BaseModal from './ui/BaseModal.vue'

const props = defineProps<{
  account: AccountProfile
  busy: boolean
  error: string | null
}>()

const emit = defineEmits<{
  close: []
  rename: [playerName: string]
  avatarPreset: [preset: AvatarPresetId]
  avatarUpload: [file: File]
}>()

const playerName = ref(props.account.playerName)
const submittedName = ref<string | null>(null)
const savedMessage = ref<string | null>(null)
const avatarInput = ref<HTMLInputElement | null>(null)
const pendingAvatarFile = ref<File | null>(null)
const avatarMessage = ref<string | null>(null)
const localAvatarError = ref<string | null>(null)
const awaitingAvatarUpdate = ref(false)
const selectedTheme = ref<ThemeName>(storedTheme())
const themes: Array<{
  id: ThemeName
  name: string
  description: string
  colors: string[]
}> = [
  {
    id: 'emerald',
    name: '极光雾舱',
    description: '深空灰、雾面玻璃与低饱和极光',
    colors: ['#080f17', '#152731', '#78bcb5'],
  },
  {
    id: 'midnight',
    name: '暖钛陶瓷',
    description: '黑钛底盘、暖陶表面与香槟金属',
    colors: ['#12110f', '#302a23', '#b99168'],
  },
  {
    id: 'royal',
    name: '月白陶瓷',
    description: '冷月灰陶瓷、乳雾玻璃与自然铝',
    colors: ['#cbd3d9', '#f4f2ec', '#4d8b7b'],
  },
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
    && normalized.length >= 1
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

watch(
  () => props.account.avatarUrl,
  () => {
    if (!awaitingAvatarUpdate.value) return
    awaitingAvatarUpdate.value = false
    avatarMessage.value = '头像已更新，新建或重连房间时会同步给其他玩家。'
  },
)

watch(
  () => props.error,
  (currentError) => {
    if (!currentError || !awaitingAvatarUpdate.value) return
    awaitingAvatarUpdate.value = false
    localAvatarError.value = currentError
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

function chooseAvatar(preset: AvatarPresetId) {
  if (
    props.busy
    || (
      props.account.avatarType === 'preset'
      && props.account.avatarPreset === preset
    )
  ) return
  localAvatarError.value = null
  avatarMessage.value = null
  awaitingAvatarUpdate.value = true
  emit('avatarPreset', preset)
}

function openAvatarUpload() {
  if (!props.busy) avatarInput.value?.click()
}

function selectAvatarFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  localAvatarError.value = null
  avatarMessage.value = null
  if (!ACCEPTED_AVATAR_TYPES.includes(file.type)) {
    localAvatarError.value = '仅支持 JPEG、PNG、WebP 或 GIF 图片。'
    return
  }
  if (file.size > MAX_AVATAR_UPLOAD_BYTES) {
    localAvatarError.value = '头像图片不能超过 8 MB。'
    return
  }
  pendingAvatarFile.value = file
}

function confirmAvatarCrop(file: File) {
  pendingAvatarFile.value = null
  awaitingAvatarUpdate.value = true
  emit('avatarUpload', file)
}
</script>

<template>
  <BaseModal
    aria-label="设置"
    panel-class="settings-modal"
    close-label="关闭设置"
    mobile-sheet
    inline
    @close="$emit('close')"
  >
      <span class="modal-icon"><Settings :size="25" /></span>
      <h2>设置</h2>
      <p>{{ account.isGuest ? '游客可以调整本机界面主题；游客昵称和头像在本次身份期间保持不变。' : '账号名用于登录；游戏昵称用于大厅、对局、聊天和排行榜。' }}</p>

      <section v-if="!account.isGuest" class="settings-section avatar-settings-section">
        <header><UserRound :size="18" /><strong>个人头像</strong></header>
        <div class="current-avatar-row">
          <AvatarImage
            class="current-avatar"
            :src="account.avatarUrl"
            :name="account.playerName"
          />
          <div>
            <strong>{{ account.avatarType === 'custom' ? '自定义头像' : '内置头像' }}</strong>
            <small>用于大厅、房间、对局和排行榜展示</small>
          </div>
          <button
            type="button"
            class="avatar-upload-button"
            :disabled="busy"
            @click="openAvatarUpload"
          >
            <Upload :size="16" />
            {{ busy ? '正在保存…' : '上传图片' }}
          </button>
          <input
            ref="avatarInput"
            class="avatar-file-input"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            @change="selectAvatarFile"
          />
        </div>

        <div class="avatar-preset-grid" role="group" aria-label="选择内置头像">
          <button
            v-for="preset in AVATAR_PRESETS"
            :key="preset.id"
            type="button"
            :class="{
              selected: account.avatarType === 'preset'
                && account.avatarPreset === preset.id,
            }"
            :aria-pressed="account.avatarType === 'preset'
              && account.avatarPreset === preset.id"
            :disabled="busy"
            @click="chooseAvatar(preset.id)"
          >
            <AvatarImage
              class="preset-avatar"
              :src="preset.url"
              :name="preset.name"
            />
            <span>{{ preset.name }}</span>
            <Check
              v-if="account.avatarType === 'preset'
                && account.avatarPreset === preset.id"
              :size="14"
            />
          </button>
        </div>
        <p class="avatar-upload-hint">
          <ImagePlus :size="14" /> JPEG、PNG、WebP 或 GIF，最大 8 MB；上传前可拖动选框精确裁剪，服务器会压缩并移除照片元数据。
        </p>
        <p v-if="localAvatarError" class="account-error" role="alert">
          {{ localAvatarError }}
        </p>
        <p v-if="avatarMessage" class="settings-success" role="status">
          {{ avatarMessage }}
        </p>
      </section>

      <section v-if="!account.isGuest" class="settings-section">
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
              minlength="1"
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

      <section v-if="account.isGuest" class="settings-section guest-settings-section">
        <header><UserRound :size="18" /><strong>游客席位</strong></header>
        <div class="current-avatar-row">
          <AvatarImage class="current-avatar" :src="account.avatarUrl" :name="account.playerName" />
          <div><strong>{{ account.playerName }}</strong><small>游客参与的整局不会写入任何玩家的个人战绩或排行榜</small></div>
        </div>
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
            <span class="theme-copy"><strong>{{ theme.name }}</strong><small>{{ theme.description }}</small></span>
            <Check v-if="selectedTheme === theme.id" :size="17" />
          </button>
        </div>
      </section>
  </BaseModal>
  <AvatarCropModal
    v-if="pendingAvatarFile"
    :file="pendingAvatarFile"
    @close="pendingAvatarFile = null"
    @confirm="confirmAvatarCrop"
  />
</template>

<style scoped>
:global(.modal-card.settings-modal) { width: min(680px, calc(100vw - 28px)); max-height: calc(100dvh - 36px); overflow-y: auto; }
.settings-section { margin-top: 20px; padding: 18px; border: 1px solid var(--line); border-radius: var(--radius-card); background: var(--surface-glass); box-shadow: inset 0 1px 0 var(--metal-edge); }
.settings-section > header { display: flex; align-items: center; gap: 9px; margin-bottom: 14px; color: var(--gold); }
.settings-section form { display: grid; gap: 11px; }
.settings-hint { color: var(--muted); line-height: 1.6; }
.settings-success { margin: 0; color: #8fe0bd; font-size: 12px; font-weight: 700; line-height: 1.55; }
.settings-theme-list { display: grid; gap: 9px; }
.settings-theme-list button { min-height: 76px; padding: 12px 14px; display: grid; grid-template-columns: auto 1fr auto; gap: 13px; align-items: center; border: 1px solid var(--line); border-radius: var(--radius-control); color: var(--text); background: var(--surface-inset); box-shadow: inset 0 1px 0 var(--metal-edge); text-align: left; cursor: pointer; }
.settings-theme-list button.selected { border-color: var(--line-strong); background: color-mix(in srgb, var(--gold) 8%, var(--surface-glass)); box-shadow: var(--shadow-contact), inset 0 1px 0 var(--metal-edge); }
.theme-copy { display: grid; gap: 4px; }.theme-copy strong { font-size: 13px; }.theme-copy small { color: var(--muted); font-size: 11px; line-height: 1.35; }
.theme-swatches { display: flex; }
.theme-swatches i { width: 18px; height: 30px; display: block; border: 1px solid #ffffff20; }
.theme-swatches i:first-child { border-radius: 8px 0 0 8px; }
.theme-swatches i:last-child { border-radius: 0 8px 8px 0; }
.current-avatar-row { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 12px; }
.current-avatar { width: 68px; height: 68px; border: 2px solid var(--line-strong); border-radius: 50%; background: var(--surface-inset); box-shadow: var(--shadow-contact); }
.current-avatar-row > div { min-width: 0; }
.current-avatar-row > div strong, .current-avatar-row > div small { display: block; }
.current-avatar-row > div small { margin-top: 4px; color: var(--muted); line-height: 1.45; }
.avatar-upload-button { min-height: 42px; display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line-strong); border-radius: var(--radius-control); padding: 0 12px; color: var(--gold); background: var(--surface-inset); font-weight: 850; }
.avatar-file-input { position: fixed; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
.avatar-preset-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 14px; }
.avatar-preset-grid button { position: relative; min-width: 0; display: grid; justify-items: center; gap: 7px; border: 1px solid var(--line); border-radius: var(--radius-control); padding: 9px 5px 8px; color: var(--muted); background: var(--surface-inset); font-size: 11px; }
.avatar-preset-grid button.selected { border-color: var(--gold); color: var(--text); background: color-mix(in srgb, var(--gold) 9%, transparent); box-shadow: inset 0 0 0 1px rgba(225, 188, 104, .08); }
.avatar-preset-grid button > svg { position: absolute; top: 6px; right: 6px; border-radius: 50%; padding: 2px; color: #1d2a22; background: var(--gold); }
.preset-avatar { width: 58px; height: 58px; border: 2px solid rgba(255, 255, 255, .09); border-radius: 50%; box-shadow: 0 7px 18px rgba(0, 0, 0, .25); }
.avatar-upload-hint { margin: 11px 0 0; display: flex; align-items: flex-start; gap: 6px; color: var(--muted); font-size: 11px; line-height: 1.55; }
.avatar-upload-hint svg { flex: 0 0 auto; margin-top: 1px; color: var(--gold); }
@media (max-width: 520px) {
  :global(.modal-card.settings-modal) { width: 100%; }
  .current-avatar-row { grid-template-columns: auto minmax(0, 1fr); }
  .avatar-upload-button { grid-column: 1 / -1; justify-content: center; width: 100%; }
  .avatar-preset-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; }
  .preset-avatar { width: 48px; height: 48px; }
  .avatar-preset-grid button { font-size: 10px; }
}
</style>
