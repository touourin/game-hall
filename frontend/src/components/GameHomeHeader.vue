<script setup lang="ts">
import type { GameCatalogItem } from '../types/arcade'
import BackNavigationButton from './BackNavigationButton.vue'
import GameCardArtwork from './GameCardArtwork.vue'

defineProps<{
  gameKey: GameCatalogItem['key']
  eyebrow: string
  title: string
  description: string
}>()

defineEmits<{
  back: []
}>()
</script>

<template>
  <header class="game-home-header surface">
    <BackNavigationButton label="返回游戏大厅" @click="$emit('back')" />
    <div class="game-home-art">
      <GameCardArtwork :game-key="gameKey" />
    </div>
    <div class="game-home-copy">
      <small>游戏入口 · {{ eyebrow }}</small>
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
  grid-template-columns: auto 112px minmax(0, 1fr) auto;
  align-items: center;
  gap: 22px;
  min-height: 164px;
  margin: 20px 0 18px;
  overflow: hidden;
  border-color: color-mix(in srgb, var(--line-strong) 74%, var(--line));
  padding: 22px;
}

.game-home-header::before {
  position: absolute;
  inset: 5px;
  border: 1px solid color-mix(in srgb, var(--line-bright) 15%, transparent);
  border-radius: calc(var(--radius-panel) - 5px);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 22%, transparent);
  content: '';
  pointer-events: none;
}

.game-home-header::after {
  position: absolute;
  top: -64px;
  right: 20%;
  width: 280px;
  height: 190px;
  border: 1px solid var(--instrument-line);
  border-radius: 50%;
  content: '';
  pointer-events: none;
  transform: rotate(-16deg);
}

.game-home-header > :deep(.back-navigation-button) {
  align-self: start;
}

.game-home-art {
  position: relative;
  z-index: 1;
  width: 112px;
  aspect-ratio: 1;
}

.game-home-art :deep(.game-card-art) {
  width: 100%;
  height: 100%;
  min-height: 0;
  border-radius: 22%;
  box-shadow:
    var(--shadow-contact),
    0 0 0 4px color-mix(in srgb, var(--surface-inset) 66%, transparent),
    0 0 0 5px color-mix(in srgb, var(--line-bright) 18%, transparent);
}

.game-home-copy {
  min-width: 0;
}

.game-home-copy small {
  color: var(--accent);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: .05em;
}

.game-home-copy h1 {
  margin: 7px 0 6px;
  font-size: clamp(32px, 4vw, 48px);
  font-weight: 800;
  letter-spacing: -.045em;
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
  min-height: 42px;
  border-radius: var(--radius-control);
  padding: 10px 13px;
  color: var(--text-soft);
  background: var(--control-surface), var(--surface-inset);
  box-shadow:
    var(--shadow-contact),
    inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 56%, transparent);
  font-size: 11px;
  font-weight: 800;
  cursor: pointer;
}

@media (hover: hover) {
  .game-home-actions :deep(button:hover) { border-color: var(--line-strong); color: var(--accent); background: var(--surface-soft); }
}

@container (max-width: 600px) {
  .game-home-header {
    grid-template-columns: auto 76px minmax(0, 1fr);
    gap: 12px;
    min-height: 0;
    margin-top: 10px;
    padding: 15px;
  }

  .game-home-art { width: 76px; }
  .game-home-copy h1 { font-size: 29px; }
  .game-home-copy p { font-size: 11px; }

  .game-home-actions {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
    width: 100%;
  }

  .game-home-actions :deep(button) {
    min-height: 42px;
    justify-content: center;
  }
}
</style>
