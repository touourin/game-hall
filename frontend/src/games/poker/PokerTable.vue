<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { CircleDollarSign, Coins } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'

interface PokerCard {
  id: string
  rank: number
  rankLabel: string
  suit: string
  suitSymbol: string
  red: boolean
}

interface PokerPlayerState {
  id: string
  name: string
  seat: number
  chips: number
  streetBet: number
  totalBet: number
  folded: boolean
  allIn: boolean
  isDealer: boolean
  isSmallBlind: boolean
  isBigBlind: boolean
  isActing: boolean
  cards: PokerCard[]
  cardCount: number
  handName: string | null
  payout: number
  eliminated: boolean
  readyNextHand: boolean
}

interface LegalActions {
  canAct: boolean
  canFold: boolean
  canCheck: boolean
  canCall: boolean
  canRaise: boolean
  canAllIn: boolean
  callAmount: number
  minimumRaiseTo: number
  maximumRaiseTo: number
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const raiseTo = ref(0)
const game = computed(() => props.snapshot.game as {
  street: string
  streetLabel: string
  communityCards: PokerCard[]
  pot: number
  currentBet: number
  smallBlind: number
  bigBlind: number
  startingChips: number
  actionPlayerId: string | null
  dealerPlayerId: string
  players: PokerPlayerState[]
  legalActions: LegalActions
  showdown: boolean
  sidePots: Array<{ amount: number; winnerIds: string[]; handName: string }>
  history: Array<{ street: string; playerId: string; action: string; amount: number; streetBet?: number }>
  handNumber: number
  lastHandReason: string | null
  nextHandReadyPlayerIds: string[]
  requiredNextHandReadyCount: number
  canReadyNextHand: boolean
  eliminatedIds: string[]
})
const self = computed(() => game.value.players.find((player) => player.id === props.snapshot.self.id))
const opponents = computed(() => game.value.players.filter((player) => player.id !== props.snapshot.self.id))
const legal = computed(() => game.value.legalActions)
const lastActions = computed(() => game.value.history.slice(-5).reverse())

watch(
  () => [legal.value.minimumRaiseTo, legal.value.maximumRaiseTo, legal.value.canRaise],
  () => {
    raiseTo.value = legal.value.canRaise ? legal.value.minimumRaiseTo : 0
  },
  { immediate: true },
)

function playerName(playerId: string): string {
  return game.value.players.find((player) => player.id === playerId)?.name ?? '玩家'
}

function actionLabel(action: string): string {
  return {
    small_blind: '小盲',
    big_blind: '大盲',
    fold: '弃牌',
    check: '过牌',
    call: '跟注',
    raise: '加注到',
    all_in: '全押',
    resign: '离局弃牌',
  }[action] ?? action
}

function quickRaise(kind: 'minimum' | 'half' | 'pot') {
  const potAfterCall = game.value.pot + legal.value.callAmount
  const desired = kind === 'minimum'
    ? legal.value.minimumRaiseTo
    : game.value.currentBet + Math.max(
        legal.value.minimumRaiseTo - game.value.currentBet,
        Math.ceil(potAfterCall * (kind === 'half' ? 0.5 : 1)),
      )
  raiseTo.value = Math.min(legal.value.maximumRaiseTo, desired)
}

function historyAmount(entry: { action: string; amount: number; streetBet?: number }): number {
  return entry.action === 'raise' && entry.streetBet !== undefined
    ? entry.streetBet
    : entry.amount
}

function act(action: string, payload: Record<string, unknown> = {}) {
  void arcade.action(action, payload)
}
</script>

<template>
  <section class="poker-panel">
    <header class="poker-status">
      <div><small>{{ game.streetLabel }}</small><strong><CircleDollarSign :size="19" />底池 {{ game.pot }}</strong></div>
      <span>盲注 {{ game.smallBlind }}/{{ game.bigBlind }}</span>
    </header>

