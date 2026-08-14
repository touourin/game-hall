<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Activity, CircleAlert, Gauge, Zap } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import SoloMetricGrid from '../shared/solo/SoloMetricGrid.vue'
import SoloResultCard from '../shared/solo/SoloResultCard.vue'

type TestStage =
  | 'intro'
  | 'waiting'
  | 'ready'
  | 'saving'
  | 'result'
  | 'false-start'
  | 'finished'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const stage = ref<TestStage>(props.snapshot.phase === 'finished' ? 'finished' : 'intro')
const localResult = ref<number | null>(null)
const signalStartedAt = ref(0)
let signalTimer: ReturnType<typeof setTimeout> | null = null
let advanceTimer: ReturnType<typeof setTimeout> | null = null
let signalFrame: number | null = null

const game = computed(() => props.snapshot.game as {
  roundsRequired: number
  resultsMs: number[]
  roundNumber: number
  bestMs: number | null
  averageMs: number | null
})
const completedRounds = computed(() => game.value.resultsMs.length)
const progressLabel = computed(() =>
  props.snapshot.phase === 'finished'
    ? '三轮完成'
    : `第 ${game.value.roundNumber} / ${game.value.roundsRequired} 轮`,
)
const buttonLabel = computed(() => {
  if (stage.value === 'waiting') return '等待变色…'
  if (stage.value === 'ready') return '现在！'
  if (stage.value === 'saving') return '记录中…'
  if (stage.value === 'result') return `${localResult.value} ms`
  if (stage.value === 'false-start') return '抢跑了'
  if (stage.value === 'finished') return '测试完成'
  return completedRounds.value ? '继续测试' : '开始测试'
})
const instruction = computed(() => {
  if (stage.value === 'waiting') return '保持专注，不要提前操作'
  if (stage.value === 'ready') return '按空格键，手机可直接点击'
  if (stage.value === 'saving') return '正在保存本轮反应时间'
  if (stage.value === 'result') return '很好，下一轮马上开始'
  if (stage.value === 'false-start') return '信号还没出现，三轮已重新开始'
  if (stage.value === 'finished') return '成绩已经保存，可以再测一次'
  return '看到按钮变绿后立即操作'
})

function clearTimers() {
  if (signalTimer !== null) window.clearTimeout(signalTimer)
  if (advanceTimer !== null) window.clearTimeout(advanceTimer)
  if (signalFrame !== null) window.cancelAnimationFrame(signalFrame)
  signalTimer = null
  advanceTimer = null
  signalFrame = null
}

function randomDelay(): number {
  const values = new Uint32Array(1)
  window.crypto.getRandomValues(values)
  return 1_500 + (values[0] % 2_501)
}

function beginRound() {
  if (props.snapshot.phase !== 'playing' || arcade.busy) return
  clearTimers()
  localResult.value = null
  stage.value = 'waiting'
  signalTimer = window.setTimeout(() => {
    signalTimer = null
    signalFrame = window.requestAnimationFrame((frameTimestamp) => {
      signalFrame = null
      signalStartedAt.value = frameTimestamp
      stage.value = 'ready'
    })
  }, randomDelay())
}

async function falseStart() {
  clearTimers()
  stage.value = 'false-start'
  await arcade.action('false_start')
  if (arcade.error) {
    stage.value = 'intro'
    return
  }
  advanceTimer = window.setTimeout(beginRound, 1_050)
}

function normalizedInputTimestamp(timestamp: number): number {
  const now = performance.now()
  return Number.isFinite(timestamp) && timestamp > 0 && Math.abs(timestamp - now) < 1_000
    ? timestamp
    : now
}

async function recordReaction(inputTimestamp: number) {
  const elapsedMs = Math.max(1, Math.round(inputTimestamp - signalStartedAt.value))
  localResult.value = elapsedMs
  stage.value = 'saving'
  const previousCount = completedRounds.value
  await arcade.action('record', { elapsedMs })
  if (arcade.error || completedRounds.value === previousCount) {
    stage.value = 'intro'
    return
  }
  if (props.snapshot.phase === 'finished') {
    stage.value = 'finished'
    return
  }
  stage.value = 'result'
  advanceTimer = window.setTimeout(beginRound, 1_050)
}

function activate(inputTimestamp = performance.now()) {
  if (stage.value === 'intro') {
    beginRound()
    return
  }
  if (stage.value === 'waiting') {
    void falseStart()
    return
  }
  if (stage.value === 'ready') void recordReaction(inputTimestamp)
}

function onPointerDown(event: PointerEvent) {
  if (event.isPrimary === false || (event.button ?? 0) !== 0) return
  activate(normalizedInputTimestamp(event.timeStamp))
}

function onAccessibleClick(event: MouseEvent) {
  if (event.detail !== 0) return
  activate(normalizedInputTimestamp(event.timeStamp))
}

