<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  CircleX,
  ScanLine,
  ShieldCheck,
  Sparkles,
} from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import { currentTheme } from '../../theme'
import type { ArcadeSnapshot } from '../../types/arcade'
import SoloMetricGrid from '../shared/solo/SoloMetricGrid.vue'
import SoloResultCard from '../shared/solo/SoloResultCard.vue'
import {
  BOARD_HEIGHT,
  BOARD_WIDTH,
  BOUNDARY_SIDES,
  BOUNDARY_ZONE_X,
  BOUNDARY_ZONE_Y,
  INPUT_DOWN,
  INPUT_LEFT,
  INPUT_RIGHT,
  INPUT_UP,
  PLAYER_HIT_RADIUS,
  PLAYER_RADIUS,
  PULSE_INTERVAL_TICKS,
  TICK_RATE,
  advanceCrossingState,
  boundaryWallDepth,
  buildPulsePlan,
  createCrossingState,
  pulseFronts,
  type BoundarySide,
  type CrossingProfile,
  type CrossingState,
} from './crossingEngine'
import {
  criticalCrossingPalette,
  type CriticalCrossingPalette,
} from './criticalCrossingPalette'

interface ServerGame {
  difficulty: '5s' | '8s' | '10s'
  difficultyLabel: string
  seed: number
  durationMs: number
  tickRate: number
  pulseCount: number
  collisionGraceMs: number
  pulseWarningMs: number
  boundaryPressureMs: number
  profile: CrossingProfile
  elapsedMs: number
  crossed: boolean | null
  collisionTick: number | null
  collisionKind: 'pulse' | 'boundary' | null
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const isSpectating = computed(() => props.snapshot.viewer?.mode === 'spectator')
const canvas = ref<HTMLCanvasElement | null>(null)
const phase = ref<'ready' | 'playing' | 'submitting' | 'finished'>(
  props.snapshot.phase === 'finished' ? 'finished' : 'ready',
)
const readyCount = ref(3)
const crossingState = ref<CrossingState>(createCrossingState())
const inputs = ref<number[]>([])
const heldMask = ref(0)
const localElapsedMs = ref(0)
const submitError = ref<string | null>(null)
const activePointers = new Map<number, number>()
let readyTimer: number | null = null
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
const durationSeconds = computed(() => Math.round(game.value.durationMs / 1_000))
const targetTicks = computed(() => durationSeconds.value * TICK_RATE)
const pulsePlan = computed(() => buildPulsePlan(
  game.value.seed,
  game.value.pulseCount,
))
const remainingMs = computed(() => Math.max(
  0,
  game.value.durationMs - localElapsedMs.value,
))
const remainingLabel = computed(() => (remainingMs.value / 1_000).toFixed(2))
const boundaryLockLabel = computed(() => (
  game.value.profile.boundaryPressureLimit / TICK_RATE
).toFixed(2))
const pulseIndex = computed(() => Math.min(
  Math.floor(crossingState.value.tick / PULSE_INTERVAL_TICKS),
  Math.max(0, game.value.pulseCount - 1),
))
const pulseTick = computed(() => crossingState.value.tick % PULSE_INTERVAL_TICKS)
const currentPulse = computed(() => pulsePlan.value[pulseIndex.value]!)
const isPulseWarning = computed(() => (
  pulseTick.value < game.value.profile.pulseWarningTicks
))
const peakBoundaryPressure = computed(() => Math.max(
  ...Object.values(crossingState.value.boundaryPressure),
))
const boundaryPressurePercent = computed(() => Math.min(
  100,
  Math.round(
    peakBoundaryPressure.value
    * 100
    / game.value.profile.boundaryPressureLimit,
  ),
))
const fieldStatus = computed(() => {
  if (peakBoundaryPressure.value > 0) {
    return `边界 ${boundaryPressurePercent.value}%`
  }
  return isPulseWarning.value ? '缺口标定' : '交叉脉冲'
})
const collisionLabel = computed(() => (
  crossingState.value.collisionKind === 'boundary'
    ? '边界封锁'
    : '脉冲拦截'
))

function publishSpectatorState(force = false) {
  if (isSpectating.value || !hasTargetSpectators.value) return
  if (!force && crossingState.value.tick - lastPublishedTick < 6) return
  lastPublishedTick = crossingState.value.tick
  spectatorSequence += 1
  arcade.publishSpectatorFrame(spectatorSequence, {
    phase: phase.value,
    readyCount: readyCount.value,
    localElapsedMs: localElapsedMs.value,
    crossingState: { ...crossingState.value },
  })
}

function applySpectatorState(raw: Record<string, unknown>) {
  const nextPhase = raw.phase
  const nextState = raw.crossingState
  if (
    !['ready', 'playing', 'submitting', 'finished'].includes(String(nextPhase))
    || !nextState
    || typeof nextState !== 'object'
  ) return
  const candidate = nextState as Record<string, unknown>
  if (
    typeof candidate.tick !== 'number'
    || typeof candidate.playerX !== 'number'
    || typeof candidate.playerY !== 'number'
  ) return
  clearLoop()
  phase.value = nextPhase as typeof phase.value
  readyCount.value = typeof raw.readyCount === 'number' ? raw.readyCount : 3
  localElapsedMs.value = typeof raw.localElapsedMs === 'number'
    ? raw.localElapsedMs
    : 0
  crossingState.value = candidate as unknown as CrossingState
  nextTick(drawArena)
}

function clearLoop() {
  if (readyTimer !== null) window.clearTimeout(readyTimer)
  if (animationFrame !== null) window.cancelAnimationFrame(animationFrame)
  readyTimer = null
  animationFrame = null
}

function beginReadySequence() {
  if (isSpectating.value) return
  clearLoop()
  phase.value = 'ready'
  readyCount.value = 3
  crossingState.value = createCrossingState()
  inputs.value = []
  heldMask.value = 0
  localElapsedMs.value = 0
  submitError.value = null
  submitted = false
  activePointers.clear()
  drawArena()
  publishSpectatorState(true)

  const countDown = () => {
    if (readyCount.value <= 1) {
      phase.value = 'playing'
      previousFrame = performance.now()
      accumulator = 0
      animationFrame = window.requestAnimationFrame(frame)
      publishSpectatorState(true)
      return
    }
    readyCount.value -= 1
    publishSpectatorState(true)
    readyTimer = window.setTimeout(countDown, 420)
  }
  readyTimer = window.setTimeout(countDown, 420)
}

function frame(timestamp: number) {
  if (phase.value !== 'playing') return
  const delta = Math.min(100, timestamp - previousFrame)
  previousFrame = timestamp
  accumulator += delta
  const tickDuration = 1_000 / TICK_RATE
  while (accumulator >= tickDuration && phase.value === 'playing') {
    accumulator -= tickDuration
    const input = heldMask.value
    inputs.value.push(input)
    crossingState.value = advanceCrossingState(
      crossingState.value,
      input,
      pulsePlan.value,
      game.value.profile,
    )
    localElapsedMs.value = Math.min(
      game.value.durationMs,
      Math.round(crossingState.value.tick * tickDuration),
    )
    if (
      crossingState.value.collisionTick !== null
      || crossingState.value.tick >= targetTicks.value
    ) {
      void submitRun()
    }
  }
  publishSpectatorState()
  drawArena()
  if (phase.value === 'playing') {
    animationFrame = window.requestAnimationFrame(frame)
  }
}

async function submitRun() {
  if (isSpectating.value || submitted) return
  submitted = true
  phase.value = 'submitting'
  if (animationFrame !== null) window.cancelAnimationFrame(animationFrame)
  animationFrame = null
  drawArena()
  publishSpectatorState(true)
  const successful = await arcade.actionWithResult('finish', {
    inputs: inputs.value,
  })
  if (!successful) {
    submitError.value = arcade.error ?? '轨迹校验失败，请重新挑战'
    submitted = false
  }
}

function retrySubmission() {
  if (isSpectating.value) return
  if (!submitted) void submitRun()
}

function keyboardMask(code: string): number {
  if (code === 'ArrowUp' || code === 'KeyW') return INPUT_UP
  if (code === 'ArrowDown' || code === 'KeyS') return INPUT_DOWN
  if (code === 'ArrowLeft' || code === 'KeyA') return INPUT_LEFT
  if (code === 'ArrowRight' || code === 'KeyD') return INPUT_RIGHT
  return 0
}

function onKeydown(event: KeyboardEvent) {
  if (isSpectating.value) return
  const mask = keyboardMask(event.code)
  if (!mask) return
  event.preventDefault()
  heldMask.value |= mask
}

function onKeyup(event: KeyboardEvent) {
  if (isSpectating.value) return
  const mask = keyboardMask(event.code)
  if (!mask) return
  event.preventDefault()
  heldMask.value &= ~mask
}

function onControlDown(event: PointerEvent, mask: number) {
  if (isSpectating.value) return
  event.preventDefault()
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
}

function resizeCanvas() {
  const element = canvas.value
  if (!element) return
  const rect = element.getBoundingClientRect()
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  element.width = Math.max(1, Math.round(rect.width * dpr))
  element.height = Math.max(1, Math.round(rect.height * dpr))
  drawArena()
}

function warningGate(side: BoundarySide): number {
  const verticalEdge = side === 'left' || side === 'right'
  return verticalEdge ? currentPulse.value.yGate : currentPulse.value.xGate
}

function drawPulseWarning(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  scaleX: number,
  scaleY: number,
  palette: CriticalCrossingPalette,
) {
  if (!isPulseWarning.value || phase.value !== 'playing') return
  const pulse = .5 + .2 * Math.sin(crossingState.value.tick * .65)
  const railWidth = Math.max(8, Math.min(width, height) * .022)

  for (const side of BOUNDARY_SIDES) {
    const verticalEdge = side === 'left' || side === 'right'
    const scale = verticalEdge ? scaleY : scaleX
    const span = verticalEdge ? height : width
    const gateRadius = game.value.profile.safeGateRadius
    const start = Math.max(0, (warningGate(side) - gateRadius) * scale)
    const end = Math.min(span, (warningGate(side) + gateRadius) * scale)
    context.globalAlpha = pulse
    context.fillStyle = palette.pulse
    if (verticalEdge) {
      const x = side === 'left' ? 0 : width - railWidth
      context.fillRect(x, 0, railWidth, start)
      context.fillRect(x, end, railWidth, height - end)
      context.fillStyle = palette.gate
      context.fillRect(x, start, railWidth, Math.max(0, end - start))
    } else {
      const y = side === 'top' ? 0 : height - railWidth
      context.fillRect(0, y, start, railWidth)
      context.fillRect(end, y, width - end, railWidth)
      context.fillStyle = palette.gate
      context.fillRect(start, y, Math.max(0, end - start), railWidth)
    }
    context.globalAlpha = 1
  }
}

function drawPulseFronts(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  scaleX: number,
  scaleY: number,
  palette: CriticalCrossingPalette,
) {
  context.lineCap = 'round'
  for (const { side, position, gate } of pulseFronts(
    pulsePlan.value,
    crossingState.value.tick,
    game.value.profile,
  )) {
    const verticalEdge = side === 'left' || side === 'right'
    const front = position * (verticalEdge ? scaleX : scaleY)
    const gateRadius = game.value.profile.safeGateRadius
    const gateStart = (gate - gateRadius) * (verticalEdge ? scaleY : scaleX)
    const gateEnd = (gate + gateRadius) * (verticalEdge ? scaleY : scaleX)
    context.shadowColor = palette.pulseGlow
    context.shadowBlur = Math.max(7, Math.min(width, height) * .018)
    context.strokeStyle = palette.pulse
    context.lineWidth = Math.max(3, Math.min(width, height) * .007)
    context.beginPath()
    if (verticalEdge) {
      context.moveTo(front, 0)
      context.lineTo(front, gateStart)
      context.moveTo(front, gateEnd)
      context.lineTo(front, height)
    } else {
      context.moveTo(0, front)
      context.lineTo(gateStart, front)
      context.moveTo(gateEnd, front)
      context.lineTo(width, front)
    }
    context.stroke()

    context.shadowColor = palette.gateGlow
    context.strokeStyle = palette.gate
    context.lineWidth *= 1.2
    context.beginPath()
    if (verticalEdge) {
      context.moveTo(front, gateStart)
      context.lineTo(front, gateEnd)
    } else {
      context.moveTo(gateStart, front)
      context.lineTo(gateEnd, front)
    }
    context.stroke()
  }
  context.shadowBlur = 0
  context.lineCap = 'butt'
}

function drawBoundaryPressure(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  scaleX: number,
  scaleY: number,
  palette: CriticalCrossingPalette,
) {
  for (const side of BOUNDARY_SIDES) {
    const pressure = crossingState.value.boundaryPressure[side]
    const ratio = Math.min(
      1,
      pressure / game.value.profile.boundaryPressureLimit,
    )
    const zoneDepth = side === 'top' || side === 'bottom'
      ? BOUNDARY_ZONE_Y * scaleY
      : BOUNDARY_ZONE_X * scaleX
    const wallDepth = boundaryWallDepth(pressure, game.value.profile)
      * (side === 'top' || side === 'bottom' ? scaleY : scaleX)

    context.globalAlpha = .28 + ratio * .72
    context.fillStyle = palette.boundary
    if (side === 'top') context.fillRect(0, 0, width, zoneDepth)
    if (side === 'right') context.fillRect(width - zoneDepth, 0, zoneDepth, height)
    if (side === 'bottom') context.fillRect(0, height - zoneDepth, width, zoneDepth)
    if (side === 'left') context.fillRect(0, 0, zoneDepth, height)
    context.globalAlpha = 1

    if (wallDepth <= 0) continue
    context.fillStyle = palette.boundaryCritical
    context.shadowColor = palette.pulseGlow
    context.shadowBlur = Math.max(10, wallDepth * .7)
    if (side === 'top') context.fillRect(0, 0, width, wallDepth)
    if (side === 'right') context.fillRect(width - wallDepth, 0, wallDepth, height)
    if (side === 'bottom') context.fillRect(0, height - wallDepth, width, wallDepth)
    if (side === 'left') context.fillRect(0, 0, wallDepth, height)
    context.shadowBlur = 0
  }
}

function drawNavigationCore(
  context: CanvasRenderingContext2D,
  scaleX: number,
  scaleY: number,
  palette: CriticalCrossingPalette,
) {
  const x = crossingState.value.playerX * scaleX
  const y = crossingState.value.playerY * scaleY
  const radius = Math.max(6.5, PLAYER_RADIUS * Math.min(scaleX, scaleY))
  const hitRadius = Math.max(3, PLAYER_HIT_RADIUS * Math.min(scaleX, scaleY))
  const interrupted = crossingState.value.collisionTick !== null

  context.beginPath()
  context.arc(x, y, radius * 2.1, 0, Math.PI * 2)
  context.fillStyle = palette.core
  context.globalAlpha = .42
  context.fill()
  context.globalAlpha = 1

  context.beginPath()
  context.arc(x, y, radius, 0, Math.PI * 2)
  context.fillStyle = interrupted ? palette.pulse : palette.core
  context.strokeStyle = interrupted ? palette.pulseGlow : palette.coreEdge
  context.lineWidth = Math.max(1.5, radius * .16)
  context.shadowColor = interrupted ? palette.pulseGlow : palette.gateGlow
  context.shadowBlur = radius * 2.6
  context.fill()
  context.stroke()
  context.shadowBlur = 0

  context.beginPath()
  context.arc(x, y, hitRadius, 0, Math.PI * 2)
  context.fillStyle = palette.coreCenter
  context.shadowColor = palette.gateGlow
  context.shadowBlur = hitRadius * 2
  context.fill()
  context.shadowBlur = 0
}

function drawArena() {
  const element = canvas.value
  const context = element?.getContext('2d')
  if (!element || !context) return
  const width = element.width
  const height = element.height
  const scaleX = width / BOARD_WIDTH
  const scaleY = height / BOARD_HEIGHT
  const palette = criticalCrossingPalette(currentTheme.value)
  context.clearRect(0, 0, width, height)

  const background = context.createRadialGradient(
    width / 2,
    height / 2,
    0,
    width / 2,
    height / 2,
    Math.max(width, height) * .72,
  )
  background.addColorStop(0, palette.center)
  background.addColorStop(1, palette.edge)
  context.fillStyle = background
  context.fillRect(0, 0, width, height)

  context.strokeStyle = palette.grid
  context.lineWidth = Math.max(1, width / 900)
  const grid = width / 12
  for (let x = 0; x < width; x += grid) {
    context.beginPath()
    context.moveTo(x, 0)
    context.lineTo(x, height)
    context.stroke()
  }
  for (let y = 0; y < height; y += grid) {
    context.beginPath()
    context.moveTo(0, y)
    context.lineTo(width, y)
    context.stroke()
  }

  drawBoundaryPressure(context, width, height, scaleX, scaleY, palette)
  drawPulseWarning(context, width, height, scaleX, scaleY, palette)
  drawPulseFronts(context, width, height, scaleX, scaleY, palette)
  drawNavigationCore(context, scaleX, scaleY, palette)
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
      clearLoop()
      phase.value = 'finished'
      localElapsedMs.value = game.value.elapsedMs
      return
    }
    if (
      snapshotPhase === 'playing'
      && (previousPhase === 'finished' || game.value.seed !== previousSeed)
    ) {
      await nextTick()
      if (!isSpectating.value) beginReadySequence()
    }
  },
)

