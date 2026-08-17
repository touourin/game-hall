<script setup lang="ts">
import { computed } from 'vue'
import { ChevronRight, Layers3 } from '@lucide/vue'
import type { GameCategory, GameCategoryId } from '../gameCategories'
import { currentTheme, isLightTheme } from '../theme'
import boardArtworkDark from '../assets/game-hall/categories/board-dark.webp'
import boardArtworkLight from '../assets/game-hall/categories/board-light.webp'
import socialArtworkDark from '../assets/game-hall/categories/social-dark.webp'
import socialArtworkLight from '../assets/game-hall/categories/social-light.webp'
import cardsArtworkDark from '../assets/game-hall/categories/cards-dark.webp'
import cardsArtworkLight from '../assets/game-hall/categories/cards-light.webp'
import soloArtworkDark from '../assets/game-hall/categories/solo-dark.webp'
import soloArtworkLight from '../assets/game-hall/categories/solo-light.webp'
import partyArtworkDark from '../assets/game-hall/categories/party-dark.webp'
import partyArtworkLight from '../assets/game-hall/categories/party-light.webp'
import communityArtworkDark from '../assets/game-hall/categories/community-dark.webp'
import communityArtworkLight from '../assets/game-hall/categories/community-light.webp'

const props = defineProps<{
  category: GameCategory
  roomCount: number
}>()

defineEmits<{
  select: []
}>()

interface CategoryArtworkVariants {
  dark: string
  light: string
}

const CATEGORY_ARTWORK: Readonly<Record<GameCategoryId, CategoryArtworkVariants>> = {
  board: { dark: boardArtworkDark, light: boardArtworkLight },
  social: { dark: socialArtworkDark, light: socialArtworkLight },
  cards: { dark: cardsArtworkDark, light: cardsArtworkLight },
  solo: { dark: soloArtworkDark, light: soloArtworkLight },
  party: { dark: partyArtworkDark, light: partyArtworkLight },
  community: { dark: communityArtworkDark, light: communityArtworkLight },
}

const categoryArtwork = computed(() => {
  const variants = CATEGORY_ARTWORK[props.category.id]
  return isLightTheme(currentTheme.value) ? variants.light : variants.dark
})
</script>

<template>
  <button
    type="button"
    class="game-category-card surface"
    :class="`category-${category.id}`"
    :aria-label="`查看${category.name}分类`"
    @click="$emit('select')"
  >
    <span class="category-card-copy">
      <small><i />{{ category.eyebrow }}</small>
      <strong>{{ category.name }}</strong>
      <p>{{ category.description }}</p>
      <span class="category-game-names">
        {{ category.games.slice(0, 3).map((game) => game.name).join(' · ') || '等待社区作品接入' }}
      </span>
      <span class="category-card-meta">
        <b><Layers3 :size="14" />{{ category.games.length }} 款游戏</b>
        <em>{{ roomCount ? `${roomCount} 个实时房间` : '浏览游戏' }}</em>
      </span>
    </span>

    <span class="category-card-art" aria-hidden="true">
      <img
        class="category-artwork"
        :src="categoryArtwork"
        alt=""
        width="768"
        height="768"
        loading="lazy"
        decoding="async"
      >
      <i class="category-art-shade" />
      <span class="category-art-meta">
        <i>{{ String(category.games.length).padStart(2, '0') }}</i>
        <em>{{ category.kind === 'community' ? 'COMMUNITY' : 'CATEGORY' }}</em>
      </span>
    </span>

    <i class="category-card-arrow" aria-hidden="true"><ChevronRight :size="20" /></i>
  </button>
</template>

<style scoped>
.game-category-card {
  --category-tone: var(--accent);
  position: relative;
  min-width: 0;
  min-height: 230px;
  display: grid;
  grid-template-columns: minmax(150px, .95fr) minmax(150px, 1.05fr);
  align-items: stretch;
  gap: 12px;
  overflow: hidden;
  border-color: color-mix(in srgb, var(--category-tone) 24%, var(--line));
  border-radius: var(--radius-card);
  padding: 20px;
  color: var(--text);
  background:
    linear-gradient(118deg, color-mix(in srgb, var(--category-tone) 8%, transparent), transparent 46%),
    var(--panel-sheen),
    var(--surface-glass);
  box-shadow:
    var(--shadow-contact),
    inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 52%, transparent),
    inset 0 -24px 50px color-mix(in srgb, var(--panel-shadow) 18%, transparent);
  text-align: left;
  cursor: pointer;
  isolation: isolate;
}

.game-category-card::before {
  position: absolute;
  z-index: -1;
  inset: 0;
  background:
    linear-gradient(color-mix(in srgb, var(--category-tone) 4%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--category-tone) 4%, transparent) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: linear-gradient(90deg, black, transparent 72%);
  content: '';
}

.game-category-card::after {
  position: absolute;
  z-index: 3;
  inset: 4px;
  border: 1px solid color-mix(in srgb, var(--line-bright) 14%, transparent);
  border-radius: calc(var(--radius-card) - 4px);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 28%, transparent);
  content: '';
  pointer-events: none;
}

