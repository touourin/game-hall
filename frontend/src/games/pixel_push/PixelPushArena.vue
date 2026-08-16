<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Gauge, Shield, Sparkles, Trophy } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import { currentTheme } from '../../theme'
import type { ArcadeSnapshot } from '../../types/arcade'
import PixelPushControls from './PixelPushControls.vue'
import { renderPixelPush } from './pixelPushRenderer'
import type {
  PixelPushFrame,
  PixelPushGameState,
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
const roundNumber = computed(() => (
  realtimeFrame.value?.roundNumber ?? game.value.roundNumber
))
const currentMap = computed(() => (
  realtimeFrame.value?.currentMap ?? game.value.currentMap
))
const shrinkProgress = computed(() => (
  realtimeFrame.value?.shrinkProgress ?? game.value.shrinkProgress
))
const roundWinnerId = computed(() => (
  realtimeFrame.value?.roundWinnerId ?? game.value.roundWinnerId
))
const roundWins = computed(() => (
  realtimeFrame.value?.roundWins ?? game.value.roundWins
))
const frozen = computed(() => realtimeFrame.value?.frozen ?? game.value.frozen)
const events = computed(() => realtimeFrame.value?.events ?? game.value.events)
const roster = computed(() => {
  const dynamic = new Map(
    (realtimeFrame.value?.players ?? game.value.players).map(
      player => [player.id, player],
    ),
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
    return String(Math.max(1, Math.ceil(
      stageTicksRemaining.value / tickRate.value,
    )))
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
    ? new Map([...currentTargets].map(
      ([id, player]) => [id, copyPlayer(player)],
    ))
    : new Map([...next].map(([id, player]) => [id, copyPlayer(player)]))
  currentTargets = next
  frameReceivedAt = performance.now()
}

function interpolatedPlayers(timestamp: number): PixelPushPlayerState[] {
  if (!currentTargets.size) return roster.value
  const alpha = Math.min(1, Math.max(0, (timestamp - frameReceivedAt) / 70))
  return [...currentTargets.values()].map(target => {
    const previous = previousTargets.get(target.id) ?? target
    const metadata = roster.value.find(player => player.id === target.id)
    return {
      ...target,
      name: metadata?.name,
      seat: metadata?.seat,
      color: metadata?.color,
      x: previous.x + (target.x - previous.x) * alpha,
      y: previous.y + (target.y - previous.y) * alpha,
      vx: previous.vx + (target.vx - previous.vx) * alpha,
      vy: previous.vy + (target.vy - previous.vy) * alpha,
    }
  })
}

function draw(timestamp: number) {
  const element = canvas.value
  if (!element) return
  renderPixelPush(element, {
    worldWidth: game.value.world?.width ?? 10_000,
    worldHeight: game.value.world?.height ?? 7_000,
    map: currentMap.value,
    shrinkProgress: shrinkProgress.value,
    tick: realtimeFrame.value?.tick ?? game.value.tick,
    timestamp,
    players: interpolatedPlayers(timestamp),
    events: events.value,
    theme: currentTheme.value,
    dpr: Math.min(window.devicePixelRatio || 1, 2),
    reducedMotion: window.matchMedia?.(
      '(prefers-reduced-motion: reduce)',
    ).matches,
  })
}

function resizeCanvas() {
  const element = canvas.value
  if (!element) return
  const rect = element.getBoundingClientRect()
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  element.width = Math.max(1, Math.round(rect.width * dpr))
  element.height = Math.max(1, Math.round(rect.height * dpr))
  draw(performance.now())
}

function renderLoop(timestamp: number) {
  draw(timestamp)
  animationFrame = window.requestAnimationFrame(renderLoop)
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

watch(currentTheme, () => draw(performance.now()))

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
          <small v-if="player.id === snapshot.self.id">
            {{ isSpectating ? '观看' : '你' }}
          </small>
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
      <div
        v-if="overlayTitle"
        class="arena-overlay"
        :class="{ danger: suddenDeath }"
      >
        <small v-if="stage === 'countdown'">准备</small>
        <strong>{{ overlayTitle }}</strong>
        <span v-if="frozen">战斗时钟已冻结</span>
        <span v-else-if="stage === 'round_result'">下一回合即将开始</span>
        <span v-else-if="suddenDeath">安全区域正在收缩</span>
      </div>
      <div v-if="isSpectating" class="spectator-badge">
        第一人称观战 · 固定观看 {{ snapshot.self.name }}
      </div>
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
.pixel-push-game {
  --push-accent: var(--accent);
  --push-danger: var(--red);
  --push-warning: color-mix(in srgb, var(--accent) 74%, var(--text));
  width: 100%;
  min-width: 0;
  display: grid;
  gap: 12px;
}

.pixel-push-match-header {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 12px;
  border: 1px solid color-mix(in srgb, var(--push-accent) 34%, var(--line));
  border-radius: 16px;
  padding: 11px 14px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--push-accent) 7%, transparent), transparent),
    var(--material-pattern),
    var(--surface-primary);
  box-shadow: var(--shadow-contact), inset 0 1px 0 var(--metal-edge);
}
.pixel-push-match-header > div:first-child { display: grid; gap: 2px; }
.pixel-push-match-header span,
.pixel-push-match-header small { color: var(--muted); font-size: 11px; }
.pixel-push-match-header strong { color: var(--text); }

.round-clock {
  min-width: 112px;
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
  border: 1px solid color-mix(in srgb, var(--push-accent) 48%, var(--line));
  border-radius: 12px;
  padding: 7px 12px;
  color: color-mix(in srgb, var(--push-accent) 72%, var(--text));
  background: color-mix(in srgb, var(--push-accent) 8%, var(--surface-inset));
}
.round-clock svg { align-self: center; }
.round-clock strong { font: 900 25px/1 ui-monospace, monospace; }
.round-clock.danger {
  border-color: color-mix(in srgb, var(--push-danger) 70%, var(--line));
  color: color-mix(in srgb, var(--push-danger) 78%, var(--text));
  animation: clock-pulse .8s ease-in-out infinite alternate;
}
.match-format {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  color: color-mix(in srgb, var(--push-warning) 76%, var(--text));
}

.pixel-push-scoreboard {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.pixel-push-scoreboard article {
  --player-color: #5ce1e6;
  position: relative;
  min-width: 0;
  border: 1px solid color-mix(in srgb, var(--player-color) 38%, var(--line));
  border-radius: 12px;
  padding: 9px 10px 8px;
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--player-color) 8%, transparent), transparent),
    var(--surface-inset);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--metal-edge) 65%, transparent);
  transition: opacity .18s, filter .18s;
}
.pixel-push-scoreboard article.self {
  box-shadow:
    inset 0 0 0 1px color-mix(in srgb, var(--player-color) 64%, transparent),
    0 0 22px color-mix(in srgb, var(--player-color) 13%, transparent);
}
.pixel-push-scoreboard article.eliminated { opacity: .46; filter: grayscale(.55); }
.pixel-push-scoreboard article.offline::after {
  position: absolute;
  right: 8px;
  bottom: 6px;
  color: color-mix(in srgb, var(--push-warning) 72%, var(--text));
  content: '重连保护';
  font-size: 9px;
}
.player-identity { min-width: 0; display: flex; align-items: center; gap: 6px; }
.player-identity > i {
  width: 9px;
  height: 9px;
  flex: 0 0 auto;
  background: var(--player-color);
  box-shadow: 0 0 10px var(--player-color);
}
.player-identity span {
  overflow: hidden;
  color: var(--text);
  font-weight: 850;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.player-identity small { margin-left: auto; color: var(--player-color); }
.round-pips { display: flex; gap: 4px; margin: 6px 0; }
.round-pips i {
  width: 18px;
  height: 5px;
  border: 1px solid color-mix(in srgb, var(--player-color) 45%, var(--line));
  background: var(--surface-inset);
}
.round-pips i.won { background: var(--player-color); box-shadow: 0 0 8px var(--player-color); }
.balance-meter { height: 5px; overflow: hidden; background: var(--surface-inset); }
.balance-meter span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #54a982 0 35%, #bf8d35 62%, #c95f68 100%);
  transition: width .08s linear;
}
.balance-copy { display: block; margin-top: 4px; color: var(--muted); font-size: 9px; }

