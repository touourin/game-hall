<script setup lang="ts">
import { computed, useSlots } from 'vue'
import BaseModal from '../../components/ui/BaseModal.vue'
import type { PluginModalProps } from '../types'

const props = withDefaults(defineProps<PluginModalProps>(), {
  title: '',
  description: '',
  ariaLabel: '',
  size: 'small',
  closeOnBackdrop: true,
  closeLabel: '关闭弹窗',
  mobileSheet: false,
  inline: false,
})

defineEmits<{ close: [] }>()

const slots = useSlots()
const panelClass = computed(() => `plugin-modal-card plugin-modal-card--${props.size}`)
</script>

<template>
  <BaseModal
    :title="title"
    :description="description"
    :aria-label="ariaLabel"
    :panel-class="panelClass"
    :close-on-backdrop="closeOnBackdrop"
    :close-label="closeLabel"
    :mobile-sheet="mobileSheet"
    :inline="inline"
    @close="$emit('close')"
  >
    <template v-if="slots.icon" #icon><slot name="icon" /></template>
    <template v-if="slots.title" #title><slot name="title" /></template>
    <template v-if="slots.description" #description><slot name="description" /></template>
    <slot />
    <template v-if="slots.footer" #footer><slot name="footer" /></template>
  </BaseModal>
</template>

<style>
.modal-card.plugin-modal-card--small { width: min(100%, 420px); }
.modal-card.plugin-modal-card--medium { width: min(100%, 620px); }
.modal-card.plugin-modal-card--large { width: min(100%, 820px); }
</style>
