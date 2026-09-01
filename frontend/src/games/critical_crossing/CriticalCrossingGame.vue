<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  CircleX,
  Footprints,
  House,
  ShieldCheck,
  Sparkles,
} from '@lucide/vue'
import runnerBridgeBackdrop from '../../assets/critical-crossing/runner-bridge-backdrop.png'
import { useArcadeStore } from '../../stores/arcade'
import { currentTheme } from '../../theme'
import type { ArcadeSnapshot } from '../../types/arcade'
import SoloMetricGrid from '../shared/solo/SoloMetricGrid.vue'
import SoloResultCard from '../shared/solo/SoloResultCard.vue'
import {
  DEFAULT_CROSSING_PROFILE,
  INPUT_DOWN,
  INPUT_LEFT,
  INPUT_RIGHT,
  INPUT_UP,
  RUNNER_LANES,
  TICK_RATE,
  advanceCrossingState,
  buildCoursePlan,
  createCrossingState,
  runnerDistanceMeters,
  runnerLanePosition,
  runnerPoseProgress,
  type CollisionKind,
  type CourseSection,
  type CrossingProfile,
  type CrossingState,
  type ObstacleKind,
  type RunnerLane,
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
  sectionCount?: number
  pulseCount?: number
  profile: CrossingProfile | Record<string, number>
  elapsedMs: number
  distanceMeters?: number
  passedSections?: number
  crossed: boolean | null
  collisionTick: number | null
  collisionKind: CollisionKind | null
}

