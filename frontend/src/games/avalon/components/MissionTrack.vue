<script setup lang="ts">
import { computed } from 'vue'
import { Check, X } from '@lucide/vue'
import type { MissionRecord } from '../types'

const props = defineProps<{
  currentMission: number
  history: MissionRecord[]
  playerCount: number
  replayableMissions?: number[]
}>()

const emit = defineEmits<{
  selectMission: [missionNumber: number]
}>()

const missionTeamSizes: Record<number, readonly number[]> = {
  5: [2, 3, 2, 3, 3],
  6: [2, 3, 4, 3, 4],
  7: [2, 3, 3, 4, 4],
  8: [3, 4, 4, 5, 5],
  9: [3, 4, 4, 5, 5],
  10: [3, 4, 4, 5, 5],
}

const missions = computed(() =>
  [1, 2, 3, 4, 5].map((number) => ({
    number,
    record: props.history.find((mission) => mission.number === number),
    teamSize: missionTeamSizes[props.playerCount]?.[number - 1] ?? 0,
    twoFails: props.playerCount >= 7 && number === 4,
    replayable: props.replayableMissions?.includes(number) ?? false,
  })),
)

function missionLabel(mission: (typeof missions.value)[number]): string {
  const outcome = mission.record
    ? mission.record.success
      ? '，任务成功'
      : '，任务失败'
    : ''
  const replay = mission.replayable ? '，点击查看本轮投票复盘' : ''
  return `第 ${mission.number} 轮，需要 ${mission.teamSize} 人${outcome}${replay}`
}
</script>

<template>
  <div class="mission-track" aria-label="任务进度">
    <button
      v-for="mission in missions"
      :key="mission.number"
      type="button"
      class="mission-node"
      :class="{
        success: mission.record?.success,
        failed: mission.record && !mission.record.success,
        current: !mission.record && mission.number === currentMission,
        replayable: mission.replayable,
      }"
      :disabled="!mission.replayable"
      :aria-label="missionLabel(mission)"
      @click="emit('selectMission', mission.number)"
    >
      <span class="mission-requirement">
        {{ mission.teamSize }}<small>人</small>
      </span>
      <span v-if="mission.record" class="mission-outcome" aria-hidden="true">
        <Check v-if="mission.record.success" :size="10" />
        <X v-else :size="10" />
      </span>
      <small v-if="mission.twoFails" class="mission-fail-note">双败</small>
    </button>
  </div>
</template>
