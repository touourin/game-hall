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
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: flex-start;
  gap: 18px;
  padding: 25px 0 38px;
}

.game-home-copy {
  min-width: 0;
}

.game-home-copy small {
  color: var(--gold);
  font-weight: 800;
}

.game-home-copy h1 {
  margin: 4px 0;
  font-family: serif;
  font-size: clamp(34px, 6vw, 58px);
}

.game-home-copy p {
  margin: 0;
  color: var(--muted);
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
  border-radius: 11px;
  padding: 9px 11px;
  color: var(--muted);
  background: var(--surface);
  font-weight: 800;
}

@media (max-width: 600px) {
  .game-home-header {
    grid-template-columns: auto minmax(0, 1fr);
    gap: 14px;
    padding: 18px 0 26px;
  }

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
