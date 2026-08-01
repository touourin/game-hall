<script setup lang="ts">
import { Check, Images } from '@lucide/vue'
import { ROLE_SKINS, type RoleSkinId } from '../roleSkins'

defineProps<{
  modelValue: RoleSkinId
}>()

const emit = defineEmits<{
  'update:modelValue': [skin: RoleSkinId]
}>()
</script>

<template>
  <section class="surface role-skin-lobby-card" aria-labelledby="role-skin-title">
    <div class="role-skin-lobby-heading">
      <span class="role-skin-lobby-icon"><Images :size="20" /></span>
      <div>
        <strong id="role-skin-title">我的身份卡画风</strong>
        <small>仅影响你看到的身份卡 · 开局后锁定</small>
      </div>
    </div>

    <div class="role-skin-options" role="group" aria-label="选择本局身份卡画风">
      <button
        v-for="skin in ROLE_SKINS"
        :key="skin.id"
        type="button"
        :data-role-skin="skin.id"
        :class="{ active: modelValue === skin.id }"
        :aria-pressed="modelValue === skin.id"
        @click="emit('update:modelValue', skin.id)"
      >
        <span>
          <strong>{{ skin.name }}</strong>
          <small>{{ skin.description }}</small>
        </span>
        <Check v-if="modelValue === skin.id" :size="16" />
      </button>
    </div>
  </section>
</template>

<style scoped>
.role-skin-lobby-card {
  display: grid;
  gap: 14px;
  padding: 16px;
}

.role-skin-lobby-heading {
  display: flex;
  align-items: center;
  gap: 12px;
}

.role-skin-lobby-heading > div {
  display: grid;
  gap: 4px;
}

.role-skin-lobby-heading strong {
  font-family: "Songti SC", "STSong", serif;
  font-size: 14px;
}

.role-skin-lobby-heading small {
  color: var(--muted);
  font-size: 10px;
}

.role-skin-lobby-icon {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 42px;
  height: 42px;
  border: 1px solid rgba(225, 188, 104, 0.18);
  border-radius: 14px;
  color: var(--gold);
  background: rgba(225, 188, 104, 0.08);
}

.role-skin-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.role-skin-options button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 13px;
  padding: 10px;
  color: var(--text);
  background: rgba(var(--surface-header-rgb), 0.58);
  text-align: left;
  cursor: pointer;
}

.role-skin-options button.active {
  border-color: rgba(225, 188, 104, 0.52);
  background: rgba(225, 188, 104, 0.11);
  box-shadow: inset 0 0 0 1px rgba(225, 188, 104, 0.08);
}

.role-skin-options button > span {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.role-skin-options strong,
.role-skin-options small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-skin-options strong {
  font-family: "Songti SC", "STSong", serif;
  font-size: 12px;
}

.role-skin-options small {
  color: var(--muted);
  font-size: 8px;
}

.role-skin-options button > svg {
  flex: 0 0 auto;
  color: var(--gold);
}

@media (max-width: 430px) {
  .role-skin-options small {
    display: none;
  }
}
</style>
