<script setup lang="ts">
import type { MatchDetail } from '../stats'

defineProps<{ match: MatchDetail }>()
</script>

<template>
  <div class="match-detail-section">
    <span>参赛玩家</span>
    <div class="match-player-list">
      <div v-for="player in match.details.players" :key="player.id">
        <b>{{ player.seat + 1 }}号</b>
        <strong>{{ player.name }}</strong>
      </div>
    </div>
  </div>
</template>
