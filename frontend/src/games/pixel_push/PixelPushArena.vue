<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Gauge, Shield, Sparkles, Trophy } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import PixelPushControls from './PixelPushControls.vue'
import type {
  PixelPushFrame,
  PixelPushGameState,
  PixelPushMapKey,
  PixelPushPlayerState,
} from './types'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const canvas = ref<HTMLCanvasElement | null>(null)
const canvasShell = ref<HTMLElement | null>(null)
const latestInputMask = ref(0)
let animationFrame: number | null = null
let resizeObserver: ResizeObserver | null = null
let inputSequence = 0
let frameReceivedAt = 0
let previousTargets = new Map<string, PixelPushPlayerState>()
let currentTargets = new Map<string, PixelPushPlayerState>()

const game = computed(() => props.snapshot.game as unknown as PixelPushGameState)
const realtimeFrame = computed(() => {
  const frame = arcade.realtimeFrame as PixelPushFrame | null
  return frame?.roomCode === props.snapshot.roomCode ? frame : null
})
const isSpectating = computed(() => props.snapshot.viewer?.mode === 'spectator')
const tickRate = computed(() => Number(game.value.tickRate || 30))
const stage = computed(() => realtimeFrame.value?.stage ?? game.value.stage)
const roundTicksRemaining = computed(() => (
  realtimeFrame.value?.roundTicksRemaining ?? game.value.roundTicksRemaining
))
const stageTicksRemaining = computed(() => (
  realtimeFrame.value?.stageTicksRemaining ?? game.value.stageTicksRemaining
))
const roundNumber = computed(() => realtimeFrame.value?.roundNumber ?? game.value.roundNumber)
const currentMap = computed(() => realtimeFrame.value?.currentMap ?? game.value.currentMap)
const shrinkProgress = computed(() => realtimeFrame.value?.shrinkProgress ?? game.value.shrinkProgress)
const roundWinnerId = computed(() => realtimeFrame.value?.roundWinnerId ?? game.value.roundWinnerId)
const roundWins = computed(() => realtimeFrame.value?.roundWins ?? game.value.roundWins)
const frozen = computed(() => realtimeFrame.value?.frozen ?? game.value.frozen)
const events = computed(() => realtimeFrame.value?.events ?? game.value.events)
const roster = computed(() => {
  const dynamic = new Map(
    (realtimeFrame.value?.players ?? game.value.players).map(player => [player.id, player]),
  )
  return game.value.players.map(player => ({
    ...player,
    ...dynamic.get(player.id),
    roundWins: roundWins.value[player.id] ?? player.roundWins ?? 0,
  }))
})
const selfPlayer = computed(() => roster.value.find(
  player => player.id === props.snapshot.self.id,
))
const controlsDisabled = computed(() => (
  isSpectating.value
  || props.snapshot.phase !== 'playing'
  || stage.value === 'round_result'
  || frozen.value
  || selfPlayer.value?.alive === false
))
const dashReady = computed(() => (selfPlayer.value?.dashCooldownTicks ?? 0) <= 0)
const roundSeconds = computed(() => Math.max(
  0,
  Math.ceil(roundTicksRemaining.value / tickRate.value),
))
const suddenDeath = computed(() => (
  stage.value === 'active' && roundSeconds.value <= 15
))
const mapName = computed(() => ({
  moon_station: '月台零号',
  cross_bridge: '十字断桥',
  pulse_factory: '脉冲工厂',
}[currentMap.value] ?? '像素擂台'))
const overlayTitle = computed(() => {
  if (frozen.value) return '等待玩家恢复'
  if (stage.value === 'countdown') {
    return String(Math.max(1, Math.ceil(stageTicksRemaining.value / tickRate.value)))
  }
  if (stage.value === 'round_result') {
    const winner = roster.value.find(player => player.id === roundWinnerId.value)
    return winner ? `${winner.name} 留在场上` : '本回合平局'
  }
  if (suddenDeath.value) return '突然死亡'
  return ''
})

