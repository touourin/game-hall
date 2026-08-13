<script setup lang="ts">
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'
import { XIANGQI_HANDICAP_OPTIONS } from './rules'

defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>

<template>
  <section class="rule-setting-group">
    <header><strong>让子规则</strong><small>让子方固定执红并先走；让九子移除五兵、双仕、双相</small></header>
    <div class="rule-segmented five">
      <button v-for="item in XIANGQI_HANDICAP_OPTIONS" :key="item.value" type="button" :class="{ active: modelValue.handicap === item.value }" @click="emit('change', 'handicap', item.value)">{{ item.label }}</button>
    </div>
  </section>
  <section v-if="modelValue.handicap !== 'none'" class="rule-setting-group">
    <header><strong>让子方</strong><small>按玩家身份固定，再来一局不会因座位轮换而改变</small></header>
    <div class="rule-option-grid">
      <button type="button" :class="{ active: modelValue.handicapGiver === 'host' }" @click="emit('change', 'handicapGiver', 'host')"><strong>房主让子</strong><small>房主作为让子方</small></button>
      <button type="button" :class="{ active: modelValue.handicapGiver === 'opponent' }" @click="emit('change', 'handicapGiver', 'opponent')"><strong>对手让子</strong><small>加入房间的玩家或 AI 作为让子方</small></button>
    </div>
  </section>
  <section class="rule-setting-group">
    <header><strong>辅助提示</strong><small>双方使用同一设置，不改变象棋走子规则</small></header>
    <div class="rule-toggle-list">
      <button type="button" :class="{ active: modelValue.captureHintsEnabled }" @click="emit('change', 'captureHintsEnabled', !modelValue.captureHintsEnabled)">
        <span><strong>吃子提醒</strong><small>轮到玩家时标出当前可以吃到的敌子</small></span><b>{{ modelValue.captureHintsEnabled ? '开' : '关' }}</b>
      </button>
    </div>
  </section>
</template>
