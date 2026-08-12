<script setup lang="ts">
import { computed, ref } from 'vue'
import {
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
  Signal,
  UserRound,
} from '@lucide/vue'
import type { AccountProfile } from '../account'
import { GAME_CATALOG, gameCatalogItem, type GameCatalogEntry } from '../gameCatalog'
import type { ArcadeLobbyRoom, GameCatalogItem } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import AvatarImage from '../components/AvatarImage.vue'
import GameCardArtwork from '../components/GameCardArtwork.vue'
import GameLibraryCard from '../components/GameLibraryCard.vue'
import LobbyRoomPanel from '../components/LobbyRoomPanel.vue'
import StatsModal from '../components/StatsModal.vue'
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
const gamesSection = ref<HTMLElement | null>(null)
const roomsSection = ref<HTMLElement | null>(null)

const games = GAME_CATALOG.filter((game) => !game.key.startsWith('plugin-')) as GameCatalogEntry[]
const thirdPartyGames = GAME_CATALOG.filter((game) => game.key.startsWith('plugin-'))
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

const hubRoom = computed(() => liveRooms.value[0] ?? null)
const hubGame = computed(() => {
  if (arcade.resumableGame) {
    const resumable = gameCatalogItem(arcade.resumableGame)
    if (resumable && !resumable.key.startsWith('plugin-')) return resumable
  }
  if (hubRoom.value) {
    const live = gameCatalogItem(hubRoom.value.gameKey)
    if (live && !live.key.startsWith('plugin-')) return live
  }
  return games.find((game) => game.key === 'go') ?? games[0]!
})
const hubMode = computed<'resume' | 'room' | 'discover'>(() => {
  if (arcade.resumableGame && arcade.resumableRoomCode) return 'resume'
  if (hubRoom.value) return 'room'
  return 'discover'
})
const hubTitle = computed(() => {
  if (hubMode.value === 'resume') return `继续上局 · ${hubGame.value.name}`
  if (hubMode.value === 'room') return hubRoom.value?.roomName || `${hubGame.value.name}公开房间`
  return `从 ${hubGame.value.name} 开始`
})
const hubDescription = computed(() => {
  if (hubMode.value === 'resume') return `房间 ${arcade.resumableRoomCode} 仍在等待你，进度已经安全保留。`
  if (hubMode.value === 'room') {
    const room = hubRoom.value!
    return `${room.hostName}创建 · ${room.playerCount}/${room.maxPlayers} 人 · ${room.phase === 'lobby' ? '等待加入' : '对局进行中'}`
  }
  return `${hubGame.value.description}，支持 ${hubGame.value.players}。`
})
const hubActionLabel = computed(() => {
  if (hubMode.value === 'resume') return '继续对局'
  if (hubMode.value === 'room') return '查看房间'
  return '开始游戏'
})

function selectThirdPartyGame(game: GameCatalogItem) {
  showThirdPartyGames.value = false
  emit('select', game)
}

function openRoom(room: ArcadeLobbyRoom) {
  emit('openRoom', { gameKey: room.gameKey, roomCode: room.roomCode })
}

function openHub() {
  if (hubMode.value === 'resume') {
    emit('resumeRoom')
    return
  }
  if (hubMode.value === 'room' && hubRoom.value) {
    openRoom(hubRoom.value)
    return
  }
  emit('select', hubGame.value)
}