async function restartTest() {
  await arcade.restartGame()
}

function onKeydown(event: KeyboardEvent) {
  if (event.code !== 'Space' || event.repeat) return
  if (!['intro', 'waiting', 'ready'].includes(stage.value)) return
  event.preventDefault()
  activate(normalizedInputTimestamp(event.timeStamp))
}

watch(
  () => props.snapshot.phase,
  (phase) => {
    if (phase === 'finished') {
      clearTimers()
      stage.value = 'finished'
    } else if (stage.value === 'finished') {
      localResult.value = null
      stage.value = 'intro'
    }
  },
)

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  clearTimers()
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <section class="reaction-game">
    <header class="surface reaction-status">
      <span><Activity :size="22" /></span>
      <div>
        <small>REACTION TEST</small>
        <strong>{{ progressLabel }}</strong>
      </div>
      <div class="round-dots" aria-label="三轮测试进度">
        <i
          v-for="round in game.roundsRequired"
          :key="round"
          :class="{ complete: round <= completedRounds, current: round === game.roundNumber && snapshot.phase === 'playing' }"
        />
      </div>
    </header>

    <div class="surface reaction-panel" :class="`stage-${stage}`">
      <div class="reaction-copy">
        <span v-if="stage === 'false-start'" class="reaction-copy-icon warning"><CircleAlert :size="25" /></span>
        <span v-else class="reaction-copy-icon"><Zap :size="25" /></span>
        <div>
          <strong>{{ buttonLabel }}</strong>
          <small>{{ instruction }}</small>
        </div>
      </div>

      <div
        role="button"
        tabindex="0"
        class="reaction-trigger"
        :class="[stage, { inactive: ['saving', 'result', 'false-start', 'finished'].includes(stage) }]"
        :aria-disabled="['saving', 'result', 'false-start', 'finished'].includes(stage)"
        :aria-label="buttonLabel"
        @pointerdown="onPointerDown"
        @click="onAccessibleClick"
      >
        <Zap v-if="stage === 'ready'" :size="34" />
        <Gauge v-else :size="34" />
        <strong>{{ buttonLabel }}</strong>
        <small v-if="stage === 'ready'">SPACE</small>
      </div>

      <p class="keyboard-hint"><kbd>SPACE</kbd> 电脑按空格 · 手机点击按钮</p>
    </div>

    <SoloMetricGrid
      class="reaction-metrics"
      aria-label="当前测试成绩"
      :items="[
        { label: '已完成', value: `${completedRounds} / ${game.roundsRequired}` },
        { label: '当前最佳', value: game.bestMs === null ? '—' : `${game.bestMs} ms` },
        { label: '当前平均', value: game.averageMs === null ? '—' : `${game.averageMs} ms` },
      ]"
    />

    <SoloResultCard
      v-if="snapshot.phase === 'finished'"
      class="reaction-result"
      eyebrow="三轮测试完成"
      title="平均反应时间"
      :score="game.averageMs"
      score-unit="ms"
      :metrics="game.resultsMs.map((result, index) => ({ label: `第 ${index + 1} 轮`, value: `${result} ms` }))"
      :can-restart="snapshot.actions.canRestart"
      restart-label="再测一次"
      @restart="restartTest"
    />
  </section>
</template>