    <section class="poker-felt">
      <div class="opponent-grid">
        <article
          v-for="player in opponents"
          :key="player.id"
          class="poker-seat opponent-seat"
          :class="{ acting: player.isActing, folded: player.folded, eliminated: player.eliminated }"
        >
          <header><strong>{{ player.name }}</strong><span v-if="player.isDealer">D</span><span v-if="player.isSmallBlind">SB</span><span v-if="player.isBigBlind">BB</span></header>
          <div class="mini-hand">
            <span v-for="card in player.cards" :key="card.id" class="playing-card mini" :class="{ red: card.red }"><b>{{ card.rankLabel }}</b><i>{{ card.suitSymbol }}</i></span>
            <span v-for="index in player.cards.length ? 0 : player.cardCount" :key="`back-${index}`" class="playing-card mini card-back">♠</span>
          </div>
          <footer><span>{{ player.eliminated ? '已淘汰' : player.folded ? '已弃牌' : player.allIn ? '已全押' : `${player.chips} 筹码` }}</span><b v-if="player.streetBet">桌面 {{ player.streetBet }}</b><em v-if="player.handName">{{ player.handName }}</em></footer>
        </article>
      </div>

      <div class="community-area">
        <div class="community-cards">
          <span v-for="card in game.communityCards" :key="card.id" class="playing-card" :class="{ red: card.red }"><b>{{ card.rankLabel }}</b><i>{{ card.suitSymbol }}</i></span>
          <span v-for="slot in 5 - game.communityCards.length" :key="`empty-${slot}`" class="playing-card empty"></span>
        </div>
        <div v-if="game.sidePots.length > 1" class="side-pot-summary">
          <span v-for="(pot, index) in game.sidePots" :key="index">{{ index ? `边池 ${index}` : '主池' }} {{ pot.amount }}</span>
        </div>
      </div>

      <article v-if="self" class="poker-seat self-seat" :class="{ acting: self.isActing, folded: self.folded, eliminated: self.eliminated }">
        <div class="self-hand">
          <span v-for="card in self.cards" :key="card.id" class="playing-card own-card" :class="{ red: card.red }"><b>{{ card.rankLabel }}</b><i>{{ card.suitSymbol }}</i></span>
        </div>
        <div class="self-copy">
          <header><strong>{{ self.name }} · 你</strong><span v-if="self.isDealer">庄家 D</span><span v-if="self.isSmallBlind">小盲</span><span v-if="self.isBigBlind">大盲</span></header>
          <p><Coins :size="16" />{{ self.eliminated ? '已淘汰' : `${self.chips} 筹码` }} <b v-if="self.streetBet">· 已下注 {{ self.streetBet }}</b></p>
          <em v-if="self.handName">{{ self.handName }}<template v-if="self.payout"> · 赢得 {{ self.payout }}</template></em>
        </div>
      </article>
    </section>

    <section v-if="snapshot.phase === 'playing'" class="poker-controls surface">
      <template v-if="legal.canAct">
        <div class="primary-actions">
          <button v-if="legal.canFold" type="button" class="fold" :disabled="arcade.busy" @click="act('fold')">弃牌</button>
          <button v-if="legal.canCheck" type="button" :disabled="arcade.busy" @click="act('check')">过牌</button>
          <button v-if="legal.canCall" type="button" :disabled="arcade.busy" @click="act('call')">跟注 {{ legal.callAmount }}</button>
          <button v-if="legal.canAllIn" type="button" class="all-in" :disabled="arcade.busy" @click="act('all_in')">全押</button>
        </div>
        <div v-if="legal.canRaise" class="raise-controls">
          <div class="quick-raises">
            <button type="button" @click="quickRaise('minimum')">最小</button>
            <button type="button" @click="quickRaise('half')">1/2 底池</button>
            <button type="button" @click="quickRaise('pot')">底池</button>
          </div>
          <label><span>加注到</span><input v-model.number="raiseTo" type="number" inputmode="numeric" :min="legal.minimumRaiseTo" :max="legal.maximumRaiseTo" /></label>
          <button type="button" class="raise-button" :disabled="arcade.busy || raiseTo < legal.minimumRaiseTo || raiseTo > legal.maximumRaiseTo" @click="act('raise', { raiseTo })">确认加注</button>
        </div>
      </template>
      <p v-else>{{ game.actionPlayerId ? `等待 ${playerName(game.actionPlayerId)} 行动` : '正在结算牌局' }}</p>
    </section>

