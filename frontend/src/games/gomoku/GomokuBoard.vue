<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Flag } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const pendingMove = ref<{ row: number; column: number } | null>(null)

const game = computed(() => props.snapshot.game as {
  boardSize: number
  board: number[][]
  turnPlayerId: string | null
  lastMove: { row: number; column: number } | null
  colors: Record<string, 'black' | 'white'>
})
const isMyTurn = computed(
  () => game.value.turnPlayerId === props.snapshot.self.id,
)
const canPlace = computed(
  () => isMyTurn.value && props.snapshot.phase === 'playing' && !arcade.busy,
)
const previewColor = computed<'black' | 'white'>(() =>
  game.value.colors[props.snapshot.self.id] ?? 'black',
)
const pendingMoveLabel = computed(() => {
  if (!pendingMove.value) {
    return '鼠标悬停可预览落子；触屏轻点一次预览，再点一次确认'
  }
  return `已预览第 ${pendingMove.value.row + 1} 行第 ${pendingMove.value.column + 1} 列，再轻点一次确认落子`
})

watch(
  () => [
    props.snapshot.phase,
    game.value.turnPlayerId,
    game.value.lastMove?.row,
    game.value.lastMove?.column,
  ],
  () => {
    pendingMove.value = null
  },
)

function isPendingMove(row: number, column: number) {
  return pendingMove.value?.row === row && pendingMove.value?.column === column
}

function isStarPoint(row: number, column: number) {
  if (game.value.boardSize !== 15) return false
  return [
    [3, 3], [3, 11], [7, 7], [11, 3], [11, 11],
  ].some(([starRow, starColumn]) => starRow === row && starColumn === column)
}

function usesTouchConfirmation(event: MouseEvent) {
  return ['touch', 'pen'].includes((event as PointerEvent).pointerType ?? '')
}

function place(row: number, column: number, event: MouseEvent) {
  if (!canPlace.value || game.value.board[row]?.[column]) return
  if (usesTouchConfirmation(event) && !isPendingMove(row, column)) {
    pendingMove.value = { row, column }
    return
  }
  pendingMove.value = null
  void arcade.action('place', { row, column })
}
</script>

<template>
  <section class="board-game-panel">
    <div class="turn-banner" :class="{ active: isMyTurn }">
      {{ isMyTurn ? '轮到你落子' : '等待对手落子' }}
      <small>你执{{ game.colors[snapshot.self.id] === 'black' ? '黑' : '白' }}</small>
    </div>
    <div
      class="gomoku-board"
      :style="{ '--board-size': game.boardSize }"
      aria-label="五子棋棋盘"
    >
      <template v-for="(row, rowIndex) in game.board" :key="rowIndex">
        <button
          v-for="(cell, columnIndex) in row"
          :key="`${rowIndex}-${columnIndex}`"
          type="button"
          class="board-point"
          :class="{
            star: isStarPoint(rowIndex, columnIndex),
            previewing: isPendingMove(rowIndex, columnIndex),
          }"
          :disabled="!canPlace || cell !== 0"
          :aria-pressed="isPendingMove(rowIndex, columnIndex)"
          :aria-label="`${isPendingMove(rowIndex, columnIndex) ? '已预览，' : ''}第 ${rowIndex + 1} 行第 ${columnIndex + 1} 列`"
          @click="place(rowIndex, columnIndex, $event)"
        >
          <span
            v-if="!cell && canPlace"
            class="stone-preview"
            :class="[previewColor, { active: isPendingMove(rowIndex, columnIndex) }]"
            aria-hidden="true"
          />
          <span
            v-if="cell"
            class="stone"
            :class="[
              cell === 1 ? 'black' : 'white',
              {
                latest:
                  game.lastMove?.row === rowIndex &&
                  game.lastMove?.column === columnIndex,
              },
            ]"
          />
        </button>
      </template>
    </div>
    <p v-if="canPlace" class="gomoku-board-hint" aria-live="polite">
      {{ pendingMoveLabel }}
    </p>
    <button
      v-if="snapshot.phase === 'playing'"
      type="button"
      class="arcade-danger-button"
      @click="arcade.action('resign')"
    >
      <Flag :size="17" />认输
    </button>
  </section>
