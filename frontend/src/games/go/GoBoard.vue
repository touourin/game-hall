<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { CheckCircle2, Flag, Play } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import UiButton from '../../components/ui/UiButton.vue'
import IntersectionBoard from '../shared/IntersectionBoard.vue'

interface GoScore {
  black: number
  white: number
  blackStones: number
  blackTerritory: number
  whiteStones: number
  whiteTerritory: number
  neutralPoints: number
  komi: number
  deadBlack: number
  deadWhite: number
}

interface GoScoring {
  deadStones: Array<{ row: number; column: number }>
  confirmedPlayerIds: string[]
  resumeRequesterId: string | null
}

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
  score: GoScore | null
  scoring: GoScoring | null
})
const isMyTurn = computed(
  () => game.value.turnPlayerId === props.snapshot.self.id,
)
const isScoring = computed(() => props.snapshot.phase === 'scoring')
const deadStoneKeys = computed(
  () => new Set(
    (game.value.scoring?.deadStones ?? []).map(
      ({ row, column }) => `${row}:${column}`,
    ),
  ),
)
const selfConfirmed = computed(() =>
  game.value.scoring?.confirmedPlayerIds.includes(props.snapshot.self.id) ?? false,
)
const resumeRequester = computed(() =>
  props.snapshot.players.find(
    (player) => player.id === game.value.scoring?.resumeRequesterId,
  ) ?? null,
)
const resumeLabel = computed(() => {
  if (!resumeRequester.value) return '申请继续对局'
  return resumeRequester.value.id === props.snapshot.self.id
    ? '撤回继续申请'
    : '同意继续对局'
})
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

function isDead(row: number, column: number) {
  return deadStoneKeys.value.has(`${row}:${column}`)
}

function pointDisabled(cell: number) {
  if (arcade.busy) return true
  if (isScoring.value) return cell === 0
  return props.snapshot.phase !== 'playing' || !isMyTurn.value || cell !== 0
}

function isPendingMove(row: number, column: number) {
  return pendingMove.value?.row === row && pendingMove.value?.column === column
}

