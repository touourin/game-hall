<script setup lang="ts">
import SoloMetricGrid from '../../games/shared/solo/SoloMetricGrid.vue'
import type { PluginMetricGridProps } from '../types'

withDefaults(defineProps<PluginMetricGridProps>(), {
  columns: 3,
  ariaLabel: '游戏数据',
  valueFirst: false,
})
</script>

<template>
  <SoloMetricGrid
    class="plugin-metric-grid"
    :items="items"
    :columns="columns"
    :aria-label="ariaLabel"
    :value-first="valueFirst"
  />
</template>