interface Projection {
  y: number
  halfWidth: number
  scale: number
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const router = useRouter()
const isSpectating = computed(() => props.snapshot.viewer?.mode === 'spectator')
const canvas = ref<HTMLCanvasElement | null>(null)
const phase = ref<'ready' | 'playing' | 'submitting' | 'finished'>(
  props.snapshot.phase === 'finished' ? 'finished' : 'ready',
)
const readyCount = ref(3)
const crossingState = ref<CrossingState>(createCrossingState())
const inputs = ref<number[]>([])
const heldMask = ref(0)
const queuedMask = ref(0)
const localElapsedMs = ref(0)
const submitError = ref<string | null>(null)
const returning = ref(false)
const activePointers = new Map<number, number>()
const backdropImage = new Image()
backdropImage.src = runnerBridgeBackdrop
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
const sectionCount = computed(() => (
  game.value.sectionCount
  ?? game.value.pulseCount
  ?? durationSeconds.value
))
const profile = computed<CrossingProfile>(() => {
  const candidate = game.value.profile as Partial<CrossingProfile>
  return typeof candidate.sectionIntervalTicks === 'number'
    ? candidate as CrossingProfile
    : DEFAULT_CROSSING_PROFILE
})
const targetTicks = computed(() => durationSeconds.value * TICK_RATE)
const coursePlan = computed(() => buildCoursePlan(
  game.value.seed,
  sectionCount.value,
  profile.value,
))
const remainingMs = computed(() => Math.max(
  0,
  game.value.durationMs - localElapsedMs.value,
))
const remainingLabel = computed(() => (remainingMs.value / 1_000).toFixed(2))
const distanceMeters = computed(() => runnerDistanceMeters(
  crossingState.value.tick,
  profile.value,
))
const resultDistanceMeters = computed(() => (
  game.value.distanceMeters ?? distanceMeters.value
))
const resultPassedSections = computed(() => (
  game.value.passedSections ?? crossingState.value.passedSections
))
const nextSectionIndex = computed(() => {
  const index = coursePlan.value.findIndex(
    section => section.impactTick > crossingState.value.tick,
  )
  return index === -1 ? Math.max(0, coursePlan.value.length - 1) : index
})
const nextSection = computed(() => coursePlan.value[nextSectionIndex.value])
const nextSectionTicks = computed(() => Math.max(
  0,
  (nextSection.value?.impactTick ?? crossingState.value.tick)
    - crossingState.value.tick,
))
const poseLabel = computed(() => {
  if (crossingState.value.pose === 'jump') return '跳跃中'
  if (crossingState.value.pose === 'slide') return '下蹲滑行'
  if (crossingState.value.laneChangeTicks > 0) {
    return crossingState.value.lane > crossingState.value.laneChangeFrom
      ? '向右变道'
      : '向左变道'
  }
  return '自动疾行'
})
const collisionLabel = computed(() => collisionKindLabel(
  crossingState.value.collisionKind ?? game.value.collisionKind,
))

function collisionKindLabel(kind: CollisionKind | null): string {
  if (kind === 'gap') return '跌入断桥缺口'
  if (kind === 'barrier') return '撞上封路护栏'
  if (kind === 'ground') return '撞上地面障碍'
  if (kind === 'overhead') return '撞上上方障碍'
  return '疾行中断'
}

function obstacleLabel(kind: ObstacleKind): string {
  if (kind === 'ground') return '跳跃'
  if (kind === 'overhead') return '下蹲'
  if (kind === 'barrier') return '封路'
  if (kind === 'gap') return '断桥'
  return '直行'
}

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
    || typeof candidate.lane !== 'number'
    || typeof candidate.pose !== 'string'
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
  queuedMask.value = 0
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
    const input = heldMask.value | queuedMask.value
    queuedMask.value = 0
    inputs.value.push(input)
    crossingState.value = advanceCrossingState(
      crossingState.value,
      input,
      coursePlan.value,
      profile.value,
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
  if (code === 'ArrowUp' || code === 'KeyW' || code === 'Space') return INPUT_UP
  if (code === 'ArrowDown' || code === 'KeyS') return INPUT_DOWN
  if (code === 'ArrowLeft' || code === 'KeyA') return INPUT_LEFT
  if (code === 'ArrowRight' || code === 'KeyD') return INPUT_RIGHT
  return 0
}

function onKeydown(event: KeyboardEvent) {
  if (isSpectating.value || phase.value !== 'playing') return
  const mask = keyboardMask(event.code)
  if (!mask) return
  event.preventDefault()
  heldMask.value |= mask
  queuedMask.value |= mask
}

function onKeyup(event: KeyboardEvent) {
  if (isSpectating.value) return
  const mask = keyboardMask(event.code)
  if (!mask) return
  event.preventDefault()
  heldMask.value &= ~mask
}

function onControlDown(event: PointerEvent, mask: number) {
  if (isSpectating.value || phase.value !== 'playing') return
  event.preventDefault()
  activePointers.set(event.pointerId, mask)
  ;(event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId)
  heldMask.value |= mask
  queuedMask.value |= mask
}

function onControlUp(event: PointerEvent) {
  const mask = activePointers.get(event.pointerId)
  if (mask === undefined) return
  activePointers.delete(event.pointerId)
  heldMask.value &= ~mask
}

function clearInput() {
  heldMask.value = 0
  queuedMask.value = 0
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

function drawCover(
  context: CanvasRenderingContext2D,
  image: HTMLImageElement,
  width: number,
  height: number,
) {
  const scale = Math.max(width / image.naturalWidth, height / image.naturalHeight)
  const sourceWidth = width / scale
  const sourceHeight = height / scale
  const sourceX = (image.naturalWidth - sourceWidth) / 2
  const sourceY = (image.naturalHeight - sourceHeight) / 2
  context.drawImage(
    image,
    sourceX,
    sourceY,
    sourceWidth,
    sourceHeight,
    0,
    0,
    width,
    height,
  )
}

function projectRoad(
  ticksAhead: number,
  width: number,
  height: number,
): Projection {
  const visibleTicks = profile.value.sectionIntervalTicks * 4.1
  const closeness = Math.max(0, Math.min(1, 1 - ticksAhead / visibleTicks))
  const depth = .035 + .965 * closeness ** 1.65
  return {
    y: height * .265 + depth * height * .59,
    halfWidth: width * (.045 + depth * .43),
    scale: .16 + depth * 1.02,
  }
}

function roadLaneCenter(
  lane: number,
  projection: Projection,
  width: number,
): number {
  return width / 2 + lane * projection.halfWidth * .62
}

function drawBridge(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  palette: CriticalCrossingPalette,
) {
  const horizonY = height * .265
  const bottomY = height * 1.03
  const horizonHalf = width * .045
  const bottomHalf = width * .49
  const deck = context.createLinearGradient(0, horizonY, 0, height)
  deck.addColorStop(0, palette.deckTop)
  deck.addColorStop(1, palette.deckBottom)

  context.beginPath()
  context.moveTo(width / 2 - horizonHalf, horizonY)
  context.lineTo(width / 2 + horizonHalf, horizonY)
  context.lineTo(width / 2 + bottomHalf, bottomY)
  context.lineTo(width / 2 - bottomHalf, bottomY)
  context.closePath()
  context.fillStyle = deck
  context.fill()

  context.strokeStyle = palette.deckEdge
  context.lineWidth = Math.max(2, width * .003)
  context.shadowColor = palette.railGlow
  context.shadowBlur = width * .012
  context.beginPath()
  context.moveTo(width / 2 - horizonHalf, horizonY)
  context.lineTo(width / 2 - bottomHalf, bottomY)
  context.moveTo(width / 2 + horizonHalf, horizonY)
  context.lineTo(width / 2 + bottomHalf, bottomY)
  context.stroke()
  context.shadowBlur = 0

  for (const divider of [-.31, .31]) {
    context.strokeStyle = palette.laneMark
    context.lineWidth = Math.max(1, width * .0016)
    context.setLineDash([height * .035, height * .027])
    context.lineDashOffset = crossingState.value.tick * height * .004
    context.beginPath()
    context.moveTo(width / 2 + divider * horizonHalf * 2, horizonY)
    context.lineTo(width / 2 + divider * bottomHalf * 2, bottomY)
    context.stroke()
  }
  context.setLineDash([])

  const seamOffset = (crossingState.value.tick * .017) % 1
  for (let seam = 0; seam < 13; seam += 1) {
    const value = (seam / 13 + seamOffset) % 1
    const curved = value ** 2.25
    const y = horizonY + curved * (bottomY - horizonY)
    const half = horizonHalf + curved * (bottomHalf - horizonHalf)
    context.strokeStyle = palette.deckDetail
    context.globalAlpha = .18 + curved * .32
    context.lineWidth = Math.max(1, curved * height * .004)
    context.beginPath()
    context.moveTo(width / 2 - half, y)
    context.lineTo(width / 2 + half, y)
    context.stroke()
  }
  context.globalAlpha = 1

  for (const side of [-1, 1]) {
    context.strokeStyle = palette.rail
    context.lineWidth = Math.max(1.5, width * .0022)
    context.beginPath()
    context.moveTo(width / 2 + side * horizonHalf, horizonY - height * .018)
    context.lineTo(width / 2 + side * bottomHalf, bottomY - height * .07)
    context.stroke()
    for (let post = 0; post < 10; post += 1) {
      const value = post / 9
      const curved = value ** 2
      const y = horizonY + curved * (bottomY - horizonY)
      const x = width / 2 + side * (
        horizonHalf + curved * (bottomHalf - horizonHalf)
      )
      const postHeight = height * (.012 + curved * .08)
      context.beginPath()
      context.moveTo(x, y)
      context.lineTo(x, y - postHeight)
      context.stroke()
    }
  }
}

function drawLanePlatform(
  context: CanvasRenderingContext2D,
  lane: RunnerLane,
  section: CourseSection,
  projection: Projection,
  width: number,
  palette: CriticalCrossingPalette,
) {
  const x = roadLaneCenter(lane, projection, width)
  const laneWidth = projection.halfWidth * .52
  const platformHeight = 24 * projection.scale
  const active = section.activeLanes.includes(lane)

  context.beginPath()
  context.roundRect(
    x - laneWidth / 2,
    projection.y - platformHeight / 2,
    laneWidth,
    platformHeight,
    Math.max(2, 5 * projection.scale),
  )
  context.fillStyle = active ? palette.deckTop : palette.gap
  context.globalAlpha = active ? .94 : .9
  context.fill()
  context.globalAlpha = 1
  context.strokeStyle = active ? palette.deckEdge : palette.barrier
  context.lineWidth = Math.max(1, 2 * projection.scale)
  context.stroke()
}

function drawObstacle(
  context: CanvasRenderingContext2D,
  lane: RunnerLane,
  kind: ObstacleKind,
  projection: Projection,
  width: number,
  palette: CriticalCrossingPalette,
) {
  if (kind === 'clear' || kind === 'gap') return
  const x = roadLaneCenter(lane, projection, width)
  const laneWidth = projection.halfWidth * .49
  const scale = projection.scale
  context.save()
  context.translate(x, projection.y)
  context.lineJoin = 'round'
  context.lineCap = 'round'

  if (kind === 'ground') {
    const height = 23 * scale
    context.fillStyle = palette.groundObstacle
    context.shadowColor = palette.groundObstacle
    context.shadowBlur = 10 * scale
    context.fillRect(-laneWidth * .38, -height, laneWidth * .76, height)
    context.fillStyle = palette.copy
    for (let stripe = -2; stripe <= 2; stripe += 1) {
      context.save()
      context.translate(stripe * laneWidth * .13, -height / 2)
      context.rotate(-.55)
      context.fillRect(-2 * scale, -height * .5, 4 * scale, height)
      context.restore()
    }
  } else if (kind === 'overhead') {
    const top = -68 * scale
    context.strokeStyle = palette.overheadObstacle
    context.lineWidth = Math.max(2, 6 * scale)
    context.shadowColor = palette.overheadObstacle
    context.shadowBlur = 11 * scale
    context.beginPath()
    context.moveTo(-laneWidth * .38, 2 * scale)
    context.lineTo(-laneWidth * .38, top)
    context.lineTo(laneWidth * .38, top)
    context.lineTo(laneWidth * .38, 2 * scale)
    context.stroke()
    context.fillStyle = palette.overheadObstacle
    context.fillRect(-laneWidth * .42, top - 5 * scale, laneWidth * .84, 13 * scale)
  } else {
    const obstacleHeight = 52 * scale
    context.fillStyle = palette.barrier
    context.strokeStyle = palette.copy
    context.lineWidth = Math.max(1, 3 * scale)
    context.shadowColor = palette.barrierGlow
    context.shadowBlur = 13 * scale
    context.beginPath()
    context.roundRect(
      -laneWidth * .4,
      -obstacleHeight,
      laneWidth * .8,
      obstacleHeight,
      5 * scale,
    )
    context.fill()
    context.beginPath()
    context.moveTo(-laneWidth * .25, -obstacleHeight * .8)
    context.lineTo(laneWidth * .25, -obstacleHeight * .2)
    context.moveTo(laneWidth * .25, -obstacleHeight * .8)
    context.lineTo(-laneWidth * .25, -obstacleHeight * .2)
    context.stroke()
  }
  context.restore()
}

function drawCourse(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  palette: CriticalCrossingPalette,
) {
  const visible = coursePlan.value
    .map(section => ({
      section,
      ticksAhead: section.impactTick - crossingState.value.tick,
    }))
    .filter(item => item.ticksAhead >= -3
      && item.ticksAhead <= profile.value.sectionIntervalTicks * 4.1)
    .sort((a, b) => b.ticksAhead - a.ticksAhead)

  for (const { section, ticksAhead } of visible) {
    const projection = projectRoad(ticksAhead, width, height)
    for (const lane of RUNNER_LANES) {
      drawLanePlatform(context, lane, section, projection, width, palette)
    }
    for (const lane of RUNNER_LANES) {
      drawObstacle(
        context,
        lane,
        section.obstacles[lane + 1],
        projection,
        width,
        palette,
      )
    }

    context.save()
    context.translate(width / 2, projection.y - 82 * projection.scale)
    context.fillStyle = palette.copy
    context.globalAlpha = Math.min(1, .38 + projection.scale * .45)
    context.font = `800 ${Math.max(7, 10 * projection.scale)}px ui-sans-serif`
    context.textAlign = 'center'
    context.fillText(`${section.branchCount} 路`, 0, 0)
    context.restore()
  }
}

function drawLimb(
  context: CanvasRenderingContext2D,
  points: readonly [number, number][],
  color: string,
  width: number,
) {
  context.strokeStyle = color
  context.lineWidth = width
  context.lineCap = 'round'
  context.lineJoin = 'round'
  context.beginPath()
  context.moveTo(points[0]![0], points[0]![1])
  for (const [x, y] of points.slice(1)) context.lineTo(x, y)
  context.stroke()
}

function drawRunner(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  palette: CriticalCrossingPalette,
) {
  const state = crossingState.value
  const lanePosition = runnerLanePosition(state, profile.value)
  const laneSpan = width * .268
  const groundY = height * .86
  const poseProgress = runnerPoseProgress(state, profile.value)
  const jumpHeight = state.pose === 'jump'
    ? Math.sin(Math.PI * poseProgress) * height * .17
    : 0
  const slideDrop = state.pose === 'slide' ? height * .025 : 0
  const x = width / 2 + lanePosition * laneSpan
  const y = groundY - jumpHeight + slideDrop
  const scale = Math.max(.66, Math.min(1.3, height / 570))
  const runSwing = Math.sin(state.tick * .57) * 17
  const changeDirection = Math.sign(state.lane - state.laneChangeFrom)
  const laneProgress = state.laneChangeTicks > 0
    ? 1 - state.laneChangeTicks / profile.value.laneChangeTicks
    : 0
  const lean = changeDirection * Math.sin(Math.PI * laneProgress) * .16
  const interrupted = state.collisionTick !== null

  context.save()
  context.translate(x, groundY + 7 * scale)
  context.scale(1 - jumpHeight / height * .65, .28)
  context.beginPath()
  context.ellipse(0, 0, 30 * scale, 13 * scale, 0, 0, Math.PI * 2)
  context.fillStyle = palette.shadow
  context.globalAlpha = state.pose === 'jump' ? .28 : .62
  context.fill()
  context.restore()

  context.save()
  context.translate(x, y)
  context.scale(scale, scale)
  context.rotate(interrupted ? .42 : lean)
  context.shadowColor = palette.shadow
  context.shadowBlur = 12

  if (state.pose === 'slide') {
    drawLimb(context, [[-2, -20], [16, -8], [39, -2]], palette.runnerBody, 11)
    drawLimb(context, [[-5, -18], [-17, -5], [-5, 1]], palette.runnerBody, 11)
    context.save()
    context.translate(0, -38)
    context.rotate(-.9)
    context.fillStyle = palette.runnerBody
    context.strokeStyle = palette.runnerEdge
    context.lineWidth = 2.5
    context.beginPath()
    context.roundRect(-13, -25, 27, 48, 9)
    context.fill()
    context.stroke()
    context.fillStyle = palette.runnerAccent
    context.fillRect(-13, 7, 27, 8)
    context.restore()
    drawLimb(context, [[-2, -51], [-21, -37], [-34, -28]], palette.runnerSkin, 7)
    context.beginPath()
    context.arc(-18, -66, 13, 0, Math.PI * 2)
    context.fillStyle = palette.runnerSkin
    context.fill()
  } else {
    const tuck = state.pose === 'jump' ? 18 * Math.sin(Math.PI * poseProgress) : 0
    drawLimb(
      context,
      [[-7, -35], [-11 - runSwing * .55, -17 - tuck], [-runSwing, 2 - tuck]],
      palette.runnerBody,
      11,
    )
    drawLimb(
      context,
      [[7, -35], [11 + runSwing * .55, -17 - tuck], [runSwing, 2 - tuck]],
      palette.runnerBody,
      11,
    )
    drawLimb(context, [[-10, -68], [runSwing * .55, -48], [runSwing * .8, -32]], palette.runnerSkin, 7)
    drawLimb(context, [[10, -68], [-runSwing * .55, -48], [-runSwing * .8, -32]], palette.runnerSkin, 7)

    context.fillStyle = palette.runnerBody
    context.strokeStyle = palette.runnerEdge
    context.lineWidth = 2.5
    context.beginPath()
    context.roundRect(-15, -81, 30, 50, 10)
    context.fill()
    context.stroke()
    context.fillStyle = palette.runnerAccent
    context.beginPath()
    context.moveTo(-15, -54)
    context.lineTo(15, -65)
    context.lineTo(15, -51)
    context.lineTo(-15, -40)
    context.closePath()
    context.fill()

    context.beginPath()
    context.arc(0, -99, 14, 0, Math.PI * 2)
    context.fillStyle = palette.runnerSkin
    context.fill()
    context.strokeStyle = palette.runnerEdge
    context.stroke()
    context.fillStyle = palette.runnerBody
    context.beginPath()
    context.arc(-2, -104, 14, Math.PI, Math.PI * 2)
    context.lineTo(12, -98)
    context.lineTo(-13, -99)
    context.closePath()
    context.fill()
  }
  context.shadowBlur = 0
  context.restore()
}

function drawSpeedLines(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  palette: CriticalCrossingPalette,
) {
  if (phase.value !== 'playing') return
  context.strokeStyle = palette.copy
  context.lineWidth = Math.max(1, width * .001)
  for (let index = 0; index < 14; index += 1) {
    const side = index % 2 === 0 ? -1 : 1
    const cycle = ((crossingState.value.tick * .035 + index * .137) % 1) ** 1.8
    const y = height * (.32 + cycle * .6)
    const x = width / 2 + side * width * (.12 + cycle * .42)
    context.globalAlpha = .06 + cycle * .24
    context.beginPath()
    context.moveTo(x, y)
    context.lineTo(x + side * width * .035, y + height * .055)
    context.stroke()
  }
  context.globalAlpha = 1
}

function drawArena() {
  const element = canvas.value
  const context = element?.getContext('2d')
  if (!element || !context) return
  const width = element.width
  const height = element.height
  const palette = criticalCrossingPalette(currentTheme.value)
  context.clearRect(0, 0, width, height)

  if (backdropImage.complete && backdropImage.naturalWidth > 0) {
    drawCover(context, backdropImage, width, height)
  } else {
    const fallback = context.createLinearGradient(0, 0, 0, height)
    fallback.addColorStop(0, '#397d9a')
    fallback.addColorStop(.48, '#f4a776')
    fallback.addColorStop(1, '#0a1c2c')
    context.fillStyle = fallback
    context.fillRect(0, 0, width, height)
  }
  context.fillStyle = palette.atmosphere
  context.fillRect(0, 0, width, height)

  drawBridge(context, width, height, palette)
  drawCourse(context, width, height, palette)
  drawSpeedLines(context, width, height, palette)
  drawRunner(context, width, height, palette)
}

async function restartChallenge() {
  if (isSpectating.value) return
  await arcade.restartGame()
}

async function returnToMain() {
  if (returning.value) return
  returning.value = true
  const returned = isSpectating.value || props.snapshot.phase === 'finished'
    ? await arcade.leaveRoom()
    : await arcade.abandonRoom()
  if (returned) await router.push({ name: 'hall' })
  else returning.value = false
}

watch(
  () => arcade.spectatorFrame,
  (spectatorFrame) => {
    if (isSpectating.value && spectatorFrame) {
      applySpectatorState(spectatorFrame.state)
    }
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
  backdropImage.addEventListener('load', drawArena)
  if (!isSpectating.value) {
    window.addEventListener('keydown', onKeydown, { passive: false })
    window.addEventListener('keyup', onKeyup, { passive: false })
    window.addEventListener('blur', clearInput)
  }
  window.addEventListener('resize', resizeCanvas)
  nextTick(() => {
    resizeCanvas()
    if (props.snapshot.phase === 'playing' && !isSpectating.value) {
      beginReadySequence()
    }
  })
})

onBeforeUnmount(() => {
  clearLoop()
  backdropImage.removeEventListener('load', drawArena)
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('keyup', onKeyup)
  window.removeEventListener('blur', clearInput)
  window.removeEventListener('resize', resizeCanvas)
})
</script>

<template>
  <section class="crossing-game">
    <header class="surface crossing-status">
      <span class="crossing-status-mark"><Footprints :size="25" /></span>
      <div class="crossing-status-copy">
        <small>MATH RUNNER · {{ game.difficultyLabel }}</small>
        <strong>算途疾行 · 云桥赛道</strong>
      </div>
      <div class="crossing-section-track" :aria-label="`共 ${sectionCount} 段桥面`">
        <i
          v-for="section in sectionCount"
          :key="section"
          :class="{
            complete: section <= crossingState.passedSections,
            current: section - 1 === nextSectionIndex && phase === 'playing',
          }"
        />
      </div>
      <button
        class="return-main"
        type="button"
        :disabled="returning || arcade.busy"
        @click="returnToMain"
      >
        <House :size="17" />
        返回主界面
      </button>
    </header>

