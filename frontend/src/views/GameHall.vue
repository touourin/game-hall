<script setup lang="ts">
import { ref } from 'vue'
import { ChevronRight, Gamepad2, History, LogOut, RotateCcw, Settings, Sparkles } from '@lucide/vue'
import type { AccountProfile } from '../account'
import type { GameCatalogItem } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import { GAME_CATALOG } from '../gameCatalog'
import StatsModal from '../components/StatsModal.vue'
import AvatarImage from '../components/AvatarImage.vue'
import GameCardArtwork from '../components/GameCardArtwork.vue'
import ThirdPartyGamesModal from '../components/ThirdPartyGamesModal.vue'
import avalonRoundTable from '../assets/game-hall/avalon-round-table.webp'
import avalonMidnightTable from '../assets/game-hall/avalon-midnight-table.webp'
import avalonIvoryTable from '../assets/game-hall/avalon-ivory-table.webp'

defineProps<{
  account: AccountProfile
}>()
const emit = defineEmits<{
  logout: []
  settings: []
  select: [game: GameCatalogItem]
  resumeRoom: []
}>()
const arcade = useArcadeStore()
const showStats = ref(false)
const showThirdPartyGames = ref(false)

const games = GAME_CATALOG.filter((game) => !game.key.startsWith('plugin-'))
const thirdPartyGames = GAME_CATALOG.filter((game) => game.key.startsWith('plugin-'))

