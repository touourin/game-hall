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

    <div class="role-skin-options" role="group" aria-label="预览并选择本局身份卡画风">
      <button
        v-for="skin in ROLE_SKINS"
        :key="skin.id"
        type="button"
        :data-role-skin="skin.id"
        :class="{ active: modelValue === skin.id }"
        :aria-pressed="modelValue === skin.id"
        :aria-label="`${skin.name}，${skin.tier}画风：${skin.description}`"
        @click="emit('update:modelValue', skin.id)"
      >
        <span class="role-skin-preview">
          <img
            :src="skin.preview"
            :alt="`${skin.name}身份卡画风预览`"
            loading="lazy"
            draggable="false"
          />
          <small class="role-skin-tier" :data-tier="skin.tier">
            {{ skin.tier }}
          </small>
          <span
            v-if="modelValue === skin.id"
            class="role-skin-check"
            aria-hidden="true"
          >
            <Check :size="15" />
          </span>
        </span>
        <span class="role-skin-copy">
          <strong>{{ skin.name }}</strong>
          <small>{{ skin.description }}</small>
        </span>
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
  grid-auto-columns: minmax(154px, 1fr);
  grid-auto-flow: column;
  gap: 10px;
  margin-inline: -4px;
  padding: 2px 4px 9px;
  overflow-x: auto;
  overscroll-behavior-inline: contain;
  scrollbar-color: rgba(225, 188, 104, 0.34) transparent;
  scrollbar-width: thin;
  scroll-snap-type: inline proximity;
}

.role-skin-options button {
  display: grid;
  align-content: start;
  gap: 9px;
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 15px;
  padding: 6px 6px 10px;
  color: var(--text);
  background: rgba(var(--surface-header-rgb), 0.58);
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  scroll-snap-align: start;
  transition: border-color 160ms ease, background 160ms ease, transform 160ms ease;
}

.role-skin-options button.active {
  border-color: rgba(225, 188, 104, 0.52);
  background: rgba(225, 188, 104, 0.11);
  box-shadow: inset 0 0 0 1px rgba(225, 188, 104, 0.08);
}

.role-skin-options button:active {
  transform: scale(0.985);
}

.role-skin-preview {
  position: relative;
  display: block;
  aspect-ratio: 4 / 3;
  border-radius: 10px;
  background: rgba(2, 10, 12, 0.78);
  overflow: hidden;
}

.role-skin-preview::after {
  position: absolute;
  inset: auto 0 0;
  height: 42%;
  background: linear-gradient(transparent, rgba(2, 10, 12, 0.76));
  content: '';
  pointer-events: none;
}

.role-skin-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 220ms ease;
}

.role-skin-options button:hover .role-skin-preview img {
  transform: scale(1.035);
}

.role-skin-tier,
.role-skin-check {
  position: absolute;
  z-index: 1;
  top: 7px;
  display: inline-grid;
  place-items: center;
  min-height: 23px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
  background: rgba(2, 10, 12, 0.72);
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.24);
  backdrop-filter: blur(7px);
}

.role-skin-tier {
  left: 7px;
  border-radius: 999px;
  padding: 0 8px;
  font-size: 8px;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.role-skin-tier[data-tier="终极"] {
  border-color: rgba(255, 226, 151, 0.62);
  color: #ffe297;
  background: rgba(83, 55, 9, 0.76);
}

.role-skin-check {
  right: 7px;
  width: 23px;
  border-color: rgba(225, 188, 104, 0.58);
  border-radius: 50%;
  color: #ffe297;
  background: rgba(69, 46, 8, 0.82);
}

.role-skin-copy {
  display: grid;
  gap: 3px;
  min-width: 0;
  padding-inline: 3px;
}

.role-skin-copy strong,
.role-skin-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-skin-copy strong {
  font-family: "Songti SC", "STSong", serif;
  font-size: 12px;
}

.role-skin-copy small {
  color: var(--muted);
  font-size: 8px;
}

@media (min-width: 820px) {
  .role-skin-options {
    grid-auto-flow: initial;
    grid-template-columns: repeat(5, minmax(0, 1fr));
  }
}

@media (max-width: 430px) {
  .role-skin-lobby-card {
    padding-inline: 13px;
  }

  .role-skin-options {
    grid-auto-columns: minmax(148px, 46vw);
  }
}
</style>
