<script setup lang="ts">
import { ref } from 'vue'
import { Trash2, X } from '@lucide/vue'

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

  <Teleport to="body">
    <div v-if="confirming" class="modal-backdrop" @click.self="confirming = false">
      <section class="modal-card cleanup-confirm-card" role="dialog" aria-modal="true">
        <button class="modal-close" type="button" aria-label="关闭" @click="confirming = false">
          <X :size="20" />
        </button>
        <span class="cleanup-confirm-icon"><Trash2 :size="25" /></span>
        <small>房间 {{ roomCode }}</small>
        <h2>彻底清理这个房间？</h2>
        <p>房间内所有真人已离线超过 10 分钟。清理后无法恢复，但历史战绩不会删除。</p>
        <div class="cleanup-confirm-actions">
          <button type="button" @click="confirming = false">取消</button>
          <button type="button" class="danger" @click="confirmCleanup">确认清理</button>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.cleanup-room-button { min-height: 38px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: 1px solid rgba(231, 119, 119, .38); border-radius: 10px; padding: 0 12px; color: #f0aaa6; background: rgba(134, 45, 49, .18); font-weight: 850; white-space: nowrap; }
.cleanup-room-button:disabled { opacity: .45; }
.cleanup-confirm-card { width: min(92vw, 430px); display: grid; justify-items: center; gap: 12px; padding: 30px; text-align: center; }
.cleanup-confirm-card small { color: var(--gold); letter-spacing: .1em; }
.cleanup-confirm-card h2, .cleanup-confirm-card p { margin: 0; }
.cleanup-confirm-card p { color: var(--muted); line-height: 1.65; }
.cleanup-confirm-icon { width: 54px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid rgba(231, 119, 119, .34); border-radius: 16px; color: #efaaa7; background: rgba(134, 45, 49, .16); }
.cleanup-confirm-actions { width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 9px; margin-top: 6px; }
.cleanup-confirm-actions button { min-height: 44px; border: 1px solid var(--line); border-radius: 11px; color: var(--text); background: var(--surface); font-weight: 850; }
.cleanup-confirm-actions .danger { border-color: rgba(231, 119, 119, .42); color: #ffd0cc; background: rgba(143, 48, 52, .52); }
</style>
