<script setup lang="ts">
import type { MatchDetail } from '../../stats'

defineProps<{ match: MatchDetail }>()
</script>

<template>
  <div class="match-detail-section">
    <span>反应挑战成绩</span>
    <div class="match-mission-list">
      <div
        v-for="(result, index) in match.details.state?.results_ms ?? []"
        :key="index"
        class="success"
      >
        <strong>第 {{ index + 1 }} 轮</strong>
        <span>{{ result }} ms</span>
      </div>
    </div>
  </div>
</template>
