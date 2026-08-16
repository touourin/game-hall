<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Bomb,
  Clock3,
  Flag,
  MousePointerClick,
  Move,
  RotateCcw,
  ShieldCheck,
  Trophy,
  ZoomIn,
  ZoomOut,
} from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import SoloResultCard from '../shared/solo/SoloResultCard.vue'

type CellState = 'hidden' | 'open' | 'flagged' | 'mine' | 'exploded' | 'wrong_flag'

interface MineCell {
  state: CellState
  adjacent: number | null
}

interface MinesweeperView {
  difficulty: 'beginner' | 'intermediate' | 'expert'
  difficultyLabel: string
  rows: number
  columns: number
  mineCount: number
  cells: MineCell[]
  started: boolean
  revealedCount: number
  safeCellCount: number
  flaggedCount: number
  remainingMines: number
  elapsedMs: number
  explodedIndex: number | null
  firstMoveSafe: boolean
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const interactionMode = ref<'open' | 'flag'>('open')
const zoom = ref(1)
const pendingIndexes = ref<Set<number>>(new Set())
const hint = ref('第一次翻开一定安全，计时会从首次翻格开始')
const now = ref(performance.now())
const clockBaseMs = ref(0)
const clockReceivedAt = ref(performance.now())
const pressStart = ref<{ index: number; x: number; y: number } | null>(null)
const suppressClickIndex = ref<number | null>(null)
let clockTimer: ReturnType<typeof setInterval> | null = null
let holdTimer: ReturnType<typeof setTimeout> | null = null

const game = computed(() => props.snapshot.game as unknown as MinesweeperView)
const won = computed(() => props.snapshot.winner === 'completed')
const progress = computed(() => game.value.safeCellCount
  ? Math.round(game.value.revealedCount / game.value.safeCellCount * 100)
  : 0)
const baseCellSize = computed(() => {
  if (game.value.difficulty === 'beginner') return 46
  if (game.value.difficulty === 'intermediate') return 38
  return 30
})
const boardStyle = computed(() => ({
  '--mine-columns': game.value.columns,
  '--mine-cell-size': `${Math.round(baseCellSize.value * zoom.value)}px`,
}))
const elapsedMs = computed(() => {
  if (!game.value.started || props.snapshot.phase !== 'playing') {
    return game.value.elapsedMs
  }
  return clockBaseMs.value + Math.max(0, now.value - clockReceivedAt.value)
})

function syncClock() {
  clockBaseMs.value = game.value.elapsedMs
  clockReceivedAt.value = performance.now()
  now.value = clockReceivedAt.value
}

function formatTime(milliseconds: number): string {
  const totalTenths = Math.floor(milliseconds / 100)
  const minutes = Math.floor(totalTenths / 600)
  const seconds = Math.floor(totalTenths / 10) % 60
  const tenths = totalTenths % 10
  return minutes
    ? `${minutes}:${String(seconds).padStart(2, '0')}.${tenths}`
    : `${seconds}.${tenths}`
}

function cellLabel(cell: MineCell, index: number): string {
  const row = Math.floor(index / game.value.columns) + 1
  const column = index % game.value.columns + 1
  const position = `第 ${row} 行第 ${column} 列`
  if (cell.state === 'flagged') return `${position}，已插旗`
  if (cell.state === 'mine' || cell.state === 'exploded') return `${position}，地雷`
  if (cell.state === 'wrong_flag') return `${position}，错误旗帜`
  if (cell.state === 'open') return `${position}，周围 ${cell.adjacent ?? 0} 个地雷`
  return `${position}，未翻开`
}

async function sendAction(action: 'open' | 'toggle_flag' | 'chord', index: number) {
  if (props.snapshot.phase !== 'playing' || pendingIndexes.value.has(index)) return
  pendingIndexes.value = new Set([...pendingIndexes.value, index])
  const succeeded = await arcade.rapidAction(action, { index })
  const nextPending = new Set(pendingIndexes.value)
  nextPending.delete(index)
  pendingIndexes.value = nextPending
  if (!succeeded) {
    hint.value = arcade.error ?? '这次操作没有成功'
    return
  }
  if (action === 'toggle_flag') {
    hint.value = '旗帜已更新；数字表示周围八格中的地雷数量'
  } else if (!game.value.started) {
    hint.value = '雷区已经生成，继续翻开安全方格'
  }
}

function activateCell(cell: MineCell, index: number) {
  if (suppressClickIndex.value === index) {
    suppressClickIndex.value = null
    return
  }
  if (cell.state === 'open') {
    if ((cell.adjacent ?? 0) > 0) void sendAction('chord', index)
    return
  }
  if (cell.state !== 'hidden' && cell.state !== 'flagged') return
  void sendAction(interactionMode.value === 'flag' ? 'toggle_flag' : 'open', index)
}

function toggleFlag(index: number) {
  const cell = game.value.cells[index]
  if (!cell || !['hidden', 'flagged'].includes(cell.state)) return
  void sendAction('toggle_flag', index)
}

function clearHoldTimer() {
  if (holdTimer !== null) {
    window.clearTimeout(holdTimer)
    holdTimer = null
  }
}

function startPress(event: PointerEvent, index: number) {
  if (event.isPrimary === false || (event.button ?? 0) !== 0) return
  pressStart.value = { index, x: event.clientX, y: event.clientY }
  clearHoldTimer()
  holdTimer = window.setTimeout(() => {
    suppressClickIndex.value = index
    toggleFlag(index)
    if ('vibrate' in navigator) navigator.vibrate?.(30)
    hint.value = '长按插旗已生效；也可以切换下方的插旗模式'
    holdTimer = null
  }, 480)
}

function movePress(event: PointerEvent) {
  const start = pressStart.value
  if (!start) return
  if (Math.hypot(event.clientX - start.x, event.clientY - start.y) > 9) {
    clearHoldTimer()
    pressStart.value = null
  }
}

function endPress() {
  clearHoldTimer()
  pressStart.value = null
}

function setZoom(next: number) {
  zoom.value = Math.min(1.25, Math.max(.75, next))
}

async function resetGame() {
  if (arcade.busy) return
  await arcade.action('reset')
  if (!arcade.error) {
    hint.value = '新雷区将在第一次翻开时生成，计时已经清零'
    pendingIndexes.value = new Set()
  }
}

async function restartGame() {
  if (await arcade.restartGame()) {
    hint.value = '新一轮挑战已准备好，第一次翻开一定安全'
    pendingIndexes.value = new Set()
  }
}

watch(
  () => [props.snapshot.revision, props.snapshot.phase, game.value.elapsedMs],
  () => syncClock(),
  { immediate: true },
)

onMounted(() => {
  clockTimer = window.setInterval(() => {
    now.value = performance.now()
  }, 100)
})

onBeforeUnmount(() => {
  if (clockTimer !== null) window.clearInterval(clockTimer)
  clearHoldTimer()
})
</script>

<template>
  <section class="minesweeper-game">
    <header class="surface minesweeper-status">
      <span class="minesweeper-mark"><Bomb :size="23" /></span>
      <div>
        <small>{{ game.difficultyLabel }} · {{ game.rows }}×{{ game.columns }}</small>
        <strong>{{ game.mineCount }} 枚地雷</strong>
      </div>
      <div class="minesweeper-status-data">
        <span><Clock3 :size="15" /><b>{{ formatTime(elapsedMs) }}</b><small>用时</small></span>
        <span><Flag :size="15" /><b>{{ game.remainingMines }}</b><small>剩余</small></span>
        <span><ShieldCheck :size="15" /><b>{{ progress }}%</b><small>进度</small></span>
      </div>
    </header>

