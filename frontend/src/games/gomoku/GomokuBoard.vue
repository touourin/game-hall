<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Flag, Pause } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import UiButton from '../../components/ui/UiButton.vue'
import IntersectionBoard from '../shared/IntersectionBoard.vue'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const ruleNotice = ref('')
const pendingMove = ref<{ row: number; column: number } | null>(null)

const game = computed(() => props.snapshot.game as {
  board: number[][]
  turnPlayerId: string | null
  lastMove: {
    row?: number
    column?: number
    stone?: number
    pass?: boolean
    seat?: number
  } | null
  colors: Record<string, 'black' | 'white'>
  winRule: 'freestyle' | 'exact_five' | 'renju'
  forbiddenPoints: Array<{ row: number; column: number; reason: string }>
  openingMove: { row: number; column: number } | null
  consecutivePasses: number
  swap2: {
    enabled: boolean
    stage:
      | 'place_three'
      | 'second_choice'
      | 'place_two'
      | 'first_choice'
      | null
    actorPlayerId: string | null
    initialPlayerId: string
    expectedColor: 'black' | 'white' | null
    resolved: boolean
  }
})
const isMyTurn = computed(
  () => game.value.turnPlayerId === props.snapshot.self.id,
)
const isRenju = computed(() => game.value.winRule === 'renju')
const isBlack = computed(
  () => game.value.colors[props.snapshot.self.id] === 'black',
)
const swapStage = computed(() => game.value.swap2.stage)
const isSwapChoice = computed(() =>
  ['second_choice', 'first_choice'].includes(swapStage.value ?? ''),
)
const canPlace = computed(
  () => isMyTurn.value && !isSwapChoice.value && props.snapshot.phase === 'playing',
)
const forbiddenReasons = computed(
  () => new Map(
    game.value.forbiddenPoints.map(
      ({ row, column, reason }) => [`${row}:${column}`, reason],
    ),
  ),
)
const previewColor = computed<'black' | 'white'>(() =>
  game.value.swap2.expectedColor ??
  game.value.colors[props.snapshot.self.id] ??
  'black',
)
const pendingMoveLabel = computed(() => {
  if (!pendingMove.value) {
    return '鼠标悬停可预览落子；触屏轻点一次预览，再点一次确认'
  }
  return `已预览第 ${pendingMove.value.row + 1} 行第 ${pendingMove.value.column + 1} 列，再轻点一次确认落子`
})

