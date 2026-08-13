<script setup lang="ts">
import type { BuiltinGameRuleSettingsEmits, BuiltinGameRuleSettingsProps } from '../../game-platform/types'
defineProps<BuiltinGameRuleSettingsProps>()
const emit = defineEmits<BuiltinGameRuleSettingsEmits>()
</script>
<template>
  <section class="rule-setting-group">
    <header><strong>角色组合</strong><small>所有组合都包含玩家人数加三张牌；多皮者留待后续扩展</small></header>
    <div class="rule-option-grid three">
      <button type="button" :class="{ active: modelValue.rolePreset === 'beginner' }" @click="emit('change', 'rolePreset', 'beginner')"><strong>初见月夜</strong><small>核心换牌角色，适合第一次教学</small></button>
      <button type="button" :class="{ active: modelValue.rolePreset === 'standard' }" @click="emit('change', 'rolePreset', 'standard')"><strong>标准疑云</strong><small>加入爪牙与皮匠，阵营判断更丰富</small></button>
      <button type="button" :class="{ active: modelValue.rolePreset === 'chaos' }" @click="emit('change', 'rolePreset', 'chaos')"><strong>混沌之夜</strong><small>高人数加入守夜人，信息交叉更多</small></button>
    </div>
  </section>
  <section class="rule-setting-group">
    <header><strong>房间发现</strong><small>进行中固定关闭观战，避免第一人称视角泄露私密身份</small></header>
    <div class="rule-option-grid">
      <button type="button" :class="{ active: modelValue.listed }" @click="emit('change', 'listed', true)"><strong>公开房间</strong><small>等待阶段可以在大厅中被发现</small></button>
      <button type="button" :class="{ active: !modelValue.listed }" @click="emit('change', 'listed', false)"><strong>私密房间</strong><small>只有拿到房间码或邀请链接的玩家可加入</small></button>
    </div>
  </section>
</template>
