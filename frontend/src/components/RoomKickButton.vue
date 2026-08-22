<script setup lang="ts">
import { ref } from 'vue'
import { UserMinus } from '@lucide/vue'
import ConfirmModal from './ui/ConfirmModal.vue'

withDefaults(
  defineProps<{
    playerName: string
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

function confirmKick() {
  showConfirmation.value = false
  emit('confirm')
}
</script>

<template>
  <button
    type="button"
    class="kick-player-button"
    data-ui-interaction="choice"
    :aria-label="`移除${playerName}`"
    :disabled="busy"
    @click="showConfirmation = true"
  >
    <UserMinus :size="16" />
  </button>

  <ConfirmModal
    v-if="showConfirmation"
    :title="`移除${playerName}？`"
    description="该玩家会立即离开当前房间。"
    confirm-label="确认移除"
    close-label="取消移除"
    panel-class="kick-player-modal"
    :busy="busy"
    tone="danger"
    @close="showConfirmation = false"
    @confirm="confirmKick"
  >
    <template #icon><UserMinus :size="28" /></template>
  </ConfirmModal>
</template>

<style scoped>
.kick-player-button {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 34px;
  aspect-ratio: 1;
  border: 1px solid rgba(225, 114, 114, .24);
  border-radius: 10px;
  color: #efaaa7;
  background: rgba(133, 47, 52, .12);
}

</style>
