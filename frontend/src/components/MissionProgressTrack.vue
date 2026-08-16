<script setup lang="ts">
import { Check, X } from '@lucide/vue'
import type { MissionProgressItem } from './uiTypes'

defineProps<{
  items: MissionProgressItem[]
}>()

const emit = defineEmits<{
  select: [missionNumber: number]
}>()
</script>

<template>
  <div class="mission-track" aria-label="任务进度">
    <button
      v-for="item in items"
      :key="item.number"
      type="button"
      class="mission-node"
      :class="[item.status, { replayable: item.replayable }]"
      :disabled="!item.replayable"
      :aria-label="item.label"
      @click="emit('select', item.number)"
    >
      <span class="mission-requirement">
        {{ item.requirement }}<small>人</small>
      </span>
      <span
        v-if="item.status === 'success' || item.status === 'failed'"
        class="mission-outcome"
        aria-hidden="true"
      >
        <Check v-if="item.status === 'success'" :size="10" />
        <X v-else :size="10" />
      </span>
      <small v-if="item.note" class="mission-fail-note">{{ item.note }}</small>
    </button>
  </div>
</template>

<style scoped>
.mission-track { display: grid; grid-template-columns: repeat(5, 1fr); align-items: center; gap: 8px; margin: 8px 0 24px; }
.mission-node { position: relative; display: grid; place-items: center; width: 42px; height: 42px; justify-self: center; border: 1px solid var(--line); border-radius: 50%; padding: 0; color: var(--muted); background: var(--surface-inset); font-size: 13px; font-weight: 800; cursor: default; }
.mission-node:disabled { opacity: 1; }
.mission-node.replayable { cursor: pointer; }
.mission-node.replayable:hover { transform: translateY(-1px); }
.mission-node:not(:last-child)::after { position: absolute; z-index: -1; top: 50%; left: 100%; width: calc((min(100vw, 720px) - 106px) / 5 - 8px); height: 1px; background: var(--line); content: ''; }
.mission-node.current { border-color: var(--accent); color: var(--accent); box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 9%, transparent); }
.mission-node.success { border-color: color-mix(in srgb, var(--green) 55%, var(--line)); color: color-mix(in srgb, var(--green) 78%, var(--text)); background: color-mix(in srgb, var(--green) 28%, var(--surface-inset)); }
.mission-node.failed { border-color: color-mix(in srgb, var(--red) 55%, var(--line)); color: color-mix(in srgb, var(--red) 78%, var(--text)); background: color-mix(in srgb, var(--red) 28%, var(--surface-inset)); }
.mission-requirement { display: inline-flex; align-items: baseline; line-height: 1; }
.mission-requirement small { margin-left: 1px; font-size: 8px; }
.mission-outcome { position: absolute; top: -4px; right: -4px; display: grid; place-items: center; width: 17px; height: 17px; border: 2px solid var(--surface-strong); border-radius: 50%; color: var(--text); background: var(--surface-strong); }
.mission-fail-note { position: absolute; top: 44px; color: var(--accent-deep); font-size: 8px; white-space: nowrap; }
</style>
