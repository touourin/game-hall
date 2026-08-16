<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Crown, Flag } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import UiButton from '../../components/ui/UiButton.vue'
import AvatarImage from '../../components/AvatarImage.vue'
import PlayingCard from '../shared/cards/PlayingCard.vue'
import GameHistoryPanel from '../shared/history/GameHistoryPanel.vue'

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

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const selectedIds = ref<string[]>([])
const game = computed(() => props.snapshot.game as {
  phase: string
  variant: 'classic' | 'laizi' | 'no_shuffle'
  currentPlayerId: string | null
  bids: HistoryEntry[]
  biddingMode: 'call' | 'rob'
  landlordCandidatePlayerId: string | null
  landlordPlayerId: string | null
  bottomCards: PlayingCard[]
  hand: PlayingCard[]
  cardCounts: Record<string, number>
  teams: Record<string, 'landlord' | 'farmer'>
  lastPlay: { cards: PlayingCard[]; pattern: { kind: string; label?: string } } | null
  lastPlayPlayerId: string | null
  multiplier: number
  multiplierEvents: Array<{ reason: string; multiplier: number }>
  wildRank: number | null
  wildLabel: string | null
  history: HistoryEntry[]
  scores: Record<string, number>
  settlement: { baseScore: number; multiplier: number; spring: string | null } | null
})
const isMyTurn = computed(
  () => game.value.currentPlayerId === props.snapshot.self.id,
)
const otherPlayers = computed(() => {
  const { players, self } = props.snapshot
  const seatCount = players.length
  return players
    .filter((player) => player.id !== self.id)
    .sort((left, right) => {
      const leftDistance = (left.seat - self.seat + seatCount) % seatCount
      const rightDistance = (right.seat - self.seat + seatCount) % seatCount
      return leftDistance - rightDistance
    })
})
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
const normalizedHistory = computed(() => game.value.history)
const historyEntries = computed(() => normalizedHistory.value.map((entry) => historyText(entry)))
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

function aiDifficultyLabel(difficulty?: string | null): string {
  return difficulty === 'douzero' ? 'DouZero' : difficulty || 'DouZero'
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
  if (cards.length >= 8 && cards.length % 4 === 0) {
    const sequenceLength = cards.length / 4
    for (const sequence of tripleSequences(counts, sequenceLength)) {
      const remaining = remainingCounts(counts, sequence)
      if (
        [...remaining.values()].reduce((total, count) => total + count, 0) === sequenceLength
        && [...remaining.keys()].every((rank) => !sequence.includes(rank))
      ) return '飞机带单'
    }
  }
  if (cards.length >= 10 && cards.length % 5 === 0) {
    const sequenceLength = cards.length / 5
    for (const sequence of tripleSequences(counts, sequenceLength)) {
      const remaining = remainingCounts(counts, sequence)
      if (
        remaining.size === sequenceLength
        && [...remaining.values()].every((count) => count === 2)
      ) return '飞机带对'
    }
  }
  if (cards.length === 6 && quantities[0] === 4) return '四带二'
  if (cards.length === 8 && quantities[0] === 4 && quantities.slice(1).every((count) => count === 2)) return '四带两对'
  return ''
}

function tripleSequences(counts: ReadonlyMap<number, number>, length: number): number[][] {
  if (length < 2) return []
  const tripleRanks = [...counts.entries()]
    .filter(([rank, count]) => rank <= 14 && count >= 3)
    .map(([rank]) => rank)
    .sort((left, right) => left - right)
  const sequences: number[][] = []
  for (let start = 0; start <= tripleRanks.length - length; start += 1) {
    const sequence = tripleRanks.slice(start, start + length)
    if (sequence.every((rank, index) => index === 0 || rank === sequence[index - 1]! + 1)) {
      sequences.push(sequence)
    }
  }
  return sequences
}

function remainingCounts(
  counts: ReadonlyMap<number, number>,
  sequence: number[],
): Map<number, number> {
  const remaining = new Map(counts)
  for (const rank of sequence) {
    const count = (remaining.get(rank) ?? 0) - 3
    if (count > 0) remaining.set(rank, count)
    else remaining.delete(rank)
  }
  return remaining
}

