<script setup lang="ts">
import type { MatchDetail } from '../../stats'

defineProps<{ match: MatchDetail }>()

function alignmentLabel(role: string | undefined): string {
  const labels: Record<string, string> = {
    'dark-red': '暗军旗·红方',
    'dark-blue': '暗军旗·蓝方',
    'flip-red': '翻棋军旗·红方',
    'flip-blue': '翻棋军旗·蓝方',
  }
  return role ? labels[role] ?? role : ''
}
</script>

<template>
  <div class="match-detail-section">
    <span>参赛玩家</span>
    <div class="match-player-list">
      <div v-for="player in match.details.players" :key="player.id">
        <b>{{ player.seat + 1 }}号</b>
        <strong>{{ player.name }}</strong>
        <em :class="player.alignment">{{ alignmentLabel(player.role) }}</em>
      </div>
    </div>
  </div>
</template>
