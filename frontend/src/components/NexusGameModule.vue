<script setup lang="ts">
import { ArrowUpRight } from '@lucide/vue'
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
    class="game-card nexus-game-module"
    :class="`tone-${game.tone}`"
    :aria-label="`打开${game.name}`"
    @click="$emit('select')"
  >
    <span class="nexus-module-scan" aria-hidden="true" />
    <span class="nexus-module-meta">
      <small>{{ String(index + 1).padStart(2, '0') }} / {{ game.category }}</small>
      <em v-if="roomCount">{{ roomCount }} ROOMS</em>
      <em v-else>{{ game.players }}</em>
    </span>

    <GameCardArtwork :game-key="game.key" />

    <span class="nexus-module-copy">
      <span><strong>{{ game.name }}</strong><small>{{ game.description }}</small></span>
      <ArrowUpRight :size="18" />
    </span>
  </button>
</template>

<style scoped>
.nexus-game-module {
  --module-tone: var(--gold);
  position: relative;
  min-width: 0;
  min-height: 220px;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: 11px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--module-tone) 25%, var(--line));
  border-radius: var(--radius-md);
  padding: 13px;
  color: var(--text);
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--module-tone) 6%, transparent), transparent 52%),
    var(--material-pattern),
    color-mix(in srgb, var(--surface-elevated) 92%, transparent);
  background-size: auto, var(--material-size), auto;
  text-align: left;
  cursor: pointer;
  isolation: isolate;
}

.nexus-game-module::after {
  position: absolute;
  z-index: -1;
  right: -18px;
  bottom: -18px;
  width: 72px;
  height: 72px;
  border: 1px solid color-mix(in srgb, var(--module-tone) 25%, transparent);
  transform: rotate(45deg);
  content: '';
}

.nexus-module-scan {
  position: absolute;
  z-index: 3;
  top: 0;
  left: -38%;
  width: 34%;
  height: 100%;
  opacity: 0;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--module-tone) 10%, transparent), transparent);
  transform: skewX(-12deg);
  pointer-events: none;
}

.nexus-module-meta,
.nexus-module-copy {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.nexus-module-meta small,
.nexus-module-meta em {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nexus-module-meta small {
  color: color-mix(in srgb, var(--module-tone) 78%, var(--text-soft));
  font-family: ui-monospace, "SFMono-Regular", Consolas, monospace;
  font-size: 7px;
  font-weight: 800;
  letter-spacing: .13em;
  text-transform: uppercase;
}

.nexus-module-meta em {
  flex: 0 0 auto;
  color: var(--muted);
  font-family: ui-monospace, "SFMono-Regular", Consolas, monospace;
  font-size: 7px;
  font-style: normal;
}

.nexus-game-module :deep(.game-card-art) {
  min-height: 112px;
  border-color: color-mix(in srgb, var(--module-tone) 20%, var(--line));
  border-radius: 3px;
  --card-tone: var(--module-tone);
  background:
    radial-gradient(circle at 50% 18%, color-mix(in srgb, var(--module-tone) 12%, transparent), transparent 50%),
    rgba(var(--surface-deep-rgb), .66);
}

.nexus-module-copy > span { min-width: 0; display: grid; gap: 4px; }
.nexus-module-copy strong,.nexus-module-copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nexus-module-copy strong { font-size: 14px; font-weight: 800; }
.nexus-module-copy small { color: var(--muted); font-size: 8px; }
.nexus-module-copy > svg { flex: 0 0 auto; color: var(--module-tone); }

.tone-red { --module-tone: #f08285; }.tone-jade { --module-tone: #63d9ad; }.tone-blue { --module-tone: #73baf1; }.tone-ink { --module-tone: #b5c8d2; }
.tone-army { --module-tone: #c0d076; }.tone-pulse { --module-tone: #53e1c5; }.tone-focus { --module-tone: #70bde8; }.tone-mine { --module-tone: #e6779c; }
.tone-tower { --module-tone: #bd93ee; }.tone-blocks { --module-tone: #62d8f0; }.tone-poker { --module-tone: #f17b85; }.tone-fortune { --module-tone: #e8b96f; }.tone-suspicion { --module-tone: #d79a69; }

@media (hover: hover) {
  .nexus-game-module:hover { border-color: color-mix(in srgb, var(--module-tone) 58%, var(--line)); box-shadow: 0 18px 48px rgba(0,0,0,.28), 0 0 24px color-mix(in srgb, var(--module-tone) 10%, transparent); transform: translateY(-3px); }
  .nexus-game-module:hover .nexus-module-scan { opacity: 1; animation: module-scan .7s ease-out; }
  .nexus-game-module:hover .nexus-module-copy > svg { transform: translate(2px,-2px); }
}

@keyframes module-scan { to { left: 104%; } }

@media (max-width: 680px) {
  .nexus-game-module { min-height: 168px; padding: 10px; }
  .nexus-game-module :deep(.game-card-art) { min-height: 78px; }
  .nexus-module-copy small { display: none; }
  .nexus-module-copy strong { font-size: 12px; }
}
</style>
