<script setup lang="ts">
import { formatMatchDuration } from '../../game-platform/recordFormatting'
import type { MatchDetail } from '../../stats'

defineProps<{ match: MatchDetail }>()
</script>

<template>
  <div class="match-detail-section">
    <span>舒尔特挑战成绩</span>
    <div class="match-mission-list">
      <div class="success">
        <strong>5×5 标准方格</strong>
        <span>{{ formatMatchDuration(match.details.state?.elapsed_ms) }}</span>
        <small>按顺序完成 1–25</small>
      </div>
      <div class="success">
        <strong>点击准确率</strong>
        <span>{{ Math.round(25 / (25 + Number(match.details.state?.mistakes ?? 0)) * 100) }}%</span>
        <small>{{ match.details.state?.mistakes ?? 0 }} 次错误点击</small>
      </div>
    </div>
  </div>
</template>
