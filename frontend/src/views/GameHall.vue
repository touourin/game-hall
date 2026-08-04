<script setup lang="ts">
import { ref } from 'vue'
import {
  ChevronRight,
  History,
  LogOut,
  RotateCcw,
  Settings,
  Sparkles,
  UsersRound,
} from '@lucide/vue'
import type { AccountProfile } from '../account'
import type { GameCatalogItem } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import {
  MULTIPLAYER_GAME_CATALOG,
  SOLO_GAME_CATALOG,
} from '../gameCatalog'
import { BOARD_GAME_PLUGINS } from '../boardGamePlugins'
import StatsModal from '../components/StatsModal.vue'
import AvatarImage from '../components/AvatarImage.vue'
import GameCardArtwork from '../components/GameCardArtwork.vue'

defineProps<{
  account: AccountProfile
}>()
const emit = defineEmits<{
  logout: []
  settings: []
  select: [game: GameCatalogItem]
  openBoardGames: []
  resumeRoom: []
}>()
const arcade = useArcadeStore()
const showStats = ref(false)

const multiplayerGames = MULTIPLAYER_GAME_CATALOG
const soloGames = SOLO_GAME_CATALOG
const boardGamePlugins = BOARD_GAME_PLUGINS
</script>

<template>
  <main class="game-hall page-container">
    <section class="account-bar salon-account-bar surface" aria-label="当前登录账号">
      <div>
        <AvatarImage
          class="avatar account-avatar"
          :src="account.avatarUrl"
          :name="account.playerName"
        />
        <span class="account-identity-copy">
          <small>{{ account.isGuest ? '游客席位 · 对局不计战绩' : `玩家账号 · ${account.username}` }}</small>
          <strong>{{ account.playerName }}</strong>
        </span>
      </div>
      <div class="account-bar-actions">
        <button v-if="!account.isGuest" type="button" aria-label="查看全部战绩" @click="showStats = true"><History :size="16" /><span>全部战绩</span></button>
        <button type="button" aria-label="打开设置" @click="emit('settings')"><Settings :size="16" /><span>设置</span></button>
        <button type="button" :aria-label="account.isGuest ? '退出游客模式' : '退出登录'" @click="emit('logout')"><LogOut :size="16" /><span>退出</span></button>
      </div>
    </section>

    <section class="hall-hero">
      <div class="hall-ornament" aria-hidden="true"><i /><Sparkles :size="14" /><i /></div>
      <h1>游戏大厅</h1>
      <div class="hall-highlights" aria-label="大厅能力">
        <span>实时联机</span><b aria-hidden="true">·</b><span>{{ account.isGuest ? '休闲对局' : '独立战绩' }}</span>
      </div>
    </section>

    <section
      v-if="arcade.resumableGame && arcade.resumableRoomCode"
      class="surface resume-arcade-card"
    >
      <div><RotateCcw :size="20" /><span><strong>你有一局尚未结束</strong><small>房间 {{ arcade.resumableRoomCode }}</small></span></div>
      <button type="button" class="primary-button" @click="emit('resumeRoom')">返回对局</button>
    </section>

    <section class="hall-section" aria-labelledby="board-game-collection-title">
      <header class="hall-section-heading">
        <div>
          <small>GAME COLLECTION</small>
          <h2 id="board-game-collection-title">桌游合集</h2>
        </div>
        <p>独立于现有游戏的桌游插件空间</p>
      </header>

      <button
        type="button"
        class="board-game-collection-card surface"
        aria-label="打开桌游合集"
        @click="emit('openBoardGames')"
      >
        <span class="collection-copy">
          <span class="collection-kicker"><UsersRound :size="17" /> 独立桌游空间</span>
          <strong>打开桌游合集</strong>
          <em>这里不包含现有 7 款联机游戏。桌游插件接入后，会统一显示人数并提供独立房间入口。</em>
          <span class="collection-meta">
            <b>{{ boardGamePlugins.length ? `${boardGamePlugins.length} 款已安装` : '等待桌游插件' }}</b>
            <b>人数清晰标注</b>
            <b>独立房间</b>
          </span>
          <span class="collection-enter">查看全部游戏 <ChevronRight :size="18" /></span>
        </span>

        <span class="collection-preview" aria-hidden="true">
          <span
            v-for="slot in 3"
            :key="slot"
            class="board-plugin-slot"
          >
            <i>+</i>
            <small>桌游插件</small>
          </span>
        </span>
      </button>
    </section>

    <section class="hall-section arcade-section" aria-labelledby="multiplayer-games-title">
      <header class="hall-section-heading">
        <div>
          <small>ONLINE ARCADE</small>
          <h2 id="multiplayer-games-title">联机游戏</h2>
        </div>
        <p>现有 {{ multiplayerGames.length }} 款游戏，保持原有入口</p>
      </header>

      <div class="game-grid" aria-label="选择联机游戏">
        <button
          v-for="game in multiplayerGames"
          :key="game.key"
          type="button"
          class="game-card surface"
          :class="`tone-${game.tone}`"
          @click="emit('select', game)"
        >
          <GameCardArtwork :game-key="game.key" />
          <span class="game-card-topline"><small>{{ game.category }}</small><em>{{ game.players }}</em></span>
          <span class="game-copy">
            <strong>{{ game.name }}</strong>
            <em>{{ game.description }}</em>
          </span>
          <span class="enter-game" aria-hidden="true">›</span>
        </button>
      </div>
    </section>

    <section class="hall-section solo-section" aria-labelledby="solo-games-title">
      <header class="hall-section-heading">
        <div>
          <small>QUICK PLAY</small>
          <h2 id="solo-games-title">单人挑战</h2>
        </div>
        <p>无需等待，选择一款立即开始</p>
      </header>

      <div class="game-grid" aria-label="选择单人游戏">
        <button
          v-for="game in soloGames"
          :key="game.key"
          type="button"
          class="game-card surface"
          :class="`tone-${game.tone}`"
          @click="emit('select', game)"
        >
          <GameCardArtwork :game-key="game.key" />
          <span class="game-card-topline"><small>{{ game.category }}</small><em>{{ game.players }}</em></span>
          <span class="game-copy">
            <strong>{{ game.name }}</strong>
            <em>{{ game.description }}</em>
          </span>
          <span class="enter-game" aria-hidden="true">›</span>
        </button>
      </div>
    </section>

    <StatsModal v-if="showStats && !account.isGuest" @close="showStats = false" />
  </main>
