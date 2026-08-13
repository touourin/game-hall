<script setup lang="ts">
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'

defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>

<template>
  <section class="rule-setting-group">
    <header><strong>玩法模式</strong><small>有禁手连珠中，黑方首手天元并受禁手限制</small></header>
    <div class="rule-option-grid three">
      <button type="button" :class="{ active: modelValue.winRule === 'freestyle' }" @click="emit('change', 'winRule', 'freestyle')"><strong>自由五子</strong><small>双方五颗或更多即获胜</small></button>
      <button type="button" :class="{ active: modelValue.winRule === 'exact_five' }" @click="emit('change', 'winRule', 'exact_five')"><strong>正好五子</strong><small>长连不算获胜</small></button>
      <button type="button" :class="{ active: modelValue.winRule === 'renju' }" @click="emit('change', 'winRule', 'renju')"><strong>有禁手连珠</strong><small>黑方禁三三、四四和长连</small></button>
    </div>
  </section>
  <section class="rule-setting-group">
    <header><strong>开局规则</strong><small>Swap2 通过摆子和交换选色降低先手优势</small></header>
    <div class="rule-option-grid">
      <button type="button" :class="{ active: modelValue.openingRule === 'swap2' }" :disabled="modelValue.winRule === 'renju'" @click="emit('change', 'openingRule', 'swap2')"><strong>Swap2 公平开局</strong><small>{{ modelValue.winRule === 'renju' ? '有禁手连珠不适用 Swap2' : '两黑一白后由对手选色或再摆两子' }}</small></button>
      <button type="button" :class="{ active: modelValue.openingRule === 'standard' }" @click="emit('change', 'openingRule', 'standard')"><strong>标准开局</strong><small>执黑玩家直接先行</small></button>
    </div>
  </section>
</template>
