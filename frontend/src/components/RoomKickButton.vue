<script setup lang="ts">
import { ref } from 'vue'
import { UserMinus, X } from '@lucide/vue'

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
    :aria-label="`移除${playerName}`"
    :disabled="busy"
    @click="showConfirmation = true"
  >
    <UserMinus :size="16" />
  </button>

  <Teleport to="body">
    <div
      v-if="showConfirmation"
      class="modal-backdrop kick-player-backdrop"
      @click.self="showConfirmation = false"
    >
      <section
        class="modal-card kick-player-modal"
        role="dialog"
        aria-modal="true"
        :aria-label="`确认移除${playerName}`"
      >
        <button
          class="modal-close"
          type="button"
          aria-label="取消移除"
          @click="showConfirmation = false"
        >
          <X :size="20" />
        </button>
        <UserMinus :size="28" />
        <h2>移除{{ playerName }}？</h2>
        <p>该玩家会立即离开当前房间。</p>
        <div class="kick-player-actions">
          <button type="button" @click="showConfirmation = false">取消</button>
          <button
            type="button"
            class="danger"
            :disabled="busy"
            @click="confirmKick"
          >
            确认移除
          </button>
        </div>
      </section>
    </div>
  </Teleport>
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

.kick-player-backdrop {
  z-index: 90;
}

.kick-player-modal {
  width: min(92vw, 430px);
  text-align: center;
}

.kick-player-modal > svg {
  color: #efaaa7;
}

.kick-player-modal h2 {
  margin: 12px 0 6px;
}

.kick-player-modal p {
  color: var(--muted);
}

.kick-player-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
  margin-top: 18px;
}

.kick-player-actions button {
  min-height: 43px;
  border: 1px solid var(--line);
  border-radius: 11px;
  color: var(--text);
  background: transparent;
  font-weight: 850;
}

.kick-player-actions button.danger {
  border-color: rgba(225, 114, 114, .34);
  color: #f1b0b0;
  background: rgba(133, 47, 52, .18);
}
</style>