function pointCanPreview(cell: number) {
  return !isScoring.value && !pointDisabled(cell)
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

function selectPoint(row: number, column: number, cell: number, event: MouseEvent) {
  if (pointDisabled(cell)) return
  if (isScoring.value) {
    void arcade.action('mark_dead', { row, column })
    return
  }
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
      <strong v-if="isScoring">终局数子确认</strong>
      <strong v-else>{{ isMyTurn ? '轮到你落子' : '等待对手落子' }}</strong>
      <span>你执{{ game.colors[snapshot.self.id] === 'black' ? '黑' : '白' }}</span>
      <span>提子 黑 {{ game.captures.black }} · 白 {{ game.captures.white }}</span>
      <span>贴目 {{ game.komi }}</span>
    </div>

    <section v-if="isScoring" class="go-scoring-guide" aria-live="polite">
      <strong>点击棋盘上的死棋，整块棋会一起标记</strong>
      <p>标记有变化时，双方需要重新确认。对死活有争议，可以申请继续下棋。</p>
    </section>

    <IntersectionBoard
      :size="game.boardSize"
      class="go-board"
      :class="{ scoring: isScoring }"
      :aria-label="`${game.boardSize} 路围棋棋盘`"
    >
      <template v-for="(row, rowIndex) in game.board" :key="rowIndex">
        <button
          v-for="(cell, columnIndex) in row"
          :key="`${rowIndex}-${columnIndex}`"
          type="button"
          class="go-point"
          :class="{
            'dead-point': isDead(rowIndex, columnIndex),
            star: isStarPoint(rowIndex, columnIndex),
            previewing: isPendingMove(rowIndex, columnIndex),
          }"
          :disabled="pointDisabled(cell)"
          :aria-pressed="isPendingMove(rowIndex, columnIndex)"
          :aria-label="isScoring && cell ? `${isDead(rowIndex, columnIndex) ? '取消' : ''}标记死子` : undefined"
          @click="selectPoint(rowIndex, columnIndex, cell, $event)"
        >
          <span
            v-if="!cell && pointCanPreview(cell)"
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
                dead: isDead(rowIndex, columnIndex),
              },
            ]"
          />
        </button>
      </template>
    </IntersectionBoard>
    <p v-if="snapshot.phase === 'playing' && isMyTurn" class="go-board-hint" aria-live="polite">
      {{ pendingMoveLabel }}
    </p>

    <div v-if="snapshot.phase === 'playing'" class="inline-actions">
      <button type="button" :disabled="!isMyTurn || arcade.busy" @click="arcade.action('pass')">
        停一手
      </button>
      <UiButton variant="danger" compact :disabled="arcade.busy" @click="arcade.action('resign')">
        <Flag :size="17" />认输
      </UiButton>
      <small>本回合不落子；双方连续停一手后进入终局数子</small>
    </div>

    <section v-if="isScoring && game.scoring" class="go-scoring-actions">
      <p>
        已确认 {{ game.scoring.confirmedPlayerIds.length }} / {{ snapshot.players.length }} 人
        <template v-if="resumeRequester">
          · {{ resumeRequester.id === snapshot.self.id ? '已申请继续对局' : `${resumeRequester.name}申请继续对局` }}
        </template>
      </p>
      <div>
        <button
          type="button"
          class="confirm-score-button"
          :disabled="selfConfirmed || arcade.busy"
          @click="arcade.action('confirm_score')"
        >
          <CheckCircle2 :size="18" />{{ selfConfirmed ? '你已确认' : '确认死子和数子' }}
        </button>
        <button type="button" :disabled="arcade.busy" @click="arcade.action('resume_play')">
          <Play :size="18" />{{ resumeLabel }}
        </button>
      </div>
    </section>

    <section v-if="game.score" class="go-score-card">
      <header>
        <strong>{{ isScoring ? '当前数子预览' : '终局数子' }}</strong>
        <span>中国数子</span>
      </header>
      <div class="go-score-breakdown">
        <article>
          <b>黑方 {{ game.score.black }}</b>
          <span>棋子 {{ game.score.blackStones }} ＋ 围空 {{ game.score.blackTerritory }}</span>
        </article>
        <article>
          <b>白方 {{ game.score.white }}</b>
          <span>棋子 {{ game.score.whiteStones }} ＋ 围空 {{ game.score.whiteTerritory }} ＋ 贴目 {{ game.score.komi }}</span>
        </article>
      </div>
      <p>
        中立点 {{ game.score.neutralPoints }}
        <template v-if="game.score.deadBlack || game.score.deadWhite">
          · 标记死子：黑 {{ game.score.deadBlack }}、白 {{ game.score.deadWhite }}
        </template>
      </p>
    </section>
  </section>
</template>

