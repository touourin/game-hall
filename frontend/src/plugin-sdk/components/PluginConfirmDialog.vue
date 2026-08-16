<script setup lang="ts">
import { computed, useSlots } from 'vue'
import ConfirmModal from '../../components/ui/ConfirmModal.vue'
import type { PluginConfirmDialogProps } from '../types'

const props = withDefaults(defineProps<PluginConfirmDialogProps>(), {
  confirmLabel: '确认',
  cancelLabel: '取消',
  closeLabel: '取消操作',
  size: 'small',
  busy: false,
  tone: 'default',
  mobileSheet: false,
  inline: false,
})

defineEmits<{
  close: []
  confirm: []
}>()

const slots = useSlots()
const panelClass = computed(() => `plugin-confirm-dialog plugin-modal-card--${props.size}`)
</script>

<template>
  <ConfirmModal
    :title="title"
    :description="description"
    :confirm-label="confirmLabel"
    :cancel-label="cancelLabel"
    :close-label="closeLabel"
    :panel-class="panelClass"
    :busy="busy"
    :tone="tone"
    :mobile-sheet="mobileSheet"
    :inline="inline"
    @close="$emit('close')"
    @confirm="$emit('confirm')"
  >
    <template v-if="slots.icon" #icon><slot name="icon" /></template>
    <slot />
    <template v-if="slots.actions" #actions><slot name="actions" /></template>
  </ConfirmModal>
</template>

<style>
.modal-card.plugin-confirm-dialog.plugin-modal-card--small { width: min(100%, 420px); }
.modal-card.plugin-confirm-dialog.plugin-modal-card--medium { width: min(100%, 620px); }
.modal-card.plugin-confirm-dialog.plugin-modal-card--large { width: min(100%, 820px); }
</style>