</template>

<style scoped>
.game-hall { width: min(100%, 1180px); padding-bottom: 88px; }
.salon-account-bar { position: sticky; z-index: 20; top: calc(12px + env(safe-area-inset-top)); min-height: 72px; border-bottom: 1px solid var(--line); padding: 10px 13px; background: color-mix(in srgb, var(--surface-elevated) 92%, transparent); box-shadow: 0 14px 34px color-mix(in srgb, var(--bg) 30%, transparent); backdrop-filter: blur(20px); }
.account-avatar { width: 42px; height: 42px; border: 1px solid color-mix(in srgb, var(--gold) 50%, transparent); border-radius: 50%; }
.salon-account-bar > div:first-child { min-width: 0; }
.account-identity-copy { min-width: 0; display: grid; gap: 2px; }
.account-identity-copy small,.account-identity-copy strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.salon-account-bar small { color: var(--gold); font-size: 9px; font-weight: 800; letter-spacing: .1em; }
.salon-account-bar strong { font-size: 14px; }
.hall-hero { min-height: 290px; display: grid; justify-items: center; align-content: center; padding: 54px 20px 38px; text-align: center; }
.hall-ornament { display: flex; align-items: center; gap: 9px; margin-bottom: 10px; color: var(--gold); }
.hall-ornament i { width: 72px; height: 1px; background: linear-gradient(90deg, transparent, var(--gold)); }
.hall-ornament i:last-child { background: linear-gradient(90deg, var(--gold), transparent); }
.hall-hero h1 { margin: 11px 0 0; font-family: "Songti SC", "STSong", serif; font-size: clamp(48px, 7vw, 72px); font-weight: 650; letter-spacing: .08em; line-height: 1; text-indent: .08em; text-shadow: 0 12px 38px color-mix(in srgb, var(--bg) 55%, transparent); }
.hall-highlights { width: 100%; display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: 20px; color: var(--text-soft); font-size: 11px; font-weight: 750; }
.hall-highlights span { letter-spacing: .08em; text-indent: .08em; }
.hall-highlights b { flex: 0 0 auto; color: var(--gold); font-weight: 400; }
.resume-arcade-card { margin-bottom: 28px; padding: 16px 18px; display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.resume-arcade-card > div { display: flex; gap: 12px; align-items: center; color: var(--gold); }
.resume-arcade-card strong, .resume-arcade-card small { display: block; }
.resume-arcade-card small { margin-top: 3px; color: var(--muted); }

.hall-section + .hall-section { margin-top: 54px; }
.hall-section-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; margin-bottom: 17px; padding: 0 3px; }
.hall-section-heading > div { display: grid; gap: 4px; }
.hall-section-heading small { color: var(--gold); font-size: 9px; font-weight: 850; letter-spacing: .18em; }
.hall-section-heading h2 { margin: 0; font-family: "Songti SC", "STSong", serif; font-size: clamp(25px, 3vw, 34px); font-weight: 650; }
.hall-section-heading p { margin: 0 0 4px; color: var(--muted); font-size: 11px; }

