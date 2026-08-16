import { computed, onBeforeUnmount, onMounted, readonly, ref, type Ref } from 'vue'

export function usePluginFullscreen(target: Readonly<Ref<HTMLElement | null>>) {
  const isFullscreen = ref(false)
  const isSupported = computed(() => (
    typeof document !== 'undefined'
    && typeof target.value?.requestFullscreen === 'function'
    && typeof document.exitFullscreen === 'function'
  ))

  function syncFullscreen() {
    isFullscreen.value = typeof document !== 'undefined'
      && document.fullscreenElement === target.value
  }

  async function enter(): Promise<boolean> {
    const element = target.value
    if (!element || typeof element.requestFullscreen !== 'function') return false

    try {
      await element.requestFullscreen()
      syncFullscreen()
      return true
    } catch {
      syncFullscreen()
      return false
    }
  }

  async function exit(): Promise<boolean> {
    if (typeof document === 'undefined') return false
    if (document.fullscreenElement !== target.value) {
      syncFullscreen()
      return true
    }
    if (typeof document.exitFullscreen !== 'function') return false

    try {
      await document.exitFullscreen()
      syncFullscreen()
      return true
    } catch {
      syncFullscreen()
      return false
    }
  }

  async function toggle(): Promise<boolean> {
    return typeof document !== 'undefined' && document.fullscreenElement === target.value
      ? exit()
      : enter()
  }

  onMounted(() => {
    document.addEventListener('fullscreenchange', syncFullscreen)
    syncFullscreen()
  })

  onBeforeUnmount(() => {
    document.removeEventListener('fullscreenchange', syncFullscreen)
  })

  return {
    isFullscreen: readonly(isFullscreen),
    isSupported,
    enter,
    exit,
    toggle,
  }
}
