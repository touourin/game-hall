<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Clock3, Grid3X3, RotateCcw, ScanSearch, Target, TriangleAlert } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import UiButton from '../../components/ui/UiButton.vue'
import SoloMetricGrid from '../shared/solo/SoloMetricGrid.vue'
import SoloResultCard from '../shared/solo/SoloResultCard.vue'

interface SchulteView {
  gridSize: number
  cellCount: number
  grid: number[]
  started: boolean
  nextNumber: number
  completedCount: number
  mistakes: number
  elapsedMs: number
  averageCellMs: number | null
  accuracy: number | null
  lastValue: number | null
  lastCorrect: boolean | null
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const isSpectating = computed(() => props.snapshot.viewer?.mode === 'spectator')
const localNext = ref(1)
const wrongValue = ref<number | null>(null)
const lastCorrectValue = ref<number | null>(null)
const now = ref(performance.now())
const clockBaseMs = ref(0)
const clockReceivedAt = ref(performance.now())
let clockTimer: ReturnType<typeof setInterval> | null = null
let wrongTimer: ReturnType<typeof setTimeout> | null = null

const game = computed(() => props.snapshot.game as unknown as SchulteView)
const elapsedMs = computed(() => {
  if (!game.value.started || props.snapshot.phase !== 'playing') {
    return game.value.elapsedMs
  }
  return clockBaseMs.value + Math.max(0, now.value - clockReceivedAt.value)
})
const completedCount = computed(() => Math.min(localNext.value - 1, game.value.cellCount))
const progress = computed(() => completedCount.value / game.value.cellCount * 100)
const nextLabel = computed(() =>
  localNext.value > game.value.cellCount ? '完成' : String(localNext.value),
)

function syncSnapshot() {
  clockBaseMs.value = game.value.elapsedMs
  clockReceivedAt.value = performance.now()
  now.value = clockReceivedAt.value
  if (!game.value.started) {
    localNext.value = 1
    return
  }
  if (props.snapshot.phase === 'finished') {
    localNext.value = game.value.cellCount + 1
    return
  }
  localNext.value = Math.max(localNext.value, game.value.nextNumber)
}

function formatTime(milliseconds: number): string {
  const totalHundredths = Math.floor(milliseconds / 10)
  const minutes = Math.floor(totalHundredths / 6_000)
  const seconds = Math.floor(totalHundredths / 100) % 60
  const hundredths = totalHundredths % 100
  return minutes
    ? `${minutes}:${String(seconds).padStart(2, '0')}.${String(hundredths).padStart(2, '0')}`
    : `${seconds}.${String(hundredths).padStart(2, '0')}`
}

async function beginChallenge() {
  if (isSpectating.value || arcade.busy || props.snapshot.phase !== 'playing') return
  await arcade.action('begin')
}

async function resetChallenge() {
  if (isSpectating.value || arcade.busy || props.snapshot.phase !== 'playing') return
  await arcade.action('reset')
  if (!arcade.error) {
    localNext.value = 1
    wrongValue.value = null
    lastCorrectValue.value = null
  }
}

async function restartChallenge() {
  if (isSpectating.value) return
  if (await arcade.restartGame()) {
    localNext.value = 1
    wrongValue.value = null
    lastCorrectValue.value = null
  }
}

function showWrong(value: number) {
  wrongValue.value = value
  if (wrongTimer !== null) window.clearTimeout(wrongTimer)
  wrongTimer = window.setTimeout(() => {
    wrongValue.value = null
    wrongTimer = null
  }, 320)
  if ('vibrate' in navigator) navigator.vibrate?.(28)
}

function sendTap(value: number): Promise<boolean> {
  const store = arcade as typeof arcade & {
    rapidAction?: (
      actionName: string,
      payload?: Record<string, unknown>,
    ) => Promise<boolean>
  }
  if (store.rapidAction) return store.rapidAction('tap', { value })
  return arcade.action('tap', { value }).then(() => !arcade.error)
}

function activateCell(value: number) {
  if (
    isSpectating.value
    || !game.value.started
    || props.snapshot.phase !== 'playing'
  ) return
  if (value !== localNext.value) {
    showWrong(value)
    void sendTap(value)
    return
  }

  wrongValue.value = null
  if (wrongTimer !== null) {
    window.clearTimeout(wrongTimer)
    wrongTimer = null
  }
  lastCorrectValue.value = value
  localNext.value += 1
  void sendTap(value).then((succeeded) => {
    if (!succeeded) localNext.value = game.value.nextNumber
  })
}

function onPointerDown(event: PointerEvent, value: number) {
  if (event.isPrimary === false || (event.button ?? 0) !== 0) return
  event.preventDefault()
  activateCell(value)
}

function onAccessibleClick(event: MouseEvent, value: number) {
  if (event.detail !== 0) return
  activateCell(value)
}

watch(
  () => [props.snapshot.revision, props.snapshot.phase, game.value.elapsedMs],
  () => syncSnapshot(),
  { immediate: true },
)

onMounted(() => {
  clockTimer = window.setInterval(() => {
    now.value = performance.now()
  }, 50)
})

onBeforeUnmount(() => {
  if (clockTimer !== null) window.clearInterval(clockTimer)
  if (wrongTimer !== null) window.clearTimeout(wrongTimer)
})
</script>

<template>
  <section class="schulte-game">
    <header class="surface schulte-status">
      <span class="schulte-status-icon"><Grid3X3 :size="22" /></span>
      <div><small>SCHULTE GRID</small><strong>5×5 标准挑战</strong></div>
      <div class="schulte-status-metrics">
        <span><Clock3 :size="15" />{{ formatTime(elapsedMs) }}<small>秒</small></span>
        <span><Target :size="15" />{{ completedCount }} / {{ game.cellCount }}</span>
      </div>
    </header>

