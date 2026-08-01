<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Crown, Flag, History, ListOrdered } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'

interface PlayingCard {
  id: string
  rank: number
  label: string
  suit: 'spade' | 'heart' | 'club' | 'diamond' | null
}

interface HistoryEntry {
  type: 'bid' | 'landlord' | 'play' | 'pass'
  playerId?: string
  playerName?: string
  decision?: 'call' | 'rob' | 'pass'
  cards?: PlayingCard[]
  pattern?: { kind: string; label: string }
}

interface LegacyBidEntry {
  seat: number
  score: number
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const selectedIds = ref<string[]>([])
const game = computed(() => props.snapshot.game as {
  phase: string
  variant?: 'classic' | 'laizi' | 'no_shuffle'
  currentPlayerId: string | null
  bids: Array<HistoryEntry | LegacyBidEntry>
  biddingMode?: 'call' | 'rob'
  highestBid?: number
  landlordCandidatePlayerId?: string | null
  landlordPlayerId: string | null
  bottomCards: PlayingCard[]
  hand: PlayingCard[]
  cardCounts: Record<string, number>
  teams: Record<string, 'landlord' | 'farmer'>
  lastPlay: { cards: PlayingCard[]; pattern: { kind: string; label?: string } } | null
  lastPlayPlayerId: string | null
  multiplier?: number
  multiplierEvents?: Array<{ reason: string; multiplier: number }>
  wildRank?: number | null
  wildLabel?: string | null
  history?: HistoryEntry[]
  remainingRanks?: Record<string, number>
  scores?: Record<string, number>
  settlement?: { baseScore: number; multiplier: number; spring: string | null } | null
})
const isMyTurn = computed(
  () => game.value.currentPlayerId === props.snapshot.self.id,
)
const otherPlayers = computed(() =>
  props.snapshot.players.filter((player) => player.id !== props.snapshot.self.id),
)
const lastPlayerName = computed(
  () =>
    props.snapshot.players.find((player) => player.id === game.value.lastPlayPlayerId)
      ?.name ?? '',
)
const candidateName = computed(
  () => props.snapshot.players.find(
    (player) => player.id === game.value.landlordCandidatePlayerId,
  )?.name ?? '',
)
const selfTeam = computed(() => game.value.teams[props.snapshot.self.id])
const currentPlayer = computed(() =>
  props.snapshot.players.find((player) => player.id === game.value.currentPlayerId),
)
const selectedCards = computed(() =>
  game.value.hand.filter((card) => selectedIds.value.includes(card.id)),
)
const usesDecisionBidding = computed(() =>
  game.value.biddingMode === 'call' || game.value.biddingMode === 'rob',
)
const normalizedHistory = computed(() => game.value.history ?? [])
const canPass = computed(
  () => isMyTurn.value
    && game.value.lastPlay !== null
    && game.value.lastPlayPlayerId !== props.snapshot.self.id,
)
const latestHistoryEntry = computed(() => normalizedHistory.value.at(-1) ?? null)
const latestPassName = computed(() => {
  const entry = latestHistoryEntry.value
  if (entry?.type !== 'pass') return ''
  return entry.playerName ?? ''
})
const handGridStyle = computed(() => ({
  '--hand-count': Math.max(game.value.hand.length, 1),
}))
const selectedPatternLabel = computed(() => describeSelectedCards(selectedCards.value))
const selectionHint = computed(() => {
  if (!selectedCards.value.length) {
    return isMyTurn.value ? '选择手牌后出牌' : '可提前选择手牌，等待你的回合'
  }
  const target = game.value.lastPlay && game.value.lastPlayPlayerId !== props.snapshot.self.id
    ? ` · 需要压过${lastPlayerName.value}的${game.value.lastPlay.pattern.label ?? '上一手牌'}`
    : ''
  return `已选 ${selectedCards.value.length} 张${selectedPatternLabel.value ? '' : ' · 出牌时校验牌型'}${target}`
})
const rankOrder = [17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3]
const rankLabels: Record<number, string> = {
  17: '大王', 16: '小王', 15: '2', 14: 'A', 13: 'K', 12: 'Q', 11: 'J',
}

watch(
  () => props.snapshot.revision,
  () => {
    selectedIds.value = selectedIds.value.filter((id) =>
      game.value.hand.some((card) => card.id === id),
    )
  },
)

function toggleCard(cardId: string) {
  selectedIds.value = selectedIds.value.includes(cardId)
    ? selectedIds.value.filter((id) => id !== cardId)
    : [...selectedIds.value, cardId]
}

function play() {
  if (!selectedIds.value.length) return
  const cardIds = [...selectedIds.value]
  selectedIds.value = []
  void arcade.action('play', { cardIds })
}

function bid(decision: 'call' | 'rob' | 'pass') {
  void arcade.action('bid', { decision })
}

function bidScore(score: number) {
  void arcade.action('bid', { score })
}

function suitSymbol(suit: PlayingCard['suit']): string {
  if (!suit) return ''
  return { spade: '♠', heart: '♥', club: '♣', diamond: '♦' }[suit] ?? ''
}

function isRed(card: PlayingCard): boolean {
  return card.suit === 'heart' || card.suit === 'diamond' || card.rank === 17
}

function isWild(card: PlayingCard): boolean {
  return game.value.wildRank != null && card.rank === game.value.wildRank
}

function teamLabel(team: 'landlord' | 'farmer' | undefined): string {
  if (!team) return '身份待定'
  return team === 'landlord' ? '地主' : '农民'
}

function describeSelectedCards(cards: PlayingCard[]): string {
  if (!cards.length) return ''
  if (cards.some(isWild)) return '含癞子'

  const ranks = cards.map((card) => card.rank).sort((a, b) => a - b)
  const counts = new Map<number, number>()
  for (const rank of ranks) counts.set(rank, (counts.get(rank) ?? 0) + 1)
  const groups = [...counts.entries()].sort(([a], [b]) => a - b)
  const quantities = groups.map(([, count]) => count).sort((a, b) => b - a)
  const consecutive = groups.every(
    ([rank], index) => index === 0 || rank === groups[index - 1][0] + 1,
  )

  if (cards.length === 1) return '单张'
  if (cards.length === 2 && ranks[0] === 16 && ranks[1] === 17) return '王炸'
  if (cards.length === 2 && quantities[0] === 2) return '对子'
  if (cards.length === 3 && quantities[0] === 3) return '三张'
  if (cards.length === 4 && quantities[0] === 4) return '炸弹'
  if (cards.length === 4 && quantities[0] === 3) return '三带一'
  if (cards.length === 5 && quantities[0] === 3 && quantities[1] === 2) return '三带二'
  if (cards.length >= 5 && quantities[0] === 1 && ranks.at(-1)! <= 14 && consecutive) return '顺子'
  if (cards.length >= 6 && cards.length % 2 === 0 && quantities.every((count) => count === 2) && ranks.at(-1)! <= 14 && consecutive) return '连对'
  if (cards.length >= 6 && cards.length % 3 === 0 && quantities.every((count) => count === 3) && ranks.at(-1)! <= 14 && consecutive) return '飞机'
  if (cards.length === 6 && quantities[0] === 4) return '四带二'
  if (cards.length === 8 && quantities[0] === 4 && quantities.slice(1).every((count) => count === 2)) return '四带两对'
  return ''
}

function historyText(entry: HistoryEntry | LegacyBidEntry): string {
  if ('score' in entry) return `${entry.seat + 1}号 ${entry.score || '不叫'}`
  if (entry.type === 'landlord') return `${entry.playerName} 成为地主`
  if (entry.type === 'pass' || entry.decision === 'pass') {
    return `${entry.playerName} ${entry.type === 'bid' ? '不叫／不抢' : '不出'}`
  }
  if (entry.type === 'bid') {
    return `${entry.playerName} ${entry.decision === 'call' ? '叫地主' : '抢地主'}`
  }
  return `${entry.playerName} · ${entry.pattern?.label ?? '出牌'} · ${entry.cards?.map((card) => card.label).join(' ') ?? ''}`
}

function rankLabel(rank: number): string {
  return rankLabels[rank] ?? String(rank)
}
</script>

<template>
  <section class="landlord-table" :class="{ 'is-my-turn': isMyTurn }">
    <header class="landlord-rule-bar">
      <span class="rule-chip">{{ game.variant === 'laizi' ? '癞子玩法' : game.variant === 'no_shuffle' ? '不洗牌玩法' : '经典玩法' }}</span>
      <strong class="multiplier-chip">倍数 <b>×{{ game.multiplier ?? 1 }}</b></strong>
      <em v-if="game.wildLabel" class="wild-chip">癞子：{{ game.wildLabel }}</em>
    </header>

