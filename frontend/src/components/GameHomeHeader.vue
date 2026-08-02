<script setup lang="ts">
import { ArrowLeft } from '@lucide/vue'

defineProps<{
  eyebrow: string
  title: string
  description: string
}>()

defineEmits<{
  back: []
}>()
</script>

<template>
  <header class="game-home-header">
    <button
      type="button"
      class="icon-button"
      aria-label="返回游戏大厅"
      @click="$emit('back')"
    >
      <ArrowLeft :size="21" />
    </button>
    <div class="game-home-copy">
      <small>{{ eyebrow }}</small>
      <h1>{{ title }}</h1>
      <p>{{ description }}</p>
    </div>
    <div class="game-home-actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.game-home-header {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: flex-start;
  gap: 18px;
  min-height: 198px;
  padding: 34px 0 46px;
}

.game-home-header::after {
  position: absolute;
  right: 2px;
  bottom: 23px;
  left: 58px;
  height: 1px;
  background: linear-gradient(90deg, var(--line-strong), transparent 72%);
  content: '';
}

.game-home-copy {
  min-width: 0;
}

.game-home-copy small {
  color: var(--gold);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .14em;
  text-transform: uppercase;
}

.game-home-copy h1 {
  margin: 7px 0 8px;
  font-family: "Songti SC", "STSong", serif;
  font-size: clamp(42px, 6vw, 64px);
  font-weight: 650;
  letter-spacing: -.035em;
  line-height: 1.05;
}

.game-home-copy p {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.6;
}

.game-home-actions {
  display: flex;
  gap: 7px;
}

.game-home-actions :deep(button) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  color: var(--text-soft);
  background: var(--surface-inset);
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

@media (hover: hover) {
  .game-home-actions :deep(button:hover) { border-color: var(--line-strong); color: var(--gold); background: var(--surface-soft); }
}

@media (max-width: 600px) {
  .game-home-header {
    grid-template-columns: auto minmax(0, 1fr);
    gap: 14px;
    min-height: 0;
    padding: 21px 0 32px;
  }

  .game-home-header::after { right: 0; bottom: 15px; left: 0; }
  .game-home-copy h1 { font-size: 39px; }

  .game-home-actions {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: 100%;
  }

  .game-home-actions :deep(button) {
    min-height: 42px;
    justify-content: center;
  }
}
</style>
