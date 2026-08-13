<script setup lang="ts">
import { formatMatchDuration } from '../../game-platform/recordFormatting'
import type { MatchDetail } from '../../stats'

defineProps<{ match: MatchDetail }>()
</script>

<template>
  <div class="match-detail-section">
    <span>三秒弹幕挑战</span>
    <div class="match-mission-list">
      <div :class="match.winner === 'survived' ? 'success' : 'failed'">
        <strong>{{ match.winner === 'survived' ? '完整生还' : '弹幕命中' }}</strong>
        <span>{{ formatMatchDuration(match.details.state?.elapsed_ms) }}</span>
        <small>目标 3.00 秒 · 60 Hz 轨迹重放</small>
      </div>
      <div class="success">
        <strong>服务端校验</strong>
        <span>{{ match.details.state?.input_count ?? 0 }} 帧输入</span>
        <small>使用相同种子重建弹幕与碰撞位置</small>
      </div>
    </div>
  </div>
</template>