    <section class="landlord-felt" aria-label="斗地主牌桌">
      <div class="felt-ring" aria-hidden="true" />

      <div class="opponent-row">
        <article
          v-for="(player, index) in otherPlayers"
          :key="player.id"
          class="opponent"
          :class="[`opponent-${index + 1}`, { active: game.currentPlayerId === player.id }]"
        >
          <span class="player-avatar">{{ player.name.slice(0, 1) }}</span>
          <div class="player-identity">
            <strong>{{ player.name }}</strong>
            <small :class="game.teams[player.id]">
              <Crown v-if="game.teams[player.id] === 'landlord'" :size="12" />
              {{ teamLabel(game.teams[player.id]) }}
            </small>
          </div>
          <div class="opponent-card-stack" aria-hidden="true"><i /><i /><i /></div>
          <b class="card-count">{{ game.cardCounts[player.id] ?? 17 }}<small>张</small></b>
          <em v-if="game.currentPlayerId === player.id">正在操作</em>
        </article>
      </div>

      <div v-if="game.bottomCards.length" class="bottom-cards">
        <span>底牌</span>
        <b
          v-for="card in game.bottomCards"
          :key="card.id"
          :class="{ red: isRed(card), wild: isWild(card) }"
        >{{ card.label }}{{ suitSymbol(card.suit) }}</b>
      </div>

