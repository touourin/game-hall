<script setup lang="ts">
import type { ArcadeGameKey } from '../types/arcade'
import { builtinGameDefinition } from '../game-platform/registry'
import {
  applyGameRuleChange,
  hasGameHandicap,
  withDefaultGameRules,
} from '../gameRules'
import { GO_HANDICAP_OPTIONS } from '../games/go/rules'
import { XIANGQI_HANDICAP_OPTIONS } from '../games/xiangqi/rules'
import ModeGuide from './ModeGuide.vue'
import { AVALON_COURT_GUIDE } from '../gameModeGuides'

const props = defineProps<{
  gameKey: ArcadeGameKey
  modelValue: Record<string, unknown>
  guestMode?: boolean
}>()
const emit = defineEmits<{
  'update:modelValue': [value: Record<string, unknown>]
}>()

function option(key: string): unknown {
  return withDefaultGameRules(props.gameKey, props.modelValue)[key]
}

function setOption(key: string, value: unknown) {
  emit(
    'update:modelValue',
    applyGameRuleChange(props.gameKey, props.modelValue, key, value),
  )
}

function hasHandicap(): boolean {
  return hasGameHandicap(
    props.gameKey,
    withDefaultGameRules(props.gameKey, props.modelValue),
  )
}

function supportsUndo(): boolean {
  const capabilities = builtinGameDefinition(props.gameKey)?.capabilities
  if (capabilities) return capabilities.undo
  return ['gomoku', 'xiangqi', 'go'].includes(props.gameKey)
}

function supportsDraw(): boolean {
  const capabilities = builtinGameDefinition(props.gameKey)?.capabilities
  if (capabilities) return capabilities.draw
  return ['gomoku', 'xiangqi', 'go'].includes(props.gameKey)
}

function supportsFirstPlayer(): boolean {
  const capabilities = builtinGameDefinition(props.gameKey)?.capabilities
  if (capabilities) return capabilities.firstPlayer
  return ![
    'avalon',
    'one_night_werewolf',
    'reaction',
    'deep_shaft',
    'schulte',
    'survive_three_seconds',
    'minesweeper',
    'hanoi',
    'tetris',
    'poker',
  ].includes(props.gameKey)
}

function supportsGuests(): boolean {
  const capabilities = builtinGameDefinition(props.gameKey)?.capabilities
  if (capabilities) return capabilities.guests
  return ![
    'reaction',
    'deep_shaft',
    'schulte',
    'survive_three_seconds',
    'minesweeper',
    'hanoi',
    'tetris',
  ].includes(props.gameKey)
}

function supportsSpectators(): boolean {
  const capabilities = builtinGameDefinition(props.gameKey)?.capabilities
  if (capabilities) return capabilities.spectators
  return !['one_night_werewolf', 'tetris'].includes(props.gameKey)
}

</script>

