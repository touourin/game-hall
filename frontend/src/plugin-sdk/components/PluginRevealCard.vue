<script setup lang="ts">
import PressRevealCard from '../../components/PressRevealCard.vue'
import type { PluginRevealCardProps } from '../types'

defineProps<PluginRevealCardProps>()
const emit = defineEmits<{ seen: [] }>()
</script>

<template>
  <PressRevealCard
    v-bind="$props"
    class="plugin-reveal-card"
    @seen="emit('seen')"
  >
    <slot />
  </PressRevealCard>
</template>
