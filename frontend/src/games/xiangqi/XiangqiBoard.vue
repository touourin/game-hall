<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Flag } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const selected = ref<{ row: number; column: number } | null>(null)

const game = computed(() => props.snapshot.game as {
  board: Array<Array<string | null>>
  turnPlayerId: string | null
  colors: Record<string, 'red' | 'black'>
  viewerColor: 'red' | 'black'
  lastMove: {
    fromRow: number
    fromColumn: number
    toRow: number
    toColumn: number
  } | null
  redInCheck: boolean
  blackInCheck: boolean
})
const isMyTurn = computed(
  () => game.value.turnPlayerId === props.snapshot.self.id,
)
const displayRows = computed(() => {
  const rows = Array.from({ length: 10 }, (_, index) => index)
  return game.value.viewerColor === 'black' ? rows.reverse() : rows
})
const displayColumns = computed(() => {
  const columns = Array.from({ length: 9 }, (_, index) => index)
  return game.value.viewerColor === 'black' ? columns.reverse() : columns
})

const labels: Record<string, string> = {
  rK: '帅', rA: '仕', rE: '相', rH: '马', rR: '车', rC: '炮', rP: '兵',
  bK: '将', bA: '士', bE: '象', bH: '马', bR: '车', bC: '炮', bP: '卒',
}
const selectedPieceLabel = computed(() => {
  if (!selected.value) return ''
  return labels[
    game.value.board[selected.value.row]?.[selected.value.column] ?? ''
  ] ?? ''
})

watch(
  () => props.snapshot.revision,
  () => { selected.value = null },
)

function isOwn(piece: string | null): boolean {
  if (!piece) return false
  return piece.startsWith(game.value.viewerColor === 'red' ? 'r' : 'b')
}

function choose(row: number, column: number) {
  if (!isMyTurn.value || arcade.busy) return
  const piece = game.value.board[row]?.[column] ?? null
  if (!selected.value) {
    if (isOwn(piece)) selected.value = { row, column }
    return
  }
  if (isOwn(piece)) {
    if (selected.value.row === row && selected.value.column === column) {
      selected.value = null
      return
    }
    selected.value = { row, column }
    return
  }
  const source = selected.value
  selected.value = null
  void arcade.action('move', {
    fromRow: source.row,
    fromColumn: source.column,
    toRow: row,
    toColumn: column,
  })
}
</script>