      <div class="table-center">
        <template v-if="game.lastPlay">
          <small>{{ lastPlayerName }} · {{ game.lastPlay.pattern.label ?? '出牌' }}</small>
          <div class="played-cards">
            <span
              v-for="card in game.lastPlay.cards"
              :key="card.id"
              :class="{ red: isRed(card), wild: isWild(card) }"
            ><b>{{ card.label }}</b><i>{{ suitSymbol(card.suit) }}</i></span>
          </div>
        </template>
        <p v-else>
          {{ snapshot.phase === 'bidding' ? '等待确定地主' : isMyTurn ? '轮到你出牌' : `等待${currentPlayer?.name ?? '玩家'}出牌` }}
        </p>
        <em v-if="latestPassName" class="pass-bubble">{{ latestPassName }} 不出</em>
      </div>

      <article class="self-seat" :class="{ active: isMyTurn }">
        <span class="player-avatar">{{ snapshot.self.name.slice(0, 1) }}</span>
        <div>
          <strong>{{ snapshot.self.name }}</strong>
          <small :class="selfTeam">
            <Crown v-if="selfTeam === 'landlord'" :size="12" />
            {{ teamLabel(selfTeam) }} · {{ game.hand.length }} 张
          </small>
        </div>
        <em v-if="isMyTurn">轮到你</em>
      </article>

      <div v-if="snapshot.phase === 'bidding'" class="bid-panel">
        <small>地主竞选</small>
        <strong v-if="isMyTurn">
          {{ !usesDecisionBidding || game.biddingMode === 'call' ? '轮到你叫地主' : `是否抢 ${candidateName} 的地主？` }}
        </strong>
        <strong v-else>等待其他玩家{{ !usesDecisionBidding || game.biddingMode === 'call' ? '叫地主' : '抢地主' }}</strong>
        <div v-if="isMyTurn && usesDecisionBidding">
          <button type="button" :disabled="arcade.busy" @click="bid('pass')">{{ game.biddingMode === 'call' ? '不叫' : '不抢' }}</button>
          <button type="button" class="primary" :disabled="arcade.busy" @click="bid(game.biddingMode ?? 'call')">
            {{ game.biddingMode === 'call' ? '叫地主' : '抢地主 ×2' }}
          </button>
        </div>
        <div v-else-if="isMyTurn">
          <button type="button" :disabled="arcade.busy" @click="bidScore(0)">不叫</button>
          <button
            v-for="score in [1, 2, 3]"
            :key="score"
            type="button"
            :class="{ primary: score === 3 }"
            :disabled="arcade.busy || score <= (game.highestBid ?? 0)"
            @click="bidScore(score)"
          >{{ score }} 分</button>
        </div>
        <p v-if="game.bids.length">{{ game.bids.map((entry) => historyText(entry)).join(' · ') }}</p>
        <button type="button" class="arcade-danger-button" :disabled="arcade.busy" @click="arcade.action('resign')">
          <Flag :size="16" />退出本局
        </button>
      </div>
    </section>

