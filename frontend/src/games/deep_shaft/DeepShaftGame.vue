<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Activity,
  CirclePause,
  CirclePlay,
  Clock3,
  Heart,
  Layers3,
  MapPin,
  ShieldAlert,
  Trophy,
} from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import { currentTheme } from '../../theme'
import type { ArcadeSnapshot } from '../../types/arcade'
import SoloResultCard from '../shared/solo/SoloResultCard.vue'
import DeepShaftControls from './DeepShaftControls.vue'
import {
  CEILING_DEPTH,
  INPUT_LEFT,
  INPUT_RIGHT,
  MAX_TICKS,
  PLAYER_HALF_HEIGHT,
  TARGET_FLOOR,
  TICK_RATE,
  advanceShaftState,
  createShaftState,
  generatePlatforms,
  type PlatformKind,
  type ShaftState,
} from './deepShaftEngine'
import { deepShaftProgress, renderDeepShaft } from './deepShaftRenderer'

interface ServerGame {
  seed: number
  targetFloor: number
  tickRate: number
  maxHealth: number
  deepestFloor: number
  health: number
  elapsedMs: number
  endReason: 'completed' | 'fell' | 'health' | 'timeout' | null
}

type LocalPhase =
  | 'ready'
  | 'countdown'
  | 'playing'
  | 'paused'
  | 'submitting'
  | 'finished'

const COUNTDOWN_STEP_MS = 900