function scrollTo(section: HTMLElement | null) {
  section?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <main class="game-hall page-container adaptive-layout-root">
    <aside class="hall-sidebar" aria-label="大厅导航">
      <span class="hall-sidebar-mark" aria-hidden="true">竞</span>
      <button type="button" aria-label="查看全部游戏" @click="scrollTo(gamesSection)">
        <Grid3X3 :size="19" /><span>全部游戏</span>
      </button>
      <button type="button" aria-label="查看实时房间" @click="scrollTo(roomsSection)">
        <Radio :size="19" /><span>房间</span>
      </button>
      <button v-if="!account.isGuest" type="button" aria-label="大厅导航：查看战绩" @click="showStats = true">
        <BarChart3 :size="19" /><span>战绩</span>
      </button>
      <button type="button" aria-label="大厅导航：打开设置" @click="emit('settings')">
        <Settings :size="19" /><span>设置</span>
      </button>
      <AvatarImage class="hall-sidebar-avatar" :src="account.avatarUrl" :name="account.playerName" />
    </aside>

    <div class="hall-shell">
      <header class="hall-topbar surface">
        <div class="hall-title-block">
          <small><i /> GAME CENTER</small>
          <h1>竞技大厅</h1>
        </div>

        <div class="hall-system-metrics" aria-label="大厅实时状态">
          <span><i :class="{ offline: !arcade.connected }" />{{ arcade.connected ? '连接正常' : '正在重连' }}</span>
          <span>{{ livePlayerCount }} 位玩家</span>
          <span>{{ builtInRooms.length }} 个房间</span>
        </div>

        <section class="account-bar hall-account-bar" aria-label="当前登录账号">
          <div>
            <AvatarImage class="account-avatar" :src="account.avatarUrl" :name="account.playerName" />
            <span class="account-identity-copy">
              <small>{{ account.isGuest ? '游客席位 · 对局不计战绩' : `玩家账号 · ${account.username}` }}</small>
              <strong>{{ account.playerName }}</strong>
            </span>
          </div>
          <div class="account-bar-actions">
            <button v-if="!account.isGuest" type="button" aria-label="查看全部战绩" @click="showStats = true"><History :size="17" /><span>全部战绩</span></button>
            <button type="button" aria-label="打开设置" @click="emit('settings')"><Settings :size="17" /><span>设置</span></button>
            <button type="button" :aria-label="account.isGuest ? '退出游客模式' : '退出登录'" @click="emit('logout')"><LogOut :size="17" /><span>退出</span></button>
          </div>
        </section>
      </header>

      <section class="hall-command-center" aria-labelledby="command-center-title">
        <header class="hall-section-heading hall-command-heading">
          <span>
            <small>对局与房间</small>
            <strong id="command-center-title">对局中枢</strong>
            <em>回到进行中的对局，或从公开房间开始下一局</em>
          </span>
          <div><Signal :size="15" />大厅数据实时同步</div>
        </header>

        <div class="hall-command-grid">
          <article class="hall-hub surface">
            <div class="hall-hub-copy">
              <span class="hall-hub-kicker">
                <RotateCcw v-if="hubMode === 'resume'" :size="15" />
                <Radio v-else-if="hubMode === 'room'" :size="15" />
                <Gamepad2 v-else :size="15" />
                {{ hubMode === 'resume' ? '继续上局' : hubMode === 'room' ? '公开房间' : '为你推荐' }}
              </span>
              <h2>{{ hubTitle }}</h2>
              <p>{{ hubDescription }}</p>
              <button type="button" class="primary-button" @click="openHub">
                {{ hubActionLabel }}<ChevronRight :size="18" />
              </button>
            </div>

            <div class="hall-hub-art" :class="`tone-${hubGame.tone}`">
              <span class="hall-hub-orbit" aria-hidden="true" />
              <GameCardArtwork :game-key="hubGame.key" />
              <small>{{ hubGame.category }} · {{ hubGame.players }}</small>
            </div>
          </article>

          <div class="hall-command-side">
            <div ref="roomsSection" class="hall-room-anchor">
              <LobbyRoomPanel :rooms="liveRooms" :connected="arcade.connected" @open="openRoom" />
            </div>

            <button
              v-if="!account.isGuest"
              type="button"
              class="hall-personal-card surface"
              aria-label="查看个人对局数据"
              @click="showStats = true"
            >
              <span><UserRound :size="19" /><small>个人中心</small><strong>战绩与排行榜</strong></span>
              <em>查看你的场次、胜负和游戏排名</em>
              <ChevronRight :size="18" />
            </button>
            <div v-else class="hall-personal-card hall-guest-card surface">
              <span><ShieldCheck :size="19" /><small>当前模式</small><strong>游客休闲席位</strong></span>
              <em>可加入公开房间；本局不会记录个人战绩</em>
            </div>
          </div>
        </div>
      </section>

      <section ref="gamesSection" class="hall-all-games" aria-labelledby="all-games-title">
        <header class="hall-section-heading hall-all-heading">
          <span>
            <small>游戏库</small>
            <strong id="all-games-title">全部游戏</strong>
            <em>统一入口，规则和玩法保持各自独立</em>
          </span>
          <div>{{ games.length }} 款可用</div>
        </header>

        <div class="game-grid" aria-label="选择游戏">
          <GameLibraryCard
            v-for="(game, index) in games"
            :key="game.key"
            :game="game"
            :index="index"
            :room-count="roomCountByGame[game.key]"
            @select="emit('select', game)"
          />
        </div>
      </section>

      <button type="button" class="third-party-entry surface" aria-label="打开第三方游戏入口" @click="showThirdPartyGames = true">
        <span class="third-party-entry-icon"><Gamepad2 :size="20" /></span>
        <span class="third-party-entry-copy"><small>独立插件</small><strong>第三方游戏</strong></span>
        <em>{{ thirdPartyGames.length ? `${thirdPartyGames.length} 款已启用` : '独立插件入口' }}</em>
        <ChevronRight :size="18" />
      </button>

      <footer class="hall-system-footer">
        <span><ShieldCheck :size="14" />安全会话已启用</span>
        <span><Radio :size="14" />大厅信号实时同步</span>
      </footer>
    </div>

    <nav class="hall-mobile-dock" aria-label="手机端大厅导航">
      <button type="button" aria-label="手机端：全部游戏" @click="scrollTo(gamesSection)"><Grid3X3 :size="21" /><span>全部游戏</span></button>
      <button type="button" aria-label="手机端：实时房间" @click="scrollTo(roomsSection)"><Radio :size="21" /><span>房间</span></button>
      <button v-if="!account.isGuest" type="button" aria-label="手机端：查看战绩" @click="showStats = true"><BarChart3 :size="21" /><span>战绩</span></button>
      <button type="button" aria-label="手机端：打开设置" @click="emit('settings')"><Settings :size="21" /><span>设置</span></button>
    </nav>

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
.game-hall {
  position: relative;
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  gap: 18px;
  width: min(100%, 1380px);
  padding-bottom: 72px;
}

.hall-shell {
  min-width: 0;
}

.hall-sidebar {
  position: sticky;
  z-index: 24;
  top: calc(18px + env(safe-area-inset-top));
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 13px;
  height: calc(100dvh - 36px - env(safe-area-inset-top));
  min-height: 520px;
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  padding: 0 10px 14px;
  background: var(--surface-glass);
  box-shadow: var(--shadow-card), inset 0 1px 0 var(--metal-edge);
  backdrop-filter: blur(24px) saturate(110%);
}

.hall-sidebar-mark {
  display: grid;
  place-items: center;
  width: calc(100% + 20px);
  height: 64px;
  border-bottom: 1px solid var(--line);
  color: var(--text);
  font-size: 16px;
  font-weight: 880;
}

.hall-sidebar button {
  position: relative;
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border: 0;
  border-radius: var(--radius-control);
  color: var(--muted);
  background: transparent;
  cursor: pointer;
}

.hall-sidebar button span {
  position: absolute;
  left: 52px;
  border: 1px solid var(--line);
  border-radius: 9px;
  padding: 6px 9px;
  opacity: 0;
  color: var(--text);
  background: var(--surface-elevated);
  box-shadow: var(--shadow-contact);
  font-size: 10px;
  white-space: nowrap;
  pointer-events: none;
}

.hall-sidebar-avatar {
  width: 36px;
  aspect-ratio: 1;
  margin-top: auto;
  border: 1px solid var(--line-strong);
  border-radius: 50%;
  background: var(--surface-soft);
}

.hall-topbar {
  display: grid;
  grid-template-columns: minmax(150px, 0.8fr) auto minmax(310px, 1.15fr);
  align-items: center;
  gap: 22px;
  min-height: 78px;
  margin-bottom: 26px;
  padding: 10px 14px 10px 22px;
}

.hall-title-block small {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--muted);
  font-size: 9px;
  font-weight: 760;
  letter-spacing: .12em;
}

