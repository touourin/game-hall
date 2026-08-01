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
  colors: Record<string, 'black' | 'white'>
  captures: { black: number; white: number }
  komi: number
  lastMove: { row?: number; column?: number; pass: boolean } | null
  score: { black: number; white: number } | null
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
    game.value.lastMove?.pass,
  ],
  () => {
    pendingMove.value = null
  },
)

function isPendingMove(row: number, column: number) {
  return pendingMove.value?.row === row && pendingMove.value?.column === column
}

function usesTouchConfirmation(event: MouseEvent) {
  return ['touch', 'pen'].includes((event as PointerEvent).pointerType ?? '')
}

function isStarPoint(row: number, column: number) {
  const starsBySize: Record<number, Array<[number, number]>> = {
    9: [[2, 2], [2, 6], [4, 4], [6, 2], [6, 6]],
    13: [[3, 3], [3, 9], [6, 6], [9, 3], [9, 9]],
    19: [
      [3, 3], [3, 9], [3, 15],
      [9, 3], [9, 9], [9, 15],
      [15, 3], [15, 9], [15, 15],
    ],
  }
  return (starsBySize[game.value.boardSize] ?? []).some(
    ([starRow, starColumn]) => starRow === row && starColumn === column,
  )
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
  <section class="go-panel">
    <div class="go-status">
      <strong>{{ isMyTurn ? '轮到你落子' : '等待对手落子' }}</strong>
      <span>你执{{ game.colors[snapshot.self.id] === 'black' ? '黑' : '白' }}</span>
      <span>提子 黑 {{ game.captures.black }} · 白 {{ game.captures.white }}</span>
      <span>贴目 {{ game.komi }}</span>
    </div>
    <div
      class="go-board"
      :style="{ '--board-size': game.boardSize }"
      aria-label="十九路围棋棋盘"
    >
      <template v-for="(row, rowIndex) in game.board" :key="rowIndex">
        <button
          v-for="(cell, columnIndex) in row"
          :key="`${rowIndex}-${columnIndex}`"
          type="button"
          class="go-point"
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
            class="go-stone go-preview"
            :class="[previewColor, { active: isPendingMove(rowIndex, columnIndex) }]"
            aria-hidden="true"
          />
          <span
            v-if="cell"
            class="go-stone"
            :class="[
              cell === 1 ? 'black' : 'white',
              {
                latest:
                  !game.lastMove?.pass &&
                  game.lastMove?.row === rowIndex &&
                  game.lastMove?.column === columnIndex,
              },
            ]"
          />
        </button>
      </template>
    </div>
    <p v-if="canPlace" class="go-board-hint" aria-live="polite">
      {{ pendingMoveLabel }}
    </p>
    <div v-if="snapshot.phase === 'playing'" class="inline-actions">
      <button type="button" :disabled="!isMyTurn" @click="arcade.action('pass')">
        停一手
      </button>
      <button type="button" class="arcade-danger-button" @click="arcade.action('resign')">
        <Flag :size="17" />认输
      </button>
    </div>
    <p v-if="game.score" class="score-line">
      终局数子：黑 {{ game.score.black }} · 白 {{ game.score.white }}
    </p>
  </section>
</template>

<style scoped>
.go-panel { display: grid; gap: 14px; justify-items: center; }
.go-status { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px 16px; color: var(--muted); }
.go-status strong { color: var(--gold); }
.go-board {
  --board-size: 19;
  width: min(94vw, 700px);
  aspect-ratio: 1;
  padding: 11px;
  display: grid;
  grid-template-columns: repeat(var(--board-size), 1fr);
  border: 5px solid #70431d;
  border-radius: 12px;
  background-color: #d8aa63;
  background-image:
    linear-gradient(102deg, transparent 0 23%, rgba(111, 62, 20, .075) 23.4%, transparent 24%),
    repeating-linear-gradient(2deg, rgba(255, 245, 205, .06) 0 2px, rgba(94, 53, 20, .035) 3px 6px);
  box-shadow:
    inset 0 0 0 2px rgba(255, 228, 169, .34),
    inset 0 0 26px rgba(88, 43, 10, .2),
    0 20px 50px #0006,
    0 0 0 1px color-mix(in srgb, var(--gold) 24%, transparent);
}
.go-point {
  position: relative;
  min-width: 0;
  padding: 0;
  border: 0;
  background:
    linear-gradient(#563519, #563519) center / 100% 1px no-repeat,
    linear-gradient(90deg, #563519, #563519) center / 1px 100% no-repeat;
}
.go-point:disabled { opacity: 1; }
.go-point:not(:disabled) { cursor: crosshair; }
.go-point:focus-visible { border-radius: 50%; outline-offset: -3px; }
.go-point.star::before { content: ''; position: absolute; inset: 40%; z-index: 1; border-radius: 50%; background: #513016; }
.go-stone { position: absolute; inset: 3%; z-index: 2; border-radius: 50%; box-shadow: inset -2px -3px 4px #0005, 0 2px 5px #0008; transition: opacity .15s, transform .15s; }
.go-stone.black { background: radial-gradient(circle at 35% 30%, #555, #050505 68%); }
.go-stone.white { border: 1px solid rgba(76, 56, 32, .22); background: radial-gradient(circle at 35% 30%, white, #d7d2c8 72%); }
.go-stone.latest::after { content: ''; position: absolute; inset: 37%; border-radius: 50%; background: #d84f42; box-shadow: 0 0 0 1px rgba(255, 238, 210, .62); }
.go-preview { z-index: 4; opacity: 0; transform: scale(.82); pointer-events: none; }
.go-point:not(:disabled):hover .go-preview,
.go-preview.active { opacity: .48; transform: scale(1); }
.go-preview.active { outline: 2px solid rgba(255, 245, 197, .78); outline-offset: 2px; }
.inline-actions { display: flex; gap: 10px; }
.inline-actions button:not(.arcade-danger-button) { border: 1px solid var(--line); border-radius: 12px; padding: 10px 18px; color: var(--text); background: var(--surface); }
.score-line { color: var(--gold); }
.go-board-hint { width: min(94vw, 700px); margin: -3px 0 0; color: var(--muted); text-align: center; font-size: 13px; }
@media (max-width: 600px) {
  .go-board { width: min(96vw, 700px); padding: 7px; border-width: 4px; }
  .go-board-hint { width: 100%; }
}
@media (hover: none) {
  .go-point:hover .go-preview:not(.active) { opacity: 0; transform: scale(.82); }
}
</style>