</template>

<style scoped>
.board-game-panel { display: grid; gap: 16px; justify-items: center; }
.turn-banner { color: var(--muted); text-align: center; font-weight: 700; }
.turn-banner.active { color: var(--gold); }
.turn-banner small { display: block; margin-top: 3px; font-weight: 500; }
.gomoku-board {
  --board-size: 15;
  width: min(92vw, 650px);
  aspect-ratio: 1;
  padding: 14px;
  display: grid;
  grid-template-columns: repeat(var(--board-size), 1fr);
  border: 5px solid #7b4a20;
  border-radius: 14px;
  background-color: #d5a45d;
  background-image:
    linear-gradient(105deg, transparent 0 17%, rgba(112, 67, 22, .08) 17.4%, transparent 18%),
    repeating-linear-gradient(3deg, rgba(255, 244, 198, .06) 0 2px, rgba(111, 65, 25, .035) 3px 5px);
  box-shadow:
    inset 0 0 0 2px rgba(255, 224, 157, .35),
    inset 0 0 24px rgba(92, 47, 14, .2),
    0 20px 50px #0006,
    0 0 0 1px color-mix(in srgb, var(--gold) 24%, transparent);
}
.board-point {
  position: relative;
  min-width: 0;
  padding: 0;
  border: 0;
  background:
    linear-gradient(#65401f, #65401f) center / 100% 1px no-repeat,
    linear-gradient(90deg, #65401f, #65401f) center / 1px 100% no-repeat;
}
.board-point:disabled { opacity: 1; }
.board-point:not(:disabled) { cursor: crosshair; }
.board-point:focus-visible { border-radius: 50%; outline-offset: -3px; }
.board-point.star::before { content: ''; position: absolute; inset: 41%; z-index: 1; border-radius: 50%; background: #5f3b1c; box-shadow: 0 0 0 1px rgba(76, 42, 15, .28); }
.stone-preview {
  pointer-events: none;
  position: absolute;
  inset: 8%;
  z-index: 4;
  border-radius: 50%;
  opacity: 0;
  transform: scale(.82);
  transition: opacity .12s ease, transform .12s ease;
  box-shadow: 0 3px 8px rgba(35, 20, 9, .38);
}
.stone-preview.black { background: radial-gradient(circle at 35% 30%, #666, #090909 68%); }
.stone-preview.white { border: 1px solid rgba(89, 68, 42, .25); background: radial-gradient(circle at 35% 30%, #fff, #d8d2c5 70%); }
.board-point:not(:disabled):hover .stone-preview,
.stone-preview.active { opacity: .5; transform: scale(1); }
.stone-preview.active { outline: 2px solid rgba(255, 245, 197, .78); outline-offset: 2px; }
.stone {
  position: absolute;
  inset: 8%;
  z-index: 2;
  border-radius: 50%;
  box-shadow: inset -2px -3px 5px #0005, 0 2px 4px #0007;
}
.stone.black { background: radial-gradient(circle at 35% 30%, #555, #080808 68%); }
.stone.white { background: radial-gradient(circle at 35% 30%, #fff, #d7d2c8 70%); }
.stone.latest::after {
  content: '';
  position: absolute;
  inset: 35%;
  border-radius: 50%;
  background: #d84f42;
  box-shadow: 0 0 0 1px rgba(255, 238, 210, .62);
}
.gomoku-board-hint { width: min(92vw, 650px); margin: -4px 0 0; color: var(--muted); text-align: center; font-size: 13px; }
@media (max-width: 600px) {
  .gomoku-board { width: min(96vw, 650px); padding: 8px; border-width: 4px; }
  .gomoku-board-hint { width: 100%; }
}
@media (hover: none) {
  .board-point:hover .stone-preview:not(.active) { opacity: 0; transform: scale(.82); }
}
</style>