const turnPrompt = computed(() => {
  if (swapStage.value === 'place_three') {
    return isMyTurn.value ? '请摆放开局的两黑一白' : '对手正在摆放开局棋子'
  }
  if (swapStage.value === 'place_two') {
    return isMyTurn.value ? '请再摆放一白一黑' : '对手选择再摆两子'
  }
  if (isSwapChoice.value) {
    return isMyTurn.value ? '请选择执黑或执白' : '等待对手选择颜色'
  }
  return isMyTurn.value ? '轮到你落子' : '等待对手落子'
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

function forbiddenReason(row: number, column: number) {
  return forbiddenReasons.value.get(`${row}:${column}`) ?? ''
}

function isOpeningMove(row: number, column: number) {
  return (
    game.value.openingMove?.row === row &&
    game.value.openingMove?.column === column
  )
}

function isPendingMove(row: number, column: number) {
  return pendingMove.value?.row === row && pendingMove.value?.column === column
}

function isStarPoint(row: number, column: number) {
  return [
    [3, 3], [3, 11], [7, 7], [11, 3], [11, 11],
  ].some(([starRow, starColumn]) => starRow === row && starColumn === column)
}

function pointCanPreview(row: number, column: number, cell: number) {
  if (!canPlace.value || cell !== 0 || arcade.busy) return false
  if (forbiddenReason(row, column)) return false
  return !game.value.openingMove || isOpeningMove(row, column)
}

function usesTouchConfirmation(event: MouseEvent) {
  return ['touch', 'pen'].includes((event as PointerEvent).pointerType ?? '')
}

function place(row: number, column: number, event: MouseEvent) {
  if (!canPlace.value || game.value.board[row]?.[column]) return
  const reason = forbiddenReason(row, column)
  if (reason) {
    pendingMove.value = null
    ruleNotice.value = `这里是黑方${reason}禁手，不能落子`
    return
  }
  if (game.value.openingMove && !isOpeningMove(row, column)) {
    pendingMove.value = null
    ruleNotice.value = '有禁手连珠的黑方首手必须落在棋盘中心的天元'
    return
  }
  if (usesTouchConfirmation(event) && !isPendingMove(row, column)) {
    pendingMove.value = { row, column }
    ruleNotice.value = ''
    return
  }
  pendingMove.value = null
  ruleNotice.value = ''
  void arcade.action('place', { row, column })
}

function chooseSwap2(choice: 'black' | 'white' | 'add') {
  if (!isMyTurn.value) return
  void arcade.action('swap2_choose', { choice })
}

function pass() {
  if (!isMyTurn.value || swapStage.value !== null) return
  void arcade.action('pass')
}

</script>

<template>
  <section class="board-game-panel">
    <div class="turn-banner" :class="{ active: isMyTurn }">
      {{ turnPrompt }}
      <small v-if="game.swap2.resolved">你执{{ game.colors[snapshot.self.id] === 'black' ? '黑' : '白' }}</small>
      <small v-else>Swap2 开局中，双方颜色尚未最终确定</small>
      <small v-if="game.swap2.expectedColor">本次请摆放{{ game.swap2.expectedColor === 'black' ? '黑子' : '白子' }}</small>
      <small v-if="isRenju">有禁手连珠 · 黑方禁三三、四四和长连</small>
    </div>
    <section v-if="isSwapChoice" class="swap2-choice-panel">
      <template v-if="isMyTurn">
        <strong>{{ swapStage === 'second_choice' ? '你可以直接选色，或再摆两子' : '请根据五颗开局棋选择颜色' }}</strong>
        <div>
          <button type="button" @click="chooseSwap2('white')">执白</button>
          <button type="button" @click="chooseSwap2('black')">执黑</button>
          <button v-if="swapStage === 'second_choice'" type="button" @click="chooseSwap2('add')">再摆两子</button>
        </div>
      </template>
      <span v-else>对手正在做 Swap2 选择</span>
    </section>
    <p v-if="game.lastMove?.pass && snapshot.phase === 'playing'" class="gomoku-pass-notice">
      上一位玩家已停一手，你若也停一手则本局和棋
    </p>
    <p v-if="ruleNotice" class="gomoku-rule-notice" role="status">{{ ruleNotice }}</p>
    <IntersectionBoard
      :size="game.board.length"
      class="gomoku-board"
      :class="{ 'renju-board': isRenju }"
      aria-label="十五路五子棋棋盘"
    >
      <template v-for="(row, rowIndex) in game.board" :key="rowIndex">
        <button
          v-for="(cell, columnIndex) in row"
          :key="`${rowIndex}-${columnIndex}`"
          type="button"
          class="board-point"
          :class="{
            forbidden: Boolean(forbiddenReason(rowIndex, columnIndex)),
            opening: isOpeningMove(rowIndex, columnIndex),
            star: isStarPoint(rowIndex, columnIndex),
            previewing: isPendingMove(rowIndex, columnIndex),
          }"
          :disabled="!canPlace || cell !== 0 || arcade.busy"
          :aria-pressed="isPendingMove(rowIndex, columnIndex)"
          :aria-label="forbiddenReason(rowIndex, columnIndex)
            ? `第 ${rowIndex + 1} 行第 ${columnIndex + 1} 列，黑方${forbiddenReason(rowIndex, columnIndex)}禁手`
            : `${isPendingMove(rowIndex, columnIndex) ? '已预览，' : ''}第 ${rowIndex + 1} 行第 ${columnIndex + 1} 列`"
          @click="place(rowIndex, columnIndex, $event)"
        >
          <span
            v-if="!cell && forbiddenReason(rowIndex, columnIndex)"
            class="forbidden-mark"
            aria-hidden="true"
          >×</span>
          <span
            v-else-if="!cell && isOpeningMove(rowIndex, columnIndex)"
            class="opening-mark"
            aria-hidden="true"
          />
          <span
            v-if="!cell && pointCanPreview(rowIndex, columnIndex, cell)"
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
    </IntersectionBoard>
    <p v-if="canPlace" class="gomoku-board-hint" aria-live="polite">
      {{ pendingMoveLabel }}
    </p>
    <div v-if="isRenju && isBlack && snapshot.phase === 'playing'" class="renju-legend">
      <span><i class="forbidden-sample">×</i> 禁手点</span>
      <span v-if="game.openingMove"><i class="opening-sample" /> 首手天元</span>
      <small>点击禁手点可查看原因，服务器也会再次校验</small>
    </div>
    <div v-if="snapshot.phase === 'playing'" class="gomoku-game-actions">
      <button
        v-if="swapStage === null"
        type="button"
        class="gomoku-pass-button"
        :disabled="!isMyTurn || arcade.busy"
        @click="pass"
      >
        <Pause :size="17" />停一手
      </button>
      <UiButton
        variant="danger"
        compact
        @click="arcade.action('resign')"
      >
        <Flag :size="17" />认输
      </UiButton>
    </div>
  </section>
</template>

<style scoped>
.board-game-panel { min-width: 0; display: grid; gap: 16px; justify-items: center; }
.turn-banner { color: var(--muted); text-align: center; font-weight: 700; }
.turn-banner.active { color: var(--gold); }
.turn-banner small { display: block; margin-top: 3px; font-weight: 500; }
.swap2-choice-panel { width: min(100%, 650px); display: grid; gap: 10px; border: 1px solid color-mix(in srgb, var(--gold) 42%, var(--line)); border-radius: 13px; padding: 13px; text-align: center; background: color-mix(in srgb, var(--gold) 7%, rgba(0, 0, 0, .14)); }
.swap2-choice-panel > div { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.swap2-choice-panel button { min-height: 42px; border: 1px solid color-mix(in srgb, var(--gold) 35%, var(--line)); border-radius: 10px; color: var(--gold); background: rgba(0, 0, 0, .16); font-weight: 850; }
.gomoku-pass-notice { width: min(100%, 650px); margin: 0; color: var(--gold); text-align: center; }
.gomoku-rule-notice { width: min(100%, 650px); margin: 0; border: 1px solid rgba(216, 91, 91, .42); border-radius: 11px; padding: 9px 12px; color: #f1b0b0; background: rgba(112, 35, 39, .18); text-align: center; }
.gomoku-board {
  --board-max-width: 650px;
  --board-padding: 14px;
}
.board-point {
  position: relative;
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
}
.board-point:disabled { opacity: 1; }
.board-point:not(:disabled) { cursor: crosshair; }
.board-point:focus-visible { border-radius: 50%; outline-offset: -3px; }
.board-point.star::before { content: ''; position: absolute; z-index: 1; top: 50%; left: 50%; width: clamp(4px, 18%, 7px); aspect-ratio: 1; border-radius: 50%; background: var(--game-board-line, #5f3b1c); box-shadow: 0 0 0 1px rgba(0, 0, 0, .22); transform: translate(-50%, -50%); }
.board-point.forbidden:not(:disabled) { cursor: help; }
.forbidden-mark { position: absolute; inset: 5%; z-index: 3; display: grid; place-items: center; border: 1px solid rgba(145, 24, 24, .62); border-radius: 50%; color: #961c1c; background: rgba(255, 220, 200, .34); font-size: clamp(12px, 2.1vw, 22px); font-weight: 950; line-height: 1; }
.opening-mark { position: absolute; inset: 25%; z-index: 2; border: 2px solid rgba(107, 57, 15, .72); border-radius: 50%; background: rgba(255, 219, 121, .3); box-shadow: 0 0 0 3px rgba(255, 226, 153, .22); }
.stone-preview {
  pointer-events: none;
  position: absolute;
  inset: 8%;
  z-index: 4;
  border-radius: 50%;
  opacity: 0;
  transform: scale(.82);
  transition: opacity .12s ease, transform .12s ease;
  box-shadow: inset 2px 2px 3px rgba(255, 255, 255, .14), inset -3px -4px 5px rgba(0, 0, 0, .38), 0 4px 8px rgba(35, 20, 9, .4);
}
.stone-preview.black { background: var(--game-black-stone, radial-gradient(circle at 35% 30%, #666, #090909 68%)); }
.stone-preview.white { border: 1px solid var(--game-white-stone-border, rgba(89, 68, 42, .25)); background: var(--game-white-stone, radial-gradient(circle at 35% 30%, #fff, #d8d2c5 70%)); }
.board-point:not(:disabled):hover .stone-preview,
.stone-preview.active { opacity: .5; transform: scale(1); }
.stone-preview.active { outline: 2px solid rgba(255, 245, 197, .78); outline-offset: 2px; }
.stone {
  position: absolute;
  inset: 8%;
  z-index: 2;
  border-radius: 50%;
  box-shadow: inset 2px 2px 3px rgba(255, 255, 255, .14), inset -3px -4px 5px rgba(0, 0, 0, .42), 0 1px 1px rgba(255, 232, 177, .15), 0 4px 7px rgba(28, 15, 5, .48);
}
.stone.black { background: var(--game-black-stone, radial-gradient(circle at 35% 30%, #555, #080808 68%)); }
.stone.white { border: 1px solid var(--game-white-stone-border, transparent); background: var(--game-white-stone, radial-gradient(circle at 35% 30%, #fff, #d7d2c8 70%)); }
.stone.latest::after {
  content: '';
  position: absolute;
  inset: 35%;
  border-radius: 50%;
  background: #d84f42;
  box-shadow: 0 0 0 1px rgba(255, 238, 210, .62);
}
.gomoku-board-hint { width: min(100%, 650px); margin: -4px 0 0; color: var(--muted); text-align: center; font-size: 13px; }
.renju-legend { width: min(100%, 650px); display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 8px 16px; color: var(--muted); }
.renju-legend > span { display: inline-flex; align-items: center; gap: 6px; }
.renju-legend i { width: 18px; aspect-ratio: 1; display: inline-grid; place-items: center; border-radius: 50%; font-style: normal; }
.forbidden-sample { color: #a12a2a; background: rgba(255, 210, 190, .45); font-weight: 950; }
.opening-sample { border: 2px solid #7c4e25; background: rgba(255, 219, 121, .35); }
.renju-legend small { flex-basis: 100%; text-align: center; }
.gomoku-game-actions { display: flex; align-items: center; gap: 9px; }
.gomoku-pass-button { display: inline-flex; align-items: center; gap: 6px; min-height: 42px; border: 1px solid var(--line); border-radius: 11px; padding: 0 14px; color: var(--text); background: transparent; font-weight: 850; }
.gomoku-pass-button:disabled { opacity: .45; }
@media (max-width: 600px) {
  .gomoku-board { --board-padding: 8px; --board-border-width: 4px; }
  .gomoku-rule-notice, .renju-legend, .swap2-choice-panel, .gomoku-pass-notice { width: 100%; }
  .swap2-choice-panel > div { grid-template-columns: 1fr; }
}
@media (hover: none) {
  .board-point:hover .stone-preview:not(.active) { opacity: 0; transform: scale(.82); }
}
</style>