watch(currentTheme, () => drawArena())

onMounted(() => {
  if (!isSpectating.value) {
    window.addEventListener('keydown', onKeydown, { passive: false })
    window.addEventListener('keyup', onKeyup, { passive: false })
    window.addEventListener('blur', clearInput)
  }
  window.addEventListener('resize', resizeCanvas)
  nextTick(() => {
    resizeCanvas()
    if (props.snapshot.phase === 'playing' && !isSpectating.value) beginReadySequence()
  })
})

onBeforeUnmount(() => {
  clearLoop()
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('keyup', onKeyup)
  window.removeEventListener('blur', clearInput)
  window.removeEventListener('resize', resizeCanvas)
})
</script>

<template>
  <section class="crossing-game">
    <header class="surface crossing-status">
      <span class="crossing-status-mark"><ScanLine :size="24" /></span>
      <div class="crossing-status-copy">
        <small>CRITICAL CROSSING · {{ game.difficultyLabel }}</small>
        <strong>{{ durationSeconds }} 秒临界场</strong>
      </div>
      <div class="crossing-pulse-track" :aria-label="`共 ${game.pulseCount} 轮脉冲`">
        <i
          v-for="pulse in game.pulseCount"
          :key="pulse"
          :class="{
            complete: pulse - 1 < pulseIndex,
            current: pulse - 1 === pulseIndex && phase === 'playing',
          }"
        />
      </div>
    </header>

    <SoloMetricGrid
      aria-label="临界穿越状态"
      :items="[
        { label: '剩余时间', value: `${remainingLabel} 秒`, tone: remainingMs < 1_000 ? 'danger' : 'warning' },
        { label: '当前序列', value: `${pulseIndex + 1} / ${game.pulseCount}` },
        { label: '临界场状态', value: fieldStatus },
      ]"
    />

    <section class="crossing-arena surface" :class="`phase-${phase}`">
      <canvas ref="canvas" aria-label="临界穿越脉冲屏障区域" />

      <div v-if="phase === 'ready'" class="arena-overlay ready-overlay">
        <small>方向键 / WASD / 触屏方向盘</small>
        <strong>{{ readyCount }}</strong>
        <span>读取缺口，准备穿越</span>
      </div>

      <div v-else-if="phase === 'submitting'" class="arena-overlay result-overlay">
        <CircleX v-if="crossingState.collisionTick !== null" :size="34" />
        <ShieldCheck v-else :size="34" />
        <strong>{{ crossingState.collisionTick !== null ? collisionLabel : '轨迹完整' }}</strong>
        <span>{{ submitError || `正在校验 ${inputs.length} 帧穿越轨迹…` }}</span>
        <button v-if="submitError" type="button" @click="retrySubmission">重新校验</button>
      </div>

      <div
        v-else-if="phase === 'finished'"
        class="arena-overlay finished-overlay"
        :class="{ crossed: game.crossed }"
      >
        <Sparkles v-if="game.crossed" :size="38" />
        <CircleX v-else :size="38" />
        <strong>{{ game.crossed ? `${durationSeconds} 秒穿越完成` : '穿越中断' }}</strong>
        <span>{{ snapshot.winReason }}</span>
      </div>

      <div v-if="phase === 'playing'" class="arena-timer" aria-live="polite">
        <small>TIME TO GATE</small><strong>{{ remainingLabel }}</strong>
      </div>

      <div
        v-if="phase === 'playing' && isPulseWarning"
        class="pulse-warning"
        aria-live="polite"
      >
        <small>序列 {{ String(pulseIndex + 1).padStart(2, '0') }}</small>
        <strong>交叉脉冲标定中</strong>
        <span>青色边缘标记安全缺口</span>
      </div>

      <div
        v-if="phase === 'playing' && peakBoundaryPressure > 0"
        class="boundary-pressure"
        :class="{ critical: boundaryPressurePercent >= 100 }"
        aria-live="polite"
      >
        <small>{{ boundaryPressurePercent >= 100 ? '边界封锁启动' : '离开边界' }}</small>
        <strong>{{ boundaryPressurePercent }}%</strong>
        <i><span :style="{ width: `${boundaryPressurePercent}%` }" /></i>
      </div>
    </section>

    <div v-if="snapshot.phase === 'playing'" class="crossing-controls" aria-label="触屏方向控制">
      <button
        class="control-up"
        type="button"
        :disabled="isSpectating"
        aria-label="向上移动"
        @pointerdown="onControlDown($event, INPUT_UP)"
        @pointerup="onControlUp"
        @pointercancel="onControlUp"
        @lostpointercapture="onControlUp"
      ><ArrowUp :size="25" /></button>
      <button
        class="control-left"
        type="button"
        :disabled="isSpectating"
        aria-label="向左移动"
        @pointerdown="onControlDown($event, INPUT_LEFT)"
        @pointerup="onControlUp"
        @pointercancel="onControlUp"
        @lostpointercapture="onControlUp"
      ><ArrowLeft :size="25" /></button>
      <span><i />导航</span>
      <button
        class="control-right"
        type="button"
        :disabled="isSpectating"
        aria-label="向右移动"
        @pointerdown="onControlDown($event, INPUT_RIGHT)"
        @pointerup="onControlUp"
        @pointercancel="onControlUp"
        @lostpointercapture="onControlUp"
      ><ArrowRight :size="25" /></button>
      <button
        class="control-down"
        type="button"
        :disabled="isSpectating"
        aria-label="向下移动"
        @pointerdown="onControlDown($event, INPUT_DOWN)"
        @pointerup="onControlUp"
        @pointercancel="onControlUp"
        @lostpointercapture="onControlUp"
      ><ArrowDown :size="25" /></button>
    </div>

    <p class="crossing-hint">
      <kbd>↑</kbd><kbd>↓</kbd><kbd>←</kbd><kbd>→</kbd> 或 <kbd>WASD</kbd>
      移动 · 提前进入青色缺口，贴边约 {{ boundaryLockLabel }} 秒会触发封锁
    </p>

    <SoloResultCard
      v-if="snapshot.phase === 'finished'"
      :eyebrow="game.crossed ? '临界场已穿越' : collisionLabel"
      :title="game.crossed ? '导航核心安全通过' : '重新读取下一处缺口'"
      :score="(game.elapsedMs / 1_000).toFixed(2)"
      score-unit="秒"
      :description="snapshot.winReason"
      :tone="game.crossed ? 'success' : 'danger'"
      :metrics="[
        { label: '挑战模式', value: `${game.difficultyLabel} · ${durationSeconds} 秒` },
        { label: '轨迹结果', value: game.crossed ? '完整穿越' : collisionLabel },
        { label: '服务端校验', value: `${game.tickRate} Hz` },
      ]"
      :can-restart="snapshot.actions.canRestart"
      :busy="arcade.busy"
      restart-label="重新穿越"
      @restart="restartChallenge"
    />
  </section>