    <section class="surface minesweeper-panel" :class="[`difficulty-${game.difficulty}`, { finished: snapshot.phase === 'finished' }]">
      <header class="minesweeper-toolbar">
        <div class="minesweeper-mode" aria-label="扫雷操作模式">
          <button type="button" :class="{ active: interactionMode === 'open' }" @click="interactionMode = 'open'">
            <MousePointerClick :size="16" />翻开
          </button>
          <button type="button" :class="{ active: interactionMode === 'flag' }" @click="interactionMode = 'flag'">
            <Flag :size="16" />插旗
          </button>
        </div>
        <p><Move :size="15" />拖动查看雷区 · 长按或右键插旗</p>
        <div class="minesweeper-zoom" aria-label="棋盘缩放">
          <button type="button" aria-label="缩小雷区" :disabled="zoom <= .75" @click="setZoom(zoom - .25)"><ZoomOut :size="16" /></button>
          <span>{{ Math.round(zoom * 100) }}%</span>
          <button type="button" aria-label="放大雷区" :disabled="zoom >= 1.25" @click="setZoom(zoom + .25)"><ZoomIn :size="16" /></button>
        </div>
      </header>

      <div class="minefield-viewport" tabindex="0" aria-label="可拖动的扫雷棋盘视口">
        <div
          class="minefield"
          :style="boardStyle"
          role="grid"
          :aria-rowcount="game.rows"
          :aria-colcount="game.columns"
        >
          <button
            v-for="(cell, index) in game.cells"
            :key="index"
            type="button"
            role="gridcell"
            class="mine-cell"
            :class="[
              `state-${cell.state}`,
              cell.state === 'open' ? `number-${cell.adjacent ?? 0}` : '',
              { pending: pendingIndexes.has(index) },
            ]"
            :aria-label="cellLabel(cell, index)"
            :disabled="snapshot.phase !== 'playing'"
            @click="activateCell(cell, index)"
            @contextmenu.prevent="toggleFlag(index)"
            @pointerdown="startPress($event, index)"
            @pointermove="movePress"
            @pointerup="endPress"
            @pointercancel="endPress"
            @pointerleave="endPress"
          >
            <Flag v-if="cell.state === 'flagged'" :size="18" fill="currentColor" />
            <Bomb v-else-if="cell.state === 'mine' || cell.state === 'exploded'" :size="19" />
            <span v-else-if="cell.state === 'wrong_flag'" class="wrong-flag"><Flag :size="17" />×</span>
            <b v-else-if="cell.state === 'open' && cell.adjacent">{{ cell.adjacent }}</b>
          </button>
        </div>
      </div>

      <div class="minesweeper-progress" aria-hidden="true"><i :style="{ width: `${progress}%` }" /></div>
      <footer>
        <p aria-live="polite">{{ hint }}</p>
        <button v-if="snapshot.phase === 'playing'" type="button" :disabled="arcade.busy" @click="resetGame">
          <RotateCcw :size="16" />重新布雷
        </button>
      </footer>
    </section>

    <SoloResultCard
      v-if="snapshot.phase === 'finished'"
      class="minesweeper-result"
      :eyebrow="won ? '排雷完成' : '本轮结束'"
      :title="won ? `${game.difficultyLabel}通关` : '踩中地雷'"
      :description="snapshot.winReason"
      :tone="won ? 'success' : 'danger'"
      :metrics="[
        { label: '完成用时', value: formatTime(game.elapsedMs) },
        { label: '安全格', value: game.revealedCount },
        { label: '旗帜', value: game.flaggedCount },
      ]"
      :can-restart="snapshot.actions.canRestart"
      @restart="restartGame"
    >
      <template #icon><Trophy v-if="won" :size="22" /><Bomb v-else :size="22" /></template>
    </SoloResultCard>
  </section>
