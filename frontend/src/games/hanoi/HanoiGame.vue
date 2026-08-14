<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Lightbulb, MousePointerClick, RotateCcw, Sparkles } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import SoloMetricGrid from '../shared/solo/SoloMetricGrid.vue'
import SoloResultCard from '../shared/solo/SoloResultCard.vue'

interface HanoiView {
  discCount: number
  towers: number[][]
  moves: number
  optimalMoves: number
  elapsedMs: number
  isOptimal: boolean
  lastMove: { fromTower: number; toTower: number; disc: number } | null
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const selectedTower = ref<number | null>(null)
const draggedTower = ref<number | null>(null)
const hint = ref('先选择一根柱子最上方的圆盘，再选择目标柱')
const now = ref(performance.now())
const clockBaseMs = ref(0)
const clockReceivedAt = ref(performance.now())
let clockTimer: ReturnType<typeof setInterval> | null = null

const game = computed(() => props.snapshot.game as unknown as HanoiView)
const towerNames = ['起始柱', '中转柱', '目标柱']
const discColors = [
  '#f2d58b',
  '#d9a86c',
  '#d77e64',
  '#9cc7a8',
  '#66a99b',
  '#7499b9',
  '#9a83ad',
  '#b76f83',
]
const elapsedMs = computed(() => {
  if (props.snapshot.phase !== 'playing') return game.value.elapsedMs
  return clockBaseMs.value + Math.max(0, now.value - clockReceivedAt.value)
})
const efficiency = computed(() => {
  if (game.value.moves === 0) return 100
  return Math.min(100, Math.round(game.value.optimalMoves / game.value.moves * 100))
})

function syncClock() {
  clockBaseMs.value = game.value.elapsedMs
  clockReceivedAt.value = performance.now()
  now.value = clockReceivedAt.value
}

function topDisc(towerIndex: number): number | null {
  const tower = game.value.towers[towerIndex]
  return tower?.length ? tower[tower.length - 1] : null
}

function canMove(source: number, target: number): boolean {
  if (source === target) return false
  const disc = topDisc(source)
  const targetDisc = topDisc(target)
  return disc !== null && (targetDisc === null || disc < targetDisc)
}

async function moveDisc(source: number, target: number) {
  if (arcade.busy || props.snapshot.phase !== 'playing') return
  if (!canMove(source, target)) {
    hint.value = source === target
      ? '请选择另一根柱子'
      : '大圆盘不能放在小圆盘上'
    return
  }
  const disc = topDisc(source)
  await arcade.action('move', { fromTower: source, toTower: target })
  if (!arcade.error) {
    selectedTower.value = null
    hint.value = props.snapshot.winner === 'completed'
      ? '所有圆盘已按顺序落在目标柱，挑战完成'
      : `已移动 ${disc} 号圆盘，继续完成整座塔`
  }
}

function selectTower(towerIndex: number) {
  if (arcade.busy || props.snapshot.phase !== 'playing') return
  if (selectedTower.value === null) {
    if (topDisc(towerIndex) === null) {
      hint.value = '这根柱子上还没有圆盘'
      return
    }
    selectedTower.value = towerIndex
    hint.value = `已选择 ${topDisc(towerIndex)} 号圆盘，请选择目标柱`
    return
  }
  if (selectedTower.value === towerIndex) {
    selectedTower.value = null
    hint.value = '已取消选择'
    return
  }
  if (canMove(selectedTower.value, towerIndex)) {
    void moveDisc(selectedTower.value, towerIndex)
    return
  }
  if (topDisc(towerIndex) !== null) {
    selectedTower.value = towerIndex
    hint.value = `不能这样放置，已改选 ${topDisc(towerIndex)} 号圆盘`
  } else {
    hint.value = '大圆盘不能放在小圆盘上'
  }
}

function startDrag(event: DragEvent, towerIndex: number) {
  if (props.snapshot.phase !== 'playing' || arcade.busy) {
    event.preventDefault()
    return
  }
  draggedTower.value = towerIndex
  selectedTower.value = towerIndex
  event.dataTransfer?.setData('text/plain', String(towerIndex))
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function dropDisc(event: DragEvent, target: number) {
  const encoded = event.dataTransfer?.getData('text/plain')
  const source = draggedTower.value ?? (encoded ? Number(encoded) : null)
  draggedTower.value = null
  if (source !== null && Number.isInteger(source)) void moveDisc(source, target)
}

function discStyle(disc: number) {
  return {
    width: `${34 + disc / game.value.discCount * 62}%`,
    '--disc-color': discColors[(disc - 1) % discColors.length],
  }
}

function formatTime(milliseconds: number): string {
  const totalTenths = Math.floor(milliseconds / 100)
  const minutes = Math.floor(totalTenths / 600)
  const seconds = Math.floor(totalTenths / 10) % 60
  const tenths = totalTenths % 10
  return minutes
    ? `${minutes}:${String(seconds).padStart(2, '0')}.${tenths}`
    : `${seconds}.${tenths} 秒`
}

async function resetChallenge() {
  if (arcade.busy) return
  await arcade.action('reset')
  if (!arcade.error) {
    selectedTower.value = null
    hint.value = '圆盘已经重新摆好，计时和步数已清零'
  }
}

async function restartChallenge() {
  if (await arcade.restartGame()) {
    selectedTower.value = null
    hint.value = '新一轮挑战开始'
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
})
</script>

<template>
  <section class="hanoi-game">
    <SoloMetricGrid
      class="hanoi-metrics"
      aria-label="汉诺塔挑战状态"
      :columns="4"
      :items="[
        { label: '挑战层数', value: game.discCount },
        { label: '当前 / 最少步数', value: `${game.moves} / ${game.optimalMoves}` },
        { label: '挑战用时', value: formatTime(elapsedMs) },
        { label: '步数效率', value: `${efficiency}%`, tone: efficiency === 100 ? 'success' : 'default' },
      ]"
    />