</template>

<style scoped>
.crossing-game {
  --cross-accent: var(--accent);
  width: min(100%, 920px);
  display: grid;
  gap: 14px;
  margin: 0 auto;
}

.crossing-status {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 13px;
  padding: 13px 15px;
  border-color: color-mix(in srgb, var(--cross-accent) 24%, var(--line));
}

.crossing-status-mark {
  width: 46px;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--cross-accent) 38%, var(--line));
  border-radius: 15px;
  color: var(--cross-accent);
  background: color-mix(in srgb, var(--cross-accent) 9%, var(--surface-inset));
  box-shadow: inset 0 1px 0 color-mix(in srgb, white 14%, transparent);
}

.crossing-status-copy { min-width: 0; }
.crossing-status-copy small,
.crossing-status-copy strong { display: block; }
.crossing-status-copy small {
  color: var(--cross-accent);
  font-size: 8px;
  font-weight: 900;
  letter-spacing: .12em;
}
.crossing-status-copy strong { margin-top: 4px; font-size: 17px; }

.crossing-pulse-track { display: flex; gap: 5px; }
.crossing-pulse-track i {
  width: 13px;
  height: 4px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--muted) 26%, transparent);
}
.crossing-pulse-track i.complete { background: color-mix(in srgb, var(--cross-accent) 55%, var(--line)); }
.crossing-pulse-track i.current {
  width: 24px;
  background: var(--cross-accent);
  box-shadow: 0 0 13px color-mix(in srgb, var(--cross-accent) 72%, transparent);
}

