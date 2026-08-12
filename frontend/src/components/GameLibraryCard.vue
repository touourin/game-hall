<script setup lang="ts">
import { ChevronRight } from '@lucide/vue'
import type { GameCatalogEntry } from '../gameCatalog'
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
    :class="`tone-${game.tone}`"
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

.tone-red { --module-tone: #b36f69; }
.tone-jade { --module-tone: #6f9b88; }
.tone-blue { --module-tone: #748faa; }
.tone-ink { --module-tone: #88969c; }
.tone-army { --module-tone: #8f9872; }
.tone-pulse { --module-tone: #66a499; }
.tone-focus { --module-tone: #738fa3; }
.tone-mine { --module-tone: #a77689; }
.tone-tower { --module-tone: #8d7da3; }
.tone-blocks { --module-tone: #7299a1; }
.tone-poker { --module-tone: #aa7074; }
.tone-fortune { --module-tone: #a58a61; }
.tone-suspicion { --module-tone: #9d7961; }
.tone-moon { --module-tone: #7f89a5; }

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
