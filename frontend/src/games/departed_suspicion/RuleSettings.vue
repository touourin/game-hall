<script setup lang="ts">
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'
defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>
<template>
  <section class="rule-setting-group">
    <header><strong>装备牌库</strong><small>卧底扩展依赖完整掩护系统，因此不混入普通身份局</small></header>
    <div class="rule-option-grid">
      <button type="button" :class="{ active: modelValue.equipmentSet === 'bombers' }" @click="emit('change', 'equipmentSet', 'bombers')"><strong>炸弹客/叛徒装备</strong><small>基础16张加该扩展5张，共21张</small></button>
      <button type="button" :class="{ active: modelValue.equipmentSet === 'base' }" @click="emit('change', 'equipmentSet', 'base')"><strong>基础装备</strong><small>只使用经典16张，适合第一次教学</small></button>
    </div>
  </section>
</template>
