<script setup lang="ts">
import { ChevronRight } from '@lucide/vue'
import type { GameCatalogEntry } from '../gameCatalog'
import { gameCatalogToneColor } from '../gameCatalogPresentation'
import GameCardArtwork from './GameCardArtwork.vue'

defineProps<{
  game: GameCatalogEntry
  index: number
  roomCount?: number
}>()

defineEmits<{
  select: []
}>()
</script>

<template>
  <button
    type="button"
    class="game-card game-library-card"
    :style="{ '--module-tone': gameCatalogToneColor(game.tone) }"
    :aria-label="`打开${game.name}`"
    @click="$emit('select')"
  >
    <span class="game-library-meta">
      <small>{{ String(index + 1).padStart(2, '0') }} · {{ game.category }}</small>
      <em>{{ roomCount ? `${roomCount} 个房间` : game.players }}</em>
    </span>

    <GameCardArtwork :game-key="game.key" />

    <span class="game-library-copy">
      <span>
        <strong>{{ game.name }}</strong>
        <small>{{ game.description }}</small>
      </span>
      <i aria-hidden="true"><ChevronRight :size="17" /></i>
    </span>
  </button>
</template>

<style scoped>
.game-library-card {
  --module-tone: var(--gold);
  position: relative;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: 12px;
  min-width: 0;
  min-height: 252px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--module-tone) 22%, var(--line));
  border-radius: var(--radius-card);
  padding: 13px;
  color: var(--text);
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--module-tone) 4%, transparent), transparent 52%),
    var(--surface-glass);
  box-shadow: var(--shadow-contact), inset 0 1px 0 var(--metal-edge);
  text-align: left;
  cursor: pointer;
  backdrop-filter: blur(20px) saturate(108%);
}

.game-library-card::before {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(118deg, rgba(255, 255, 255, .035), transparent 28%);
  content: '';
  pointer-events: none;
}

.game-library-card::after {
  position: absolute;
  z-index: 1;
  inset: 4px;
  border: 1px solid color-mix(in srgb, var(--line-bright) 13%, transparent);
  border-radius: calc(var(--radius-card) - 4px);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 24%, transparent);
  content: '';
  pointer-events: none;
}

.game-library-meta,
.game-library-copy {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.game-library-meta small,
.game-library-meta em {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.game-library-meta small {
  color: color-mix(in srgb, var(--module-tone) 72%, var(--text-soft));
  font-size: 9px;
  font-weight: 780;
}

.game-library-meta em {
  flex: 0 0 auto;
  color: var(--muted);
  font-size: 9px;
  font-style: normal;
}

.game-library-card :deep(.game-card-art) {
  min-height: 142px;
  border-color: color-mix(in srgb, var(--module-tone) 18%, var(--line));
  border-radius: 16px;
  --card-tone: var(--module-tone);
  box-shadow: var(--shadow-contact);
}

.game-library-copy > span {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.game-library-copy strong,
.game-library-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.game-library-copy strong {
  font-size: 15px;
  font-weight: 820;
}

.game-library-copy small {
  color: var(--muted);
  font-size: 9px;
}

.game-library-copy > i {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 30px;
  height: 30px;
  border: 1px solid var(--line);
  border-radius: 50%;
  color: color-mix(in srgb, var(--module-tone) 74%, var(--text-soft));
  background: var(--surface-inset);
  font-style: normal;
}

:global(:root[data-theme="emerald"] .game-library-card) {
  border-color: color-mix(in srgb, var(--module-tone) 21%, var(--line-strong));
  background:
    linear-gradient(155deg, rgba(207, 232, 250, .055), transparent 29%),
    linear-gradient(180deg, rgba(18, 39, 59, .78), rgba(4, 13, 23, .92));
  box-shadow:
    var(--shadow-contact),
    inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 56%, transparent),
    inset 0 -20px 42px rgba(0, 3, 9, .34);
}

:global(:root[data-theme="emerald"] .game-library-meta::after) {
  width: 18px;
  height: 1px;
  margin-left: auto;
  background: linear-gradient(90deg, var(--module-tone), transparent);
  box-shadow: 0 0 8px color-mix(in srgb, var(--module-tone) 36%, transparent);
  content: '';
}

:global(:root[data-theme="emerald"] .game-library-meta em) {
  order: 3;
}

:global(:root[data-theme="emerald"] .game-library-copy > i) {
  background: var(--control-surface), var(--surface-inset);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 48%, transparent);
}

@media (hover: hover) {
  .game-library-card:hover {
    border-color: color-mix(in srgb, var(--module-tone) 48%, var(--line));
    box-shadow: var(--shadow-raised), inset 0 1px 0 var(--metal-edge);
    transform: translateY(-4px);
  }

  .game-library-card:hover .game-library-copy > i {
    border-color: color-mix(in srgb, var(--module-tone) 45%, var(--line));
    transform: translateX(2px);
  }
}

@media (max-width: 680px) {
  .game-library-card {
    min-height: 196px;
    padding: 10px;
  }

  .game-library-card :deep(.game-card-art) {
    min-height: 104px;
  }

  .game-library-copy small {
    display: none;
  }
}
</style>
