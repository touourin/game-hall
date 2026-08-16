<script setup lang="ts">
import { useSlots } from 'vue'
import PluginStatePanel from './PluginStatePanel.vue'
import type { PluginFeedbackStateProps } from '../types'

withDefaults(defineProps<PluginFeedbackStateProps>(), {
  title: '暂无内容',
  description: '',
  actionLabel: '',
  busy: false,
})

defineEmits<{ action: [] }>()
const slots = useSlots()
</script>

<template>
  <PluginStatePanel
    :title="title"
    :description="description"
    :action-label="actionLabel"
    :busy="busy"
    tone="empty"
    @action="$emit('action')"
  >
    <template v-if="slots.icon" #icon><slot name="icon" /></template>
    <slot />
    <template v-if="slots.action" #action><slot name="action" /></template>
  </PluginStatePanel>
</template>