.board-game-collection-card { --card-tone: var(--gold); position: relative; width: 100%; min-height: 326px; display: grid; grid-template-columns: minmax(0, .82fr) minmax(430px, 1.18fr); align-items: center; gap: 42px; overflow: hidden; padding: 34px 38px; border-color: color-mix(in srgb, var(--gold) 28%, var(--line)); color: var(--text); text-align: left; isolation: isolate; cursor: pointer; }
.board-game-collection-card::before { position: absolute; z-index: -1; inset: 0; background: radial-gradient(circle at 78% 42%, color-mix(in srgb, var(--gold) 14%, transparent), transparent 34%), linear-gradient(120deg, color-mix(in srgb, var(--gold) 6%, transparent), transparent 48%); content: ''; }
.collection-copy { min-width: 0; display: grid; align-content: center; justify-items: start; gap: 12px; }
.collection-kicker { display: inline-flex; align-items: center; gap: 7px; color: var(--gold); font-size: 11px; font-weight: 850; letter-spacing: .08em; }
.collection-copy > strong { font-family: "Songti SC", "STSong", serif; font-size: clamp(36px, 4.5vw, 56px); font-weight: 650; letter-spacing: -.035em; line-height: 1.05; }
.collection-copy > em { max-width: 390px; color: var(--text-soft); font-size: 13px; font-style: normal; line-height: 1.7; }
.collection-meta { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 3px; }
.collection-meta b { border: 1px solid color-mix(in srgb, var(--gold) 22%, var(--line)); border-radius: 999px; padding: 6px 9px; color: var(--muted); background: color-mix(in srgb, var(--surface-inset) 82%, transparent); font-size: 9px; font-weight: 800; }
.collection-enter { display: inline-flex; align-items: center; gap: 7px; margin-top: 6px; color: var(--gold); font-size: 12px; font-weight: 850; }
.collection-preview { min-width: 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: center; gap: 12px; perspective: 900px; }
.board-plugin-slot { position: relative; min-width: 0; height: 198px; display: grid; place-items: center; align-content: center; gap: 12px; border: 1px dashed color-mix(in srgb, var(--gold) 40%, var(--line)); border-radius: 18px; color: var(--muted); background: radial-gradient(circle at 50% 30%, color-mix(in srgb, var(--gold) 9%, transparent), transparent 54%), color-mix(in srgb, var(--surface-elevated) 84%, transparent); box-shadow: 0 22px 44px rgba(0,0,0,.18); transform: rotateY(6deg) rotateZ(-2deg); }
.board-plugin-slot:nth-child(2) { z-index: 2; transform: translateY(-10px) scale(1.04); }
.board-plugin-slot:nth-child(3) { transform: rotateY(-6deg) rotateZ(2deg); }
.board-plugin-slot i { width: 48px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--gold) 34%, var(--line)); border-radius: 15px; color: var(--gold); background: color-mix(in srgb, var(--gold) 8%, transparent); font-size: 27px; font-style: normal; font-weight: 300; }
.board-plugin-slot small { font-size: 9px; font-weight: 800; letter-spacing: .08em; }