.hall-title-block small i,
.hall-system-metrics i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 10px color-mix(in srgb, var(--green) 52%, transparent);
}

.hall-title-block h1 {
  margin: 3px 0 0;
  font-size: 21px;
  font-weight: 850;
  letter-spacing: -.02em;
}

.hall-system-metrics {
  display: flex;
  gap: 16px;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 10px 14px;
  color: var(--muted);
  background: var(--surface-inset);
  font-size: 10px;
}

.hall-system-metrics span {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.hall-system-metrics i.offline {
  background: var(--red);
  box-shadow: none;
}

.hall-account-bar {
  min-width: 0;
  min-height: 52px;
  border: 0;
  border-left: 1px solid var(--line);
  padding: 0 0 0 18px;
}

.account-avatar {
  width: 38px;
  height: 38px;
  border: 1px solid var(--line-strong);
  border-radius: 50%;
}

.account-identity-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.account-identity-copy small,
.account-identity-copy strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hall-account-bar small {
  color: var(--muted);
  font-size: 9px;
}

.hall-account-bar strong {
  font-size: 13px;
}

.hall-account-bar .account-bar-actions {
  margin-left: auto;
}

.hall-account-bar .account-bar-actions button {
  width: 38px;
  height: 38px;
  min-height: 0;
  justify-content: center;
  border-radius: 50%;
  padding: 0;
  background: var(--surface-glass);
  box-shadow: var(--shadow-contact), inset 0 1px 0 var(--metal-edge);
}

.hall-account-bar .account-bar-actions button span {
  display: none;
}

.hall-section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  padding: 0 4px 14px;
}