    <SoloMetricGrid
      aria-label="算途疾行状态"
      :items="[
        { label: '前进距离', value: `${distanceMeters} 米`, tone: 'success' },
        { label: '桥面进度', value: `${crossingState.passedSections} / ${sectionCount}` },
        { label: '人物动作', value: poseLabel, tone: crossingState.pose === 'run' ? undefined : 'warning' },
      ]"
    />

    <section class="crossing-arena surface" :class="`phase-${phase}`">
      <canvas ref="canvas" aria-label="算途疾行三轨云桥跑酷区域" />

      <div v-if="phase === 'ready'" class="arena-overlay ready-overlay">
        <small>电脑键盘 · A/D 变道 · W 跳跃 · S 下蹲</small>
        <strong>{{ readyCount }}</strong>
        <span>双脚开跑，观察前方分叉与上下障碍</span>
      </div>

      <div v-else-if="phase === 'submitting'" class="arena-overlay result-overlay">
        <CircleX v-if="crossingState.collisionTick !== null" :size="36" />
        <ShieldCheck v-else :size="36" />
        <strong>{{ crossingState.collisionTick !== null ? collisionLabel : '抵达终点' }}</strong>
        <span>{{ submitError || `正在校验 ${inputs.length} 帧键盘轨迹…` }}</span>
        <button v-if="submitError" type="button" @click="retrySubmission">重新校验</button>
      </div>

      <div
        v-else-if="phase === 'finished'"
        class="arena-overlay finished-overlay"
        :class="{ crossed: game.crossed }"
      >
        <Sparkles v-if="game.crossed" :size="40" />
        <CircleX v-else :size="40" />
        <strong>{{ game.crossed ? `${resultDistanceMeters} 米疾行完成` : '本次疾行中断' }}</strong>
        <span>{{ snapshot.winReason }}</span>
      </div>

      <div v-if="phase === 'playing'" class="arena-timer" aria-live="polite">
        <small>BRIDGE RUN</small><strong>{{ remainingLabel }}</strong>
      </div>

      <div
        v-if="phase !== 'finished' && phase !== 'submitting' && nextSection"
        class="fork-radar"
        aria-live="polite"
      >
        <span>{{ nextSection.branchCount }}</span>
        <div>
          <small>前方分叉</small>
          <strong>{{ (nextSectionTicks / TICK_RATE).toFixed(1) }} 秒抵达</strong>
        </div>
      </div>

      <div
        v-if="phase !== 'finished' && phase !== 'submitting' && nextSection"
        class="obstacle-radar"
      >
        <span
          v-for="(kind, index) in nextSection.obstacles"
          :key="index"
          :class="`obstacle-${kind}`"
        >{{ obstacleLabel(kind) }}</span>
      </div>
    </section>

    <div v-if="snapshot.phase === 'playing'" class="runner-controls" aria-label="跑酷动作控制">
      <button
        type="button"
        :disabled="isSpectating"
        aria-label="向左变道"
        @pointerdown="onControlDown($event, INPUT_LEFT)"
        @pointerup="onControlUp"
        @pointercancel="onControlUp"
        @lostpointercapture="onControlUp"
      ><ArrowLeft :size="23" /><span><kbd>A</kbd> 左变道</span></button>
      <button
        type="button"
        :disabled="isSpectating"
        aria-label="跳跃"
        @pointerdown="onControlDown($event, INPUT_UP)"
        @pointerup="onControlUp"
        @pointercancel="onControlUp"
        @lostpointercapture="onControlUp"
      ><ArrowUp :size="23" /><span><kbd>W</kbd> 跳跃</span></button>
      <button
        type="button"
        :disabled="isSpectating"
        aria-label="下蹲滑行"
        @pointerdown="onControlDown($event, INPUT_DOWN)"
        @pointerup="onControlUp"
        @pointercancel="onControlUp"
        @lostpointercapture="onControlUp"
      ><ArrowDown :size="23" /><span><kbd>S</kbd> 下蹲</span></button>
      <button
        type="button"
        :disabled="isSpectating"
        aria-label="向右变道"
        @pointerdown="onControlDown($event, INPUT_RIGHT)"
        @pointerup="onControlUp"
        @pointercancel="onControlUp"
        @lostpointercapture="onControlUp"
      ><ArrowRight :size="23" /><span><kbd>D</kbd> 右变道</span></button>
    </div>

    <p class="crossing-hint">
      人物会自动向前跑：<kbd>A</kbd><kbd>D</kbd> 左右变道，<kbd>W</kbd>/<kbd>空格</kbd>
      跳过地面障碍，<kbd>S</kbd> 下蹲避开上方障碍
    </p>

    <SoloResultCard
      v-if="snapshot.phase === 'finished'"
      :eyebrow="game.crossed ? '云桥疾行完成' : collisionLabel"
      :title="game.crossed ? '双脚跑过整段算途' : '观察分叉，再跑一次'"
      :score="resultDistanceMeters"
      score-unit="米"
      :description="snapshot.winReason"
      :tone="game.crossed ? 'success' : 'danger'"
      :metrics="[
        { label: '挑战模式', value: `${game.difficultyLabel} · ${durationSeconds} 秒` },
        { label: '通过桥段', value: `${resultPassedSections} / ${sectionCount}` },
        { label: '服务端校验', value: `${game.tickRate} Hz` },
      ]"
      :can-restart="snapshot.actions.canRestart"
      :busy="arcade.busy"
      restart-label="重新起跑"
      @restart="restartChallenge"
    />
  </section>
