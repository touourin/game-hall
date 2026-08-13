<script setup lang="ts">
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'
import { GO_HANDICAP_OPTIONS } from './rules'

defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>

<template>
  <section class="rule-setting-group">
    <header><strong>棋盘大小</strong><small>小棋盘适合快速对局</small></header>
    <div class="rule-segmented three"><button v-for="size in [9, 13, 19]" :key="size" type="button" :class="{ active: modelValue.boardSize === size }" @click="emit('change', 'boardSize', size)">{{ size }} 路</button></div>
  </section>
  <section class="rule-setting-group">
    <header><strong>让子规则</strong><small>仅限 19 路；让子方执黑先走，贴目固定为 0</small></header>
    <div class="rule-segmented five"><button v-for="count in GO_HANDICAP_OPTIONS" :key="count" type="button" :class="{ active: modelValue.handicap === count }" @click="emit('change', 'handicap', count)">{{ count ? `让 ${count} 子` : '不让子' }}</button></div>
  </section>
  <section v-if="Number(modelValue.handicap) > 0" class="rule-setting-group">
    <header><strong>让子方</strong><small>按玩家身份固定，再来一局不会因座位轮换而改变</small></header>
    <div class="rule-option-grid">
      <button type="button" :class="{ active: modelValue.handicapGiver === 'host' }" @click="emit('change', 'handicapGiver', 'host')"><strong>房主让子</strong><small>房主作为让子方</small></button>
      <button type="button" :class="{ active: modelValue.handicapGiver === 'opponent' }" @click="emit('change', 'handicapGiver', 'opponent')"><strong>对手让子</strong><small>加入房间的玩家或 AI 作为让子方</small></button>
    </div>
  </section>
  <section class="rule-setting-group">
    <header><strong>贴目</strong><small>终局数子时计入白方</small></header>
    <div class="rule-segmented three"><button v-for="komi in [0, 6.5, 7.5]" :key="komi" type="button" :disabled="Number(modelValue.handicap) > 0" :class="{ active: modelValue.komi === komi }" @click="emit('change', 'komi', komi)">{{ komi }}</button></div>
  </section>
</template>
