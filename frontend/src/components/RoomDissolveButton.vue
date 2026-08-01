<script setup lang="ts">
import { ref } from 'vue'
import { Trash2, X } from '@lucide/vue'

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
    aria-label="解散当前房间"
    :disabled="busy"
    @click="showConfirmation = true"
  >
    <Trash2 :size="17" />
    <span>解散房间</span>
  </button>

  <div
    v-if="showConfirmation"
    class="modal-backdrop"
    @click.self="showConfirmation = false"
  >
    <section
      class="modal-card dissolve-room-modal"
      role="dialog"
      aria-modal="true"
      aria-label="确认解散房间"
    >
      <button
        class="modal-close"
        type="button"
        aria-label="取消解散"
        @click="showConfirmation = false"
      >
        <X :size="20" />
      </button>
      <Trash2 :size="28" />
      <h2>解散这个房间？</h2>
      <p>所有等待中的玩家都会返回大厅。</p>
      <div class="dissolve-room-actions">
        <button type="button" @click="showConfirmation = false">取消</button>
        <button
          type="button"
          class="danger"
          :disabled="busy"
          @click="confirmDissolve"
        >
          确认解散
        </button>
      </div>
    </section>
  </div>
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

.dissolve-room-modal {
  width: min(92vw, 430px);
  text-align: center;
}

.dissolve-room-modal > svg {
  color: #efaaa7;
}

.dissolve-room-modal h2 {
  margin: 12px 0 6px;
}

.dissolve-room-modal p {
  color: var(--muted);
}

.dissolve-room-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
  margin-top: 18px;
}

.dissolve-room-actions button {
  min-height: 43px;
  border: 1px solid var(--line);
  border-radius: 11px;
  color: var(--text);
  background: transparent;
  font-weight: 850;
}

.dissolve-room-actions button.danger {
  border-color: rgba(225, 114, 114, .34);
  color: #f1b0b0;
  background: rgba(133, 47, 52, .18);
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