<template>
  <section class="xiangqi-panel">
    <div class="xiangqi-status">
      <strong>{{ isMyTurn ? '轮到你走棋' : '等待对手走棋' }}</strong>
      <span>你执{{ game.viewerColor === 'red' ? '红' : '黑' }}</span>
      <span v-if="selected" class="selection">已选{{ selectedPieceLabel }} · 请选择落点</span>
      <span v-if="game.redInCheck || game.blackInCheck" class="check">将军！</span>
    </div>
    <div class="xiangqi-board" :class="{ 'has-selection': selected }" aria-label="中国象棋棋盘">
      <svg class="palace-lines" viewBox="0 0 8 9" preserveAspectRatio="none" aria-hidden="true">
        <path d="M3 0 L5 2 M5 0 L3 2 M3 7 L5 9 M5 7 L3 9" />
      </svg>
      <template v-for="row in displayRows" :key="row">
        <button
          v-for="column in displayColumns"
          :key="`${row}-${column}`"
          type="button"
          class="xiangqi-cell"
          :disabled="snapshot.phase !== 'playing' || !isMyTurn || arcade.busy"
          :aria-pressed="selected?.row === row && selected?.column === column"
          :aria-label="`第 ${row + 1} 行第 ${column + 1} 列`"
          :class="{
            selected: selected?.row === row && selected?.column === column,
            latest:
              game.lastMove?.toRow === row && game.lastMove?.toColumn === column,
            'last-from':
              game.lastMove?.fromRow === row && game.lastMove?.fromColumn === column,
            'river-bank-top':
              (game.viewerColor === 'red' && row === 4)
              || (game.viewerColor === 'black' && row === 5),
            'river-bank-bottom':
              (game.viewerColor === 'red' && row === 5)
              || (game.viewerColor === 'black' && row === 4),
            'edge-column': column === 0 || column === 8,
          }"
          @click="choose(row, column)"
        >
          <span
            v-if="game.board[row][column]"
            class="xiangqi-piece"
            :class="game.board[row][column]?.startsWith('r') ? 'red' : 'black'"
          >
            {{ labels[game.board[row][column] ?? ''] }}
          </span>
        </button>
      </template>
      <div class="river-label"><span>楚 河</span><span>汉 界</span></div>
    </div>
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
.xiangqi-panel { display: grid; gap: 15px; justify-items: center; }
.xiangqi-status { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px 14px; color: var(--muted); text-align: center; }
.xiangqi-status strong { color: var(--gold); }
.xiangqi-status .selection { color: color-mix(in srgb, var(--gold) 78%, white); font-weight: 800; }
.xiangqi-status .check { color: #ff8d86; font-weight: 800; }
.xiangqi-board {
  --board-padding: 18px;
  position: relative;
  width: min(92vw, 610px);
  aspect-ratio: 9 / 10;
  padding: var(--board-padding);
  display: grid;
  grid-template-columns: repeat(9, 1fr);
  grid-template-rows: repeat(10, 1fr);
  border: 7px double #6e3e19;
  border-radius: 12px;
  background-color: #d9aa65;
  background-image:
    linear-gradient(103deg, transparent 0 21%, rgba(106, 56, 17, .08) 21.4%, transparent 22%),
    repeating-linear-gradient(2deg, rgba(255, 245, 205, .065) 0 2px, rgba(92, 49, 16, .035) 3px 6px);
  box-shadow: inset 0 0 0 2px rgba(255, 229, 168, .3), inset 0 0 28px rgba(83, 39, 8, .22), 0 20px 50px #0006, 0 0 0 1px color-mix(in srgb, var(--gold) 24%, transparent);
}
.xiangqi-cell {
  position: relative;
  min-width: 0;
  padding: 0;
  border: 0;
  background:
    linear-gradient(#603b1d, #603b1d) center / 100% 1px no-repeat,
    linear-gradient(90deg, #603b1d, #603b1d) center / 1px 100% no-repeat;
}
.xiangqi-cell:disabled { opacity: 1; }
.xiangqi-cell:not(:disabled) { cursor: pointer; }
.xiangqi-cell.river-bank-top:not(.edge-column) {
  background:
    linear-gradient(#603b1d, #603b1d) center / 100% 1px no-repeat,
    linear-gradient(90deg, #603b1d, #603b1d) center top / 1px 50% no-repeat;
}
.xiangqi-cell.river-bank-bottom:not(.edge-column) {
  background:
    linear-gradient(#603b1d, #603b1d) center / 100% 1px no-repeat,
    linear-gradient(90deg, #603b1d, #603b1d) center bottom / 1px 50% no-repeat;
}
.xiangqi-cell.selected::after,
.xiangqi-cell.latest::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 4;
  border: 3px solid var(--gold);
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255, 235, 168, .35), 0 0 18px rgba(246, 196, 89, .62);
}
.xiangqi-cell.latest::after {
  inset: 10%;
  z-index: 1;
  border-width: 2px;
  border-color: #b94337;
  box-shadow: 0 0 0 2px rgba(255, 229, 186, .34);
}
.xiangqi-cell.last-from::before {
  content: '';
  position: absolute;
  inset: 30%;
  z-index: 1;
  border-radius: 50%;
  background: rgba(178, 64, 50, .62);
  box-shadow: 0 0 0 3px rgba(255, 225, 177, .28);
}
.xiangqi-cell:focus-visible { border-radius: 50%; outline-offset: -3px; }
.xiangqi-piece {
  position: absolute;
  inset: 5%;
  z-index: 2;
  display: grid;
  place-items: center;
  border: 2px solid currentColor;
  border-radius: 50%;
  background:
    radial-gradient(circle at 38% 30%, rgba(255, 245, 202, .9), transparent 27%),
    radial-gradient(circle, #efd398, #bd7d35 76%);
  box-shadow: 0 3px 7px #0008, inset 0 0 0 2px #edc77d, inset 0 -4px 8px rgba(103, 51, 12, .22);
  font-family: serif;
  font-size: clamp(15px, 4.5vw, 28px);
  font-weight: 900;
  transition: transform .14s ease, box-shadow .14s ease, filter .14s ease;
}
.xiangqi-piece.red { color: #a92b25; }
.xiangqi-piece.black { color: #242621; }
.xiangqi-cell.selected .xiangqi-piece {
  transform: translateY(-4px) scale(1.08);
  filter: saturate(1.12) brightness(1.06);
  box-shadow: 0 7px 13px rgba(48, 24, 8, .62), 0 0 0 3px #f4cd68, 0 0 22px rgba(246, 196, 82, .78), inset 0 0 0 2px #f3d58d;
}
.palace-lines {
  pointer-events: none;
  position: absolute;
  z-index: 1;
  left: calc(var(--board-padding) + 5.2%);
  right: calc(var(--board-padding) + 5.2%);
  top: calc(var(--board-padding) + 4.75%);
  bottom: calc(var(--board-padding) + 4.75%);
  width: auto;
  height: auto;
  overflow: visible;
}
.palace-lines path { fill: none; stroke: #603b1d; stroke-width: .025; }
.river-label {
  pointer-events: none;
  position: absolute;
  top: 50%;
  left: 8%;
  right: 8%;
  display: flex;
  justify-content: space-around;
  z-index: 2;
  color: #603b1d;
  font-family: serif;
  font-size: clamp(16px, 4vw, 28px);
  font-weight: 900;
  text-shadow: 0 1px rgba(255, 229, 164, .46);
  transform: translateY(-50%);
}
@media (max-width: 600px) {
  .xiangqi-board { --board-padding: 10px; width: 100%; border-width: 5px; }
  .xiangqi-piece { font-size: clamp(14px, 5.5vw, 24px); }
}
</style>
