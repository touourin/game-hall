<script setup lang="ts">
import { ref } from 'vue'
import { Trash2 } from '@lucide/vue'
import ConfirmModal from './ui/ConfirmModal.vue'

withDefaults(
  defineProps<{
    busy?: boolean
  }>(),
  {
    busy: false,
  },
)

const emit = defineEmits<{
  confirm: []
}>()

const showConfirmation = ref(false)

function confirmDissolve() {
  showConfirmation.value = false
  emit('confirm')
}
</script>

<template>
  <button
    type="button"
    class="dissolve-room-trigger"
    data-ui-interaction="choice"
    aria-label="解散当前房间"
    :disabled="busy"
    @click="showConfirmation = true"
  >
    <Trash2 :size="17" />
    <span>解散房间</span>
  </button>

  <ConfirmModal
    v-if="showConfirmation"
    title="解散这个房间？"
    description="所有等待中的玩家都会返回大厅。"
    confirm-label="确认解散"
    close-label="取消解散"
    panel-class="dissolve-room-modal"
    :busy="busy"
    tone="danger"
    @close="showConfirmation = false"
    @confirm="confirmDissolve"
  >
    <template #icon><Trash2 :size="28" /></template>
  </ConfirmModal>
</template>

<style scoped>
.dissolve-room-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 42px;
  border: 1px solid rgba(225, 114, 114, .3);
  border-radius: 11px;
  padding: 0 12px;
  color: #efaaa7;
  background: rgba(133, 47, 52, .16);
  font-weight: 800;
}

@media (max-width: 600px) {
  .dissolve-room-trigger {
    justify-content: center;
    width: 42px;
    padding: 0;
  }

  .dissolve-room-trigger span {
    display: none;
  }
}
</style>