<template>
  <div class="game-rule-settings">
    <section v-if="gameKey === 'avalon'" class="rule-setting-group">
      <header><strong>玩法模式</strong><small>王庭暗流加入心怀异念之臣、黑誓授刃和最后议事</small></header>
      <div class="rule-option-grid">
        <button type="button" :class="{ active: option('mode') === 'standard' }" @click="setOption('mode', 'standard')">
          <strong>标准阿瓦隆</strong><small>经典任务、湖中仙女与刺杀梅林</small>
        </button>
        <button type="button" :class="{ active: option('mode') === 'court_undercurrent' }" @click="setOption('mode', 'court_undercurrent')">
          <strong>王庭暗流</strong><small>心怀异念之臣可能被刺客授刃转化</small>
        </button>
      </div>
    </section>

    <section v-if="gameKey === 'departed_suspicion'" class="rule-setting-group">
      <header><strong>装备牌库</strong><small>卧底扩展依赖完整掩护系统，因此不混入普通身份局</small></header>
      <div class="rule-option-grid">
        <button type="button" :class="{ active: option('equipmentSet') === 'bombers' }" @click="setOption('equipmentSet', 'bombers')">
          <strong>炸弹客/叛徒装备</strong><small>基础16张加该扩展5张，共21张</small>
        </button>
        <button type="button" :class="{ active: option('equipmentSet') === 'base' }" @click="setOption('equipmentSet', 'base')">
          <strong>基础装备</strong><small>只使用经典16张，适合第一次教学</small>
        </button>
      </div>
    </section>

    <section v-if="gameKey === 'one_night_werewolf'" class="rule-setting-group">
      <header><strong>角色组合</strong><small>所有组合都包含玩家人数加三张牌；多皮者留待后续扩展</small></header>
      <div class="rule-option-grid three">
        <button type="button" :class="{ active: option('rolePreset') === 'beginner' }" @click="setOption('rolePreset', 'beginner')">
          <strong>初见月夜</strong><small>核心换牌角色，适合第一次教学</small>
        </button>
        <button type="button" :class="{ active: option('rolePreset') === 'standard' }" @click="setOption('rolePreset', 'standard')">
          <strong>标准疑云</strong><small>加入爪牙与皮匠，阵营判断更丰富</small>
        </button>
        <button type="button" :class="{ active: option('rolePreset') === 'chaos' }" @click="setOption('rolePreset', 'chaos')">
          <strong>混沌之夜</strong><small>高人数加入守夜人，信息交叉更多</small>
        </button>
      </div>
    </section>

    <section v-if="gameKey === 'one_night_werewolf'" class="rule-setting-group">
      <header><strong>房间发现</strong><small>进行中固定关闭观战，避免第一人称视角泄露私密身份</small></header>
      <div class="rule-option-grid">
        <button type="button" :class="{ active: option('listed') }" @click="setOption('listed', true)">
          <strong>公开房间</strong><small>等待阶段可以在大厅中被发现</small>
        </button>
        <button type="button" :class="{ active: !option('listed') }" @click="setOption('listed', false)">
          <strong>私密房间</strong><small>只有拿到房间码或邀请链接的玩家可加入</small>
        </button>
      </div>
    </section>

    <details
      v-if="gameKey === 'avalon' && option('mode') === 'court_undercurrent'"
      class="avalon-mode-guide-disclosure"
    >
      <summary>
        <span><strong>王庭暗流完整说明</strong><small>一分钟导读 · 完整规则 · 完整背景故事</small></span>
        <b>展开 / 收起</b>
      </summary>
      <ModeGuide :content="AVALON_COURT_GUIDE" />
    </details>

    <section
      v-if="gameKey === 'avalon' && option('mode') === 'court_undercurrent'"
      class="rule-setting-group"
    >
      <header><strong>扩展包角色</strong><small>暗影梅林建立在王庭暗流完整规则之上</small></header>
      <div class="rule-toggle-list">
        <button
          type="button"
          :class="{ active: option('shadowMerlinEnabled') }"
          @click="setOption('shadowMerlinEnabled', !option('shadowMerlinEnabled'))"
        >
          <span>
            <strong>暗影梅林</strong>
            <small>六人及以上可用 · 替换一名忠臣 · 开启祓影议庭</small>
          </span>
          <b>{{ option('shadowMerlinEnabled') ? '开' : '关' }}</b>
        </button>
      </div>
    </section>

    <section v-if="gameKey === 'avalon'" class="rule-setting-group">
      <header><strong>对局规则</strong><small>王庭暗流固定关闭湖中仙女和提前刺杀</small></header>
      <div class="rule-toggle-list">
        <button type="button" :class="{ active: option('listed') }" @click="setOption('listed', !option('listed'))">
          <span><strong>公开房间</strong><small>允许其他玩家在大厅房间列表中发现</small></span><b>{{ option('listed') ? '开' : '关' }}</b>
        </button>
        <button type="button" :class="{ active: option('ladyEnabled') }" :disabled="option('mode') === 'court_undercurrent'" @click="setOption('ladyEnabled', !option('ladyEnabled'))">
          <span><strong>湖中仙女</strong><small>从第 2 次任务后开始查验阵营</small></span><b>{{ option('ladyEnabled') ? '开' : '关' }}</b>
        </button>
        <button type="button" :class="{ active: option('earlyAssassinationEnabled') }" :disabled="option('mode') === 'court_undercurrent'" @click="setOption('earlyAssassinationEnabled', !option('earlyAssassinationEnabled'))">
          <span><strong>提前刺杀</strong><small>刺客可在任务期间豪赌梅林，刺错立即失败</small></span><b>{{ option('earlyAssassinationEnabled') ? '开' : '关' }}</b>
        </button>
      </div>
    </section>

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

    <section v-if="gameKey === 'tetris'" class="rule-setting-group">
      <header><strong>挑战模式</strong><small>限时模式到点自动结算；无限模式保留原来的堆顶结束玩法</small></header>
      <div class="rule-option-grid">
        <button type="button" :class="{ active: option('challengeMode') === 'timed' }" @click="setOption('challengeMode', 'timed')">
          <strong>限时挑战</strong><small>在固定时间内尽可能获得高分</small>
        </button>
        <button type="button" :class="{ active: option('challengeMode') === 'endless' }" @click="setOption('challengeMode', 'endless')">
          <strong>无限挑战</strong><small>持续游玩，直到方块堆到顶部</small>
        </button>
      </div>
    </section>

    <section v-if="gameKey === 'tetris' && option('challengeMode') === 'timed'" class="rule-setting-group">
      <header><strong>挑战时长</strong><small>不同时间档位分别记录排行榜</small></header>
      <div class="rule-segmented three">
        <button
          v-for="seconds in [60, 180, 300]"
          :key="seconds"
          type="button"
          :class="{ active: option('durationSeconds') === seconds }"
          @click="setOption('durationSeconds', seconds)"
        >{{ seconds / 60 }} 分钟</button>
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

    <section v-if="gameKey === 'xiangqi'" class="rule-setting-group">
      <header><strong>让子规则</strong><small>让子方固定执红并先走；让九子移除五兵、双仕、双相</small></header>
      <div class="rule-segmented five">
        <button v-for="item in XIANGQI_HANDICAP_OPTIONS" :key="item.value" type="button" :class="{ active: option('handicap') === item.value }" @click="setOption('handicap', item.value)">{{ item.label }}</button>
      </div>
    </section>

    <section v-if="gameKey === 'go'" class="rule-setting-group">
      <header><strong>让子规则</strong><small>仅限 19 路；被让子方执白并预置白子，让子方执黑先走，贴目固定为 0</small></header>
      <div class="rule-segmented five">
        <button v-for="count in GO_HANDICAP_OPTIONS" :key="count" type="button" :class="{ active: option('handicap') === count }" @click="setOption('handicap', count)">{{ count ? `让 ${count} 子` : '不让子' }}</button>
      </div>
    </section>

    <section v-if="['xiangqi', 'go'].includes(gameKey) && hasHandicap()" class="rule-setting-group">
      <header><strong>让子方</strong><small>按玩家身份固定，再来一局不会因座位轮换而改变</small></header>
      <div class="rule-option-grid">
        <button type="button" :class="{ active: option('handicapGiver') === 'host' }" @click="setOption('handicapGiver', 'host')">
          <strong>房主让子</strong><small>房主作为让子方</small>
        </button>
        <button type="button" :class="{ active: option('handicapGiver') === 'opponent' }" @click="setOption('handicapGiver', 'opponent')">
          <strong>对手让子</strong><small>加入房间的玩家或 AI 作为让子方</small>
        </button>
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
      <header><strong>起始筹码</strong><small>开桌时发放，后续手牌持续继承，不涉及真实货币</small></header>
      <div class="rule-segmented three">
        <button v-for="chips in [500, 1000, 2000]" :key="chips" type="button" :class="{ active: option('startingChips') === chips }" @click="setOption('startingChips', chips)">{{ chips }}</button>
      </div>
    </section>

    <section v-if="gameKey === 'monopoly'" class="rule-setting-group">
      <header><strong>起始资金</strong><small>资金越少，前期买地取舍越明显</small></header>
      <div class="rule-segmented three">
        <button v-for="cash in [6000, 8000, 10000]" :key="cash" type="button" :class="{ active: option('startingCash') === cash }" @click="setOption('startingCash', cash)">{{ cash }}</button>
      </div>
    </section>

    <section v-if="gameKey === 'monopoly'" class="rule-setting-group">
      <header><strong>比赛回合</strong><small>达到上限时按现金、地产与升级总值排名</small></header>
      <div class="rule-segmented three">
        <button v-for="rounds in [12, 20, 30]" :key="rounds" type="button" :class="{ active: option('maxRounds') === rounds }" @click="setOption('maxRounds', rounds)">{{ rounds }} 回合</button>
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
        <button v-for="komi in [0, 6.5, 7.5]" :key="komi" type="button" :disabled="hasHandicap()" :class="{ active: option('komi') === komi }" @click="setOption('komi', komi)">{{ komi }}</button>
      </div>
    </section>

    <section v-if="supportsFirstPlayer() && !hasHandicap()" class="rule-setting-group">
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

    <section v-if="gameKey === 'xiangqi'" class="rule-setting-group">
      <header><strong>辅助提示</strong><small>双方使用同一设置，不改变象棋走子规则</small></header>
      <div class="rule-toggle-list">
        <button
          type="button"
          :class="{ active: option('captureHintsEnabled') }"
          @click="setOption('captureHintsEnabled', !option('captureHintsEnabled'))"
        >
          <span>
            <strong>吃子提醒</strong>
            <small>轮到玩家时标出当前可以吃到的敌子</small>
          </span>
          <b>{{ option('captureHintsEnabled') ? '开' : '关' }}</b>
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

