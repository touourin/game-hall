<script setup lang="ts">
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'
defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>
<template>
  <section class="rule-setting-group">
    <header><strong>起始筹码</strong><small>开桌时发放，后续手牌持续继承，不涉及真实货币</small></header>
    <div class="rule-segmented three"><button v-for="chips in [500, 1000, 2000]" :key="chips" type="button" :class="{ active: modelValue.startingChips === chips }" @click="emit('change', 'startingChips', chips)">{{ chips }}</button></div>
  </section>
  <section class="rule-setting-group">
    <header><strong>大小盲注</strong><small>大盲始终是小盲的两倍</small></header>
    <div class="rule-segmented three"><button v-for="blind in [5, 10, 20]" :key="blind" type="button" :class="{ active: modelValue.smallBlind === blind }" @click="emit('change', 'smallBlind', blind)">{{ blind }}/{{ blind * 2 }}</button></div>
  </section>
</template>
