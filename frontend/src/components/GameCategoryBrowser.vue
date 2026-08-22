<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowLeft, Compass, Layers3, PackageOpen, Radio } from '@lucide/vue'
import type { GameCatalogEntry } from '../gameCatalog'
import {
  buildGameCategories,
  type GameCategory,
  type GameCategoryId,
} from '../gameCategories'
import GameCategoryCard from './GameCategoryCard.vue'
import GameLibraryCard from './GameLibraryCard.vue'

const props = defineProps<{
  games: readonly GameCatalogEntry[]
  roomCounts: Readonly<Record<string, number>>
}>()

const emit = defineEmits<{
  select: [game: GameCatalogEntry]
}>()

const activeCategoryId = ref<GameCategoryId | null>(null)
const categories = computed(() => buildGameCategories(props.games))
const activeCategory = computed(() => (
  categories.value.find((category) => category.id === activeCategoryId.value) ?? null
))
const totalRoomCount = computed(() => Object.values(props.roomCounts).reduce(
  (total, count) => total + count,
  0,
))

function categoryRoomCount(category: GameCategory): number {
  return category.games.reduce(
    (total, game) => total + (props.roomCounts[game.key] ?? 0),
    0,
  )
}

function showCategory(category: GameCategory) {
  activeCategoryId.value = category.id
}

function showOverview() {
  activeCategoryId.value = null
}

defineExpose({ showOverview })
</script>

<template>
  <section class="game-category-browser" aria-live="polite">
    <Transition name="category-view" mode="out-in">
      <div v-if="!activeCategory" key="overview" class="category-overview-view">
        <header class="category-browser-header">
          <span class="category-heading-symbol"><Compass :size="24" /></span>
          <span class="category-heading-copy">
            <small>游戏分类 · GAME CATEGORIES</small>
            <strong>选择游戏分类</strong>
            <em>先选择玩法方向，再进入具体游戏</em>
          </span>
          <span class="category-heading-status">
            <b><Layers3 :size="14" />{{ categories.length }} 类</b>
            <em>{{ games.length }} 款游戏</em>
            <small v-if="totalRoomCount"><Radio :size="13" />{{ totalRoomCount }} 个房间</small>
          </span>
        </header>

        <div class="category-card-grid" aria-label="选择游戏分类">
          <GameCategoryCard
            v-for="category in categories"
            :key="category.id"
            :category="category"
            :room-count="categoryRoomCount(category)"
            @select="showCategory(category)"
          />
        </div>
      </div>

      <div v-else key="detail" class="category-detail-view">
        <header class="category-detail-header surface">
          <button type="button" data-ui-interaction="choice" aria-label="返回游戏分类" @click="showOverview">
            <ArrowLeft :size="20" />
          </button>
          <span>
            <small>{{ activeCategory.eyebrow }} · {{ activeCategory.kind === 'community' ? 'COMMUNITY' : 'CATEGORY' }}</small>
            <strong>{{ activeCategory.name }}</strong>
            <em>{{ activeCategory.description }}</em>
          </span>
          <aside>
            <b>{{ activeCategory.games.length }} 款游戏</b>
            <em v-if="categoryRoomCount(activeCategory)">
              {{ categoryRoomCount(activeCategory) }} 个实时房间
            </em>
            <em v-else>选择一款开始</em>
          </aside>
        </header>

        <div v-if="activeCategory.games.length" class="category-game-grid" :aria-label="`${activeCategory.name}游戏`">
          <GameLibraryCard
            v-for="(game, index) in activeCategory.games"
            :key="game.key"
            :game="game"
            :index="index"
            :room-count="roomCounts[game.key]"
            @select="emit('select', game)"
          />
        </div>

        <div v-else class="category-empty-state" role="status">
          <PackageOpen :size="31" />
          <strong>社区作品正在准备中</strong>
          <span>新的社区游戏通过校验后，会自动出现在这里。</span>
        </div>
      </div>
    </Transition>
  </section>
</template>

<style scoped>
.game-category-browser {
  min-width: 0;
  margin-top: 34px;
  scroll-margin-top: 20px;
}

.category-browser-header {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
  border-bottom: 1px solid var(--instrument-line);
  padding: 0 4px 16px;
}

