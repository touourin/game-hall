<script setup lang="ts">
import { ArrowLeft, ArrowRight } from '@lucide/vue'

defineProps<{ disabled?: boolean }>()
const emit = defineEmits<{
  press: [direction: -1 | 1, event: PointerEvent]
  release: [event: PointerEvent]
}>()
</script>

<template>
  <section class="shaft-controls" aria-label="触屏左右控制">
    <button
      type="button"
      :disabled="disabled"
      aria-label="向左移动"
      @pointerdown="emit('press', -1, $event)"
      @pointerup="emit('release', $event)"
      @pointercancel="emit('release', $event)"
      @lostpointercapture="emit('release', $event)"
    ><ArrowLeft :size="34" /><strong>向左</strong><small>按住移动</small></button>
    <button
      type="button"
      :disabled="disabled"
      aria-label="向右移动"
      @pointerdown="emit('press', 1, $event)"
      @pointerup="emit('release', $event)"
      @pointercancel="emit('release', $event)"
      @lostpointercapture="emit('release', $event)"
    ><ArrowRight :size="34" /><strong>向右</strong><small>按住移动</small></button>
  </section>
</template>

<style scoped>
.shaft-controls { width: min(100%, 520px); margin: 0 auto; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; user-select: none; touch-action: none; }
.shaft-controls button { min-height: 82px; display: grid; grid-template-columns: auto auto; place-content: center; align-items: center; gap: 1px 9px; border: 1px solid color-mix(in srgb, #368f89 38%, var(--line)); border-radius: 16px; color: color-mix(in srgb, #15766f 74%, var(--text)); background: linear-gradient(145deg, #65d8d012, transparent), var(--surface-inset); box-shadow: inset 0 1px 0 #ffffff12; touch-action: none; }
.shaft-controls button svg { grid-row: 1 / 3; }.shaft-controls strong,.shaft-controls small { text-align: left; }.shaft-controls strong { font-size: 14px; }.shaft-controls small { color: var(--muted); font-size: 8px; }
.shaft-controls button:active { border-color: #3ca69e; color: color-mix(in srgb, #0d625c 82%, var(--text)); background: #65d8d02b; transform: scale(.97); }.shaft-controls button:disabled { opacity: .58; transform: none; }
@media (min-width: 760px) and (hover: hover) and (pointer: fine) { .shaft-controls { display: none; } }
@media (max-height: 700px) { .shaft-controls button { min-height: 66px; } }
</style>
