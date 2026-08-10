<script setup lang="ts">
import { History } from '@lucide/vue'

withDefaults(defineProps<{
  title: string
  entries: readonly string[]
  open?: boolean
  emptyText?: string
  countLabel?: string
}>(), {
  open: false,
  emptyText: '暂无记录',
  countLabel: '',
})
</script>

<template>
  <details class="game-history-panel" :open="open">
    <summary>
      <span><History :size="16" />{{ title }}</span>
      <small>{{ countLabel || `${entries.length} 条` }}</small>
    </summary>
    <ol v-if="entries.length">
      <li v-for="(entry, index) in entries" :key="`${index}-${entry}`">{{ entry }}</li>
    </ol>
    <p v-else>{{ emptyText }}</p>
  </details>
</template>

<style scoped>
.game-history-panel {
  --game-history-accent: var(--accent, var(--gold));
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 12px;
  background: var(--surface-inset);
}
.game-history-panel summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: var(--text-soft);
  font-size: 11px;
  font-weight: 850;
  list-style: none;
  cursor: pointer;
}
.game-history-panel summary::-webkit-details-marker { display: none; }
.game-history-panel summary > span { min-width: 0; display: flex; align-items: center; gap: 7px; }
.game-history-panel summary svg { flex: 0 0 auto; color: var(--game-history-accent); }
.game-history-panel summary small { flex: 0 0 auto; color: var(--muted); font-size: 9px; }
.game-history-panel[open] summary { margin-bottom: 10px; }
.game-history-panel ol {
  display: grid;
  gap: 6px;
  max-height: var(--game-history-max-height, 240px);
  margin: 0;
  padding: 0;
  overflow: auto;
  list-style: none;
}
.game-history-panel li {
  position: relative;
  border-left: 1px solid color-mix(in srgb, var(--game-history-accent) 24%, transparent);
  padding: 3px 0 3px 12px;
  color: var(--text-soft);
  font-size: 10px;
  line-height: 1.55;
}
.game-history-panel li::before {
  position: absolute;
  top: 8px;
  left: -3px;
  width: 5px;
  aspect-ratio: 1;
  border-radius: 50%;
  background: var(--game-history-accent);
  content: '';
}
.game-history-panel > p { margin: 0; color: var(--muted); font-size: 10px; }
@media (max-width: 600px) {
  .game-history-panel { padding: 11px; }
  .game-history-panel ol { max-height: var(--game-history-mobile-max-height, 170px); }
}
</style>