</template>

<style scoped>
.crossing-game {
  --runner-accent: #ff7a48;
  width: min(100%, 1080px);
  display: grid;
  gap: 14px;
  margin: 0 auto;
}

.crossing-status {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 13px;
  padding: 12px 14px;
  border-color: color-mix(in srgb, var(--runner-accent) 25%, var(--line));
}

.crossing-status-mark {
  width: 46px;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--runner-accent) 42%, var(--line));
  border-radius: 15px;
  color: var(--runner-accent);
  background: color-mix(in srgb, var(--runner-accent) 10%, var(--surface-inset));
}

.crossing-status-copy { min-width: 0; }
.crossing-status-copy small,
.crossing-status-copy strong { display: block; }
.crossing-status-copy small {
  color: var(--runner-accent);
  font-size: 8px;
  font-weight: 950;
  letter-spacing: .14em;
}
.crossing-status-copy strong { margin-top: 4px; font-size: 17px; }

.crossing-section-track { display: flex; gap: 5px; }
.crossing-section-track i {
  width: 12px;
  height: 4px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--muted) 26%, transparent);
}
.crossing-section-track i.complete { background: color-mix(in srgb, var(--accent) 70%, var(--line)); }
.crossing-section-track i.current {
  width: 23px;
  background: var(--runner-accent);
  box-shadow: 0 0 12px color-mix(in srgb, var(--runner-accent) 68%, transparent);
}