.crossing-arena {
  position: relative;
  aspect-ratio: 20 / 13;
  overflow: hidden;
  border-color: color-mix(in srgb, var(--cross-accent) 32%, var(--line));
  background: var(--surface-inset);
  box-shadow: var(--shadow-raised), inset 0 0 70px color-mix(in srgb, var(--bg) 64%, transparent);
}
.crossing-arena::after {
  position: absolute;
  inset: 7px;
  border: 1px solid color-mix(in srgb, var(--cross-accent) 16%, transparent);
  border-radius: calc(var(--radius-panel) - 7px);
  content: '';
  pointer-events: none;
}
.crossing-arena canvas { width: 100%; height: 100%; display: block; }

.arena-overlay {
  position: absolute;
  z-index: 3;
  inset: 0;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  padding: 24px;
  text-align: center;
  background: color-mix(in srgb, var(--surface-primary) 72%, transparent);
  backdrop-filter: blur(7px);
}
.arena-overlay small {
  color: var(--cross-accent);
  font-size: 10px;
  font-weight: 900;
  letter-spacing: .12em;
}
.arena-overlay strong { font-family: "Songti SC", "STSong", serif; }
.ready-overlay strong {
  color: var(--cross-accent);
  font-size: clamp(72px, 16vw, 126px);
  line-height: .9;
  text-shadow: 0 0 35px color-mix(in srgb, var(--cross-accent) 50%, transparent);
}
.ready-overlay span { color: var(--text-soft); font-weight: 850; letter-spacing: .12em; }
.result-overlay svg,
.finished-overlay svg { color: var(--red); filter: drop-shadow(0 0 14px color-mix(in srgb, var(--red) 48%, transparent)); }
.result-overlay strong,
.finished-overlay strong { color: var(--text); font-size: clamp(30px, 6vw, 52px); }
.result-overlay span,
.finished-overlay span { max-width: 480px; color: var(--muted); font-size: 11px; line-height: 1.6; }
.result-overlay button {
  min-width: 112px;
  margin-top: 7px;
  border: 1px solid color-mix(in srgb, var(--red) 48%, var(--line));
  border-radius: 11px;
  padding: 10px 15px;
  color: var(--text);
  background: color-mix(in srgb, var(--red) 12%, var(--surface-elevated));
  font-weight: 850;
  cursor: pointer;
}
.finished-overlay.crossed svg { color: var(--cross-accent); }

