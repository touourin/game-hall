<script setup lang="ts">
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'
defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>
<template>
  <section class="rule-setting-group">
    <header><strong>挑战层数</strong><small>层数越高，理论最少步数呈指数增长</small></header>
    <div class="rule-segmented six">
      <button v-for="count in [3, 4, 5, 6, 7, 8]" :key="count" type="button" :class="{ active: modelValue.discCount === count }" @click="emit('change', 'discCount', count)">{{ count }} 层<br><small>{{ 2 ** count - 1 }} 步</small></button>
    </div>
  </section>
</template>
