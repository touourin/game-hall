<script setup lang="ts">
import BaseModal from './BaseModal.vue'

withDefaults(defineProps<{
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  closeLabel?: string
  panelClass?: string
  busy?: boolean
  tone?: 'default' | 'danger'
}>(), {
  confirmLabel: '确认',
  cancelLabel: '取消',
  closeLabel: '取消操作',
  panelClass: '',
  busy: false,
  tone: 'default',
})

defineEmits<{
  close: []
  confirm: []
}>()
</script>

<template>
  <BaseModal
    :title="title"
    :description="description"
    :close-label="closeLabel"
    :panel-class="['confirm-modal', panelClass].filter(Boolean).join(' ')"
    @close="$emit('close')"
  >
    <template v-if="$slots.icon" #icon>
      <span class="confirm-modal-icon" :class="`tone-${tone}`"><slot name="icon" /></span>
    </template>
    <slot />
    <div v-if="$slots.actions" class="confirm-modal-actions custom-actions">
      <slot name="actions" />
    </div>
    <div v-else class="confirm-modal-actions">
      <button type="button" class="cancel" @click="$emit('close')">{{ cancelLabel }}</button>
      <button
        type="button"
        class="confirm"
        :class="{ danger: tone === 'danger' }"
        :disabled="busy"
        @click="$emit('confirm')"
      >
        {{ confirmLabel }}
      </button>
    </div>
  </BaseModal>
</template>

<style scoped>
.confirm-modal-icon { display: grid; place-items: center; }
.confirm-modal-icon.tone-danger { color: #efaaa7; }
.confirm-modal-actions { width: 100%; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; margin-top: 18px; }
.confirm-modal-actions button { min-height: 46px; display: inline-flex; align-items: center; justify-content: center; gap: 7px; border: 1px solid var(--line); border-radius: 12px; color: var(--text); background: var(--surface-inset); font-size: 12px; font-weight: 850; cursor: pointer; }
.confirm-modal-actions .confirm { border-color: color-mix(in srgb, var(--gold) 38%, var(--line)); color: var(--accent-contrast); background: var(--gold); }
.confirm-modal-actions .danger { border-color: rgba(231, 119, 119, .42); color: #ffd0cc; background: rgba(143, 48, 52, .72); }
.confirm-modal-actions.custom-actions { display: block; }
@media (max-width: 420px) {
  .confirm-modal-actions { grid-template-columns: 1fr; }
}
</style>