function selectThirdPartyGame(game: GameCatalogItem) {
  showThirdPartyGames.value = false
  emit('select', game)
}
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

    <button
      type="button"
      class="third-party-entry surface"
      aria-label="打开第三方游戏入口"
      @click="showThirdPartyGames = true"
    >
      <span class="third-party-entry-icon"><Gamepad2 :size="22" /></span>
      <span class="third-party-entry-copy">
        <small>EXTENSION ARCADE</small>
        <strong>第三方游戏</strong>
      </span>
      <em>{{ thirdPartyGames.length ? `${thirdPartyGames.length} 款已启用` : '独立插件入口' }}</em>
      <ChevronRight :size="20" />
    </button>

    <section
      v-if="arcade.resumableGame && arcade.resumableRoomCode"
      class="surface resume-arcade-card"
    >
      <div><RotateCcw :size="20" /><span><strong>你有一局尚未结束</strong><small>房间 {{ arcade.resumableRoomCode }}</small></span></div>
      <button type="button" class="primary-button" @click="emit('resumeRoom')">返回对局</button>
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
        <template v-if="index === 0">
          <img class="featured-art featured-art-emerald" :src="avalonRoundTable" alt="" />
          <img class="featured-art featured-art-midnight" :src="avalonMidnightTable" alt="" />
          <img class="featured-art featured-art-royal" :src="avalonIvoryTable" alt="" />
        </template>
        <GameCardArtwork v-else :game-key="game.key" />
        <span class="game-card-topline"><small>{{ game.category }}</small><em>{{ game.players }}</em></span>
        <span class="game-copy">
          <strong>{{ game.name }}</strong>
          <em>{{ game.description }}</em>
        </span>
        <span class="enter-game" aria-hidden="true">›</span>
      </button>
    </section>

    <StatsModal v-if="showStats && !account.isGuest" @close="showStats = false" />
    <ThirdPartyGamesModal
      v-if="showThirdPartyGames"
      :games="thirdPartyGames"
      @close="showThirdPartyGames = false"
      @select="selectThirdPartyGame"
    />
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
.hall-hero { min-height: 305px; display: grid; justify-items: center; align-content: center; padding: 58px 20px 42px; text-align: center; }
.hall-ornament { display: flex; align-items: center; gap: 9px; margin-bottom: 10px; color: var(--gold); }.hall-ornament i { width: 72px; height: 1px; background: linear-gradient(90deg, transparent, var(--gold)); }.hall-ornament i:last-child { background: linear-gradient(90deg, var(--gold), transparent); }
.hall-hero h1 { margin: 11px 0 0; font-family: "Songti SC", "STSong", serif; font-size: clamp(48px, 7vw, 72px); font-weight: 650; letter-spacing: .08em; line-height: 1; text-indent: .08em; text-shadow: 0 12px 38px color-mix(in srgb, var(--bg) 55%, transparent); }
.hall-highlights { width: 100%; display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: 20px; color: var(--text-soft); font-size: 11px; font-weight: 750; }.hall-highlights span { letter-spacing: .08em; text-indent: .08em; }.hall-highlights b { flex: 0 0 auto; color: var(--gold); font-weight: 400; }
.third-party-entry { position: relative; width: 100%; min-height: 76px; display: grid; grid-template-columns: auto minmax(0,1fr) auto auto; align-items: center; gap: 14px; margin: 0 0 22px; padding: 13px 16px; border-color: color-mix(in srgb, var(--gold) 28%, var(--line)); color: var(--text); background: radial-gradient(circle at 86% 0, color-mix(in srgb, var(--gold) 10%, transparent), transparent 34%), color-mix(in srgb, var(--surface-elevated) 91%, transparent); text-align: left; cursor: pointer; overflow: hidden; }
.third-party-entry::after { position: absolute; inset: 0; background: linear-gradient(115deg, transparent 52%, color-mix(in srgb, var(--gold) 4%, transparent)); content: ''; pointer-events: none; }
.third-party-entry-icon { position: relative; z-index: 1; width: 48px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--gold) 34%, var(--line)); border-radius: 15px; color: var(--gold); background: color-mix(in srgb, var(--gold) 9%, var(--surface-inset)); }
.third-party-entry-copy { position: relative; z-index: 1; min-width: 0; display: grid; gap: 3px; }.third-party-entry-copy small { color: var(--gold); font-size: 8px; font-weight: 900; letter-spacing: .17em; }.third-party-entry-copy strong { font-family: "Songti SC", "STSong", serif; font-size: 20px; letter-spacing: .04em; }
.third-party-entry > em { position: relative; z-index: 1; border: 1px solid var(--line); border-radius: 999px; padding: 6px 9px; color: var(--text-soft); background: var(--surface-inset); font-size: 9px; font-style: normal; font-weight: 760; }.third-party-entry > svg { position: relative; z-index: 1; color: var(--gold); }
.resume-arcade-card { margin-bottom: 22px; padding: 16px 18px; display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.resume-arcade-card > div { display: flex; gap: 12px; align-items: center; color: var(--gold); }
.resume-arcade-card strong, .resume-arcade-card small { display: block; }
.resume-arcade-card small { margin-top: 3px; color: var(--muted); }
.game-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); grid-auto-rows: 230px; gap: 13px; }
.game-card { --card-tone: var(--gold); position: relative; height: 100%; min-width: 0; padding: 42px 14px 14px; display: grid; grid-template-rows: minmax(0, 1fr) auto; gap: 10px; border-color: color-mix(in srgb, var(--card-tone) 24%, var(--line)); text-align: left; color: var(--text); overflow: hidden; isolation: isolate; cursor: pointer; }
.game-card:first-child { grid-column: span 2; grid-row: span 2; padding: 32px; align-content: end; }
.game-card::before { position: absolute; z-index: -1; inset: 0; background: radial-gradient(circle at 86% 8%, color-mix(in srgb, var(--card-tone) 14%, transparent), transparent 34%), linear-gradient(145deg, transparent 44%, color-mix(in srgb, var(--card-tone) 4%, transparent)); content: ''; }
.game-card-topline { position: absolute; z-index: 3; top: 15px; right: 14px; left: 14px; display: flex; justify-content: space-between; gap: 7px; color: var(--card-tone); font-style: normal; }.game-card-topline small { font-size: 9px; font-weight: 850; letter-spacing: .1em; }.game-card-topline em { color: var(--muted); font-size: 9px; font-style: normal; font-weight: 750; }
.featured-art { position: absolute; z-index: -2; inset: 0; display: none; width: 100%; height: 100%; object-fit: cover; object-position: center; transition: transform 500ms ease, filter 220ms ease; }.featured-art-emerald { display: block; }
.game-card:first-child::before { z-index: -1; background: linear-gradient(90deg, rgba(3,9,8,.92) 0%, rgba(4,13,11,.74) 40%, rgba(3,8,7,.12) 76%), linear-gradient(0deg, rgba(3,10,8,.78), transparent 58%); }
.game-card:first-child .game-card-topline { top: 26px; right: 28px; left: 28px; }.game-card:first-child .game-card-topline small,.game-card:first-child .game-card-topline em { color: #d6b76e; font-size: 10px; }
.game-copy { position: relative; z-index: 2; display: grid; gap: 4px; min-width: 0; padding-right: 19px; }
.game-copy strong { font-family: "Songti SC", "STSong", serif; font-size: 20px; letter-spacing: .01em; }
.game-copy em { overflow: hidden; color: var(--text-soft); font-size: 11px; font-style: normal; line-height: 1.4; letter-spacing: .015em; text-overflow: ellipsis; white-space: nowrap; }
.game-card:first-child .game-copy { align-self: end; max-width: 55%; gap: 10px; padding: 0 0 12px; }.game-card:first-child .game-copy strong { color: #f4efe1; font-size: clamp(38px,5vw,58px); }.game-card:first-child .game-copy em { color: #aab5aa; font-size: 14px; line-height: 1.6; white-space: normal; }
.enter-game { position: absolute; z-index: 3; right: 13px; bottom: 14px; width: 24px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--card-tone) 34%, transparent); border-radius: 50%; color: var(--card-tone); font-size: 21px; line-height: 1; }
.game-card:first-child .enter-game { right: 29px; bottom: 28px; width: 34px; color: #d6b76e; border-color: rgba(214,183,110,.44); }
.tone-red { --card-tone: #e88a82; }.tone-jade { --card-tone: #72d0ad; }.tone-blue { --card-tone: #86bde4; }.tone-ink { --card-tone: #d7d8d1; }
.tone-army { --card-tone: #d8b66b; }.tone-pulse { --card-tone: #8fe0bd; }.tone-focus { --card-tone: #7ecdb5; }.tone-mine { --card-tone: #ef9d93; }.tone-tower { --card-tone: #d9a86c; }.tone-poker { --card-tone: #ef8c88; }.tone-fortune { --card-tone: #e0b65e; }.tone-suspicion { --card-tone: #d6a765; }
:global(:root[data-theme="royal"] .tone-red) { --card-tone: #a54e40; }:global(:root[data-theme="royal"] .tone-jade) { --card-tone: #36785f; }:global(:root[data-theme="royal"] .tone-blue) { --card-tone: #3f6f91; }:global(:root[data-theme="royal"] .tone-ink) { --card-tone: #4d4a43; }:global(:root[data-theme="royal"] .tone-army) { --card-tone: #85651f; }:global(:root[data-theme="royal"] .tone-pulse) { --card-tone: #39785e; }:global(:root[data-theme="royal"] .tone-focus) { --card-tone: #346f68; }:global(:root[data-theme="royal"] .tone-mine) { --card-tone: #a44a42; }:global(:root[data-theme="royal"] .tone-tower) { --card-tone: #90602d; }:global(:root[data-theme="royal"] .tone-poker) { --card-tone: #a54e40; }:global(:root[data-theme="royal"] .tone-fortune) { --card-tone: #9b6d25; }:global(:root[data-theme="royal"] .tone-suspicion) { --card-tone: #82542d; }
:global(:root[data-theme="midnight"] .featured-art-emerald) { display: none; }:global(:root[data-theme="midnight"] .featured-art-midnight) { display: block; }
:global(:root[data-theme="royal"] .featured-art-emerald) { display: none; }:global(:root[data-theme="royal"] .featured-art-royal) { display: block; }
:global(:root[data-theme="royal"] .game-card:first-child) { border-color: rgba(165,78,64,.34); }
:global(:root[data-theme="royal"] .game-card:first-child::before) { background: linear-gradient(90deg, rgba(249,246,237,.98), rgba(249,246,237,.77) 46%, rgba(249,246,237,.08) 78%), linear-gradient(0deg, rgba(249,246,237,.7), transparent 62%); }
:global(:root[data-theme="royal"] .game-card:first-child .game-card-topline small),:global(:root[data-theme="royal"] .game-card:first-child .game-card-topline em),:global(:root[data-theme="royal"] .game-card:first-child .game-copy strong) { color: #292720; }:global(:root[data-theme="royal"] .game-card:first-child .game-copy em) { color: #716c61; }:global(:root[data-theme="royal"] .game-card:first-child .enter-game) { border-color: rgba(165,78,64,.38); color: #a54e40; }
@media (hover: hover) {
  .third-party-entry:hover { border-color: color-mix(in srgb, var(--gold) 52%, var(--line)); box-shadow: 0 20px 50px color-mix(in srgb, var(--bg) 42%, transparent); transform: translateY(-2px); }
  .game-card:hover { border-color: color-mix(in srgb, var(--card-tone) 48%, var(--line)); box-shadow: 0 24px 60px color-mix(in srgb, var(--bg) 48%, transparent); transform: translateY(-3px); }
  .game-card:hover .featured-art { transform: scale(1.035); }.game-card:hover .enter-game { color: var(--accent-contrast); background: var(--card-tone); }
}
@media (max-width: 960px) {
  .game-grid { grid-template-columns: repeat(3,minmax(0,1fr)); }
}
@media (max-width: 680px) {
  .game-hall { padding-right: 11px; padding-bottom: calc(36px + env(safe-area-inset-bottom)); padding-left: 11px; }
  .salon-account-bar { top: calc(7px + env(safe-area-inset-top)); min-height: 62px; border-radius: 15px; padding: 8px 9px; }.account-avatar { width: 38px; height: 38px; }.account-identity-copy { max-width: min(36vw, 140px); }.salon-account-bar small { overflow: hidden; font-size: 7px; text-overflow: ellipsis; white-space: nowrap; }
  .salon-account-bar .account-bar-actions { display: flex; width: auto; }
  .salon-account-bar .account-bar-actions button { flex: 0 0 38px; width: 38px; height: 38px; min-height: 38px; display: inline-flex; align-items: center; justify-content: center; gap: 0; padding: 0; line-height: 0; }
  .salon-account-bar .account-bar-actions button span { display: none; }
  .salon-account-bar .account-bar-actions button :deep(svg) { display: block; flex: 0 0 auto; margin: 0; }
  .hall-hero { min-height: 216px; padding: 39px 5px 27px; }.hall-ornament { margin-bottom: 7px; }.hall-ornament i { width: 40px; }.hall-hero h1 { margin-top: 8px; font-size: 43px; }.hall-highlights { gap: 6px; margin-top: 14px; font-size: 8px; }
  .third-party-entry { min-height: 66px; gap: 10px; margin-bottom: 12px; padding: 9px 11px; border-radius: 14px; }.third-party-entry-icon { width: 42px; border-radius: 13px; }.third-party-entry-copy small { font-size: 6px; }.third-party-entry-copy strong { font-size: 17px; }.third-party-entry > em { padding: 5px 7px; font-size: 7px; }.third-party-entry > svg { width: 17px; }
  .game-grid { grid-template-columns: repeat(2,minmax(0,1fr)); grid-auto-rows: 184px; gap: 8px; }
  .game-card { padding: 36px 9px 10px; gap: 7px; border-radius: 13px; }
  .game-card:first-child { grid-column: 1 / -1; grid-row: auto; padding: 19px; }
  .game-card:first-child::before { background: linear-gradient(90deg, rgba(3,9,8,.94), rgba(4,13,11,.63) 55%, rgba(3,8,7,.1)), linear-gradient(0deg, rgba(3,10,8,.75), transparent 68%); }
  .featured-art { object-position: center; }.game-card:first-child .game-card-topline { top: 16px; right: 17px; left: 17px; }.game-card:first-child .game-card-topline small,.game-card:first-child .game-card-topline em { font-size: 8px; }
  .game-copy strong { font-size: 16px; }.game-copy em { font-size: 8px; }.game-card:not(:first-child) .game-copy em { display: none; }
  .game-card:first-child .game-copy { max-width: 64%; gap: 5px; padding-bottom: 4px; }.game-card:first-child .game-copy strong { font-size: 29px; }.game-card:first-child .game-copy em { font-size: 10px; line-height: 1.45; }
  .game-card-topline { top: 12px; right: 10px; left: 10px; }.game-card-topline small,.game-card-topline em { font-size: 7px; }
  .game-card:first-child .enter-game { right: 17px; bottom: 15px; width: 27px; }.enter-game { right: 9px; bottom: 10px; width: 20px; font-size: 17px; }
  .resume-arcade-card { align-items: stretch; flex-direction: column; }
}
@media (max-width: 370px) {
  .third-party-entry > em { display: none; }
  .game-grid { grid-auto-rows: 175px; }
}
</style>