.hall-section-heading > span {
  display: grid;
  gap: 4px;
}

.hall-section-heading small {
  color: var(--gold);
  font-size: 10px;
  font-weight: 780;
  letter-spacing: .08em;
}

.hall-section-heading strong {
  font-size: clamp(23px, 2.5vw, 31px);
  letter-spacing: -.035em;
}

.hall-section-heading em {
  color: var(--muted);
  font-size: 12px;
  font-style: normal;
}

.hall-section-heading > div {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--muted);
  font-size: 10px;
}

.hall-command-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, .78fr);
  gap: 14px;
}

.hall-hub {
  display: grid;
  grid-template-columns: minmax(0, .9fr) minmax(300px, 1.1fr);
  align-items: center;
  gap: 16px;
  min-height: 420px;
  overflow: hidden;
  padding: clamp(24px, 3.2vw, 42px);
}

.hall-hub::before {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 76% 42%, color-mix(in srgb, var(--gold) 10%, transparent), transparent 42%),
    linear-gradient(118deg, transparent 44%, color-mix(in srgb, var(--metal-edge) 32%, transparent));
  content: '';
  pointer-events: none;
}

.hall-hub-copy {
  position: relative;
  z-index: 2;
}

.hall-hub-kicker {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 15px;
  color: var(--gold);
  font-size: 11px;
  font-weight: 780;
}

.hall-hub h2 {
  max-width: 420px;
  margin: 0;
  font-size: clamp(31px, 4vw, 52px);
  line-height: 1.08;
  letter-spacing: -.055em;
}

