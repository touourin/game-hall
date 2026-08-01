<script setup lang="ts">
import { ref } from 'vue'
import { History, LogOut, RotateCcw, Settings } from '@lucide/vue'
import type { AccountProfile } from '../account'
import type { GameCatalogItem } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import StatsModal from '../components/StatsModal.vue'
import SettingsModal from '../components/SettingsModal.vue'

defineProps<{
  account: AccountProfile
  busy: boolean
  error: string | null
}>()
const emit = defineEmits<{
  logout: []
  select: [game: GameCatalogItem]
  rename: [playerName: string]
}>()
const arcade = useArcadeStore()
const showStats = ref(false)
const showSettings = ref(false)

const games: Array<GameCatalogItem & { symbol: string; tone: string }> = [
  { key: 'avalon', name: '阿瓦隆', players: '5–10 人', description: '身份推理、组队投票与湖中仙女', symbol: '♛', tone: 'gold' },
  { key: 'gomoku', name: '五子棋', players: '2 人', description: '15 路棋盘，Swap2 与有禁手连珠', symbol: '●', tone: 'ink' },
  { key: 'xiangqi', name: '中国象棋', players: '2 人', description: '楚河汉界，完整走子与重复局面限制', symbol: '将', tone: 'red' },
  { key: 'go', name: '围棋', players: '2 人', description: '9/13/19 路可选，中国数子与贴目', symbol: '○', tone: 'jade' },
  { key: 'poker', name: '德州扑克', players: '2–8 人', description: '大小盲、四轮下注与全押边池', symbol: '♥', tone: 'poker' },
  { key: 'doudizhu', name: '斗地主', players: '3 人', description: '叫抢地主、三种玩法与倍数结算', symbol: '♠', tone: 'blue' },
  { key: 'junqi', name: '军旗', players: '2 人', description: '暗军旗布阵，或翻棋决定阵营', symbol: '旗', tone: 'army' },
  { key: 'reaction', name: '反应挑战', players: '1 人', description: '等待信号变色，测出三轮真实反应', symbol: '⚡', tone: 'pulse' },
  { key: 'schulte', name: '舒尔特方格', players: '1 人', description: '按顺序寻找 1–25，训练专注与视觉搜索', symbol: '格', tone: 'focus' },
  { key: 'minesweeper', name: '扫雷', players: '1 人', description: '初、中、高三种经典难度，首次点击安全', symbol: '雷', tone: 'mine' },
  { key: 'hanoi', name: '汉诺塔', players: '1 人', description: '3–8 层经典益智挑战，争取最少步数', symbol: '塔', tone: 'tower' },
]
</script>

<template>
  <main class="game-hall page-container">
    <section class="account-bar" aria-label="当前登录账号">
      <div>
        <span class="avatar">{{ account.playerName.slice(0, 1) }}</span>
        <span><small>游戏大厅</small><strong>{{ account.playerName }}</strong></span>
      </div>
      <div class="account-bar-actions">
        <button type="button" @click="showStats = true"><History :size="16" /><span>战绩</span></button>
        <button type="button" @click="showSettings = true"><Settings :size="16" /><span>设置</span></button>
        <button type="button" @click="emit('logout')"><LogOut :size="16" /><span>退出</span></button>
      </div>
    </section>

    <section class="hall-hero">
      <p class="eyebrow">GAME HALL</p>
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
    <SettingsModal
      v-if="showSettings"
      :account="account"
      :busy="busy"
      :error="error"
      @close="showSettings = false"
      @rename="emit('rename', $event)"
    />
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
.tone-focus .game-symbol { color: #7ecdb5; }
.tone-mine .game-symbol { color: #ef9d93; }
.tone-tower .game-symbol { color: #d9a86c; }
.tone-poker .game-symbol { color: #ef8c88; }
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