</template>

<style scoped>
.minesweeper-game { width: min(100%, 1180px); min-width: 0; margin: 0 auto; display: grid; gap: 16px; }
.minesweeper-game > * { min-width: 0; max-width: 100%; }
.minesweeper-status { padding: 14px 16px; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 12px; }
.minesweeper-mark { width: 44px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 13px; color: var(--red); background: color-mix(in srgb, var(--red) 11%, transparent); }
.minesweeper-status > div:nth-child(2) { display: grid; gap: 3px; }.minesweeper-status > div:nth-child(2) small { color: var(--accent); font-size: 10px; font-weight: 850; }.minesweeper-status > div:nth-child(2) strong { font-family: "Songti SC", "STSong", serif; font-size: 20px; }
.minesweeper-status-data { min-width: 0; display: flex; gap: 7px; }.minesweeper-status-data > span { min-width: 82px; min-height: 39px; display: grid; grid-template-columns: auto auto; align-content: center; justify-content: center; column-gap: 5px; border: 1px solid var(--line); border-radius: 11px; padding: 4px 9px; background: var(--surface-inset); }.minesweeper-status-data svg { color: var(--accent); }.minesweeper-status-data b { font-size: 14px; }.minesweeper-status-data small { grid-column: 1 / 3; color: var(--muted); font-size: 8px; text-align: center; }
.minesweeper-panel { padding: 14px; display: grid; gap: 12px; overflow: hidden; background: radial-gradient(circle at 50% 35%, color-mix(in srgb, var(--green) 5%, transparent), transparent 52%), var(--surface); }
.minesweeper-panel.finished { border-color: color-mix(in srgb, var(--accent) 40%, var(--line)); }
.minesweeper-toolbar { min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 10px; }.minesweeper-toolbar p { min-width: 0; margin: 0; display: flex; align-items: center; justify-content: center; gap: 5px; overflow: hidden; color: var(--muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.minesweeper-mode { display: flex; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }.minesweeper-mode button { min-height: 38px; display: inline-flex; align-items: center; gap: 5px; border: 0; padding: 0 11px; color: var(--muted); background: var(--surface-inset); font-weight: 850; }.minesweeper-mode button + button { border-left: 1px solid var(--line); }.minesweeper-mode button.active { color: var(--accent-contrast); background: var(--accent); }
.minesweeper-zoom { display: flex; align-items: center; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }.minesweeper-zoom button { width: 36px; min-height: 36px; display: grid; place-items: center; border: 0; color: var(--muted); background: var(--surface-inset); }.minesweeper-zoom span { min-width: 48px; color: var(--accent); font-size: 10px; font-weight: 900; text-align: center; }
.minefield-viewport { min-width: 0; max-width: 100%; max-height: min(68vh, 720px); overflow: auto; border: 1px solid var(--line); border-radius: 14px; padding: 12px; background: color-mix(in srgb, var(--surface-inset) 82%, var(--bg)); box-shadow: inset 0 12px 30px color-mix(in srgb, var(--panel-shadow) 38%, transparent); overscroll-behavior: contain; scrollbar-color: color-mix(in srgb, var(--accent) 38%, transparent) transparent; }
.minefield { --mine-columns: 9; --mine-cell-size: 46px; width: max-content; margin: 0 auto; display: grid; grid-template-columns: repeat(var(--mine-columns), var(--mine-cell-size)); grid-auto-rows: var(--mine-cell-size); gap: 3px; }
.mine-cell { position: relative; width: var(--mine-cell-size); height: var(--mine-cell-size); min-width: 0; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--line) 96%, var(--panel-highlight) 5%); border-radius: clamp(5px, calc(var(--mine-cell-size) * .18), 9px); padding: 0; color: var(--text); background: linear-gradient(145deg, color-mix(in srgb, var(--surface-elevated) 91%, var(--panel-highlight) 5%), color-mix(in srgb, var(--surface-strong) 92%, var(--surface-inset))); box-shadow: inset 1px 1px 0 color-mix(in srgb, var(--panel-highlight) 34%, transparent), 0 2px 5px color-mix(in srgb, var(--panel-shadow) 42%, transparent); touch-action: pan-x pan-y; user-select: none; transition: transform .08s, border-color .12s, background .12s, opacity .12s; }
.mine-cell:not(:disabled) { cursor: pointer; }.mine-cell:active:not(:disabled) { transform: scale(.92); }.mine-cell:disabled { opacity: 1; }.mine-cell.pending { opacity: .62; }.mine-cell:focus-visible { z-index: 2; outline: 2px solid var(--accent); outline-offset: 1px; }
.mine-cell.state-open { border-color: color-mix(in srgb, var(--line) 52%, transparent); border-radius: 5px; background: color-mix(in srgb, var(--surface-soft) 52%, var(--surface-primary)); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--panel-shadow) 18%, transparent); }.mine-cell.state-open b { font-size: clamp(13px, calc(var(--mine-cell-size) * .48), 21px); text-shadow: 0 1px 2px color-mix(in srgb, var(--panel-shadow) 38%, transparent); }.mine-cell.number-1 { color: color-mix(in srgb, #4386c2 72%, var(--text)); }.mine-cell.number-2 { color: color-mix(in srgb, #3b9a6c 72%, var(--text)); }.mine-cell.number-3 { color: color-mix(in srgb, #c75e59 72%, var(--text)); }.mine-cell.number-4 { color: color-mix(in srgb, #7756a4 72%, var(--text)); }.mine-cell.number-5 { color: color-mix(in srgb, #a86535 72%, var(--text)); }.mine-cell.number-6 { color: color-mix(in srgb, #388f8d 72%, var(--text)); }.mine-cell.number-7 { color: var(--text); }.mine-cell.number-8 { color: var(--text-soft); }
.mine-cell.state-flagged { color: var(--accent); background: linear-gradient(145deg, color-mix(in srgb, var(--accent) 12%, var(--surface-strong)), var(--surface-strong)); }.mine-cell.state-mine { color: var(--red); background: color-mix(in srgb, var(--red) 14%, var(--surface-inset)); }.mine-cell.state-exploded { z-index: 2; color: white; border-color: color-mix(in srgb, var(--red) 76%, white); background: var(--red); box-shadow: 0 0 0 4px color-mix(in srgb, var(--red) 18%, transparent), 0 0 24px color-mix(in srgb, var(--red) 40%, transparent); animation: mine-burst .38s ease; }.mine-cell.state-wrong_flag { color: var(--red); background: color-mix(in srgb, var(--red) 12%, var(--surface-inset)); }.wrong-flag { display: flex; align-items: center; font-weight: 950; }
@keyframes mine-burst { 45% { transform: scale(1.18) rotate(6deg); } }
.minesweeper-progress { height: 5px; overflow: hidden; border-radius: 999px; background: var(--surface-inset); }.minesweeper-progress i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--accent), var(--green)); transition: width .18s ease; }
.minesweeper-panel > footer { min-width: 0; display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 10px; }.minesweeper-panel > footer p { min-width: 0; margin: 0; overflow: hidden; color: var(--muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }.minesweeper-panel > footer button { min-height: 38px; display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 10px; padding: 0 11px; color: var(--muted); background: var(--surface-inset); font-weight: 850; }
.minesweeper-result { padding: 24px; display: grid; justify-items: center; gap: 7px; text-align: center; }.minesweeper-result > span { display: flex; align-items: center; gap: 6px; color: var(--red); font-weight: 850; }.minesweeper-result.won > span { color: var(--green); }.minesweeper-result h2 { margin: 2px 0 0; font-family: "Songti SC", "STSong", serif; font-size: clamp(32px, 7vw, 48px); }.minesweeper-result > p { margin: 0; color: var(--muted); }.minesweeper-result > div { width: min(100%, 500px); margin: 8px 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }.minesweeper-result > div span { border: 1px solid var(--line); border-radius: 11px; padding: 10px 6px; color: var(--muted); font-size: 10px; }.minesweeper-result > div b { display: block; margin-bottom: 3px; color: var(--accent); font-size: 15px; }.minesweeper-result .ui-button--primary { margin-top: 5px; }
@media (max-width: 620px) {
  .minesweeper-status { grid-template-columns: auto minmax(0, 1fr); }.minesweeper-status-data { grid-column: 1 / 3; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }.minesweeper-status-data > span { min-width: 0; }
  .minesweeper-panel { padding: 10px; }.minesweeper-toolbar { grid-template-columns: minmax(0, 1fr) auto; }.minesweeper-toolbar p { grid-column: 1 / 3; grid-row: 2; justify-content: flex-start; }.minesweeper-mode { min-width: 0; }.minesweeper-mode button { flex: 1; justify-content: center; }
  .minefield-viewport { max-height: 61vh; padding: 8px; }.minefield { margin: 0; }
  .minesweeper-panel > footer { grid-template-columns: 1fr; }.minesweeper-panel > footer p { white-space: normal; line-height: 1.5; }.minesweeper-panel > footer button { justify-content: center; }
}
@media (max-width: 390px) {
  .minesweeper-zoom span { min-width: 40px; }.minesweeper-zoom button { width: 32px; }.minesweeper-mode button { padding-inline: 8px; }
  .minesweeper-result > div { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  .mine-cell.state-exploded { animation: none; }
  .minesweeper-progress i { transition: none; }
}
</style>
