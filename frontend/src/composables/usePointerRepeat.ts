import { onBeforeUnmount, onMounted } from 'vue'

interface RepeatState {
  delayTimer: number | null
  intervalTimer: number | null
}

interface PointerRepeatOptions {
  delayMs?: number
  intervalMs?: number
}

function acceptsPointer(event: PointerEvent): boolean {
  return event.pointerType !== 'mouse' || event.button === 0
}

export function usePointerRepeat(options: PointerRepeatOptions = {}) {
  const delayMs = options.delayMs ?? 190
  const intervalMs = options.intervalMs ?? 70
  const repeats = new Map<number, RepeatState>()

  function stopRepeating(pointer: number | PointerEvent) {
    const pointerId = typeof pointer === 'number' ? pointer : pointer.pointerId
    const state = repeats.get(pointerId)
    if (!state) return
    if (state.delayTimer !== null) window.clearTimeout(state.delayTimer)
    if (state.intervalTimer !== null) window.clearInterval(state.intervalTimer)
    repeats.delete(pointerId)
  }

  function stopAllRepeats() {
    for (const pointerId of [...repeats.keys()]) stopRepeating(pointerId)
  }

  function beginRepeat(event: PointerEvent, action: () => void) {
    if (!acceptsPointer(event)) return
    event.preventDefault()
    stopRepeating(event.pointerId)
    action()

    if (
      event.currentTarget instanceof Element
      && 'setPointerCapture' in event.currentTarget
      && typeof event.currentTarget.setPointerCapture === 'function'
    ) event.currentTarget.setPointerCapture(event.pointerId)

    const state: RepeatState = { delayTimer: null, intervalTimer: null }
    state.delayTimer = window.setTimeout(() => {
      if (repeats.get(event.pointerId) !== state) return
      state.delayTimer = null
      state.intervalTimer = window.setInterval(action, intervalMs)
    }, delayMs)
    repeats.set(event.pointerId, state)
  }

  function runOnce(event: PointerEvent, action: () => void) {
    if (!acceptsPointer(event)) return
    event.preventDefault()
    action()
  }

  onMounted(() => {
    window.addEventListener('pointerup', stopRepeating)
    window.addEventListener('pointercancel', stopRepeating)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('pointerup', stopRepeating)
    window.removeEventListener('pointercancel', stopRepeating)
    stopAllRepeats()
  })

  return { beginRepeat, runOnce, stopRepeating, stopAllRepeats }
}