.category-heading-symbol {
  width: 44px;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: 14px;
  color: var(--accent);
  background: var(--control-surface), var(--surface-inset);
  box-shadow: var(--shadow-contact), inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 48%, transparent);
}

.category-heading-copy {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.category-heading-copy small,
.category-detail-header small {
  color: var(--accent);
  font-size: 9px;
  font-weight: 780;
  letter-spacing: .08em;
}

.category-heading-copy strong {
  font-size: clamp(23px, 2.5vw, 31px);
  font-weight: 850;
  letter-spacing: -.025em;
}

.category-heading-copy em,
.category-detail-header em {
  color: var(--muted);
  font-size: 10px;
  font-style: normal;
}

.category-heading-status {
  display: grid;
  grid-template-columns: auto auto;
  align-items: center;
  gap: 5px 12px;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 9px 12px;
  color: var(--text-soft);
  background: var(--control-surface), var(--surface-inset);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 38%, transparent);
  font-size: 9px;
}

.category-heading-status b,
.category-heading-status small {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.category-heading-status em {
  color: var(--muted);
  font-style: normal;
}

.category-heading-status small {
  grid-column: 1 / -1;
  color: var(--green);
}

.category-card-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.category-detail-header {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 15px;
  min-height: 108px;
  margin-bottom: 14px;
  border-color: var(--line-strong);
  padding: 15px 18px;
  overflow: hidden;
}

.category-detail-header::after {
  position: absolute;
  inset: 4px;
  border: 1px solid color-mix(in srgb, var(--line-bright) 14%, transparent);
  border-radius: calc(var(--radius-card) - 4px);
  content: '';
  pointer-events: none;
}

.category-detail-header > button {
  position: relative;
  z-index: 1;
  width: 42px;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: 50%;
  color: var(--text-soft);
  background: var(--control-surface), var(--surface-inset);
  box-shadow: var(--shadow-contact), inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 46%, transparent);
  cursor: pointer;
}

.category-detail-header > span {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.category-detail-header strong {
  font-size: clamp(24px, 3vw, 35px);
  font-weight: 880;
  letter-spacing: -.035em;
}

.category-detail-header aside {
  display: grid;
  gap: 4px;
  border-left: 1px solid var(--line);
  padding-left: 18px;
  text-align: right;
}

.category-detail-header aside b {
  color: var(--text-soft);
  font-size: 12px;
}

.category-detail-header aside em {
  font-size: 9px;
}

.category-game-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.category-empty-state {
  min-height: 250px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  border: 1px dashed color-mix(in srgb, var(--accent) 32%, var(--line));
  border-radius: var(--radius-card);
  color: var(--muted);
  background: color-mix(in srgb, var(--accent) 3%, var(--surface-inset));
  text-align: center;
}

.category-empty-state > svg { color: var(--accent); }
.category-empty-state > strong { color: var(--text); font-size: 15px; }
.category-empty-state > span { font-size: 10px; }

.category-view-enter-active,
.category-view-leave-active {
  transition: opacity .2s ease, transform .2s ease;
}

.category-view-enter-from { opacity: 0; transform: translateX(10px); }
.category-view-leave-to { opacity: 0; transform: translateX(-8px); }

@media (max-width: 1180px) {
  .category-card-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .category-game-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}

@media (max-width: 880px) {
  .category-game-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (max-width: 680px) {
  .game-category-browser { margin-top: 26px; }

  .category-browser-header {
    grid-template-columns: auto minmax(0, 1fr);
    padding-right: 2px;
    padding-left: 2px;
  }

  .category-heading-symbol { width: 39px; border-radius: 12px; }
  .category-heading-copy strong { font-size: 24px; }
  .category-heading-copy em { display: none; }
  .category-heading-status { display: none; }
  .category-card-grid { grid-template-columns: 1fr; gap: 10px; }

  .category-detail-header {
    grid-template-columns: auto minmax(0, 1fr);
    gap: 11px;
    min-height: 88px;
    padding: 12px;
  }

  .category-detail-header > button { width: 38px; }
  .category-detail-header strong { font-size: 25px; }
  .category-detail-header > span > em,
  .category-detail-header aside { display: none; }
  .category-game-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 380px) {
  .category-game-grid { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  .category-view-enter-active,
  .category-view-leave-active { transition: none; }
}
</style>