.pixel-push-canvas-shell {
  position: relative;
  width: 100%;
  min-height: 360px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--push-accent) 36%, var(--line));
  border-radius: 20px;
  background: var(--surface-inset);
  box-shadow: var(--shadow-raised), inset 0 0 0 5px color-mix(in srgb, var(--metal-edge) 18%, transparent);
}
.pixel-push-canvas-shell canvas {
  width: 100%;
  min-height: 360px;
  max-height: min(72dvh, 760px);
  display: block;
  aspect-ratio: 10 / 7;
  image-rendering: pixelated;
  touch-action: none;
}
.arena-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  justify-items: center;
  color: var(--text);
  pointer-events: none;
  text-align: center;
  text-shadow: 0 3px 16px color-mix(in srgb, var(--bg) 72%, transparent);
}
.arena-overlay::before {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle, transparent 10%, color-mix(in srgb, var(--bg) 46%, transparent) 100%);
  content: '';
}
.arena-overlay > * { z-index: 1; }
.arena-overlay small {
  color: color-mix(in srgb, var(--push-accent) 74%, var(--text));
  font: 800 12px/1 ui-monospace, monospace;
  letter-spacing: .32em;
  text-transform: uppercase;
}
.arena-overlay strong {
  color: var(--text);
  font: 950 clamp(34px, 7vw, 78px)/1 ui-monospace, monospace;
  letter-spacing: -.04em;
}
.arena-overlay span { margin-top: 8px; color: var(--text-soft); font-size: 12px; }
.arena-overlay.danger strong {
  color: color-mix(in srgb, var(--push-danger) 82%, var(--text));
  animation: danger-glitch .5s steps(2) infinite alternate;
}
.spectator-badge {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  border: 1px solid color-mix(in srgb, var(--accent-secondary) 58%, var(--line));
  border-radius: 999px;
  padding: 6px 11px;
  color: var(--text);
  background: color-mix(in srgb, var(--accent-secondary) 13%, var(--surface-primary));
  box-shadow: var(--shadow-contact);
  font-size: 10px;
}

