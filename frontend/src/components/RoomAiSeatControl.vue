<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Bot, Plus } from '@lucide/vue'
import type { ArcadeAiConfig } from '../types/arcade'

const props = withDefaults(defineProps<{
  config?: ArcadeAiConfig | null
  availableSeats: number
  busy?: boolean
}>(), {
  config: null,
  busy: false,
})

const emit = defineEmits<{
  add: [difficulty: string]
}>()

const difficulties = computed(() => props.config?.difficulties ?? [])
const defaultDifficulty = computed(() => (
  props.config?.defaultDifficulty
  ?? difficulties.value[0]?.key
  ?? 'normal'
))
const selectedDifficulty = ref(defaultDifficulty.value)

watch(defaultDifficulty, (difficulty) => {
  selectedDifficulty.value = difficulty
})

function addAiPlayer() {
  emit('add', selectedDifficulty.value)
}
</script>

<template>
  <article class="room-ai-seat-control" aria-label="AI 空席位">
    <span class="room-ai-seat-icon" aria-hidden="true">
      <Bot :size="20" />
    </span>
    <div class="room-ai-seat-copy">
      <strong>添加 AI 玩家</strong>
      <small>填补空席 · 还可加入 {{ availableSeats }} 名</small>
    </div>
    <label v-if="difficulties.length > 1" class="room-ai-difficulty">
      <span class="sr-only">AI 难度</span>
      <select v-model="selectedDifficulty" aria-label="AI 难度">
        <option
          v-for="difficulty in difficulties"
          :key="difficulty.key"
          :value="difficulty.key"
        >{{ difficulty.label }}</option>
      </select>
    </label>
    <button
      type="button"
      class="room-ai-add-button"
      aria-label="添加 AI 玩家"
      :disabled="busy"
      @click="addAiPlayer"
    >
      <Plus :size="16" />
      <span>添加</span>
    </button>
  </article>
</template>

<style scoped>
.room-ai-seat-control {
  display: flex;
  flex: 0 0 var(--player-card-width);
  align-items: center;
  gap: 10px;
  min-width: 0;
  min-height: 68px;
  padding: 10px;
  border: 1px dashed color-mix(in srgb, var(--gold) 48%, var(--line));
  border-radius: 12px;
  background: color-mix(in srgb, var(--gold) 5%, var(--surface-elevated));
}

.room-ai-seat-icon {
  flex: 0 0 auto;
  width: 34px;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: var(--gold);
  background: color-mix(in srgb, var(--gold) 13%, transparent);
}

.room-ai-seat-copy {
  min-width: 0;
  flex: 1;
}

.room-ai-seat-copy strong,
.room-ai-seat-copy small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-ai-seat-copy small {
  margin-top: 2px;
  color: var(--muted);
  font-size: 10px;
}

.room-ai-difficulty {
  flex: 0 0 auto;
}

.room-ai-difficulty select {
  min-width: 76px;
  min-height: 34px;
  border: 1px solid var(--line);
  border-radius: 9px;
  padding: 0 25px 0 9px;
  color: var(--text);
  background: var(--surface-raised);
  font: inherit;
  font-size: 11px;
}

.room-ai-add-button {
  flex: 0 0 auto;
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: 1px solid color-mix(in srgb, var(--gold) 58%, var(--line));
  border-radius: 9px;
  padding: 0 10px;
  color: var(--surface-inset);
  background: var(--gold);
  font-weight: 900;
}

.room-ai-add-button:disabled {
  cursor: wait;
  opacity: .55;
}

@media (max-width: 860px) {
  .room-ai-seat-control {
    flex-basis: calc(33.333333% - 6.667px);
    flex-wrap: wrap;
  }

  .room-ai-seat-copy {
    min-width: calc(100% - 44px);
  }

  .room-ai-difficulty,
  .room-ai-add-button {
    flex: 1 1 0;
  }

  .room-ai-difficulty select,
  .room-ai-add-button {
    width: 100%;
  }
}

@media (max-width: 620px), (orientation: landscape) and (max-height: 600px) and (max-width: 980px) {
  .room-ai-seat-control {
    flex-basis: calc(50% - 5px);
  }
}

@media (max-width: 430px) {
  .room-ai-seat-control {
    flex-basis: 100%;
  }
}
</style>