    <section v-else-if="snapshot.phase === 'between_hands'" class="surface next-hand-panel">
      <div>
        <small>第 {{ game.handNumber }} 手牌结束</small>
        <strong>{{ game.lastHandReason }}</strong>
        <span>{{ game.nextHandReadyPlayerIds.length }} / {{ game.requiredNextHandReadyCount }} 人已准备下一手</span>
      </div>
      <button
        v-if="game.canReadyNextHand"
        type="button"
        class="primary-button"
        :disabled="arcade.busy"
        @click="act('ready_next_hand')"
      >
        准备下一手
      </button>
      <p v-else-if="self?.eliminated">你已淘汰，可以继续观战</p>
      <p v-else>等待其他玩家准备</p>
    </section>

    <section v-if="lastActions.length" class="poker-history">
      <span v-for="(entry, index) in lastActions" :key="index"><b>{{ playerName(entry.playerId) }}</b>{{ actionLabel(entry.action) }}<em v-if="historyAmount(entry)"> {{ historyAmount(entry) }}</em></span>
    </section>
  </section>
</template>

<style scoped>
.poker-panel { display: grid; gap: 14px; }.poker-status { display: flex; align-items: end; justify-content: space-between; gap: 12px; }.poker-status div { display: grid; gap: 3px; }.poker-status small { color: var(--gold); font-weight: 850; letter-spacing: .08em; }.poker-status strong { display: flex; align-items: center; gap: 6px; font-size: 22px; }.poker-status > span { color: var(--muted); font-weight: 800; }
.poker-felt { position: relative; min-height: 610px; overflow: hidden; display: grid; grid-template-rows: 1fr auto auto; gap: 22px; border: 8px solid var(--game-felt-border, #5d351d); border-radius: 42% / 9%; padding: clamp(24px, 5vw, 48px); background: var(--game-felt-surface, radial-gradient(ellipse at center, #176348 0%, #0d4b38 62%, #08382d 100%)); box-shadow: inset 0 0 0 3px var(--game-felt-highlight, #bc8650), inset 0 0 70px #001018aa, 0 20px 52px #0007; }.poker-felt::after { content: ''; pointer-events: none; position: absolute; inset: 14px; border: 1px solid color-mix(in srgb, var(--game-felt-highlight, #d7bd78) 45%, transparent); border-radius: inherit; }
.opponent-grid { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(auto-fit, minmax(118px, 1fr)); align-content: start; gap: 10px; }.poker-seat { border: 1px solid #ffffff20; border-radius: 14px; color: #effaf4; background: var(--game-seat-surface, #062e27d9); box-shadow: 0 9px 20px #001018aa; }.poker-seat.acting { border-color: #f2c862; box-shadow: 0 0 0 2px #f2c86244, 0 10px 24px #001c17; }.poker-seat.folded,.poker-seat.eliminated { opacity: .52; filter: grayscale(.45); }.opponent-seat { min-height: 112px; padding: 10px; display: grid; grid-template-rows: auto 1fr auto; gap: 6px; }.poker-seat header { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; }.poker-seat header strong { min-width: 0; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.poker-seat header span { border-radius: 5px; padding: 2px 4px; color: #241b0e; background: #e4bc67; font-size: 10px; font-weight: 900; }.opponent-seat footer { display: flex; flex-wrap: wrap; gap: 4px 7px; color: #aec8bd; font-size: 11px; }.opponent-seat footer b { color: #edca7e; }.opponent-seat footer em { width: 100%; color: #f4d58d; font-style: normal; font-weight: 800; }
.mini-hand { display: flex; align-items: center; justify-content: center; }.playing-card { width: clamp(42px, 9vw, 64px); aspect-ratio: 5 / 7; display: grid; align-content: space-between; border: 1px solid var(--game-card-border, #d8d4c6); border-radius: 7px; padding: 5px; color: #17211f; background: var(--game-card-face, linear-gradient(145deg, #fffdf6, #ddd9cc)); box-shadow: 0 5px 10px #001017aa; font-family: Georgia, serif; font-style: normal; }.playing-card b { line-height: 1; font-size: clamp(16px, 3.8vw, 24px); }.playing-card i { justify-self: end; line-height: 1; font-size: clamp(18px, 4vw, 26px); font-style: normal; }.playing-card.red { color: #bd2f35; }.playing-card.mini { width: 32px; border-radius: 5px; padding: 3px; }.playing-card.mini + .playing-card.mini { margin-left: -7px; }.playing-card.mini b { font-size: 12px; }.playing-card.mini i { font-size: 13px; }.card-back { place-items: center; border-color: var(--game-card-back-accent, #d0b06a); color: var(--game-card-back-accent, #e8c978); background: var(--game-card-back, repeating-linear-gradient(45deg, #243d55 0 4px, #172c42 4px 8px)); font-size: 14px; }.playing-card.empty { border-style: dashed; border-color: color-mix(in srgb, var(--game-card-back-accent, #e6d392) 28%, transparent); background: rgba(0, 0, 0, .16); box-shadow: none; }
.community-area { position: relative; z-index: 1; display: grid; justify-items: center; gap: 8px; }.community-cards { min-height: 70px; display: flex; justify-content: center; gap: clamp(4px, 1.3vw, 9px); }.side-pot-summary { display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; }.side-pot-summary span { border-radius: 999px; padding: 3px 7px; color: #ead295; background: #002c21aa; font-size: 11px; }
.self-seat { position: relative; z-index: 1; min-height: 106px; display: grid; grid-template-columns: auto 1fr; align-items: center; gap: 14px; padding: 12px 16px; }.self-hand { display: flex; }.own-card + .own-card { margin-left: -9px; }.self-copy { min-width: 0; }.self-copy header strong { font-size: 18px; }.self-copy p { margin: 8px 0 0; display: flex; flex-wrap: wrap; align-items: center; gap: 3px 5px; color: #dfeee7; }.self-copy p b { color: #e4c172; white-space: nowrap; }.self-copy > em { display: block; margin-top: 5px; color: #f0cd7b; font-style: normal; font-weight: 850; }
.poker-controls { padding: 14px; display: grid; gap: 10px; }.poker-controls p { margin: 0; color: var(--muted); text-align: center; }.primary-actions { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 7px; }.primary-actions button, .raise-button, .quick-raises button { min-height: 44px; border: 1px solid var(--line); border-radius: 10px; color: var(--text); background: rgba(255,255,255,.05); font-weight: 850; }.primary-actions .fold { color: #f08e8b; }.primary-actions .all-in { color: #f1ca73; border-color: #d4aa5355; background: #d4aa5314; }.raise-controls { display: grid; grid-template-columns: 1fr auto auto; align-items: end; gap: 8px; }.quick-raises { display: flex; gap: 5px; }.quick-raises button { min-height: 38px; padding: 0 9px; color: var(--muted); font-size: 12px; }.raise-controls label { display: grid; gap: 3px; color: var(--muted); font-size: 11px; }.raise-controls input { width: 100px; min-height: 38px; border: 1px solid var(--line); border-radius: 9px; padding: 0 9px; color: var(--text); background: #001f20; }.raise-button { padding: 0 13px; color: #192019; background: var(--gold); }
.next-hand-panel { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 16px; }.next-hand-panel > div { display: grid; gap: 3px; }.next-hand-panel small { color: var(--gold); }.next-hand-panel span,.next-hand-panel p { margin: 0; color: var(--muted); }.next-hand-panel .primary-button { flex: 0 0 auto; }
.poker-history { display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; }.poker-history span { border: 1px solid var(--line); border-radius: 999px; padding: 4px 8px; color: var(--muted); font-size: 11px; }.poker-history b { margin-right: 4px; color: var(--text); }.poker-history em { margin-left: 3px; color: var(--gold); font-style: normal; }
@media (max-width: 600px) { .poker-status { align-items: start; }.poker-status strong { font-size: 19px; }.poker-felt { min-height: 560px; border-width: 5px; border-radius: 30px; padding: 23px 12px; gap: 16px; }.opponent-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 7px; }.opponent-seat { min-height: 102px; padding: 8px; }.playing-card { width: clamp(43px, 12vw, 52px); }.self-seat { padding: 10px 12px; gap: 9px; }.self-copy p { font-size: 12px; }.primary-actions { grid-template-columns: repeat(2, minmax(0, 1fr)); }.raise-controls { grid-template-columns: 1fr auto; }.quick-raises { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(3, 1fr); }.quick-raises button { padding: 0 5px; }.raise-controls input { width: 100%; }.raise-button { min-width: 98px; }.next-hand-panel { align-items: stretch; flex-direction: column; }.poker-history { justify-content: flex-start; overflow-x: auto; flex-wrap: nowrap; padding-bottom: 3px; }.poker-history span { flex: 0 0 auto; } }
</style>
