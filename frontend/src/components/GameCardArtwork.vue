<script setup lang="ts">
import { computed } from 'vue'
import type { BuiltinArcadeGameKey, GameCatalogItem } from '../types/arcade'
import avalonArtwork from '../assets/game-hall/icons/avalon.webp'
import departedSuspicionArtwork from '../assets/game-hall/icons/departed-suspicion.webp'
import doudizhuArtwork from '../assets/game-hall/icons/doudizhu.webp'
import goArtwork from '../assets/game-hall/icons/go.webp'
import gomokuArtwork from '../assets/game-hall/icons/gomoku.webp'
import hanoiArtwork from '../assets/game-hall/icons/hanoi.webp'
import junqiArtwork from '../assets/game-hall/icons/junqi.webp'
import minesweeperArtwork from '../assets/game-hall/icons/minesweeper.webp'
import monopolyArtwork from '../assets/game-hall/icons/monopoly.webp'
import oneNightWerewolfArtwork from '../assets/game-hall/icons/one-night-werewolf.webp'
import pokerArtwork from '../assets/game-hall/icons/poker.webp'
import reactionArtwork from '../assets/game-hall/icons/reaction.webp'
import schulteArtwork from '../assets/game-hall/icons/schulte.webp'
import tetrisArtwork from '../assets/game-hall/icons/tetris.webp'
import xiangqiArtwork from '../assets/game-hall/icons/xiangqi.webp'

const props = defineProps<{ gameKey: GameCatalogItem['key'] }>()

const artworkByGame = {
  avalon: avalonArtwork,
  departed_suspicion: departedSuspicionArtwork,
  one_night_werewolf: oneNightWerewolfArtwork,
  gomoku: gomokuArtwork,
  xiangqi: xiangqiArtwork,
  go: goArtwork,
  poker: pokerArtwork,
  doudizhu: doudizhuArtwork,
  junqi: junqiArtwork,
  reaction: reactionArtwork,
  schulte: schulteArtwork,
  minesweeper: minesweeperArtwork,
  hanoi: hanoiArtwork,
  tetris: tetrisArtwork,
  monopoly: monopolyArtwork,
} satisfies Record<BuiltinArcadeGameKey, string>

const artwork = computed(() => artworkByGame[props.gameKey as BuiltinArcadeGameKey] ?? null)
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
    <span class="game-card-art-vignette" />
    <span class="game-card-art-scan" />
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
  box-shadow: inset 0 0 28px rgba(0, 0, 0, .36);
  isolation: isolate;
}

.game-card-art img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.015);
  transition: filter .35s ease, transform .55s cubic-bezier(.2, .8, .2, 1);
}

.game-card-art-vignette {
  position: absolute;
  z-index: 1;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(3, 8, 13, .02) 42%, rgba(3, 8, 13, .34) 100%),
    radial-gradient(circle at 50% 48%, transparent 51%, rgba(2, 6, 10, .22) 100%);
  pointer-events: none;
}

.game-card-art-scan {
  position: absolute;
  z-index: 2;
  top: -12%;
  bottom: -12%;
  left: -50%;
  width: 26%;
  opacity: 0;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--card-tone) 17%, transparent), transparent);
  filter: blur(1px);
  transform: skewX(-12deg);
  pointer-events: none;
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

:global(:root[data-theme="royal"] .game-card-art) {
  border-color: color-mix(in srgb, var(--card-tone) 46%, var(--line));
  background: #07101a;
  box-shadow: inset 0 0 28px rgba(0, 0, 0, .4), 0 10px 24px rgba(37, 63, 78, .18);
}

:global(:root[data-theme="royal"] .game-card-art img) {
  filter: saturate(.96) contrast(1.05) brightness(1.045);
}

:global(.nexus-game-module:hover) .game-card-art img {
  filter: saturate(1.08) contrast(1.04) brightness(1.04);
  transform: scale(1.07);
}

:global(.nexus-game-module:hover) .game-card-art-scan {
  opacity: 1;
  animation: artwork-scan .8s ease-out;
}

@keyframes artwork-scan {
  to { left: 125%; }
}

@media (max-width: 680px) {
  .game-card-art { min-height: 92px; }
  .game-card-art img { transform: scale(1.025); }
}

@media (prefers-reduced-motion: reduce) {
  .game-card-art img { transition: none; }
  :global(.nexus-game-module:hover) .game-card-art-scan { animation: none; }
}
</style>
