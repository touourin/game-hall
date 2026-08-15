<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  INPUT_BRACE,
  INPUT_DASH,
  INPUT_DOWN,
  INPUT_LEFT,
  INPUT_RIGHT,
  INPUT_UP,
} from './types'

const props = defineProps<{
  disabled?: boolean
  dashReady?: boolean
}>()
const emit = defineEmits<{
  mask: [value: number]
}>()

const joystick = ref<HTMLElement | null>(null)
const stickX = ref(0)
const stickY = ref(0)
const keyboardMask = ref(0)
const directionMask = ref(0)
const actionMask = ref(0)
const actionPointers = new Map<number, number>()
let joystickPointer: number | null = null
let lastMask = -1

function combinedMask(): number {
  return props.disabled
    ? 0
    : keyboardMask.value | directionMask.value | actionMask.value
}

function publish() {
  const next = combinedMask()
  if (next === lastMask) return
  lastMask = next
  emit('mask', next)
}

function keyboardBit(code: string): number {
  if (code === 'ArrowUp' || code === 'KeyW') return INPUT_UP
  if (code === 'ArrowDown' || code === 'KeyS') return INPUT_DOWN
  if (code === 'ArrowLeft' || code === 'KeyA') return INPUT_LEFT
  if (code === 'ArrowRight' || code === 'KeyD') return INPUT_RIGHT
  if (code === 'Space' || code === 'KeyJ') return INPUT_DASH
  if (code === 'ShiftLeft' || code === 'ShiftRight' || code === 'KeyK') return INPUT_BRACE
  return 0
}

function isTypingTarget(target: EventTarget | null): boolean {
  return target instanceof Element && Boolean(
    target.closest('input, textarea, select, [contenteditable="true"]'),
  )
}

function onKeydown(event: KeyboardEvent) {
  const bit = keyboardBit(event.code)
  if (!bit || isTypingTarget(event.target)) return
  event.preventDefault()
  keyboardMask.value |= bit
  publish()
}

function onKeyup(event: KeyboardEvent) {
  const bit = keyboardBit(event.code)
  if (!bit || isTypingTarget(event.target)) return
  event.preventDefault()
  keyboardMask.value &= ~bit
  publish()
}

function updateJoystick(event: PointerEvent) {
  const element = joystick.value
  if (!element || event.pointerId !== joystickPointer) return
  const rect = element.getBoundingClientRect()
  const dx = event.clientX - (rect.left + rect.width / 2)
  const dy = event.clientY - (rect.top + rect.height / 2)
  const radius = Math.max(1, Math.min(rect.width, rect.height) * .34)
  const distance = Math.hypot(dx, dy)
  const scale = distance > radius ? radius / distance : 1
  const x = dx * scale
  const y = dy * scale
  stickX.value = x
  stickY.value = y
  const deadzone = radius * .24
  let next = 0
  if (x < -deadzone) next |= INPUT_LEFT
  if (x > deadzone) next |= INPUT_RIGHT
  if (y < -deadzone) next |= INPUT_UP
  if (y > deadzone) next |= INPUT_DOWN
  directionMask.value = next
  publish()
}

function onJoystickDown(event: PointerEvent) {
  if (props.disabled || joystickPointer !== null) return
  event.preventDefault()
  joystickPointer = event.pointerId
  ;(event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId)
  updateJoystick(event)
}

function onJoystickMove(event: PointerEvent) {
  if (event.pointerId !== joystickPointer) return
  event.preventDefault()
  updateJoystick(event)
}

function onJoystickUp(event: PointerEvent) {
  if (event.pointerId !== joystickPointer) return
  joystickPointer = null
  stickX.value = 0
  stickY.value = 0
  directionMask.value = 0
  publish()
}

function onActionDown(bit: number, event: PointerEvent) {
  if (props.disabled) return
  event.preventDefault()
  actionPointers.set(event.pointerId, bit)
  ;(event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId)
  actionMask.value |= bit
  publish()
}

function onActionUp(event: PointerEvent) {
  const bit = actionPointers.get(event.pointerId)
  if (bit === undefined) return
  actionPointers.delete(event.pointerId)
  actionMask.value = [...actionPointers.values()].reduce(
    (mask, pointerBit) => mask | pointerBit,
    0,
  )
  publish()
}

function reset() {
  keyboardMask.value = 0
  directionMask.value = 0
  actionMask.value = 0
  actionPointers.clear()
  joystickPointer = null
  stickX.value = 0
  stickY.value = 0
  publish()
}

function onVisibilityChange() {
  if (document.hidden) reset()
}

