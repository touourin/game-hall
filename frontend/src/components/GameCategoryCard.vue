<script setup lang="ts">
import { computed } from 'vue'
import { ChevronRight, Layers3 } from '@lucide/vue'
import type { GameCategory, GameCategoryId } from '../gameCategories'
import boardEmblem from '../assets/game-hall/categories/board.svg'
import socialEmblem from '../assets/game-hall/categories/social.svg'
import cardsEmblem from '../assets/game-hall/categories/cards.svg'
import soloEmblem from '../assets/game-hall/categories/solo.svg'
import partyEmblem from '../assets/game-hall/categories/party.svg'
import communityEmblem from '../assets/game-hall/categories/community.svg'

const props = defineProps<{
  category: GameCategory
  roomCount: number
}>()

defineEmits<{
  select: []
}>()

const CATEGORY_EMBLEMS: Readonly<Record<GameCategoryId, string>> = {
  board: boardEmblem,
  social: socialEmblem,
  cards: cardsEmblem,
  solo: soloEmblem,
  party: partyEmblem,
  community: communityEmblem,
}

const categoryEmblem = computed(() => CATEGORY_EMBLEMS[props.category.id])
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
      <i class="category-art-orbit" />
      <i class="category-art-signal" />
      <span class="category-emblem">
        <i class="category-emblem-core" />
        <img
          class="category-emblem-symbol"
          :src="categoryEmblem"
          alt=""
          width="128"
          height="128"
        >
        <i class="category-emblem-index">{{ String(category.games.length).padStart(2, '0') }}</i>
      </span>
      <span class="category-art-label">{{ category.kind === 'community' ? 'COMMUNITY' : 'CATEGORY' }}</span>
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
.category-community { --category-tone: #748da9; }

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
  background:
    radial-gradient(circle at 50% 48%, color-mix(in srgb, var(--category-tone) 18%, transparent), transparent 55%),
    linear-gradient(150deg, color-mix(in srgb, var(--surface-elevated) 74%, transparent), var(--surface-inset));
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 38%, transparent),
    inset 0 -24px 42px color-mix(in srgb, var(--panel-shadow) 22%, transparent);
}

.category-art-orbit,
.category-art-signal {
  position: absolute;
  pointer-events: none;
}

.category-art-orbit {
  inset: 14% 8%;
  border: 1px solid color-mix(in srgb, var(--category-tone) 20%, transparent);
  border-radius: 50%;
  transform: rotate(-12deg);
}

.category-art-orbit::before,
.category-art-orbit::after {
  position: absolute;
  inset: 13%;
  border: inherit;
  border-radius: inherit;
  content: '';
}

.category-art-orbit::after { inset: 29%; }

.category-art-signal {
  top: 14px;
  right: 16px;
  width: 38px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--category-tone));
  box-shadow: 0 0 8px color-mix(in srgb, var(--category-tone) 38%, transparent);
}

.category-emblem {
  position: relative;
  z-index: 2;
  width: min(68%, 132px);
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--category-tone) 42%, var(--line));
  border-radius: 31%;
  color: color-mix(in srgb, var(--category-tone) 84%, var(--text-soft));
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--panel-highlight) 18%, transparent), transparent 42%),
    color-mix(in srgb, var(--category-tone) 8%, var(--surface-elevated));
  box-shadow:
    0 18px 34px color-mix(in srgb, var(--panel-shadow) 64%, transparent),
    0 0 0 7px color-mix(in srgb, var(--surface-inset) 62%, transparent),
    inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 58%, transparent);
  transform: rotate(-2deg);
  transition: transform .45s cubic-bezier(.2, .8, .2, 1), box-shadow .45s ease;
}

.category-emblem::before,
.category-emblem::after,
.category-emblem-core {
  position: absolute;
  border-radius: inherit;
  content: '';
}

.category-emblem::before {
  inset: 7px;
  border: 1px solid color-mix(in srgb, var(--category-tone) 22%, var(--line));
}

.category-emblem::after {
  width: 7px;
  height: 7px;
  right: 13px;
  top: 13px;
  border-radius: 50%;
  background: var(--category-tone);
  box-shadow: 0 0 12px color-mix(in srgb, var(--category-tone) 52%, transparent);
}

.category-emblem-core {
  inset: 21%;
  border: 1px solid color-mix(in srgb, var(--category-tone) 17%, transparent);
  transform: rotate(45deg);
}

.category-emblem-symbol {
  display: block;
  width: 54%;
  height: auto;
  aspect-ratio: 1;
  filter: drop-shadow(0 0 9px color-mix(in srgb, var(--category-tone) 28%, transparent));
}

.category-emblem-index {
  position: absolute;
  right: 12px;
  bottom: 10px;
  color: color-mix(in srgb, var(--category-tone) 62%, var(--muted));
  font-family: ui-monospace, "SFMono-Regular", Consolas, monospace;
  font-size: 8px;
  font-style: normal;
  font-weight: 800;
  letter-spacing: .1em;
}

.category-art-label {
  position: absolute;
  left: 11px;
  bottom: 9px;
  color: color-mix(in srgb, var(--category-tone) 56%, var(--muted));
  font-family: ui-monospace, "SFMono-Regular", Consolas, monospace;
  font-size: 7px;
  font-weight: 760;
  letter-spacing: .12em;
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

  .game-category-card:hover .category-emblem {
    box-shadow:
      0 22px 38px color-mix(in srgb, var(--panel-shadow) 70%, transparent),
      0 0 0 7px color-mix(in srgb, var(--surface-inset) 62%, transparent),
      0 0 26px color-mix(in srgb, var(--category-tone) 15%, transparent),
      inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 62%, transparent);
    transform: rotate(1deg) translateY(-4px) scale(1.025);
  }

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
  .category-emblem { width: min(66%, 86px); }
  .category-emblem-index { right: 8px; bottom: 7px; font-size: 7px; }
  .category-art-label { left: 7px; bottom: 6px; font-size: 6px; }
  .category-card-arrow { right: 9px; top: 9px; width: 28px; }
}

@media (max-width: 380px) {
  .game-category-card {
    grid-template-columns: minmax(0, 1fr) 112px;
    padding: 12px;
  }

  .category-card-copy > p { display: none; }
  .category-emblem { width: 78px; }
}

@media (prefers-reduced-motion: reduce) {
  .category-emblem { transition: none; }
}
</style>