    <section v-if="!game.started && snapshot.phase === 'playing'" class="surface schulte-intro">
      <span class="schulte-intro-icon"><ScanSearch :size="34" /></span>
      <small>视觉搜索与专注挑战</small>
      <h2>按顺序找到 1–25</h2>
      <p>点击开始后数字才会出现。请保持视线覆盖整个方格，不要逐行扫描。</p>
      <div class="schulte-preview" aria-hidden="true">
        <i v-for="number in 25" :key="number">{{ number % 4 === 0 ? number : '·' }}</i>
      </div>
      <UiButton variant="primary" :disabled="isSpectating || arcade.busy" @click="beginChallenge">
        <ScanSearch :size="19" />开始挑战
      </UiButton>
    </section>

    <template v-else>
      <section class="surface schulte-board-card" :class="{ finished: snapshot.phase === 'finished' }">
        <header>
          <div>
            <small>{{ snapshot.phase === 'finished' ? '挑战完成' : '下一个数字' }}</small>
            <strong>{{ nextLabel }}</strong>
          </div>
          <p v-if="snapshot.phase === 'playing'">从数字 1 开始，依次点击到 25</p>
          <p v-else>服务端已验证全部点击顺序</p>
          <button
            v-if="snapshot.phase === 'playing'"
            type="button"
            class="schulte-reset-button"
            :disabled="isSpectating || arcade.busy"
            @click="resetChallenge"
          ><RotateCcw :size="16" />重置</button>
        </header>

        <div class="schulte-progress" aria-hidden="true"><i :style="{ width: `${progress}%` }" /></div>

        <div
          class="schulte-grid"
          :style="{ '--grid-size': game.gridSize }"
          role="grid"
          aria-label="舒尔特方格，按从小到大的顺序点击"
        >
          <button
            v-for="value in game.grid"
            :key="value"
            type="button"
            role="gridcell"
            class="schulte-cell"
            :class="{
              complete: value < localNext,
              wrong: wrongValue === value,
              latest: lastCorrectValue === value,
            }"
            :disabled="isSpectating || snapshot.phase !== 'playing'"
            :aria-label="`数字 ${value}${value < localNext ? '，已完成' : ''}`"
            @pointerdown="onPointerDown($event, value)"
            @click="onAccessibleClick($event, value)"
          >
            <span>{{ value }}</span>
          </button>
        </div>

        <p v-if="snapshot.phase === 'playing'" class="schulte-hint" aria-live="polite">
          <TriangleAlert v-if="wrongValue !== null" :size="16" />
          {{ wrongValue !== null ? `应该点击 ${localNext}` : `请寻找数字 ${localNext}` }}
        </p>
      </section>

      <SoloMetricGrid
        class="schulte-metrics"
        aria-label="舒尔特方格挑战数据"
        :items="[
          { label: '当前用时', value: `${formatTime(elapsedMs)} 秒` },
          { label: '点击错误', value: game.mistakes, tone: game.mistakes ? 'warning' : 'default' },
          { label: '完成进度', value: `${Math.round(progress)}%` },
        ]"
      />
    </template>

    <SoloResultCard
      v-if="snapshot.phase === 'finished'"
      class="schulte-result"
      eyebrow="5×5 标准挑战完成"
      title="服务端已验证完整点击顺序"
      :score="formatTime(game.elapsedMs)"
      score-unit="秒"
      :metrics="[
        { label: '平均每格', value: `${game.averageCellMs} ms` },
        { label: '错误点击', value: game.mistakes, tone: game.mistakes ? 'warning' : 'default' },
        { label: '点击准确率', value: `${game.accuracy}%` },
      ]"
      :can-restart="snapshot.actions.canRestart"
      @restart="restartChallenge"
    />
  </section>
