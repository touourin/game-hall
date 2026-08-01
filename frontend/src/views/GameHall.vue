<script setup lang="ts">
import { ref } from 'vue'
import { History, LogOut, Palette, RotateCcw } from '@lucide/vue'
import type { AccountProfile } from '../account'
import type { GameCatalogItem } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import StatsModal from '../components/StatsModal.vue'
import ThemeModal from '../components/ThemeModal.vue'

defineProps<{ account: AccountProfile }>()
const emit = defineEmits<{
  logout: []
  select: [game: GameCatalogItem]
}>()
const arcade = useArcadeStore()
const showStats = ref(false)
const showTheme = ref(false)

const games: Array<GameCatalogItem & { symbol: string; tone: string }> = [
  { key: 'avalon', name: '阿瓦隆', players: '5–10 人', description: '身份推理、组队投票与湖中仙女', symbol: '♛', tone: 'gold' },
  { key: 'gomoku', name: '五子棋', players: '2 人', description: '15 路棋盘，率先连成五子', symbol: '●', tone: 'ink' },
  { key: 'xiangqi', name: '中国象棋', players: '2 人', description: '楚河汉界，完整将军与将死规则', symbol: '将', tone: 'red' },
  { key: 'go', name: '围棋', players: '2 人', description: '19 路棋盘，中国数子与贴目', symbol: '○', tone: 'jade' },
  { key: 'doudizhu', name: '斗地主', players: '3 人', description: '叫地主、牌型对抗与农民协作', symbol: '♠', tone: 'blue' },
  { key: 'junqi', name: '军旗', players: '2 人', description: '暗军旗布阵，或翻棋决定阵营', symbol: '旗', tone: 'army' },
  { key: 'reaction', name: '反应时间', players: '1 人', description: '等待信号变色，测出三轮真实反应', symbol: '⚡', tone: 'pulse' },
]
</script>

<template>
  <main class="game-hall page-container">
    <section class="account-bar" aria-label="当前登录账号">
      <div>
        <span class="avatar">{{ account.displayName.slice(0, 1) }}</span>
        <span><small>游戏大厅</small><strong>{{ account.displayName }}</strong></span>
      </div>
      <div class="account-bar-actions">
        <button type="button" @click="showStats = true"><History :size="16" /><span>战绩</span></button>
        <button type="button" @click="showTheme = true"><Palette :size="16" /><span>主题</span></button>
        <button type="button" @click="emit('logout')"><LogOut :size="16" /><span>退出</span></button>
      </div>
    </section>

    <section class="hall-hero">
      <p class="eyebrow">PRIVATE GAME HALL</p>
      <h1>今晚玩什么？</h1>
      <p>同一个账号、同一个大厅，每款游戏都有独立战绩。</p>
    </section>

    <section
      v-if="arcade.resumableGame && arcade.resumableRoomCode"
      class="surface resume-arcade-card"
    >
      <div><RotateCcw :size="20" /><span><strong>你有一局尚未结束</strong><small>房间 {{ arcade.resumableRoomCode }}</small></span></div>
      <button type="button" class="primary-button" @click="arcade.returnToRoom">返回对局</button>
    </section>

    <section class="game-grid" aria-label="选择游戏">
      <button
        v-for="game in games"
        :key="game.key"
        type="button"
        class="game-card surface"
        :class="`tone-${game.tone}`"
        @click="emit('select', game)"
      >
        <span class="game-symbol">{{ game.symbol }}</span>
        <span class="game-copy">
          <small>{{ game.players }}</small>
          <strong>{{ game.name }}</strong>
          <em>{{ game.description }}</em>
        </span>
        <span class="enter-game">进入 →</span>
      </button>
    </section>

    <StatsModal v-if="showStats" @close="showStats = false" />
    <ThemeModal v-if="showTheme" @close="showTheme = false" />
  </main>
</template>

<style scoped>
.game-hall { padding-bottom: 80px; }
.hall-hero { padding: clamp(36px, 7vw, 78px) 0 32px; text-align: center; }
.hall-hero h1 { margin: 8px 0; font-family: serif; font-size: clamp(38px, 7vw, 72px); }
.hall-hero p:last-child { color: var(--muted); }
.resume-arcade-card { margin-bottom: 22px; padding: 16px 18px; display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.resume-arcade-card > div { display: flex; gap: 12px; align-items: center; color: var(--gold); }
.resume-arcade-card strong, .resume-arcade-card small { display: block; }
.resume-arcade-card small { margin-top: 3px; color: var(--muted); }
.game-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.game-card { position: relative; min-height: 210px; padding: 24px; display: grid; grid-template-columns: auto 1fr; gap: 18px; align-items: start; text-align: left; color: var(--text); overflow: hidden; }
.game-card:first-child { grid-column: 1 / -1; min-height: 230px; }
.game-card::after { content: ''; position: absolute; width: 180px; aspect-ratio: 1; right: -70px; bottom: -90px; border-radius: 50%; background: currentColor; opacity: .055; }
.game-symbol { width: 64px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid currentColor; border-radius: 18px; color: var(--gold); font-family: serif; font-size: 32px; background: color-mix(in srgb, var(--gold) 7%, transparent); }
.game-copy { display: grid; gap: 7px; }
.game-copy small { color: var(--gold); font-weight: 800; }
.game-copy strong { font-family: serif; font-size: 28px; }
.game-copy em { color: var(--muted); font-style: normal; line-height: 1.5; }
.enter-game { position: absolute; right: 22px; bottom: 20px; color: var(--gold); font-weight: 800; }
.tone-red .game-symbol { color: #e88a82; }.tone-jade .game-symbol { color: #72d0ad; }.tone-blue .game-symbol { color: #86bde4; }.tone-ink .game-symbol { color: #d7d8d1; }
.tone-army .game-symbol { color: #d8b66b; }
.tone-pulse .game-symbol { color: #8fe0bd; }
@media (max-width: 680px) {
  .game-grid { grid-template-columns: 1fr; }
  .game-card:first-child { grid-column: auto; }
  .resume-arcade-card { align-items: stretch; flex-direction: column; }
  .account-bar { display: grid; grid-template-columns: minmax(0, 1fr); gap: 10px; padding: 0 0 12px; }
  .account-bar > div:first-child { min-width: 0; }
  .account-bar > div:first-child strong { max-width: min(68vw, 260px); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .account-bar .account-bar-actions { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); width: 100%; gap: 6px; }
  .account-bar button { width: 100%; min-width: 0; min-height: 46px; padding: 5px 2px; flex-direction: column; justify-content: center; gap: 2px; }
  .account-bar-actions span { display: block; line-height: 1; white-space: nowrap; }
}
</style>