function syncInputSequence() {
  inputSequence = Math.max(
    inputSequence,
    Number(game.value.selfInputSequence ?? -1) + 1,
    Number(selfPlayer.value?.lastInputSequence ?? -1) + 1,
  )
}

function sendInput(mask: number) {
  latestInputMask.value = mask
  if (isSpectating.value || props.snapshot.phase !== 'playing') return
  syncInputSequence()
  void arcade.realtimeInput(inputSequence, mask)
  inputSequence += 1
}

function copyPlayer(player: PixelPushPlayerState): PixelPushPlayerState {
  return { ...player }
}

function acceptTargets(players: PixelPushPlayerState[]) {
  const next = new Map(players.map(player => [player.id, copyPlayer(player)]))
  previousTargets = currentTargets.size
    ? new Map([...currentTargets].map(([id, player]) => [id, copyPlayer(player)]))
    : new Map([...next].map(([id, player]) => [id, copyPlayer(player)]))
  currentTargets = next
  frameReceivedAt = performance.now()
}

watch(
  () => realtimeFrame.value,
  frame => {
    if (frame) acceptTargets(frame.players)
  },
  { immediate: true },
)

watch(
  () => game.value.players,
  players => {
    if (!realtimeFrame.value) acceptTargets(players)
  },
  { immediate: true },
)

watch(controlsDisabled, disabled => {
  if (disabled && latestInputMask.value !== 0) sendInput(0)
})

function resizeCanvas() {
  const element = canvas.value
  if (!element) return
  const rect = element.getBoundingClientRect()
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  element.width = Math.max(1, Math.round(rect.width * dpr))
  element.height = Math.max(1, Math.round(rect.height * dpr))
}

function roundedRectPath(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
) {
  const right = x + width
  const bottom = y + height
  context.beginPath()
  context.moveTo(x + radius, y)
  context.lineTo(right - radius, y)
  context.quadraticCurveTo(right, y, right, y + radius)
  context.lineTo(right, bottom - radius)
  context.quadraticCurveTo(right, bottom, right - radius, bottom)
  context.lineTo(x + radius, bottom)
  context.quadraticCurveTo(x, bottom, x, bottom - radius)
  context.lineTo(x, y + radius)
  context.quadraticCurveTo(x, y, x + radius, y)
  context.closePath()
}

function arenaDimensions(map: PixelPushMapKey, progress: number) {
  if (map === 'moon_station') {
    return {
      halfWidth: 4_200 - progress * 2_150 / 1_000,
      halfHeight: 2_700 - progress * 1_150 / 1_000,
      radius: 760,
    }
  }
  return {
    halfWidth: 4_250 - progress * 1_050 / 1_000,
    halfHeight: 2_450 - progress * 1_150 / 1_000,
    radius: 420,
  }
}

function arenaPath(
  context: CanvasRenderingContext2D,
  map: PixelPushMapKey,
  progress: number,
) {
  if (map !== 'cross_bridge') {
    const dimensions = arenaDimensions(map, progress)
    roundedRectPath(
      context,
      5_000 - dimensions.halfWidth,
      3_500 - dimensions.halfHeight,
      dimensions.halfWidth * 2,
      dimensions.halfHeight * 2,
      dimensions.radius,
    )
    return
  }

  const centreX = 5_000
  const centreY = 3_500
  const centreHalfWidth = 1_900
  const centreHalfHeight = 1_450
  const armHalfThickness = 720
  const armX = 2_250 * (1_000 - progress) / 1_000
  const armY = 1_100 * (1_000 - progress) / 1_000
  const points: Array<[number, number]> = [
    [-armHalfThickness, -centreHalfHeight - armY],
    [armHalfThickness, -centreHalfHeight - armY],
    [armHalfThickness, -centreHalfHeight],
    [centreHalfWidth, -centreHalfHeight],
    [centreHalfWidth, -armHalfThickness],
    [centreHalfWidth + armX, -armHalfThickness],
    [centreHalfWidth + armX, armHalfThickness],
    [centreHalfWidth, armHalfThickness],
    [centreHalfWidth, centreHalfHeight],
    [armHalfThickness, centreHalfHeight],
    [armHalfThickness, centreHalfHeight + armY],
    [-armHalfThickness, centreHalfHeight + armY],
    [-armHalfThickness, centreHalfHeight],
    [-centreHalfWidth, centreHalfHeight],
    [-centreHalfWidth, armHalfThickness],
    [-centreHalfWidth - armX, armHalfThickness],
    [-centreHalfWidth - armX, -armHalfThickness],
    [-centreHalfWidth, -armHalfThickness],
    [-centreHalfWidth, -centreHalfHeight],
    [-armHalfThickness, -centreHalfHeight],
  ]
  context.beginPath()
  context.moveTo(centreX + points[0]![0], centreY + points[0]![1])
  for (const [x, y] of points.slice(1)) context.lineTo(centreX + x, centreY + y)
  context.closePath()
}

