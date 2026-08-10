<script setup lang="ts">
import { ref } from 'vue'
import { Trash2 } from '@lucide/vue'
import ConfirmModal from './ui/ConfirmModal.vue'

defineProps<{ roomCode: string; busy?: boolean }>()
const emit = defineEmits<{ confirm: [] }>()
const confirming = ref(false)

function confirmCleanup() {
  confirming.value = false
  emit('confirm')
}
</script>

<template>
  <button
    type="button"
    class="cleanup-room-button"
    :disabled="busy"
    @click.stop="confirming = true"
  >
    <Trash2 :size="16" />清理房间
  </button>

  <ConfirmModal
    v-if="confirming"
    title="彻底清理这个房间？"
    :description="`房间 ${roomCode} · 房间内所有真人已离线超过 10 分钟。清理后无法恢复，但历史战绩不会删除。`"
    confirm-label="确认清理"
    close-label="取消清理"
    panel-class="cleanup-confirm-card"
    :busy="busy"
    tone="danger"
    @close="confirming = false"
    @confirm="confirmCleanup"
  >
    <template #icon><Trash2 :size="25" /></template>
  </ConfirmModal>
</template>

<style scoped>
.cleanup-room-button { min-height: 38px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: 1px solid rgba(231, 119, 119, .38); border-radius: 10px; padding: 0 12px; color: #f0aaa6; background: rgba(134, 45, 49, .18); font-weight: 850; white-space: nowrap; }
.cleanup-room-button:disabled { opacity: .45; }
</style>
