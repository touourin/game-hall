<script setup lang="ts">
import { CirclePause, CirclePlay, Trophy } from '@lucide/vue'
import type { PieceType } from './tetrisEngine'

interface DisplayCell {
  type: PieceType | null
  active: boolean
  ghost: boolean
}

defineProps<{
  cells: DisplayCell[]
  paused: boolean
  autoPaused: boolean
  runEnded: boolean
  submitting: boolean
  submissionError?: string | null
}>()

defineEmits<{ resume: []; retry: [] }>()
</script>

<template>
  <div class="tetris-board-wrap">
    <div class="tetris-board" role="grid" aria-label="10 列 20 行落块棋盘">
      <span
        v-for="(cell, index) in cells"
        :key="index"
        class="tetris-cell"
        :class="[
          cell.type ? `piece-${cell.type}` : '',
          { active: cell.active, ghost: cell.ghost },
        ]"
      ><i v-if="cell.type" /></span>
    </div>

    <div v-if="paused || runEnded" class="tetris-overlay" role="status" aria-live="polite">
      <Trophy v-if="runEnded" :size="38" />
      <CirclePause v-else :size="38" />
      <strong>{{ submitting ? '正在保存成绩' : runEnded ? '成绩尚未保存' : autoPaused ? '已自动暂停' : '游戏暂停' }}</strong>
      <small>{{ submissionError || (submitting ? '请稍候…' : runEnded ? '游戏已结束，可以重新提交本轮成绩' : '点击继续恢复挑战') }}</small>
      <button v-if="paused && !runEnded" type="button" @click="$emit('resume')">
        <CirclePlay :size="18" />继续游戏
      </button>
      <button v-else-if="runEnded && !submitting" type="button" @click="$emit('retry')">
        <Trophy :size="18" />重新保存成绩
      </button>
    </div>
  </div>
</template>

<style scoped>
.tetris-board-wrap { position: relative; min-width: 0; border: 1px solid color-mix(in srgb, #62d8f0 36%, var(--line)); border-radius: 10px; padding: 6px; background: #031012; box-shadow: inset 0 0 24px #0009, 0 14px 34px #0005; }
.tetris-board { display: grid; grid-template-columns: repeat(10, 1fr); aspect-ratio: 1 / 2; background: linear-gradient(#0b2528, #061719); }
.tetris-cell { position: relative; min-width: 0; border: 1px solid #bdeaf006; background: #ffffff02; }
.tetris-cell[class*="piece-"] { z-index: 1; border-color: color-mix(in srgb, var(--cell-color) 65%, #fff); border-radius: 2px; background: linear-gradient(145deg, color-mix(in srgb, var(--cell-color) 70%, #fff), var(--cell-color) 44%, color-mix(in srgb, var(--cell-color) 72%, #071416)); box-shadow: inset 1px 1px 0 #ffffff66, inset -2px -2px 0 #0003; }
.tetris-cell[class*="piece-"] i { position: absolute; inset: 16%; border: 1px solid #ffffff28; border-radius: 2px; }
.tetris-cell.ghost { z-index: 0; opacity: .24; background: transparent; box-shadow: inset 0 0 0 2px var(--cell-color); }
.tetris-cell.active { filter: brightness(1.12); }
.piece-I { --cell-color: var(--piece-I); }.piece-J { --cell-color: var(--piece-J); }.piece-L { --cell-color: var(--piece-L); }.piece-O { --cell-color: var(--piece-O); }.piece-S { --cell-color: var(--piece-S); }.piece-T { --cell-color: var(--piece-T); }.piece-Z { --cell-color: var(--piece-Z); }
.tetris-overlay { position: absolute; z-index: 5; inset: 6px; display: grid; place-items: center; align-content: center; gap: 8px; padding: 20px; color: #bdeef4; background: #031316e8; text-align: center; backdrop-filter: blur(5px); }
.tetris-overlay strong { font-size: 20px; }
.tetris-overlay small { max-width: 260px; color: var(--muted); line-height: 1.45; }
.tetris-overlay button { margin-top: 8px; display: inline-flex; align-items: center; gap: 7px; border: 1px solid #62d8f066; border-radius: 10px; padding: 10px 14px; color: #bdeef4; background: #62d8f015; font-weight: 850; cursor: pointer; }
</style>