function drawVoid(context: CanvasRenderingContext2D, width: number, height: number) {
  context.fillStyle = '#030911'
  context.fillRect(0, 0, width, height)
  const gradient = context.createRadialGradient(
    width * .5,
    height * .46,
    0,
    width * .5,
    height * .46,
    Math.max(width, height) * .68,
  )
  gradient.addColorStop(0, '#113342')
  gradient.addColorStop(.55, '#081b29')
  gradient.addColorStop(1, '#02070d')
  context.fillStyle = gradient
  context.fillRect(0, 0, width, height)
  context.fillStyle = '#8be9ec55'
  for (let index = 0; index < 72; index += 1) {
    const x = (index * 2_137 % 9_973) / 9_973 * width
    const y = (index * 3_791 % 9_941) / 9_941 * height
    const size = index % 9 === 0 ? 3 : 1
    context.fillRect(Math.round(x), Math.round(y), size, size)
  }
}

function drawArena(
  context: CanvasRenderingContext2D,
  map: PixelPushMapKey,
  progress: number,
  tick: number,
) {
  context.save()
  context.shadowColor = progress > 0 ? '#ff506caa' : '#47d9e466'
  context.shadowBlur = progress > 0 ? 180 : 110
  context.fillStyle = '#163842'
  context.strokeStyle = progress > 0 ? '#ff6680' : '#67dfe1'
  context.lineWidth = 52
  arenaPath(context, map, progress)
  context.fill()
  context.shadowBlur = 0
  context.stroke()

  context.save()
  arenaPath(context, map, progress)
  context.clip()
  context.globalAlpha = .32
  context.strokeStyle = '#9ae4e4'
  context.lineWidth = 14
  const tile = 500
  for (let x = 750; x < 9_500; x += tile) {
    context.beginPath()
    context.moveTo(x, 650)
    context.lineTo(x, 6_350)
    context.stroke()
  }
  for (let y = 750; y < 6_500; y += tile) {
    context.beginPath()
    context.moveTo(650, y)
    context.lineTo(9_350, y)
    context.stroke()
  }
  context.globalAlpha = 1

  if (map === 'pulse_factory') {
    const cycleTicks = 8 * 30
    const cycleTick = tick % cycleTicks
    const start = 2 * 30
    const travel = 3 * 30
    if (cycleTick >= start && cycleTick < start + travel) {
      const pulseX = 1_050 + (cycleTick - start) / travel * 7_900
      const pulseGradient = context.createLinearGradient(pulseX - 280, 0, pulseX + 280, 0)
      pulseGradient.addColorStop(0, '#ffcf5800')
      pulseGradient.addColorStop(.5, '#ffdc75cc')
      pulseGradient.addColorStop(1, '#ffcf5800')
      context.fillStyle = pulseGradient
      context.fillRect(pulseX - 280, 950, 560, 5_100)
    }
  }
  context.restore()
  context.restore()
}

