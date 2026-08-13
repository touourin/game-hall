<script setup lang="ts">
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'
defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>
<template>
  <section class="rule-setting-group">
    <header><strong>挑战模式</strong><small>限时模式到点自动结算；无限模式保留堆顶结束玩法</small></header>
    <div class="rule-option-grid">
      <button type="button" :class="{ active: modelValue.challengeMode === 'timed' }" @click="emit('change', 'challengeMode', 'timed')"><strong>限时挑战</strong><small>在固定时间内尽可能获得高分</small></button>
      <button type="button" :class="{ active: modelValue.challengeMode === 'endless' }" @click="emit('change', 'challengeMode', 'endless')"><strong>无限挑战</strong><small>持续游玩，直到方块堆到顶部</small></button>
    </div>
  </section>
  <section v-if="modelValue.challengeMode === 'timed'" class="rule-setting-group">
    <header><strong>挑战时长</strong><small>不同时间档位分别记录排行榜</small></header>
    <div class="rule-segmented three"><button v-for="seconds in [60, 180, 300]" :key="seconds" type="button" :class="{ active: modelValue.durationSeconds === seconds }" @click="emit('change', 'durationSeconds', seconds)">{{ seconds / 60 }} 分钟</button></div>
  </section>
</template>
