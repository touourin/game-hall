<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  Activity,
  BarChart3,
  ChevronRight,
  Gamepad2,
  Grid3X3,
  History,
  LogOut,
  Radio,
  RotateCcw,
  Settings,
  ShieldCheck,
} from '@lucide/vue'
import type { AccountProfile } from '../account'
import type { ArcadeLobbyRoom, GameCatalogItem } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import { GAME_CATALOG, type GameCatalogEntry } from '../gameCatalog'
import StatsModal from '../components/StatsModal.vue'
import AvatarImage from '../components/AvatarImage.vue'
import GameCardArtwork from '../components/GameCardArtwork.vue'
import NexusGameModule from '../components/NexusGameModule.vue'
import NexusLiveRooms from '../components/NexusLiveRooms.vue'
import ThirdPartyGamesModal from '../components/ThirdPartyGamesModal.vue'

defineProps<{
  account: AccountProfile
}>()

const emit = defineEmits<{
  logout: []
  settings: []
  select: [game: GameCatalogItem]
  openRoom: [payload: { gameKey: ArcadeLobbyRoom['gameKey']; roomCode: string }]
  resumeRoom: []
}>()

const arcade = useArcadeStore()
const showStats = ref(false)
const showThirdPartyGames = ref(false)

const games = GAME_CATALOG.filter((game) => !game.key.startsWith('plugin-')) as GameCatalogEntry[]
const thirdPartyGames = GAME_CATALOG.filter((game) => game.key.startsWith('plugin-'))
const primaryModules = games.slice(0, 4)
const remainingModules = games.slice(4)
const builtInRooms = computed(() => arcade.availableRooms.filter(
  (room) => !room.gameKey.startsWith('plugin-') && !room.cleanupAvailable,
))
const liveRooms = computed(() => [...builtInRooms.value]
  .sort((first, second) => {
    const firstLobby = (first.phase ?? 'lobby') === 'lobby' ? 1 : 0
    const secondLobby = (second.phase ?? 'lobby') === 'lobby' ? 1 : 0
    return secondLobby - firstLobby || second.playerCount - first.playerCount
  })
  .slice(0, 4))
const livePlayerCount = computed(() => builtInRooms.value.reduce(
  (total, room) => total + room.playerCount,
  0,
))
const roomCountByGame = computed(() => builtInRooms.value.reduce<Record<string, number>>(
  (counts, room) => {
    counts[room.gameKey] = (counts[room.gameKey] ?? 0) + 1
    return counts
  },
  {},
))
const featuredGame = games[0]!
const featuredRoom = computed(() => (
  liveRooms.value.find((room) => room.gameKey === featuredGame.key)
  ?? liveRooms.value[0]
  ?? null
))
const featuredCatalogGame = computed(() => (
  featuredRoom.value
    ? games.find((game) => game.key === featuredRoom.value?.gameKey) ?? featuredGame
    : featuredGame
))

function selectThirdPartyGame(game: GameCatalogItem) {
  showThirdPartyGames.value = false
  emit('select', game)
}

function openRoom(room: ArcadeLobbyRoom) {
  emit('openRoom', { gameKey: room.gameKey, roomCode: room.roomCode })
}

function openFeatured() {
  if (featuredRoom.value) {
    openRoom(featuredRoom.value)
    return
  }
  emit('select', featuredCatalogGame.value)
}
</script>

