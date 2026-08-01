<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Crown, WifiOff } from '@lucide/vue'

const props = defineProps<{ transferAt?: string | null }>()
const now = ref(Date.now())
let timer: number | undefined

const seconds = computed(() => {
  if (!props.transferAt) return 0
  return Math.max(0, Math.ceil((Date.parse(props.transferAt) - now.value) / 1000))
})

onMounted(() => {
  timer = window.setInterval(() => {
    now.value = Date.now()
  }, 250)
})
onUnmounted(() => window.clearInterval(timer))
</script>

<template>
  <div v-if="transferAt" class="host-transfer-notice" role="status">
    <span><WifiOff :size="17" /></span>
    <div>
      <strong>房主暂时离线</strong>
      <small v-if="seconds > 0">{{ seconds }} 秒后将房主转给在线玩家</small>
      <small v-else><Crown :size="13" />正在转移房主…</small>
    </div>
  </div>
</template>

<style scoped>
.host-transfer-notice { margin-bottom: 16px; display: flex; align-items: center; gap: 11px; border: 1px solid color-mix(in srgb, var(--gold) 42%, var(--line)); border-radius: 13px; padding: 11px 13px; color: var(--gold); background: color-mix(in srgb, var(--gold) 9%, var(--surface)); }
.host-transfer-notice > span { width: 36px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 10px; background: color-mix(in srgb, var(--gold) 14%, transparent); }
.host-transfer-notice strong, .host-transfer-notice small { display: block; }
.host-transfer-notice small { margin-top: 2px; display: flex; align-items: center; gap: 4px; color: var(--muted); }
</style>
