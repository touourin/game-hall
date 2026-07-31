<script setup lang="ts">
import { computed, ref } from 'vue'
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

function isOwn(piece: string | null): boolean {
  if (!piece) return false
  return piece.startsWith(game.value.viewerColor === 'red' ? 'r' : 'b')
}

function choose(row: number, column: number) {
  if (!isMyTurn.value) return
  const piece = game.value.board[row]?.[column] ?? null
  if (!selected.value) {
    if (isOwn(piece)) selected.value = { row, column }
    return
  }
  if (isOwn(piece)) {
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
      <span v-if="game.redInCheck || game.blackInCheck" class="check">将军！</span>
    </div>
    <div class="xiangqi-board" aria-label="中国象棋棋盘">
      <template v-for="row in displayRows" :key="row">
        <button
          v-for="column in displayColumns"
          :key="`${row}-${column}`"
          type="button"
          class="xiangqi-cell"
          :class="{
            selected: selected?.row === row && selected?.column === column,
            latest:
              game.lastMove?.toRow === row && game.lastMove?.toColumn === column,
            river: row === 4,
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
      class="resign-button"
      @click="arcade.action('resign')"
    >
      认输
    </button>
  </section>
</template>

<style scoped>
.xiangqi-panel { display: grid; gap: 15px; justify-items: center; }
.xiangqi-status { display: flex; gap: 14px; color: var(--muted); }
.xiangqi-status strong { color: var(--gold); }
.xiangqi-status .check { color: #ff8d86; font-weight: 800; }
.xiangqi-board {
  position: relative;
  width: min(92vw, 610px);
  aspect-ratio: 9 / 10;
  padding: 18px;
  display: grid;
  grid-template-columns: repeat(9, 1fr);
  grid-template-rows: repeat(10, 1fr);
  background: #d7a763;
  border: 4px double #75471f;
  border-radius: 8px;
  box-shadow: 0 20px 50px #0006;
}
.xiangqi-cell {
  position: relative;
  min-width: 0;
  padding: 0;
  border: 0;
  background:
    linear-gradient(#704a29, #704a29) center / 100% 1px no-repeat,
    linear-gradient(90deg, #704a29, #704a29) center / 1px 100% no-repeat;
}
.xiangqi-cell.selected::after,
.xiangqi-cell.latest::after {
  content: '';
  position: absolute;
  inset: 8%;
  border: 3px solid #e8c25a;
  border-radius: 50%;
}
.xiangqi-cell.latest::after { border-color: #4c947b; }
.xiangqi-piece {
  position: absolute;
  inset: 5%;
  z-index: 2;
  display: grid;
  place-items: center;
  border: 2px solid currentColor;
  border-radius: 50%;
  background: radial-gradient(circle, #f5d99b, #c68d43);
  box-shadow: 0 2px 5px #0008, inset 0 0 0 2px #eac681;
  font-family: serif;
  font-size: clamp(15px, 4.5vw, 28px);
  font-weight: 900;
}
.xiangqi-piece.red { color: #a92b25; }
.xiangqi-piece.black { color: #242621; }
.river-label {
  pointer-events: none;
  position: absolute;
  top: 50%;
  left: 8%;
  right: 8%;
  display: flex;
  justify-content: space-around;
  color: #704a29;
  font-family: serif;
  font-size: clamp(16px, 4vw, 28px);
  font-weight: 900;
  transform: translateY(-50%);
}
.resign-button { padding: 10px 22px; border: 1px solid #9b4c4c; border-radius: 12px; color: #ffaaa8; background: var(--surface); }
</style>