.hall-hub p {
  max-width: 430px;
  margin: 15px 0 25px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.7;
}

.hall-hub .primary-button {
  min-height: 48px;
  border-radius: var(--radius-control);
  font-size: 13px;
}

.hall-hub-art {
  --card-tone: var(--gold);
  position: relative;
  z-index: 1;
  display: grid;
  place-items: center;
  width: min(100%, 370px);
  aspect-ratio: 1;
  justify-self: center;
}

.hall-hub-art :deep(.game-card-art) {
  width: 72%;
  aspect-ratio: 1;
  min-height: 0;
  border-radius: 26%;
  box-shadow: var(--shadow-raised);
  transform: rotate(-2deg);
}

.hall-hub-art > small {
  position: absolute;
  z-index: 4;
  bottom: 5%;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 7px 11px;
  color: var(--text-soft);
  background: var(--surface-glass);
  box-shadow: var(--shadow-contact);
  font-size: 9px;
  backdrop-filter: blur(16px);
}

.hall-hub-orbit {
  position: absolute;
  inset: 8%;
  border: 1px solid color-mix(in srgb, var(--gold) 24%, transparent);
  border-radius: 50%;
}

.hall-hub-orbit::before,
.hall-hub-orbit::after {
  position: absolute;
  inset: 13%;
  border: 1px solid color-mix(in srgb, var(--accent-secondary) 17%, transparent);
  border-radius: 50%;
  content: '';
}

.hall-hub-orbit::after {
  inset: 29%;
  border-color: color-mix(in srgb, var(--gold) 18%, transparent);
}

.hall-command-side {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 12px;
  min-width: 0;
}

.hall-room-anchor {
  min-width: 0;
  scroll-margin-top: 20px;
}

.hall-room-anchor :deep(.lobby-room-panel) {
  height: 100%;
  min-height: 316px;
}

.hall-personal-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 16px;
  min-height: 92px;
  padding: 18px;
  color: var(--text);
  text-align: left;
  cursor: pointer;
}

.hall-personal-card > span {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 2px 8px;
}

.hall-personal-card > span svg {
  grid-row: 1 / 3;
  color: var(--gold);
}

.hall-personal-card small {
  color: var(--muted);
  font-size: 9px;
}

.hall-personal-card strong {
  font-size: 13px;
}

.hall-personal-card em {
  color: var(--muted);
  font-size: 10px;
  font-style: normal;
}

.hall-personal-card > svg {
  color: var(--muted);
}

.hall-guest-card {
  grid-template-columns: minmax(0, 1fr) auto;
  cursor: default;
}

.hall-all-games {
  margin-top: 34px;
  scroll-margin-top: 20px;
}

.hall-all-heading {
  border-bottom: 1px solid var(--line);
  margin-bottom: 14px;
  padding-bottom: 16px;
}

.game-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.third-party-entry {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 13px;
  width: 100%;
  min-height: 74px;
  margin-top: 22px;
  padding: 12px 16px;
  color: var(--text);
  text-align: left;
  cursor: pointer;
}

.third-party-entry-icon {
  display: grid;
  place-items: center;
  width: 43px;
  aspect-ratio: 1;
  border: 1px solid var(--line);
  border-radius: var(--radius-control);
  color: var(--accent-secondary);
  background: var(--surface-inset);
}

.third-party-entry-copy {
  display: grid;
  gap: 3px;
}

.third-party-entry-copy small,
.third-party-entry > em {
  color: var(--muted);
  font-size: 9px;
  font-style: normal;
}

.third-party-entry-copy strong {
  font-size: 14px;
}

.third-party-entry > svg {
  color: var(--muted);
}

.hall-system-footer {
  display: flex;
  gap: 18px;
  margin-top: 14px;
  padding: 0 5px;
  color: var(--muted);
  font-size: 9px;
}

.hall-system-footer span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.hall-mobile-dock {
  display: none;
}