function historyText(entry: HistoryEntry): string {
  if (entry.type === 'landlord') return `${entry.playerName} 成为地主`
  if (entry.type === 'pass' || entry.decision === 'pass') {
    return `${entry.playerName} ${entry.type === 'bid' ? '不叫／不抢' : '不出'}`
  }
  if (entry.type === 'bid') {
    return `${entry.playerName} ${entry.decision === 'call' ? '叫地主' : '抢地主'}`
  }
  return `${entry.playerName} · ${entry.pattern?.label ?? '出牌'} · ${entry.cards?.map((card) => card.label).join(' ') ?? ''}`
}

</script>

<template>
  <section class="landlord-table" :class="{ 'is-my-turn': isMyTurn }">
    <header class="landlord-rule-bar">
      <span class="rule-chip">{{ game.variant === 'laizi' ? '癞子玩法' : game.variant === 'no_shuffle' ? '不洗牌玩法' : '经典玩法' }}</span>
      <strong class="multiplier-chip">倍数 <b>×{{ game.multiplier }}</b></strong>
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
          <AvatarImage class="player-avatar" :src="player.avatarUrl" :name="player.name" />
          <div class="player-identity">
            <strong>
              {{ player.name }}
              <i v-if="player.isBot" class="ai-badge">AI · {{ aiDifficultyLabel(player.botDifficulty) }}</i>
            </strong>
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
        <PlayingCard
          v-for="card in game.bottomCards"
          :key="card.id"
          :rank="card.label"
          :suit="suitSymbol(card.suit)"
          :red="isRed(card)"
          :wild="isWild(card)"
          size="bottom"
        />
      </div>

      <div class="table-center">
        <template v-if="game.lastPlay">
          <small>{{ lastPlayerName }} · {{ game.lastPlay.pattern.label ?? '出牌' }}</small>
          <div class="played-cards">
            <PlayingCard
              v-for="card in game.lastPlay.cards"
              :key="card.id"
              :rank="card.label"
              :suit="suitSymbol(card.suit)"
              :red="isRed(card)"
              :wild="isWild(card)"
              size="compact"
            />
          </div>
        </template>
        <p v-else>
          {{ snapshot.phase === 'bidding' ? '等待确定地主' : isMyTurn ? '轮到你出牌' : `等待${currentPlayer?.name ?? '玩家'}出牌` }}
        </p>
        <em v-if="latestPassName" class="pass-bubble">{{ latestPassName }} 不出</em>
      </div>

      <article class="self-seat" :class="{ active: isMyTurn }">
        <AvatarImage class="player-avatar" :src="snapshot.self.avatarUrl" :name="snapshot.self.name" />
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
          {{ game.biddingMode === 'call' ? '轮到你叫地主' : `是否抢 ${candidateName} 的地主？` }}
        </strong>
        <strong v-else>等待其他玩家{{ game.biddingMode === 'call' ? '叫地主' : '抢地主' }}</strong>
        <div v-if="isMyTurn">
          <button type="button" :disabled="arcade.busy" @click="bid('pass')">{{ game.biddingMode === 'call' ? '不叫' : '不抢' }}</button>
          <button type="button" class="primary" :disabled="arcade.busy" @click="bid(game.biddingMode)">
            {{ game.biddingMode === 'call' ? '叫地主' : '抢地主 ×2' }}
          </button>
        </div>
        <p v-if="game.bids.length">{{ game.bids.map((entry) => historyText(entry)).join(' · ') }}</p>
        <UiButton variant="danger" compact :disabled="arcade.busy" @click="arcade.action('resign')">
          <Flag :size="16" />退出本局
        </UiButton>
      </div>
    </section>

    <section
      v-if="game.hand.length || snapshot.phase === 'playing'"
      class="hand-zone"
      :class="{ active: snapshot.phase === 'playing' && isMyTurn }"
    >
      <header class="self-hand-header">
        <div>
          <small>我的手牌</small>
          <strong>{{ snapshot.phase === 'bidding' ? '地主竞选' : teamLabel(selfTeam) }} · {{ game.hand.length }} 张</strong>
        </div>
        <span v-if="snapshot.phase === 'bidding'" :class="{ active: isMyTurn }">
          {{ isMyTurn ? (game.biddingMode === 'call' ? '请看牌后决定是否叫地主' : '请看牌后决定是否抢地主') : `等待${currentPlayer?.name ?? '其他玩家'}${game.biddingMode === 'call' ? '叫地主' : '抢地主'}` }}
        </span>
        <span v-else :class="{ active: isMyTurn }">{{ isMyTurn ? '轮到你出牌' : `等待${currentPlayer?.name ?? '对手'}` }}</span>
      </header>

      <div v-if="snapshot.phase === 'playing'" id="doudizhu-selection-hint" class="selection-feedback" :class="{ ready: selectedIds.length }" role="status" aria-live="polite">
        <b v-if="selectedPatternLabel">{{ selectedPatternLabel }}</b>
        <span>{{ selectionHint }}</span>
      </div>

      <div class="hand" :style="handGridStyle" aria-label="我的手牌">
        <PlayingCard
          v-for="(card, index) in game.hand"
          :key="card.id"
          :style="{ '--card-index': index }"
          :rank="card.label"
          :suit="suitSymbol(card.suit)"
          :red="isRed(card)"
          :wild="isWild(card)"
          :joker="!card.suit"
          :selected="selectedIds.includes(card.id)"
          interactive
          size="hand"
          :disabled="snapshot.phase !== 'playing' || arcade.busy"
          :aria-label="`${card.label}${suitSymbol(card.suit)}${isWild(card) ? '，癞子' : ''}`"
          @select="toggleCard(card.id)"
        />
      </div>

      <div v-if="snapshot.phase === 'playing'" class="play-actions" aria-describedby="doudizhu-selection-hint">
        <button type="button" :disabled="!canPass || arcade.busy" @click="arcade.action('pass')">不出</button>
        <button type="button" class="primary" :disabled="!isMyTurn || !selectedIds.length || arcade.busy" @click="play">
          出牌 <small v-if="selectedIds.length">{{ selectedIds.length }}</small>
        </button>
        <UiButton variant="danger" compact :disabled="arcade.busy" @click="arcade.action('resign')"><Flag :size="17" />认输</UiButton>
      </div>
    </section>

    <section v-if="game.settlement" class="settlement-card">
      <header><strong>本局结算</strong><span>底分 {{ game.settlement.baseScore }} × 倍数 {{ game.settlement.multiplier }}</span></header>
      <p v-if="game.settlement.spring">{{ game.settlement.spring }}，倍数翻倍</p>
      <div>
        <span v-for="player in snapshot.players" :key="player.id">
          {{ player.name }} <b :class="{ gain: (game.scores[player.id] ?? 0) > 0 }">{{ (game.scores[player.id] ?? 0) > 0 ? '+' : '' }}{{ game.scores[player.id] ?? 0 }}</b>
        </span>
      </div>
    </section>

    <div class="landlord-tools">
      <GameHistoryPanel class="history-panel" title="完整记录" :entries="historyEntries" />
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
.multiplier-chip b { margin-left: 5px; color: var(--accent); font-size: 15px; }
.wild-chip { border-color: color-mix(in srgb, #d65bc8 38%, var(--line)); color: #eda8e5; }
.landlord-felt {
  position: relative;
  isolation: isolate;
  width: 100%;
  min-height: clamp(390px, 49vw, 475px);
  overflow: hidden;
  border: 7px solid var(--game-felt-border, color-mix(in srgb, var(--accent) 34%, #4a2712));
  border-radius: clamp(34px, 8vw, 92px);
  background: var(--game-felt-surface, radial-gradient(circle at 50% 40%, #176348, #073c31));
  box-shadow:
    inset 0 0 0 2px color-mix(in srgb, var(--game-felt-highlight, #ffe6ab) 42%, transparent),
    inset 0 0 80px rgba(0, 0, 0, .35),
    0 20px 54px rgba(0, 0, 0, .42);
}
.felt-ring {
  position: absolute;
  z-index: -1;
  inset: 14px;
  border: 1px solid color-mix(in srgb, var(--accent) 18%, transparent);
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
  background: var(--game-seat-surface, color-mix(in srgb, var(--surface-strong) 83%, transparent));
  box-shadow: 0 10px 24px rgba(0,0,0,.24);
  pointer-events: auto;
  transition: border-color .18s, box-shadow .18s, transform .18s;
}
.opponent-1 { left: clamp(16px, 4vw, 42px); }
.opponent-2 { right: clamp(16px, 4vw, 42px); }
.opponent.active {
  border-color: color-mix(in srgb, var(--accent) 72%, white);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 12%, transparent), 0 0 28px color-mix(in srgb, var(--accent) 25%, transparent);
  transform: translateY(-3px);
}
.player-avatar {
  grid-row: 1 / 3;
  width: 43px;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
  border-radius: 50%;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 15%, var(--surface-strong));
  font-weight: 900;
}
.opponent.active .player-avatar,
.self-seat.active .player-avatar { animation: active-seat-pulse 1.6s ease-in-out infinite; }
@keyframes active-seat-pulse {
  50% { box-shadow: 0 0 0 6px color-mix(in srgb, var(--accent) 12%, transparent); }
}
.player-identity { min-width: 0; display: grid; gap: 4px; }
.player-identity strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ai-badge { margin-left: 4px; border-radius: 999px; padding: 2px 5px; color: var(--accent); background: color-mix(in srgb, var(--accent) 13%, transparent); font-size: 8px; font-style: normal; font-weight: 900; }
.player-identity small,
.self-seat small {
  width: max-content;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  border-radius: 999px;
  padding: 2px 7px;
  color: var(--muted);
  background: var(--surface-inset);
  font-size: 10px;
}
.player-identity small.landlord,
.self-seat small.landlord { color: color-mix(in srgb, var(--accent) 78%, var(--text)); background: color-mix(in srgb, var(--accent) 16%, var(--surface-inset)); }
.opponent-card-stack { position: relative; width: 29px; height: 42px; }
.opponent-card-stack i {
  position: absolute;
  inset: 0;
  border: 1px solid color-mix(in srgb, var(--game-card-back-accent, #eddab4) 58%, transparent);
  border-radius: 4px;
  background: var(--game-card-back, repeating-linear-gradient(45deg, #a43c3c 0 3px, #7b292e 3px 6px));
  box-shadow: 0 2px 5px rgba(0,0,0,.34);
}
.opponent-card-stack i:nth-child(1) { transform: translateX(-8px) rotate(-7deg); }
.opponent-card-stack i:nth-child(3) { transform: translateX(8px) rotate(7deg); }
.card-count { grid-column: 3; color: var(--accent); font-size: 18px; text-align: center; }
.card-count small { display: block; color: var(--muted); font-size: 9px; }
.opponent > em {
  grid-column: 2 / 4;
  color: var(--green);
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
  border: 1px solid color-mix(in srgb, var(--accent) 24%, transparent);
  border-radius: 10px;
  padding: 5px 7px;
  background: color-mix(in srgb, var(--surface-inset) 82%, transparent);
  transform: translateX(-50%);
}
.bottom-cards > span:not(.playing-card) { margin-right: 2px; color: var(--muted); font-size: 10px; }
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
.table-center > p { margin: 0; color: color-mix(in srgb, var(--accent) 74%, var(--text)); font-weight: 850; }
.played-cards { max-width: 100%; display: flex; justify-content: center; margin-top: 9px; }
.played-cards .playing-card + .playing-card { margin-left: -8px; }
.pass-bubble {
  margin-top: 9px;
  border-radius: 999px;
  padding: 4px 9px;
  color: var(--muted);
  background: var(--surface-inset);
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
  background: var(--game-seat-surface, color-mix(in srgb, var(--surface-strong) 88%, transparent));
  box-shadow: 0 8px 22px rgba(0,0,0,.25);
}
.self-seat > div { display: grid; gap: 4px; }
.self-seat > em { margin-left: 5px; color: var(--accent); font-size: 11px; font-style: normal; font-weight: 900; }
.self-seat.active { border-color: color-mix(in srgb, var(--accent) 68%, var(--line)); box-shadow: 0 0 26px color-mix(in srgb, var(--accent) 20%, transparent); }
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
  border: 1px solid color-mix(in srgb, var(--accent) 32%, var(--line));
  border-radius: 18px;
  padding: 12px 14px;
  background: color-mix(in srgb, var(--surface-strong) 92%, transparent);
  box-shadow: 0 14px 34px rgba(0,0,0,.35);
}
.bid-panel > small { color: var(--accent); font-weight: 800; }
.bid-panel > strong { grid-column: 1 / 3; font-size: clamp(16px, 2.2vw, 22px); }
.bid-panel > div { display: flex; gap: 8px; }
.bid-panel > p { grid-column: 1 / 3; margin: 0; color: var(--muted); font-size: 10px; }
.bid-panel button:not(.ui-button--danger),
.play-actions button:not(.ui-button--danger) {
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
  color: var(--accent-contrast);
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
  box-shadow: var(--shadow-contact);
  transition: border-color .18s, box-shadow .18s;
}
.hand-zone.active {
  border-color: color-mix(in srgb, var(--accent) 56%, var(--line));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 8%, transparent), 0 16px 36px rgba(0,0,0,.25);
}
.self-hand-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.self-hand-header > div { display: grid; }
.self-hand-header small { color: var(--muted); }
.self-hand-header > span {
  border-radius: 999px;
  padding: 6px 10px;
  color: var(--muted);
  background: var(--surface-inset);
  font-size: 11px;
  font-weight: 800;
}
.self-hand-header > span.active { color: var(--accent-contrast); background: var(--green); }
.selection-feedback {
  min-height: 33px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border-radius: 10px;
  padding: 6px 10px;
  color: var(--muted);
  background: var(--surface-inset);
  text-align: center;
  font-size: 11px;
}
.selection-feedback.ready { color: var(--text); background: color-mix(in srgb, var(--accent) 8%, transparent); }
.selection-feedback b { border-radius: 999px; padding: 3px 7px; color: var(--accent-contrast); background: var(--accent); }
.hand {
  --hand-count: 1;
  width: 100%;
  min-height: 142px;
  display: grid;
  grid-template-columns: repeat(var(--hand-count), minmax(0, 1fr));
  align-items: end;
  padding: 30px 34px 7px;
}
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
  background: var(--surface-inset);
}
.settlement-card { width: min(100%, 620px); display: grid; gap: 10px; border: 1px solid color-mix(in srgb, var(--accent) 45%, var(--line)); border-radius: 16px; padding: 15px; background: var(--surface); }
.settlement-card header,
.settlement-card > div { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 9px 16px; }
.settlement-card p { margin: 0; color: var(--accent); }
.settlement-card b { color: var(--red); }
.settlement-card b.gain { color: var(--green); }
.landlord-tools { width: 100%; display: grid; grid-template-columns: 1fr; gap: 10px; }
.landlord-tools details { border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; background: var(--surface-inset); }
.landlord-tools summary { display: flex; align-items: center; gap: 7px; cursor: pointer; color: var(--accent); font-weight: 800; }
.history-panel { --game-history-max-height: 260px; }
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
  .played-cards .playing-card { width: 38px; height: 57px; padding: 5px; }
  .played-cards .playing-card + .playing-card { margin-left: -12px; }
  .bottom-cards { top: 7px; padding: 3px 5px; }
  .bottom-cards .playing-card { width: 25px; height: 31px; }
  .self-seat { bottom: 9px; left: 10px; max-width: calc(100% - 20px); padding: 6px 9px 6px 6px; }
  .self-seat > em { display: none; }
  .landlord-felt:has(.bid-panel) .self-seat { display: none; }
  .bid-panel { right: 9px; bottom: 9px; left: 9px; width: auto; min-height: 108px; grid-template-columns: 1fr auto; border-radius: 14px; padding: 10px; }
  .bid-panel > strong { font-size: 16px; }
  .bid-panel > p { max-height: 28px; overflow: auto; }
  .bid-panel button:not(.ui-button--danger) { min-height: 38px; padding: 0 12px; }
  .hand-zone { border-radius: 16px; padding: 11px 8px 10px; }
  .self-hand-header { padding: 0 3px; }
  .selection-feedback { align-items: flex-start; flex-direction: column; gap: 2px; text-align: left; }
  .hand { min-height: 126px; padding: 29px 24px 6px; }
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
  .play-actions button:not(.ui-button--danger) { min-height: 40px; padding: 0 15px; }
  .play-actions .primary { min-width: 112px; }
}
@media (prefers-reduced-motion: reduce) {
  .opponent.active .player-avatar,
  .self-seat.active .player-avatar { animation: none; }
}
</style>
