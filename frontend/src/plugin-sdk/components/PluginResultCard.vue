<script setup lang="ts">
import SoloResultCard from '../../games/shared/solo/SoloResultCard.vue'
import type { PluginResultCardProps } from '../types'

defineProps<PluginResultCardProps>()
const emit = defineEmits<{ restart: [] }>()
</script>

<template>
  <SoloResultCard
    v-bind="$props"
    class="plugin-result-card"
    @restart="emit('restart')"
  >
    <template #icon><slot name="icon" /></template>
    <template #note><slot name="note" /></template>
  </SoloResultCard>
</template>
