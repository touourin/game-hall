<script setup lang="ts">
import { computed, ref } from 'vue'
import { Calculator, Handshake, OctagonX, Undo2 } from '@lucide/vue'
import type {
  ArcadeGameRequest,
  ArcadeGameRequestKind,
} from '../types/arcade'
import ConfirmModal from './ui/ConfirmModal.vue'

const props = withDefaults(
  defineProps<{
    request: ArcadeGameRequest | null
    canRequestUndo?: boolean
    canRequestDraw?: boolean
    canRequestScore?: boolean
    canRequestEndTable?: boolean
    busy?: boolean
  }>(),
  {
    canRequestUndo: false,
    canRequestDraw: false,
    canRequestScore: false,
    canRequestEndTable: false,
    busy: false,
  },
)

const emit = defineEmits<{
  request: [kind: ArcadeGameRequestKind]
  resolve: [accept: boolean]
}>()

const showEndTableConfirmation = ref(false)
const requestLabels: Record<ArcadeGameRequestKind, string> = {
  undo: '悔棋',
  draw: '和棋',
  score: '点目',
  end_table: '结束本桌',
}
const requestLabel = computed(() => requestLabels[props.request?.kind ?? 'undo'])
const approvalProgress = computed(() => {
  if (!props.request) return ''
  const approved = props.request.approvalCount ?? props.request.approvedPlayerIds?.length ?? 1
  const required = props.request.requiredApprovalCount ?? 2
  return `${approved} / ${required} 人已同意`
})

function requestEndTable() {
  showEndTableConfirmation.value = false
  emit('request', 'end_table')
}
</script>

<template>
  <section class="surface match-request-panel" aria-label="对局协商">
    <template v-if="request">
      <div class="request-copy">
        <strong>{{ request.requesterName }}</strong>
        <span>申请{{ requestLabel }}</span>
        <small v-if="request.kind === 'end_table'">{{ approvalProgress }}</small>
      </div>
      <div v-if="request.isMine" class="request-response-actions request-waiting-actions">
        <p>等待其他玩家确认</p>
        <button type="button" data-ui-interaction="lift" :disabled="busy" @click="emit('resolve', false)">撤回申请</button>
      </div>
      <div v-else-if="request.hasApproved" class="request-response-actions request-waiting-actions">
        <p>你已同意，等待其他玩家</p>
      </div>
      <div v-else-if="request.canRespond !== false" class="request-response-actions">
        <button type="button" data-ui-interaction="lift" :disabled="busy" @click="emit('resolve', false)">拒绝</button>
        <button type="button" class="accept" data-ui-interaction="lift" :disabled="busy" @click="emit('resolve', true)">同意</button>
      </div>
      <div v-else class="request-response-actions request-waiting-actions">
        <p>等待仍在本桌的玩家确认</p>
      </div>
    </template>
    <template v-else>
      <span>对局协商</span>
      <div class="request-actions">
        <button
          v-if="canRequestUndo"
          type="button"
          data-ui-interaction="lift"
          :disabled="busy"
          @click="emit('request', 'undo')"
        >
          <Undo2 :size="16" />申请悔棋
        </button>
        <button
          v-if="canRequestDraw"
          type="button"
          data-ui-interaction="lift"
          :disabled="busy"
          @click="emit('request', 'draw')"
        >
          <Handshake :size="16" />申请和棋
        </button>
        <button
          v-if="canRequestScore"
          type="button"
          data-ui-interaction="lift"
          :disabled="busy"
          @click="emit('request', 'score')"
        >
          <Calculator :size="16" />申请点目
        </button>
        <button
          v-if="canRequestEndTable"
          type="button"
          class="end-table-button"
          data-ui-interaction="lift"
          :disabled="busy"
          @click="showEndTableConfirmation = true"
        >
          <OctagonX :size="16" />申请结束本桌
        </button>
      </div>
    </template>
  </section>

  <ConfirmModal
    v-if="showEndTableConfirmation"
    title="申请结束本桌？"
    description="所有真人玩家同意后，本桌立即终止并返回等待房间；当前进度不会计入战绩。"
    confirm-label="发起申请"
    cancel-label="取消"
    close-label="取消申请"
    panel-class="end-table-modal"
    tone="danger"
    :busy="busy"
    inline
    @close="showEndTableConfirmation = false"
    @confirm="requestEndTable"
  >
    <template #icon><OctagonX :size="28" /></template>
  </ConfirmModal>
</template>

<style scoped>
.match-request-panel { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 13px 15px; }
.match-request-panel > span { color: var(--muted); font-weight: 800; }
.request-copy { display: grid; gap: 2px; }
.request-copy span { color: var(--muted); }
.request-copy small { color: var(--accent); }
.request-actions,.request-response-actions { display: flex; align-items: center; gap: 8px; }
.match-request-panel p { margin: 0; color: var(--accent); }
.match-request-panel button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 38px; border: 1px solid var(--line); border-radius: 10px; padding: 0 11px; color: var(--text); background: transparent; font-weight: 800; }
.request-waiting-actions { justify-content: flex-end; }
.request-response-actions button.accept { border-color: color-mix(in srgb, var(--accent) 38%, var(--line)); color: var(--accent); background: color-mix(in srgb, var(--accent) 8%, transparent); }
.match-request-panel .end-table-button { border-color: rgba(225, 114, 114, .3); color: #efaaa7; background: rgba(133, 47, 52, .12); }
:global(.modal-card.end-table-modal) { width: min(92vw, 460px); text-align: center; }
@media (max-width: 620px) {
  .match-request-panel { align-items: stretch; flex-direction: column; }
  .request-actions,.request-response-actions { display: grid; grid-template-columns: 1fr 1fr; }
  .request-actions .end-table-button:only-child { grid-column: 1 / -1; }
}
</style>
