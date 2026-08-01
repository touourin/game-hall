<script setup lang="ts">
import { ref } from 'vue'
import { DoorOpen, X } from '@lucide/vue'

withDefaults(
  defineProps<{
    description?: string
    busy?: boolean
  }>(),
  {
    description: '退出后将返回游戏大厅。',
    busy: false,
  },
)

const emit = defineEmits<{
  confirm: []
}>()

const showConfirmation = ref(false)

function confirmExit() {
  showConfirmation.value = false
  emit('confirm')
}
</script>

<template>
  <button
    class="header-action exit-room-trigger"
    type="button"
    aria-label="退出当前房间"
    :disabled="busy"
    @click="showConfirmation = true"
  >
    <DoorOpen :size="20" />
  </button>

  <div
    v-if="showConfirmation"
    class="modal-backdrop"
    @click.self="showConfirmation = false"
  >
    <section
      class="modal-card exit-room-modal"
      role="dialog"
      aria-modal="true"
      aria-label="确认退出房间"
    >
      <button
        class="modal-close"
        type="button"
        aria-label="取消退出"
        @click="showConfirmation = false"
      >
        <X :size="20" />
      </button>
      <span class="modal-icon"><DoorOpen :size="25" /></span>
      <h2>退出当前房间？</h2>
      <p>{{ description }}</p>
      <div class="exit-room-actions">
        <button
          type="button"
          class="secondary-button"
          @click="showConfirmation = false"
        >
          继续游戏
        </button>
        <button
          type="button"
          class="danger-button"
          :disabled="busy"
          @click="confirmExit"
        >
          <DoorOpen :size="17" /> 确认退出
        </button>
      </div>
    </section>
  </div>
</template>