    <section v-if="snapshot.phase !== 'bidding'" class="hand-zone" :class="{ active: isMyTurn }">
      <header class="self-hand-header">
        <div>
          <small>我的手牌</small>
          <strong>{{ teamLabel(selfTeam) }} · {{ game.hand.length }} 张</strong>
        </div>
        <span :class="{ active: isMyTurn }">{{ isMyTurn ? '轮到你出牌' : `等待${currentPlayer?.name ?? '对手'}` }}</span>
      </header>

      <div id="doudizhu-selection-hint" class="selection-feedback" :class="{ ready: selectedIds.length }" role="status" aria-live="polite">
        <b v-if="selectedPatternLabel">{{ selectedPatternLabel }}</b>
        <span>{{ selectionHint }}</span>
      </div>

      <div class="hand" :style="handGridStyle" aria-label="我的手牌">
        <button
          v-for="(card, index) in game.hand"
          :key="card.id"
          type="button"
          class="playing-card"
          :class="{ selected: selectedIds.includes(card.id), red: isRed(card), wild: isWild(card), joker: !card.suit }"
          :style="{ '--card-index': index }"
          :disabled="snapshot.phase !== 'playing' || arcade.busy"
          :aria-pressed="selectedIds.includes(card.id)"
          :aria-label="`${card.label}${suitSymbol(card.suit)}${isWild(card) ? '，癞子' : ''}`"
          @click="toggleCard(card.id)"
        >
          <b>{{ card.label }}</b>
          <span>{{ suitSymbol(card.suit) }}</span>
          <i aria-hidden="true">{{ suitSymbol(card.suit) || card.label.slice(0, 1) }}</i>
          <em v-if="isWild(card)">癞</em>
        </button>
      </div>

      <div v-if="snapshot.phase === 'playing'" class="play-actions" aria-describedby="doudizhu-selection-hint">
        <button type="button" :disabled="!canPass || arcade.busy" @click="arcade.action('pass')">不出</button>
        <button type="button" class="primary" :disabled="!isMyTurn || !selectedIds.length || arcade.busy" @click="play">
          出牌 <small v-if="selectedIds.length">{{ selectedIds.length }}</small>
        </button>
        <button type="button" class="arcade-danger-button" :disabled="arcade.busy" @click="arcade.action('resign')"><Flag :size="17" />认输</button>
      </div>
    </section>

    <section v-if="game.settlement" class="settlement-card">
      <header><strong>本局结算</strong><span>底分 {{ game.settlement.baseScore }} × 倍数 {{ game.settlement.multiplier }}</span></header>
      <p v-if="game.settlement.spring">{{ game.settlement.spring }}，倍数翻倍</p>
      <div>
        <span v-for="player in snapshot.players" :key="player.id">
          {{ player.name }} <b :class="{ gain: (game.scores?.[player.id] ?? 0) > 0 }">{{ (game.scores?.[player.id] ?? 0) > 0 ? '+' : '' }}{{ game.scores?.[player.id] ?? 0 }}</b>
        </span>
      </div>
    </section>

