<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight, Download, Flag, History, X } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'

interface XiangqiMove {
  number: number
  fromRow: number
  fromColumn: number
  toRow: number
  toColumn: number
  piece: string
  captured: string | null
  color: 'red' | 'black'
  gaveCheck: boolean
}

interface LegalMove {
  fromRow: number
  fromColumn: number
  toRow: number
  toColumn: number
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const selected = ref<{ row: number; column: number } | null>(null)
const pendingTarget = ref<{ row: number; column: number } | null>(null)
const showReplay = ref(false)
const replayStep = ref(0)

const game = computed(() => props.snapshot.game as {
  board: Array<Array<string | null>>
  turnPlayerId: string | null
  colors: Record<string, 'red' | 'black'>
  viewerColor: 'red' | 'black'
  lastMove: XiangqiMove | null
  moveHistory: XiangqiMove[]
  capturedPieces: Array<{ piece: string; capturedBy: 'red' | 'black'; moveNumber: number }>
  legalMoves: LegalMove[]
  redInCheck: boolean
  blackInCheck: boolean
  checkedColor: 'red' | 'black' | null
})
const isMyTurn = computed(
  () => game.value.turnPlayerId === props.snapshot.self.id,
)
const isReplaying = computed(() => showReplay.value)
const moveHistory = computed(() => game.value.moveHistory ?? [])
const selectedLegalMoves = computed(() => selected.value
  ? (game.value.legalMoves ?? []).filter(
      (move) => move.fromRow === selected.value?.row
        && move.fromColumn === selected.value?.column,
    )
  : [])
const displayRows = computed(() => {
  const rows = Array.from({ length: 10 }, (_, index) => index)
  return game.value.viewerColor === 'black' ? rows.reverse() : rows
})
const displayColumns = computed(() => {
  const columns = Array.from({ length: 9 }, (_, index) => index)
  return game.value.viewerColor === 'black' ? columns.reverse() : columns
})
const displayBoard = computed(() => {
  if (!isReplaying.value) return game.value.board
  const board = makeInitialBoard()
  for (const move of moveHistory.value.slice(0, replayStep.value)) {
    board[move.toRow][move.toColumn] = move.piece
    board[move.fromRow][move.fromColumn] = null
  }
  return board
})
const replayMove = computed(
  () => replayStep.value > 0 ? moveHistory.value[replayStep.value - 1] : null,
)
const checkedText = computed(() => game.value.checkedColor
  ? `${game.value.checkedColor === 'red' ? '红方' : '黑方'}被将军！`
  : '')
const capturedRed = computed(() => (game.value.capturedPieces ?? []).filter((item) => item.piece.startsWith('r')))
const capturedBlack = computed(() => (game.value.capturedPieces ?? []).filter((item) => item.piece.startsWith('b')))

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
const selectionHint = computed(() => {
  if (!selected.value) return ''
  if (!pendingTarget.value) return `已选${selectedPieceLabel.value} · 请选择落点`
  return `预览${selectedPieceLabel.value}到第 ${pendingTarget.value.row + 1} 行第 ${pendingTarget.value.column + 1} 列 · 再点一次确认`
})

watch(
  () => props.snapshot.revision,
  () => {
    selected.value = null
    pendingTarget.value = null
    if (showReplay.value) replayStep.value = moveHistory.value.length
  },
)

function makeInitialBoard(): Array<Array<string | null>> {
  const board: Array<Array<string | null>> = Array.from({ length: 10 }, () => Array(9).fill(null))
  const backRank = ['R', 'H', 'E', 'A', 'K', 'A', 'E', 'H', 'R']
  board[0] = backRank.map((piece) => `b${piece}`)
  board[2][1] = board[2][7] = 'bC'
  board[3][0] = board[3][2] = board[3][4] = board[3][6] = board[3][8] = 'bP'
  board[6][0] = board[6][2] = board[6][4] = board[6][6] = board[6][8] = 'rP'
  board[7][1] = board[7][7] = 'rC'
  board[9] = backRank.map((piece) => `r${piece}`)
  return board
}

function isOwn(piece: string | null): boolean {
  if (!piece) return false
  return piece.startsWith(game.value.viewerColor === 'red' ? 'r' : 'b')
}

function isLegalTarget(row: number, column: number): boolean {
  return selectedLegalMoves.value.some(
    (move) => move.toRow === row && move.toColumn === column,
  )
}

function isPendingTarget(row: number, column: number): boolean {
  return pendingTarget.value?.row === row && pendingTarget.value?.column === column
}

function usesTouchConfirmation(event: MouseEvent): boolean {
  const pointerType = (event as PointerEvent).pointerType ?? ''
  return ['touch', 'pen'].includes(pointerType)
    || (pointerType === '' && window.matchMedia?.('(pointer: coarse)').matches === true)
}

function choose(row: number, column: number, event: MouseEvent) {
  if (!isMyTurn.value || isReplaying.value || arcade.busy) return
  const piece = game.value.board[row]?.[column] ?? null
  if (!selected.value) {
    if (isOwn(piece)) {
      selected.value = { row, column }
      pendingTarget.value = null
    }
    return
  }
  if (isOwn(piece)) {
    if (selected.value.row === row && selected.value.column === column) {
      selected.value = null
      pendingTarget.value = null
      return
    }
    selected.value = { row, column }
    pendingTarget.value = null
    return
  }
  if (!isLegalTarget(row, column)) return
  if (usesTouchConfirmation(event) && !isPendingTarget(row, column)) {
    pendingTarget.value = { row, column }
    return
  }
  const source = selected.value
  selected.value = null
  pendingTarget.value = null
  void arcade.action('move', {
    fromRow: source.row,
    fromColumn: source.column,
    toRow: row,
    toColumn: column,
  })
}

function openReplay(step = moveHistory.value.length) {
  replayStep.value = step
  selected.value = null
  pendingTarget.value = null
  showReplay.value = true
}

function moveLabel(move: XiangqiMove): string {
  const piece = labels[move.piece] ?? move.piece
  return `${piece} (${move.fromRow + 1},${move.fromColumn + 1}) → (${move.toRow + 1},${move.toColumn + 1})`
}

function exportMoves() {
  const lines = moveHistory.value.map((move, index) => {
    const round = Math.floor(index / 2) + 1
    return `${round}.${index % 2 === 0 ? '红' : '黑'} ${moveLabel(move)}${move.gaveCheck ? ' 将军' : ''}`
  })
  const blob = new Blob([
    `中国象棋 房间 ${props.snapshot.roomCode}\n${props.snapshot.players.map((player) => `${player.name}（${game.value.colors[player.id] === 'red' ? '红' : '黑'}）`).join(' vs ')}\n\n${lines.join('\n')}\n`,
  ], { type: 'text/plain;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `象棋-${props.snapshot.roomCode}.txt`
  link.click()
  URL.revokeObjectURL(link.href)
}
</script>

<template>
  <section class="xiangqi-panel">
    <div class="xiangqi-status">
      <strong>{{ isReplaying ? `复盘第 ${replayStep} / ${moveHistory.length} 手` : isMyTurn ? '轮到你走棋' : '等待对手走棋' }}</strong>
      <span>你执{{ game.viewerColor === 'red' ? '红' : '黑' }}</span>
      <span v-if="selected && !isReplaying" class="selection">{{ selectionHint }}</span>
      <span v-if="checkedText && !isReplaying" class="check">{{ checkedText }}</span>
    </div>

    <div class="captured-pieces">
      <span><b>红方被吃</b><i v-for="(item, index) in capturedRed" :key="index">{{ labels[item.piece] }}</i><em v-if="!capturedRed.length">无</em></span>
      <span><b>黑方被吃</b><i v-for="(item, index) in capturedBlack" :key="index">{{ labels[item.piece] }}</i><em v-if="!capturedBlack.length">无</em></span>
    </div>

    <div class="xiangqi-board" :class="{ 'has-selection': selected }" aria-label="中国象棋棋盘">
      <div class="xiangqi-grid">
        <svg class="xiangqi-lines" viewBox="0 0 8 9" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0 0H8 M0 1H8 M0 2H8 M0 3H8 M0 4H8 M0 5H8 M0 6H8 M0 7H8 M0 8H8 M0 9H8" />
          <path d="M0 0V9 M8 0V9 M1 0V4 M1 5V9 M2 0V4 M2 5V9 M3 0V4 M3 5V9 M4 0V4 M4 5V9 M5 0V4 M5 5V9 M6 0V4 M6 5V9 M7 0V4 M7 5V9" />
          <path class="palace-lines" d="M3 0L5 2 M5 0L3 2 M3 7L5 9 M5 7L3 9" />
        </svg>
        <template v-for="row in displayRows" :key="row">
          <button
            v-for="column in displayColumns"
            :key="`${row}-${column}`"
            type="button"
            class="xiangqi-cell"
            :disabled="snapshot.phase !== 'playing' || !isMyTurn || isReplaying || arcade.busy"
            :aria-pressed="selected?.row === row && selected?.column === column"
            :aria-label="`第 ${row + 1} 行第 ${column + 1} 列`"
            :class="{
              selected: selected?.row === row && selected?.column === column,
              confirming: isPendingTarget(row, column),
              legal: !isReplaying && isLegalTarget(row, column),
              capture: !isReplaying && isLegalTarget(row, column) && game.board[row][column],
              latest: (isReplaying ? replayMove : game.lastMove)?.toRow === row && (isReplaying ? replayMove : game.lastMove)?.toColumn === column,
              'last-from': (isReplaying ? replayMove : game.lastMove)?.fromRow === row && (isReplaying ? replayMove : game.lastMove)?.fromColumn === column,
            }"
            @click="choose(row, column, $event)"
          >
            <span
              v-if="displayBoard[row][column]"
              class="xiangqi-piece"
              :class="displayBoard[row][column]?.startsWith('r') ? 'red' : 'black'"
            >{{ labels[displayBoard[row][column] ?? ''] }}</span>
          </button>
        </template>
        <div class="river-label"><span>楚 河</span><span>汉 界</span></div>
      </div>
    </div>

    <div class="xiangqi-actions">
      <button type="button" :disabled="!moveHistory.length" @click="openReplay()"><History :size="17" />对局复盘</button>
      <button type="button" :disabled="!moveHistory.length" @click="exportMoves"><Download :size="17" />导出记录</button>
      <button v-if="snapshot.phase === 'playing'" type="button" class="arcade-danger-button" @click="arcade.action('resign')"><Flag :size="17" />认输</button>
    </div>

    <div v-if="showReplay" class="replay-backdrop" @click.self="showReplay = false">
      <section class="replay-panel" role="dialog" aria-modal="true" aria-label="象棋对局复盘">
        <header><div><small>走棋记录</small><strong>第 {{ replayStep }} / {{ moveHistory.length }} 手</strong></div><button type="button" aria-label="关闭复盘" @click="showReplay = false"><X :size="20" /></button></header>
        <div class="move-list">
          <button type="button" :class="{ active: replayStep === 0 }" @click="replayStep = 0">开局</button>
          <button v-for="move in moveHistory" :key="move.number" type="button" :class="{ active: replayStep === move.number }" @click="replayStep = move.number">
            <span>{{ move.number }}.</span><b>{{ moveLabel(move) }}</b><em v-if="move.gaveCheck">将军</em>
          </button>
        </div>
        <footer>
          <button type="button" :disabled="replayStep === 0" @click="replayStep--"><ChevronLeft :size="18" />上一步</button>
          <button type="button" :disabled="replayStep >= moveHistory.length" @click="replayStep++">下一步<ChevronRight :size="18" /></button>
        </footer>
      </section>
    </div>
  </section>
</template>

<style scoped>
.xiangqi-panel { display: grid; gap: 15px; justify-items: center; }.xiangqi-status { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px 14px; color: var(--muted); text-align: center; }.xiangqi-status strong { color: var(--gold); }.xiangqi-status .selection { color: color-mix(in srgb, var(--gold) 78%, white); font-weight: 800; }.xiangqi-status .check { color: #ff8d86; font-weight: 800; }
.captured-pieces { width: min(92vw, 610px); display: grid; grid-template-columns: 1fr 1fr; gap: 9px; }.captured-pieces > span { min-height: 38px; display: flex; flex-wrap: wrap; align-items: center; gap: 5px; border: 1px solid var(--line); border-radius: 10px; padding: 7px 10px; color: var(--muted); background: rgba(0,0,0,.1); }.captured-pieces b { margin-right: 5px; color: var(--text); }.captured-pieces i { width: 24px; height: 24px; display: grid; place-items: center; border-radius: 50%; color: #3b2718; background: #d6a05d; font-family: serif; font-style: normal; font-weight: 900; }.captured-pieces em { font-style: normal; }
.xiangqi-board { --board-padding: clamp(14px, 3vw, 20px); position: relative; width: min(100%, 610px); box-sizing: border-box; overflow: hidden; padding: var(--board-padding); border: 3px solid var(--game-board-frame, #74451f); border-radius: 15px; background-color: var(--game-board-surface, #d9aa65); background-image: var(--game-board-texture, repeating-linear-gradient(2deg, rgba(255, 245, 205, .075) 0 2px, rgba(92, 49, 16, .04) 3px 7px)); box-shadow: inset 0 0 0 3px var(--game-board-highlight, #e5bd75), inset 0 0 0 6px color-mix(in srgb, var(--game-board-frame, #74451f) 62%, transparent), inset 0 0 30px rgba(0, 0, 0, .2), 0 18px 45px #0006, 0 0 0 1px color-mix(in srgb, var(--gold) 24%, transparent); }
.xiangqi-grid { position: relative; isolation: isolate; width: 100%; aspect-ratio: 9 / 10; display: grid; grid-template-columns: repeat(9, 1fr); grid-template-rows: repeat(10, 1fr); }
.xiangqi-lines { pointer-events: none; position: absolute; z-index: 0; inset: 5% 5.5556%; width: auto; height: auto; overflow: hidden; }.xiangqi-lines path { fill: none; stroke: var(--game-board-line, #603b1d); stroke-width: 1.25; vector-effect: non-scaling-stroke; stroke-linecap: square; }
.xiangqi-cell { position: relative; z-index: 2; min-width: 0; min-height: 0; appearance: none; -webkit-appearance: none; touch-action: manipulation; padding: 0; border: 0; border-radius: 0; background: transparent; }.xiangqi-cell:disabled { opacity: 1; }.xiangqi-cell:not(:disabled) { cursor: pointer; }.xiangqi-cell.selected::after, .xiangqi-cell.latest::after { content: ''; position: absolute; inset: 0; z-index: 4; border: 3px solid var(--gold); border-radius: 50%; box-shadow: 0 0 0 2px rgba(255, 235, 168, .35), 0 0 18px rgba(246, 196, 89, .62); }.xiangqi-cell.latest::after { inset: 10%; z-index: 1; border-width: 2px; border-color: #b94337; box-shadow: 0 0 0 2px rgba(255, 229, 186, .34); }.xiangqi-cell.last-from::before { content: ''; position: absolute; inset: 30%; z-index: 1; border-radius: 50%; background: rgba(178, 64, 50, .62); box-shadow: 0 0 0 3px rgba(255, 225, 177, .28); }.xiangqi-cell.legal::before { content: ''; position: absolute; z-index: 3; width: 13px; height: 13px; top: 50%; left: 50%; border-radius: 50%; background: #18875edb; box-shadow: 0 0 0 4px rgba(24, 135, 94, .14); transform: translate(-50%, -50%); }.xiangqi-cell.legal.capture::before { width: 72%; height: 72%; border: 3px solid #18875e; background: transparent; box-shadow: 0 0 0 3px rgba(24, 135, 94, .13); }
.xiangqi-cell.confirming::after { content: ''; position: absolute; inset: 5%; z-index: 5; border: 3px solid var(--gold); border-radius: 50%; background: color-mix(in srgb, var(--gold) 16%, transparent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--gold) 22%, transparent), 0 0 20px color-mix(in srgb, var(--gold) 62%, transparent); pointer-events: none; }
.xiangqi-cell:focus-visible { border-radius: 50%; outline-offset: -3px; }
.xiangqi-piece { position: absolute; inset: 7%; z-index: 3; display: grid; place-items: center; border: 2px solid currentColor; border-radius: 50%; background: var(--game-piece-surface, radial-gradient(circle at 38% 30%, rgba(255, 248, 215, .92), transparent 27%), radial-gradient(circle, #efd398, #bd7d35 76%)); box-shadow: 0 3px 7px #0008, inset 0 0 0 2px var(--game-piece-rim, #edc77d), inset 0 -4px 8px rgba(0, 0, 0, .22); font-family: serif; font-size: clamp(15px, 4.3vw, 27px); line-height: 1; font-weight: 900; transition: transform .14s ease, box-shadow .14s ease, filter .14s ease; }.xiangqi-piece.red { color: #a92b25; }.xiangqi-piece.black { color: #242621; }.xiangqi-cell.selected .xiangqi-piece { transform: translateY(-3px) scale(1.06); filter: saturate(1.12) brightness(1.06); box-shadow: 0 7px 13px rgba(48, 24, 8, .62), 0 0 0 3px #f4cd68, 0 0 22px rgba(246, 196, 82, .78), inset 0 0 0 2px #f3d58d; }.river-label { pointer-events: none; position: absolute; z-index: 1; top: 50%; left: 9%; right: 9%; display: flex; justify-content: space-around; color: var(--game-board-label, #603b1d); font-family: serif; font-size: clamp(16px, 4vw, 27px); line-height: 1; font-weight: 900; text-shadow: 0 1px rgba(255, 255, 255, .28); transform: translateY(-50%); }
.xiangqi-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }.xiangqi-actions > button:not(.arcade-danger-button) { min-height: 42px; display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 10px; padding: 0 13px; color: var(--text); background: var(--surface); font-weight: 800; }.xiangqi-actions button:disabled { opacity: .4; }
.replay-backdrop { position: fixed; z-index: 80; inset: 0; display: grid; place-items: center; padding: 18px; background: #020b0bd4; }.replay-panel { width: min(92vw, 560px); max-height: min(82vh, 720px); display: grid; grid-template-rows: auto 1fr auto; gap: 12px; border: 1px solid var(--line); border-radius: 17px; padding: 17px; background: var(--surface-strong); box-shadow: 0 24px 70px #000a; }.replay-panel header { display: flex; justify-content: space-between; align-items: center; }.replay-panel header > div { display: grid; }.replay-panel header small { color: var(--gold); }.replay-panel header button { border: 0; color: var(--muted); background: transparent; }.move-list { min-height: 0; overflow: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }.move-list button { min-height: 42px; display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 8px; padding: 7px 9px; color: var(--text); background: rgba(0,0,0,.11); text-align: left; }.move-list button.active { border-color: var(--gold); background: color-mix(in srgb, var(--gold) 12%, transparent); }.move-list span { color: var(--muted); }.move-list em { color: #ff8d86; font-style: normal; font-size: 12px; }.replay-panel footer { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }.replay-panel footer button { min-height: 42px; display: flex; justify-content: center; align-items: center; gap: 5px; border: 1px solid var(--line); border-radius: 9px; color: var(--text); background: rgba(0,0,0,.14); }
@media (max-width: 600px) { .xiangqi-panel { gap: 10px; width: 100%; }.xiangqi-status { position: sticky; z-index: 7; top: max(6px, env(safe-area-inset-top)); width: 100%; border: 1px solid color-mix(in srgb, var(--gold) 28%, var(--line)); border-radius: 12px; padding: 9px 10px; background: color-mix(in srgb, var(--surface-elevated) 94%, transparent); box-shadow: 0 8px 24px rgba(0,0,0,.18); backdrop-filter: blur(14px); }.captured-pieces { width: 100%; grid-template-columns: 1fr 1fr; gap: 6px; }.captured-pieces > span { min-height: 34px; padding: 5px 8px; font-size: 11px; }.captured-pieces i { width: 21px; height: 21px; }.xiangqi-board { --board-padding: clamp(10px, 3.2vw, 14px); width: min(100%, calc((100dvh - 235px) * .9)); min-width: min(100%, 296px); border-width: 2px; border-radius: 13px; }.move-list { grid-template-columns: 1fr; }.replay-panel { width: 100%; max-height: 88dvh; }.xiangqi-piece { inset: 7%; font-size: clamp(14px, 5.1vw, 22px); }.xiangqi-lines path { stroke-width: 1.1; }.river-label { font-size: clamp(16px, 4.8vw, 21px); }.xiangqi-actions { width: 100%; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }.xiangqi-actions > button, .xiangqi-actions > button:not(.arcade-danger-button) { min-width: 0; justify-content: center; padding: 0 7px; font-size: 11px; } }
@media (orientation: landscape) and (min-width: 601px) and (max-width: 980px) and (max-height: 600px) {
  .xiangqi-panel { width: min(100%, 820px); grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: "status board" "captured board" "actions board"; align-items: start; justify-items: stretch; gap: 9px 14px; }
  .xiangqi-status { grid-area: status; align-self: end; border: 1px solid color-mix(in srgb, var(--gold) 28%, var(--line)); border-radius: 12px; padding: 9px 10px; background: color-mix(in srgb, var(--surface-elevated) 94%, transparent); }
  .captured-pieces { grid-area: captured; width: 100%; grid-template-columns: 1fr; gap: 6px; }
  .captured-pieces > span { min-height: 32px; padding: 4px 8px; font-size: 10px; }
  .captured-pieces i { width: 20px; height: 20px; }
  .xiangqi-board { grid-area: board; --board-padding: 10px; width: min(42vw, calc((100dvh - 78px) * .9)); min-width: 250px; max-width: 400px; border-width: 2px; border-radius: 12px; }
  .xiangqi-piece { inset: 6%; font-size: clamp(14px, 2.9vw, 21px); }
  .river-label { font-size: clamp(15px, 2.5vw, 20px); }
  .xiangqi-actions { grid-area: actions; width: 100%; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .xiangqi-actions > button, .xiangqi-actions > button:not(.arcade-danger-button) { min-width: 0; min-height: 38px; justify-content: center; padding: 0 7px; font-size: 10px; }
  .xiangqi-actions .arcade-danger-button { grid-column: 1 / -1; }
}
@media (max-width: 360px) { .captured-pieces { grid-template-columns: 1fr; }.xiangqi-board { min-width: 0; }.xiangqi-piece { inset: 5%; font-size: clamp(13px, 5.2vw, 18px); }.xiangqi-actions { grid-template-columns: 1fr 1fr; }.xiangqi-actions .arcade-danger-button { grid-column: 1 / -1; } }
</style>
