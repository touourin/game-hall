<script setup lang="ts">
import { computed } from 'vue'
import type { GameCatalogItem } from '../types/arcade'
import { builtinGameDefinition } from '../game-platform/registry'
import { currentTheme } from '../theme'

const props = defineProps<{ gameKey: GameCatalogItem['key'] }>()

const artwork = computed(() => {
  const variants = builtinGameDefinition(props.gameKey)?.catalog.artwork
  if (!variants) return null

  return currentTheme.value === 'royal' ? variants.light : variants.dark
})
</script>

<template>
  <span class="game-card-art" :class="`art-${gameKey}`" aria-hidden="true">
    <img
      v-if="artwork"
      :src="artwork"
      alt=""
      width="768"
      height="768"
      loading="lazy"
      decoding="async"
    >
    <span v-else class="game-card-art-fallback" />
  </span>
</template>

<style scoped>
.game-card-art {
  position: relative;
  width: 100%;
  min-height: 114px;
  display: grid;
  place-items: center;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--card-tone) 28%, var(--line));
  border-radius: 13px;
  background: var(--surface-inset);
  box-shadow: inset 0 0 22px rgba(0, 0, 0, .28);
  isolation: isolate;
}

.game-card-art::after {
  position: absolute;
  content: '';
  pointer-events: none;
  z-index: 3;
  inset: 4px;
  border: 1px solid color-mix(in srgb, var(--line-bright) 16%, transparent);
  border-radius: calc(13px - 3px);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 28%, transparent);
}

.game-card-art img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
  transform: scale(1.002);
  transition: transform .55s cubic-bezier(.2, .8, .2, 1);
}

.game-card-art-fallback {
  width: 44px;
  aspect-ratio: 1;
  border: 1px solid var(--card-tone);
  transform: rotate(45deg);
  box-shadow: 0 0 24px color-mix(in srgb, var(--card-tone) 24%, transparent);
}

:global(:root[data-theme="midnight"] .game-card-art) {
  box-shadow: inset 0 0 30px rgba(4, 2, 16, .5), 0 0 18px color-mix(in srgb, var(--card-tone) 7%, transparent);
}

:global(:root[data-theme="emerald"] .game-card-art) {
  border-color: color-mix(in srgb, var(--card-tone) 18%, var(--line-strong));
  background: #060a0f;
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 58%, transparent),
    0 12px 26px rgba(0, 3, 10, .48);
}

:global(:root[data-theme="royal"] .game-card-art) {
  border-color: color-mix(in srgb, var(--card-tone) 46%, var(--line));
  background: #e8e6e2;
  box-shadow: inset 0 0 24px rgba(74, 82, 86, .12), 0 10px 24px rgba(37, 63, 78, .14);
}

:global(.game-library-card:hover) .game-card-art img {
  transform: scale(1.035);
}

@media (max-width: 680px) {
  .game-card-art { min-height: 92px; }
}

@media (prefers-reduced-motion: reduce) {
  .game-card-art img { transition: none; }
}
</style>