const PLATFORM_COPY: Record<PlatformKind, { label: string; detail: string }> = {
  normal: { label: '稳定平台', detail: '落地恢复 1 点生命' },
  spikes: { label: '尖刺平台', detail: '首次落地损失 3 点生命' },
  crumble: { label: '碎裂平台', detail: '落地后即将崩解' },
  conveyor_left: { label: '左向传送带', detail: '持续牵引探测舱向左' },
  conveyor_right: { label: '右向传送带', detail: '持续牵引探测舱向右' },
  spring: { label: '弹簧平台', detail: '强制向上弹射' },
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const isSpectating = computed(() => props.snapshot.viewer?.mode === 'spectator')
const canvas = ref<HTMLCanvasElement | null>(null)
const phase = ref<LocalPhase>(
  props.snapshot.phase === 'finished' ? 'finished' : 'ready',
)
const countdown = ref(3)
const state = ref<ShaftState>(createShaftState(1))
const inputs = ref<number[]>([])
const heldMask = ref(0)
const submitError = ref<string | null>(null)
const activePointers = new Map<number, number>()
let countdownTimer: number | null = null
let animationFrame: number | null = null
let previousFrame = 0
let accumulator = 0
let submitted = false
let spectatorSequence = 0
let lastPublishedTick = -1

const game = computed(() => props.snapshot.game as unknown as ServerGame)
const hasTargetSpectators = computed(() => props.snapshot.spectators?.some(
  spectator => spectator.targetPlayerId === props.snapshot.self.id,
) ?? false)
const platforms = computed(() => generatePlatforms(game.value.seed))
const elapsedMs = computed(() => Math.round(state.value.tick * 1_000 / TICK_RATE))
const elapsedLabel = computed(() => {
  const total = Math.floor(elapsedMs.value / 1_000)
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`
})
const progress = computed(() => deepShaftProgress(state.value.deepestFloor))
const platformCopy = computed(() => PLATFORM_COPY[state.value.lastLandedKind])
const depthZone = computed(() => {
  if (state.value.deepestFloor >= 75) return '核心深层'
  if (state.value.deepestFloor >= 50) return '高压井段'
  if (state.value.deepestFloor >= 25) return '深层井段'
  return '浅层井段'
})
const ceilingPressure = computed(() => {
  const playerTop = state.value.playerY - PLAYER_HALF_HEIGHT
  const ceiling = state.value.cameraY + CEILING_DEPTH
  return Math.round(Math.max(0, Math.min(1, 1 - (playerTop - ceiling) / 900)) * 100)
})
const pressureCritical = computed(() => ceilingPressure.value >= 58)
const canUseControls = computed(() => (
  !isSpectating.value && ['ready', 'countdown', 'playing'].includes(phase.value)
))

function publishSpectatorState(force = false) {
  if (isSpectating.value || !hasTargetSpectators.value) return
  if (!force && state.value.tick - lastPublishedTick < 6) return
  lastPublishedTick = state.value.tick
  spectatorSequence += 1
  const current = state.value
  arcade.publishSpectatorFrame(spectatorSequence, {
    phase: phase.value,
    countdown: countdown.value,
    shaftState: {
      ...current,
      visitedFloors: [...current.visitedFloors],
      crumbleDue: [...current.crumbleDue.entries()],
      brokenFloors: [...current.brokenFloors],
    },
  })
}

function applySpectatorState(raw: Record<string, unknown>) {
  const nextPhase = raw.phase
  const nextState = raw.shaftState
  if (
    !['ready', 'countdown', 'playing', 'paused', 'submitting', 'finished']
      .includes(String(nextPhase))
    || !nextState
    || typeof nextState !== 'object'
  ) return
  const candidate = nextState as Record<string, unknown>
  if (candidate.seed !== game.value.seed || typeof candidate.tick !== 'number') return
  stopLoops()
  phase.value = nextPhase as LocalPhase
  countdown.value = typeof raw.countdown === 'number' ? raw.countdown : 3
  state.value = {
    ...(candidate as unknown as ShaftState),
    visitedFloors: new Set(
      Array.isArray(candidate.visitedFloors) ? candidate.visitedFloors as number[] : [],
    ),
    crumbleDue: new Map(
      Array.isArray(candidate.crumbleDue)
        ? candidate.crumbleDue as [number, number][]
        : [],
    ),
    brokenFloors: new Set(
      Array.isArray(candidate.brokenFloors) ? candidate.brokenFloors as number[] : [],
    ),
  }
  nextTick(draw)
}

function stopFrame() {
  if (animationFrame !== null) window.cancelAnimationFrame(animationFrame)
  animationFrame = null
}

function stopCountdown() {
  if (countdownTimer !== null) window.clearTimeout(countdownTimer)
  countdownTimer = null
}

function stopLoops() {
  stopFrame()
  stopCountdown()
}

function draw() {
  const element = canvas.value
  if (!element) return
  renderDeepShaft(element, {
    state: state.value,
    platforms: platforms.value,
    theme: currentTheme.value,
    reducedMotion: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches,
  })
}

function freshRun() {
  if (isSpectating.value) return
  stopLoops()
  state.value = createShaftState(game.value.seed)
  inputs.value = []
  heldMask.value = 0
  submitError.value = null
  submitted = false
  activePointers.clear()
  countdown.value = 3
  phase.value = 'ready'
  draw()
  publishSpectatorState(true)
}

function beginPlaying() {
  if (isSpectating.value) return
  stopCountdown()
  phase.value = 'playing'
  previousFrame = performance.now()
  accumulator = 0
  animationFrame = window.requestAnimationFrame(frame)
  publishSpectatorState(true)
}

function stepCountdown() {
  if (isSpectating.value) return
  if (phase.value !== 'countdown') return
  if (countdown.value <= 1) {
    beginPlaying()
    return
  }
  countdown.value -= 1
  publishSpectatorState(true)
  countdownTimer = window.setTimeout(stepCountdown, COUNTDOWN_STEP_MS)
}

function startRun() {
  if (isSpectating.value || phase.value !== 'ready') return
  phase.value = 'countdown'
  countdown.value = 3
  publishSpectatorState(true)
  countdownTimer = window.setTimeout(stepCountdown, COUNTDOWN_STEP_MS)
}

function frame(timestamp: number) {
  if (phase.value !== 'playing') return
  const delta = Math.min(100, Math.max(0, timestamp - previousFrame))
  previousFrame = timestamp
  accumulator += delta
  const tickDuration = 1_000 / TICK_RATE
  while (accumulator >= tickDuration && phase.value === 'playing') {
    accumulator -= tickDuration
    const input = heldMask.value
    inputs.value.push(input)
    state.value = advanceShaftState(state.value, input, platforms.value)
    if (state.value.endReason || state.value.tick >= MAX_TICKS) void submitRun()
  }
  publishSpectatorState()
  draw()
  if (phase.value === 'playing') animationFrame = window.requestAnimationFrame(frame)
}

async function submitRun() {
  if (isSpectating.value || submitted) return
  submitted = true
  phase.value = 'submitting'
  stopLoops()
  heldMask.value = 0
  draw()
  publishSpectatorState(true)
  const successful = await arcade.actionWithResult('finish', { inputs: inputs.value })
  if (!successful) {
    submitError.value = arcade.error ?? '轨迹校验失败，请重新提交'
    submitted = false
  }
}

function togglePause() {
  if (isSpectating.value) return
  if (phase.value === 'playing') {
    phase.value = 'paused'
    heldMask.value = 0
    stopFrame()
    draw()
    publishSpectatorState(true)
  } else if (phase.value === 'paused') {
    phase.value = 'playing'
    previousFrame = performance.now()
    animationFrame = window.requestAnimationFrame(frame)
    publishSpectatorState(true)
  }
}

function keyboardMask(code: string): number {
  if (code === 'ArrowLeft' || code === 'KeyA') return INPUT_LEFT
  if (code === 'ArrowRight' || code === 'KeyD') return INPUT_RIGHT
  return 0
}

function onKeydown(event: KeyboardEvent) {
  if (isSpectating.value) return
  if (event.code === 'Space' || event.code === 'KeyP' || event.code === 'Escape') {
    if (event.repeat) return
    event.preventDefault()
    if (phase.value === 'ready') startRun()
    else if (phase.value === 'playing' || phase.value === 'paused') togglePause()
    return
  }
  const mask = keyboardMask(event.code)
  if (!mask) return
  event.preventDefault()
  if (phase.value === 'ready') startRun()
  heldMask.value |= mask
}

function onKeyup(event: KeyboardEvent) {
  if (isSpectating.value) return
  const mask = keyboardMask(event.code)
  if (!mask) return
  event.preventDefault()
  heldMask.value &= ~mask
}

function onControlDown(direction: -1 | 1, event: PointerEvent) {
  if (isSpectating.value) return
  event.preventDefault()
  if (phase.value === 'ready') startRun()
  const mask = direction < 0 ? INPUT_LEFT : INPUT_RIGHT
  activePointers.set(event.pointerId, mask)
  ;(event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId)
  heldMask.value |= mask
}

function onControlUp(event: PointerEvent) {
  const mask = activePointers.get(event.pointerId)
  if (mask === undefined) return
  activePointers.delete(event.pointerId)
  heldMask.value &= ~mask
}

function clearInput() {
  heldMask.value = 0
  activePointers.clear()
  if (phase.value === 'playing') togglePause()
}

function resizeCanvas() {
  const element = canvas.value
  if (!element) return
  const rect = element.getBoundingClientRect()
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  element.width = Math.max(1, Math.round(rect.width * dpr))
  element.height = Math.max(1, Math.round(rect.height * dpr))
  draw()
}

async function restartChallenge() {
  if (isSpectating.value) return
  await arcade.restartGame()
}

watch(
  () => arcade.spectatorFrame,
  (frame) => {
    if (isSpectating.value && frame) applySpectatorState(frame.state)
  },
)

watch(hasTargetSpectators, () => publishSpectatorState(true))

watch(
  () => [props.snapshot.phase, game.value.seed] as const,
  async ([snapshotPhase], [previousPhase, previousSeed]) => {
    if (snapshotPhase === 'finished') {
      stopLoops()
      phase.value = 'finished'
      return
    }
    if (
      snapshotPhase === 'playing'
      && (previousPhase === 'finished' || game.value.seed !== previousSeed)
    ) {
      await nextTick()
      if (!isSpectating.value) freshRun()
    }
  },
)

watch(currentTheme, draw)

onMounted(() => {
  if (!isSpectating.value) {
    window.addEventListener('keydown', onKeydown, { passive: false })
    window.addEventListener('keyup', onKeyup, { passive: false })
    window.addEventListener('blur', clearInput)
  }
  window.addEventListener('resize', resizeCanvas)
  state.value = createShaftState(game.value.seed)
  resizeCanvas()
  if (props.snapshot.phase === 'playing' && !isSpectating.value) freshRun()
})

onBeforeUnmount(() => {
  stopLoops()
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('keyup', onKeyup)
  window.removeEventListener('blur', clearInput)
  window.removeEventListener('resize', resizeCanvas)
})
</script>

<template>
  <section class="deep-shaft-game">
    <section class="shaft-station surface">
      <div class="shaft-console" :class="[`phase-${phase}`, { 'pressure-critical': pressureCritical }]">
        <canvas ref="canvas" aria-label="百层深井垂直探测区域" />

        <header class="shaft-viewport-hud">
          <div class="shaft-location">
            <MapPin :size="15" />
            <span><small>DEEP SHAFT</small><strong>{{ depthZone }}</strong></span>
          </div>
          <div
            class="shaft-health"
            :class="{ danger: state.health <= 3, warning: state.health > 3 && state.health <= 6 }"
            :aria-label="`生命值 ${state.health} / ${game.maxHealth}`"
          >
            <Heart :size="14" />
            <span>
              <i
                v-for="heart in game.maxHealth"
                :key="heart"
                :class="{ active: heart <= state.health }"
              />
            </span>
          </div>
          <button
            v-if="['playing', 'paused'].includes(phase)"
            class="pause-button"
            type="button"
            :disabled="isSpectating"
            @click="togglePause"
          >
            <CirclePlay v-if="phase === 'paused'" :size="16" />
            <CirclePause v-else :size="16" />
            <span>{{ phase === 'paused' ? '继续' : '暂停' }}</span>
          </button>
        </header>

        <div v-if="pressureCritical && phase === 'playing'" class="ceiling-warning" role="status">
          <ShieldAlert :size="14" />
          <span><small>顶部压力</small><strong>{{ ceilingPressure }}%</strong></span>
        </div>

        <div
          class="shaft-depth-ruler"
          :style="{ '--shaft-progress': `${progress}%` }"
          aria-hidden="true"
        >
          <strong>{{ state.deepestFloor }}F</strong>
          <div class="depth-track"><i /><span v-for="mark in [0, 25, 50, 75, 100]" :key="mark">{{ mark }}</span></div>
        </div>

        <DeepShaftControls
          v-if="snapshot.phase === 'playing'"
          :disabled="!canUseControls"
          @press="onControlDown"
          @release="onControlUp"
        />

        <div v-if="phase === 'ready'" class="shaft-overlay ready-overlay">
          <span class="overlay-kicker">VERTICAL OBSERVATION</span>
          <span class="overlay-mark"><Layers3 :size="28" /></span>
          <strong>准备下潜</strong>
          <p>校准左右落点，穿越五种机械平台并抵达第 100 层。</p>
          <div class="ready-instructions">
            <span><kbd>←</kbd><kbd>→</kbd><small>控制方向</small></span>
            <span><Heart :size="15" /><small>稳定平台恢复生命</small></span>
            <span><ShieldAlert :size="15" /><small>远离顶部压力区</small></span>
          </div>
          <button type="button" :disabled="isSpectating" @click="startRun">启动探测舱</button>
        </div>

        <div v-else-if="phase === 'countdown'" class="shaft-overlay countdown-overlay" aria-live="assertive">
          <span>DESCENT SEQUENCE</span>
          <strong>{{ countdown }}</strong>
          <small>保持视线，准备控制落点</small>
        </div>

        <div v-else-if="phase === 'paused'" class="shaft-overlay compact-overlay">
          <CirclePause :size="34" />
          <strong>探测暂停</strong>
          <span>继续后井道压力与平台运动将同步恢复</span>
          <button type="button" :disabled="isSpectating" @click="togglePause">继续下潜</button>
        </div>

        <div v-else-if="phase === 'submitting'" class="shaft-overlay compact-overlay">
          <ShieldAlert :size="34" />
          <strong>{{ state.endReason === 'completed' ? '百层抵达' : '本轮结束' }}</strong>
          <span>{{ submitError || `正在校验 ${inputs.length.toLocaleString()} 帧左右输入…` }}</span>
          <button v-if="submitError" type="button" @click="submitRun">重新校验</button>
        </div>

        <div v-else-if="phase === 'finished'" class="shaft-overlay compact-overlay finished-overlay">
          <Trophy v-if="game.endReason === 'completed'" :size="38" />
          <Heart v-else :size="38" />
          <strong>{{ game.endReason === 'completed' ? '百层通关' : `最深 ${game.deepestFloor} 层` }}</strong>
          <span>{{ snapshot.winReason }}</span>
        </div>
      </div>

      <aside class="shaft-instruments" aria-label="深井观测仪表">
        <header>
          <span>OBSERVATION DECK</span>
          <strong>垂直观测仪</strong>
        </header>

        <section class="depth-instrument">
          <small>当前深度</small>
          <strong>{{ String(state.deepestFloor).padStart(2, '0') }}</strong>
          <span>/ {{ TARGET_FLOOR }} 层</span>
          <i><b :style="{ width: `${progress}%` }" /></i>
        </section>

        <dl class="shaft-readouts">
          <div><dt><Clock3 :size="14" />运行时间</dt><dd>{{ elapsedLabel }}</dd></div>
          <div><dt><Activity :size="14" />顶部压力</dt><dd :class="{ critical: pressureCritical }">{{ ceilingPressure }}%</dd></div>
        </dl>

        <section class="platform-readout">
          <small>接触平台</small>
          <strong>{{ platformCopy.label }}</strong>
          <span>{{ platformCopy.detail }}</span>
        </section>

        <section class="platform-legend">
          <small>平台识别</small>
          <ul>
            <li class="normal"><i />稳定</li>
            <li class="spikes"><i />尖刺</li>
            <li class="crumble"><i />碎裂</li>
            <li class="conveyor"><i />传送</li>
            <li class="spring"><i />弹簧</li>
          </ul>
        </section>

        <p class="shaft-keyboard-hint"><kbd>A</kbd><kbd>D</kbd><span>或方向键控制</span><kbd>Space</kbd><span>暂停</span></p>
      </aside>
    </section>

    <p class="shaft-mobile-hint">按住左右控制区调整落点 · 稳定平台回血 · 不要被顶部追上</p>

    <SoloResultCard
      v-if="snapshot.phase === 'finished'"
      :eyebrow="game.endReason === 'completed' ? '深井征服者' : '本轮探索结束'"
      :title="game.endReason === 'completed' ? '成功抵达第一百层' : `最深抵达第 ${game.deepestFloor} 层`"
      :score="String(game.deepestFloor)"
      score-unit="层"
      :description="snapshot.winReason"
      :tone="game.endReason === 'completed' ? 'success' : 'danger'"
      :metrics="[
        { label: '剩余生命', value: `${game.health} / ${game.maxHealth}` },
        { label: '挑战用时', value: `${(game.elapsedMs / 1_000).toFixed(1)} 秒` },
        { label: '轨迹校验', value: `${game.tickRate} Hz` },
      ]"
      :can-restart="snapshot.actions.canRestart"
      :busy="arcade.busy"
      restart-label="再下百层"
      @restart="restartChallenge"
    />
  </section>
</template>

<style scoped>
.deep-shaft-game {
  --shaft-accent: var(--accent);
  --shaft-danger: var(--red);
  width: min(100%, 980px);
  display: grid;
  gap: 14px;
  margin: 0 auto;
}

.shaft-station {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 244px;
  gap: 14px;
  padding: 14px;
  overflow: hidden;
  border-color: color-mix(in srgb, var(--shaft-accent) 24%, var(--line));
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--shaft-accent) 3%, transparent), transparent 44%),
    var(--material-pattern),
    var(--surface);
}

.shaft-console {
  position: relative;
  width: 100%;
  min-width: 0;
  aspect-ratio: 4 / 5;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--shaft-accent) 40%, var(--line));
  border-radius: calc(var(--radius-panel) - 4px);
  background: var(--surface-inset);
  box-shadow:
    inset 0 0 0 1px color-mix(in srgb, white 9%, transparent),
    inset 0 0 70px color-mix(in srgb, var(--bg) 42%, transparent),
    var(--shadow-contact);
  isolation: isolate;
}
.shaft-console::after {
  position: absolute;
  z-index: 6;
  inset: 7px;
  border: 1px solid color-mix(in srgb, var(--shaft-accent) 14%, transparent);
  border-radius: calc(var(--radius-panel) - 10px);
  content: '';
  pointer-events: none;
}
.shaft-console canvas { width: 100%; height: 100%; display: block; }

.shaft-viewport-hud {
  position: absolute;
  z-index: 3;
  top: 14px;
  right: 14px;
  left: 14px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 9px;
  pointer-events: none;
}
.shaft-viewport-hud > * {
  border: 1px solid color-mix(in srgb, var(--shaft-accent) 22%, var(--line));
  color: var(--text);
  background: color-mix(in srgb, var(--surface-primary) 76%, transparent);
  box-shadow: inset 0 1px 0 color-mix(in srgb, white 12%, transparent);
  backdrop-filter: blur(11px) saturate(1.08);
}
.shaft-location {
  min-width: 0;
  width: fit-content;
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 12px;
  padding: 7px 10px;
  color: var(--shaft-accent);
}
.shaft-location span { min-width: 0; display: grid; gap: 1px; }
.shaft-location small { color: var(--shaft-accent); font-size: 6px; font-weight: 950; letter-spacing: .14em; }
.shaft-location strong { overflow: hidden; color: var(--text); font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }

.shaft-health {
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  padding: 8px 10px;
  color: var(--shaft-danger);
}
.shaft-health span { display: flex; gap: 3px; }
.shaft-health i { width: 4px; height: 10px; border-radius: 4px; background: color-mix(in srgb, var(--muted) 23%, transparent); }
.shaft-health i.active { background: var(--shaft-accent); box-shadow: 0 0 8px color-mix(in srgb, var(--shaft-accent) 55%, transparent); }
.shaft-health.warning i.active { background: var(--accent); box-shadow: 0 0 8px color-mix(in srgb, var(--accent) 42%, transparent); }
.shaft-health.danger i.active { background: var(--shaft-danger); box-shadow: 0 0 8px color-mix(in srgb, var(--shaft-danger) 55%, transparent); }

.pause-button {
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-radius: 999px;
  padding: 0 11px;
  font-size: 9px;
  font-weight: 850;
  pointer-events: auto;
  cursor: pointer;
}

.ceiling-warning {
  position: absolute;
  z-index: 3;
  top: 66px;
  left: 14px;
  display: flex;
  align-items: center;
  gap: 7px;
  border: 1px solid color-mix(in srgb, var(--shaft-danger) 55%, var(--line));
  border-radius: 11px;
  padding: 7px 9px;
  color: var(--shaft-danger);
  background: color-mix(in srgb, var(--shaft-danger) 10%, var(--surface-primary));
  box-shadow: 0 0 20px color-mix(in srgb, var(--shaft-danger) 14%, transparent);
  backdrop-filter: blur(10px);
}
.ceiling-warning span { display: grid; }
.ceiling-warning small { font-size: 6px; font-weight: 900; letter-spacing: .1em; }
.ceiling-warning strong { font-size: 10px; }

.shaft-depth-ruler {
  position: absolute;
  z-index: 3;
  top: 78px;
  right: 16px;
  bottom: 78px;
  width: 28px;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  justify-items: center;
  gap: 5px;
  color: var(--shaft-accent);
  pointer-events: none;
}
.shaft-depth-ruler > strong {
  border: 1px solid color-mix(in srgb, var(--shaft-accent) 24%, var(--line));
  border-radius: 999px;
  padding: 4px 6px;
  background: color-mix(in srgb, var(--surface-primary) 76%, transparent);
  font-size: 8px;
  backdrop-filter: blur(9px);
}
.depth-track { position: relative; width: 4px; height: 100%; border-radius: 999px; background: color-mix(in srgb, var(--text) 14%, transparent); }
.depth-track::before {
  position: absolute;
  inset: 0;
  height: var(--shaft-progress);
  border-radius: inherit;
  background: linear-gradient(var(--shaft-accent), color-mix(in srgb, var(--shaft-accent) 42%, var(--accent-secondary)));
  box-shadow: 0 0 12px color-mix(in srgb, var(--shaft-accent) 44%, transparent);
  content: '';
}
.depth-track i {
  position: absolute;
  z-index: 1;
  top: var(--shaft-progress);
  left: 50%;
  width: 9px;
  aspect-ratio: 1;
  border: 2px solid color-mix(in srgb, var(--surface-primary) 82%, transparent);
  border-radius: 50%;
  background: var(--shaft-accent);
  box-shadow: 0 0 12px var(--shaft-accent);
  transform: translate(-50%, -50%);
}
.depth-track span { position: absolute; left: -18px; color: color-mix(in srgb, var(--text) 62%, transparent); font-size: 6px; transform: translateY(-50%); }
.depth-track span:nth-of-type(1) { top: 0; }
.depth-track span:nth-of-type(2) { top: 25%; }
.depth-track span:nth-of-type(3) { top: 50%; }
.depth-track span:nth-of-type(4) { top: 75%; }
.depth-track span:nth-of-type(5) { top: 100%; }

.shaft-overlay {
  position: absolute;
  z-index: 5;
  inset: 0;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 9px;
  padding: clamp(24px, 6vw, 48px);
  color: var(--text);
  background:
    radial-gradient(circle at 50% 42%, color-mix(in srgb, var(--shaft-accent) 12%, transparent), transparent 34%),
    color-mix(in srgb, var(--surface-primary) 74%, transparent);
  text-align: center;
  backdrop-filter: blur(8px) saturate(.86);
}
.shaft-overlay > strong { font-family: "Songti SC", "STSong", serif; }
.shaft-overlay button {
  min-height: 44px;
  margin-top: 6px;
  border: 1px solid color-mix(in srgb, var(--shaft-accent) 56%, var(--line));
  border-radius: 12px;
  padding: 0 18px;
  color: var(--text);
  background: color-mix(in srgb, var(--shaft-accent) 13%, var(--surface-elevated));
  box-shadow: inset 0 1px 0 color-mix(in srgb, white 24%, transparent), var(--shadow-contact);
  font-weight: 850;
  cursor: pointer;
}
.overlay-kicker { color: var(--shaft-accent); font-size: 7px; font-weight: 950; letter-spacing: .18em; }
.overlay-mark {
  width: 64px;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  margin: 7px 0 3px;
  border: 1px solid color-mix(in srgb, var(--shaft-accent) 48%, var(--line));
  border-radius: 22px;
  color: var(--shaft-accent);
  background: color-mix(in srgb, var(--shaft-accent) 10%, var(--surface-elevated));
  box-shadow: inset 0 1px 0 color-mix(in srgb, white 22%, transparent), 0 0 30px color-mix(in srgb, var(--shaft-accent) 15%, transparent);
}
.ready-overlay > strong { font-size: clamp(32px, 6vw, 52px); }
.ready-overlay > p { max-width: 430px; margin: 0; color: var(--text-soft); font-size: 11px; line-height: 1.65; }
.ready-instructions { width: min(100%, 450px); display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; margin: 8px 0 2px; }
.ready-instructions > span {
  min-width: 0;
  min-height: 54px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  align-content: center;
  gap: 4px;
  border: 1px solid color-mix(in srgb, var(--shaft-accent) 18%, var(--line));
  border-radius: 11px;
  padding: 7px;
  color: var(--shaft-accent);
  background: color-mix(in srgb, var(--surface-elevated) 48%, transparent);
}
.ready-instructions small { flex-basis: 100%; color: var(--muted); font-size: 7px; }
.ready-instructions kbd,
.shaft-keyboard-hint kbd {
  border: 1px solid color-mix(in srgb, var(--shaft-accent) 24%, var(--line));
  border-bottom-width: 2px;
  border-radius: 5px;
  padding: 2px 5px;
  color: var(--text);
  background: var(--surface-inset);
  font: inherit;
  font-weight: 900;
}

.countdown-overlay { background: radial-gradient(circle, color-mix(in srgb, var(--shaft-accent) 17%, transparent), transparent 34%); backdrop-filter: none; }
.countdown-overlay > span { color: var(--shaft-accent); font-size: 8px; font-weight: 950; letter-spacing: .18em; }
.countdown-overlay > strong {
  color: var(--shaft-accent);
  font-size: clamp(104px, 24vw, 172px);
  line-height: .88;
  text-shadow: 0 0 42px color-mix(in srgb, var(--shaft-accent) 48%, transparent);
}
.countdown-overlay > small { color: var(--text-soft); font-weight: 800; letter-spacing: .08em; }

.compact-overlay > svg { color: var(--shaft-accent); filter: drop-shadow(0 0 14px color-mix(in srgb, var(--shaft-accent) 58%, transparent)); }
.compact-overlay > strong { font-size: clamp(28px, 6vw, 48px); }
.compact-overlay > span { max-width: 430px; color: var(--text-soft); font-size: 11px; line-height: 1.65; }
.finished-overlay > svg { color: var(--accent); }

.shaft-instruments {
  min-width: 0;
  display: grid;
  grid-template-rows: auto auto auto auto 1fr auto;
  align-content: start;
  gap: 10px;
}
.shaft-instruments > header { padding: 4px 2px 7px; border-bottom: 1px solid var(--line); }
.shaft-instruments > header span,
.shaft-instruments > header strong { display: block; }
.shaft-instruments > header span { color: var(--shaft-accent); font-size: 7px; font-weight: 950; letter-spacing: .16em; }
.shaft-instruments > header strong { margin-top: 4px; font-size: 16px; }
.shaft-instruments section,
.shaft-readouts > div {
  border: 1px solid color-mix(in srgb, var(--shaft-accent) 14%, var(--line));
  border-radius: 13px;
  background: color-mix(in srgb, var(--surface-elevated) 70%, transparent);
  box-shadow: inset 0 1px 0 color-mix(in srgb, white 10%, transparent);
}
.depth-instrument { display: grid; grid-template-columns: 1fr auto; align-items: end; gap: 2px 7px; padding: 13px; }
.depth-instrument small { grid-column: 1 / -1; color: var(--muted); font-size: 8px; }
.depth-instrument strong { color: var(--shaft-accent); font-size: 42px; font-variant-numeric: tabular-nums; line-height: 1; }
.depth-instrument span { padding-bottom: 4px; color: var(--muted); font-size: 9px; }
.depth-instrument i { grid-column: 1 / -1; height: 4px; margin-top: 8px; overflow: hidden; border-radius: 999px; background: color-mix(in srgb, var(--muted) 20%, transparent); }
.depth-instrument b { display: block; height: 100%; border-radius: inherit; background: var(--shaft-accent); box-shadow: 0 0 11px color-mix(in srgb, var(--shaft-accent) 50%, transparent); }

.shaft-readouts { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 0; }
.shaft-readouts > div { min-width: 0; padding: 10px; }
.shaft-readouts dt { display: flex; align-items: center; gap: 5px; color: var(--muted); font-size: 7px; }
.shaft-readouts dd { margin: 6px 0 0; color: var(--text); font-size: 14px; font-weight: 900; font-variant-numeric: tabular-nums; }
.shaft-readouts dd.critical { color: var(--shaft-danger); }

.platform-readout { display: grid; gap: 4px; padding: 11px 12px; }
.platform-readout small,
.platform-legend > small { color: var(--shaft-accent); font-size: 7px; font-weight: 900; letter-spacing: .1em; }
.platform-readout strong { font-size: 13px; }
.platform-readout span { color: var(--muted); font-size: 8px; line-height: 1.5; }

.platform-legend { align-self: stretch; padding: 11px 12px; }
.platform-legend ul { display: grid; gap: 8px; margin: 10px 0 0; padding: 0; list-style: none; }
.platform-legend li { display: grid; grid-template-columns: 22px 1fr; align-items: center; gap: 7px; color: var(--text-soft); font-size: 8px; }
.platform-legend i { height: 7px; border: 1px solid color-mix(in srgb, white 25%, transparent); border-radius: 3px; background: #73949e; box-shadow: inset 0 1px 0 #fff4; }
.platform-legend .spikes i { background: #b26a71; }
.platform-legend .crumble i { background: #a48262; }
.platform-legend .conveyor i { background: #629b9d; }
.platform-legend .spring i { background: #8174a2; }

.shaft-keyboard-hint { display: grid; grid-template-columns: auto auto 1fr; align-items: center; gap: 5px; margin: 0; color: var(--muted); font-size: 7px; }
.shaft-keyboard-hint kbd:nth-of-type(3) { grid-column: 1 / 3; text-align: center; }
.shaft-mobile-hint { display: none; margin: 0; color: var(--muted); font-size: 8px; text-align: center; line-height: 1.6; }

@media (max-width: 720px) {
  .deep-shaft-game { gap: 9px; }
  .shaft-station { display: block; padding: 6px; border-radius: 18px; }
  .shaft-console { aspect-ratio: 3 / 4; border-radius: 14px; }
  .shaft-console::after { inset: 5px; border-radius: 10px; }
  .shaft-instruments { display: none; }
  .shaft-mobile-hint { display: block; }
  .shaft-viewport-hud { top: 10px; right: 10px; left: 10px; gap: 6px; }
  .shaft-location { padding: 6px 8px; }
  .shaft-location svg { display: none; }
  .shaft-health { padding: 7px 8px; }
  .shaft-health i { width: 3px; height: 8px; }
  .pause-button { width: 34px; padding: 0; }
  .pause-button span { display: none; }
  .ceiling-warning { top: 56px; left: 10px; }
  .shaft-depth-ruler { top: 66px; right: 10px; bottom: 82px; }
  .shaft-overlay { padding: 20px; }
  .overlay-mark { width: 52px; border-radius: 18px; }
  .ready-overlay > strong { font-size: 31px; }
  .ready-overlay > p { max-width: 310px; font-size: 9px; }
  .ready-instructions { max-width: 330px; gap: 5px; }
  .ready-instructions > span { min-height: 47px; padding: 5px; }
  .ready-instructions small { font-size: 6px; }
}

@media (max-width: 380px) {
  .ready-instructions { grid-template-columns: 1fr 1fr; }
  .ready-instructions > span:last-child { grid-column: 1 / -1; min-height: 40px; }
  .overlay-mark { margin: 2px 0 0; }
}

@media (orientation: landscape) and (max-height: 600px) {
  .shaft-station { grid-template-columns: minmax(0, 1fr) 214px; }
  .shaft-console { width: auto; height: min(76dvh, 520px); aspect-ratio: 4 / 3; justify-self: center; }
  .shaft-instruments { display: grid; }
  .platform-legend { display: none; }
  .shaft-mobile-hint { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .shaft-overlay { backdrop-filter: none; }
}
</style>
