<script setup lang="ts">
import { computed } from 'vue'
import {
  usePluginGameActions,
  type ArcadeSnapshot,
} from '@game-hall/plugin-sdk'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const actions = usePluginGameActions()
const game = computed(() => props.snapshot.game as {
  targetScore?: number
  currentPlayerId?: string | null
  scores?: Record<string, number>
})
const canIncrement = computed(() => (
  props.snapshot.phase === 'playing'
  && game.value.currentPlayerId === props.snapshot.self.id
))

function score(playerId: string): number {
  return game.value.scores?.[playerId] ?? 0
}
</script>

<template>
  <section class="counter-demo surface">
    <header>
      <small>THIRD-PARTY GAME PLUGIN</small>
      <h2>计数竞速</h2>
      <p>双方轮流计数，率先达到 {{ game.targetScore ?? 10 }} 分者获胜。</p>
    </header>
    <div class="counter-scoreboard">
      <article v-for="player in snapshot.players" :key="player.id" :class="{ active: game.currentPlayerId === player.id }">
        <span>{{ player.name }}</span>
        <strong>{{ score(player.id) }}</strong>
        <small>{{ player.id === snapshot.self.id ? '你' : '对手' }}</small>
      </article>
    </div>
    <button
      type="button"
      class="primary-button"
      :disabled="!canIncrement"
      @click="actions.action('increment')"
    >
      {{ canIncrement ? '计数 +1' : '等待对手' }}
    </button>
  </section>
</template>

<style scoped>
.counter-demo { width: min(100%, 720px); min-width: 0; max-width: 100%; display: grid; gap: 22px; margin: 0 auto; padding: clamp(20px, 5vw, 38px); }
.counter-demo header { text-align: center; }.counter-demo small { color: var(--gold); font-weight: 850; letter-spacing: .12em; }.counter-demo h2 { margin: 7px 0; font-family: "Songti SC", serif; font-size: clamp(30px, 7vw, 48px); }.counter-demo p { margin: 0; color: var(--muted); }
.counter-scoreboard { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }.counter-scoreboard article { min-width: 0; display: grid; justify-items: center; gap: 5px; border: 1px solid var(--line); border-radius: 16px; padding: 18px 10px; background: var(--surface-soft); }.counter-scoreboard article.active { border-color: var(--gold); }.counter-scoreboard span { overflow: hidden; max-width: 100%; text-overflow: ellipsis; white-space: nowrap; }.counter-scoreboard strong { font-size: clamp(38px, 10vw, 62px); }.counter-demo > button { width: 100%; justify-content: center; }
@media (max-width: 420px) { .counter-scoreboard { grid-template-columns: 1fr; } }
</style>