<template>
  <main class="game-hall page-container adaptive-layout-root">
    <aside class="nexus-rail" aria-label="大厅导航">
      <span class="nexus-rail-mark" aria-hidden="true">NX</span>
      <button type="button" class="active" aria-label="当前页面：游戏大厅"><Grid3X3 :size="18" /><span>大厅</span></button>
      <button v-if="!account.isGuest" type="button" aria-label="大厅导航：查看战绩" @click="showStats = true"><BarChart3 :size="18" /><span>战绩</span></button>
      <button type="button" aria-label="大厅导航：打开设置" @click="emit('settings')"><Settings :size="18" /><span>设置</span></button>
      <AvatarImage class="nexus-rail-avatar" :src="account.avatarUrl" :name="account.playerName" />
    </aside>

    <div class="nexus-hall-shell">
      <header class="nexus-topbar surface">
        <div class="nexus-title-block">
          <span><i /> NEXUS // GAME GRID</span>
          <h1>竞技大厅</h1>
        </div>

        <div class="nexus-system-metrics" aria-label="大厅实时状态">
          <span><i :class="{ offline: !arcade.connected }" />{{ arcade.connected ? 'ASIA-01' : 'RECONNECTING' }}</span>
          <span>{{ livePlayerCount }} ONLINE</span>
          <span>{{ builtInRooms.length }} ROOMS</span>
        </div>

        <section class="account-bar salon-account-bar" aria-label="当前登录账号">
          <div>
            <AvatarImage class="avatar account-avatar" :src="account.avatarUrl" :name="account.playerName" />
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
      </header>

      <section v-if="arcade.resumableGame && arcade.resumableRoomCode" class="surface resume-arcade-card nexus-resume-card">
        <div><RotateCcw :size="20" /><span><small>SESSION RECOVERY</small><strong>检测到一局尚未结束</strong><em>房间 {{ arcade.resumableRoomCode }}</em></span></div>
        <button type="button" class="primary-button" @click="emit('resumeRoom')">返回对局</button>
      </section>

      <section class="nexus-command-grid">
        <article class="nexus-feature surface">
          <header><span>FEATURED MATCH</span><b><i />{{ featuredRoom ? 'LIVE ROOM' : 'RECOMMENDED' }}</b></header>

          <div class="nexus-arena" aria-hidden="true">
            <span class="nexus-ring nexus-ring-outer" />
            <span class="nexus-ring nexus-ring-inner" />
            <span class="nexus-arena-core">
              <GameCardArtwork :game-key="featuredCatalogGame.key" />
              <small>{{ featuredRoom ? `${featuredRoom.playerCount}/${featuredRoom.maxPlayers}` : featuredCatalogGame.players.replace(' 人', 'P') }}</small>
            </span>
            <i class="nexus-ping ping-one" /><i class="nexus-ping ping-two" /><i class="nexus-ping ping-three" /><i class="nexus-ping ping-four" />
          </div>

          <div class="nexus-feature-copy">
            <span><small>{{ featuredCatalogGame.category }} // {{ featuredCatalogGame.players }}</small><strong>{{ featuredRoom?.roomName || `${featuredCatalogGame.name}精选对局` }}</strong><em>{{ featuredRoom ? `${featuredRoom.hostName}正在等待玩家加入` : featuredCatalogGame.description }}</em></span>
            <button type="button" @click="openFeatured">{{ featuredRoom ? '查看房间' : '进入游戏' }}<ChevronRight :size="17" /></button>
          </div>
        </article>

        <section class="nexus-module-preview" aria-label="主要游戏模块">
          <header class="nexus-section-heading"><span><small>SELECT MODULE</small><strong>快速启动</strong></span><em>{{ games.length }} AVAILABLE</em></header>
          <div>
            <NexusGameModule
              v-for="(game, index) in primaryModules"
              :key="game.key"
              :game="game"
              :index="index"
              :room-count="roomCountByGame[game.key]"
              @select="emit('select', game)"
            />
          </div>
        </section>

        <NexusLiveRooms :rooms="liveRooms" :connected="arcade.connected" @open="openRoom" />
      </section>

      <section class="nexus-all-modules">
        <header class="nexus-section-heading nexus-all-heading">
          <span><small>MODULE LIBRARY</small><strong>全部游戏模块</strong></span>
          <div><Activity :size="15" /><span>{{ games.length }} MODULES</span><i />SYSTEM READY</div>
        </header>
        <div class="game-grid" aria-label="选择游戏">
          <NexusGameModule
            v-for="(game, index) in remainingModules"
            :key="game.key"
            :game="game"
            :index="index + primaryModules.length"
            :room-count="roomCountByGame[game.key]"
            @select="emit('select', game)"
          />
        </div>
      </section>

      <button type="button" class="third-party-entry surface" aria-label="打开第三方游戏入口" @click="showThirdPartyGames = true">
        <span class="third-party-entry-icon"><Gamepad2 :size="20" /></span>
        <span class="third-party-entry-copy"><small>EXTERNAL MODULE BAY</small><strong>第三方游戏</strong></span>
        <em>{{ thirdPartyGames.length ? `${thirdPartyGames.length} 款已启用` : '独立插件入口' }}</em>
        <ChevronRight :size="18" />
      </button>

      <footer class="nexus-system-footer">
        <span><ShieldCheck :size="13" />安全会话已启用</span>
        <span><Radio :size="13" />大厅信号实时同步</span>
        <small>NEXUS BUILD 2026.08</small>
      </footer>
    </div>

    <nav class="nexus-mobile-dock" aria-label="手机端大厅导航">
      <button type="button" class="active" aria-label="当前页面：游戏大厅"><Grid3X3 :size="19" /><span>大厅</span></button>
      <button v-if="!account.isGuest" type="button" aria-label="手机端：查看战绩" @click="showStats = true"><BarChart3 :size="19" /><span>战绩</span></button>
      <button type="button" aria-label="手机端：打开设置" @click="emit('settings')"><Settings :size="19" /><span>设置</span></button>
      <button type="button" :aria-label="account.isGuest ? '手机端：退出游客模式' : '手机端：退出登录'" @click="emit('logout')"><LogOut :size="19" /><span>退出</span></button>
    </nav>

    <StatsModal v-if="showStats && !account.isGuest" @close="showStats = false" />
    <ThirdPartyGamesModal v-if="showThirdPartyGames" :games="thirdPartyGames" @close="showThirdPartyGames = false" @select="selectThirdPartyGame" />
  </main>