    <section class="surface hanoi-board" :class="{ finished: snapshot.phase === 'finished' }">
      <div class="hanoi-board-glow" />
      <div class="hanoi-towers">
        <button
          v-for="(tower, towerIndex) in game.towers"
          :key="towerIndex"
          type="button"
          class="hanoi-tower"
          :class="{
            selected: selectedTower === towerIndex,
            target: selectedTower !== null && canMove(selectedTower, towerIndex),
            complete: towerIndex === 2 && tower.length === game.discCount,
          }"
          :aria-label="`${towerNames[towerIndex]}，${tower.length} 个圆盘`"
          @click="selectTower(towerIndex)"
          @dragover.prevent
          @drop.prevent="dropDisc($event, towerIndex)"
        >
          <span class="tower-name">{{ towerNames[towerIndex] }}</span>
          <span class="tower-rod" />
          <span class="tower-base" />
          <span class="hanoi-discs">
            <span
              v-for="disc in tower"
              :key="disc"
              class="hanoi-disc"
              :class="{
                movable: disc === topDisc(towerIndex) && snapshot.phase === 'playing',
                'just-moved': game.lastMove?.disc === disc && game.lastMove?.toTower === towerIndex,
              }"
              :style="discStyle(disc)"
              :draggable="disc === topDisc(towerIndex) && snapshot.phase === 'playing'"
              @dragstart.stop="startDrag($event, towerIndex)"
              @dragend="draggedTower = null"
            >
              <i />
              <b>{{ disc }}</b>
            </span>
          </span>
        </button>
      </div>
    </section>

    <div class="surface hanoi-guide">
      <span><MousePointerClick :size="19" /></span>
      <p><strong>{{ hint }}</strong><small>电脑可拖动圆盘；手机点击起点和目标即可移动</small></p>
      <button
        v-if="snapshot.phase === 'playing'"
        type="button"
        :disabled="arcade.busy"
        @click="resetChallenge"
      >
        <RotateCcw :size="16" />重新摆盘
      </button>
    </div>

    <SoloResultCard
      v-if="snapshot.phase === 'finished'"
      class="hanoi-result"
      eyebrow="挑战完成"
      :title="game.isOptimal ? '完美解法' : `${game.discCount} 层通关`"
      :description="snapshot.winReason"
      :metrics="[
        { label: '实际步数', value: game.moves, tone: game.isOptimal ? 'success' : 'default' },
        { label: '理论最少', value: game.optimalMoves },
        { label: '完成时间', value: formatTime(game.elapsedMs) },
      ]"
      :can-restart="snapshot.actions.canRestart"
      :busy="arcade.busy"
      @restart="restartChallenge"
    >
      <template #icon><Sparkles :size="22" /></template>
      <template v-if="!game.isOptimal" #note>
        <p class="hanoi-result-tip"><Lightbulb :size="16" />还可以减少 {{ game.moves - game.optimalMoves }} 步</p>
      </template>
    </SoloResultCard>
  </section>