</template>

<style scoped>
.schulte-game { width: min(100%, 720px); min-width: 0; margin: 0 auto; display: grid; gap: 16px; }
.schulte-game > * { min-width: 0; max-width: 100%; }
.schulte-status { padding: 14px 16px; display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 12px; }
.schulte-status-icon { width: 42px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 12px; color: var(--green); background: color-mix(in srgb, var(--green) 10%, transparent); }
.schulte-status > div:nth-child(2) { display: grid; }.schulte-status > div > small { color: var(--accent); font-size: 9px; font-weight: 850; letter-spacing: .15em; }.schulte-status > div > strong { margin-top: 3px; }
.schulte-status-metrics { min-width: 0; display: flex; gap: 7px; }.schulte-status-metrics > span { min-width: 0; min-height: 34px; display: inline-flex; align-items: center; gap: 5px; border: 1px solid var(--line); border-radius: 10px; padding: 0 9px; color: var(--text); background: var(--surface-inset); font-weight: 850; }.schulte-status-metrics svg { flex: 0 0 auto; color: var(--accent); }.schulte-status-metrics small { color: var(--muted); }
.schulte-intro { min-height: 520px; padding: clamp(26px, 6vw, 50px); display: grid; justify-items: center; align-content: center; gap: 10px; overflow: hidden; text-align: center; background: radial-gradient(circle at 50% 55%, color-mix(in srgb, var(--green) 10%, transparent), transparent 44%), var(--surface); }
.schulte-intro-icon { width: 66px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--green) 38%, var(--line)); border-radius: 20px; color: var(--green); background: color-mix(in srgb, var(--green) 8%, transparent); }.schulte-intro > small { color: var(--accent); font-weight: 850; letter-spacing: .08em; }.schulte-intro h2 { margin: 2px 0 0; font-family: "Songti SC", "STSong", serif; font-size: clamp(30px, 7vw, 46px); }.schulte-intro p { max-width: 460px; margin: 0; color: var(--muted); line-height: 1.7; }
.schulte-preview { width: min(75vw, 270px); aspect-ratio: 1; margin: 16px 0; display: grid; grid-template-columns: repeat(5, 1fr); gap: 5px; opacity: .58; transform: rotate(-3deg); }.schulte-preview i { display: grid; place-items: center; border: 1px solid var(--line); border-radius: 8px; color: var(--muted); background: var(--surface-strong); font-style: normal; }
.schulte-intro .ui-button--primary, .schulte-result .ui-button--primary { min-width: 190px; }
.schulte-board-card { padding: clamp(14px, 4vw, 24px); display: grid; gap: 14px; overflow: hidden; background: radial-gradient(circle at 50% 48%, color-mix(in srgb, var(--green) 7%, transparent), transparent 48%), var(--surface); }
.schulte-board-card > header { min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 12px; }.schulte-board-card > header > div { min-width: 82px; display: grid; justify-items: center; border: 1px solid color-mix(in srgb, var(--accent) 30%, var(--line)); border-radius: 13px; padding: 8px 12px; background: color-mix(in srgb, var(--accent) 7%, transparent); }.schulte-board-card > header small { color: var(--muted); font-size: 9px; }.schulte-board-card > header strong { color: var(--accent); font-size: 25px; line-height: 1.1; }.schulte-board-card > header p { min-width: 0; margin: 0; color: var(--muted); text-align: center; }
.schulte-reset-button { min-height: 38px; display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 10px; padding: 0 11px; color: var(--muted); background: var(--surface-inset); font-weight: 800; }
.schulte-progress { height: 5px; overflow: hidden; border-radius: 999px; background: var(--surface-inset); }.schulte-progress i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--accent), var(--green)); transition: width .16s ease; }
.schulte-grid { --grid-size: 5; width: min(100%, 570px); min-width: 0; max-width: 100%; aspect-ratio: 1; margin: 0 auto; display: grid; grid-template-columns: repeat(var(--grid-size), minmax(0, 1fr)); gap: clamp(5px, 1.3vw, 9px); }
.schulte-cell { position: relative; min-width: 0; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--line) 92%, transparent); border-radius: clamp(9px, 2vw, 15px); padding: 0; color: var(--text); background: linear-gradient(145deg, color-mix(in srgb, var(--surface-strong) 88%, var(--panel-highlight) 3%), var(--surface-strong)); box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 26%, transparent), 0 5px 14px color-mix(in srgb, var(--panel-shadow) 25%, transparent); touch-action: manipulation; user-select: none; transition: border-color .12s, color .12s, background .12s, transform .1s, opacity .12s; }
.schulte-cell:not(:disabled) { cursor: pointer; }.schulte-cell:active:not(:disabled) { transform: scale(.94); }.schulte-cell:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }.schulte-cell:disabled { opacity: 1; }.schulte-cell span { font-family: "Songti SC", "STSong", serif; font-size: clamp(22px, 6.6vw, 39px); font-weight: 900; }
.schulte-cell.complete { border-color: color-mix(in srgb, var(--green) 24%, transparent); color: color-mix(in srgb, var(--green) 38%, transparent); background: color-mix(in srgb, var(--green) 6%, var(--surface-strong)); box-shadow: none; }.schulte-cell.latest { border-color: color-mix(in srgb, var(--green) 72%, white); box-shadow: 0 0 0 4px color-mix(in srgb, var(--green) 10%, transparent); }.schulte-cell.wrong { z-index: 2; border-color: color-mix(in srgb, var(--red) 72%, var(--line)); color: color-mix(in srgb, var(--red) 72%, var(--text)); background: color-mix(in srgb, var(--red) 14%, var(--surface-inset)); animation: wrong-shake .28s ease; }
@keyframes wrong-shake { 25% { transform: translateX(-4px); } 50% { transform: translateX(4px); } 75% { transform: translateX(-2px); } }
.schulte-hint { min-height: 23px; margin: 0; display: flex; align-items: center; justify-content: center; gap: 6px; color: var(--muted); font-size: 12px; }.schulte-hint:has(svg) { color: var(--red); }
.schulte-metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }.schulte-metrics > div { padding: 13px; text-align: center; }.schulte-metrics small, .schulte-metrics strong { display: block; }.schulte-metrics small { color: var(--muted); }.schulte-metrics strong { margin-top: 4px; color: var(--accent); font-size: 16px; }.schulte-metrics strong.warning { color: var(--red); }
.schulte-result { padding: 25px; display: grid; justify-items: center; gap: 8px; text-align: center; }.schulte-result > span { color: var(--green); font-weight: 850; }.schulte-result > strong { font-family: "Songti SC", "STSong", serif; font-size: clamp(44px, 12vw, 66px); line-height: 1; }.schulte-result > strong small { color: var(--accent); font-size: 19px; }.schulte-result > p { margin: 0 0 8px; color: var(--muted); }.schulte-result > div { width: min(100%, 470px); display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }.schulte-result > div span { border: 1px solid var(--line); border-radius: 11px; padding: 10px 6px; color: var(--muted); font-size: 10px; }.schulte-result > div b { display: block; margin-bottom: 3px; color: var(--text); font-size: 14px; }
@media (max-width: 560px) {
  .schulte-status { grid-template-columns: auto 1fr; }.schulte-status-metrics { grid-column: 1 / 3; display: grid; grid-template-columns: 1fr 1fr; }.schulte-status-metrics > span { justify-content: center; }
  .schulte-intro { min-height: 440px; padding: 24px 14px; }.schulte-preview { width: min(68vw, 245px); }
  .schulte-board-card { padding: 12px; }.schulte-board-card > header { grid-template-columns: auto 1fr; }.schulte-board-card > header p { text-align: right; font-size: 11px; }.schulte-reset-button { grid-column: 1 / 3; justify-content: center; }
  .schulte-grid { gap: 5px; }.schulte-cell { border-radius: 9px; }.schulte-cell span { font-size: clamp(21px, 8vw, 32px); }
  .schulte-metrics { gap: 6px; }.schulte-metrics > div { padding: 11px 4px; }.schulte-metrics strong { font-size: 13px; }
  .schulte-result > div { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  .schulte-cell.wrong { animation: none; }
  .schulte-progress i { transition: none; }
}
</style>
