<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Crosshair,
  ShieldCheck,
  Sparkles,
} from '@lucide/vue'
import type { ArcadeSnapshot } from '../../types/arcade'
import { useArcadeStore } from '../../stores/arcade'
import SoloMetricGrid from '../shared/solo/SoloMetricGrid.vue'
import SoloResultCard from '../shared/solo/SoloResultCard.vue'
import {
  BOARD_HEIGHT,
  BOARD_WIDTH,
  DURATION_TICKS,
  EDGE_PRESSURE_LIMIT,
  EDGE_SIDES,
  EDGE_WALL_DEPTH,
  EDGE_ZONE_X,
  EDGE_ZONE_Y,
  INPUT_DOWN,
  INPUT_LEFT,
  INPUT_RIGHT,
  INPUT_UP,
  PLAYER_HIT_RADIUS,
  PLAYER_RADIUS,
  SAFE_GAP_RADIUS,
  TICK_RATE,
  WAVE_TICKS,
  WAVE_WARNING_TICKS,
  advanceDodgeState,
  createDodgeState,
  edgeWallDepth,
  waveFronts,
  waveSafeGap,
  waveSides,
  type EdgeSide,
  type DodgeState,
} from './dodgeEngine'

interface ServerGame {
  seed: number
  durationMs: number
  tickRate: number
  collisionGraceMs: number
  waveWarningMs: number
  edgePressureMs: number
  elapsedMs: number
  survived: boolean | null
  collisionTick: number | null
  collisionKind: 'bullet' | 'edge_wall' | null
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const canvas = ref<HTMLCanvasElement | null>(null)
const arena = ref<HTMLElement | null>(null)
const phase = ref<'ready' | 'playing' | 'submitting' | 'finished'>(
  props.snapshot.phase === 'finished' ? 'finished' : 'ready',
)
const readyCount = ref(3)
const state = ref<DodgeState>(createDodgeState())
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

const game = computed(() => props.snapshot.game as unknown as ServerGame)
const remainingMs = computed(() => Math.max(0, 3_000 - localElapsedMs.value))
const remainingLabel = computed(() => (remainingMs.value / 1_000).toFixed(2))
const waveIndex = computed(() => Math.min(Math.floor(state.value.tick / WAVE_TICKS), 2))
const waveTick = computed(() => state.value.tick % WAVE_TICKS)
const isWaveWarning = computed(() => waveTick.value < WAVE_WARNING_TICKS)
const waveName = computed(() => ['横向弹幕', '纵向弹幕', '交叉弹幕'][waveIndex.value])
const peakEdgePressure = computed(() => Math.max(...Object.values(state.value.edgePressure)))
const edgePressurePercent = computed(() => Math.min(
  100,
  Math.round(peakEdgePressure.value * 100 / EDGE_PRESSURE_LIMIT),
))
const dangerLevel = computed(() => (
  peakEdgePressure.value > 0
    ? `边缘 ${edgePressurePercent.value}%`
    : isWaveWarning.value ? '波次预警' : waveName.value
))
const collisionLabel = computed(() => (
  state.value.collisionKind === 'edge_wall' ? '清场墙命中' : '弹幕命中'
))

function clearLoop() {
  if (readyTimer !== null) window.clearTimeout(readyTimer)
  if (animationFrame !== null) window.cancelAnimationFrame(animationFrame)
  readyTimer = null
  animationFrame = null
}

function beginReadySequence() {
  clearLoop()
  phase.value = 'ready'
  readyCount.value = 3
  state.value = createDodgeState()
  inputs.value = []
  heldMask.value = 0
  localElapsedMs.value = 0
  submitError.value = null
  submitted = false
  activePointers.clear()
  drawArena()
  const countDown = () => {
    if (readyCount.value <= 1) {
      phase.value = 'playing'
      previousFrame = performance.now()
      accumulator = 0
      animationFrame = window.requestAnimationFrame(frame)
      return
    }
    readyCount.value -= 1
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
    state.value = advanceDodgeState(state.value, game.value.seed, input)
    localElapsedMs.value = Math.min(3_000, Math.round(state.value.tick * tickDuration))
    if (state.value.collisionTick !== null || state.value.tick >= DURATION_TICKS) {
      void submitRun()
    }
  }
  drawArena()
  if (phase.value === 'playing') animationFrame = window.requestAnimationFrame(frame)
}

async function submitRun() {
  if (submitted) return
  submitted = true
  phase.value = 'submitting'
  if (animationFrame !== null) window.cancelAnimationFrame(animationFrame)
  animationFrame = null
  drawArena()
  const successful = await arcade.actionWithResult('finish', { inputs: inputs.value })
  if (!successful) {
    submitError.value = arcade.error ?? '成绩校验失败，请重新挑战'
    submitted = false
    return
  }
}

function retrySubmission() {
  if (submitted) return
  void submitRun()
}

function keyboardMask(code: string): number {
  if (code === 'ArrowUp' || code === 'KeyW') return INPUT_UP
  if (code === 'ArrowDown' || code === 'KeyS') return INPUT_DOWN
  if (code === 'ArrowLeft' || code === 'KeyA') return INPUT_LEFT
  if (code === 'ArrowRight' || code === 'KeyD') return INPUT_RIGHT
  return 0
}

function onKeydown(event: KeyboardEvent) {
  const mask = keyboardMask(event.code)
  if (!mask) return
  event.preventDefault()
  heldMask.value |= mask
}

function onKeyup(event: KeyboardEvent) {
  const mask = keyboardMask(event.code)
  if (!mask) return
  event.preventDefault()
  heldMask.value &= ~mask
}

function onControlDown(event: PointerEvent, mask: number) {
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

function warningGap(side: EdgeSide): number {
  const verticalEdge = side === 'left' || side === 'right'
  if (waveIndex.value === 2) {
    return waveSafeGap(game.value.seed, verticalEdge ? 0 : 1, verticalEdge ? 'y' : 'x')
  }
  return waveSafeGap(game.value.seed, waveIndex.value, verticalEdge ? 'y' : 'x')
}

function drawWaveWarning(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  scaleX: number,
  scaleY: number,
) {
  if (!isWaveWarning.value || phase.value !== 'playing') return
  const pulse = .45 + .25 * Math.sin(state.value.tick * .7)
  const edgeWidth = Math.max(8, Math.min(width, height) * .025)
  const gapRadius = SAFE_GAP_RADIUS

  for (const side of waveSides(waveIndex.value)) {
    const verticalEdge = side === 'left' || side === 'right'
    const scale = verticalEdge ? scaleY : scaleX
    const start = Math.max(0, (warningGap(side) - gapRadius) * scale)
    const end = Math.min(verticalEdge ? height : width, (warningGap(side) + gapRadius) * scale)
    context.fillStyle = `rgba(255, 78, 99, ${pulse})`
    if (side === 'left' || side === 'right') {
      const x = side === 'left' ? 0 : width - edgeWidth
      context.fillRect(x, 0, edgeWidth, start)
      context.fillRect(x, end, edgeWidth, height - end)
      context.fillStyle = 'rgba(94, 235, 209, .72)'
      context.fillRect(x, start, edgeWidth, Math.max(0, end - start))
    } else {
      const y = side === 'top' ? 0 : height - edgeWidth
      context.fillRect(0, y, start, edgeWidth)
      context.fillRect(end, y, width - end, edgeWidth)
      context.fillStyle = 'rgba(94, 235, 209, .72)'
      context.fillRect(start, y, Math.max(0, end - start), edgeWidth)
    }
  }
}

function drawWaveFronts(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  scaleX: number,
  scaleY: number,
) {
  context.lineCap = 'round'
  context.shadowColor = '#ff4967'
  context.shadowBlur = Math.max(7, Math.min(width, height) * .018)
  for (const { side, position, gap } of waveFronts(game.value.seed, state.value.tick)) {
    const verticalEdge = side === 'left' || side === 'right'
    const front = position * (verticalEdge ? scaleX : scaleY)
    const gapStart = (gap - SAFE_GAP_RADIUS) * (verticalEdge ? scaleY : scaleX)
    const gapEnd = (gap + SAFE_GAP_RADIUS) * (verticalEdge ? scaleY : scaleX)
    context.strokeStyle = 'rgba(255, 92, 111, .72)'
    context.lineWidth = Math.max(3, Math.min(width, height) * .007)
    context.beginPath()
    if (verticalEdge) {
      context.moveTo(front, 0); context.lineTo(front, gapStart)
      context.moveTo(front, gapEnd); context.lineTo(front, height)
    } else {
      context.moveTo(0, front); context.lineTo(gapStart, front)
      context.moveTo(gapEnd, front); context.lineTo(width, front)
    }
    context.stroke()

    context.strokeStyle = 'rgba(102, 239, 214, .88)'
    context.lineWidth *= 1.15
    context.beginPath()
    if (verticalEdge) {
      context.moveTo(front, gapStart); context.lineTo(front, gapEnd)
    } else {
      context.moveTo(gapStart, front); context.lineTo(gapEnd, front)
    }
    context.stroke()
  }
  context.shadowBlur = 0
  context.lineCap = 'butt'
}

function drawEdgePressure(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  scaleX: number,
  scaleY: number,
) {
  for (const side of EDGE_SIDES) {
    const pressure = state.value.edgePressure[side]
    const pressureRatio = Math.min(1, pressure / EDGE_PRESSURE_LIMIT)
    const zoneDepth = (side === 'top' || side === 'bottom' ? EDGE_ZONE_Y * scaleY : EDGE_ZONE_X * scaleX)
    const wallDepth = edgeWallDepth(pressure)
      * (side === 'top' || side === 'bottom' ? scaleY : scaleX)

    context.fillStyle = `rgba(255, ${Math.round(190 - pressureRatio * 100)}, 67, ${.035 + pressureRatio * .16})`
    if (side === 'top') context.fillRect(0, 0, width, zoneDepth)
    if (side === 'right') context.fillRect(width - zoneDepth, 0, zoneDepth, height)
    if (side === 'bottom') context.fillRect(0, height - zoneDepth, width, zoneDepth)
    if (side === 'left') context.fillRect(0, 0, zoneDepth, height)

    if (wallDepth <= 0) continue
    context.fillStyle = 'rgba(255, 55, 81, .52)'
    context.shadowColor = '#ff3751'
    context.shadowBlur = Math.max(10, wallDepth * .8)
    if (side === 'top') context.fillRect(0, 0, width, wallDepth)
    if (side === 'right') context.fillRect(width - wallDepth, 0, wallDepth, height)
    if (side === 'bottom') context.fillRect(0, height - wallDepth, width, wallDepth)
    if (side === 'left') context.fillRect(0, 0, wallDepth, height)
    context.shadowBlur = 0
  }
}

function drawArena() {
  const element = canvas.value
  const context = element?.getContext('2d')
  if (!element || !context) return
  const width = element.width
  const height = element.height
  const scaleX = width / BOARD_WIDTH
  const scaleY = height / BOARD_HEIGHT
  const visibleWaveFronts = waveFronts(game.value.seed, state.value.tick)
  context.clearRect(0, 0, width, height)

  const background = context.createRadialGradient(
    width / 2, height / 2, 0, width / 2, height / 2, Math.max(width, height) * .7,
  )
  background.addColorStop(0, '#13253b')
  background.addColorStop(.55, '#081421')
  background.addColorStop(1, '#03080e')
  context.fillStyle = background
  context.fillRect(0, 0, width, height)

  context.strokeStyle = 'rgba(105, 156, 190, .09)'
  context.lineWidth = Math.max(1, width / 900)
  const grid = width / 12
  for (let x = 0; x < width; x += grid) {
    context.beginPath(); context.moveTo(x, 0); context.lineTo(x, height); context.stroke()
  }
  for (let y = 0; y < height; y += grid) {
    context.beginPath(); context.moveTo(0, y); context.lineTo(width, y); context.stroke()
  }

  drawEdgePressure(context, width, height, scaleX, scaleY)
  drawWaveWarning(context, width, height, scaleX, scaleY)
  drawWaveFronts(context, width, height, scaleX, scaleY)

  if (visibleWaveFronts.length === 0) for (const bullet of state.value.bullets) {
    const x = bullet.x * scaleX
    const y = bullet.y * scaleY
    const radius = Math.max(2.6, bullet.radius * Math.min(scaleX, scaleY))
    const trailScale = Math.max(scaleX, scaleY) * 2.2
    context.beginPath()
    context.moveTo(x - bullet.vx * trailScale, y - bullet.vy * trailScale)
    context.lineTo(x, y)
    context.strokeStyle = 'rgba(248, 99, 116, .32)'
    context.lineWidth = radius * 1.35
    context.stroke()
    context.beginPath()
    context.arc(x, y, radius, 0, Math.PI * 2)
    context.fillStyle = '#ff7182'
    context.shadowColor = '#ff4967'
    context.shadowBlur = radius * 3
    context.fill()
    context.shadowBlur = 0
    context.beginPath()
    context.arc(x - radius * .28, y - radius * .28, radius * .3, 0, Math.PI * 2)
    context.fillStyle = '#fff1e9'
    context.fill()
  }

  const playerX = state.value.playerX * scaleX
  const playerY = state.value.playerY * scaleY
  const playerRadius = Math.max(6.5, PLAYER_RADIUS * Math.min(scaleX, scaleY))
  const playerHitRadius = Math.max(3, PLAYER_HIT_RADIUS * Math.min(scaleX, scaleY))
  context.beginPath()
  context.arc(playerX, playerY, playerRadius * 1.85, 0, Math.PI * 2)
  context.fillStyle = 'rgba(91, 230, 209, .12)'
  context.fill()
  context.beginPath()
  context.arc(playerX, playerY, playerRadius, 0, Math.PI * 2)
  context.fillStyle = state.value.collisionTick === null ? 'rgba(109, 231, 210, .25)' : '#ffffff'
  context.strokeStyle = state.value.collisionTick === null ? '#6de7d2' : '#ff7182'
  context.lineWidth = Math.max(1.5, playerRadius * .16)
  context.shadowColor = state.value.collisionTick === null ? '#4bd8c0' : '#ff546e'
  context.shadowBlur = playerRadius * 2.5
  context.fill()
  context.stroke()
  context.shadowBlur = 0
  context.beginPath()
  context.arc(playerX, playerY, playerHitRadius, 0, Math.PI * 2)
  context.fillStyle = '#e8fff9'
  context.shadowColor = '#6de7d2'
  context.shadowBlur = playerHitRadius * 2
  context.fill()
  context.shadowBlur = 0
}

async function restartChallenge() {
  await arcade.restartGame()
}

watch(
  () => [props.snapshot.phase, game.value.seed] as const,
  async ([snapshotPhase], [previousPhase, previousSeed]) => {
    if (snapshotPhase === 'finished') {
      clearLoop()
      phase.value = 'finished'
      localElapsedMs.value = game.value.elapsedMs
      return
    }
    if (snapshotPhase === 'playing' && (previousPhase === 'finished' || game.value.seed !== previousSeed)) {
      await nextTick()
      beginReadySequence()
    }
  },
)

onMounted(() => {
  window.addEventListener('keydown', onKeydown, { passive: false })
  window.addEventListener('keyup', onKeyup, { passive: false })
  window.addEventListener('blur', clearInput)
  window.addEventListener('resize', resizeCanvas)
  nextTick(() => {
    resizeCanvas()
    if (props.snapshot.phase === 'playing') beginReadySequence()
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
  <section class="survive-game">
    <SoloMetricGrid
      aria-label="弹幕挑战状态"
      :items="[
        { label: '剩余时间', value: `${remainingLabel} 秒`, tone: remainingMs < 1_000 ? 'danger' : 'warning' },
        { label: '屏幕弹幕', value: state.bullets.length },
        { label: '当前强度', value: dangerLevel },
      ]"
    />

    <section ref="arena" class="survive-arena surface" :class="`phase-${phase}`">
      <canvas ref="canvas" aria-label="坚持三秒弹幕躲避区域" />
      <div v-if="phase === 'ready'" class="arena-overlay ready-overlay">
        <small>方向键 / WASD 移动</small>
        <strong>{{ readyCount }}</strong>
        <span>准备躲避</span>
      </div>
      <div v-else-if="phase === 'submitting'" class="arena-overlay result-overlay">
        <Crosshair v-if="state.collisionTick !== null" :size="34" />
        <ShieldCheck v-else :size="34" />
        <strong>{{ state.collisionTick !== null ? collisionLabel : '坚持住了' }}</strong>
        <span>{{ submitError || '正在校验 180 帧躲避轨迹…' }}</span>
        <button v-if="submitError" type="button" @click="retrySubmission">重新校验</button>
      </div>
      <div v-else-if="phase === 'finished'" class="arena-overlay finished-overlay" :class="{ survived: game.survived }">
        <Sparkles v-if="game.survived" :size="38" />
        <Crosshair v-else :size="38" />
        <strong>{{ game.survived ? '3 秒达成' : '挑战失败' }}</strong>
        <span>{{ snapshot.winReason }}</span>
      </div>
      <div v-if="phase === 'playing'" class="arena-timer" aria-live="polite">
        <small>HOLD ON</small><strong>{{ remainingLabel }}</strong>
      </div>
      <div v-if="phase === 'playing' && isWaveWarning" class="wave-warning" aria-live="polite">
        <small>第 {{ waveIndex + 1 }} 波</small>
        <strong>{{ waveName }}来袭</strong>
        <span>青色边缘是安全缺口</span>
      </div>
      <div
        v-if="phase === 'playing' && peakEdgePressure > 0"
        class="edge-pressure"
        :class="{ critical: edgePressurePercent >= 100 }"
        aria-live="polite"
      >
        <small>{{ edgePressurePercent >= 100 ? '清场墙启动' : '离开边缘' }}</small>
        <strong>{{ edgePressurePercent }}%</strong>
        <i><span :style="{ width: `${edgePressurePercent}%` }" /></i>
      </div>
    </section>

    <div v-if="snapshot.phase === 'playing'" class="survive-controls" aria-label="触屏方向控制">
      <button
        class="control-up"
        type="button"
        aria-label="向上移动"
        @pointerdown="onControlDown($event, INPUT_UP)"
        @pointerup="onControlUp"
        @pointercancel="onControlUp"
        @lostpointercapture="onControlUp"
      ><ArrowUp :size="25" /></button>
      <button
        class="control-left"
        type="button"
        aria-label="向左移动"
        @pointerdown="onControlDown($event, INPUT_LEFT)"
        @pointerup="onControlUp"
        @pointercancel="onControlUp"
        @lostpointercapture="onControlUp"
      ><ArrowLeft :size="25" /></button>
      <span><i />移动</span>
      <button
        class="control-right"
        type="button"
        aria-label="向右移动"
        @pointerdown="onControlDown($event, INPUT_RIGHT)"
        @pointerup="onControlUp"
        @pointercancel="onControlUp"
        @lostpointercapture="onControlUp"
      ><ArrowRight :size="25" /></button>
      <button
        class="control-down"
        type="button"
        aria-label="向下移动"
        @pointerdown="onControlDown($event, INPUT_DOWN)"
        @pointerup="onControlUp"
        @pointercancel="onControlUp"
        @lostpointercapture="onControlUp"
      ><ArrowDown :size="25" /></button>
    </div>

    <p class="survive-hint"><kbd>↑</kbd><kbd>↓</kbd><kbd>←</kbd><kbd>→</kbd> 或 <kbd>WASD</kbd> 移动 · 看青色缺口穿过慢速弹幕，边缘停留 0.6 秒会启动清场墙</p>

    <SoloResultCard
      v-if="snapshot.phase === 'finished'"
      :eyebrow="game.survived ? '极限生还' : '弹幕命中'"
      :title="game.survived ? '你坚持了三秒' : '再试一次，别停下来'"
      :score="(game.elapsedMs / 1_000).toFixed(2)"
      score-unit="秒"
      :description="snapshot.winReason"
      :tone="game.survived ? 'success' : 'danger'"
      :metrics="[
        { label: '校验帧率', value: `${game.tickRate} Hz` },
        { label: '轨迹结果', value: game.survived ? '完整存活' : game.collisionKind === 'edge_wall' ? '清场墙命中' : '弹幕命中' },
        { label: '目标时间', value: '3.00 秒' },
      ]"
      :can-restart="snapshot.actions.canRestart"
      :busy="arcade.busy"
      restart-label="再来三秒"
      @restart="restartChallenge"
    />
  </section>
</template>

<style scoped>
.survive-game { width: min(100%, 920px); margin: 0 auto; display: grid; gap: 14px; }
.survive-arena { position: relative; aspect-ratio: 20 / 13; overflow: hidden; border-color: color-mix(in srgb, #ee6478 34%, var(--line)); background: #03080e; box-shadow: var(--shadow-raised), inset 0 0 70px #000; }
.survive-arena::after { position: absolute; inset: 7px; border: 1px solid rgba(139, 187, 216, .16); border-radius: calc(var(--radius-panel) - 7px); content: ''; pointer-events: none; }
.survive-arena canvas { width: 100%; height: 100%; display: block; }
.arena-overlay { position: absolute; z-index: 3; inset: 0; display: grid; place-items: center; align-content: center; gap: 8px; padding: 24px; text-align: center; background: rgba(3, 8, 14, .62); backdrop-filter: blur(5px); }
.arena-overlay small { color: #82b6ce; font-size: 10px; font-weight: 900; letter-spacing: .12em; }
.arena-overlay strong { font-family: "Songti SC", "STSong", serif; }
.ready-overlay strong { color: #70e2d0; font-size: clamp(72px, 16vw, 126px); line-height: .9; text-shadow: 0 0 35px #4bd8c077; }
.ready-overlay span { color: var(--text-soft); font-weight: 850; letter-spacing: .12em; }
.result-overlay svg,.finished-overlay svg { color: #ff7182; filter: drop-shadow(0 0 14px #ff496777); }
.result-overlay strong,.finished-overlay strong { color: var(--text); font-size: clamp(30px, 6vw, 52px); }
.result-overlay span,.finished-overlay span { max-width: 480px; color: var(--muted); font-size: 11px; line-height: 1.6; }
.result-overlay button { margin-top: 7px; border: 1px solid #ff718266; border-radius: 10px; padding: 9px 14px; color: #ffc2ca; background: #79293a55; cursor: pointer; }
.finished-overlay.survived svg { color: #70e2d0; }
.arena-timer { position: absolute; z-index: 2; top: 14px; left: 50%; display: grid; justify-items: center; padding: 6px 14px; border: 1px solid rgba(255,255,255,.12); border-radius: 999px; color: white; background: rgba(3,8,14,.5); transform: translateX(-50%); backdrop-filter: blur(8px); }
.arena-timer small { color: #ff91a1; font-size: 7px; font-weight: 950; letter-spacing: .18em; }.arena-timer strong { font-size: 18px; font-variant-numeric: tabular-nums; }
.wave-warning { position: absolute; z-index: 2; top: 15px; left: 15px; display: grid; gap: 2px; border: 1px solid rgba(109,231,210,.34); border-radius: 10px; padding: 7px 10px; color: white; background: rgba(4,15,23,.7); backdrop-filter: blur(8px); }
.wave-warning small { color: #76e6d3; font-size: 7px; font-weight: 950; letter-spacing: .12em; }.wave-warning strong { font-size: 11px; }.wave-warning span { color: #a9cbc5; font-size: 8px; }
.edge-pressure { position: absolute; z-index: 2; right: 15px; bottom: 15px; width: 126px; display: grid; grid-template-columns: 1fr auto; gap: 4px 8px; border: 1px solid rgba(255,190,67,.38); border-radius: 10px; padding: 8px 10px; color: #ffe2a0; background: rgba(31,18,5,.76); backdrop-filter: blur(8px); }
.edge-pressure small { align-self: end; font-size: 8px; font-weight: 900; }.edge-pressure strong { font-size: 15px; font-variant-numeric: tabular-nums; }.edge-pressure i { grid-column: 1 / -1; height: 3px; overflow: hidden; border-radius: 999px; background: rgba(255,255,255,.12); }.edge-pressure i span { display: block; height: 100%; border-radius: inherit; background: #ffbe43; transition: width 80ms linear; }
.edge-pressure.critical { border-color: rgba(255,71,91,.72); color: #ff9ba7; background: rgba(45,5,11,.84); }.edge-pressure.critical i span { background: #ff475b; }
.survive-controls { width: min(100%, 330px); margin: 0 auto; display: grid; grid-template: repeat(3, 56px) / repeat(3, 56px); justify-content: center; gap: 6px; user-select: none; touch-action: none; }
.survive-controls button { display: grid; place-items: center; border: 1px solid color-mix(in srgb, #70e2d0 28%, var(--line)); border-radius: 15px; color: #9ce9dc; background: var(--surface-inset); box-shadow: inset 0 1px 0 #ffffff14; touch-action: none; cursor: pointer; }
.survive-controls button:active { border-color: #70e2d0; color: #071616; background: #70e2d0; transform: scale(.95); }
.control-up { grid-area: 1 / 2; }.control-left { grid-area: 2 / 1; }.control-right { grid-area: 2 / 3; }.control-down { grid-area: 3 / 2; }
.survive-controls > span { grid-area: 2 / 2; display: grid; place-items: center; align-content: center; gap: 4px; color: var(--muted); font-size: 8px; font-weight: 850; }.survive-controls > span i { width: 8px; aspect-ratio: 1; border-radius: 50%; background: #70e2d0; box-shadow: 0 0 12px #70e2d0; }
.survive-hint { margin: -3px 0 0; color: var(--muted); font-size: 9px; text-align: center; }.survive-hint kbd { display: inline-block; margin: 0 1px; border: 1px solid var(--line); border-bottom-width: 2px; border-radius: 5px; padding: 2px 5px; color: var(--text); background: var(--surface-inset); font: inherit; font-weight: 900; }
@media (min-width: 760px) and (hover: hover) and (pointer: fine) { .survive-controls { display: none; } }
@media (max-width: 600px) { .survive-arena { aspect-ratio: 4 / 3; }.survive-controls { grid-template: repeat(3, 52px) / repeat(3, 52px); }.survive-hint { line-height: 1.8; } }
@media (orientation: landscape) and (max-height: 560px) { .survive-game { grid-template-columns: minmax(0, 1fr) 190px; width: min(100%, 900px); }.survive-game > :first-child { grid-column: 1 / -1; }.survive-arena { grid-column: 1; }.survive-controls { grid-column: 2; align-self: center; }.survive-hint { display: none; } }
@media (prefers-reduced-motion: reduce) { .survive-controls button:active { transform: none; } }
</style>