function interpolatedPlayers(timestamp: number): PixelPushPlayerState[] {
  if (!currentTargets.size) return roster.value
  const alpha = Math.min(1, Math.max(0, (timestamp - frameReceivedAt) / 70))
  return [...currentTargets.values()].map(target => {
    const previous = previousTargets.get(target.id) ?? target
    return {
      ...target,
      x: previous.x + (target.x - previous.x) * alpha,
      y: previous.y + (target.y - previous.y) * alpha,
      vx: previous.vx + (target.vx - previous.vx) * alpha,
      vy: previous.vy + (target.vy - previous.vy) * alpha,
    }
  })
}

function playerMetadata(playerId: string) {
  return roster.value.find(player => player.id === playerId)
}

function drawPlayer(
  context: CanvasRenderingContext2D,
  player: PixelPushPlayerState,
) {
  const metadata = playerMetadata(player.id) ?? player
  const color = metadata.color ?? '#5ce1e6'
  context.save()
  context.translate(player.x, player.y)
  context.globalAlpha = player.alive ? 1 : .22
  const angle = Math.atan2(player.facingY, player.facingX)

  context.fillStyle = '#02080ba0'
  context.beginPath()
  context.ellipse(40, 170, 330, 150, 0, 0, Math.PI * 2)
  context.fill()

  if (player.dashing) {
    context.save()
    context.rotate(angle)
    context.fillStyle = `${color}22`
    context.fillRect(-840, -210, 650, 420)
    context.fillStyle = `${color}55`
    context.fillRect(-620, -140, 420, 280)
    context.restore()
  }

  if (player.bracing) {
    context.save()
    context.rotate(angle)
    context.strokeStyle = '#b9ecff'
    context.lineWidth = 64
    context.beginPath()
    context.arc(0, 0, 430, -.88, .88)
    context.stroke()
    context.strokeStyle = '#ffffff55'
    context.lineWidth = 18
    context.beginPath()
    context.arc(0, 0, 475, -.72, .72)
    context.stroke()
    context.restore()
  }

  context.rotate(angle)
  context.fillStyle = '#051116'
  context.fillRect(-255, -255, 510, 510)
  context.fillStyle = color
  context.fillRect(-220, -220, 440, 440)
  context.fillStyle = '#ffffff24'
  context.fillRect(-180, -180, 360, 72)
  context.fillStyle = '#07131a'
  context.fillRect(50, -92, 108, 76)
  context.fillRect(50, 34, 108, 76)
  context.fillStyle = '#e9ffff'
  context.fillRect(76, -72, 54, 38)
  context.fillRect(76, 54, 54, 38)
  context.fillStyle = '#07131a'
  context.fillRect(-205, -24, 130, 48)
  context.fillStyle = color
  context.fillRect(-315, -160, 95, 120)
  context.fillRect(-315, 40, 95, 120)
  context.restore()

  context.save()
  context.translate(player.x, player.y - 470)
  context.textAlign = 'center'
  context.font = '800 180px ui-monospace, monospace'
  context.lineWidth = 38
  context.strokeStyle = '#02080ddd'
  context.strokeText(metadata.name ?? `P${(metadata.seat ?? 0) + 1}`, 0, 0)
  context.fillStyle = '#f4ffff'
  context.fillText(metadata.name ?? `P${(metadata.seat ?? 0) + 1}`, 0, 0)
  context.restore()
}

function drawEventEffects(
  context: CanvasRenderingContext2D,
  players: PixelPushPlayerState[],
  tick: number,
) {
  const playerById = new Map(players.map(player => [player.id, player]))
  for (const event of events.value) {
    const age = tick - event.tick
    if (age < 0 || age > 10 || !event.targetId) continue
    const target = playerById.get(event.targetId)
    if (!target) continue
    const progress = age / 10
    context.save()
    context.translate(target.x, target.y)
    context.globalAlpha = 1 - progress
    context.strokeStyle = event.kind === 'braced' ? '#b9ecff' : '#ffdd70'
    context.lineWidth = 38
    for (let index = 0; index < 8; index += 1) {
      const angle = index * Math.PI / 4 + event.id * .37
      const inner = 300 + progress * 180
      const outer = 480 + progress * 360
      context.beginPath()
      context.moveTo(Math.cos(angle) * inner, Math.sin(angle) * inner)
      context.lineTo(Math.cos(angle) * outer, Math.sin(angle) * outer)
      context.stroke()
    }
    context.restore()
  }
}

