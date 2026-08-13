<script setup lang="ts">
import { formatMatchDuration } from '../../game-platform/recordFormatting'
import type { MatchDetail } from '../../stats'

defineProps<{ match: MatchDetail }>()
</script>

<template>
  <div class="match-detail-section">
    <span>落块挑战成绩</span>
    <div class="match-mission-list">
      <div class="success">
        <strong>最终得分</strong>
        <span>{{ Number(match.details.state?.score ?? 0).toLocaleString() }} 分</span>
        <small>到达等级 {{ match.details.state?.level ?? 1 }}</small>
      </div>
      <div class="success">
        <strong>棋盘表现</strong>
        <span>消除 {{ match.details.state?.lines ?? 0 }} 行</span>
        <small>
          使用 {{ match.details.state?.pieces ?? 0 }} 个方块 ·
          {{ formatMatchDuration(match.details.state?.elapsed_ms) }}
        </small>
      </div>
    </div>
  </div>
</template>