@media (hover: hover) {
  .hall-sidebar button:hover span {
    opacity: 1;
  }

  .hall-sidebar button:hover,
  .hall-personal-card:hover,
  .third-party-entry:hover {
    border-color: var(--line-strong);
    transform: translateY(-2px);
  }
}

@media (max-width: 1180px) {
  .hall-topbar {
    grid-template-columns: minmax(140px, .7fr) minmax(300px, 1.2fr);
  }

  .hall-system-metrics {
    display: none;
  }

  .hall-command-grid {
    grid-template-columns: minmax(0, 1.35fr) minmax(300px, .75fr);
  }

  .hall-hub {
    grid-template-columns: minmax(0, .85fr) minmax(240px, 1fr);
  }

  .game-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 880px) {
  .game-hall {
    display: block;
    padding-right: 12px;
    padding-bottom: calc(102px + env(safe-area-inset-bottom));
    padding-left: 12px;
  }

  .hall-sidebar {
    display: none;
  }

  .hall-topbar {
    grid-template-columns: 1fr auto;
    min-height: 70px;
    margin-bottom: 22px;
    padding: 9px 11px 9px 16px;
  }

  .hall-account-bar {
    border-left: 0;
    padding-left: 0;
  }

  .hall-account-bar > div:first-child {
    display: none;
  }

  .hall-command-grid {
    grid-template-columns: 1fr;
  }

  .hall-hub {
    min-height: 430px;
  }

  .hall-command-side {
    grid-template-columns: minmax(0, 1.2fr) minmax(260px, .8fr);
    grid-template-rows: 1fr;
  }

  .hall-room-anchor :deep(.lobby-room-panel),
  .hall-personal-card {
    height: 100%;
  }

  .hall-personal-card {
    grid-template-columns: 1fr auto;
    align-content: center;
  }

  .hall-personal-card > em {
    grid-column: 1 / -1;
  }

  .game-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .hall-mobile-dock {
    position: fixed;
    z-index: 35;
    right: 12px;
    bottom: calc(10px + env(safe-area-inset-bottom));
    left: 12px;
    display: grid;
    grid-auto-flow: column;
    grid-auto-columns: 1fr;
    gap: 4px;
    min-height: 68px;
    border: 1px solid var(--line);
    border-radius: var(--radius-card);
    padding: 5px;
    background: color-mix(in srgb, var(--surface-elevated) 88%, transparent);
    box-shadow: var(--shadow-raised), inset 0 1px 0 var(--metal-edge);
    backdrop-filter: blur(28px) saturate(120%);
  }

  .hall-mobile-dock button {
    display: grid;
    place-items: center;
    align-content: center;
    gap: 4px;
    min-width: 0;
    border: 0;
    border-radius: 15px;
    color: var(--muted);
    background: transparent;
    font-size: 9px;
  }
}

@media (max-width: 620px) {
  .hall-section-heading > div,
  .hall-section-heading em {
    display: none;
  }

  .hall-command-heading {
    padding-left: 3px;
  }

  .hall-hub {
    grid-template-columns: 1fr;
    min-height: 0;
    padding: 24px 20px 18px;
  }

  .hall-hub-copy {
    order: 2;
  }

  .hall-hub-art {
    width: min(100%, 310px);
  }

  .hall-hub h2 {
    font-size: 34px;
  }

  .hall-command-side {
    grid-template-columns: 1fr;
  }

  .hall-room-anchor :deep(.lobby-room-panel) {
    min-height: 0;
  }

  .game-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .third-party-entry {
    grid-template-columns: auto minmax(0, 1fr) auto;
  }

  .third-party-entry > em {
    display: none;
  }
}

@media (max-width: 380px) {
  .hall-account-bar .account-bar-actions button:first-child {
    display: none;
  }

  .game-grid {
    grid-template-columns: 1fr;
  }
}
</style>