</template>

<style scoped>
.hanoi-game { width: min(100%, 920px); margin: 0 auto; display: grid; gap: 16px; }
.hanoi-metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 9px; }
.hanoi-metrics > div { min-width: 0; border: 1px solid var(--line); border-radius: 13px; padding: 12px 10px; background: var(--surface); text-align: center; }
.hanoi-metrics span, .hanoi-metrics small { display: block; }.hanoi-metrics span { color: var(--gold); font-size: clamp(16px, 3vw, 20px); font-weight: 900; }.hanoi-metrics small { margin-top: 3px; color: var(--muted); font-size: 10px; }
.hanoi-board { position: relative; min-height: clamp(330px, 52vw, 455px); padding: 24px clamp(8px, 2.5vw, 25px) 18px; overflow: hidden; }
.hanoi-board-glow { position: absolute; inset: 0; pointer-events: none; background: radial-gradient(circle at 50% 104%, color-mix(in srgb, var(--gold) 16%, transparent), transparent 48%), linear-gradient(180deg, transparent 55%, #020d0e66); }
.hanoi-board.finished { border-color: color-mix(in srgb, var(--gold) 58%, var(--line)); box-shadow: inset 0 0 50px color-mix(in srgb, var(--gold) 7%, transparent); }
.hanoi-board.finished .hanoi-board-glow { background: radial-gradient(circle at 82% 58%, color-mix(in srgb, var(--gold) 20%, transparent), transparent 26%), radial-gradient(circle at 50% 104%, color-mix(in srgb, var(--gold) 18%, transparent), transparent 48%), linear-gradient(180deg, transparent 55%, #020d0e66); animation: finish-glow 2.2s ease-in-out infinite alternate; }
.hanoi-towers { position: absolute; inset: 18px clamp(5px, 2vw, 20px); display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: clamp(4px, 1.4vw, 14px); }
.hanoi-tower { position: relative; min-width: 0; border: 1px solid transparent; border-radius: 18px; padding: 0; color: var(--text); background: transparent; transition: border-color .16s, background .16s, transform .16s; }
.hanoi-tower:hover { background: #ffffff04; }.hanoi-tower.selected { border-color: color-mix(in srgb, var(--gold) 64%, transparent); background: color-mix(in srgb, var(--gold) 7%, transparent); transform: translateY(-2px); }.hanoi-tower.target:not(.selected) { border-color: #75c8aa44; background: #62c69b09; }.hanoi-tower.complete { background: linear-gradient(180deg, transparent, color-mix(in srgb, var(--gold) 9%, transparent)); }
.hanoi-tower.selected .hanoi-disc.movable { filter: brightness(1.13); box-shadow: inset 0 2px 0 #ffffff70, inset 0 -4px 8px #0003, 0 0 0 3px color-mix(in srgb, var(--gold) 22%, transparent), 0 7px 18px #0008; transform: translateY(-4px); }
.hanoi-tower.complete .tower-name { color: var(--gold); }
.tower-name { position: absolute; z-index: 5; top: 8px; left: 50%; transform: translateX(-50%); color: var(--muted); font-size: 10px; font-weight: 850; letter-spacing: .09em; white-space: nowrap; }
.tower-rod { position: absolute; z-index: 1; left: 50%; top: 54px; bottom: 34px; width: clamp(7px, 1.1vw, 11px); transform: translateX(-50%); border: 1px solid #d9a86c55; border-radius: 999px 999px 3px 3px; background: linear-gradient(90deg, #75502f, #d8a66a 45%, #795332); box-shadow: 0 8px 20px #0008; }
.tower-base { position: absolute; z-index: 2; right: 2%; bottom: 23px; left: 2%; height: 16px; border: 1px solid #d9a86c55; border-radius: 999px; background: linear-gradient(180deg, #c58e52, #644326); box-shadow: 0 8px 18px #0008; }
.hanoi-discs { position: absolute; z-index: 3; right: 4%; bottom: 39px; left: 4%; display: flex; flex-direction: column-reverse; align-items: center; pointer-events: none; }
.hanoi-disc { position: relative; height: clamp(27px, 4.5vw, 42px); flex: 0 0 auto; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--disc-color) 74%, #fff); border-radius: 999px 999px 12px 12px; color: #102021; background: linear-gradient(180deg, color-mix(in srgb, var(--disc-color) 72%, #fff), var(--disc-color) 54%, color-mix(in srgb, var(--disc-color) 68%, #28170e)); box-shadow: inset 0 2px 0 #ffffff65, inset 0 -4px 8px #0003, 0 5px 9px #0006; pointer-events: auto; transition: filter .16s, transform .16s; }
.hanoi-disc::after { content: ''; position: absolute; inset: 4px 8%; border: 1px solid #ffffff35; border-radius: inherit; }
.hanoi-disc i { position: absolute; top: 4px; width: 8px; height: 8px; border-radius: 50%; background: #20312e88; box-shadow: inset 0 1px 2px #0008; }.hanoi-disc b { position: relative; z-index: 1; font-size: 10px; text-shadow: 0 1px #ffffff55; }
.hanoi-disc.movable { cursor: grab; }.hanoi-disc.movable:hover { filter: brightness(1.12); transform: translateY(-2px); }.hanoi-disc.movable:active { cursor: grabbing; }
.hanoi-disc.just-moved { animation: disc-arrive .38s cubic-bezier(.2, .9, .25, 1.15); }
.hanoi-guide { min-height: 66px; padding: 12px 14px; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 11px; align-items: center; }
.hanoi-guide > span { width: 40px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 12px; color: var(--gold); background: color-mix(in srgb, var(--gold) 11%, transparent); }.hanoi-guide p { min-width: 0; margin: 0; }.hanoi-guide strong, .hanoi-guide small { display: block; }.hanoi-guide strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.hanoi-guide small { margin-top: 3px; color: var(--muted); }.hanoi-guide button { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 10px; padding: 9px 11px; color: var(--muted); background: #0002; font-weight: 800; }
.hanoi-result { padding: 24px; display: grid; justify-items: center; gap: 8px; text-align: center; }.hanoi-result > span { display: flex; align-items: center; gap: 7px; color: #8fe0bd; font-weight: 850; }.hanoi-result h2 { margin: 3px 0 0; font-family: "Songti SC", "STSong", serif; font-size: clamp(32px, 7vw, 48px); }.hanoi-result > p { margin: 0; color: var(--muted); }.hanoi-result > div { width: min(100%, 520px); margin: 8px 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }.hanoi-result > div span { border: 1px solid var(--line); border-radius: 11px; padding: 11px 7px; color: var(--muted); font-size: 10px; }.hanoi-result > div b { display: block; margin-bottom: 3px; color: var(--gold); font-size: 16px; }.hanoi-result .hanoi-result-tip { display: flex; align-items: center; gap: 6px; color: var(--gold); }.hanoi-result .ui-button--primary { margin-top: 8px; }
@media (max-width: 620px) {
  .hanoi-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hanoi-board { min-height: 360px; padding-inline: 4px; }
  .hanoi-towers { inset-inline: 3px; gap: 2px; }
  .hanoi-tower { border-radius: 12px; }
  .tower-name { font-size: 9px; letter-spacing: 0; }
  .hanoi-guide { grid-template-columns: auto minmax(0, 1fr); }.hanoi-guide button { grid-column: 1 / -1; justify-content: center; }
}
@media (max-width: 390px) { .hanoi-board { min-height: 330px; }.hanoi-disc { height: 27px; }.hanoi-result { padding: 20px 12px; } }
@keyframes disc-arrive { from { opacity: .55; transform: translateY(-22px) scale(.96); } to { opacity: 1; transform: translateY(0) scale(1); } }
@keyframes finish-glow { to { opacity: .68; } }
@media (prefers-reduced-motion: reduce) { .hanoi-tower, .hanoi-disc { transition: none; }.hanoi-disc.just-moved, .hanoi-board.finished .hanoi-board-glow { animation: none; } }
</style>
