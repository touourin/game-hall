<script setup lang="ts">
import BaseModal from './BaseModal.vue'
import UiButton from './UiButton.vue'

withDefaults(defineProps<{
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  closeLabel?: string
  panelClass?: string
  busy?: boolean
  tone?: 'default' | 'danger'
  mobileSheet?: boolean
  inline?: boolean
}>(), {
  confirmLabel: '确认',
  cancelLabel: '取消',
  closeLabel: '取消操作',
  panelClass: '',
  busy: false,
  tone: 'default',
  mobileSheet: false,
  inline: false,
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
    :mobile-sheet="mobileSheet"
    :inline="inline"
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
      <UiButton class="cancel" @click="$emit('close')">{{ cancelLabel }}</UiButton>
      <UiButton
        class="confirm"
        :variant="tone === 'danger' ? 'danger' : 'primary'"
        :disabled="busy"
        @click="$emit('confirm')"
      >
        {{ confirmLabel }}
      </UiButton>
    </div>
  </BaseModal>
</template>

<style scoped>
.confirm-modal-icon { display: grid; place-items: center; }
.confirm-modal-icon.tone-danger { color: #efaaa7; }
.confirm-modal-actions { width: 100%; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; margin-top: 18px; }
.confirm-modal-actions.custom-actions { display: block; }
@media (max-width: 420px) {
  .confirm-modal-actions { grid-template-columns: 1fr; }
}
</style>
