<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight, Download, Flag, History, X } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'

type ChessColor = 'white' | 'black'
type PromotionPiece = 'Q' | 'R' | 'B' | 'N'

interface ChessMove {
  number: number
  fullmoveNumber: number
  fromRow: number
  fromColumn: number
  toRow: number
  toColumn: number
  piece: string
  resultPiece: string
  captured: string | null
  color: ChessColor
  promotion: PromotionPiece | null
  castle: 'kingside' | 'queenside' | null
  enPassant: boolean
  gaveCheck: boolean
  notation: string
}

interface LegalMove {
  fromRow: number
  fromColumn: number
  toRow: number
  toColumn: number
  isCapture: boolean
  promotionRequired: boolean
  castle: 'kingside' | 'queenside' | null
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const selected = ref<{ row: number; column: number } | null>(null)
const pendingTarget = ref<{ row: number; column: number } | null>(null)
const pendingPromotion = ref<LegalMove | null>(null)
const showReplay = ref(false)
const replayStep = ref(0)

const game = computed(() => props.snapshot.game as {
  board: Array<Array<string | null>>
  turnPlayerId: string | null
  colors: Record<string, ChessColor>
  viewerColor: ChessColor
  lastMove: ChessMove | null
  moveHistory: ChessMove[]
  capturedPieces: Array<{ piece: string; capturedBy: ChessColor; moveNumber: number }>
  legalMoves: LegalMove[]
  whiteInCheck: boolean
  blackInCheck: boolean
  checkedColor: ChessColor | null
  halfmoveClock: number
  fullmoveNumber: number
})
const isMyTurn = computed(() => game.value.turnPlayerId === props.snapshot.self.id)
const canMove = computed(() => (
  props.snapshot.phase === 'playing'
  && props.snapshot.actions.canAct
  && isMyTurn.value
  && !showReplay.value
))
const moveHistory = computed(() => game.value.moveHistory ?? [])
const displayRows = computed(() => {
  const rows = Array.from({ length: 8 }, (_, index) => index)
  return game.value.viewerColor === 'black' ? rows.reverse() : rows
})
const displayColumns = computed(() => {
  const columns = Array.from({ length: 8 }, (_, index) => index)
  return game.value.viewerColor === 'black' ? columns.reverse() : columns
})
const selectedLegalMoves = computed(() => selected.value
  ? (game.value.legalMoves ?? []).filter(
      (move) => move.fromRow === selected.value?.row
        && move.fromColumn === selected.value?.column,
    )
  : [])
const displayBoard = computed(() => {
  if (!showReplay.value) return game.value.board
  const board = makeInitialBoard()
  for (const move of moveHistory.value.slice(0, replayStep.value)) {
    if (move.enPassant) board[move.fromRow][move.toColumn] = null
    board[move.toRow][move.toColumn] = move.resultPiece
    board[move.fromRow][move.fromColumn] = null
    if (move.castle) {
      const rookSource = move.toColumn === 6 ? 7 : 0
      const rookTarget = move.toColumn === 6 ? 5 : 3
      board[move.toRow][rookTarget] = board[move.toRow][rookSource]
      board[move.toRow][rookSource] = null
    }
  }
  return board
})
const replayMove = computed(
  () => replayStep.value > 0 ? moveHistory.value[replayStep.value - 1] : null,
)
const capturedWhite = computed(() => (
  (game.value.capturedPieces ?? []).filter((item) => item.piece.startsWith('w'))
))
const capturedBlack = computed(() => (
  (game.value.capturedPieces ?? []).filter((item) => item.piece.startsWith('b'))
))
const checkedText = computed(() => game.value.checkedColor
  ? `${game.value.checkedColor === 'white' ? '白方' : '黑方'}被将军！`
  : '')
const selectedPieceName = computed(() => {
  if (!selected.value) return ''
  const piece = game.value.board[selected.value.row]?.[selected.value.column]
  return pieceNames[piece ?? ''] ?? ''
})

const pieceGlyphs: Record<string, string> = {
  wK: '♔', wQ: '♕', wR: '♖', wB: '♗', wN: '♘', wP: '♙',
  bK: '♚', bQ: '♛', bR: '♜', bB: '♝', bN: '♞', bP: '♟',
}
const pieceNames: Record<string, string> = {
  wK: '白王', wQ: '白后', wR: '白车', wB: '白象', wN: '白马', wP: '白兵',
  bK: '黑王', bQ: '黑后', bR: '黑车', bB: '黑象', bN: '黑马', bP: '黑兵',
}
const promotionChoices: Array<{ kind: PromotionPiece; label: string }> = [
  { kind: 'Q', label: '后' },
  { kind: 'R', label: '车' },
  { kind: 'B', label: '象' },
  { kind: 'N', label: '马' },
]

watch(() => props.snapshot.roundNumber, clearInteraction)
watch(() => game.value.lastMove?.number, () => {
  selected.value = null
  pendingTarget.value = null
  pendingPromotion.value = null
})

function makeInitialBoard(): Array<Array<string | null>> {
  const board = Array.from({ length: 8 }, () => Array<string | null>(8).fill(null))
  const backRank = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
  board[0] = backRank.map((piece) => `b${piece}`)
  board[1] = Array(8).fill('bP')
  board[6] = Array(8).fill('wP')
  board[7] = backRank.map((piece) => `w${piece}`)
  return board
}

function clearInteraction() {
  selected.value = null
  pendingTarget.value = null
  pendingPromotion.value = null
  showReplay.value = false
  replayStep.value = 0
}

function ownPrefix(): string {
  return game.value.viewerColor === 'white' ? 'w' : 'b'
}

function isOwn(piece: string | null | undefined): boolean {
  return Boolean(piece?.startsWith(ownPrefix()))
}

function legalMoveAt(row: number, column: number): LegalMove | undefined {
  return selectedLegalMoves.value.find(
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
  if (!canMove.value || arcade.busy || pendingPromotion.value) return
  const piece = game.value.board[row]?.[column] ?? null
  if (!selected.value) {
    if (isOwn(piece)) selected.value = { row, column }
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
  const legalMove = legalMoveAt(row, column)
  if (!legalMove) return
  if (legalMove.promotionRequired) {
    pendingPromotion.value = legalMove
    pendingTarget.value = null
    return
  }
  if (usesTouchConfirmation(event) && !isPendingTarget(row, column)) {
    pendingTarget.value = { row, column }
    return
  }
  submitMove(legalMove)
}

function submitMove(move: LegalMove, promotion?: PromotionPiece) {
  selected.value = null
  pendingTarget.value = null
  pendingPromotion.value = null
  void arcade.action('move', {
    fromRow: move.fromRow,
    fromColumn: move.fromColumn,
    toRow: move.toRow,
    toColumn: move.toColumn,
    ...(promotion ? { promotion } : {}),
  })
}

function completePromotion(promotion: PromotionPiece) {
  if (pendingPromotion.value) submitMove(pendingPromotion.value, promotion)
}

function openReplay(step = moveHistory.value.length) {
  replayStep.value = step
  selected.value = null
  pendingTarget.value = null
  pendingPromotion.value = null
  showReplay.value = true
}

function fileName(column: number): string {
  return 'abcdefgh'[column] ?? ''
}

function cellAriaLabel(row: number, column: number): string {
  const square = `${fileName(column)}${8 - row}`
  const piece = displayBoard.value[row]?.[column]
  const legalMove = legalMoveAt(row, column)
  if (legalMove?.isCapture) return `${square}，可吃子`
  if (legalMove) return `${square}，可以落子`
  return piece ? `${square}，${pieceNames[piece]}` : `${square}，空格`
}

function isLightSquare(row: number, column: number): boolean {
  return (row + column) % 2 === 0
}

function isCheckedKing(piece: string | null): boolean {
  if (!piece || piece[1] !== 'K') return false
  return (piece.startsWith('w') ? 'white' : 'black') === game.value.checkedColor
}

function moveResult(): string {
  if (props.snapshot.phase !== 'finished') return '*'
  if (props.snapshot.winner === 'draw') return '1/2-1/2'
  return props.snapshot.winner === 'white' ? '1-0' : '0-1'
}

function exportMoves() {
  const whitePlayer = props.snapshot.players.find(
    (player) => game.value.colors[player.id] === 'white',
  )
  const blackPlayer = props.snapshot.players.find(
    (player) => game.value.colors[player.id] === 'black',
  )
  const turns: string[] = []
  for (let index = 0; index < moveHistory.value.length; index += 2) {
    const white = moveHistory.value[index]
    const black = moveHistory.value[index + 1]
    turns.push(`${Math.floor(index / 2) + 1}. ${white?.notation ?? ''}${black ? ` ${black.notation}` : ''}`)
  }
  const content = [
    '[Event "游戏大厅国际象棋"]',
    `[Site "${window.location.host}"]`,
    `[White "${whitePlayer?.name ?? '白方'}"]`,
    `[Black "${blackPlayer?.name ?? '黑方'}"]`,
    `[Result "${moveResult()}"]`,
    '',
    `${turns.join(' ')} ${moveResult()}`,
    '',
  ].join('\n')
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `国际象棋-${props.snapshot.roomCode}.pgn`
  link.click()
  URL.revokeObjectURL(link.href)
}
</script>

<template>
  <section class="chess-panel">
    <div class="chess-status" role="status">
      <strong>{{ showReplay ? `复盘第 ${replayStep} / ${moveHistory.length} 手` : canMove ? '轮到你走棋' : isMyTurn ? '正在观战' : '等待对手走棋' }}</strong>
      <span v-if="snapshot.viewer?.mode !== 'spectator'">你执{{ game.viewerColor === 'white' ? '白' : '黑' }}</span>
      <span v-if="selected && !showReplay" class="selection">已选择{{ selectedPieceName }}，请选择目标格</span>
      <span v-if="checkedText && !showReplay" class="check">{{ checkedText }}</span>
    </div>

    <div class="captured-pieces">
      <span><b>白方损失</b><i v-for="(item, index) in capturedWhite" :key="index">{{ pieceGlyphs[item.piece] }}</i><em v-if="!capturedWhite.length">无</em></span>
      <span><b>黑方损失</b><i v-for="(item, index) in capturedBlack" :key="index">{{ pieceGlyphs[item.piece] }}</i><em v-if="!capturedBlack.length">无</em></span>
    </div>

    <div class="chess-board" aria-label="国际象棋棋盘">
      <template v-for="row in displayRows" :key="row">
        <button
          v-for="column in displayColumns"
          :key="`${row}-${column}`"
          type="button"
          class="chess-cell"
          :class="{
            light: isLightSquare(row, column),
            dark: !isLightSquare(row, column),
            selected: selected?.row === row && selected?.column === column,
            legal: !showReplay && Boolean(legalMoveAt(row, column)),
            capture: !showReplay && legalMoveAt(row, column)?.isCapture,
            confirming: isPendingTarget(row, column),
            latest: (showReplay ? replayMove : game.lastMove)?.toRow === row && (showReplay ? replayMove : game.lastMove)?.toColumn === column,
            'last-from': (showReplay ? replayMove : game.lastMove)?.fromRow === row && (showReplay ? replayMove : game.lastMove)?.fromColumn === column,
            checked: !showReplay && isCheckedKing(displayBoard[row][column]),
          }"
          :disabled="!canMove || arcade.busy || Boolean(pendingPromotion)"
          :aria-label="cellAriaLabel(row, column)"
          :aria-pressed="selected?.row === row && selected?.column === column"
          :data-square="`${fileName(column)}${8 - row}`"
          @click="choose(row, column, $event)"
        >
          <span
            v-if="displayBoard[row][column]"
            class="chess-piece"
            :class="displayBoard[row][column]?.startsWith('w') ? 'white' : 'black'"
          >{{ pieceGlyphs[displayBoard[row][column] ?? ''] }}</span>
          <small v-if="row === displayRows[7]" class="file-label">{{ fileName(column) }}</small>
          <small v-if="column === displayColumns[0]" class="rank-label">{{ 8 - row }}</small>
        </button>
      </template>
    </div>

    <div class="chess-actions">
      <button type="button" :disabled="!moveHistory.length" @click="openReplay()"><History :size="17" />对局复盘</button>
      <button type="button" :disabled="!moveHistory.length" @click="exportMoves"><Download :size="17" />导出 PGN</button>
      <button v-if="snapshot.phase === 'playing' && snapshot.actions.canAct" type="button" class="arcade-danger-button" @click="arcade.action('resign')"><Flag :size="17" />认输</button>
    </div>

    <div v-if="pendingPromotion" class="promotion-backdrop" @click.self="pendingPromotion = null">
      <section class="promotion-panel" role="dialog" aria-modal="true" aria-label="选择升变棋子">
        <header><div><small>兵抵达底线</small><strong>选择升变棋子</strong></div><button type="button" aria-label="取消升变" @click="pendingPromotion = null"><X :size="20" /></button></header>
        <div>
          <button v-for="choice in promotionChoices" :key="choice.kind" type="button" @click="completePromotion(choice.kind)">
            <span :class="game.viewerColor">{{ pieceGlyphs[`${game.viewerColor === 'white' ? 'w' : 'b'}${choice.kind}`] }}</span>
            <strong>{{ choice.label }}</strong>
          </button>
        </div>
      </section>
    </div>

    <div v-if="showReplay" class="replay-backdrop" @click.self="showReplay = false">
      <section class="replay-panel" role="dialog" aria-modal="true" aria-label="国际象棋对局复盘">
        <header><div><small>标准棋谱</small><strong>第 {{ replayStep }} / {{ moveHistory.length }} 手</strong></div><button type="button" aria-label="关闭复盘" @click="showReplay = false"><X :size="20" /></button></header>
        <div class="move-list">
          <button type="button" :class="{ active: replayStep === 0 }" @click="replayStep = 0">开局</button>
          <button v-for="move in moveHistory" :key="move.number" type="button" :class="{ active: replayStep === move.number }" @click="replayStep = move.number">
            <span>{{ move.fullmoveNumber }}{{ move.color === 'white' ? '.' : '...' }}</span><b>{{ move.notation }}</b><em v-if="move.gaveCheck">将军</em>
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
.chess-panel { display: grid; gap: 14px; justify-items: center; width: 100%; }
.chess-status { min-height: 28px; display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 7px 14px; color: var(--muted); text-align: center; }.chess-status strong { color: var(--gold); }.chess-status .selection { color: color-mix(in srgb, var(--gold) 78%, white); font-weight: 800; }.chess-status .check { border-radius: 999px; padding: 4px 8px; color: #ffd6d2; background: #a83c38; font-weight: 900; }
.captured-pieces { width: min(100%, 600px); display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }.captured-pieces > span { min-height: 38px; display: flex; flex-wrap: wrap; align-items: center; gap: 3px; border: 1px solid var(--line); border-radius: 10px; padding: 6px 9px; color: var(--muted); background: color-mix(in srgb, var(--surface-inset) 88%, transparent); }.captured-pieces b { margin-right: 5px; color: var(--text); font-size: 10px; }.captured-pieces i { color: var(--text); font-family: "Times New Roman", "Noto Sans Symbols 2", serif; font-size: 21px; font-style: normal; line-height: 1; }.captured-pieces em { font-size: 9px; font-style: normal; }
.chess-board { --light-square: color-mix(in srgb, var(--game-board-surface, #d7c6a6) 67%, #f4ead7); --dark-square: color-mix(in srgb, var(--game-board-frame, #65523c) 72%, var(--game-board-surface, #a88b68)); position: relative; isolation: isolate; width: min(100%, 600px); aspect-ratio: 1; display: grid; grid-template-columns: repeat(8, minmax(0, 1fr)); overflow: hidden; border: clamp(6px, 1.5vw, 11px) solid var(--game-board-frame, #554331); border-radius: 14px; background: var(--game-board-frame, #554331); box-shadow: inset 0 0 0 2px var(--game-board-highlight, rgba(255,255,255,.25)), 0 20px 50px rgba(0,0,0,.4), 0 3px 0 color-mix(in srgb, var(--game-board-frame, #554331) 70%, black); }
.chess-board::after { position: absolute; z-index: 5; inset: 0; border: 1px solid color-mix(in srgb, var(--game-board-highlight, #fff) 48%, transparent); content: ''; pointer-events: none; }
.chess-cell { position: relative; min-width: 0; min-height: 0; appearance: none; -webkit-appearance: none; display: grid; place-items: center; border: 0; padding: 0; touch-action: manipulation; cursor: pointer; }.chess-cell.light { background: var(--light-square); }.chess-cell.dark { background: var(--dark-square); }.chess-cell:disabled { opacity: 1; cursor: default; }
.chess-cell::before,.chess-cell::after { position: absolute; content: ''; pointer-events: none; }.chess-cell.last-from::after { z-index: 1; inset: 0; background: color-mix(in srgb, #f7cf5c 32%, transparent); }.chess-cell.latest::after { z-index: 1; inset: 0; background: color-mix(in srgb, #f7cf5c 42%, transparent); box-shadow: inset 0 0 0 3px color-mix(in srgb, #fff1a8 64%, transparent); }.chess-cell.selected::after { z-index: 4; inset: 4px; border: 3px solid var(--gold); border-radius: 8px; background: color-mix(in srgb, var(--gold) 18%, transparent); box-shadow: inset 0 0 15px color-mix(in srgb, var(--gold) 25%, transparent), 0 0 16px color-mix(in srgb, var(--gold) 48%, transparent); }.chess-cell.legal::before { z-index: 4; width: 18%; aspect-ratio: 1; border-radius: 50%; background: #175e47b8; box-shadow: 0 0 0 5px rgba(23,94,71,.12); }.chess-cell.legal.capture::before { width: 78%; border: 4px solid #17694f; background: transparent; box-shadow: inset 0 0 0 3px rgba(229,255,243,.16); }.chess-cell.confirming::after { z-index: 5; inset: 3px; border: 3px solid #ffe48b; border-radius: 8px; background: rgba(255,220,104,.18); box-shadow: 0 0 18px rgba(255,220,104,.72); }.chess-cell.checked { box-shadow: inset 0 0 0 4px #d94742, inset 0 0 24px rgba(189,39,35,.7); }
.chess-piece { position: relative; z-index: 3; display: block; font-family: "Times New Roman", "Noto Sans Symbols 2", "Arial Unicode MS", serif; font-size: clamp(32px, 8.6vw, 64px); line-height: .9; user-select: none; transform: translateY(-1px); transition: transform .14s ease, filter .14s ease; }.chess-piece.white { color: #fff8df; text-shadow: 0 1px #4a3d31, 1px 0 #4a3d31, 0 -1px #4a3d31, -1px 0 #4a3d31, 0 3px 4px rgba(0,0,0,.45); }.chess-piece.black { color: #262724; text-shadow: 0 1px rgba(255,247,216,.72), 1px 0 rgba(255,247,216,.45), 0 3px 4px rgba(0,0,0,.42); }.chess-cell.selected .chess-piece { transform: translateY(-4px) scale(1.07); filter: drop-shadow(0 7px 6px rgba(0,0,0,.38)); }
.file-label,.rank-label { position: absolute; z-index: 6; color: color-mix(in srgb, var(--game-board-label, #32291f) 86%, transparent); font-size: clamp(7px, 1.8vw, 10px); font-weight: 900; line-height: 1; pointer-events: none; }.file-label { right: 3px; bottom: 2px; }.rank-label { top: 3px; left: 3px; }.chess-cell.dark .file-label,.chess-cell.dark .rank-label { color: color-mix(in srgb, var(--light-square) 82%, transparent); }
.chess-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }.chess-actions > button:not(.arcade-danger-button) { min-height: 42px; display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 10px; padding: 0 13px; color: var(--text); background: var(--surface); font-weight: 800; }.chess-actions button:disabled { opacity: .4; }
.promotion-backdrop,.replay-backdrop { position: fixed; z-index: 80; inset: 0; display: grid; place-items: center; padding: 18px; background: #020b0bd4; backdrop-filter: blur(7px); }.promotion-panel { width: min(92vw, 430px); display: grid; gap: 16px; border: 1px solid color-mix(in srgb, var(--gold) 40%, var(--line)); border-radius: 18px; padding: 18px; background: var(--surface-strong); box-shadow: 0 24px 70px #000a; }.promotion-panel header,.replay-panel header { display: flex; justify-content: space-between; align-items: center; }.promotion-panel header > div,.replay-panel header > div { display: grid; }.promotion-panel header small,.replay-panel header small { color: var(--gold); }.promotion-panel header button,.replay-panel header button { border: 0; color: var(--muted); background: transparent; }.promotion-panel > div { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }.promotion-panel > div button { min-width: 0; min-height: 96px; display: grid; place-items: center; gap: 3px; border: 1px solid var(--line); border-radius: 12px; color: var(--text); background: var(--surface-inset); }.promotion-panel > div span { font-family: "Times New Roman", serif; font-size: 48px; line-height: 1; }.promotion-panel > div span.white { color: #fff8df; text-shadow: 0 1px #4a3d31, 1px 0 #4a3d31, 0 -1px #4a3d31, -1px 0 #4a3d31; }.promotion-panel > div span.black { color: #222; text-shadow: 0 1px #ddd; }
.replay-panel { width: min(92vw, 560px); max-height: min(82vh, 720px); display: grid; grid-template-rows: auto 1fr auto; gap: 12px; border: 1px solid var(--line); border-radius: 17px; padding: 17px; background: var(--surface-strong); box-shadow: 0 24px 70px #000a; }.move-list { min-height: 0; overflow: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }.move-list button { min-height: 42px; display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 7px; border: 1px solid var(--line); border-radius: 8px; padding: 7px 9px; color: var(--text); background: rgba(0,0,0,.11); text-align: left; }.move-list button.active { border-color: var(--gold); background: color-mix(in srgb, var(--gold) 12%, transparent); }.move-list span { color: var(--muted); }.move-list b { font-family: ui-monospace, monospace; }.move-list em { color: #ff8d86; font-style: normal; font-size: 10px; }.replay-panel footer { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }.replay-panel footer button { min-height: 42px; display: flex; justify-content: center; align-items: center; gap: 5px; border: 1px solid var(--line); border-radius: 9px; color: var(--text); background: rgba(0,0,0,.14); }
@media (hover: hover) { .chess-cell:not(:disabled):hover .chess-piece { transform: translateY(-4px) scale(1.05); }.promotion-panel > div button:hover { border-color: var(--gold); transform: translateY(-2px); } }
@media (max-width: 600px) { .chess-panel { gap: 9px; }.chess-status { position: sticky; z-index: 7; top: max(6px, env(safe-area-inset-top)); width: 100%; border: 1px solid color-mix(in srgb, var(--gold) 28%, var(--line)); border-radius: 12px; padding: 8px 9px; background: color-mix(in srgb, var(--surface-elevated) 94%, transparent); box-shadow: 0 8px 24px rgba(0,0,0,.18); backdrop-filter: blur(14px); }.captured-pieces { gap: 5px; }.captured-pieces > span { min-height: 31px; padding: 4px 6px; }.captured-pieces b { font-size: 8px; }.captured-pieces i { font-size: 17px; }.chess-board { width: min(100%, calc(100dvh - 245px)); min-width: min(100%, 292px); border-width: 6px; border-radius: 10px; }.chess-piece { font-size: clamp(29px, 10.6vw, 51px); }.chess-actions { width: 100%; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }.chess-actions > button,.chess-actions > button:not(.arcade-danger-button) { min-width: 0; justify-content: center; padding: 0 6px; font-size: 10px; }.move-list { grid-template-columns: 1fr; }.replay-panel { width: 100%; max-height: 88dvh; } }
@media (orientation: landscape) and (min-width: 601px) and (max-width: 980px) and (max-height: 600px) { .chess-panel { width: min(100%, 850px); grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: "status board" "captured board" "actions board"; align-items: start; justify-items: stretch; gap: 9px 14px; }.chess-status { grid-area: status; align-self: end; border: 1px solid color-mix(in srgb, var(--gold) 28%, var(--line)); border-radius: 12px; padding: 9px 10px; background: color-mix(in srgb, var(--surface-elevated) 94%, transparent); }.captured-pieces { grid-area: captured; width: 100%; grid-template-columns: 1fr; gap: 6px; }.chess-board { grid-area: board; width: min(48vw, calc(100dvh - 76px)); min-width: 300px; max-width: 500px; }.chess-actions { grid-area: actions; width: 100%; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }.chess-actions .arcade-danger-button { grid-column: 1 / -1; } }
</style>
