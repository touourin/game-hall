<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight, Download, Flag, History, X } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import UiButton from '../../components/ui/UiButton.vue'
import UiIconButton from '../../components/ui/UiIconButton.vue'

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
  destinationAttacked?: boolean
  destinationProtected?: boolean
}

type HintTone = 'green' | 'red'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const selected = ref<{ row: number; column: number } | null>(null)
const pendingTarget = ref<{ row: number; column: number } | null>(null)
const showReplay = ref(false)
const replayStep = ref(0)

const game = computed(() => props.snapshot.game as {
  board: Array<Array<string | null>>
  initialBoard: Array<Array<string | null>>
  turnPlayerId: string | null
  colors: Record<string, 'red' | 'black'>
  viewerColor: 'red' | 'black'
  lastMove: XiangqiMove | null
  moveHistory: XiangqiMove[]
  capturedPieces: Array<{ piece: string; capturedBy: 'red' | 'black'; moveNumber: number }>
  legalMoves: LegalMove[]
  hangingPieces?: Array<{ row: number; column: number }>
  redInCheck: boolean
  blackInCheck: boolean
  checkedColor: 'red' | 'black' | null
})
const isMyTurn = computed(
  () => game.value.turnPlayerId === props.snapshot.self.id,
)
const isReplaying = computed(() => showReplay.value)
const moveHistory = computed(() => game.value.moveHistory ?? [])
const captureHintsEnabled = computed(
  () => props.snapshot.options.captureHintsEnabled !== false,
)
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
const boardGeometry = {
  columns: 9,
  rows: 10,
  firstX: 0.5,
  lastX: 8.5,
  firstY: 0.5,
  lastY: 9.5,
} as const
const horizontalGridPath = Array.from(
  { length: boardGeometry.rows - 2 },
  (_, index) => `M${boardGeometry.firstX} ${index + 1.5}H${boardGeometry.lastX}`,
).join(' ')
const verticalGridPath = Array.from(
  { length: boardGeometry.columns - 2 },
  (_, index) => {
    const x = index + 1.5
    return `M${x} ${boardGeometry.firstY}V4.5 M${x} 5.5V${boardGeometry.lastY}`
  },
).join(' ')
const palaceGridPath = 'M3.5 .5L5.5 2.5 M5.5 .5L3.5 2.5 M3.5 7.5L5.5 9.5 M5.5 7.5L3.5 9.5'
const placementMarkPoints = [
  { row: 2, column: 1 }, { row: 2, column: 7 },
  { row: 3, column: 0 }, { row: 3, column: 2 }, { row: 3, column: 4 },
  { row: 3, column: 6 }, { row: 3, column: 8 },
  { row: 6, column: 0 }, { row: 6, column: 2 }, { row: 6, column: 4 },
  { row: 6, column: 6 }, { row: 6, column: 8 },
  { row: 7, column: 1 }, { row: 7, column: 7 },
] as const
const placementMarkSegments = placementMarkPoints.flatMap(({ row, column }) => [
  ...(column > 0 ? [{ row, column, side: 'left' as const }] : []),
  ...(column < 8 ? [{ row, column, side: 'right' as const }] : []),
])
const hangingPieceKeys = computed(() => new Set(
  (game.value.hangingPieces ?? []).map(({ row, column }) => `${row}:${column}`),
))

function selectedMoveHintTone(move: LegalMove): HintTone {
  if (!captureHintsEnabled.value) return 'green'
  return move.destinationAttacked === true
    && move.destinationProtected !== true
    ? 'red'
    : 'green'
}

const boardHints = computed(() => {
  const hints = new Map<string, HintTone>()
  if (isReplaying.value) return hints

  if (captureHintsEnabled.value) {
    for (const key of hangingPieceKeys.value) hints.set(key, 'red')
  }

  if (isMyTurn.value && selected.value) {
    for (const move of selectedLegalMoves.value) {
      const key = `${move.toRow}:${move.toColumn}`
      const tone = selectedMoveHintTone(move)
      if (tone === 'red' || !hints.has(key)) hints.set(key, tone)
    }
  }
  return hints
})
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
  if (game.value.initialBoard) {
    return game.value.initialBoard.map((row) => [...row])
  }
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

