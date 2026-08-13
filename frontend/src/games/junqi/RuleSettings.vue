<script setup lang="ts">
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'
defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>
<template>
  <section class="rule-setting-group">
    <header><strong>军旗玩法</strong><small>选择完整暗棋或轻量翻棋</small></header>
    <div class="rule-option-grid">
      <button type="button" :class="{ active: modelValue.mode === 'dark' }" @click="emit('change', 'mode', 'dark')"><strong>暗军旗</strong><small>双方秘密布阵后行棋</small></button>
      <button type="button" :class="{ active: modelValue.mode === 'flip' }" @click="emit('change', 'mode', 'flip')"><strong>翻棋军旗</strong><small>随机扣棋，首翻确定阵营</small></button>
    </div>
  </section>
</template>
