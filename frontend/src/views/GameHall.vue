<script setup lang="ts">
import { ref } from 'vue'
import { History, LogOut, RotateCcw, Settings, Sparkles } from '@lucide/vue'
import type { AccountProfile, AvatarPresetId } from '../account'
import type { GameCatalogItem } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import StatsModal from '../components/StatsModal.vue'
import SettingsModal from '../components/SettingsModal.vue'
import AvatarImage from '../components/AvatarImage.vue'

defineProps<{
  account: AccountProfile
  busy: boolean
  error: string | null
}>()
const emit = defineEmits<{
  logout: []
  select: [game: GameCatalogItem]
  rename: [playerName: string]
  avatarPreset: [preset: AvatarPresetId]
  avatarUpload: [file: File]
}>()
const arcade = useArcadeStore()
const showStats = ref(false)
const showSettings = ref(false)

const games: Array<GameCatalogItem & { symbol: string; tone: string; category: string }> = [
  { key: 'avalon', name: '阿瓦隆', players: '5–10 人', description: '身份推理、组队投票与湖中仙女', symbol: '♛', tone: 'gold', category: '社交推理' },
  { key: 'gomoku', name: '五子棋', players: '2 人', description: '15 路棋盘，Swap2 与有禁手连珠', symbol: '●', tone: 'ink', category: '棋类竞技' },
  { key: 'xiangqi', name: '中国象棋', players: '2 人', description: '楚河汉界，完整走子与重复局面限制', symbol: '将', tone: 'red', category: '棋类竞技' },
  { key: 'go', name: '围棋', players: '2 人', description: '9/13/19 路可选，中国数子与贴目', symbol: '○', tone: 'jade', category: '棋类竞技' },
  { key: 'poker', name: '德州扑克', players: '2–8 人', description: '大小盲、四轮下注与全押边池', symbol: '♥', tone: 'poker', category: '扑克对战' },
  { key: 'doudizhu', name: '斗地主', players: '3 人', description: '叫抢地主、三种玩法与倍数结算', symbol: '♠', tone: 'blue', category: '扑克对战' },
  { key: 'junqi', name: '军旗', players: '2 人', description: '暗军旗布阵，或翻棋决定阵营', symbol: '旗', tone: 'army', category: '棋类竞技' },
  { key: 'reaction', name: '反应挑战', players: '1 人', description: '等待信号变色，测出三轮真实反应', symbol: '⚡', tone: 'pulse', category: '个人挑战' },
  { key: 'schulte', name: '舒尔特方格', players: '1 人', description: '按顺序寻找 1–25，训练专注与视觉搜索', symbol: '格', tone: 'focus', category: '个人挑战' },
  { key: 'minesweeper', name: '扫雷', players: '1 人', description: '初、中、高三种经典难度，首次点击安全', symbol: '雷', tone: 'mine', category: '个人挑战' },
  { key: 'hanoi', name: '汉诺塔', players: '1 人', description: '3–8 层经典益智挑战，争取最少步数', symbol: '塔', tone: 'tower', category: '个人挑战' },
]
</script>

<template>
  <main class="game-hall page-container">
    <section class="account-bar" aria-label="当前登录账号">
      <div>
        <AvatarImage
          class="avatar account-avatar"
          :src="account.avatarUrl"
          :name="account.playerName"
        />
        <span><small>游戏大厅</small><strong>{{ account.playerName }}</strong></span>
      </div>
      <div class="account-bar-actions">
        <button type="button" @click="showStats = true"><History :size="16" /><span>战绩</span></button>
        <button type="button" @click="showSettings = true"><Settings :size="16" /><span>设置</span></button>
        <button type="button" @click="emit('logout')"><LogOut :size="16" /><span>退出</span></button>
      </div>
    </section>

    <section class="hall-hero">
      <div class="hall-hero-copy">
        <p class="eyebrow">PRIVATE GAME SALON · 11 GAMES</p>
        <h1>今晚，开一局。</h1>
        <p>棋局、牌桌与社交推理汇于同一间私人会所。每款游戏独立记录，随时回来继续。</p>
        <div class="hall-highlights" aria-label="大厅能力">
          <span>实时联机</span><span>独立战绩</span><span>专属皮肤</span>
        </div>
      </div>
      <div class="hall-seal" aria-hidden="true">
        <Sparkles :size="20" />
        <strong>十一</strong>
        <small>款精选游戏</small>
      </div>
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
        v-for="(game, index) in games"
        :key="game.key"
        type="button"
        class="game-card surface"
        :class="`tone-${game.tone}`"
        @click="emit('select', game)"
      >
        <span class="game-index">{{ String(index + 1).padStart(2, '0') }}</span>
        <span class="game-symbol">{{ game.symbol }}</span>
        <span class="game-copy">
          <small>{{ game.category }} · {{ game.players }}</small>
          <strong>{{ game.name }}</strong>
          <em>{{ game.description }}</em>
        </span>
        <span v-if="index === 0" class="featured-label">本周主桌</span>
        <span class="enter-game">进入游戏 <b>↗</b></span>
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
      @avatar-preset="emit('avatarPreset', $event)"
      @avatar-upload="emit('avatarUpload', $event)"
    />
  </main>