.game-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); grid-auto-rows: 230px; gap: 13px; }
.game-card { --card-tone: var(--gold); position: relative; height: 100%; min-width: 0; padding: 42px 14px 14px; display: grid; grid-template-rows: minmax(0, 1fr) auto; gap: 10px; border-color: color-mix(in srgb, var(--card-tone) 24%, var(--line)); color: var(--text); text-align: left; overflow: hidden; isolation: isolate; cursor: pointer; }
.game-card::before { position: absolute; z-index: -1; inset: 0; background: radial-gradient(circle at 86% 8%, color-mix(in srgb, var(--card-tone) 14%, transparent), transparent 34%), linear-gradient(145deg, transparent 44%, color-mix(in srgb, var(--card-tone) 4%, transparent)); content: ''; }
.game-card-topline { position: absolute; z-index: 3; top: 15px; right: 14px; left: 14px; display: flex; justify-content: space-between; gap: 7px; color: var(--card-tone); font-style: normal; }
.game-card-topline small { font-size: 9px; font-weight: 850; letter-spacing: .1em; }
.game-card-topline em { color: var(--muted); font-size: 9px; font-style: normal; font-weight: 750; }
.game-copy { position: relative; z-index: 2; display: grid; gap: 4px; min-width: 0; padding-right: 19px; }
.game-copy strong { font-family: "Songti SC", "STSong", serif; font-size: 20px; letter-spacing: .01em; }
.game-copy em { overflow: hidden; color: var(--text-soft); font-size: 11px; font-style: normal; line-height: 1.4; letter-spacing: .015em; text-overflow: ellipsis; white-space: nowrap; }
.enter-game { position: absolute; z-index: 3; right: 13px; bottom: 14px; width: 24px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--card-tone) 34%, transparent); border-radius: 50%; color: var(--card-tone); font-size: 21px; line-height: 1; }