watch(() => props.disabled, reset)

onMounted(() => {
  window.addEventListener('keydown', onKeydown, { passive: false })
  window.addEventListener('keyup', onKeyup, { passive: false })
  window.addEventListener('blur', reset)
  document.addEventListener('visibilitychange', onVisibilityChange)
  publish()
})

onBeforeUnmount(() => {
  reset()
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('keyup', onKeyup)
  window.removeEventListener('blur', reset)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<template>
  <div class="pixel-push-touch-controls" :class="{ disabled }" aria-label="像素推推王触控操作">
    <div
      ref="joystick"
      class="pixel-push-joystick"
      role="application"
      aria-label="移动摇杆"
      @pointerdown="onJoystickDown"
      @pointermove="onJoystickMove"
      @pointerup="onJoystickUp"
      @pointercancel="onJoystickUp"
    >
      <span class="joystick-cross horizontal" />
      <span class="joystick-cross vertical" />
      <span
        class="joystick-stick"
        :style="{ transform: `translate(${stickX}px, ${stickY}px)` }"
      />
    </div>

    <div class="pixel-push-action-buttons">
      <button
        type="button"
        class="brace-button"
        :disabled="disabled"
        @pointerdown="onActionDown(INPUT_BRACE, $event)"
        @pointerup="onActionUp"
        @pointercancel="onActionUp"
      >
        <strong>稳住</strong><small>按住</small>
      </button>
      <button
        type="button"
        class="dash-button"
        :class="{ cooling: !dashReady }"
        :disabled="disabled"
        @pointerdown="onActionDown(INPUT_DASH, $event)"
        @pointerup="onActionUp"
        @pointercancel="onActionUp"
      >
        <strong>冲刺</strong><small>{{ dashReady ? '可用' : '冷却' }}</small>
      </button>
    </div>
  </div>
</template>

<style scoped>
.pixel-push-touch-controls { display: none; grid-template-columns: 1fr 1fr; align-items: end; gap: 24px; width: 100%; padding: 8px max(8px, env(safe-area-inset-right)) max(8px, env(safe-area-inset-bottom)) max(8px, env(safe-area-inset-left)); user-select: none; -webkit-user-select: none; touch-action: none; }
.pixel-push-touch-controls.disabled { opacity: .48; }
.pixel-push-joystick { position: relative; width: clamp(116px, 34vw, 154px); aspect-ratio: 1; border: 2px solid #78dce477; border-radius: 50%; background: radial-gradient(circle, #12333edb 0 42%, #071923e8 44% 100%); box-shadow: inset 0 0 0 8px #ffffff06, 0 12px 32px #0006; touch-action: none; }
.joystick-cross { position: absolute; inset: 50% 18% auto; height: 2px; background: #83ced42b; transform: translateY(-1px); }
.joystick-cross.vertical { inset: 18% auto 18% 50%; width: 2px; height: auto; transform: translateX(-1px); }
.joystick-stick { position: absolute; left: calc(50% - 25px); top: calc(50% - 25px); width: 50px; height: 50px; border: 2px solid #b6f7f7aa; border-radius: 50%; background: linear-gradient(145deg, #4bc0c9, #176a77); box-shadow: inset 0 3px 0 #ffffff40, 0 8px 18px #0008; pointer-events: none; }
.pixel-push-action-buttons { display: flex; align-items: end; justify-content: flex-end; gap: 12px; }
.pixel-push-action-buttons button { display: grid; place-content: center; width: clamp(76px, 22vw, 96px); aspect-ratio: 1; border: 2px solid; border-radius: 50%; color: #efffff; box-shadow: inset 0 4px 0 #ffffff22, 0 10px 24px #0007; touch-action: none; }
.pixel-push-action-buttons strong { font-size: 17px; line-height: 1; }
.pixel-push-action-buttons small { margin-top: 5px; color: #ffffffb5; font-size: 10px; }
.brace-button { border-color: #9bc7ff88 !important; background: linear-gradient(145deg, #3c668a, #1d344f); }
.dash-button { width: clamp(88px, 25vw, 108px) !important; border-color: #ffe17caa !important; background: linear-gradient(145deg, #e68d35, #a3432e); }
.dash-button.cooling { filter: saturate(.35); }
.pixel-push-action-buttons button:active { transform: translateY(2px) scale(.97); }
@media (hover: none), (pointer: coarse), (max-width: 720px) {
  .pixel-push-touch-controls { display: grid; }
}
@media (max-width: 420px) {
  .pixel-push-touch-controls { gap: 10px; }
  .pixel-push-action-buttons { gap: 7px; }
}
</style>
