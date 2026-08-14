<script setup lang="ts">
import type { MatchDetail } from '../stats'

defineProps<{
  match: MatchDetail
  roleLabel?: (role: string) => string
}>()
</script>

<template>
  <div class="match-detail-section">
    <span>参赛玩家</span>
    <div class="match-player-list">
      <div v-for="player in match.details.players" :key="player.id">
        <b>{{ player.seat + 1 }}号</b>
        <strong>{{ player.name }}</strong>
        <em v-if="player.role && roleLabel" :class="player.alignment">
          {{ roleLabel(player.role) }}
        </em>
      </div>
    </div>
  </div>
</template>
