<script setup lang="ts">
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'
defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>
<template>
  <section class="rule-setting-group">
    <header><strong>斗地主玩法</strong><small>三种玩法共用叫地主、抢地主与倍数结算</small></header>
    <div class="rule-option-grid three">
      <button type="button" :class="{ active: modelValue.variant === 'classic' }" @click="emit('change', 'variant', 'classic')"><strong>经典</strong><small>标准54张牌</small></button>
      <button type="button" :class="{ active: modelValue.variant === 'laizi' }" @click="emit('change', 'variant', 'laizi')"><strong>癞子</strong><small>随机点数充当万能牌</small></button>
      <button type="button" :class="{ active: modelValue.variant === 'no_shuffle' }" @click="emit('change', 'variant', 'no_shuffle')"><strong>不洗牌</strong><small>再来一局保留收牌顺序</small></button>
    </div>
  </section>
</template>