function draw(timestamp: number) {
  const element = canvas.value
  const context = element?.getContext('2d')
  if (!element || !context) return
  const width = element.width
  const height = element.height
  drawVoid(context, width, height)
  const worldWidth = game.value.world?.width ?? 10_000
  const worldHeight = game.value.world?.height ?? 7_000
  const scale = Math.min(width / worldWidth, height / worldHeight)
  const offsetX = (width - worldWidth * scale) / 2
  const offsetY = (height - worldHeight * scale) / 2
  const players = interpolatedPlayers(timestamp)
  const renderTick = realtimeFrame.value?.tick ?? game.value.tick
  const recentImpact = events.value.some(event => (
    ['hit', 'braced', 'ring_out'].includes(event.kind)
    && renderTick - event.tick >= 0
    && renderTick - event.tick <= 2
  ))
  const shake = recentImpact ? Math.sin(timestamp * .08) * 5 * (window.devicePixelRatio || 1) : 0

  context.save()
  context.translate(offsetX + shake, offsetY - shake * .45)
  context.scale(scale, scale)
  drawArena(context, currentMap.value, shrinkProgress.value, renderTick)
  for (const player of players.filter(item => item.alive)) drawPlayer(context, player)
  drawEventEffects(context, players, renderTick)
  context.restore()
}

function renderLoop(timestamp: number) {
  draw(timestamp)
  animationFrame = window.requestAnimationFrame(renderLoop)
}

onMounted(async () => {
  syncInputSequence()
  await nextTick()
  resizeCanvas()
  if (canvasShell.value) {
    resizeObserver = new ResizeObserver(resizeCanvas)
    resizeObserver.observe(canvasShell.value)
  }
  animationFrame = window.requestAnimationFrame(renderLoop)
})

onBeforeUnmount(() => {
  if (latestInputMask.value !== 0) sendInput(0)
  if (animationFrame !== null) window.cancelAnimationFrame(animationFrame)
  resizeObserver?.disconnect()
})
</script>

<template>
  <section class="pixel-push-game">
    <header class="pixel-push-match-header">
      <div>
        <span>{{ mapName }}</span>
        <strong>第 {{ roundNumber }} 回合</strong>
      </div>
      <div class="round-clock" :class="{ danger: suddenDeath }">
        <Gauge :size="18" />
        <strong>{{ roundSeconds }}</strong><small>秒</small>
      </div>
      <div class="match-format">
        <Trophy :size="17" />
        <span>先胜 2 回合</span>
      </div>
    </header>

    <div class="pixel-push-scoreboard">
      <article
        v-for="player in roster"
        :key="player.id"
        :class="{
          self: player.id === snapshot.self.id,
          eliminated: !player.alive,
          offline: (player.disconnectTicks ?? 0) > 0,
        }"
        :style="{ '--player-color': player.color }"
      >
        <div class="player-identity">
          <i /><span>{{ player.name }}</span>
          <small v-if="player.id === snapshot.self.id">{{ isSpectating ? '观看' : '你' }}</small>
        </div>
        <div class="round-pips" aria-label="回合胜利">
          <i :class="{ won: (player.roundWins ?? 0) >= 1 }" />
          <i :class="{ won: (player.roundWins ?? 0) >= 2 }" />
        </div>
        <div class="balance-meter">
          <span :style="{ width: `${player.balance}%` }" />
        </div>
        <small class="balance-copy">失衡 {{ player.balance }}%</small>
      </article>
    </div>

    <div ref="canvasShell" class="pixel-push-canvas-shell">
      <canvas ref="canvas" aria-label="像素推推王实时擂台" />
      <div v-if="overlayTitle" class="arena-overlay" :class="{ danger: suddenDeath }">
        <small v-if="stage === 'countdown'">准备</small>
        <strong>{{ overlayTitle }}</strong>
        <span v-if="frozen">战斗时钟已冻结</span>
        <span v-else-if="stage === 'round_result'">下一回合即将开始</span>
        <span v-else-if="suddenDeath">安全区域正在收缩</span>
      </div>
      <div v-if="isSpectating" class="spectator-badge">第一人称观战 · 固定观看 {{ snapshot.self.name }}</div>
    </div>

    <div v-if="!isSpectating" class="desktop-control-legend">
      <span><kbd>WASD</kbd><kbd>方向键</kbd>移动</span>
      <span><kbd>空格</kbd><kbd>J</kbd>冲刺</span>
      <span><kbd>Shift</kbd><kbd>K</kbd>稳住</span>
      <span><Shield :size="15" />迎着冲刺稳住，能让对手反弹</span>
      <span><Sparkles :size="15" />侧后方撞击会增加更多失衡</span>
    </div>

    <PixelPushControls
      v-if="!isSpectating"
      :disabled="controlsDisabled"
      :dash-ready="dashReady"
      @mask="sendInput"
    />
  </section>