<style scoped>
.reaction-game { width: min(100%, 720px); margin: 0 auto; display: grid; gap: 16px; }
.reaction-status { padding: 14px 16px; display: grid; grid-template-columns: auto 1fr auto; gap: 12px; align-items: center; }
.reaction-status > span { width: 42px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 12px; color: #8fe0bd; background: #62c69b18; }
.reaction-status small, .reaction-status strong { display: block; }.reaction-status small { color: var(--gold); font-size: 9px; font-weight: 850; letter-spacing: .15em; }.reaction-status strong { margin-top: 3px; }
.round-dots { display: flex; gap: 7px; }.round-dots i { width: 9px; aspect-ratio: 1; border: 1px solid var(--line); border-radius: 50%; background: var(--bg); }.round-dots i.current { border-color: var(--gold); box-shadow: 0 0 0 4px color-mix(in srgb, var(--gold) 9%, transparent); }.round-dots i.complete { border-color: var(--green); background: var(--green); }
.reaction-panel { min-height: 430px; padding: clamp(22px, 5vw, 38px); display: grid; place-items: center; align-content: center; gap: 28px; overflow: hidden; text-align: center; transition: border-color .18s, background .18s; }
.reaction-panel.stage-ready { border-color: #76d9ae78; background: radial-gradient(circle at 50% 55%, #62c69b24, transparent 46%), var(--surface); transition: none; }
.reaction-panel.stage-false-start { border-color: #e1727266; background: radial-gradient(circle at 50% 55%, #e1727218, transparent 46%), var(--surface); }
.reaction-copy { min-height: 58px; display: flex; align-items: center; justify-content: center; gap: 11px; }.reaction-copy-icon { width: 46px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 14px; color: #8fe0bd; background: #62c69b16; }.reaction-copy-icon.warning { color: #f0a3a3; background: #e1727216; }.reaction-copy strong, .reaction-copy small { display: block; text-align: left; }.reaction-copy strong { font-family: "Songti SC", "STSong", serif; font-size: 22px; }.reaction-copy small { margin-top: 4px; color: var(--muted); }
.reaction-trigger { position: relative; width: min(72vw, 300px); aspect-ratio: 1; display: grid; place-items: center; align-content: center; gap: 10px; border: 1px solid color-mix(in srgb, var(--gold) 32%, transparent); border-radius: 48px; color: var(--gold); background: linear-gradient(145deg, color-mix(in srgb, var(--gold) 11%, transparent), color-mix(in srgb, var(--bg) 34%, transparent)), var(--surface-strong); box-shadow: inset 0 1px 0 #ffffff14, 0 24px 55px #0007; cursor: pointer; overflow: hidden; transition: transform .14s; touch-action: manipulation; user-select: none; }
.reaction-trigger::before { content: ''; position: absolute; inset: 0; border-radius: inherit; background: transparent; }
.reaction-trigger > svg, .reaction-trigger > strong, .reaction-trigger > small { position: relative; z-index: 1; }
.reaction-trigger:focus-visible { outline: 2px solid var(--gold); outline-offset: 4px; }
.reaction-trigger:hover:not(.inactive) { transform: translateY(-2px); }.reaction-trigger:active:not(.inactive) { transform: scale(.975); }.reaction-trigger.inactive { cursor: default; }
.reaction-trigger strong { font-family: "Songti SC", "STSong", serif; font-size: clamp(23px, 7vw, 34px); }.reaction-trigger small { font-size: 10px; font-weight: 900; letter-spacing: .18em; }
.reaction-trigger.waiting { border-color: var(--line); color: var(--muted); background: var(--surface-strong); animation: waiting-pulse 1.4s ease-in-out infinite; }
.reaction-trigger.ready { border-color: #a7efd0; color: #06231c; box-shadow: 0 0 0 10px #62c69b14, 0 24px 70px #3ab18442; }
.reaction-trigger.ready::before { background: var(--green); }
.reaction-trigger.false-start { color: #f3b1b1; border-color: #e1727266; background: #6a292d55; }.reaction-trigger.saving, .reaction-trigger.result, .reaction-trigger.finished { opacity: 1; }
.keyboard-hint { margin: 0; color: var(--muted); font-size: 11px; }.keyboard-hint kbd { margin-right: 3px; border: 1px solid var(--line); border-bottom-width: 3px; border-radius: 7px; padding: 4px 7px; color: var(--text); background: #061719; font: inherit; font-weight: 850; }
.reaction-metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }.reaction-metrics > div { padding: 14px; text-align: center; }.reaction-metrics small, .reaction-metrics strong { display: block; }.reaction-metrics small { color: var(--muted); }.reaction-metrics strong { margin-top: 5px; color: var(--gold); font-size: 17px; }
.reaction-result { padding: 24px; display: grid; justify-items: center; gap: 8px; text-align: center; }.reaction-result > span { color: #8fe0bd; font-weight: 850; }.reaction-result > strong { color: var(--text); font-family: "Songti SC", "STSong", serif; font-size: clamp(46px, 12vw, 68px); line-height: 1; }.reaction-result > strong small { color: var(--gold); font-family: inherit; font-size: 20px; }.reaction-result > p { margin: 0 0 8px; color: var(--muted); }.reaction-result > div { width: min(100%, 430px); display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }.reaction-result > div span { padding: 10px 7px; border: 1px solid var(--line); border-radius: 11px; color: var(--muted); font-size: 10px; }.reaction-result > div b { display: block; margin-top: 3px; color: var(--text); font-size: 13px; }.reaction-result .ui-button--primary { margin-top: 12px; }
@keyframes waiting-pulse { 50% { border-color: color-mix(in srgb, var(--gold) 22%, transparent); box-shadow: inset 0 1px 0 #ffffff12, 0 18px 45px #0005; } }
@media (max-width: 520px) { .reaction-panel { min-height: 390px; padding: 22px 14px; }.reaction-trigger { width: min(72vw, 270px); }.reaction-copy strong { font-size: 19px; }.reaction-metrics { gap: 7px; }.reaction-metrics > div { padding: 12px 6px; }.reaction-metrics strong { font-size: 14px; } }
@media (prefers-reduced-motion: reduce) { .reaction-trigger.waiting { animation: none; } }
</style>
