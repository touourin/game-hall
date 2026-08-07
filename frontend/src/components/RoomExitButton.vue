<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowLeft, DoorOpen, Flag, X } from '@lucide/vue'
import BackNavigationButton from './BackNavigationButton.vue'

const props = withDefaults(
  defineProps<{
    description?: string
    busy?: boolean
    mode?: 'leave' | 'solo-active' | 'multiplayer-active' | 'spectator'
    abandonLabel?: string
  }>(),
  {
    description: '退出后将返回游戏大厅。',
    busy: false,
    mode: 'leave',
  },
)

const emit = defineEmits<{
  leave: []
  detach: []
  abandon: []
}>()

const showConfirmation = ref(false)
const title = computed(() => ({
  leave: '退出当前房间？',
  spectator: '退出当前观战？',
  'solo-active': '放弃本次挑战？',
  'multiplayer-active': '离开当前对局？',
}[props.mode]))
const dangerLabel = computed(() => {
  if (props.mode === 'leave') return '确认退出'
  if (props.mode === 'spectator') return '退出观战'
  if (props.mode === 'solo-active') return '放弃并退出'
  return props.abandonLabel ?? '认输并退出'
})

function confirm(action: 'leave' | 'detach' | 'abandon') {
  showConfirmation.value = false
  if (action === 'leave') emit('leave')
  else if (action === 'detach') emit('detach')
  else emit('abandon')
}
</script>

<template>
  <BackNavigationButton
    class="exit-room-trigger"
    label="退出当前房间"
    :disabled="busy"
    @click="showConfirmation = true"
  />

  <div
    v-if="showConfirmation"
    class="modal-backdrop"
    @click.self="showConfirmation = false"
  >
    <section
      class="modal-card exit-room-modal"
      role="dialog"
      aria-modal="true"
      :aria-label="title"
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
      <h2>{{ title }}</h2>
      <p>{{ description }}</p>
      <div class="exit-room-actions">
        <button
          v-if="mode !== 'multiplayer-active'"
          type="button"
          class="secondary-button"
          @click="showConfirmation = false"
        >
          继续游戏
        </button>
        <button
          v-if="mode === 'multiplayer-active'"
          type="button"
          class="secondary-button"
          :disabled="busy"
          @click="confirm('detach')"
        >
          <ArrowLeft :size="17" /> 暂时返回
        </button>
        <button
          type="button"
          class="danger-button"
          :disabled="busy"
          @click="confirm(mode === 'leave' || mode === 'spectator' ? 'leave' : 'abandon')"
        >
          <DoorOpen v-if="mode === 'leave' || mode === 'spectator'" :size="17" />
          <Flag v-else :size="17" />
          {{ dangerLabel }}
        </button>
      </div>
    </section>
  </div>
</template>