</template>

<style scoped>
.pixel-push-game { --push-cyan: #5ce1e6; display: grid; gap: 12px; width: 100%; min-width: 0; }
.pixel-push-match-header { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 12px; border: 1px solid color-mix(in srgb, var(--push-cyan) 35%, var(--line)); border-radius: 16px; padding: 11px 14px; background: linear-gradient(135deg, #102a34f2, #071923f5); box-shadow: inset 0 1px #ffffff0a; }
.pixel-push-match-header > div:first-child { display: grid; gap: 2px; }
.pixel-push-match-header span, .pixel-push-match-header small { color: #a6c4ca; font-size: 11px; }
.pixel-push-match-header strong { color: #efffff; }
.round-clock { display: flex; align-items: baseline; justify-content: center; gap: 4px; min-width: 112px; border: 1px solid #5ce1e650; border-radius: 12px; padding: 7px 12px; color: #8df5f3; background: #5ce1e60c; }
.round-clock svg { align-self: center; }.round-clock strong { font: 900 25px/1 ui-monospace, monospace; }.round-clock.danger { border-color: #ff6981aa; color: #ff8095; animation: clock-pulse .8s ease-in-out infinite alternate; }
.match-format { display: flex; align-items: center; justify-content: flex-end; gap: 6px; color: #d9bd72; }
.pixel-push-scoreboard { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.pixel-push-scoreboard article { --player-color: #5ce1e6; position: relative; min-width: 0; border: 1px solid color-mix(in srgb, var(--player-color) 38%, #35515a); border-radius: 12px; padding: 9px 10px 8px; background: linear-gradient(145deg, color-mix(in srgb, var(--player-color) 8%, #10232c), #091821); transition: opacity .18s, filter .18s; }
.pixel-push-scoreboard article.self { box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--player-color) 65%, transparent), 0 0 22px color-mix(in srgb, var(--player-color) 14%, transparent); }
.pixel-push-scoreboard article.eliminated { opacity: .46; filter: grayscale(.55); }.pixel-push-scoreboard article.offline::after { content: '重连保护'; position: absolute; right: 8px; bottom: 6px; color: #ffbd78; font-size: 9px; }
.player-identity { display: flex; align-items: center; gap: 6px; min-width: 0; }.player-identity > i { width: 9px; height: 9px; flex: 0 0 auto; background: var(--player-color); box-shadow: 0 0 10px var(--player-color); }.player-identity span { overflow: hidden; color: #edfdfd; font-weight: 850; text-overflow: ellipsis; white-space: nowrap; }.player-identity small { margin-left: auto; color: var(--player-color); }
.round-pips { display: flex; gap: 4px; margin: 6px 0; }.round-pips i { width: 18px; height: 5px; border: 1px solid color-mix(in srgb, var(--player-color) 45%, #29434c); background: #020a0f; }.round-pips i.won { background: var(--player-color); box-shadow: 0 0 8px var(--player-color); }
.balance-meter { height: 5px; overflow: hidden; background: #02090e; }.balance-meter span { display: block; height: 100%; background: linear-gradient(90deg, #66ddb7 0 35%, #f0c661 62%, #ff637a 100%); transition: width .08s linear; }.balance-copy { display: block; margin-top: 4px; color: #92abb1; font-size: 9px; }
.pixel-push-canvas-shell { position: relative; width: 100%; min-height: 360px; overflow: hidden; border: 1px solid #5ce1e641; border-radius: 20px; background: #02080e; box-shadow: 0 24px 70px #0007, inset 0 0 0 5px #ffffff05; }
.pixel-push-canvas-shell canvas { display: block; width: 100%; aspect-ratio: 10 / 7; max-height: min(72dvh, 760px); min-height: 360px; image-rendering: pixelated; touch-action: none; }
.arena-overlay { position: absolute; inset: 0; display: grid; place-content: center; justify-items: center; pointer-events: none; text-align: center; text-shadow: 0 4px 20px #000; }.arena-overlay::before { content: ''; position: absolute; inset: 0; background: radial-gradient(circle, #03111700 10%, #02070fa8 100%); }.arena-overlay > * { z-index: 1; }.arena-overlay small { color: #8adbdc; font: 800 12px/1 ui-monospace, monospace; letter-spacing: .32em; text-transform: uppercase; }.arena-overlay strong { color: #f3ffff; font: 950 clamp(34px, 7vw, 78px)/1 ui-monospace, monospace; letter-spacing: -.04em; }.arena-overlay span { margin-top: 8px; color: #b6d2d5; font-size: 12px; }.arena-overlay.danger strong { color: #ff758c; animation: danger-glitch .5s steps(2) infinite alternate; }
.spectator-badge { position: absolute; top: 12px; left: 50%; transform: translateX(-50%); border: 1px solid #a78bfa88; border-radius: 999px; padding: 6px 11px; color: #e2d8ff; background: #1a1437dd; font-size: 10px; }
.desktop-control-legend { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 7px 15px; border: 1px solid #ffffff10; border-radius: 12px; padding: 8px 10px; color: #8faab0; background: #071820b5; font-size: 10px; }.desktop-control-legend span { display: inline-flex; align-items: center; gap: 5px; }.desktop-control-legend kbd { min-width: 27px; border: 1px solid #ffffff20; border-bottom-width: 2px; border-radius: 5px; padding: 2px 5px; color: #d7eeef; background: #132b34; font: 800 9px ui-monospace, monospace; text-align: center; }
@keyframes clock-pulse { to { box-shadow: 0 0 22px #ff506c35; } }
@keyframes danger-glitch { to { transform: translateX(3px); text-shadow: -5px 0 #5ce1e688, 5px 0 #ff4e6e88, 0 5px 20px #000; } }
@media (hover: none), (pointer: coarse), (max-width: 720px) { .desktop-control-legend { display: none; } }
@media (max-width: 720px) {
  .pixel-push-match-header { grid-template-columns: 1fr auto; }.match-format { display: none; }
  .pixel-push-scoreboard { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .pixel-push-canvas-shell, .pixel-push-canvas-shell canvas { min-height: 280px; }
  .pixel-push-canvas-shell canvas { max-height: 56dvh; }
}
@media (max-width: 420px) {
  .pixel-push-game { gap: 8px; }.pixel-push-match-header { padding: 8px 10px; }.round-clock { min-width: 92px; }.round-clock strong { font-size: 21px; }
  .pixel-push-scoreboard { gap: 5px; }.pixel-push-scoreboard article { padding: 7px; }.balance-copy { display: none; }
  .pixel-push-canvas-shell, .pixel-push-canvas-shell canvas { min-height: 250px; border-radius: 14px; }
}
</style>
