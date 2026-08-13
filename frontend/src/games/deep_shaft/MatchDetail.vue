<script setup lang="ts">
import { formatMatchDuration } from '../../game-platform/recordFormatting'
import type { MatchDetail } from '../../stats'

defineProps<{ match: MatchDetail }>()
</script>

<template>
  <div class="match-detail-section">
    <span>百层深井挑战成绩</span>
    <div class="match-mission-list">
      <div :class="match.winner === 'completed' ? 'success' : 'failed'">
        <strong>
          {{ match.winner === 'completed'
            ? '抵达第一百层'
            : `最深抵达第 ${match.details.state?.deepest_floor ?? 0} 层` }}
        </strong>
        <span>{{ formatMatchDuration(match.details.state?.elapsed_ms) }}</span>
        <small>结束时剩余 {{ match.details.state?.health ?? 0 }} 点生命</small>
      </div>
      <div class="success">
        <strong>服务端轨迹校验</strong>
        <span>{{ match.details.state?.input_count ?? 0 }} 帧输入</span>
        <small>固定 60 Hz 重建平台、移动与碰撞</small>
      </div>
    </div>
  </div>
</template>