.category-board { --category-tone: #719b8a; }
.category-social { --category-tone: #8a7ca6; }
.category-cards { --category-tone: #a97579; }
.category-solo { --category-tone: #6f9da2; }
.category-party { --category-tone: #a78e64; }
.category-community { --category-tone: #b46f35; }

.category-card-copy {
  position: relative;
  z-index: 2;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 5px 0 2px;
}

.category-card-copy > small {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: color-mix(in srgb, var(--category-tone) 76%, var(--text-soft));
  font-size: 9px;
  font-weight: 800;
  letter-spacing: .09em;
}

.category-card-copy > small i {
  width: 17px;
  height: 2px;
  border-radius: 999px;
  background: var(--category-tone);
  box-shadow: 0 0 9px color-mix(in srgb, var(--category-tone) 42%, transparent);
}

.category-card-copy > strong {
  margin-top: 14px;
  font-size: clamp(26px, 2.2vw, 31px);
  font-weight: 880;
  letter-spacing: -.035em;
  white-space: nowrap;
}

.category-card-copy > p {
  max-width: 390px;
  margin: 9px 0 0;
  color: var(--text-soft);
  font-size: 10px;
  line-height: 1.65;
}

.category-game-names {
  max-width: 100%;
  margin-top: 12px;
  overflow: hidden;
  color: var(--muted);
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-card-meta {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: auto;
  padding-top: 16px;
}

.category-card-meta b,
.category-card-meta em {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
  font-style: normal;
}

.category-card-meta b { color: var(--text-soft); }
.category-card-meta em { color: color-mix(in srgb, var(--category-tone) 72%, var(--muted)); }

.category-card-art {
  position: relative;
  z-index: 1;
  min-width: 0;
  min-height: 188px;
  display: grid;
  place-items: center;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--category-tone) 19%, var(--line));
  border-radius: calc(var(--radius-card) - 3px);
  background: var(--surface-inset);
  box-shadow:
    var(--shadow-contact),
    inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 38%, transparent);
  isolation: isolate;
}

.category-card-art::after {
  position: absolute;
  z-index: 4;
  inset: 4px;
  border: 1px solid color-mix(in srgb, var(--line-bright) 15%, transparent);
  border-radius: calc(var(--radius-card) - 7px);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 28%, transparent);
  content: '';
  pointer-events: none;
}

.category-artwork {
  position: absolute;
  z-index: 1;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.015);
  transition: transform .55s cubic-bezier(.2, .8, .2, 1);
}

.category-art-shade {
  position: absolute;
  z-index: 2;
  inset: 0;
  background:
    linear-gradient(180deg, transparent 52%, rgba(0, 0, 0, .52)),
    linear-gradient(110deg, color-mix(in srgb, var(--category-tone) 6%, transparent), transparent 48%);
  pointer-events: none;
}

.category-art-meta {
  position: absolute;
  z-index: 3;
  right: 10px;
  bottom: 9px;
  left: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: rgba(255, 255, 255, .62);
  font-family: ui-monospace, "SFMono-Regular", Consolas, monospace;
  text-shadow: 0 1px 6px rgba(0, 0, 0, .72);
}

.category-art-meta i,
.category-art-meta em {
  font-size: 7px;
  font-style: normal;
  font-weight: 800;
  letter-spacing: .11em;
}

.category-card-arrow {
  position: absolute;
  z-index: 4;
  right: 14px;
  top: 14px;
  width: 34px;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--category-tone) 26%, var(--line));
  border-radius: 50%;
  color: color-mix(in srgb, var(--category-tone) 74%, var(--text));
  background: var(--control-surface), var(--surface-inset);
  box-shadow: var(--shadow-contact), inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 42%, transparent);
  font-style: normal;
}

:global(:root[data-theme="emerald"] .game-category-card) {
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--category-tone) 8%, transparent), transparent 46%),
    var(--panel-sheen),
    linear-gradient(160deg, rgba(17, 38, 58, .86), rgba(3, 11, 20, .95));
}

:global(:root[data-color-scheme="light"] .game-category-card) {
  border-color: color-mix(in srgb, var(--category-tone) 34%, var(--line));
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--category-tone) 8%, transparent), transparent 48%),
    var(--panel-sheen),
    var(--surface-glass);
}

@media (hover: hover) {
  .game-category-card:hover {
    border-color: color-mix(in srgb, var(--category-tone) 48%, var(--line));
    box-shadow: var(--shadow-raised), inset 0 1px 0 var(--metal-edge);
    transform: translateY(-4px);
  }

  .game-category-card:hover .category-artwork { transform: scale(1.055); }

  .game-category-card:hover .category-card-arrow { transform: translateX(2px); }
}

@media (max-width: 680px) {
  .game-category-card {
    min-height: 148px;
    grid-template-columns: minmax(0, 1.08fr) minmax(128px, .92fr);
    gap: 8px;
    padding: 14px;
  }

  .category-card-copy { padding: 1px 0; }
  .category-card-copy > strong { margin-top: 8px; font-size: 23px; }
  .category-card-copy > p { margin-top: 6px; font-size: 9px; line-height: 1.5; }
  .category-game-names { display: none; }
  .category-card-meta { padding-top: 9px; }
  .category-card-meta em { display: none; }
  .category-card-art { min-height: 118px; }
  .category-art-meta { right: 7px; bottom: 6px; left: 7px; }
  .category-art-meta i,
  .category-art-meta em { font-size: 6px; }
  .category-card-arrow { right: 9px; top: 9px; width: 28px; }
}

@media (max-width: 380px) {
  .game-category-card {
    grid-template-columns: minmax(0, 1fr) 112px;
    padding: 12px;
  }

  .category-card-copy > p { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .category-artwork { transition: none; }
}
</style>
