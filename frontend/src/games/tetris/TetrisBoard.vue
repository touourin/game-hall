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
  endReason: 'topped_out' | 'timeout'
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
      <strong>{{ submitting ? '正在保存成绩' : runEnded ? endReason === 'timeout' ? '时间到' : '成绩尚未保存' : autoPaused ? '已自动暂停' : '游戏暂停' }}</strong>
      <small>{{ submissionError || (submitting ? '请稍候…' : runEnded ? endReason === 'timeout' ? '限时挑战结束，正在结算本轮得分' : '游戏已结束，可以重新提交本轮成绩' : '点击继续恢复挑战') }}</small>
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
.tetris-board-wrap { position: relative; min-width: 0; border: 1px solid color-mix(in srgb, var(--accent) 36%, var(--line)); border-radius: 10px; padding: 6px; background: color-mix(in srgb, var(--surface-inset) 78%, var(--bg)); box-shadow: inset 0 0 24px color-mix(in srgb, var(--panel-shadow) 58%, transparent), var(--shadow-contact); }
.tetris-board { display: grid; grid-template-columns: repeat(10, 1fr); aspect-ratio: 1 / 2; background: linear-gradient(var(--surface-strong), color-mix(in srgb, var(--surface-inset) 84%, var(--bg))); }
.tetris-cell { position: relative; min-width: 0; border: 1px solid color-mix(in srgb, var(--line) 24%, transparent); background: color-mix(in srgb, var(--panel-highlight) 4%, transparent); }
.tetris-cell[class*="piece-"] { z-index: 1; border-color: color-mix(in srgb, var(--cell-color) 65%, var(--panel-highlight)); border-radius: 2px; background: linear-gradient(145deg, color-mix(in srgb, var(--cell-color) 70%, white), var(--cell-color) 44%, color-mix(in srgb, var(--cell-color) 72%, var(--bg))); box-shadow: inset 1px 1px 0 color-mix(in srgb, white 42%, transparent), inset -2px -2px 0 color-mix(in srgb, black 18%, transparent); }
.tetris-cell[class*="piece-"] i { position: absolute; inset: 16%; border: 1px solid color-mix(in srgb, white 16%, transparent); border-radius: 2px; }
.tetris-cell.ghost { z-index: 0; opacity: .24; background: transparent; box-shadow: inset 0 0 0 2px var(--cell-color); }
.tetris-cell.active { filter: brightness(1.12); }
.piece-I { --cell-color: var(--piece-I); }.piece-J { --cell-color: var(--piece-J); }.piece-L { --cell-color: var(--piece-L); }.piece-O { --cell-color: var(--piece-O); }.piece-S { --cell-color: var(--piece-S); }.piece-T { --cell-color: var(--piece-T); }.piece-Z { --cell-color: var(--piece-Z); }
.tetris-overlay { position: absolute; z-index: 5; inset: 6px; display: grid; place-items: center; align-content: center; gap: 8px; padding: 20px; color: var(--text); background: color-mix(in srgb, var(--surface-elevated) 94%, transparent); text-align: center; backdrop-filter: blur(5px); }
.tetris-overlay strong { font-size: 20px; }
.tetris-overlay small { max-width: 260px; color: var(--muted); line-height: 1.45; }
.tetris-overlay button { margin-top: 8px; display: inline-flex; align-items: center; gap: 7px; border: 1px solid color-mix(in srgb, var(--accent) 42%, var(--line)); border-radius: 10px; padding: 10px 14px; color: var(--text); background: color-mix(in srgb, var(--accent) 10%, var(--surface-elevated)); font-weight: 850; cursor: pointer; }
</style>
