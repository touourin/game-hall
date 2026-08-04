<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { KeyRound, RotateCcw, ShieldCheck } from '@lucide/vue'
import {
  usePluginGameActions,
  type ArcadeSnapshot,
} from '@game-hall/plugin-sdk'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const actions = usePluginGameActions()
const guess = ref(10)
const game = computed(() => props.snapshot.game as {
  minimum?: number
  maximum?: number
  maxAttempts?: number
  remainingAttempts?: number
  guesses?: number[]
  hint?: 'ready' | 'higher' | 'lower' | 'correct'
  answer?: number | null
  won?: boolean
})
const canGuess = computed(() => (
  props.snapshot.phase === 'playing'
  && props.snapshot.actions.canAct
  && Number.isInteger(guess.value)
  && guess.value >= (game.value.minimum ?? 1)
  && guess.value <= (game.value.maximum ?? 20)
))
const hintText = computed(() => ({
  ready: '输入你的第一个猜测',
  higher: '答案更大一些',
  lower: '答案更小一些',
  correct: '密匣已经破解',
}[game.value.hint ?? 'ready']))

watch(() => props.snapshot.roundNumber, () => {
  guess.value = 10
})

function submitGuess() {
  if (!canGuess.value) return
  void actions.action('guess', { value: guess.value })
}
</script>

<template>
  <section class="number-vault surface">
    <header class="vault-header">
      <span class="vault-icon"><KeyRound :size="28" /></span>
      <div>
        <small>NUMBER VAULT · SOLO</small>
        <h2>数字密匣</h2>
        <p>在 {{ game.minimum ?? 1 }}–{{ game.maximum ?? 20 }} 之间找到唯一答案。</p>
      </div>
    </header>

    <div class="vault-status" :class="`hint-${game.hint ?? 'ready'}`" role="status">
      <small>密匣提示</small>
      <strong>{{ hintText }}</strong>
      <span v-if="snapshot.phase !== 'finished'">还剩 {{ game.remainingAttempts ?? 6 }} 次机会</span>
      <span v-else>答案：{{ game.answer }}</span>
    </div>

    <div class="vault-history" aria-label="猜测记录">
      <span v-if="!game.guesses?.length">尚未提交数字</span>
      <b v-for="value in game.guesses" :key="value">{{ value }}</b>
    </div>

    <form v-if="snapshot.phase === 'playing'" class="vault-control" @submit.prevent="submitGuess">
      <label>
        <span>你的猜测</span>
        <input
          v-model.number="guess"
          type="number"
          :min="game.minimum ?? 1"
          :max="game.maximum ?? 20"
          inputmode="numeric"
          aria-label="猜测数字"
        />
      </label>
      <button type="submit" class="primary-button" :disabled="!canGuess">尝试破解</button>
    </form>

    <div v-else class="vault-result">
      <strong>{{ game.won ? '破解成功' : '挑战结束' }}</strong>
      <span>{{ game.won ? `你用了 ${game.guesses?.length ?? 0} 次猜中答案` : '换个思路，再试一次。' }}</span>
      <button type="button" class="primary-button" @click="actions.restart()">
        <RotateCcw :size="17" /> 再开一个密匣
      </button>
    </div>

    <footer><ShieldCheck :size="14" />答案只保存在服务端，结束前不会发送到浏览器。</footer>
  </section>
</template>

<style scoped>
.number-vault { width: min(100%, 760px); min-width: 0; max-width: 100%; display: grid; gap: 18px; margin: 0 auto; padding: clamp(18px, 4vw, 32px); }
.vault-header { display: flex; align-items: center; gap: 15px; }.vault-icon { width: 58px; aspect-ratio: 1; display: grid; flex: 0 0 auto; place-items: center; border: 1px solid color-mix(in srgb, var(--gold) 45%, var(--line)); border-radius: 18px; color: var(--gold); background: color-mix(in srgb, var(--gold) 9%, var(--surface-inset)); }.vault-header div { min-width: 0; }.vault-header small { color: var(--gold); font-size: 8px; font-weight: 900; letter-spacing: .17em; }.vault-header h2 { margin: 5px 0 3px; font-family: "Songti SC", "STSong", serif; font-size: clamp(28px, 7vw, 40px); }.vault-header p { margin: 0; color: var(--muted); font-size: 11px; }
.vault-status { min-height: 150px; display: grid; place-items: center; align-content: center; gap: 7px; border: 1px solid color-mix(in srgb, var(--gold) 30%, var(--line)); border-radius: 20px; padding: 22px; background: radial-gradient(circle at 50% 20%, color-mix(in srgb, var(--gold) 13%, transparent), transparent 48%), var(--surface-inset); text-align: center; }.vault-status small { color: var(--gold); font-size: 8px; font-weight: 900; letter-spacing: .13em; }.vault-status strong { font-family: "Songti SC", "STSong", serif; font-size: clamp(24px, 6vw, 34px); }.vault-status span { color: var(--muted); font-size: 10px; }.vault-status.hint-correct { border-color: color-mix(in srgb, #69d29f 60%, var(--line)); }
.vault-history { min-height: 42px; display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 8px; }.vault-history > span { color: var(--muted); font-size: 10px; }.vault-history b { min-width: 38px; min-height: 38px; display: grid; place-items: center; border: 1px solid var(--line); border-radius: 11px; background: var(--surface-inset); }
.vault-control { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: end; gap: 10px; }.vault-control label { min-width: 0; display: grid; gap: 7px; }.vault-control label span { color: var(--muted); font-size: 9px; font-weight: 800; }.vault-control input { width: 100%; min-height: 48px; border: 1px solid var(--line); border-radius: 12px; outline: 0; padding: 0 14px; color: var(--text); background: var(--surface-inset); font-size: 18px; font-weight: 900; }.vault-control input:focus { border-color: var(--gold); }.vault-control button { min-height: 48px; }
.vault-result { display: grid; justify-items: center; gap: 8px; text-align: center; }.vault-result > strong { font-size: 20px; }.vault-result > span { color: var(--muted); font-size: 11px; }.vault-result button { margin-top: 5px; }
.number-vault footer { display: flex; align-items: flex-start; justify-content: center; gap: 6px; border-top: 1px solid var(--line); padding-top: 14px; color: var(--muted); font-size: 9px; line-height: 1.5; }.number-vault footer svg { flex: 0 0 auto; color: var(--gold); }
@media (max-width: 480px) { .number-vault { gap: 14px; padding: 16px 13px; }.vault-header { align-items: flex-start; }.vault-icon { width: 48px; border-radius: 15px; }.vault-control { grid-template-columns: 1fr; }.vault-control button { width: 100%; justify-content: center; }.vault-status { min-height: 132px; } }
</style>
