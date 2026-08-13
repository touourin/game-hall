<script setup lang="ts">
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'
defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>
<template>
  <section class="rule-setting-group">
    <header><strong>挑战难度</strong><small>三种经典规格分别记录成绩和排行榜</small></header>
    <div class="rule-option-grid three">
      <button type="button" :class="{ active: modelValue.difficulty === 'beginner' }" @click="emit('change', 'difficulty', 'beginner')"><strong>初级</strong><small>9×9 · 10 雷</small></button>
      <button type="button" :class="{ active: modelValue.difficulty === 'intermediate' }" @click="emit('change', 'difficulty', 'intermediate')"><strong>中级</strong><small>16×16 · 40 雷</small></button>
      <button type="button" :class="{ active: modelValue.difficulty === 'expert' }" @click="emit('change', 'difficulty', 'expert')"><strong>高级</strong><small>16×30 · 99 雷</small></button>
    </div>
  </section>
</template>
