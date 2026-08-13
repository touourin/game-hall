<script setup lang="ts">
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'
defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>
<template>
  <section class="rule-setting-group">
    <header><strong>起始资金</strong><small>资金越少，前期买地取舍越明显</small></header>
    <div class="rule-segmented three"><button v-for="cash in [6000, 8000, 10000]" :key="cash" type="button" :class="{ active: modelValue.startingCash === cash }" @click="emit('change', 'startingCash', cash)">{{ cash }}</button></div>
  </section>
  <section class="rule-setting-group">
    <header><strong>比赛回合</strong><small>达到上限时按现金、地产与升级总值排名</small></header>
    <div class="rule-segmented three"><button v-for="rounds in [12, 20, 30]" :key="rounds" type="button" :class="{ active: modelValue.maxRounds === rounds }" @click="emit('change', 'maxRounds', rounds)">{{ rounds }} 回合</button></div>
  </section>
</template>
