<script setup lang="ts">
import { computed } from 'vue'
import { Sparkles } from '@lucide/vue'
import {
  usePluginGameActions,
  type ArcadeSnapshot,
} from '@game-hall/plugin-sdk'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const actions = usePluginGameActions()
const game = computed(() => props.snapshot.game as {
  startingStones?: number
  maxTake?: number
  remaining?: number
  currentPlayerId?: string | null
  moves?: Array<{ playerId: string; playerName: string; count: number }>
  winnerPlayerId?: string | null
  isMyTurn?: boolean
})
const currentPlayer = computed(() => (
  props.snapshot.players.find((player) => player.id === game.value.currentPlayerId)
))
const winner = computed(() => (
  props.snapshot.players.find((player) => player.id === game.value.winnerPlayerId)
))

function canTake(count: number): boolean {
  return props.snapshot.phase === 'playing'
    && game.value.isMyTurn === true
    && count <= (game.value.remaining ?? 0)
}

function take(count: number) {
  if (!canTake(count)) return
  void actions.action('take', { count })
}
</script>

<template>
  <section class="star-stones surface">
    <header>
      <div><small>STAR STONES · DUEL</small><h2>星石争夺</h2></div>
      <span>{{ game.remaining ?? 0 }} / {{ game.startingStones ?? 15 }}</span>
    </header>

    <div class="turn-banner" :class="{ mine: game.isMyTurn }" role="status">
      <Sparkles :size="19" />
      <span v-if="snapshot.phase === 'finished'">
        <strong>{{ winner?.name ?? '胜者' }} 获胜</strong><small>取得了最后一颗星石</small>
      </span>
      <span v-else>
        <strong>{{ game.isMyTurn ? '轮到你取石' : `等待 ${currentPlayer?.name ?? '对手'}` }}</strong>
        <small>每次可以取走 1–{{ Math.min(game.maxTake ?? 3, game.remaining ?? 0) }} 颗</small>
      </span>
    </div>

    <div class="stone-field" aria-label="剩余星石">
      <i v-for="stone in game.remaining ?? 0" :key="stone"><Sparkles :size="17" /></i>
      <span v-if="!game.remaining">星石已全部取完</span>
    </div>

    <div v-if="snapshot.phase === 'playing'" class="take-actions" aria-label="取石操作">
      <button
        v-for="count in (game.maxTake ?? 3)"
        :key="count"
        type="button"
        :disabled="!canTake(count)"
        @click="take(count)"
      >
        <span>{{ count }}</span><strong>取 {{ count }} 颗</strong>
      </button>
    </div>

    <div class="move-log">
      <small>最近行动</small>
      <span v-if="!game.moves?.length">等待第一步</span>
      <ol v-else>
        <li v-for="(move, index) in [...game.moves].reverse()" :key="`${move.playerId}-${index}`">
          <b>{{ move.playerName }}</b><span>取走 {{ move.count }} 颗</span>
        </li>
      </ol>
    </div>
  </section>
</template>

<style scoped>
.star-stones { width: min(100%, 900px); min-width: 0; max-width: 100%; display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(230px, .65fr); gap: 16px; margin: 0 auto; padding: clamp(18px, 3vw, 28px); }
.star-stones > header { grid-column: 1 / -1; display: flex; align-items: center; justify-content: space-between; gap: 14px; border-bottom: 1px solid var(--line); padding-bottom: 15px; }.star-stones header small { color: var(--gold); font-size: 8px; font-weight: 900; letter-spacing: .17em; }.star-stones h2 { margin: 4px 0 0; font-family: "Songti SC", "STSong", serif; font-size: clamp(27px, 5vw, 38px); }.star-stones header > span { border: 1px solid color-mix(in srgb, var(--gold) 38%, var(--line)); border-radius: 999px; padding: 7px 10px; color: var(--gold); background: color-mix(in srgb, var(--gold) 7%, var(--surface-inset)); font-size: 11px; font-weight: 900; }
.turn-banner { min-height: 70px; display: flex; align-items: center; gap: 11px; border: 1px solid var(--line); border-radius: 15px; padding: 12px 14px; color: var(--muted); background: var(--surface-inset); }.turn-banner.mine { border-color: color-mix(in srgb, var(--gold) 52%, var(--line)); color: var(--gold); background: color-mix(in srgb, var(--gold) 8%, var(--surface-inset)); }.turn-banner > span { display: grid; gap: 3px; }.turn-banner strong { color: var(--text); font-size: 14px; }.turn-banner small { color: var(--muted); font-size: 9px; }
.stone-field { min-height: 230px; display: grid; grid-template-columns: repeat(5, minmax(38px, 1fr)); place-items: center; gap: 10px; border: 1px solid color-mix(in srgb, var(--gold) 24%, var(--line)); border-radius: 20px; padding: 20px; background: radial-gradient(circle at 50% 38%, color-mix(in srgb, var(--gold) 10%, transparent), transparent 58%), var(--surface-inset); }.stone-field i { width: 44px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--gold) 48%, var(--line)); border-radius: 50%; color: var(--gold); background: color-mix(in srgb, var(--gold) 9%, var(--surface-elevated)); box-shadow: 0 8px 22px color-mix(in srgb, var(--bg) 45%, transparent); }.stone-field > span { grid-column: 1 / -1; color: var(--muted); font-size: 11px; }
.take-actions { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }.take-actions button { min-width: 0; min-height: 64px; display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: center; gap: 8px; border: 1px solid color-mix(in srgb, var(--gold) 34%, var(--line)); border-radius: 13px; padding: 8px 10px; color: var(--text); background: color-mix(in srgb, var(--gold) 7%, var(--surface-inset)); cursor: pointer; }.take-actions button > span { width: 32px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 10px; color: var(--accent-contrast); background: var(--gold); font-size: 15px; font-weight: 900; }.take-actions strong { overflow: hidden; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }.take-actions button:disabled { opacity: .38; cursor: not-allowed; }
.move-log { grid-column: 2; grid-row: 2 / span 3; min-width: 0; border: 1px solid var(--line); border-radius: 17px; padding: 14px; background: color-mix(in srgb, var(--surface-elevated) 42%, transparent); }.move-log > small { display: block; border-bottom: 1px solid var(--line); padding-bottom: 10px; color: var(--gold); font-size: 8px; font-weight: 900; letter-spacing: .12em; }.move-log > span { display: block; padding: 22px 0; color: var(--muted); font-size: 10px; text-align: center; }.move-log ol { display: grid; gap: 7px; margin: 10px 0 0; padding: 0; list-style: none; }.move-log li { min-width: 0; display: flex; justify-content: space-between; gap: 8px; border-bottom: 1px solid color-mix(in srgb, var(--line) 65%, transparent); padding: 7px 2px; font-size: 9px; }.move-log b,.move-log li span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.move-log li span { color: var(--muted); }
@media (hover: hover) { .take-actions button:hover:not(:disabled) { border-color: var(--gold); transform: translateY(-2px); } }
@media (max-width: 680px) { .star-stones { grid-template-columns: 1fr; gap: 12px; padding: 15px 12px; }.move-log { grid-column: auto; grid-row: auto; }.stone-field { min-height: 205px; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 7px; padding: 15px 10px; }.stone-field i { width: min(40px, 100%); }.take-actions button { grid-template-columns: 1fr; justify-items: center; gap: 4px; padding: 7px 4px; }.take-actions strong { font-size: 8px; } }
</style>