.tone-red { --card-tone: #e88a82; }
.tone-jade { --card-tone: #72d0ad; }
.tone-blue { --card-tone: #86bde4; }
.tone-ink { --card-tone: #d7d8d1; }
.tone-army { --card-tone: #d8b66b; }
.tone-pulse { --card-tone: #8fe0bd; }
.tone-focus { --card-tone: #7ecdb5; }
.tone-mine { --card-tone: #ef9d93; }
.tone-tower { --card-tone: #d9a86c; }
.tone-poker { --card-tone: #ef8c88; }
:global(:root[data-theme="royal"] .tone-red) { --card-tone: #a54e40; }
:global(:root[data-theme="royal"] .tone-jade) { --card-tone: #36785f; }
:global(:root[data-theme="royal"] .tone-blue) { --card-tone: #3f6f91; }
:global(:root[data-theme="royal"] .tone-ink) { --card-tone: #4d4a43; }
:global(:root[data-theme="royal"] .tone-army) { --card-tone: #85651f; }
:global(:root[data-theme="royal"] .tone-pulse) { --card-tone: #39785e; }
:global(:root[data-theme="royal"] .tone-focus) { --card-tone: #346f68; }
:global(:root[data-theme="royal"] .tone-mine) { --card-tone: #a44a42; }
:global(:root[data-theme="royal"] .tone-tower) { --card-tone: #90602d; }
:global(:root[data-theme="royal"] .tone-poker) { --card-tone: #a54e40; }

@media (hover: hover) {
  .board-game-collection-card:hover { border-color: color-mix(in srgb, var(--gold) 52%, var(--line)); box-shadow: 0 30px 80px color-mix(in srgb, var(--bg) 50%, transparent); transform: translateY(-3px); }
  .board-game-collection-card:hover .board-plugin-slot:nth-child(1) { transform: translateX(-5px) rotateY(6deg) rotateZ(-3deg); }
  .board-game-collection-card:hover .board-plugin-slot:nth-child(2) { transform: translateY(-16px) scale(1.05); }
  .board-game-collection-card:hover .board-plugin-slot:nth-child(3) { transform: translateX(5px) rotateY(-6deg) rotateZ(3deg); }
  .game-card:hover { border-color: color-mix(in srgb, var(--card-tone) 48%, var(--line)); box-shadow: 0 24px 60px color-mix(in srgb, var(--bg) 48%, transparent); transform: translateY(-3px); }
  .game-card:hover .enter-game { color: var(--accent-contrast); background: var(--card-tone); }
}

@media (max-width: 960px) {
  .board-game-collection-card { grid-template-columns: minmax(0, .9fr) minmax(330px, 1.1fr); gap: 28px; padding: 30px; }
  .board-plugin-slot { height: 173px; }
  .game-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 680px) {
  .game-hall { padding-right: 11px; padding-bottom: calc(36px + env(safe-area-inset-bottom)); padding-left: 11px; }
  .salon-account-bar { top: calc(7px + env(safe-area-inset-top)); min-height: 62px; border-radius: 15px; padding: 8px 9px; }
  .account-avatar { width: 38px; height: 38px; }
  .account-identity-copy { max-width: min(36vw, 140px); }
  .salon-account-bar small { overflow: hidden; font-size: 7px; text-overflow: ellipsis; white-space: nowrap; }
  .salon-account-bar .account-bar-actions { display: flex; width: auto; }
  .salon-account-bar .account-bar-actions button { flex: 0 0 38px; width: 38px; height: 38px; min-height: 38px; display: inline-flex; align-items: center; justify-content: center; gap: 0; padding: 0; line-height: 0; }
  .salon-account-bar .account-bar-actions button span { display: none; }
  .salon-account-bar .account-bar-actions button :deep(svg) { display: block; flex: 0 0 auto; margin: 0; }
  .hall-hero { min-height: 216px; padding: 39px 5px 27px; }
  .hall-ornament { margin-bottom: 7px; }
  .hall-ornament i { width: 40px; }
  .hall-hero h1 { margin-top: 8px; font-size: 43px; }
  .hall-highlights { gap: 6px; margin-top: 14px; font-size: 8px; }
  .hall-section + .hall-section { margin-top: 38px; }
  .hall-section-heading { align-items: flex-start; flex-direction: column; gap: 4px; margin-bottom: 12px; padding: 0 4px; }
  .hall-section-heading h2 { font-size: 25px; }
  .hall-section-heading p { font-size: 9px; }
  .board-game-collection-card { min-height: 0; grid-template-columns: 1fr; gap: 24px; padding: 24px 18px 19px; border-radius: 18px; }
  .collection-copy { gap: 9px; }
  .collection-copy > strong { font-size: 36px; }
  .collection-copy > em { font-size: 11px; line-height: 1.55; }
  .collection-meta { gap: 5px; }
  .collection-meta b { padding: 5px 7px; font-size: 7px; }
  .collection-enter { margin-top: 2px; font-size: 10px; }
  .collection-preview { gap: 7px; }
  .board-plugin-slot { height: 126px; gap: 8px; border-radius: 12px; }
  .board-plugin-slot i { width: 36px; border-radius: 11px; font-size: 21px; }
  .board-plugin-slot small { font-size: 7px; }
  .game-grid { grid-template-columns: repeat(2,minmax(0,1fr)); grid-auto-rows: 184px; gap: 8px; }
  .game-card { padding: 36px 9px 10px; gap: 7px; border-radius: 13px; }
  .game-copy strong { font-size: 16px; }
  .game-copy em { display: none; }
  .game-card-topline { top: 12px; right: 10px; left: 10px; }
  .game-card-topline small,.game-card-topline em { font-size: 7px; }
  .enter-game { right: 9px; bottom: 10px; width: 20px; font-size: 17px; }
  .resume-arcade-card { align-items: stretch; flex-direction: column; }
}

@media (max-width: 370px) {
  .game-grid { grid-auto-rows: 175px; }
  .board-plugin-slot { height: 116px; }
}
</style>
