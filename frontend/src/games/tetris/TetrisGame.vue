<script setup lang="ts">
import { onMounted, ref, toRef } from 'vue'
import {
  CirclePause,
  CirclePlay,
  RefreshCw,
  Save,
  Trophy,
} from '@lucide/vue'
import type { ArcadeSnapshot } from '../../types/arcade'
import SoloMetricGrid from '../shared/solo/SoloMetricGrid.vue'
import SoloResultCard from '../shared/solo/SoloResultCard.vue'
import TetrisBoard from './TetrisBoard.vue'
import TetrisPiecePreview from './TetrisPiecePreview.vue'
import TetrisThumbControls from './TetrisThumbControls.vue'
import { useTetrisGame } from './useTetrisGame'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const gameRoot = ref<HTMLElement | null>(null)
const {
  arcade,
  autoPaused,
  canControl,
  displayCells,
  endReason,
  formattedTime,
  hardDrop,
  held,
  holdPiece,
  holdUsed,
  isPlaying,
  isTimed,
  lastClear,
  level,
  lines,
  moveHorizontal,
  nextPieces,
  paused,
  restartChallenge,
  rotate,
  runEnded,
  score,
  serverGame,
  softDrop,
  submissionError,
  submitFinalScore,
  submitting,
  togglePause,
} = useTetrisGame(toRef(props, 'snapshot'))

onMounted(() => {
  if (
    typeof window.matchMedia === 'function'
    && window.matchMedia('(max-width: 700px), (hover: none) and (pointer: coarse), (orientation: landscape) and (max-height: 560px) and (max-width: 980px)').matches
  ) {
    window.requestAnimationFrame(() => gameRoot.value?.scrollIntoView({ block: 'start' }))
  }
})
</script>

<template>
  <section ref="gameRoot" class="tetris-game">
    <SoloMetricGrid
      aria-label="落块挑战状态"
      :columns="4"
      :items="[
        { label: '当前得分', value: score.toLocaleString(), tone: 'success' },
        { label: '消除行数', value: lines },
        { label: '当前等级', value: level },
        { label: isTimed ? '剩余时间' : '挑战用时', value: formattedTime, tone: isTimed ? 'warning' : 'default' },
      ]"
    />

    <section class="tetris-console surface">
      <aside class="tetris-side tetris-hold">
        <header><Save :size="15" /><span>暂存</span><kbd>C</kbd></header>
        <button type="button" :disabled="holdUsed || !canControl" aria-label="暂存当前方块" @click="holdPiece">
          <TetrisPiecePreview :piece="held" />
          <small>{{ holdUsed ? '下个方块后可用' : held ? '点击交换' : '暂未使用' }}</small>
        </button>
      </aside>

      <TetrisBoard
        :cells="displayCells"
        :paused="paused"
        :auto-paused="autoPaused"
        :run-ended="runEnded"
        :end-reason="endReason"
        :submitting="submitting"
        :submission-error="submissionError"
        @resume="togglePause"
        @retry="submitFinalScore"
      />

      <aside class="tetris-side tetris-next">
        <header><RefreshCw :size="15" /><span>接下来</span></header>
        <div v-for="(piece, previewIndex) in nextPieces" :key="`${piece}-${previewIndex}`" class="next-piece">
          <TetrisPiecePreview :piece="piece" />
        </div>
        <button class="pause-button" type="button" :disabled="!isPlaying" @click="togglePause">
          <CirclePlay v-if="paused" :size="16" /><CirclePause v-else :size="16" />{{ paused ? '继续' : '暂停' }}
        </button>
      </aside>
    </section>

    <TetrisThumbControls
      v-if="snapshot.phase === 'playing'"
      :disabled="!canControl"
      :hold-disabled="holdUsed || !canControl"
      @move="moveHorizontal"
      @rotate="rotate"
      @soft-drop="softDrop"
      @hard-drop="hardDrop"
      @hold="holdPiece"
    />

    <p class="desktop-control-hint">
      <span><kbd>←</kbd><kbd>→</kbd> 移动</span><span><kbd>↓</kbd> 软降</span><span><kbd>↑</kbd>/<kbd>X</kbd> 旋转</span><span><kbd>Z</kbd> 反转</span><span><kbd>SPACE</kbd> 落底</span><span><kbd>C</kbd> 暂存</span><span><kbd>P</kbd> 暂停</span>
    </p>

    <p v-if="lastClear" class="line-clear-toast" aria-live="polite">刚刚消除 {{ lastClear }} 行</p>

    <SoloResultCard
      v-if="snapshot.phase === 'finished'"
      eyebrow="本轮挑战结束"
      title="最终得分"
      :score="serverGame.score.toLocaleString()"
      score-unit="分"
      :description="snapshot.winReason"
      :metrics="[
        { label: '消除行数', value: serverGame.lines },
        { label: '到达等级', value: serverGame.level },
        { label: '使用方块', value: serverGame.pieces },
      ]"
      :can-restart="snapshot.actions.canRestart"
      :busy="arcade.busy"
      restart-label="再来一局"
      @restart="restartChallenge"
    >
      <template #icon><Trophy :size="22" /></template>
    </SoloResultCard>
  </section>