function isHangingPiece(row: number, column: number): boolean {
  return hangingPieceKeys.value.has(`${row}:${column}`)
}

function hintTone(row: number, column: number): HintTone | null {
  return boardHints.value.get(`${row}:${column}`) ?? null
}

function cellAriaLabel(row: number, column: number): string {
  const base = `第 ${row + 1} 行第 ${column + 1} 列`
  const piece = game.value.board[row]?.[column]
  if (piece && isHangingPiece(row, column)) {
    const pieceLabel = labels[piece] ?? '棋子'
    return isOwn(piece)
      ? `${base}，我方${pieceLabel}无根，可被对方吃`
      : `${base}，可吃无根${pieceLabel}`
  }
  if (selected.value && captureHintsEnabled.value && isLegalTarget(row, column)) {
    if (piece) return `${base}，可吃${labels[piece] ?? '敌子'}`
  }
  return base
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

function placementMarkPath(row: number, column: number, side: 'left' | 'right') {
  const direction = side === 'left' ? -1 : 1
  const x = column + 0.5
  const y = row + 0.5
  const inner = x + direction * 0.12
  const outer = x + direction * 0.3
  return [
    `M${outer} ${y - 0.12}H${inner}V${y - 0.3}`,
    `M${outer} ${y + 0.12}H${inner}V${y + 0.3}`,
  ].join(' ')
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

    <div class="xiangqi-board-shell" aria-label="中国象棋棋盘">
      <div class="xiangqi-board-stage" :class="{ 'has-selection': selected }">
        <svg class="xiangqi-board-art" viewBox="0 0 9 10" preserveAspectRatio="none" aria-hidden="true">
          <g class="xiangqi-board-geometry">
            <rect
              class="xiangqi-board-boundary"
              :x="boardGeometry.firstX"
              :y="boardGeometry.firstY"
              :width="boardGeometry.lastX - boardGeometry.firstX"
              :height="boardGeometry.lastY - boardGeometry.firstY"
            />
            <path class="xiangqi-lattice-lines" :d="horizontalGridPath" />
            <path class="xiangqi-lattice-lines" :d="verticalGridPath" />
            <path class="xiangqi-palace-lines" :d="palaceGridPath" />
          </g>
          <g class="xiangqi-position-marks">
            <path
              v-for="mark in placementMarkSegments"
              :key="`${mark.row}-${mark.column}-${mark.side}`"
              class="xiangqi-position-mark"
              :data-position="`${mark.row}-${mark.column}`"
              :data-side="mark.side"
              :d="placementMarkPath(mark.row, mark.column, mark.side)"
            />
          </g>
          <g class="xiangqi-river-label" aria-hidden="true">
            <text x="2.75" y="5">楚 河</text>
            <text x="6.25" y="5">汉 界</text>
          </g>
        </svg>
        <template v-for="row in displayRows" :key="row">
          <button
            v-for="column in displayColumns"
            :key="`${row}-${column}`"
            type="button"
            class="xiangqi-cell"
            :disabled="snapshot.phase !== 'playing' || !isMyTurn || isReplaying || arcade.busy"
            :aria-pressed="selected?.row === row && selected?.column === column"
            :aria-label="cellAriaLabel(row, column)"
            :class="{
              selected: selected?.row === row && selected?.column === column,
              confirming: isPendingTarget(row, column),
              legal: !isReplaying && isLegalTarget(row, column),
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
            <span
              v-if="hintTone(row, column)"
              class="xiangqi-hint-dot"
              :class="`is-${hintTone(row, column)}`"
              aria-hidden="true"
            />
          </button>
        </template>
      </div>
    </div>

    <div class="xiangqi-actions">
      <button type="button" :disabled="!moveHistory.length" @click="openReplay()"><History :size="17" />对局复盘</button>
      <button type="button" :disabled="!moveHistory.length" @click="exportMoves"><Download :size="17" />导出记录</button>
      <UiButton v-if="snapshot.phase === 'playing'" variant="danger" compact @click="arcade.action('resign')"><Flag :size="17" />认输</UiButton>
    </div>

    <div v-if="showReplay" class="replay-backdrop" @click.self="showReplay = false">
      <section class="replay-panel" role="dialog" aria-modal="true" aria-label="象棋对局复盘">
        <header><div><small>走棋记录</small><strong>第 {{ replayStep }} / {{ moveHistory.length }} 手</strong></div><UiIconButton compact aria-label="关闭复盘" @click="showReplay = false"><X :size="20" /></UiIconButton></header>
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
.xiangqi-panel { display: grid; gap: 15px; justify-items: center; }.xiangqi-status { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px 14px; color: var(--muted); text-align: center; }.xiangqi-status strong { color: var(--accent); }.xiangqi-status .selection { color: color-mix(in srgb, var(--accent) 78%, var(--text)); font-weight: 800; }.xiangqi-status .check { color: var(--red); font-weight: 800; }
.captured-pieces { width: min(92vw, 610px); display: grid; grid-template-columns: 1fr 1fr; gap: 9px; }.captured-pieces > span { min-height: 38px; display: flex; flex-wrap: wrap; align-items: center; gap: 5px; border: 1px solid var(--line); border-radius: 10px; padding: 7px 10px; color: var(--muted); background: var(--surface-inset); }.captured-pieces b { margin-right: 5px; color: var(--text); }.captured-pieces i { width: 24px; height: 24px; display: grid; place-items: center; border-radius: 50%; color: var(--accent-contrast); background: var(--accent); font-family: serif; font-style: normal; font-weight: 900; }.captured-pieces em { font-style: normal; }
.xiangqi-board-shell {
  --board-padding: clamp(14px, 3vw, 20px);
  position: relative;
  isolation: isolate;
  width: min(100%, 610px);
  box-sizing: border-box;
  overflow: hidden;
  padding: var(--board-padding);
  border: 3px solid var(--game-board-frame, #74451f);
  border-radius: 15px;
  background-color: var(--game-board-surface, #d9aa65);
  background-image:
    linear-gradient(145deg, color-mix(in srgb, white 11%, transparent), transparent 34%, color-mix(in srgb, var(--game-board-frame, #74451f) 12%, transparent)),
    var(--game-board-texture, repeating-linear-gradient(2deg, rgba(255, 245, 205, .075) 0 2px, rgba(92, 49, 16, .04) 3px 7px));
  box-shadow:
    inset 0 0 0 3px var(--game-board-highlight, #e5bd75),
    inset 0 0 0 7px color-mix(in srgb, var(--game-board-frame, #74451f) 64%, transparent),
    inset 0 0 34px rgba(0, 0, 0, .23),
    0 18px 45px #0006,
    0 0 0 1px color-mix(in srgb, var(--accent) 24%, transparent);
}
.xiangqi-board-shell::before {
  content: '';
  position: absolute;
  z-index: 0;
  inset: 8px;
  border: 1px solid color-mix(in srgb, var(--game-board-highlight, #e5bd75) 48%, transparent);
  border-radius: 8px;
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--game-board-frame, #74451f) 42%, transparent);
  pointer-events: none;
}
.xiangqi-board-shell::after {
  content: '';
  position: absolute;
  z-index: 0;
  inset: 0;
  background:
    radial-gradient(ellipse at 50% -8%, color-mix(in srgb, white 10%, transparent), transparent 42%),
    linear-gradient(90deg, color-mix(in srgb, var(--game-board-frame, #74451f) 10%, transparent), transparent 10% 90%, color-mix(in srgb, var(--game-board-frame, #74451f) 10%, transparent));
  pointer-events: none;
}
.xiangqi-board-stage {
  position: relative;
  z-index: 1;
  isolation: isolate;
  width: 100%;
  aspect-ratio: 9 / 10;
  display: grid;
  grid-template-columns: repeat(9, minmax(0, 1fr));
  grid-template-rows: repeat(10, minmax(0, 1fr));
}
.xiangqi-board-art {
  position: absolute;
  z-index: 0;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
  pointer-events: none;
  filter: drop-shadow(0 1px color-mix(in srgb, white 14%, transparent));
}
.xiangqi-board-geometry > *,
.xiangqi-position-mark {
  fill: none;
  stroke: var(--game-board-line, #603b1d);
  stroke-width: 1.35;
  vector-effect: non-scaling-stroke;
  stroke-linecap: square;
  stroke-linejoin: miter;
  shape-rendering: geometricPrecision;
}
.xiangqi-board-boundary { stroke-width: 1.6; }
.xiangqi-position-mark { stroke-width: 1.35; }
.xiangqi-river-label text {
  fill: var(--game-board-label, #603b1d);
  font-family: "Songti SC", "STSong", serif;
  font-size: .4px;
  font-weight: 900;
  letter-spacing: .06px;
  text-anchor: middle;
  dominant-baseline: central;
  filter: drop-shadow(0 .02px color-mix(in srgb, white 28%, transparent));
}
.xiangqi-cell { position: relative; z-index: 2; min-width: 0; min-height: 0; appearance: none; -webkit-appearance: none; touch-action: manipulation; padding: 0; border: 0; border-radius: 0; background: transparent; }.xiangqi-cell:disabled { opacity: 1; }.xiangqi-cell:not(:disabled) { cursor: pointer; }.xiangqi-cell.selected::after, .xiangqi-cell.latest::after { content: ''; position: absolute; inset: 0; z-index: 4; border: 3px solid var(--accent); border-radius: 50%; box-shadow: 0 0 0 2px rgba(255, 235, 168, .35), 0 0 18px rgba(246, 196, 89, .62); }.xiangqi-cell.latest::after { inset: 10%; z-index: 1; border-width: 2px; border-color: #b94337; box-shadow: 0 0 0 2px rgba(255, 229, 186, .34); }.xiangqi-cell.last-from::before { content: ''; position: absolute; inset: 30%; z-index: 1; border-radius: 50%; background: rgba(178, 64, 50, .62); box-shadow: 0 0 0 3px rgba(255, 225, 177, .28); }
.xiangqi-hint-dot { position: absolute; z-index: 6; top: 50%; left: 50%; width: 13px; height: 13px; border-radius: 50%; color: #18875e; background: currentColor; box-shadow: 0 0 0 4px color-mix(in srgb, currentColor 18%, transparent); transform: translate(-50%, -50%); pointer-events: none; }.xiangqi-hint-dot.is-green { color: #18875e; }.xiangqi-hint-dot.is-red { color: #dc493f; }
.xiangqi-cell.confirming::after { content: ''; position: absolute; inset: 5%; z-index: 5; border: 3px solid var(--accent); border-radius: 50%; background: color-mix(in srgb, var(--accent) 16%, transparent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 22%, transparent), 0 0 20px color-mix(in srgb, var(--accent) 62%, transparent); pointer-events: none; }
.xiangqi-cell:focus-visible { border-radius: 50%; outline-offset: -3px; }
.xiangqi-piece { position: absolute; inset: 7%; z-index: 3; display: grid; place-items: center; border: 2px solid currentColor; border-radius: 50%; background: var(--game-piece-surface, radial-gradient(circle at 38% 30%, rgba(255, 248, 215, .92), transparent 27%), radial-gradient(circle, #efd398, #bd7d35 76%)); box-shadow: 0 3px 7px #0008, inset 0 0 0 2px var(--game-piece-rim, #edc77d), inset 0 -4px 8px rgba(0, 0, 0, .22); font-family: serif; font-size: clamp(15px, 4.3vw, 27px); line-height: 1; font-weight: 900; transition: transform .14s ease, box-shadow .14s ease, filter .14s ease; }.xiangqi-piece.red { color: #a92b25; }.xiangqi-piece.black { color: #242621; }.xiangqi-cell.selected .xiangqi-piece { transform: translateY(-3px) scale(1.06); filter: saturate(1.12) brightness(1.06); box-shadow: 0 7px 13px rgba(48, 24, 8, .62), 0 0 0 3px #f4cd68, 0 0 22px rgba(246, 196, 82, .78), inset 0 0 0 2px #f3d58d; }
.xiangqi-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }.xiangqi-actions > button:not(.ui-button--danger) { min-height: 42px; display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 10px; padding: 0 13px; color: var(--text); background: var(--surface); font-weight: 800; }.xiangqi-actions button:disabled { opacity: .4; }
.replay-backdrop { position: fixed; z-index: 80; inset: 0; display: grid; place-items: center; padding: 18px; background: var(--backdrop); }.replay-panel { width: min(92vw, 560px); max-height: min(82vh, 720px); display: grid; grid-template-rows: auto 1fr auto; gap: 12px; border: 1px solid var(--line); border-radius: 17px; padding: 17px; background: var(--surface-strong); box-shadow: var(--shadow); }.replay-panel header { display: flex; justify-content: space-between; align-items: center; }.replay-panel header > div { display: grid; }.replay-panel header small { color: var(--accent); }.move-list { min-height: 0; overflow: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }.move-list button { min-height: 42px; display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 8px; padding: 7px 9px; color: var(--text); background: var(--surface-inset); text-align: left; }.move-list button.active { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, var(--surface-inset)); }.move-list span { color: var(--muted); }.move-list em { color: var(--red); font-style: normal; font-size: 12px; }.replay-panel footer { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }.replay-panel footer button { min-height: 42px; display: flex; justify-content: center; align-items: center; gap: 5px; border: 1px solid var(--line); border-radius: 9px; color: var(--text); background: var(--surface-inset); }
@media (max-width: 600px) { .xiangqi-panel { gap: 10px; width: 100%; }.xiangqi-status { position: sticky; z-index: 7; top: max(6px, env(safe-area-inset-top)); width: 100%; border: 1px solid color-mix(in srgb, var(--accent) 28%, var(--line)); border-radius: 12px; padding: 9px 10px; background: color-mix(in srgb, var(--surface-elevated) 94%, transparent); box-shadow: 0 8px 24px rgba(0,0,0,.18); backdrop-filter: blur(14px); }.captured-pieces { width: 100%; grid-template-columns: 1fr 1fr; gap: 6px; }.captured-pieces > span { min-height: 34px; padding: 5px 8px; font-size: 11px; }.captured-pieces i { width: 21px; height: 21px; }.xiangqi-board-shell { --board-padding: clamp(9px, 3vw, 13px); width: 100%; border-width: 2px; border-radius: 13px; }.move-list { grid-template-columns: 1fr; }.replay-panel { width: 100%; max-height: 88dvh; }.xiangqi-piece { inset: 7%; font-size: clamp(14px, 5.1vw, 22px); }.xiangqi-actions { width: 100%; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }.xiangqi-actions > button, .xiangqi-actions > button:not(.ui-button--danger) { min-width: 0; justify-content: center; padding: 0 7px; font-size: 11px; } }
@media (orientation: landscape) and (min-width: 601px) and (max-width: 980px) and (max-height: 600px) {
  .xiangqi-panel { width: min(100%, 820px); grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: "status board" "captured board" "actions board"; align-items: start; justify-items: stretch; gap: 9px 14px; }
  .xiangqi-status { grid-area: status; align-self: end; border: 1px solid color-mix(in srgb, var(--accent) 28%, var(--line)); border-radius: 12px; padding: 9px 10px; background: color-mix(in srgb, var(--surface-elevated) 94%, transparent); }
  .captured-pieces { grid-area: captured; width: 100%; grid-template-columns: 1fr; gap: 6px; }
  .captured-pieces > span { min-height: 32px; padding: 4px 8px; font-size: 10px; }
  .captured-pieces i { width: 20px; height: 20px; }
  .xiangqi-board-shell { grid-area: board; --board-padding: 10px; width: min(42vw, calc((100svh - 78px) * .9)); min-width: 250px; max-width: 400px; border-width: 2px; border-radius: 12px; }
  .xiangqi-piece { inset: 6%; font-size: clamp(14px, 2.9vw, 21px); }
  .xiangqi-actions { grid-area: actions; width: 100%; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .xiangqi-actions > button, .xiangqi-actions > button:not(.ui-button--danger) { min-width: 0; min-height: 38px; justify-content: center; padding: 0 7px; font-size: 10px; }
  .xiangqi-actions .ui-button--danger { grid-column: 1 / -1; }
}
@media (max-width: 360px) { .captured-pieces { grid-template-columns: 1fr; }.xiangqi-piece { inset: 5%; font-size: clamp(13px, 5.2vw, 18px); }.xiangqi-actions { grid-template-columns: 1fr 1fr; }.xiangqi-actions .ui-button--danger { grid-column: 1 / -1; } }
</style>
