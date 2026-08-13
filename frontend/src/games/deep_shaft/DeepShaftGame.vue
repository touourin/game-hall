<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { CirclePause, CirclePlay, Heart, MapPin, ShieldAlert, Trophy } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import SoloMetricGrid from '../shared/solo/SoloMetricGrid.vue'
import SoloResultCard from '../shared/solo/SoloResultCard.vue'
import DeepShaftControls from './DeepShaftControls.vue'
import {
  CEILING_DEPTH,
  CRUMBLE_DELAY_TICKS,
  INPUT_LEFT,
  INPUT_RIGHT,
  MAX_TICKS,
  PLATFORM_GAP,
  PLAYER_HALF_HEIGHT,
  PLAYER_HALF_WIDTH,
  TARGET_FLOOR,
  TICK_RATE,
  VIEW_HEIGHT,
  WORLD_WIDTH,
  advanceShaftState,
  createShaftState,
  generatePlatforms,
  type ShaftPlatform,
  type ShaftState,
} from './deepShaftEngine'

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

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const canvas = ref<HTMLCanvasElement | null>(null)
const phase = ref<'ready' | 'playing' | 'paused' | 'submitting' | 'finished'>(
  props.snapshot.phase === 'finished' ? 'finished' : 'ready',
)
const state = ref<ShaftState>(createShaftState(1))
const inputs = ref<number[]>([])
const heldMask = ref(0)
const submitError = ref<string | null>(null)
const activePointers = new Map<number, number>()
let animationFrame: number | null = null
let previousFrame = 0
let accumulator = 0
let submitted = false