.return-main {
  min-height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border: 1px solid color-mix(in srgb, var(--runner-accent) 38%, var(--line));
  border-radius: 11px;
  padding: 0 12px;
  color: var(--text);
  background: color-mix(in srgb, var(--runner-accent) 9%, var(--surface-inset));
  font-size: 10px;
  font-weight: 900;
  cursor: pointer;
}
.return-main:hover { border-color: var(--runner-accent); color: var(--runner-accent); }
.return-main:disabled { cursor: wait; opacity: .56; }

.crossing-arena {
  position: relative;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  border-color: color-mix(in srgb, var(--runner-accent) 38%, var(--line));
  background: #0a1c2c;
  box-shadow: var(--shadow-raised), inset 0 0 90px rgba(0, 13, 25, .5);
  isolation: isolate;
}
.crossing-arena::after {
  position: absolute;
  z-index: 6;
  inset: 7px;
  border: 1px solid color-mix(in srgb, white 18%, transparent);
  border-radius: calc(var(--radius-panel) - 7px);
  content: '';
  pointer-events: none;
}
.crossing-arena canvas { width: 100%; height: 100%; display: block; }

.arena-overlay {
  position: absolute;
  z-index: 5;
  inset: 0;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  padding: 24px;
  color: #f7fbff;
  text-align: center;
  background: linear-gradient(180deg, rgba(4, 20, 34, .34), rgba(4, 14, 25, .74));
  backdrop-filter: blur(3px);
}
.arena-overlay small {
  color: #ffc09e;
  font-size: 10px;
  font-weight: 950;
  letter-spacing: .12em;
}
.arena-overlay strong { font-family: "Songti SC", "STSong", serif; }
.ready-overlay strong {
  color: #ff8b5d;
  font-size: clamp(72px, 16vw, 132px);
  line-height: .88;
  text-shadow: 0 0 38px rgba(255, 119, 70, .65);
}
.ready-overlay span { color: #e7f4ff; font-weight: 850; letter-spacing: .08em; }
.result-overlay svg,
.finished-overlay svg { color: #ff6b78; filter: drop-shadow(0 0 14px rgba(255, 80, 99, .55)); }
.result-overlay strong,
.finished-overlay strong { font-size: clamp(30px, 6vw, 54px); }
.result-overlay span,
.finished-overlay span { max-width: 500px; color: #d4e4f0; font-size: 11px; line-height: 1.7; }
.finished-overlay.crossed svg { color: #67e0cf; }
.result-overlay button {
  margin-top: 7px;
  border: 1px solid rgba(255, 107, 120, .65);
  border-radius: 11px;
  padding: 10px 16px;
  color: white;
  background: rgba(255, 107, 120, .14);
  font-weight: 850;
  cursor: pointer;
}

.arena-timer {
  position: absolute;
  z-index: 3;
  top: 15px;
  left: 50%;
  display: grid;
  justify-items: center;
  border: 1px solid rgba(255, 255, 255, .24);
  border-radius: 999px;
  padding: 6px 15px;
  color: white;
  background: rgba(5, 20, 33, .68);
  transform: translateX(-50%);
  backdrop-filter: blur(9px);
}
.arena-timer small { color: #ff9a70; font-size: 7px; font-weight: 950; letter-spacing: .18em; }
.arena-timer strong { font-size: 18px; font-variant-numeric: tabular-nums; }

.fork-radar {
  position: absolute;
  z-index: 3;
  top: 15px;
  left: 15px;
  display: flex;
  align-items: center;
  gap: 9px;
  border: 1px solid rgba(103, 224, 207, .52);
  border-radius: 13px;
  padding: 8px 11px;
  color: white;
  background: rgba(5, 20, 33, .7);
  backdrop-filter: blur(9px);
}
.fork-radar > span {
  width: 32px;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: #062229;
  background: #67e0cf;
  font-size: 18px;
  font-weight: 950;
}
.fork-radar div { display: grid; gap: 2px; }
.fork-radar small { color: #9fc9d5; font-size: 7px; font-weight: 900; letter-spacing: .1em; }
.fork-radar strong { font-size: 10px; }

.obstacle-radar {
  position: absolute;
  z-index: 3;
  right: 15px;
  bottom: 15px;
  display: grid;
  grid-template-columns: repeat(3, minmax(44px, 1fr));
  gap: 5px;
  border: 1px solid rgba(255, 255, 255, .2);
  border-radius: 12px;
  padding: 6px;
  background: rgba(5, 20, 33, .7);
  backdrop-filter: blur(9px);
}
.obstacle-radar span {
  border-radius: 8px;
  padding: 6px 7px;
  color: white;
  background: rgba(103, 224, 207, .22);
  font-size: 8px;
  font-weight: 900;
  text-align: center;
}
.obstacle-radar .obstacle-barrier,
.obstacle-radar .obstacle-gap { background: rgba(255, 84, 105, .3); }
.obstacle-radar .obstacle-ground { background: rgba(255, 196, 91, .32); }
.obstacle-radar .obstacle-overhead { background: rgba(103, 224, 207, .32); }

.runner-controls {
  width: min(100%, 680px);
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin: 0 auto;
  user-select: none;
  touch-action: none;
}
.runner-controls button {
  min-height: 54px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid color-mix(in srgb, var(--runner-accent) 34%, var(--line));
  border-radius: 14px;
  color: var(--text);
  background: var(--control-surface), var(--surface-inset);
  box-shadow: var(--shadow-contact), inset 0 1px 0 color-mix(in srgb, white 16%, transparent);
  touch-action: none;
  cursor: pointer;
}
.runner-controls button:active {
  color: white;
  background: var(--runner-accent);
  transform: translateY(2px);
}
.runner-controls button span { font-size: 9px; font-weight: 900; }
.runner-controls kbd,
.crossing-hint kbd {
  display: inline-grid;
  min-width: 22px;
  place-items: center;
  margin: 0 1px;
  border: 1px solid var(--line);
  border-bottom-width: 2px;
  border-radius: 5px;
  padding: 2px 5px;
  color: var(--text);
  background: var(--surface-inset);
  font: inherit;
  font-weight: 950;
}
.crossing-hint { margin: -3px 0 0; color: var(--muted); font-size: 9px; text-align: center; }

@media (min-width: 760px) and (hover: hover) and (pointer: fine) {
  .runner-controls { display: none; }
}

@media (max-width: 760px) {
  .crossing-status { grid-template-columns: auto minmax(0, 1fr) auto; }
  .crossing-section-track { grid-column: 1 / -1; grid-row: 2; justify-content: center; }
  .return-main { grid-column: 3; grid-row: 1; padding: 0 9px; }
  .return-main svg { display: none; }
  .crossing-arena { aspect-ratio: 4 / 3; }
  .runner-controls { grid-template-columns: repeat(2, 1fr); }
  .crossing-hint { line-height: 1.9; }
}

@media (max-width: 480px) {
  .crossing-status-copy strong { font-size: 14px; }
  .return-main { font-size: 8px; }
  .fork-radar { top: 10px; left: 10px; }
  .obstacle-radar { right: 10px; bottom: 10px; }
  .arena-timer { top: 10px; }
}

@media (orientation: landscape) and (max-height: 560px) {
  .crossing-game { grid-template-columns: minmax(0, 1fr) 180px; width: min(100%, 1040px); }
  .crossing-game > :first-child,
  .crossing-game > :nth-child(2) { grid-column: 1 / -1; }
  .crossing-arena { grid-column: 1; }
  .runner-controls { grid-column: 2; align-self: center; grid-template-columns: 1fr; }
  .crossing-hint { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .runner-controls button:active { transform: none; }
}
</style>