</template>

<style scoped>
.game-hall { position: relative; width: min(100%, 1280px); display: grid; grid-template-columns: 58px minmax(0,1fr); gap: 16px; padding-bottom: 70px; }
.nexus-hall-shell { min-width: 0; }
.nexus-rail { position: sticky; z-index: 24; top: calc(18px + env(safe-area-inset-top)); height: calc(100dvh - 36px - env(safe-area-inset-top)); min-height: 520px; display: flex; flex-direction: column; align-items: center; gap: 15px; border: 1px solid var(--line); border-radius: var(--radius-md); padding: 0 9px 13px; background: color-mix(in srgb,var(--surface-elevated) 94%,transparent); box-shadow: var(--shadow-card); backdrop-filter: blur(18px); }
.nexus-rail-mark { width: calc(100% + 18px); height: 59px; display: grid; place-items: center; border-bottom: 1px solid var(--line); color: var(--gold); font-family: ui-monospace,"SFMono-Regular",Consolas,monospace; font-size: 10px; font-weight: 850; letter-spacing: .12em; }
.nexus-rail button { position: relative; width: 38px; height: 38px; display: grid; place-items: center; border: 0; border-radius: var(--radius-sm); color: var(--muted); background: transparent; cursor: pointer; }.nexus-rail button span { position:absolute; left:48px; opacity:0; pointer-events:none; border:1px solid var(--line); border-radius:4px; padding:5px 7px; color:var(--text); background:var(--surface-elevated); font-size:8px; white-space:nowrap; transition:opacity .16s; }.nexus-rail button.active { color:var(--accent-contrast); background:var(--gold); box-shadow:var(--glow-primary); }.nexus-rail-avatar { width:31px; aspect-ratio:1; margin-top:auto; border:1px solid var(--line-strong); border-radius:4px; color:var(--gold); background:var(--surface-soft); font-size:9px; font-weight:850; }
.nexus-topbar { min-height:68px; display:grid; grid-template-columns:minmax(160px,1fr) auto minmax(300px,1.2fr); align-items:center; gap:18px; margin-bottom:14px; padding:8px 12px 8px 17px; }
.nexus-title-block>span { display:flex; align-items:center; gap:6px; color:var(--gold); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:6px; font-weight:800; letter-spacing:.18em; }.nexus-title-block>span i { width:5px; height:5px; border-radius:50%; background:var(--green); box-shadow:0 0 8px var(--green); }.nexus-title-block h1 { margin:3px 0 0; font-size:18px; font-weight:800; }
.nexus-system-metrics { display:flex; gap:16px; color:var(--muted); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:6px; letter-spacing:.08em; }.nexus-system-metrics span { display:flex; align-items:center; gap:5px; white-space:nowrap; }.nexus-system-metrics i { width:5px; height:5px; border-radius:50%; background:var(--green); box-shadow:0 0 8px var(--green); }.nexus-system-metrics i.offline { background:var(--red); box-shadow:0 0 8px var(--red); }
.salon-account-bar { min-height:50px; border:0; border-left:1px solid var(--line); padding:0 0 0 15px; background:transparent; box-shadow:none; backdrop-filter:none; }.account-avatar { width:34px; height:34px; border:1px solid var(--line-strong); border-radius:4px; }.account-identity-copy { min-width:0; display:grid; gap:2px; }.account-identity-copy small,.account-identity-copy strong { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }.salon-account-bar small { color:var(--gold); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:6px; letter-spacing:.08em; }.salon-account-bar strong { font-size:11px; }.salon-account-bar .account-bar-actions { margin-left:auto; }.salon-account-bar .account-bar-actions button { min-width:35px; min-height:35px; justify-content:center; border-radius:4px; padding:0 8px; font-size:8px; }.salon-account-bar .account-bar-actions button span { display:none; }
.nexus-resume-card { min-height:64px; display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:14px; padding:10px 13px; border-color:color-mix(in srgb,var(--gold) 34%,var(--line)); }.nexus-resume-card>div { display:flex; align-items:center; gap:10px; color:var(--gold); }.nexus-resume-card>div>span { display:grid; gap:2px; }.nexus-resume-card small { font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:6px; letter-spacing:.14em; }.nexus-resume-card strong { color:var(--text); font-size:11px; }.nexus-resume-card em { color:var(--muted); font-size:7px; font-style:normal; }.nexus-resume-card .primary-button { min-height:38px; border-radius:4px; font-size:9px; }
.nexus-command-grid { display:grid; grid-template-columns:minmax(300px,1.02fr) minmax(390px,1.22fr) minmax(255px,.78fr); gap:12px; align-items:stretch; }
.nexus-feature { position:relative; min-height:488px; overflow:hidden; padding:14px; border-color:color-mix(in srgb,var(--gold) 27%,var(--line)); background:radial-gradient(circle at 50% 38%,color-mix(in srgb,var(--gold) 9%,transparent),transparent 42%),var(--material-pattern),var(--surface); background-size:auto,var(--material-size),auto; }
.nexus-feature>header { display:flex; justify-content:space-between; color:var(--muted); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:6px; letter-spacing:.13em; }.nexus-feature>header b { display:flex; align-items:center; gap:5px; color:var(--accent-secondary); font-weight:700; }.nexus-feature>header i { width:5px; height:5px; border-radius:50%; background:var(--accent-secondary); box-shadow:0 0 8px var(--accent-secondary); }
.nexus-arena { position:absolute; width:min(85%,330px); aspect-ratio:1; top:47%; left:50%; transform:translate(-50%,-50%); }.nexus-ring { position:absolute; border:1px solid color-mix(in srgb,var(--gold) 32%,transparent); border-radius:50%; }.nexus-ring-outer { inset:4%; box-shadow:0 0 42px color-mix(in srgb,var(--gold) 8%,transparent); }.nexus-ring-outer::before,.nexus-ring-outer::after { position:absolute; inset:9%; border:1px solid color-mix(in srgb,var(--gold) 13%,transparent); border-radius:50%; content:''; }.nexus-ring-outer::after { inset:22%; border-color:color-mix(in srgb,var(--accent-secondary) 38%,transparent); border-style:dashed; }.nexus-ring-inner { inset:34%; border-color:var(--gold); box-shadow:var(--glow-primary); }.nexus-arena-core { position:absolute; inset:21%; display:grid; place-items:center; overflow:hidden; border:1px solid color-mix(in srgb,var(--gold) 68%,var(--line)); border-radius:50%; color:var(--gold); background:var(--surface-inset); box-shadow:0 0 42px color-mix(in srgb,var(--gold) 20%,transparent),inset 0 0 24px rgba(0,0,0,.5); }.nexus-arena-core :deep(.game-card-art) { width:100%; height:100%; min-height:0; border:0; border-radius:50%; }.nexus-arena-core :deep(.game-card-art-vignette) { background:radial-gradient(circle at 50% 46%,transparent 43%,rgba(2,6,10,.38) 76%,rgba(2,6,10,.78) 100%); }.nexus-arena-core small { position:absolute; z-index:4; bottom:8%; left:50%; border:1px solid color-mix(in srgb,var(--gold) 50%,transparent); border-radius:999px; padding:3px 7px; color:var(--gold); background:rgba(3,8,13,.82); box-shadow:0 0 14px rgba(0,0,0,.45); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:6px; letter-spacing:.08em; transform:translateX(-50%); backdrop-filter:blur(7px); }.nexus-ping { position:absolute; width:9px; height:9px; border:2px solid var(--accent-secondary); border-radius:50%; background:var(--surface-elevated); box-shadow:0 0 11px var(--accent-secondary); }.ping-one { left:22%; top:18%; }.ping-two { right:15%; top:35%; }.ping-three { right:27%; bottom:13%; }.ping-four { left:12%; bottom:31%; }
.nexus-feature-copy { position:absolute; right:14px; bottom:14px; left:14px; display:flex; align-items:flex-end; justify-content:space-between; gap:12px; }.nexus-feature-copy>span { min-width:0; display:grid; gap:5px; }.nexus-feature-copy small { color:var(--muted); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:6px; letter-spacing:.13em; }.nexus-feature-copy strong { font-size:clamp(20px,2.4vw,31px); line-height:1.05; }.nexus-feature-copy em { overflow:hidden; color:var(--muted); font-size:8px; font-style:normal; text-overflow:ellipsis; white-space:nowrap; }.nexus-feature-copy button { flex:0 0 auto; min-height:39px; display:inline-flex; align-items:center; gap:4px; border:0; border-radius:3px; padding:0 10px; color:var(--accent-contrast); background:var(--gold); font-size:8px; font-weight:850; cursor:pointer; }
.nexus-module-preview { min-width:0; }.nexus-section-heading { min-height:45px; display:flex; align-items:center; justify-content:space-between; gap:12px; padding:0 2px 10px; }.nexus-section-heading>span { display:grid; gap:3px; }.nexus-section-heading small { color:var(--gold); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:7px; font-weight:800; letter-spacing:.18em; }.nexus-section-heading strong { font-size:15px; }.nexus-section-heading>em { color:var(--muted); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:6px; font-style:normal; }.nexus-module-preview>div { display:grid; grid-template-columns:1fr 1fr; gap:8px; }.nexus-module-preview :deep(.nexus-game-module) { min-height:217px; }
.nexus-all-modules { margin-top:25px; }.nexus-all-heading { border-bottom:1px solid var(--line); margin-bottom:12px; padding:0 2px 13px; }.nexus-all-heading>div { display:flex; align-items:center; gap:7px; color:var(--muted); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:6px; }.nexus-all-heading>div>i { width:5px; height:5px; border-radius:50%; background:var(--green); box-shadow:0 0 8px var(--green); }.game-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:9px; }
.third-party-entry { width:100%; min-height:66px; display:grid; grid-template-columns:auto minmax(0,1fr) auto auto; align-items:center; gap:12px; margin-top:18px; padding:9px 13px; color:var(--text); text-align:left; cursor:pointer; }.third-party-entry-icon { width:40px; aspect-ratio:1; display:grid; place-items:center; border:1px solid color-mix(in srgb,var(--accent-secondary) 34%,var(--line)); border-radius:4px; color:var(--accent-secondary); background:color-mix(in srgb,var(--accent-secondary) 8%,var(--surface-inset)); }.third-party-entry-copy { display:grid; gap:3px; }.third-party-entry-copy small { color:var(--accent-secondary); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:6px; letter-spacing:.14em; }.third-party-entry-copy strong { font-size:13px; }.third-party-entry>em { color:var(--muted); font-size:7px; font-style:normal; }.third-party-entry>svg { color:var(--muted); }
.nexus-system-footer { display:flex; align-items:center; gap:18px; margin-top:13px; padding:0 3px; color:var(--muted); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:6px; }.nexus-system-footer span { display:inline-flex; align-items:center; gap:5px; }.nexus-system-footer small { margin-left:auto; font-size:6px; }
.nexus-mobile-dock { display:none; }
@media (hover:hover) { .nexus-rail button:hover span { opacity:1; }.nexus-rail button:hover:not(.active) { color:var(--gold); background:color-mix(in srgb,var(--gold) 8%,transparent); }.nexus-feature-copy button:hover { box-shadow:var(--glow-primary); transform:translateY(-2px); }.third-party-entry:hover { border-color:color-mix(in srgb,var(--accent-secondary) 45%,var(--line)); transform:translateY(-2px); } }
@media (max-width:1120px) { .nexus-command-grid { grid-template-columns:minmax(280px,.9fr) minmax(390px,1.1fr); }.nexus-command-grid :deep(.nexus-live-rooms) { grid-column:1/-1; }.game-grid { grid-template-columns:repeat(3,minmax(0,1fr)); } }
@media (max-width:820px) { .game-hall { display:block; padding-right:12px; padding-bottom:calc(92px + env(safe-area-inset-bottom)); padding-left:12px; }.nexus-rail { display:none; }.nexus-topbar { grid-template-columns:1fr auto; min-height:64px; padding:9px 10px 9px 13px; }.nexus-system-metrics { display:none; }.salon-account-bar { min-width:0; border-left:0; padding-left:0; }.salon-account-bar>div:first-child { display:none; }.nexus-command-grid { grid-template-columns:1fr; }.nexus-feature { min-height:410px; }.nexus-module-preview { order:2; }.nexus-command-grid :deep(.nexus-live-rooms) { order:3; grid-column:auto; }.nexus-module-preview>div { gap:7px; }.nexus-module-preview :deep(.nexus-game-module) { min-height:175px; }.game-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }.nexus-mobile-dock { position:fixed; z-index:35; right:10px; bottom:calc(8px + env(safe-area-inset-bottom)); left:10px; min-height:58px; display:grid; grid-template-columns:repeat(4,1fr); gap:3px; border:1px solid var(--line-strong); border-radius:9px; padding:4px; background:color-mix(in srgb,var(--surface-elevated) 95%,transparent); box-shadow:0 18px 45px rgba(0,0,0,.48),var(--glow-primary); backdrop-filter:blur(20px); }.nexus-mobile-dock button { min-width:0; display:grid; place-items:center; align-content:center; gap:2px; border:0; border-radius:5px; color:var(--muted); background:transparent; font-size:7px; }.nexus-mobile-dock button.active { color:var(--accent-contrast); background:var(--gold); }.nexus-system-footer { padding-bottom:3px; } }
@media (max-width:520px) { .nexus-title-block h1 { font-size:16px; }.salon-account-bar .account-bar-actions { gap:4px; }.salon-account-bar .account-bar-actions button { width:34px; min-width:34px; height:34px; padding:0; }.nexus-feature { min-height:375px; }.nexus-arena { top:45%; width:86%; }.nexus-feature-copy { align-items:stretch; flex-direction:column; }.nexus-feature-copy button { align-self:flex-start; }.nexus-all-modules { margin-top:19px; }.nexus-all-heading>div span { display:none; }.third-party-entry { grid-template-columns:auto minmax(0,1fr) auto; }.third-party-entry>em { display:none; }.nexus-system-footer span:nth-child(2) { display:none; } }
@media (max-width:370px) { .nexus-module-preview>div,.game-grid { grid-template-columns:1fr; }.nexus-module-preview :deep(.nexus-game-module) { min-height:168px; }.nexus-system-footer small { display:none; } }
</style>
