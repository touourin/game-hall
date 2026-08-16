<script setup lang="ts">
import { watch } from 'vue'
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ChevronsDown,
  RefreshCw,
  RotateCcw,
  Save,
} from '@lucide/vue'
import { usePointerRepeat } from '../../composables/usePointerRepeat'

const props = defineProps<{ disabled?: boolean; holdDisabled?: boolean }>()
const emit = defineEmits<{
  move: [direction: -1 | 1]
  rotate: [direction: -1 | 1]
  softDrop: []
  hardDrop: []
  hold: []
}>()
const { beginRepeat, runOnce, stopAllRepeats } = usePointerRepeat()

watch(() => props.disabled, (disabled) => {
  if (disabled) stopAllRepeats()
})
</script>

<template>
  <section class="mobile-tetris-controls surface" aria-label="手机游戏控制器">
    <header>
      <span><strong>拇指控制器</strong><small>长按方向键可连续移动</small></span>
      <button type="button" :disabled="disabled || holdDisabled" @pointerdown="runOnce($event, () => emit('hold'))"><Save :size="17" />暂存</button>
    </header>
    <div class="mobile-control-layout">
      <div class="move-controls">
        <button type="button" :disabled="disabled" aria-label="向左移动" @pointerdown="beginRepeat($event, () => emit('move', -1))"><ArrowLeft :size="30" /></button>
        <button type="button" :disabled="disabled" aria-label="向右移动" @pointerdown="beginRepeat($event, () => emit('move', 1))"><ArrowRight :size="30" /></button>
      </div>
      <div class="action-controls">
        <button class="rotate-left" type="button" :disabled="disabled" aria-label="逆时针旋转" @pointerdown="runOnce($event, () => emit('rotate', -1))"><RotateCcw :size="23" /><small>反转</small></button>
        <button class="rotate-main" type="button" :disabled="disabled" aria-label="顺时针旋转" @pointerdown="runOnce($event, () => emit('rotate', 1))"><RefreshCw :size="29" /><strong>旋转</strong></button>
        <button class="soft-drop" type="button" :disabled="disabled" aria-label="向下软降" @pointerdown="beginRepeat($event, () => emit('softDrop'))"><ArrowDown :size="25" /><small>软降</small></button>
      </div>
      <button class="hard-drop" type="button" :disabled="disabled" aria-label="直接落到底部" @pointerdown="runOnce($event, () => emit('hardDrop'))"><ChevronsDown :size="32" /><strong>落底</strong><small>立即锁定</small></button>
    </div>
  </section>
</template>

<style scoped>
.mobile-tetris-controls { display: none; padding: 12px; touch-action: none; user-select: none; -webkit-user-select: none; }
.mobile-tetris-controls header { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.mobile-tetris-controls header strong,.mobile-tetris-controls header small { display: block; }
.mobile-tetris-controls header small { margin-top: 2px; color: var(--muted); font-size: 9px; }
.mobile-tetris-controls header button { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 9px; padding: 9px 11px; color: var(--text); background: var(--surface-inset); font-weight: 800; }
.mobile-control-layout { display: grid; grid-template-columns: 1fr 1.18fr .72fr; gap: 10px; align-items: stretch; }
.move-controls { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.move-controls button { min-height: 72px; }
.action-controls { display: grid; grid-template-columns: .8fr 1.2fr; grid-template-rows: 1fr 1fr; gap: 7px; }
.action-controls .rotate-main { grid-row: 1 / 3; grid-column: 2; }
.action-controls button,.move-controls button,.hard-drop { display: grid; place-items: center; align-content: center; gap: 3px; border: 1px solid color-mix(in srgb, var(--accent) 25%, var(--line)); border-radius: 14px; color: var(--text); background: linear-gradient(145deg, color-mix(in srgb, var(--accent) 5%, transparent), transparent), var(--surface-inset); box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 32%, transparent); touch-action: none; }
.action-controls button:active,.move-controls button:active,.hard-drop:active { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, var(--surface-inset)); transform: scale(.96); }
.action-controls button:disabled,.move-controls button:disabled,.hard-drop:disabled,.mobile-tetris-controls header button:disabled { opacity: .48; cursor: not-allowed; transform: none; }
.action-controls small,.hard-drop small { color: var(--muted); font-size: 8px; }
.hard-drop { min-height: 100%; border-color: color-mix(in srgb, var(--accent) 46%, var(--line)); color: var(--accent); background: linear-gradient(145deg, color-mix(in srgb, var(--accent) 13%, transparent), color-mix(in srgb, var(--accent-deep) 8%, transparent)), var(--surface-inset); }
.hard-drop strong { font-size: 14px; }
@media (max-width: 700px), (hover: none) and (pointer: coarse) { .mobile-tetris-controls { display: block; } }
@media (max-width: 430px) {
  .mobile-control-layout { grid-template-columns: 1fr 1.15fr .72fr; gap: 6px; }
  .move-controls,.action-controls { gap: 5px; }
  .move-controls button { min-height: 64px; }
  .action-controls button,.move-controls button,.hard-drop { border-radius: 12px; }
  .hard-drop strong { font-size: 12px; }
}
@media (max-width: 350px) {
  .mobile-control-layout { grid-template-columns: .95fr 1.15fr; grid-template-rows: minmax(72px, auto) 52px; }
  .move-controls { grid-column: 1; grid-row: 1; }
  .action-controls { grid-column: 2; grid-row: 1; }
  .hard-drop { grid-column: 1 / -1; grid-row: 2; min-height: 52px; display: flex; flex-direction: row; gap: 7px; }
  .hard-drop small { display: inline; }
}
@media (max-width: 700px) and (max-height: 760px) {
  .mobile-tetris-controls { padding: 9px; }
  .mobile-tetris-controls header { margin-bottom: 7px; }
  .move-controls button { min-height: 58px; }
}
@media (max-width: 350px) and (max-height: 760px) {
  .mobile-tetris-controls { padding: 7px; }
  .mobile-tetris-controls header { margin-bottom: 5px; }
  .mobile-tetris-controls header small { display: none; }
  .mobile-tetris-controls header button { padding: 7px 9px; }
  .mobile-control-layout { grid-template-rows: 68px 44px; }
  .move-controls button { min-height: 68px; }
  .hard-drop { min-height: 44px; }
}
@media (orientation: landscape) and (max-height: 560px) and (max-width: 980px) {
  .mobile-tetris-controls { display: block; align-self: center; }
  .mobile-control-layout { min-height: 170px; }
}
@media (prefers-reduced-motion: reduce) { .action-controls button,.move-controls button,.hard-drop { transition: none; } }
</style>
