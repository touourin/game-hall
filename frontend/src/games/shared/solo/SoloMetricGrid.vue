<script setup lang="ts">
import type { GameMetricItem } from '../../../components/uiTypes'

withDefaults(defineProps<{
  items: GameMetricItem[]
  columns?: number
  ariaLabel?: string
  valueFirst?: boolean
}>(), {
  columns: 3,
  ariaLabel: '游戏数据',
  valueFirst: false,
})
</script>

<template>
  <section
    class="solo-metric-grid"
    :style="{ '--solo-metric-columns': columns }"
    :aria-label="ariaLabel"
  >
    <div
      v-for="item in items"
      :key="item.label"
      class="surface solo-metric-card"
      :class="`tone-${item.tone ?? 'default'}`"
    >
      <template v-if="valueFirst">
        <strong>{{ item.value }}</strong>
        <small>{{ item.label }}</small>
      </template>
      <template v-else>
        <small>{{ item.label }}</small>
        <strong>{{ item.value }}</strong>
      </template>
    </div>
  </section>
</template>

<style scoped>
.solo-metric-grid { width: 100%; min-width: 0; display: grid; grid-template-columns: repeat(var(--solo-metric-columns), minmax(0, 1fr)); gap: 9px; }
.solo-metric-card { min-width: 0; display: grid; gap: 5px; padding: 13px 10px; border-radius: var(--radius-card); background: var(--surface-glass); box-shadow: var(--shadow-contact), inset 0 1px 0 var(--metal-edge); text-align: center; }
.solo-metric-card small { overflow: hidden; color: var(--muted); font-size: 9px; font-weight: 750; text-overflow: ellipsis; white-space: nowrap; }
.solo-metric-card strong { overflow: hidden; color: var(--accent); font-size: clamp(15px, 2.5vw, 19px); font-weight: 900; text-overflow: ellipsis; white-space: nowrap; }
.solo-metric-card.tone-success strong { color: var(--green); }
.solo-metric-card.tone-warning strong,.solo-metric-card.tone-danger strong { color: var(--red); }
@media (max-width: 520px) {
  .solo-metric-grid { gap: 6px; }
  .solo-metric-card { padding: 10px 5px; }
  .solo-metric-card small { font-size: 8px; }
  .solo-metric-card strong { font-size: clamp(13px, 4vw, 17px); }
}
</style>
