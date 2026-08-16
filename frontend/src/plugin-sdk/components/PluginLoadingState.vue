<script setup lang="ts">
import { useSlots } from 'vue'
import PluginStatePanel from './PluginStatePanel.vue'
import type { PluginFeedbackStateProps } from '../types'

withDefaults(defineProps<Pick<PluginFeedbackStateProps, 'title' | 'description'>>(), {
  title: '正在加载',
  description: '',
})

const slots = useSlots()
</script>

<template>
  <PluginStatePanel :title="title" :description="description" tone="loading">
    <template v-if="slots.icon" #icon><slot name="icon" /></template>
    <slot />
  </PluginStatePanel>
</template>