    <div v-if="game.history || game.remainingRanks" class="landlord-tools">
      <details class="history-panel">
        <summary><History :size="16" />完整记录（{{ normalizedHistory.length }}）</summary>
        <ol><li v-for="(entry, index) in normalizedHistory" :key="index">{{ historyText(entry) }}</li></ol>
      </details>
      <details class="counter-panel">
        <summary><ListOrdered :size="16" />记牌器</summary>
        <div><span v-for="rank in rankOrder" :key="rank"><b>{{ rankLabel(rank) }}</b>{{ game.remainingRanks?.[String(rank)] ?? 0 }}</span></div>
      </details>
    </div>
  </section>
</template>

<style scoped>
.landlord-table {
  width: min(100%, 1000px);
  margin: 0 auto;
  display: grid;
  gap: 14px;
  justify-items: center;
}
:global(.arcade-room:has(.landlord-table) .arcade-player-strip) { display: none; }
.landlord-rule-bar {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}
.rule-chip,
.multiplier-chip,
.wild-chip {
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 0 11px;
  color: var(--muted);
  background: color-mix(in srgb, var(--surface) 78%, transparent);
  font-size: 12px;
  font-style: normal;
  font-weight: 800;
}
.multiplier-chip { color: var(--text); }
.multiplier-chip b { margin-left: 5px; color: var(--gold); font-size: 15px; }
.wild-chip { border-color: color-mix(in srgb, #d65bc8 38%, var(--line)); color: #eda8e5; }
.landlord-felt {
  position: relative;
  isolation: isolate;
  width: 100%;
  min-height: clamp(390px, 49vw, 475px);
  overflow: hidden;
  border: 7px solid color-mix(in srgb, var(--gold) 34%, #4a2712);
  border-radius: clamp(34px, 8vw, 92px);
  background:
    radial-gradient(circle at 50% 40%, color-mix(in srgb, var(--green) 24%, transparent), transparent 48%),
    repeating-linear-gradient(117deg, rgba(255,255,255,.018) 0 1px, transparent 1px 5px),
    color-mix(in srgb, var(--surface-strong) 78%, #073c31);
  box-shadow:
    inset 0 0 0 2px rgba(255, 230, 171, .13),
    inset 0 0 80px rgba(0, 0, 0, .35),
    0 20px 54px rgba(0, 0, 0, .42);
}
.felt-ring {
  position: absolute;
  z-index: -1;
  inset: 14px;
  border: 1px solid color-mix(in srgb, var(--gold) 18%, transparent);
  border-radius: inherit;
}
.opponent-row { position: absolute; inset: 0; pointer-events: none; }
.opponent {
  position: absolute;
  top: clamp(58px, 8vw, 78px);
  width: min(31%, 250px);
  min-height: 92px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  grid-template-rows: auto auto;
  gap: 5px 9px;
  align-items: center;
  border: 1px solid color-mix(in srgb, var(--line) 78%, transparent);
  border-radius: 18px;
  padding: 10px;
  background: color-mix(in srgb, var(--surface-strong) 83%, transparent);
  box-shadow: 0 10px 24px rgba(0,0,0,.24);
  pointer-events: auto;
  transition: border-color .18s, box-shadow .18s, transform .18s;
}
.opponent-1 { left: clamp(16px, 4vw, 42px); }
.opponent-2 { right: clamp(16px, 4vw, 42px); }
.opponent.active {
  border-color: color-mix(in srgb, var(--gold) 72%, white);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--gold) 12%, transparent), 0 0 28px color-mix(in srgb, var(--gold) 25%, transparent);
  transform: translateY(-3px);
}
.player-avatar {
  grid-row: 1 / 3;
  width: 43px;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--gold) 30%, transparent);
  border-radius: 50%;
  color: var(--gold);
  background: color-mix(in srgb, var(--gold) 15%, var(--surface-strong));
  font-weight: 900;
}
.opponent.active .player-avatar,
.self-seat.active .player-avatar { animation: active-seat-pulse 1.6s ease-in-out infinite; }
@keyframes active-seat-pulse {
  50% { box-shadow: 0 0 0 6px color-mix(in srgb, var(--gold) 12%, transparent); }
}
.player-identity { min-width: 0; display: grid; gap: 4px; }
.player-identity strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.player-identity small,
.self-seat small {
  width: max-content;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  border-radius: 999px;
  padding: 2px 7px;
  color: var(--muted);
  background: rgba(0,0,0,.16);
  font-size: 10px;
}
.player-identity small.landlord,
.self-seat small.landlord { color: #ffe2a0; background: rgba(150, 93, 24, .28); }
.opponent-card-stack { position: relative; width: 29px; height: 42px; }
.opponent-card-stack i {
  position: absolute;
  inset: 0;
  border: 1px solid rgba(237, 218, 180, .5);
  border-radius: 4px;
  background: repeating-linear-gradient(45deg, #a43c3c 0 3px, #7b292e 3px 6px);
  box-shadow: 0 2px 5px rgba(0,0,0,.34);
}
.opponent-card-stack i:nth-child(1) { transform: translateX(-8px) rotate(-7deg); }
.opponent-card-stack i:nth-child(3) { transform: translateX(8px) rotate(7deg); }
.card-count { grid-column: 3; color: var(--gold); font-size: 18px; text-align: center; }
.card-count small { display: block; color: var(--muted); font-size: 9px; }
.opponent > em {
  grid-column: 2 / 4;
  color: #8cf1cb;
  font-size: 11px;
  font-style: normal;
  font-weight: 800;
}
.bottom-cards {
  position: absolute;
  z-index: 3;
  top: 14px;
  left: 50%;
  display: flex;
  align-items: center;
  gap: 5px;
  border: 1px solid color-mix(in srgb, var(--gold) 24%, transparent);
  border-radius: 10px;
  padding: 5px 7px;
  background: rgba(0, 0, 0, .2);
  transform: translateX(-50%);
}
.bottom-cards span { margin-right: 2px; color: var(--muted); font-size: 10px; }
.bottom-cards b {
  min-width: 30px;
  min-height: 38px;
  display: grid;
  place-items: center;
  border: 1px solid #cbbda5;
  border-radius: 5px;
  color: #20231f;
  background: linear-gradient(145deg, #fffdf8, #eee2ce);
  box-shadow: 0 3px 7px rgba(0,0,0,.28);
}
.table-center {
  position: absolute;
  z-index: 2;
  top: 46%;
  left: 50%;
  width: min(58%, 540px);
  min-height: 128px;
  display: grid;
  place-items: center;
  align-content: center;
  color: var(--muted);
  text-align: center;
  transform: translate(-50%, -50%);
}
.table-center > small { color: color-mix(in srgb, var(--text) 80%, var(--muted)); font-weight: 800; }
.table-center > p { margin: 0; color: color-mix(in srgb, var(--gold) 74%, var(--text)); font-weight: 850; }
.played-cards { max-width: 100%; display: flex; justify-content: center; margin-top: 9px; }
.played-cards span {
  position: relative;
  min-width: 45px;
  height: 66px;
  margin-left: -8px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  border: 1px solid #c8baa3;
  border-radius: 7px;
  padding: 6px;
  color: #20231f;
  background: linear-gradient(145deg, #fffef9, #eee4d2);
  box-shadow: 0 5px 10px rgba(0,0,0,.4);
}
.played-cards span:first-child { margin-left: 0; }
.played-cards span b { font-size: 16px; line-height: 1; }
.played-cards span i { font-size: 17px; font-style: normal; }
.pass-bubble {
  margin-top: 9px;
  border-radius: 999px;
  padding: 4px 9px;
  color: var(--muted);
  background: rgba(0,0,0,.18);
  font-size: 10px;
  font-style: normal;
}
.self-seat {
  position: absolute;
  z-index: 4;
  bottom: 18px;
  left: clamp(18px, 4vw, 42px);
  display: flex;
  align-items: center;
  gap: 9px;
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 8px 11px 8px 8px;
  background: color-mix(in srgb, var(--surface-strong) 88%, transparent);
  box-shadow: 0 8px 22px rgba(0,0,0,.25);
}
.self-seat > div { display: grid; gap: 4px; }
.self-seat > em { margin-left: 5px; color: var(--gold); font-size: 11px; font-style: normal; font-weight: 900; }
.self-seat.active { border-color: color-mix(in srgb, var(--gold) 68%, var(--line)); box-shadow: 0 0 26px color-mix(in srgb, var(--gold) 20%, transparent); }
.bid-panel {
  position: absolute;
  z-index: 5;
  right: clamp(18px, 4vw, 42px);
  bottom: 16px;
  width: min(58%, 530px);
  min-height: 112px;
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 8px 14px;
  border: 1px solid color-mix(in srgb, var(--gold) 32%, var(--line));
  border-radius: 18px;
  padding: 12px 14px;
  background: color-mix(in srgb, var(--surface-strong) 92%, transparent);
  box-shadow: 0 14px 34px rgba(0,0,0,.35);
}
.bid-panel > small { color: var(--gold); font-weight: 800; }
.bid-panel > strong { grid-column: 1 / 3; font-size: clamp(16px, 2.2vw, 22px); }
.bid-panel > div { display: flex; gap: 8px; }
.bid-panel > p { grid-column: 1 / 3; margin: 0; color: var(--muted); font-size: 10px; }
.bid-panel button:not(.arcade-danger-button),
.play-actions button:not(.arcade-danger-button) {
  min-height: 42px;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0 18px;
  color: var(--text);
  background: var(--surface);
  font-weight: 850;
}
.bid-panel button.primary,
.play-actions .primary {
  border-color: color-mix(in srgb, var(--green) 72%, white);
  color: #06231c;
  background: linear-gradient(135deg, color-mix(in srgb, var(--green) 82%, white), var(--green));
  box-shadow: 0 7px 18px color-mix(in srgb, var(--green) 22%, transparent);
}
.bid-panel button:disabled,
.play-actions button:disabled { opacity: .35; }
.hand-zone {
  width: 100%;
  display: grid;
  gap: 7px;
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 13px 15px 15px;
  background: color-mix(in srgb, var(--surface) 72%, transparent);
  box-shadow: 0 14px 34px rgba(0,0,0,.2);
  transition: border-color .18s, box-shadow .18s;
}
.hand-zone.active {
  border-color: color-mix(in srgb, var(--gold) 56%, var(--line));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--gold) 8%, transparent), 0 16px 36px rgba(0,0,0,.25);
}
.self-hand-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.self-hand-header > div { display: grid; }
.self-hand-header small { color: var(--muted); }
.self-hand-header > span {
  border-radius: 999px;
  padding: 6px 10px;
  color: var(--muted);
  background: rgba(0,0,0,.13);
  font-size: 11px;
  font-weight: 800;
}
.self-hand-header > span.active { color: #06231c; background: var(--green); }
.selection-feedback {
  min-height: 33px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border-radius: 10px;
  padding: 6px 10px;
  color: var(--muted);
  background: rgba(0,0,0,.1);
  text-align: center;
  font-size: 11px;
}
.selection-feedback.ready { color: var(--text); background: color-mix(in srgb, var(--gold) 8%, transparent); }
.selection-feedback b { border-radius: 999px; padding: 3px 7px; color: #37270b; background: var(--gold); }
.hand {
  --hand-count: 1;
  width: 100%;
  min-height: 142px;
  display: grid;
  grid-template-columns: repeat(var(--hand-count), minmax(0, 1fr));
  align-items: end;
  padding: 30px 34px 7px;
}
.playing-card {
  --card-index: 0;
  position: relative;
  z-index: calc(var(--card-index) + 1);
  width: clamp(49px, 6.4vw, 65px);
  height: clamp(94px, 11vw, 121px);
  min-width: 0;
  justify-self: center;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  overflow: hidden;
  border: 1px solid #c8baa3;
  border-radius: 9px;
  padding: 8px 5px;
  color: #1d211e;
  background:
    linear-gradient(145deg, rgba(255,255,255,.82), transparent 48%),
    #f3ead9;
  box-shadow: 0 5px 12px rgba(0,0,0,.52), inset 0 0 0 1px rgba(255,255,255,.55);
  transform-origin: bottom center;
  transition: transform .15s ease, border-color .15s, box-shadow .15s, filter .15s;
}
.playing-card:not(:disabled) { cursor: pointer; }
.playing-card:disabled { opacity: 1; }
.playing-card:hover:not(:disabled) { transform: translateY(-7px); }
.playing-card.selected {
  z-index: 80;
  overflow: visible;
  border-color: #f1c65c;
  box-shadow: 0 9px 18px rgba(0,0,0,.55), 0 0 0 3px rgba(241,198,92,.38), 0 0 22px rgba(241,198,92,.35);
  transform: translateY(-22px) scale(1.035);
}
.playing-card b { font-size: clamp(17px, 2vw, 21px); line-height: 1; }
.playing-card > span { font-size: clamp(18px, 2.2vw, 24px); line-height: 1; }
.playing-card > i {
  position: absolute;
  right: 3px;
  bottom: -5px;
  color: currentColor;
  font-size: clamp(28px, 4vw, 46px);
  font-style: normal;
  opacity: .13;
}
.playing-card > em { position: absolute; right: 4px; bottom: 4px; color: #a42691; font-style: normal; font-weight: 900; }
.playing-card.joker b { font-size: clamp(13px, 1.7vw, 17px); writing-mode: vertical-rl; letter-spacing: .08em; }
.playing-card.joker > i { font-size: 34px; }
.red { color: #bd312e !important; }
.wild { box-shadow: 0 0 0 2px #c854bd, 0 5px 13px rgba(0,0,0,.5) !important; }
.play-actions { display: flex; justify-content: center; gap: 8px; padding-top: 3px; }
.play-actions .primary { min-width: 124px; }
.play-actions .primary small {
  min-width: 19px;
  height: 19px;
  display: inline-grid;
  place-items: center;
  margin-left: 4px;
  border-radius: 999px;
  color: var(--green);
  background: #06231c;
}
.settlement-card { width: min(100%, 620px); display: grid; gap: 10px; border: 1px solid color-mix(in srgb, var(--gold) 45%, var(--line)); border-radius: 16px; padding: 15px; background: var(--surface); }
.settlement-card header,
.settlement-card > div { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 9px 16px; }
.settlement-card p { margin: 0; color: var(--gold); }
.settlement-card b { color: var(--red); }
.settlement-card b.gain { color: var(--green); }
.landlord-tools { width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.landlord-tools details { border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; background: rgba(0,0,0,.1); }
.landlord-tools summary { display: flex; align-items: center; gap: 7px; cursor: pointer; color: var(--gold); font-weight: 800; }
.history-panel ol { max-height: 260px; overflow: auto; margin: 10px 0 0; padding-left: 25px; color: var(--muted); }
.history-panel li { margin: 5px 0; }
.counter-panel > div { display: grid; grid-template-columns: repeat(5, 1fr); gap: 7px; margin-top: 10px; }
.counter-panel span { display: grid; place-items: center; border-radius: 7px; padding: 5px; background: var(--surface); color: var(--muted); }
.counter-panel b { color: var(--text); }
@media (max-width: 700px) {
  .landlord-table { gap: 11px; }
  .landlord-felt { min-height: 330px; border-width: 5px; border-radius: 34px; }
  .opponent { top: 49px; width: calc(50% - 22px); min-height: 76px; grid-template-columns: auto minmax(0,1fr) auto; gap: 3px 6px; padding: 7px; border-radius: 13px; }
  .opponent-1 { left: 9px; }
  .opponent-2 { right: 9px; }
  .player-avatar { width: 34px; }
  .opponent-card-stack { width: 21px; height: 32px; }
  .opponent-card-stack i:nth-child(1) { transform: translateX(-5px) rotate(-6deg); }
  .opponent-card-stack i:nth-child(3) { transform: translateX(5px) rotate(6deg); }
  .card-count { font-size: 15px; }
  .player-identity strong { font-size: 12px; }
  .table-center { top: 53%; width: 80%; min-height: 100px; }
  .played-cards span { min-width: 38px; height: 57px; margin-left: -12px; padding: 5px; }
  .bottom-cards { top: 7px; padding: 3px 5px; }
  .bottom-cards b { min-width: 25px; min-height: 31px; font-size: 11px; }
  .self-seat { bottom: 9px; left: 10px; max-width: calc(100% - 20px); padding: 6px 9px 6px 6px; }
  .self-seat > em { display: none; }
  .landlord-felt:has(.bid-panel) .self-seat { display: none; }
  .bid-panel { right: 9px; bottom: 9px; left: 9px; width: auto; min-height: 108px; grid-template-columns: 1fr auto; border-radius: 14px; padding: 10px; }
  .bid-panel > strong { font-size: 16px; }
  .bid-panel > p { max-height: 28px; overflow: auto; }
  .bid-panel button:not(.arcade-danger-button) { min-height: 38px; padding: 0 12px; }
  .hand-zone { border-radius: 16px; padding: 11px 8px 10px; }
  .self-hand-header { padding: 0 3px; }
  .selection-feedback { align-items: flex-start; flex-direction: column; gap: 2px; text-align: left; }
  .hand { min-height: 126px; padding: 29px 24px 6px; }
  .playing-card { width: 50px; height: 102px; padding: 7px 4px; }
  .playing-card.selected { transform: translateY(-19px) scale(1.025); }
  .play-actions {
    position: sticky;
    z-index: 45;
    bottom: calc(8px + env(safe-area-inset-bottom));
    flex-wrap: wrap;
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 7px;
    background: color-mix(in srgb, var(--surface-strong) 93%, transparent);
    box-shadow: 0 8px 24px rgba(0,0,0,.38);
    backdrop-filter: blur(14px);
  }
  .play-actions button:not(.arcade-danger-button) { min-height: 40px; padding: 0 15px; }
  .play-actions .primary { min-width: 112px; }
  .landlord-tools { grid-template-columns: 1fr; }
  .counter-panel > div { grid-template-columns: repeat(5, 1fr); }
}
@media (prefers-reduced-motion: reduce) {
  .opponent.active .player-avatar,
  .self-seat.active .player-avatar { animation: none; }
}
</style>
