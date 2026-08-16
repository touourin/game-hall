<script setup lang="ts">
import PlayingCard from '../../games/shared/cards/PlayingCard.vue'
import type { PluginPlayingCardProps } from '../types'

defineProps<PluginPlayingCardProps>()
const emit = defineEmits<{ select: [] }>()
</script>

<template>
  <PlayingCard
    v-bind="$props"
    class="plugin-playing-card"
    @select="emit('select')"
  />
</template>
