<script setup lang="ts">
import { computed } from 'vue'
import { ArrowUpRight, Shapes } from '@lucide/vue'
import {
  groupGamesByCategory,
  type GameCatalogEntry,
} from '../gameCatalog'
import { gameCatalogToneColor } from '../gameCatalogPresentation'
import BaseModal from './ui/BaseModal.vue'
import GameCardArtwork from './GameCardArtwork.vue'

const props = defineProps<{
  games: readonly GameCatalogEntry[]
}>()

defineEmits<{
  close: []
  select: [game: GameCatalogEntry]
}>()

const categories = computed(() => groupGamesByCategory(props.games))

function scrollToCategory(index: number) {
  document.getElementById(`game-category-${index}`)?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}
</script>

<template>
  <BaseModal
    aria-label="游戏分类"
    panel-class="game-categories-modal"
    close-label="关闭游戏分类"
    mobile-sheet
    inline
    @close="$emit('close')"
  >
    <header class="category-modal-header">
      <span class="category-modal-symbol"><Shapes :size="24" /></span>
      <span>
        <small>OFFICIAL GAME INDEX</small>
        <h2>游戏分类</h2>
        <p>按玩法找到下一局；游戏仍由各自的官方模块独立维护。</p>
      </span>
      <em>{{ categories.length }} 类 · {{ games.length }} 款</em>
    </header>

    <nav class="category-overview" aria-label="游戏类别概览">
      <button
        v-for="(category, index) in categories"
        :key="category.name"
        type="button"
        @click="scrollToCategory(index)"
      >
        <small>{{ String(index + 1).padStart(2, '0') }}</small>
        <strong>{{ category.name }}</strong>
        <em>{{ category.games.length }} 款</em>
      </button>
    </nav>

    <div class="category-sections">
      <section
        v-for="(category, categoryIndex) in categories"
        :id="`game-category-${categoryIndex}`"
        :key="category.name"
        class="category-section"
      >
        <header>
          <span>
            <small>TYPE {{ String(categoryIndex + 1).padStart(2, '0') }}</small>
            <strong>{{ category.name }}</strong>
          </span>
          <em>{{ category.games.length }} 款游戏</em>
        </header>

        <div class="category-game-grid">
          <button
            v-for="game in category.games"
            :key="game.key"
            type="button"
            :style="{ '--module-tone': gameCatalogToneColor(game.tone) }"
            :aria-label="`从${category.name}打开${game.name}`"
            @click="$emit('select', game)"
          >
            <GameCardArtwork :game-key="game.key" />
            <span>
              <small>{{ game.players }}</small>
              <strong>{{ game.name }}</strong>
              <em>{{ game.description }}</em>
            </span>
            <ArrowUpRight :size="17" />
          </button>
        </div>
      </section>
    </div>
  </BaseModal>
</template>

<style scoped>
:global(.modal-card.game-categories-modal) {
  width: min(100%, 980px);
  max-height: min(92dvh, 860px);
  padding: clamp(24px, 3vw, 36px);
  overflow: auto;
  text-align: left;
}

.category-modal-header {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 15px;
  padding: 2px 44px 23px 0;
  border-bottom: 1px solid var(--instrument-line);
}

.category-modal-symbol {
  display: grid;
  place-items: center;
  width: 52px;
  aspect-ratio: 1;
  border: 1px solid color-mix(in srgb, var(--gold) 30%, var(--line));
  border-radius: var(--radius-control);
  color: var(--gold);
  background: var(--control-surface), var(--surface-inset);
  box-shadow: var(--shadow-contact), inset 0 1px 0 var(--metal-edge);
}

.category-modal-header > span:nth-child(2) {
  display: grid;
  gap: 4px;
}

.category-modal-header small,
.category-section header small {
  color: var(--gold);
  font-size: 8px;
  font-weight: 830;
  letter-spacing: .1em;
}

.category-modal-header h2 {
  margin: 0;
  font-size: clamp(26px, 4vw, 34px);
  letter-spacing: -.04em;
}

.category-modal-header p {
  margin: 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.55;
}

.category-modal-header > em,
.category-section header > em {
  color: var(--muted);
  font-size: 9px;
  font-style: normal;
  white-space: nowrap;
}

.category-overview {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 7px;
  padding: 17px 0;
  overflow-x: auto;
}

.category-overview button {
  display: grid;
  gap: 3px;
  min-width: 105px;
  border: 1px solid var(--line);
  border-radius: var(--radius-control);
  padding: 10px 11px;
  color: var(--text);
  background: var(--surface-glass);
  box-shadow: inset 0 1px 0 var(--metal-edge);
  text-align: left;
  cursor: pointer;
}

.category-overview small {
  color: var(--gold);
  font-size: 8px;
  font-weight: 800;
}

.category-overview strong {
  font-size: 12px;
}

.category-overview em {
  color: var(--muted);
  font-size: 8px;
  font-style: normal;
}

.category-sections {
  display: grid;
  gap: 22px;
}

.category-section {
  scroll-margin-top: 12px;
}

.category-section > header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 9px;
  padding: 0 2px 8px;
  border-bottom: 1px solid var(--instrument-line);
}

.category-section header > span {
  display: grid;
  gap: 2px;
}

.category-section header strong {
  font-size: 17px;
}

.category-game-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.category-game-grid > button {
  --module-tone: var(--gold);
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) auto;
  align-items: center;
  gap: 11px;
  min-width: 0;
  min-height: 92px;
  border: 1px solid color-mix(in srgb, var(--module-tone) 20%, var(--line));
  border-radius: var(--radius-card);
  padding: 9px;
  color: var(--text);
  background:
    linear-gradient(140deg, color-mix(in srgb, var(--module-tone) 5%, transparent), transparent 55%),
    var(--surface-glass);
  box-shadow: var(--shadow-contact), inset 0 1px 0 var(--metal-edge);
  text-align: left;
  cursor: pointer;
}

.category-game-grid :deep(.game-card-art) {
  width: 72px;
  min-height: 0;
  aspect-ratio: 1;
  border-radius: 16px;
  --card-tone: var(--module-tone);
}

.category-game-grid > button > span {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.category-game-grid button small {
  color: color-mix(in srgb, var(--module-tone) 72%, var(--text-soft));
  font-size: 8px;
  font-weight: 760;
}

.category-game-grid button strong,
.category-game-grid button em {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-game-grid button strong {
  font-size: 14px;
}

.category-game-grid button em {
  color: var(--muted);
  font-size: 8px;
  font-style: normal;
}

.category-game-grid button > svg {
  color: color-mix(in srgb, var(--module-tone) 70%, var(--muted));
}

@media (hover: hover) {
  .category-overview button:hover,
  .category-game-grid > button:hover {
    border-color: color-mix(in srgb, var(--gold) 42%, var(--line));
    transform: translateY(-2px);
  }
}

@media (max-width: 820px) {
  .category-overview { grid-template-columns: repeat(6, 122px); }
  .category-game-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 560px) {
  :global(.modal-card.game-categories-modal) {
    width: 100%;
    padding: 21px 14px calc(18px + env(safe-area-inset-bottom));
  }

  .category-modal-header {
    grid-template-columns: auto minmax(0, 1fr);
    gap: 11px;
    padding-right: 38px;
  }

  .category-modal-symbol { width: 45px; }
  .category-modal-header > em { display: none; }
  .category-overview { margin-right: -14px; padding-right: 14px; }
  .category-game-grid { grid-template-columns: 1fr; }
  .category-game-grid > button { min-height: 86px; }
}
</style>
