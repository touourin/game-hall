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
  const nextValue = { ...props.modelValue, [key]: value }
  if (props.gameKey === 'gomoku' && key === 'winRule' && value === 'renju') {
    nextValue.openingRule = 'standard'
  }
  emit('update:modelValue', nextValue)
}
</script>

<template>
  <div class="game-rule-settings">
    <section v-if="gameKey === 'minesweeper'" class="rule-setting-group">
      <header><strong>挑战难度</strong><small>三种经典规格分别记录成绩和排行榜</small></header>
      <div class="rule-option-grid three">
        <button type="button" :class="{ active: option('difficulty') === 'beginner' }" @click="setOption('difficulty', 'beginner')">
          <strong>初级</strong><small>9×9 · 10 雷</small>
        </button>
        <button type="button" :class="{ active: option('difficulty') === 'intermediate' }" @click="setOption('difficulty', 'intermediate')">
          <strong>中级</strong><small>16×16 · 40 雷</small>
        </button>
        <button type="button" :class="{ active: option('difficulty') === 'expert' }" @click="setOption('difficulty', 'expert')">
          <strong>高级</strong><small>16×30 · 99 雷</small>
        </button>
      </div>
    </section>

    <section v-if="gameKey === 'hanoi'" class="rule-setting-group">
      <header><strong>挑战层数</strong><small>层数越高，理论最少步数呈指数增长</small></header>
      <div class="rule-segmented six">
        <button
          v-for="count in [3, 4, 5, 6, 7, 8]"
          :key="count"
          type="button"
          :class="{ active: option('discCount') === count }"
          @click="setOption('discCount', count)"
        >
          {{ count }} 层<br><small>{{ 2 ** count - 1 }} 步</small>
        </button>
      </div>
    </section>

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
        <button
          type="button"
          :class="{ active: option('openingRule') === 'swap2' }"
          :disabled="option('winRule') === 'renju'"
          @click="setOption('openingRule', 'swap2')"
        >
          <strong>Swap2 公平开局</strong><small>{{ option('winRule') === 'renju' ? '有禁手连珠不适用 Swap2' : '两黑一白后由对手选色或再摆两子' }}</small>
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

    <section v-if="gameKey === 'poker'" class="rule-setting-group">
      <header><strong>起始筹码</strong><small>每局重新发放，不涉及真实货币</small></header>
      <div class="rule-segmented three">
        <button v-for="chips in [500, 1000, 2000]" :key="chips" type="button" :class="{ active: option('startingChips') === chips }" @click="setOption('startingChips', chips)">{{ chips }}</button>
      </div>
    </section>

    <section v-if="gameKey === 'poker'" class="rule-setting-group">
      <header><strong>大小盲注</strong><small>大盲始终是小盲的两倍</small></header>
      <div class="rule-segmented three">
        <button v-for="blind in [5, 10, 20]" :key="blind" type="button" :class="{ active: option('smallBlind') === blind }" @click="setOption('smallBlind', blind)">{{ blind }}/{{ blind * 2 }}</button>
      </div>
    </section>

    <section v-if="gameKey === 'go'" class="rule-setting-group">
      <header><strong>贴目</strong><small>终局数子时计入白方</small></header>
      <div class="rule-segmented three">
        <button v-for="komi in [0, 6.5, 7.5]" :key="komi" type="button" :class="{ active: option('komi') === komi }" @click="setOption('komi', komi)">{{ komi }}</button>
      </div>
    </section>

    <section v-if="!['reaction', 'schulte', 'minesweeper', 'hanoi', 'poker'].includes(gameKey)" class="rule-setting-group">
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
.game-rule-settings { display: grid; gap: 0; }
.rule-setting-group { display: grid; gap: 11px; padding: 18px 0; border-bottom: 1px solid var(--line); }
.rule-setting-group:first-child { padding-top: 0; }
.rule-setting-group:last-child { padding-bottom: 0; border-bottom: 0; }
.rule-setting-group > header { display: grid; grid-template-columns: minmax(105px, auto) minmax(0, 1fr); align-items: baseline; gap: 10px; }
.rule-setting-group > header strong { font-size: 15px; letter-spacing: .01em; }
.rule-setting-group > header small { color: var(--muted); font-size: 12px; line-height: 1.45; text-align: right; }
.rule-option-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }
.rule-option-grid.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.rule-option-grid button { position: relative; min-height: 74px; display: grid; align-content: center; gap: 4px; border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 12px 14px; color: var(--text); background: var(--surface-inset); text-align: left; cursor: pointer; }
.rule-option-grid button::after { position: absolute; top: 11px; right: 11px; width: 7px; aspect-ratio: 1; border: 1px solid var(--line); border-radius: 50%; content: ''; }
.rule-option-grid button strong { padding-right: 12px; font-size: 13px; }
.rule-option-grid small { color: var(--muted); font-size: 11px; line-height: 1.4; }
.rule-option-grid button.active, .rule-segmented button.active { border-color: color-mix(in srgb, var(--gold) 58%, var(--line)); background: color-mix(in srgb, var(--gold) 9%, var(--surface-inset)); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--gold) 12%, transparent); }
.rule-option-grid button.active::after { border-color: var(--gold); background: var(--gold); box-shadow: 0 0 0 3px color-mix(in srgb, var(--gold) 11%, transparent); }
.rule-option-grid button:disabled { cursor: not-allowed; opacity: .48; }
.rule-segmented { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 3px; border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 3px; overflow: hidden; background: var(--surface-inset); }
.rule-segmented.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.rule-segmented.six { grid-template-columns: repeat(6, minmax(0, 1fr)); }
.rule-segmented button { min-height: 44px; border: 0; border-radius: 7px; color: var(--muted); background: transparent; font-size: 12px; font-weight: 850; cursor: pointer; }
.rule-segmented button.active { color: var(--gold); background: var(--surface-elevated); box-shadow: 0 4px 12px color-mix(in srgb, var(--bg) 20%, transparent); }
.rule-toggle-list { display: grid; gap: 8px; }
.rule-toggle-list button { min-height: 62px; display: flex; align-items: center; justify-content: space-between; gap: 12px; border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 10px 13px; color: var(--text); background: var(--surface-inset); text-align: left; cursor: pointer; }
.rule-toggle-list span { display: grid; gap: 2px; }
.rule-toggle-list small { color: var(--muted); }
.rule-toggle-list b { min-width: 38px; border-radius: 999px; padding: 5px 8px; color: var(--muted); background: rgba(255, 255, 255, .06); text-align: center; }
.rule-toggle-list button.active b { color: var(--accent-contrast); background: var(--gold); }
@media (hover: hover) {
  .rule-option-grid button:hover:not(:disabled), .rule-toggle-list button:hover { border-color: var(--line-strong); transform: translateY(-1px); }
}
@media (max-width: 520px) {
  .rule-setting-group { padding: 15px 0; }
  .rule-setting-group > header { grid-template-columns: 1fr; gap: 3px; }
  .rule-setting-group > header small { text-align: left; }
  .rule-option-grid, .rule-option-grid.three { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 7px; }
  .rule-option-grid button { min-height: 80px; padding: 10px; }
  .rule-option-grid button strong { font-size: 12px; }.rule-option-grid small { font-size: 10px; }
  .rule-option-grid.three button:first-child { grid-column: 1 / -1; min-height: 66px; }
  .rule-segmented.six { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 350px) {
  .rule-option-grid, .rule-option-grid.three { grid-template-columns: 1fr; }
  .rule-option-grid.three button:first-child { grid-column: auto; }
}
</style>
