<script setup lang="ts">
import { formatMatchDuration } from '../../game-platform/recordFormatting'
import type { MatchDetail } from '../../stats'

defineProps<{ match: MatchDetail }>()
</script>

<template>
  <div class="match-detail-section">
    <span>汉诺塔挑战成绩</span>
    <div class="match-mission-list">
      <div class="success">
        <strong>{{ match.details.state?.disc_count }} 层圆盘</strong>
        <span>{{ match.details.state?.moves }} 步完成</span>
        <small>理论最少 {{ 2 ** Number(match.details.state?.disc_count ?? 0) - 1 }} 步</small>
      </div>
      <div class="success">
        <strong>完成用时</strong>
        <span>{{ formatMatchDuration(match.details.state?.elapsed_ms) }}</span>
      </div>
    </div>
  </div>
</template>