.arena-timer {
  position: absolute;
  z-index: 2;
  top: 14px;
  left: 50%;
  display: grid;
  justify-items: center;
  border: 1px solid color-mix(in srgb, var(--cross-accent) 20%, var(--line));
  border-radius: 999px;
  padding: 6px 14px;
  color: var(--text);
  background: color-mix(in srgb, var(--surface-primary) 72%, transparent);
  box-shadow: inset 0 1px 0 color-mix(in srgb, white 12%, transparent);
  transform: translateX(-50%);
  backdrop-filter: blur(9px);
}
.arena-timer small { color: var(--red); font-size: 7px; font-weight: 950; letter-spacing: .18em; }
.arena-timer strong { font-size: 18px; font-variant-numeric: tabular-nums; }

.pulse-warning {
  position: absolute;
  z-index: 2;
  top: 15px;
  left: 15px;
  display: grid;
  gap: 2px;
  border: 1px solid color-mix(in srgb, var(--cross-accent) 42%, var(--line));
  border-radius: 11px;
  padding: 8px 11px;
  color: var(--text);
  background: color-mix(in srgb, var(--surface-primary) 78%, transparent);
  backdrop-filter: blur(9px);
}
.pulse-warning small { color: var(--cross-accent); font-size: 7px; font-weight: 950; letter-spacing: .12em; }
.pulse-warning strong { font-size: 11px; }
.pulse-warning span { color: var(--muted); font-size: 8px; }