<style scoped>
.go-panel { width: 100%; min-width: 0; display: grid; gap: 14px; justify-items: center; }
.go-status { width: 100%; min-width: 0; display: flex; flex-wrap: wrap; justify-content: center; gap: 8px 16px; color: var(--muted); }
.go-status strong { color: var(--gold); }
.go-scoring-guide { width: min(100%, 700px); padding: 13px 15px; border: 1px solid color-mix(in srgb, var(--gold) 42%, var(--line)); border-radius: 13px; background: color-mix(in srgb, var(--gold) 8%, var(--surface)); text-align: center; }
.go-scoring-guide strong { color: var(--gold); }
.go-scoring-guide p { margin: 5px 0 0; color: var(--muted); line-height: 1.5; }
.go-board {
  --board-padding: 11px;
}
.go-board.scoring { --board-status-ring: 0 0 0 3px color-mix(in srgb, var(--gold) 45%, transparent); }
.go-point {
  position: relative;
  padding: 0;
  border: 0;
  background: transparent;
}
.go-point:disabled { opacity: 1; }
.go-point:not(:disabled) { cursor: crosshair; }
.go-point:focus-visible { border-radius: 50%; outline-offset: -3px; }
.go-point.star::before { content: ''; position: absolute; z-index: 1; top: 50%; left: 50%; width: clamp(4px, 18%, 7px); aspect-ratio: 1; border-radius: 50%; background: var(--game-board-line, #513016); box-shadow: 0 0 0 1px rgba(0, 0, 0, .2); transform: translate(-50%, -50%); }
.go-board.scoring .go-point:not(:disabled) { cursor: pointer; }
.go-stone { position: absolute; inset: 4%; z-index: 2; border-radius: 50%; box-shadow: inset 2px 2px 3px rgba(255, 255, 255, .14), inset -3px -4px 5px rgba(0, 0, 0, .42), 0 1px 1px rgba(255, 232, 177, .15), 0 4px 7px rgba(28, 15, 5, .5); transition: opacity .15s, transform .15s; }
.go-stone.black { background: var(--game-black-stone, radial-gradient(circle at 35% 30%, #555, #050505 68%)); }
.go-stone.white { border: 1px solid var(--game-white-stone-border, rgba(76, 56, 32, .22)); background: var(--game-white-stone, radial-gradient(circle at 35% 30%, white, #d7d2c8 72%)); }
.go-stone.latest::after { content: ''; position: absolute; inset: 37%; border-radius: 50%; background: #d84f42; box-shadow: 0 0 0 1px rgba(255, 238, 210, .62); }
.go-preview { z-index: 4; opacity: 0; transform: scale(.82); pointer-events: none; }
.go-point:not(:disabled):hover .go-preview,
.go-preview.active { opacity: .48; transform: scale(1); }
.go-preview.active { outline: 2px solid rgba(255, 245, 197, .78); outline-offset: 2px; }
.go-stone.dead { opacity: .38; transform: scale(.88); }
.go-stone.dead::after { content: '×'; position: absolute; inset: -20%; display: grid; place-items: center; border-radius: 50%; color: #8d1717; background: rgba(255, 230, 210, .55); font-size: clamp(14px, 2.4vw, 26px); font-weight: 950; }
.inline-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }
.inline-actions button:not(.ui-button--danger) { border: 1px solid var(--line); border-radius: 12px; padding: 10px 18px; color: var(--text); background: var(--surface); }
.inline-actions small { flex-basis: 100%; color: var(--muted); text-align: center; }
.go-scoring-actions { width: min(100%, 700px); display: grid; gap: 10px; padding: 14px; border: 1px solid var(--line); border-radius: 14px; background: var(--surface); }
.go-scoring-actions p { margin: 0; color: var(--muted); text-align: center; }
.go-scoring-actions > div { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; }
.go-scoring-actions button { min-height: 44px; display: inline-flex; align-items: center; justify-content: center; gap: 7px; border: 1px solid var(--line); border-radius: 11px; color: var(--text); background: transparent; font-weight: 850; }
.go-scoring-actions .confirm-score-button { border-color: color-mix(in srgb, var(--gold) 48%, var(--line)); color: var(--gold); background: color-mix(in srgb, var(--gold) 8%, transparent); }
.go-scoring-actions button:disabled { opacity: .58; }
.go-score-card { width: min(100%, 700px); display: grid; gap: 10px; padding: 14px; border: 1px solid var(--line); border-radius: 14px; background: var(--surface); }
.go-score-card header { display: flex; align-items: center; justify-content: space-between; }
.go-score-card header strong { color: var(--gold); }
.go-score-card header span, .go-score-card p, .go-score-breakdown span { color: var(--muted); }
.go-score-breakdown { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; }
.go-score-breakdown article { display: grid; gap: 4px; padding: 11px; border: 1px solid var(--line); border-radius: 11px; }
.go-score-breakdown b { font-size: 16px; }
.go-score-breakdown span { line-height: 1.45; }
.go-score-card p { margin: 0; text-align: center; }
.go-board-hint { width: min(100%, 700px); margin: -3px 0 0; color: var(--muted); text-align: center; font-size: 13px; }
@media (max-width: 600px) {
  .go-scoring-guide, .go-scoring-actions, .go-score-card { width: 100%; }
  .go-scoring-guide { text-align: left; }
  .go-scoring-actions > div, .go-score-breakdown { grid-template-columns: 1fr; }
  .go-board { --board-padding: 7px; --board-border-width: 4px; }
}
@media (orientation: landscape) and (max-width: 980px) and (max-height: 600px) {
  .go-board { --board-max-width: min(58vw, calc(100svh - 96px)); }
}
@media (hover: none) {
  .go-point:hover .go-preview:not(.active) { opacity: 0; transform: scale(.82); }
}
</style>
