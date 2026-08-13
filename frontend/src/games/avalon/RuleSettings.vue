<script setup lang="ts">
import ModeGuide from '../../components/ModeGuide.vue'
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'
import { AVALON_COURT_GUIDE } from '../../gameModeGuides'

defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>

<template>
  <section class="rule-setting-group">
    <header><strong>玩法模式</strong><small>王庭暗流加入心怀异念之臣、黑誓授刃和最后议事</small></header>
    <div class="rule-option-grid">
      <button type="button" :class="{ active: modelValue.mode === 'standard' }" @click="emit('change', 'mode', 'standard')"><strong>标准阿瓦隆</strong><small>经典任务、湖中仙女与刺杀梅林</small></button>
      <button type="button" :class="{ active: modelValue.mode === 'court_undercurrent' }" @click="emit('change', 'mode', 'court_undercurrent')"><strong>王庭暗流</strong><small>心怀异念之臣可能被刺客授刃转化</small></button>
    </div>
  </section>
  <details v-if="modelValue.mode === 'court_undercurrent'" class="avalon-mode-guide-disclosure">
    <summary><span><strong>王庭暗流完整说明</strong><small>一分钟导读 · 完整规则 · 完整背景故事</small></span><b>展开 / 收起</b></summary>
    <ModeGuide :content="AVALON_COURT_GUIDE" />
  </details>
  <section v-if="modelValue.mode === 'court_undercurrent'" class="rule-setting-group">
    <header><strong>扩展包角色</strong><small>暗影梅林建立在王庭暗流完整规则之上</small></header>
    <div class="rule-toggle-list">
      <button type="button" :class="{ active: modelValue.shadowMerlinEnabled }" @click="emit('change', 'shadowMerlinEnabled', !modelValue.shadowMerlinEnabled)">
        <span><strong>暗影梅林</strong><small>六人及以上可用 · 替换一名忠臣 · 开启祓影议庭</small></span><b>{{ modelValue.shadowMerlinEnabled ? '开' : '关' }}</b>
      </button>
    </div>
  </section>
  <section class="rule-setting-group">
    <header><strong>对局规则</strong><small>王庭暗流固定关闭湖中仙女和提前刺杀</small></header>
    <div class="rule-toggle-list">
      <button type="button" :class="{ active: modelValue.listed }" @click="emit('change', 'listed', !modelValue.listed)"><span><strong>公开房间</strong><small>允许其他玩家在大厅房间列表中发现</small></span><b>{{ modelValue.listed ? '开' : '关' }}</b></button>
      <button type="button" :class="{ active: modelValue.ladyEnabled }" :disabled="modelValue.mode === 'court_undercurrent'" @click="emit('change', 'ladyEnabled', !modelValue.ladyEnabled)"><span><strong>湖中仙女</strong><small>从第 2 次任务后开始查验阵营</small></span><b>{{ modelValue.ladyEnabled ? '开' : '关' }}</b></button>
      <button type="button" :class="{ active: modelValue.earlyAssassinationEnabled }" :disabled="modelValue.mode === 'court_undercurrent'" @click="emit('change', 'earlyAssassinationEnabled', !modelValue.earlyAssassinationEnabled)"><span><strong>提前刺杀</strong><small>刺客可在任务期间豪赌梅林，刺错立即失败</small></span><b>{{ modelValue.earlyAssassinationEnabled ? '开' : '关' }}</b></button>
    </div>
  </section>
</template>