const game = computed(() => props.snapshot.game as unknown as ServerGame)
const platforms = computed(() => generatePlatforms(game.value.seed))
const elapsedMs = computed(() => Math.round(state.value.tick * 1_000 / TICK_RATE))
const elapsedLabel = computed(() => {
  const total = Math.floor(elapsedMs.value / 1_000)
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`
})
const healthTone = computed(() => state.value.health <= 3 ? 'danger' : state.value.health <= 6 ? 'warning' : 'success')
const progress = computed(() => Math.min(100, state.value.deepestFloor))

const platformKindLabel = computed(() => {
  if (state.value.lastLandedKind === 'spikes') return '尖刺'
  if (state.value.lastLandedKind === 'crumble') return '碎裂'
  if (state.value.lastLandedKind === 'spring') return '弹簧'
  if (state.value.lastLandedKind.startsWith('conveyor')) return '传送带'
  return '普通'
})

function stopFrame() {
  if (animationFrame !== null) window.cancelAnimationFrame(animationFrame)
  animationFrame = null
}

function freshRun() {
  stopFrame()
  state.value = createShaftState(game.value.seed)
  inputs.value = []
  heldMask.value = 0
  submitError.value = null
  submitted = false
  activePointers.clear()
  phase.value = 'ready'
  draw()
}

function startRun() {
  if (phase.value !== 'ready') return
  phase.value = 'playing'
  previousFrame = performance.now()
  accumulator = 0
  animationFrame = window.requestAnimationFrame(frame)
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
  draw()
  if (phase.value === 'playing') animationFrame = window.requestAnimationFrame(frame)
}

async function submitRun() {
  if (submitted) return
  submitted = true
  phase.value = 'submitting'
  stopFrame()
  heldMask.value = 0
  draw()
  const successful = await arcade.actionWithResult('finish', { inputs: inputs.value })
  if (!successful) {
    submitError.value = arcade.error ?? '轨迹校验失败，请重新提交'
    submitted = false
  }
}

function togglePause() {
  if (phase.value === 'playing') {
    phase.value = 'paused'
    heldMask.value = 0
    stopFrame()
    draw()
  } else if (phase.value === 'paused') {
    phase.value = 'playing'
    previousFrame = performance.now()
    animationFrame = window.requestAnimationFrame(frame)
  }
}

function keyboardMask(code: string): number {
  if (code === 'ArrowLeft' || code === 'KeyA') return INPUT_LEFT
  if (code === 'ArrowRight' || code === 'KeyD') return INPUT_RIGHT
  return 0
}

function onKeydown(event: KeyboardEvent) {
  if (event.code === 'Space' || event.code === 'KeyP' || event.code === 'Escape') {
    if (event.repeat) return
    event.preventDefault()
    if (phase.value === 'ready') startRun()
    else togglePause()
    return
  }
  const mask = keyboardMask(event.code)
  if (!mask) return
  event.preventDefault()
  if (phase.value === 'ready') startRun()
  heldMask.value |= mask
}

function onKeyup(event: KeyboardEvent) {
  const mask = keyboardMask(event.code)
  if (!mask) return
  event.preventDefault()
  heldMask.value &= ~mask
}

function onControlDown(direction: -1 | 1, event: PointerEvent) {
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

function platformColor(platform: ShaftPlatform): string {
  if (platform.kind === 'spikes') return '#d96b62'
  if (platform.kind === 'crumble') return '#c6945e'
  if (platform.kind === 'spring') return '#9a78d0'
  if (platform.kind.startsWith('conveyor')) return '#5a9caa'
  return '#708f88'
}

function drawPlatform(context: CanvasRenderingContext2D, platform: ShaftPlatform, scale: number, offsetX: number) {
  if (state.value.brokenFloors.has(platform.floor)) return
  const y = (platform.y - state.value.cameraY) * scale
  if (y < -120 || y > context.canvas.height + 120) return
  const x = offsetX + platform.x * scale
  const width = platform.width * scale
  const height = Math.max(11, 125 * scale)
  context.fillStyle = platformColor(platform)
  context.shadowColor = platformColor(platform)
  context.shadowBlur = 8 * scale
  context.fillRect(x, y, width, height)
  context.shadowBlur = 0
  context.fillStyle = 'rgba(255,255,255,.18)'
  context.fillRect(x, y, width, Math.max(2, 18 * scale))
  context.strokeStyle = 'rgba(5,13,16,.68)'
  context.lineWidth = Math.max(1, 15 * scale)
  context.strokeRect(x, y, width, height)

  if (platform.kind === 'spikes') {
    const spikeWidth = Math.max(8, 170 * scale)
    for (let spikeX = x + spikeWidth * .15; spikeX < x + width - spikeWidth; spikeX += spikeWidth) {
      context.beginPath()
      context.moveTo(spikeX, y)
      context.lineTo(spikeX + spikeWidth / 2, y - 135 * scale)
      context.lineTo(spikeX + spikeWidth, y)
      context.fillStyle = '#ff9a7d'
      context.fill()
    }
  } else if (platform.kind === 'crumble') {
    const remaining = state.value.crumbleDue.get(platform.floor)
    const alpha = remaining === undefined
      ? .45
      : Math.max(.08, (remaining - state.value.tick) / CRUMBLE_DELAY_TICKS)
    context.strokeStyle = `rgba(44,24,12,${alpha})`
    context.beginPath()
    context.moveTo(x + width * .28, y)
    context.lineTo(x + width * .42, y + height)
    context.moveTo(x + width * .68, y)
    context.lineTo(x + width * .57, y + height)
    context.stroke()
  } else if (platform.kind === 'spring') {
    context.strokeStyle = '#d8c0ff'
    context.lineWidth = Math.max(2, 25 * scale)
    context.beginPath()
    for (let index = 0; index <= 8; index += 1) {
      const springX = x + width * .38 + index * width * .03
      const springY = y - (index % 2 ? 80 : 15) * scale
      if (index === 0) context.moveTo(springX, springY)
      else context.lineTo(springX, springY)
    }
    context.stroke()
  } else if (platform.kind.startsWith('conveyor')) {
    context.fillStyle = '#b9eef0'
    const direction = platform.kind === 'conveyor_left' ? -1 : 1
    for (let marker = x + 80 * scale; marker < x + width - 80 * scale; marker += 290 * scale) {
      context.beginPath()
      context.moveTo(marker, y + height * .5)
      context.lineTo(marker + direction * 90 * scale, y + height * .2)
      context.lineTo(marker + direction * 90 * scale, y + height * .8)
      context.fill()
    }
  }
  context.fillStyle = 'rgba(231,245,241,.8)'
  context.font = `800 ${Math.max(8, 105 * scale)}px system-ui`
  context.fillText(String(platform.floor), x + 18 * scale, y + height + 120 * scale)
}

function draw() {
  const element = canvas.value
  const context = element?.getContext('2d')
  if (!element || !context) return
  const width = element.width
  const height = element.height
  const scale = Math.min(width / WORLD_WIDTH, height / VIEW_HEIGHT)
  const offsetX = (width - WORLD_WIDTH * scale) / 2
  const background = context.createLinearGradient(0, 0, 0, height)
  background.addColorStop(0, '#07181d')
  background.addColorStop(.55, '#09262c')
  background.addColorStop(1, '#041015')
  context.fillStyle = background
  context.fillRect(0, 0, width, height)

  context.strokeStyle = 'rgba(104,190,190,.07)'
  context.lineWidth = 1
  for (let x = offsetX; x <= width - offsetX; x += 850 * scale) {
    context.beginPath(); context.moveTo(x, 0); context.lineTo(x, height); context.stroke()
  }
  for (const platform of platforms.value) drawPlatform(context, platform, scale, offsetX)

  const ceilingHeight = CEILING_DEPTH * scale
  context.fillStyle = '#7b3033'
  for (let x = offsetX; x < width - offsetX; x += 260 * scale) {
    context.beginPath()
    context.moveTo(x, 0)
    context.lineTo(x + 130 * scale, ceilingHeight)
    context.lineTo(x + 260 * scale, 0)
    context.fill()
  }
  const playerX = offsetX + state.value.playerX * scale
  const playerY = (state.value.playerY - state.value.cameraY) * scale
  const halfWidth = Math.max(7, PLAYER_HALF_WIDTH * scale)
  const halfHeight = Math.max(9, PLAYER_HALF_HEIGHT * scale)
  context.save()
  context.translate(playerX, playerY)
  context.shadowColor = '#6de3da'
  context.shadowBlur = halfWidth * 1.4
  context.fillStyle = state.value.health <= 3 ? '#ff8279' : '#73ddd3'
  context.beginPath()
  context.roundRect(-halfWidth, -halfHeight, halfWidth * 2, halfHeight * 2, halfWidth * .55)
  context.fill()
  context.shadowBlur = 0
  context.fillStyle = '#d9ffff'
  context.beginPath()
  context.arc(halfWidth * .28, -halfHeight * .25, halfWidth * .22, 0, Math.PI * 2)
  context.fill()
  context.restore()
}

async function restartChallenge() {
  await arcade.restartGame()
}

watch(
  () => [props.snapshot.phase, game.value.seed] as const,
  async ([snapshotPhase], [previousPhase, previousSeed]) => {
    if (snapshotPhase === 'finished') {
      stopFrame()
      phase.value = 'finished'
      return
    }
    if (snapshotPhase === 'playing' && (previousPhase === 'finished' || game.value.seed !== previousSeed)) {
      await nextTick()
      freshRun()
    }
  },
)

onMounted(() => {
  window.addEventListener('keydown', onKeydown, { passive: false })
  window.addEventListener('keyup', onKeyup, { passive: false })
  window.addEventListener('blur', clearInput)
  window.addEventListener('resize', resizeCanvas)
  state.value = createShaftState(game.value.seed)
  resizeCanvas()
  if (props.snapshot.phase === 'playing') freshRun()
})

onBeforeUnmount(() => {
  stopFrame()
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('keyup', onKeyup)
  window.removeEventListener('blur', clearInput)
  window.removeEventListener('resize', resizeCanvas)
})
</script>

<template>
  <section class="deep-shaft-game">
    <SoloMetricGrid
      aria-label="深井挑战状态"
      :columns="4"
      :items="[
        { label: '最深层数', value: `${state.deepestFloor} / ${TARGET_FLOOR}`, tone: 'success' },
        { label: '生命值', value: `${state.health} / ${game.maxHealth}`, tone: healthTone },
        { label: '挑战用时', value: elapsedLabel },
        { label: '当前平台', value: platformKindLabel },
      ]"
    />

    <section class="shaft-console surface" :class="`phase-${phase}`">
      <canvas ref="canvas" aria-label="百层深井游戏区域" />
      <div class="shaft-progress" aria-hidden="true"><i :style="{ height: `${progress}%` }" /><span>{{ state.deepestFloor }}F</span></div>
      <button v-if="['playing', 'paused'].includes(phase)" class="pause-button" type="button" @click="togglePause">
        <CirclePlay v-if="phase === 'paused'" :size="17" /><CirclePause v-else :size="17" />{{ phase === 'paused' ? '继续' : '暂停' }}
      </button>
      <div v-if="phase === 'ready'" class="shaft-overlay ready-overlay">
        <MapPin :size="34" />
        <strong>准备深入百层</strong>
        <span>方向键 / A D 控制左右，手机按住屏幕下方按钮</span>
        <button type="button" @click="startRun">开始下降</button>
      </div>
      <div v-else-if="phase === 'paused'" class="shaft-overlay">
        <CirclePause :size="34" /><strong>挑战暂停</strong><span>继续后镜头才会恢复下压</span><button type="button" @click="togglePause">继续挑战</button>
      </div>
      <div v-else-if="phase === 'submitting'" class="shaft-overlay">
        <ShieldAlert :size="34" /><strong>{{ state.endReason === 'completed' ? '百层抵达' : '本轮结束' }}</strong><span>{{ submitError || `正在校验 ${inputs.length.toLocaleString()} 帧左右输入…` }}</span><button v-if="submitError" type="button" @click="submitRun">重新校验</button>
      </div>
      <div v-else-if="phase === 'finished'" class="shaft-overlay finished-overlay">
        <Trophy v-if="game.endReason === 'completed'" :size="38" /><Heart v-else :size="38" />
        <strong>{{ game.endReason === 'completed' ? '百层通关' : `最深 ${game.deepestFloor} 层` }}</strong>
        <span>{{ snapshot.winReason }}</span>
      </div>
    </section>

    <DeepShaftControls
      v-if="snapshot.phase === 'playing'"
      :disabled="!['ready', 'playing'].includes(phase)"
      @press="onControlDown"
      @release="onControlUp"
    />
    <p class="shaft-hint"><kbd>←</kbd><kbd>→</kbd> 或 <kbd>A</kbd><kbd>D</kbd> 移动 · 普通平台回血 · 尖刺扣血 · 不要被顶部追上，也别掉出底部</p>

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
.deep-shaft-game { width: min(100%, 760px); margin: 0 auto; display: grid; gap: 14px; }
.shaft-console { position: relative; width: min(100%, 610px); aspect-ratio: 10 / 12; margin: 0 auto; overflow: hidden; border-color: color-mix(in srgb, #65d8d0 34%, var(--line)); background: #041015; box-shadow: var(--shadow-raised), inset 0 0 90px #000a; }
.shaft-console canvas { width: 100%; height: 100%; display: block; }
.shaft-progress { position: absolute; z-index: 2; top: 58px; right: 13px; bottom: 18px; width: 7px; overflow: hidden; border-radius: 999px; background: #ffffff17; }.shaft-progress i { position: absolute; right: 0; bottom: 0; left: 0; border-radius: inherit; background: linear-gradient(#e9a968,#5dd5cc); }.shaft-progress span { position: absolute; top: -25px; right: -4px; color: #bdeee8; font-size: 8px; font-weight: 900; white-space: nowrap; }
.pause-button { position: absolute; z-index: 3; top: 13px; right: 13px; display: inline-flex; align-items: center; gap: 6px; border: 1px solid #ffffff21; border-radius: 999px; padding: 7px 11px; color: #d6f5f0; background: #051418a8; backdrop-filter: blur(8px); }
.shaft-overlay { position: absolute; z-index: 4; inset: 0; display: grid; place-items: center; align-content: center; gap: 9px; padding: 24px; color: #daf6f2; background: #031216ce; text-align: center; backdrop-filter: blur(5px); }.shaft-overlay svg { color: #69d9d0; filter: drop-shadow(0 0 14px #54cbbf77); }.shaft-overlay strong { font-size: clamp(25px,6vw,42px); }.shaft-overlay span { max-width: 420px; color: #a9c8c4; line-height: 1.6; }.shaft-overlay button { margin-top: 7px; border: 1px solid #65d8d066; border-radius: 11px; padding: 10px 16px; color: #c9f8f2; background: #65d8d018; font-weight: 850; }.finished-overlay svg { color: #efa861; }
.shaft-hint { margin: -3px 0 0; color: var(--muted); font-size: 9px; text-align: center; line-height: 1.7; }.shaft-hint kbd { margin: 0 1px; border: 1px solid var(--line); border-bottom-width: 2px; border-radius: 5px; padding: 2px 5px; color: var(--text); background: var(--surface-inset); font: inherit; font-weight: 900; }
@media (max-width: 600px) { .shaft-console { width: min(100%, 480px); aspect-ratio: 4 / 5; }.deep-shaft-game { gap: 10px; } }
@media (orientation: landscape) and (max-height: 580px) { .deep-shaft-game { width: min(100%, 940px); grid-template-columns: minmax(300px, 1fr) 260px; align-items: center; }.deep-shaft-game > :first-child { grid-column: 1 / -1; }.shaft-console { grid-column: 1; height: min(66vh, 440px); width: auto; }.shaft-controls { grid-column: 2; }.shaft-hint { display: none; } }
@media (prefers-reduced-motion: reduce) { .shaft-overlay { backdrop-filter: none; } }
</style>