</template>

<style scoped>
.tetris-game { width: min(100%, 820px); margin: 0 auto; display: grid; gap: 14px; --piece-I: #55d8e8; --piece-J: #638df2; --piece-L: #eea752; --piece-O: #efd75d; --piece-S: #67d28d; --piece-T: #ad79e8; --piece-Z: #eb6d78; }
.tetris-console { display: grid; grid-template-columns: minmax(96px, 1fr) minmax(260px, 360px) minmax(96px, 1fr); gap: clamp(10px, 2vw, 20px); align-items: start; padding: clamp(12px, 2.5vw, 22px); overflow: hidden; background: radial-gradient(circle at 50% 14%, #48cbe610, transparent 34%), var(--material-pattern), var(--surface); }
.tetris-side { min-width: 0; display: grid; gap: 9px; }
.tetris-side header { min-height: 28px; display: flex; align-items: center; gap: 6px; color: #91ddea; font-size: 9px; font-weight: 900; letter-spacing: .08em; text-transform: uppercase; }
.tetris-side header kbd { margin-left: auto; border: 1px solid var(--line); border-radius: 5px; padding: 2px 5px; color: var(--muted); font: inherit; }
.tetris-hold > button,.next-piece { min-width: 0; border: 1px solid var(--line); border-radius: 10px; padding: 8px; color: var(--muted); background: var(--surface-inset); }
.tetris-hold > button { width: 100%; cursor: pointer; }.tetris-hold > button:disabled { opacity: .52; cursor: not-allowed; }
.tetris-hold small { display: block; margin-top: 4px; font-size: 8px; line-height: 1.35; }
.next-piece:not(:first-of-type) { opacity: .68; transform: scale(.92); }.pause-button { min-height: 38px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: 1px solid var(--line); border-radius: 9px; color: var(--text); background: var(--surface-inset); font-weight: 800; cursor: pointer; }
.desktop-control-hint { margin: 0; display: flex; flex-wrap: wrap; justify-content: center; gap: 7px 13px; color: var(--muted); font-size: 9px; }.desktop-control-hint span { display: inline-flex; align-items: center; gap: 3px; }.desktop-control-hint kbd { border: 1px solid var(--line); border-bottom-width: 2px; border-radius: 5px; padding: 2px 5px; color: var(--text); background: var(--surface-inset); font: inherit; font-weight: 850; }
.line-clear-toast { margin: -5px auto 0; border-radius: 999px; padding: 5px 10px; color: #8fe0bd; background: #62c69b12; font-size: 9px; font-weight: 850; }
@media (max-width: 700px), (hover: none) and (pointer: coarse) {
  .tetris-game { width: min(100%, 560px); }
  .tetris-console { grid-template-columns: minmax(0, 1fr) minmax(74px, 24%); gap: 9px; padding: 9px; }
  .tetris-board-wrap { grid-column: 1; grid-row: 1 / 3; }
  .tetris-side { grid-column: 2; }.tetris-hold { grid-row: 1; }.tetris-next { grid-row: 2; align-self: end; }
  .next-piece:nth-of-type(n+3) { display: none; }.tetris-game { --tetris-preview-size: 70px; }.tetris-side header { font-size: 8px; }.tetris-hold small { display: none; }
  .desktop-control-hint { display: none; }
}
@media (max-width: 700px) and (max-height: 760px) {
  .tetris-game { gap: 10px; }
  .tetris-console { grid-template-columns: minmax(0, 160px) 68px; justify-content: center; padding: 7px; }
  .tetris-board-wrap { padding: 4px; }
  .tetris-game { --tetris-preview-size: 62px; }
}
@media (max-width: 350px) and (max-height: 760px) {
  .tetris-console { grid-template-columns: minmax(0, 130px) 62px; }
  .tetris-next .next-piece:nth-of-type(n+2) { display: none; }
}
@media (orientation: landscape) and (max-height: 560px) and (max-width: 980px) {
  .tetris-game { width: min(100%, 900px); grid-template-columns: minmax(200px, 240px) minmax(320px, 1fr); gap: 8px 12px; align-items: start; }
  .tetris-game > :first-child { grid-column: 1 / -1; }
  .tetris-game :deep(.solo-metric-card) { gap: 2px; padding: 6px; }
  .tetris-console { grid-column: 1; grid-template-columns: minmax(0, 1fr) minmax(58px, 25%); gap: 6px; padding: 6px; }
  .tetris-board-wrap { grid-column: 1; grid-row: 1 / 3; padding: 4px; }
  .tetris-side { grid-column: 2; }
  .tetris-hold { grid-row: 1; }
  .tetris-next { grid-row: 2; align-self: end; }
  .tetris-hold small,.next-piece:nth-of-type(n+2) { display: none; }
  .tetris-game { --tetris-preview-size: 54px; }
  .mobile-tetris-controls { grid-column: 2; display: block; align-self: center; }
  .desktop-control-hint,.line-clear-toast { display: none; }
}
</style>