</template>

<style scoped>
.game-hall { width: min(100%, 1180px); padding-bottom: 88px; }
.account-avatar { border: 1px solid color-mix(in srgb, var(--gold) 45%, transparent); }
.hall-hero { min-height: 330px; padding: clamp(54px, 8vw, 96px) clamp(4px, 2vw, 24px) 48px; display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 50px; }
.hall-hero-copy { max-width: 680px; }
.hall-hero h1 { margin: 13px 0 15px; font-family: "Songti SC", "STSong", serif; font-size: clamp(48px, 7vw, 78px); font-weight: 650; letter-spacing: -.045em; line-height: 1.04; }
.hall-hero-copy > p:last-of-type { max-width: 570px; margin: 0; color: var(--muted); font-size: 16px; line-height: 1.75; }
.hall-highlights { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 24px; }
.hall-highlights span { border: 1px solid var(--line); border-radius: 999px; padding: 7px 11px; color: var(--text-soft); background: var(--surface-inset); font-size: 11px; font-weight: 750; letter-spacing: .08em; }
.hall-seal { position: relative; width: 152px; aspect-ratio: 1; display: grid; place-items: center; align-content: center; gap: 3px; border: 1px solid var(--line-strong); border-radius: 50%; color: var(--gold); background: radial-gradient(circle, color-mix(in srgb, var(--gold) 13%, var(--surface)) 0 47%, transparent 48%), var(--surface-inset); box-shadow: inset 0 0 0 9px color-mix(in srgb, var(--gold) 4%, transparent), var(--shadow-card); transform: rotate(3deg); }
.hall-seal::before { position: absolute; inset: 10px; border: 1px dashed color-mix(in srgb, var(--gold) 42%, transparent); border-radius: 50%; content: ''; }
.hall-seal strong { font-family: "Songti SC", "STSong", serif; font-size: 34px; line-height: 1; }
.hall-seal small { color: var(--muted); font-size: 10px; letter-spacing: .12em; }
.resume-arcade-card { margin-bottom: 22px; padding: 16px 18px; display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.resume-arcade-card > div { display: flex; gap: 12px; align-items: center; color: var(--gold); }
.resume-arcade-card strong, .resume-arcade-card small { display: block; }
.resume-arcade-card small { margin-top: 3px; color: var(--muted); }
.game-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.game-card { --card-tone: var(--gold); position: relative; min-height: 250px; padding: 27px; display: grid; grid-template-columns: auto minmax(0, 1fr); align-content: start; gap: 19px; border-color: color-mix(in srgb, var(--card-tone) 18%, var(--line)); text-align: left; color: var(--text); overflow: hidden; isolation: isolate; cursor: pointer; }
.game-card:first-child { grid-column: span 2; min-height: 286px; }
.game-card::before { position: absolute; z-index: -1; inset: 0; background: radial-gradient(circle at 88% 8%, color-mix(in srgb, var(--card-tone) 18%, transparent), transparent 35%), linear-gradient(145deg, transparent 40%, color-mix(in srgb, var(--card-tone) 5%, transparent)); content: ''; }
.game-card::after { position: absolute; z-index: -1; right: -42px; bottom: -76px; width: 184px; aspect-ratio: 1; border: 1px solid color-mix(in srgb, var(--card-tone) 22%, transparent); border-radius: 50%; box-shadow: inset 0 0 0 18px color-mix(in srgb, var(--card-tone) 2%, transparent); content: ''; }
.game-index { position: absolute; top: 19px; right: 21px; color: color-mix(in srgb, var(--muted) 58%, transparent); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 10px; letter-spacing: .14em; }
.game-symbol { width: 62px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--card-tone) 36%, var(--line)); border-radius: var(--radius-md); color: var(--card-tone); background: color-mix(in srgb, var(--card-tone) 9%, var(--surface-inset)); font-family: "Songti SC", serif; font-size: 31px; box-shadow: inset 0 1px rgba(255,255,255,.08); }
.game-copy { display: grid; gap: 8px; min-width: 0; }
.game-copy small { color: var(--card-tone); font-size: 11px; font-weight: 850; letter-spacing: .06em; }
.game-copy strong { font-family: "Songti SC", "STSong", serif; font-size: 29px; letter-spacing: -.02em; }
.game-copy em { color: var(--muted); font-style: normal; line-height: 1.5; }
.featured-label { position: absolute; left: 27px; bottom: 25px; border: 1px solid color-mix(in srgb, var(--gold) 35%, transparent); border-radius: 999px; padding: 6px 10px; color: var(--gold); background: color-mix(in srgb, var(--gold) 8%, transparent); font-size: 10px; font-weight: 850; letter-spacing: .08em; }
.enter-game { position: absolute; right: 23px; bottom: 22px; color: var(--card-tone); font-size: 12px; font-weight: 800; }
.enter-game b { display: inline-grid; width: 24px; aspect-ratio: 1; margin-left: 5px; place-items: center; border: 1px solid color-mix(in srgb, var(--card-tone) 28%, transparent); border-radius: 50%; font-size: 12px; }
.tone-red { --card-tone: #e88a82; }.tone-jade { --card-tone: #72d0ad; }.tone-blue { --card-tone: #86bde4; }.tone-ink { --card-tone: #d7d8d1; }
.tone-army { --card-tone: #d8b66b; }.tone-pulse { --card-tone: #8fe0bd; }.tone-focus { --card-tone: #7ecdb5; }.tone-mine { --card-tone: #ef9d93; }.tone-tower { --card-tone: #d9a86c; }.tone-poker { --card-tone: #ef8c88; }
:global(:root[data-theme="royal"]) .tone-red { --card-tone: #a54e40; }:global(:root[data-theme="royal"]) .tone-jade { --card-tone: #36785f; }:global(:root[data-theme="royal"]) .tone-blue { --card-tone: #3f6f91; }:global(:root[data-theme="royal"]) .tone-ink { --card-tone: #4d4a43; }:global(:root[data-theme="royal"]) .tone-army { --card-tone: #85651f; }:global(:root[data-theme="royal"]) .tone-pulse { --card-tone: #39785e; }:global(:root[data-theme="royal"]) .tone-focus { --card-tone: #346f68; }:global(:root[data-theme="royal"]) .tone-mine { --card-tone: #a44a42; }:global(:root[data-theme="royal"]) .tone-tower { --card-tone: #90602d; }:global(:root[data-theme="royal"]) .tone-poker { --card-tone: #a54e40; }
@media (hover: hover) {
  .game-card:hover { border-color: color-mix(in srgb, var(--card-tone) 42%, var(--line)); box-shadow: 0 24px 60px color-mix(in srgb, var(--bg) 56%, transparent); transform: translateY(-4px); }
  .game-card:hover .enter-game b { background: var(--card-tone); color: var(--accent-contrast); transform: rotate(8deg); }
}
@media (max-width: 680px) {
  .game-hall { padding-right: 12px; padding-left: 12px; }
  .hall-hero { min-height: 0; padding: 40px 5px 30px; grid-template-columns: minmax(0, 1fr) 78px; gap: 12px; }
  .hall-hero h1 { margin: 10px 0 12px; font-size: clamp(40px, 12vw, 54px); }
  .hall-hero-copy > p:last-of-type { font-size: 14px; line-height: 1.65; }
  .hall-seal { width: 76px; }.hall-seal::before { inset: 6px; }.hall-seal svg { display: none; }.hall-seal strong { font-size: 25px; }.hall-seal small { font-size: 7px; }
  .hall-highlights { gap: 5px; margin-top: 17px; }.hall-highlights span { padding: 5px 7px; font-size: 9px; }
  .game-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .game-card { min-height: 202px; padding: 17px 14px; grid-template-columns: 1fr; gap: 10px; }
  .game-card:first-child { grid-column: 1 / -1; min-height: 225px; padding: 20px; grid-template-columns: auto 1fr; gap: 15px; }
  .game-symbol { width: 50px; border-radius: 14px; font-size: 25px; }
  .game-copy { gap: 5px; }.game-copy small { padding-right: 20px; font-size: 9px; line-height: 1.4; }.game-copy strong { font-size: 22px; }.game-copy em { display: -webkit-box; overflow: hidden; font-size: 11px; line-height: 1.45; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
  .game-index { top: 13px; right: 12px; }.enter-game { right: 14px; bottom: 14px; font-size: 0; }.enter-game b { margin: 0; }
  .featured-label { left: 20px; bottom: 18px; }
  .resume-arcade-card { align-items: stretch; flex-direction: column; }
  .account-bar { display: grid; grid-template-columns: minmax(0, 1fr); gap: 10px; padding: 0 0 12px; }
  .account-bar > div:first-child { min-width: 0; }
  .account-bar > div:first-child strong { max-width: min(68vw, 260px); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .account-bar .account-bar-actions { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); width: 100%; gap: 6px; }
  .account-bar button { width: 100%; min-width: 0; min-height: 46px; padding: 5px 2px; flex-direction: column; justify-content: center; gap: 2px; }
  .account-bar-actions span { display: block; line-height: 1; white-space: nowrap; }
}
@media (max-width: 370px) {
  .hall-seal { display: none; }.hall-hero { grid-template-columns: 1fr; }
  .game-grid { grid-template-columns: 1fr; }.game-card:first-child { grid-column: auto; }
}
</style>
