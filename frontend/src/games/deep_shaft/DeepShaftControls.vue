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
.shaft-controls {
  position: absolute;
  z-index: 4;
  right: 16px;
  bottom: 15px;
  left: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: clamp(54px, 22vw, 118px);
  user-select: none;
  touch-action: none;
  pointer-events: none;
}
.shaft-controls button {
  min-width: 0;
  min-height: 62px;
  display: grid;
  grid-template-columns: auto minmax(0, auto);
  place-content: center;
  align-items: center;
  gap: 1px 8px;
  border: 1px solid color-mix(in srgb, var(--shaft-accent) 46%, var(--line));
  border-radius: 19px;
  padding: 8px 12px;
  color: color-mix(in srgb, var(--shaft-accent) 76%, var(--text));
  background:
    linear-gradient(145deg, color-mix(in srgb, white 12%, transparent), transparent 38%),
    color-mix(in srgb, var(--surface-primary) 78%, transparent);
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, white 18%, transparent),
    0 9px 24px color-mix(in srgb, var(--bg) 38%, transparent);
  backdrop-filter: blur(13px) saturate(1.08);
  touch-action: none;
  pointer-events: auto;
}
.shaft-controls button svg { grid-row: 1 / 3; }
.shaft-controls strong,
.shaft-controls small { overflow: hidden; text-align: left; text-overflow: ellipsis; white-space: nowrap; }
.shaft-controls strong { color: var(--text); font-size: 11px; }
.shaft-controls small { color: var(--muted); font-size: 6px; }
.shaft-controls button:active {
  border-color: var(--shaft-accent);
  color: var(--accent-contrast);
  background: var(--shaft-accent);
  transform: translateY(1px) scale(.96);
}
.shaft-controls button:active strong,
.shaft-controls button:active small { color: var(--accent-contrast); }
.shaft-controls button:disabled { opacity: .46; transform: none; }
@media (min-width: 760px) and (hover: hover) and (pointer: fine) { .shaft-controls { display: none; } }
@media (max-width: 380px) {
  .shaft-controls { right: 12px; bottom: 11px; left: 12px; gap: 46px; }
  .shaft-controls button { min-height: 56px; padding: 7px 9px; }
  .shaft-controls button svg { width: 27px; }
}
@media (max-height: 700px) { .shaft-controls button { min-height: 54px; } }
</style>