.boundary-pressure {
  position: absolute;
  z-index: 2;
  right: 15px;
  bottom: 15px;
  width: 132px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 4px 8px;
  border: 1px solid color-mix(in srgb, var(--accent) 48%, var(--line));
  border-radius: 11px;
  padding: 8px 10px;
  color: color-mix(in srgb, var(--accent) 72%, var(--text));
  background: color-mix(in srgb, var(--accent) 10%, var(--surface-primary));
  backdrop-filter: blur(9px);
}
.boundary-pressure small { align-self: end; font-size: 8px; font-weight: 900; }
.boundary-pressure strong { font-size: 15px; font-variant-numeric: tabular-nums; }
.boundary-pressure i {
  grid-column: 1 / -1;
  height: 3px;
  overflow: hidden;
  border-radius: 999px;
  background: color-mix(in srgb, var(--muted) 22%, transparent);
}
.boundary-pressure i span { display: block; height: 100%; border-radius: inherit; background: var(--accent); }
.boundary-pressure.critical {
  border-color: color-mix(in srgb, var(--red) 70%, var(--line));
  color: var(--red);
  background: color-mix(in srgb, var(--red) 13%, var(--surface-primary));
}
.boundary-pressure.critical i span { background: var(--red); }

.crossing-controls {
  width: min(100%, 330px);
  display: grid;
  grid-template: repeat(3, 56px) / repeat(3, 56px);
  justify-content: center;
  gap: 6px;
  margin: 0 auto;
  user-select: none;
  touch-action: none;
}
.crossing-controls button {
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--cross-accent) 34%, var(--line));
  border-radius: 15px;
  color: color-mix(in srgb, var(--cross-accent) 78%, var(--text));
  background: var(--control-surface), var(--surface-inset);
  box-shadow: var(--shadow-contact), inset 0 1px 0 color-mix(in srgb, white 16%, transparent);
  touch-action: none;
  cursor: pointer;
}
.crossing-controls button:active {
  border-color: var(--cross-accent);
  color: var(--accent-contrast);
  background: var(--cross-accent);
  transform: scale(.95);
}
.control-up { grid-area: 1 / 2; }
.control-left { grid-area: 2 / 1; }
.control-right { grid-area: 2 / 3; }
.control-down { grid-area: 3 / 2; }
.crossing-controls > span {
  grid-area: 2 / 2;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 4px;
  color: var(--muted);
  font-size: 8px;
  font-weight: 850;
}
.crossing-controls > span i {
  width: 8px;
  aspect-ratio: 1;
  border-radius: 50%;
  background: var(--cross-accent);
  box-shadow: 0 0 12px color-mix(in srgb, var(--cross-accent) 76%, transparent);
}