<style scoped>
.game-rule-settings { min-width: 0; display: grid; gap: 0; }
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
.rule-segmented.five { grid-template-columns: repeat(5, minmax(0, 1fr)); }
.rule-segmented.six { grid-template-columns: repeat(6, minmax(0, 1fr)); }
.rule-segmented button { min-height: 44px; border: 0; border-radius: 7px; color: var(--muted); background: transparent; font-size: 12px; font-weight: 850; cursor: pointer; }
.rule-segmented button.active { color: var(--gold); background: var(--surface-elevated); box-shadow: 0 4px 12px color-mix(in srgb, var(--bg) 20%, transparent); }
.rule-segmented button:disabled { cursor: not-allowed; opacity: .48; }
.rule-toggle-list { display: grid; gap: 8px; }
.rule-toggle-list button { min-height: 62px; display: flex; align-items: center; justify-content: space-between; gap: 12px; border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 10px 13px; color: var(--text); background: var(--surface-inset); text-align: left; cursor: pointer; }
.rule-toggle-list button:disabled { cursor: not-allowed; opacity: .48; }
.rule-toggle-list span { display: grid; gap: 2px; }
.rule-toggle-list small { color: var(--muted); }
.rule-toggle-list b { min-width: 38px; border-radius: 999px; padding: 5px 8px; color: var(--muted); background: rgba(255, 255, 255, .06); text-align: center; }
.rule-toggle-list button.active b { color: var(--accent-contrast); background: var(--gold); }
.avalon-mode-guide-disclosure { min-width: 0; margin: 0; border-bottom: 1px solid var(--line); padding: 14px 0 18px; }
.avalon-mode-guide-disclosure summary { display: flex; align-items: center; justify-content: space-between; gap: 14px; border: 1px solid color-mix(in srgb, var(--gold) 30%, var(--line)); border-radius: 13px; padding: 11px 13px; color: var(--text); background: color-mix(in srgb, var(--gold) 7%, var(--surface-inset)); cursor: pointer; list-style: none; }
.avalon-mode-guide-disclosure summary::-webkit-details-marker { display: none; }
.avalon-mode-guide-disclosure summary > span { min-width: 0; display: grid; gap: 2px; }
.avalon-mode-guide-disclosure summary strong { color: var(--gold); font-size: 12px; }
.avalon-mode-guide-disclosure summary small { color: var(--muted); font-size: 10px; }
.avalon-mode-guide-disclosure summary b { flex: 0 0 auto; color: var(--muted); font-size: 9px; }
.avalon-mode-guide-disclosure[open] summary { margin-bottom: 11px; }
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
  .rule-segmented.five, .rule-segmented.six { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 350px) {
  .rule-option-grid, .rule-option-grid.three { grid-template-columns: 1fr; }
  .rule-option-grid.three button:first-child { grid-column: auto; }
}
</style>
