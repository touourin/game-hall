<script setup lang="ts">
import { computed } from 'vue'
import type { ArcadeGameKey } from '../types/arcade'
import { builtinGameDefinition } from '../game-platform/registry'
import {
  applyGameRuleChange,
  hasGameHandicap,
  withDefaultGameRules,
} from '../gameRules'

const props = defineProps<{
  gameKey: ArcadeGameKey
  modelValue: Record<string, unknown>
  guestMode?: boolean
}>()
const emit = defineEmits<{
  'update:modelValue': [value: Record<string, unknown>]
}>()

const builtinGame = computed(() => builtinGameDefinition(props.gameKey))
const resolvedOptions = computed(() => withDefaultGameRules(
  props.gameKey,
  props.modelValue,
))
const gameSettingsComponent = computed(
  () => builtinGame.value?.rules.settingsComponent ?? null,
)
const gameSettingsGroups = computed(
  () => (builtinGame.value?.rules.settingsGroups ?? []).filter((group) => (
    !group.visibleWhen
    || resolvedOptions.value[group.visibleWhen[0]] === group.visibleWhen[1]
  )),
)
const firstPlayerCopy = computed(() => (
  builtinGame.value?.rules.firstPlayerCopy?.(resolvedOptions.value) ?? {
    title: '首局先手',
    description: '再来一局时仍会自动轮换',
    randomDescription: '开局随机分配座位',
    hostDescription: '房主在首局获得先手',
  }
))

function option(key: string): unknown {
  return resolvedOptions.value[key]
}

function setOption(key: string, value: unknown) {
  emit(
    'update:modelValue',
    applyGameRuleChange(props.gameKey, props.modelValue, key, value),
  )
}

function hasHandicap(): boolean {
  return hasGameHandicap(props.gameKey, resolvedOptions.value)
}

function supportsUndo(): boolean {
  return builtinGame.value?.capabilities.undo ?? false
}

function supportsDraw(): boolean {
  return builtinGame.value?.capabilities.draw ?? false
}

function supportsFirstPlayer(): boolean {
  return builtinGame.value?.capabilities.firstPlayer ?? true
}

function supportsGuests(): boolean {
  return builtinGame.value?.capabilities.guests ?? true
}

function supportsSpectators(): boolean {
  return builtinGame.value?.capabilities.spectators ?? true
}
</script>

<template>
  <div class="game-rule-settings">
    <section v-for="group in gameSettingsGroups" :key="group.key" class="rule-setting-group">
      <header><strong>{{ group.title }}</strong><small>{{ group.description }}</small></header>
      <div v-if="group.control === 'cards'" class="rule-option-grid" :class="{ three: group.columns === 3 }">
        <button
          v-for="[value, label, description] in group.options"
          :key="String(value)"
          type="button"
          :class="{ active: option(group.key) === value }"
          @click="setOption(group.key, value)"
        >
          <strong>{{ label }}</strong><small v-if="description">{{ description }}</small>
        </button>
      </div>
      <div v-else class="rule-segmented" :class="{ three: group.columns === 3, five: group.columns === 5, six: group.columns === 6 }">
        <button
          v-for="[value, label, description] in group.options"
          :key="String(value)"
          type="button"
          :class="{ active: option(group.key) === value }"
          @click="setOption(group.key, value)"
        >
          {{ label }}<br v-if="description"><small v-if="description">{{ description }}</small>
        </button>
      </div>
    </section>

    <component
      :is="gameSettingsComponent"
      v-if="gameSettingsComponent"
      :model-value="resolvedOptions"
      @change="setOption"
    />

    <section v-if="supportsFirstPlayer() && !hasHandicap()" class="rule-setting-group">
      <header>
        <strong>{{ firstPlayerCopy.title }}</strong>
        <small>{{ firstPlayerCopy.description }}</small>
      </header>
      <div class="rule-option-grid">
        <button type="button" :class="{ active: option('firstPlayer') === 'random' }" @click="setOption('firstPlayer', 'random')">
          <strong>随机</strong><small>{{ firstPlayerCopy.randomDescription }}</small>
        </button>
        <button type="button" :class="{ active: option('firstPlayer') === 'host' }" @click="setOption('firstPlayer', 'host')">
          <strong>房主</strong><small>{{ firstPlayerCopy.hostDescription }}</small>
        </button>
      </div>
    </section>

    <section v-if="supportsUndo() || supportsDraw()" class="rule-setting-group">
      <header><strong>对局协商</strong><small>真人对局需对手确认；AI 会自动同意悔棋</small></header>
      <div class="rule-toggle-list">
        <button v-if="supportsUndo()" type="button" :class="{ active: option('allowUndo') }" @click="setOption('allowUndo', !option('allowUndo'))">
          <span><strong>允许悔棋</strong><small>真人撤回一步；人机局撤回玩家上一步及 AI 回应</small></span><b>{{ option('allowUndo') ? '开' : '关' }}</b>
        </button>
        <button v-if="supportsDraw()" type="button" :class="{ active: option('allowDraw') }" @click="setOption('allowDraw', !option('allowDraw'))">
          <span><strong>允许和棋</strong><small>可以向对手发起和棋申请</small></span><b>{{ option('allowDraw') ? '开' : '关' }}</b>
        </button>
      </div>
    </section>

    <section v-if="supportsGuests()" class="rule-setting-group guest-access-rules">
      <header><strong>游客准入</strong><small>包含游客的整局不会写入任何玩家的个人战绩或排行榜</small></header>
      <div class="rule-option-grid">
        <button type="button" :class="{ active: option('allowGuests') }" @click="setOption('allowGuests', true)">
          <strong>允许游客</strong><small>游客可以加入；有人以游客身份开局后自动成为休闲局</small>
        </button>
        <button type="button" :class="{ active: !option('allowGuests') }" :disabled="guestMode" @click="setOption('allowGuests', false)">
          <strong>仅登录玩家</strong><small>{{ guestMode ? '游客只能创建允许游客加入的休闲房间' : '拒绝游客加入，正常记录战绩' }}</small>
        </button>
      </div>
    </section>

    <section v-if="supportsSpectators()" class="rule-setting-group spectator-access-rules">
      <header><strong>第一人称观战</strong><small>观众固定观看一名玩家，只能看到该玩家当时可见的内容</small></header>
      <div class="rule-option-grid">
        <button type="button" :class="{ active: option('allowSpectators') }" @click="setOption('allowSpectators', true)">
          <strong>允许观战</strong><small>对局开始后，观众可以选择并固定一个玩家视角</small>
        </button>
        <button type="button" :class="{ active: !option('allowSpectators') }" @click="setOption('allowSpectators', false)">
          <strong>关闭观战</strong><small>本房间不会出现在进行中的观战列表</small>
        </button>
      </div>
    </section>
  </div>
</template>

<style src="./gameRuleSettings.css"></style>
