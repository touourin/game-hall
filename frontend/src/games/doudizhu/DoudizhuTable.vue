<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Flag } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'

interface PlayingCard {
  id: string
  rank: number
  label: string
  suit: 'spade' | 'heart' | 'club' | 'diamond' | null
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const selectedIds = ref<string[]>([])
const game = computed(() => props.snapshot.game as {
  phase: string
  currentPlayerId: string | null
  bids: Array<{ seat: number; score: number }>
  highestBid: number
  landlordPlayerId: string | null
  bottomCards: PlayingCard[]
  hand: PlayingCard[]
  cardCounts: Record<string, number>
  teams: Record<string, 'landlord' | 'farmer'>
  lastPlay: { cards: PlayingCard[]; pattern: { kind: string } } | null
  lastPlayPlayerId: string | null
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
const selfTeam = computed(() => game.value.teams[props.snapshot.self.id])

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

function suitSymbol(suit: PlayingCard['suit']): string {
  if (!suit) return ''
  const symbols: Record<string, string> = {
    spade: '♠',
    heart: '♥',
    club: '♣',
    diamond: '♦',
  }
  return symbols[suit] ?? ''
}

function isRed(card: PlayingCard): boolean {
  return card.suit === 'heart' || card.suit === 'diamond' || card.rank === 17
}
</script>

<template>
  <section class="landlord-table">
    <div class="opponent-row">
      <article v-for="player in otherPlayers" :key="player.id" class="opponent">
        <span class="player-avatar">{{ player.name.slice(0, 1) }}</span>
        <strong>{{ player.name }}</strong>
        <small v-if="game.teams[player.id]">
          {{ game.teams[player.id] === 'landlord' ? '地主' : '农民' }}
        </small>
        <b>{{ game.cardCounts[player.id] ?? 17 }} 张</b>
        <em v-if="game.currentPlayerId === player.id">正在操作</em>
      </article>
    </div>

    <div v-if="game.bottomCards.length" class="bottom-cards">
      <span>
        你是{{ selfTeam === 'landlord' ? '地主' : '农民' }} · 底牌
      </span>
      <b
        v-for="card in game.bottomCards"
        :key="card.id"
        :class="{ red: isRed(card) }"
      >{{ card.label }}{{ suitSymbol(card.suit) }}</b>
    </div>

    <div class="table-center">
      <template v-if="game.lastPlay">
        <small>{{ lastPlayerName }} 出牌</small>
        <div class="played-cards">
          <span
            v-for="card in game.lastPlay.cards"
            :key="card.id"
            :class="{ red: isRed(card) }"
          >
            <b>{{ card.label }}</b>{{ suitSymbol(card.suit) }}
          </span>
        </div>
      </template>
      <p v-else>
        {{ snapshot.phase === 'bidding' ? '等待确定地主' : isMyTurn ? '请出牌' : '等待玩家出牌' }}
      </p>
    </div>

    <div v-if="snapshot.phase === 'bidding'" class="bid-panel">
      <strong>{{ isMyTurn ? '轮到你叫地主' : '等待其他玩家叫地主' }}</strong>
      <div v-if="isMyTurn">
        <button type="button" @click="arcade.action('bid', { score: 0 })">不叫</button>
        <button
          v-for="score in [1, 2, 3]"
          :key="score"
          type="button"
          :disabled="score <= game.highestBid"
          @click="arcade.action('bid', { score })"
        >
          {{ score }} 分
        </button>
      </div>
      <small v-if="game.bids.length">
        已叫：{{ game.bids.map((bid) => `${bid.seat + 1}号 ${bid.score || '不叫'}`).join(' · ') }}
      </small>
    </div>

    <template v-else>
      <div class="hand" aria-label="我的手牌">
        <button
          v-for="card in game.hand"
          :key="card.id"
          type="button"
          class="playing-card"
          :class="{ selected: selectedIds.includes(card.id), red: isRed(card) }"
          @click="toggleCard(card.id)"
        >
          <b>{{ card.label }}</b>
          <span>{{ suitSymbol(card.suit) }}</span>
        </button>
      </div>
      <div v-if="snapshot.phase === 'playing'" class="play-actions">
        <button type="button" :disabled="!isMyTurn" @click="arcade.action('pass')">不出</button>
        <button
          type="button"
          class="primary"
          :disabled="!isMyTurn || !selectedIds.length"
          @click="play"
        >
          出牌
        </button>
        <button type="button" class="arcade-danger-button" @click="arcade.action('resign')"><Flag :size="17" />认输</button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.landlord-table { width: min(100%, 1000px); margin: 0 auto; display: grid; gap: 18px; justify-items: center; }
.opponent-row { width: 100%; display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.opponent { display: grid; grid-template-columns: auto 1fr auto; gap: 2px 10px; align-items: center; padding: 12px; border: 1px solid var(--line); border-radius: 14px; background: var(--surface); }
.player-avatar { grid-row: span 3; width: 38px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 50%; color: var(--gold); background: color-mix(in srgb, var(--gold) 19%, transparent); }
.opponent small, .opponent em { color: var(--muted); font-style: normal; }
.opponent b { grid-column: 3; grid-row: 1 / 3; color: var(--gold); }
.opponent em { grid-column: 2 / 4; color: #6ee0b5; }
.bottom-cards { display: flex; gap: 8px; align-items: center; color: var(--muted); }
.bottom-cards b { padding: 5px 8px; border-radius: 7px; color: #20231f; background: #f3ead8; }
.red { color: #bd312e !important; }
.table-center { min-height: 112px; display: grid; place-items: center; color: var(--muted); text-align: center; }
.played-cards { display: flex; justify-content: center; margin-top: 8px; }
.played-cards span { min-width: 44px; padding: 8px 5px; margin-left: -5px; border: 1px solid #c8baa3; border-radius: 6px; color: #20231f; background: #f7f1e5; box-shadow: 0 3px 8px #0005; }
.bid-panel { display: grid; justify-items: center; gap: 12px; }
.bid-panel div, .play-actions { display: flex; gap: 8px; }
.bid-panel button, .play-actions button:not(.arcade-danger-button) { padding: 10px 17px; border: 1px solid var(--line); border-radius: 11px; color: var(--text); background: var(--surface); }
.bid-panel button:disabled, .play-actions button:disabled { opacity: .35; }
.hand { width: 100%; min-height: 128px; display: flex; align-items: end; justify-content: center; overflow-x: auto; padding: 24px 16px 5px; }
.playing-card { flex: 0 0 clamp(42px, 6vw, 62px); height: clamp(84px, 12vw, 116px); margin-left: clamp(-18px, -2vw, -10px); padding: 8px 4px; display: flex; flex-direction: column; align-items: flex-start; border: 1px solid #c8baa3; border-radius: 8px; color: #20231f; background: #f7f1e5; box-shadow: 0 4px 10px #0006; transition: transform .15s; }
.playing-card:first-child { margin-left: 0; }
.playing-card.selected { transform: translateY(-20px); border-color: var(--gold); }
.playing-card b { font-size: 18px; }
.playing-card span { font-size: 20px; }
.play-actions .primary { color: #06231c; background: var(--green); }
@media (max-width: 600px) { .opponent-row { grid-template-columns: 1fr 1fr; } .opponent { grid-template-columns: auto 1fr; } .opponent b { grid-column: 2; grid-row: 2; } }
@media (max-width: 600px) {
  .hand { justify-content: flex-start; padding-right: 4px; padding-left: 4px; }
  .playing-card { flex-basis: 44px; margin-left: 4px; }
  .playing-card:first-child { margin-left: 0; }
}
</style>
