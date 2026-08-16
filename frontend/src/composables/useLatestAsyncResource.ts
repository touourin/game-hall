import { onBeforeUnmount, ref, shallowRef } from 'vue'

export function useLatestAsyncResource<T>(
  initialValue: () => T,
  fallbackError: string,
) {
  const data = shallowRef<T>(initialValue())
  const loading = ref(false)
  const error = ref<string | null>(null)
  let generation = 0

  async function execute(loader: () => Promise<T>): Promise<T | null> {
    const currentGeneration = ++generation
    data.value = initialValue()
    loading.value = true
    error.value = null

    try {
      const result = await loader()
      if (currentGeneration !== generation) return null
      data.value = result
      return result
    } catch (caught) {
      if (currentGeneration !== generation) return null
      error.value = caught instanceof Error && caught.message.trim()
        ? caught.message
        : fallbackError
      return null
    } finally {
      if (currentGeneration === generation) loading.value = false
    }
  }

  function reset(): void {
    generation += 1
    data.value = initialValue()
    loading.value = false
    error.value = null
  }

  onBeforeUnmount(() => {
    generation += 1
  })

  return { data, loading, error, execute, reset }
}