.crossing-hint { margin: -3px 0 0; color: var(--muted); font-size: 9px; text-align: center; }
.crossing-hint kbd {
  display: inline-block;
  margin: 0 1px;
  border: 1px solid var(--line);
  border-bottom-width: 2px;
  border-radius: 5px;
  padding: 2px 5px;
  color: var(--text);
  background: var(--surface-inset);
  font: inherit;
  font-weight: 900;
}

@media (min-width: 760px) and (hover: hover) and (pointer: fine) {
  .crossing-controls { display: none; }
}

@media (max-width: 600px) {
  .crossing-status { grid-template-columns: auto minmax(0, 1fr); }
  .crossing-pulse-track { grid-column: 1 / -1; justify-content: center; }
  .crossing-arena { aspect-ratio: 4 / 3; }
  .crossing-controls { grid-template: repeat(3, 52px) / repeat(3, 52px); }
  .crossing-hint { line-height: 1.8; }
  .pulse-warning { top: 10px; left: 10px; }
  .boundary-pressure { right: 10px; bottom: 10px; }
}

@media (orientation: landscape) and (max-height: 560px) {
  .crossing-game { grid-template-columns: minmax(0, 1fr) 190px; width: min(100%, 900px); }
  .crossing-game > :first-child,
  .crossing-game > :nth-child(2) { grid-column: 1 / -1; }
  .crossing-arena { grid-column: 1; }
  .crossing-controls { grid-column: 2; align-self: center; }
  .crossing-hint { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .crossing-controls button:active { transform: none; }
}
</style>
