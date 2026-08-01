<script setup lang="ts">
import type { ArcadeGameKey } from '../types/arcade'
import { withDefaultGameRules } from '../gameRules'

const props = defineProps<{
  gameKey: ArcadeGameKey
  modelValue: Record<string, unknown>
}>()
const emit = defineEmits<{
  'update:modelValue': [value: Record<string, unknown>]
}>()

function option(key: string): unknown {
  return withDefaultGameRules(props.gameKey, props.modelValue)[key]
}

function setOption(key: string, value: unknown) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}
</script>

<template>
  <div class="game-rule-settings">
    <section v-if="gameKey === 'junqi'" class="rule-setting-group">
      <header><strong>军旗玩法</strong><small>选择完整暗棋或轻量翻棋</small></header>
      <div class="rule-option-grid">
        <button type="button" :class="{ active: option('mode') === 'dark' }" @click="setOption('mode', 'dark')">
          <strong>暗军旗</strong><small>双方秘密布阵后行棋</small>
        </button>
        <button type="button" :class="{ active: option('mode') === 'flip' }" @click="setOption('mode', 'flip')">
          <strong>翻棋军旗</strong><small>随机扣棋，首翻确定阵营</small>
        </button>
      </div>
    </section>

    <section v-if="gameKey === 'gomoku'" class="rule-setting-group">
      <header><strong>玩法模式</strong><small>有禁手连珠中，黑方首手天元并受禁手限制</small></header>
      <div class="rule-option-grid three">
        <button type="button" :class="{ active: option('winRule') === 'freestyle' }" @click="setOption('winRule', 'freestyle')">
          <strong>自由五子</strong><small>双方五颗或更多即获胜</small>
        </button>
        <button type="button" :class="{ active: option('winRule') === 'exact_five' }" @click="setOption('winRule', 'exact_five')">
          <strong>正好五子</strong><small>长连不算获胜</small>
        </button>
        <button type="button" :class="{ active: option('winRule') === 'renju' }" @click="setOption('winRule', 'renju')">
          <strong>有禁手连珠</strong><small>黑方禁三三、四四和长连</small>
        </button>
      </div>
    </section>

    <section v-if="gameKey === 'gomoku'" class="rule-setting-group">
      <header><strong>开局规则</strong><small>Swap2 通过摆子和交换选色降低先手优势</small></header>
      <div class="rule-option-grid">
        <button type="button" :class="{ active: option('openingRule') === 'swap2' }" @click="setOption('openingRule', 'swap2')">
          <strong>Swap2 公平开局</strong><small>两黑一白后由对手选色或再摆两子</small>
        </button>
        <button type="button" :class="{ active: option('openingRule') === 'standard' }" @click="setOption('openingRule', 'standard')">
          <strong>标准开局</strong><small>执黑玩家直接先行</small>
        </button>
      </div>
    </section>

    <section v-if="gameKey === 'go'" class="rule-setting-group">
      <header><strong>棋盘大小</strong><small>小棋盘适合快速对局</small></header>
      <div class="rule-segmented three">
        <button v-for="size in [9, 13, 19]" :key="size" type="button" :class="{ active: option('boardSize') === size }" @click="setOption('boardSize', size)">{{ size }} 路</button>
      </div>
    </section>

    <section v-if="gameKey === 'doudizhu'" class="rule-setting-group">
      <header><strong>斗地主玩法</strong><small>三种玩法共用叫地主、抢地主与倍数结算</small></header>
      <div class="rule-option-grid three">
        <button type="button" :class="{ active: option('variant') === 'classic' }" @click="setOption('variant', 'classic')">
          <strong>经典</strong><small>标准54张牌</small>
        </button>
        <button type="button" :class="{ active: option('variant') === 'laizi' }" @click="setOption('variant', 'laizi')">
          <strong>癞子</strong><small>随机点数充当万能牌</small>
        </button>
        <button type="button" :class="{ active: option('variant') === 'no_shuffle' }" @click="setOption('variant', 'no_shuffle')">
          <strong>不洗牌</strong><small>再来一局保留收牌顺序</small>
        </button>
      </div>
    </section>

    <section v-if="gameKey === 'go'" class="rule-setting-group">
      <header><strong>贴目</strong><small>终局数子时计入白方</small></header>
      <div class="rule-segmented three">
        <button v-for="komi in [0, 6.5, 7.5]" :key="komi" type="button" :class="{ active: option('komi') === komi }" @click="setOption('komi', komi)">{{ komi }}</button>
      </div>
    </section>

    <section v-if="gameKey !== 'reaction'" class="rule-setting-group">
      <header><strong>{{ gameKey === 'doudizhu' ? '首叫玩家' : gameKey === 'gomoku' && option('openingRule') === 'swap2' ? '首局摆子者' : '首局先手' }}</strong><small>再来一局时仍会自动轮换</small></header>
      <div class="rule-option-grid">
        <button type="button" :class="{ active: option('firstPlayer') === 'random' }" @click="setOption('firstPlayer', 'random')">
          <strong>随机</strong><small>{{ gameKey === 'doudizhu' ? '随机指定首叫玩家' : gameKey === 'gomoku' && option('openingRule') === 'swap2' ? '随机指定首位摆子者' : '开局随机分配座位' }}</small>
        </button>
        <button type="button" :class="{ active: option('firstPlayer') === 'host' }" @click="setOption('firstPlayer', 'host')">
          <strong>房主</strong><small>{{ gameKey === 'doudizhu' ? '房主在首局首先叫地主' : gameKey === 'gomoku' && option('openingRule') === 'swap2' ? '房主负责首先摆两黑一白' : '房主在首局获得先手' }}</small>
        </button>
      </div>
    </section>

    <section v-if="gameKey === 'gomoku'" class="rule-setting-group">
      <header><strong>棋钟</strong><small>每位玩家独立计时，用时耗尽自动判负</small></header>
      <div class="rule-segmented four">
        <button type="button" :class="{ active: option('timeLimitSeconds') === 0 }" @click="setOption('timeLimitSeconds', 0)">不计时</button>
        <button type="button" :class="{ active: option('timeLimitSeconds') === 180 }" @click="setOption('timeLimitSeconds', 180)">3 分钟</button>
        <button type="button" :class="{ active: option('timeLimitSeconds') === 300 }" @click="setOption('timeLimitSeconds', 300)">5 分钟</button>
        <button type="button" :class="{ active: option('timeLimitSeconds') === 600 }" @click="setOption('timeLimitSeconds', 600)">10 分钟</button>
      </div>
    </section>

    <section v-if="['gomoku', 'xiangqi', 'go'].includes(gameKey)" class="rule-setting-group">
      <header><strong>对局协商</strong><small>申请仍需对手确认</small></header>
      <div class="rule-toggle-list">
        <button type="button" :class="{ active: option('allowUndo') }" @click="setOption('allowUndo', !option('allowUndo'))">
          <span><strong>允许悔棋</strong><small>可以向对手申请撤回一步</small></span><b>{{ option('allowUndo') ? '开' : '关' }}</b>
        </button>
        <button type="button" :class="{ active: option('allowDraw') }" @click="setOption('allowDraw', !option('allowDraw'))">
          <span><strong>允许和棋</strong><small>可以向对手发起和棋申请</small></span><b>{{ option('allowDraw') ? '开' : '关' }}</b>
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.game-rule-settings { display: grid; gap: 20px; }
.rule-setting-group { display: grid; gap: 9px; }
.rule-setting-group > header { display: grid; gap: 2px; }
.rule-setting-group > header small { color: var(--muted); line-height: 1.4; }
.rule-option-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.rule-option-grid.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.rule-option-grid button { min-height: 68px; display: grid; align-content: center; gap: 3px; border: 1px solid var(--line); border-radius: 12px; padding: 11px 12px; color: var(--text); background: rgba(0, 0, 0, .12); text-align: left; }
.rule-option-grid small { color: var(--muted); line-height: 1.35; }
.rule-option-grid button.active, .rule-segmented button.active { border-color: color-mix(in srgb, var(--gold) 65%, var(--line)); background: color-mix(in srgb, var(--gold) 10%, transparent); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--gold) 18%, transparent); }
.rule-segmented { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
.rule-segmented.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.rule-segmented.four { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.rule-segmented button { min-height: 42px; border: 0; border-right: 1px solid var(--line); color: var(--muted); background: rgba(0, 0, 0, .12); font-weight: 850; }
.rule-segmented button:last-child { border-right: 0; }
.rule-segmented button.active { color: var(--gold); }
.rule-toggle-list { display: grid; gap: 8px; }
.rule-toggle-list button { min-height: 58px; display: flex; align-items: center; justify-content: space-between; gap: 12px; border: 1px solid var(--line); border-radius: 12px; padding: 9px 12px; color: var(--text); background: rgba(0, 0, 0, .12); text-align: left; }
.rule-toggle-list span { display: grid; gap: 2px; }
.rule-toggle-list small { color: var(--muted); }
.rule-toggle-list b { min-width: 38px; border-radius: 999px; padding: 5px 8px; color: var(--muted); background: rgba(255, 255, 255, .06); text-align: center; }
.rule-toggle-list button.active b { color: #15211c; background: var(--gold); }
@media (max-width: 520px) {
  .rule-option-grid, .rule-option-grid.three { grid-template-columns: 1fr; }
  .rule-segmented.four { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .rule-segmented.four button:nth-child(2) { border-right: 0; }
  .rule-segmented.four button:nth-child(-n + 2) { border-bottom: 1px solid var(--line); }
}
</style>