.desktop-control-legend {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 7px 15px;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 8px 10px;
  color: var(--muted);
  background: var(--control-surface), var(--surface-inset);
  box-shadow: var(--shadow-contact);
  font-size: 10px;
}
.desktop-control-legend span { display: inline-flex; align-items: center; gap: 5px; }
.desktop-control-legend kbd {
  min-width: 27px;
  border: 1px solid var(--line);
  border-bottom-width: 2px;
  border-radius: 5px;
  padding: 2px 5px;
  color: var(--text);
  background: var(--surface-inset);
  font: 800 9px ui-monospace, monospace;
  text-align: center;
}

@keyframes clock-pulse {
  to { box-shadow: 0 0 22px color-mix(in srgb, var(--push-danger) 22%, transparent); }
}
@keyframes danger-glitch {
  to {
    transform: translateX(3px);
    text-shadow:
      -5px 0 color-mix(in srgb, var(--push-accent) 48%, transparent),
      5px 0 color-mix(in srgb, var(--push-danger) 54%, transparent),
      0 5px 20px color-mix(in srgb, var(--bg) 76%, transparent);
  }
}
@media (prefers-reduced-motion: reduce) {
  .round-clock.danger,
  .arena-overlay.danger strong { animation: none; }
}
@media (hover: none), (pointer: coarse), (max-width: 720px) {
  .desktop-control-legend { display: none; }
}
@media (max-width: 720px) {
  .pixel-push-match-header { grid-template-columns: 1fr auto; }
  .match-format { display: none; }
  .pixel-push-scoreboard { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .pixel-push-canvas-shell,
  .pixel-push-canvas-shell canvas { min-height: 280px; }
  .pixel-push-canvas-shell canvas { max-height: 56dvh; }
}
@media (max-width: 420px) {
  .pixel-push-game { gap: 8px; }
  .pixel-push-match-header { padding: 8px 10px; }
  .round-clock { min-width: 92px; }
  .round-clock strong { font-size: 21px; }
  .pixel-push-scoreboard { gap: 5px; }
  .pixel-push-scoreboard article { padding: 7px; }
  .balance-copy { display: none; }
  .pixel-push-canvas-shell,
  .pixel-push-canvas-shell canvas { min-height: 250px; border-radius: 14px; }
}
@media (max-height: 520px) and (orientation: landscape) {
  .pixel-push-canvas-shell,
  .pixel-push-canvas-shell canvas { min-height: 230px; }
  .pixel-push-canvas-shell canvas { max-height: 54dvh; }
}
</style>
