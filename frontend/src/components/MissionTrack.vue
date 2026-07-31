<script setup lang="ts">
import { computed } from 'vue'
import { Check, X } from '@lucide/vue'
import type { MissionRecord } from '../types/game'

const props = defineProps<{
  currentMission: number
  history: MissionRecord[]
  playerCount: number
}>()

const missions = computed(() =>
  [1, 2, 3, 4, 5].map((number) => ({
    number,
    record: props.history.find((mission) => mission.number === number),
    twoFails: props.playerCount >= 7 && number === 4,
  })),
)
</script>

<template>
  <div class="mission-track" aria-label="任务进度">
    <div
      v-for="mission in missions"
      :key="mission.number"
      class="mission-node"
      :class="{
        success: mission.record?.success,
        failed: mission.record && !mission.record.success,
        current: !mission.record && mission.number === currentMission,
      }"
    >
      <Check v-if="mission.record?.success" :size="18" />
      <X v-else-if="mission.record" :size="18" />
      <span v-else>{{ mission.number }}</span>
      <small v-if="mission.twoFails">双败</small>
    </div>
  </div>
</template>
