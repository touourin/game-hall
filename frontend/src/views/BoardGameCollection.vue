<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ChevronRight, Settings, UsersRound } from '@lucide/vue'
import {
  BOARD_GAME_PLUGINS,
  type BoardGamePlugin,
} from '../boardGamePlugins'
import BackNavigationButton from '../components/BackNavigationButton.vue'
import BoardGamePluginArtwork from '../components/BoardGamePluginArtwork.vue'

const props = withDefaults(defineProps<{
  plugins?: readonly BoardGamePlugin[]
}>(), {
  plugins: () => BOARD_GAME_PLUGINS,
})

const emit = defineEmits<{
  back: []
  settings: []
  select: [plugin: BoardGamePlugin]
}>()

const games = computed(() => props.plugins)
const selectedKey = ref(games.value[0]?.key ?? '')
const selectedGame = computed(
  () => games.value.find((game) => game.key === selectedKey.value) ?? games.value[0] ?? null,
)

watch(games, (nextGames) => {
  if (nextGames.some((game) => game.key === selectedKey.value)) return
  selectedKey.value = nextGames[0]?.key ?? ''
})

function previewGame(game: BoardGamePlugin) {
  selectedKey.value = game.key
}

function launchGame(game: BoardGamePlugin) {
  selectedKey.value = game.key
  emit('select', game)
}

function focusSibling(event: KeyboardEvent, index: number, offset: number) {
  const strip = (event.currentTarget as HTMLElement).parentElement
  const tiles = Array.from(
    strip?.querySelectorAll<HTMLButtonElement>('.switch-game-tile') ?? [],
  )
  if (!tiles.length) return

  const targetIndex = (index + offset + tiles.length) % tiles.length
  const target = tiles[targetIndex]
  if (!target) return

  target.focus()
  target.scrollIntoView?.({ behavior: 'smooth', block: 'nearest', inline: 'center' })
}
</script>

<template>
  <main
    class="board-game-collection page-container adaptive-layout-root"
    :class="selectedGame ? `tone-${selectedGame.tone}` : undefined"
  >
    <header class="collection-page-header">
      <BackNavigationButton label="返回游戏大厅" @click="emit('back')" />
      <div>
        <small>BOARD GAME COLLECTION · {{ games.length ? `${games.length} PLUGINS` : 'PLUGIN READY' }}</small>
        <h1>桌游合集</h1>
        <p>独立于现有 7 款联机游戏，专门承载可插拔桌游。</p>
      </div>
      <button
        type="button"
        class="collection-settings"
        aria-label="打开设置"
        @click="emit('settings')"
      >
        <Settings :size="18" />
        <span>设置</span>
      </button>
    </header>

    <section v-if="selectedGame" class="selected-game-panel surface" aria-label="当前选择的桌游">
      <div class="selected-game-art">
        <BoardGamePluginArtwork :plugin="selectedGame" />
        <span class="selected-game-number">
          {{ String(games.findIndex((game) => game.key === selectedGame?.key) + 1).padStart(2, '0') }}
        </span>
      </div>

      <div class="selected-game-copy">
        <span class="plugin-status"><i /> BOARD GAME PLUGIN <b>已安装</b></span>
        <div class="selected-game-meta">
          <span>{{ selectedGame.category }}</span>
          <span><UsersRound :size="16" /> {{ selectedGame.players }}</span>
        </div>
        <h2>{{ selectedGame.name }}</h2>
        <p>{{ selectedGame.description }}</p>
        <button
          type="button"
          class="primary-button launch-game-button"
          @click="launchGame(selectedGame)"
        >
          创建或加入房间
          <ChevronRight :size="19" />
        </button>
        <small class="launch-note">桌游插件负责自己的规则、房间流程与游戏界面。</small>
      </div>
    </section>

    <section v-else class="empty-plugin-cabinet surface" aria-labelledby="empty-cabinet-title">
      <div class="empty-cartridge-row" aria-hidden="true">
        <span v-for="slot in 3" :key="slot">
          <i>+</i>
          <small>SLOT {{ String(slot).padStart(2, '0') }}</small>
        </span>
      </div>
      <div class="empty-cabinet-copy">
        <span class="plugin-status"><i /> BOARD GAME PLUGINS <b>等待接入</b></span>
        <h2 id="empty-cabinet-title">桌游柜已准备好</h2>
        <p>当前还没有安装桌游插件。新增插件后，它会自动以卡带形式出现在这里，并标注适配人数；点击即可进入自己的创建房间流程。</p>
        <div class="empty-capabilities">
          <span><UsersRound :size="16" /> 独立人数配置</span>
          <span>独立规则与房间</span>
          <span>不占用现有 7 款游戏</span>
        </div>
      </div>
    </section>

    <section v-if="games.length" class="game-selector" aria-labelledby="game-selector-title">
      <header>
        <div>
          <small>SELECT A BOARD GAME</small>
          <h2 id="game-selector-title">选择桌游</h2>
        </div>
        <span>← → 切换 · Enter 打开</span>
      </header>

      <div class="switch-game-strip" role="list" aria-label="桌游插件列表">
        <button
          v-for="(game, index) in games"
          :key="game.key"
          type="button"
          role="listitem"
          class="switch-game-tile"
          :class="[`tone-${game.tone}`, { active: selectedGame?.key === game.key }]"
          :aria-current="selectedGame?.key === game.key ? 'true' : undefined"
          :aria-label="`${game.name}，${game.players}，打开房间大厅`"
          @mouseenter="previewGame(game)"
          @focus="previewGame(game)"
          @click="launchGame(game)"
          @keydown.left.prevent="focusSibling($event, index, -1)"
          @keydown.right.prevent="focusSibling($event, index, 1)"
        >
          <span class="tile-plugin-index">PLUGIN {{ String(index + 1).padStart(2, '0') }}</span>
          <BoardGamePluginArtwork :plugin="game" />
          <span class="tile-copy">
            <strong>{{ game.name }}</strong>
            <small><UsersRound :size="13" /> {{ game.players }}</small>
          </span>
        </button>
      </div>

      <p class="selector-hint"><i /> 点按任意游戏卡带，即可进入该插件的创建或加入房间流程</p>
    </section>
  </main>
</template>

<style scoped>
.board-game-collection { --card-tone: var(--gold); width: min(100%, 1180px); padding-bottom: 84px; }
.collection-page-header { position: relative; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: start; gap: 18px; min-height: 212px; padding: 30px 0 47px; }
.collection-page-header::after { position: absolute; right: 0; bottom: 23px; left: 59px; height: 1px; background: linear-gradient(90deg, var(--line-strong), transparent 76%); content: ''; }
.collection-page-header > div { min-width: 0; }
.collection-page-header small { color: var(--gold); font-size: 10px; font-weight: 850; letter-spacing: .16em; }
.collection-page-header h1 { margin: 8px 0 9px; font-family: "Songti SC", "STSong", serif; font-size: clamp(44px, 6vw, 66px); font-weight: 650; letter-spacing: -.035em; line-height: 1; }
.collection-page-header p { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.6; }
.collection-settings { display: inline-flex; align-items: center; gap: 7px; min-height: 42px; border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 0 12px; color: var(--text-soft); background: var(--surface-inset); font-size: 11px; font-weight: 800; cursor: pointer; }

.selected-game-panel,.empty-plugin-cabinet { min-height: 382px; display: grid; grid-template-columns: minmax(380px, 1.08fr) minmax(0, .92fr); overflow: hidden; border-color: color-mix(in srgb, var(--card-tone) 28%, var(--line)); }
.selected-game-art { position: relative; min-height: 382px; padding: 18px; background: radial-gradient(circle at 50% 30%, color-mix(in srgb, var(--card-tone) 15%, transparent), transparent 58%), var(--surface-inset); }
.selected-game-art :deep(.board-game-plugin-art) { height: 100%; min-height: 346px; border-radius: 18px; }
.selected-game-art :deep(.plugin-mark) { width: 96px; border-radius: 26px; font-size: 42px; }
.selected-game-number { position: absolute; right: 30px; bottom: 27px; z-index: 3; color: color-mix(in srgb, var(--card-tone) 82%, white); font-family: ui-monospace, "SFMono-Regular", Consolas, monospace; font-size: 13px; font-weight: 850; letter-spacing: .16em; text-shadow: 0 2px 12px var(--bg); }
.selected-game-copy,.empty-cabinet-copy { position: relative; display: grid; align-content: center; justify-items: start; min-width: 0; padding: 38px 42px; background: radial-gradient(circle at 80% 10%, color-mix(in srgb, var(--card-tone) 10%, transparent), transparent 40%); }
.plugin-status { display: inline-flex; align-items: center; gap: 7px; color: var(--muted); font-size: 9px; font-weight: 850; letter-spacing: .13em; }
.plugin-status i { width: 7px; aspect-ratio: 1; border-radius: 50%; background: var(--green); box-shadow: 0 0 0 4px color-mix(in srgb, var(--green) 12%, transparent); }
.plugin-status b { border-radius: 999px; padding: 4px 7px; color: var(--green); background: color-mix(in srgb, var(--green) 10%, transparent); font-size: 8px; letter-spacing: .06em; }
.selected-game-meta { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 28px; }
.selected-game-meta span { display: inline-flex; align-items: center; gap: 5px; border: 1px solid color-mix(in srgb, var(--card-tone) 23%, var(--line)); border-radius: 999px; padding: 7px 10px; color: var(--card-tone); background: color-mix(in srgb, var(--card-tone) 7%, transparent); font-size: 10px; font-weight: 800; }
.selected-game-copy h2,.empty-cabinet-copy h2 { margin: 14px 0 7px; font-family: "Songti SC", "STSong", serif; font-size: clamp(38px, 5vw, 58px); font-weight: 650; letter-spacing: -.04em; line-height: 1.05; }
.selected-game-copy > p,.empty-cabinet-copy > p { margin: 0; color: var(--text-soft); font-size: 14px; line-height: 1.65; }
.launch-game-button { margin-top: 26px; }
.launch-note { max-width: 360px; margin-top: 10px; color: var(--muted); font-size: 9px; line-height: 1.55; }

.empty-plugin-cabinet { --card-tone: var(--gold); }
.empty-cartridge-row { min-height: 382px; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: center; gap: 12px; padding: 32px; background: radial-gradient(circle at 50% 38%, color-mix(in srgb, var(--gold) 13%, transparent), transparent 58%), var(--surface-inset); perspective: 900px; }
.empty-cartridge-row > span { height: 210px; display: grid; place-items: center; align-content: center; gap: 16px; border: 1px dashed color-mix(in srgb, var(--gold) 42%, var(--line)); border-radius: 18px; color: var(--muted); background: color-mix(in srgb, var(--surface-elevated) 78%, transparent); box-shadow: 0 20px 40px rgba(0,0,0,.18); transform: rotateY(7deg) rotateZ(-2deg); }
.empty-cartridge-row > span:nth-child(2) { transform: translateY(-11px) scale(1.04); }
.empty-cartridge-row > span:nth-child(3) { transform: rotateY(-7deg) rotateZ(2deg); }
.empty-cartridge-row i { width: 54px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--gold) 34%, var(--line)); border-radius: 17px; color: var(--gold); background: color-mix(in srgb, var(--gold) 8%, transparent); font-size: 30px; font-style: normal; font-weight: 300; }
.empty-cartridge-row small { font-family: ui-monospace, "SFMono-Regular", Consolas, monospace; font-size: 8px; font-weight: 850; letter-spacing: .12em; }
.empty-cabinet-copy .plugin-status i { background: var(--gold); box-shadow: 0 0 0 4px color-mix(in srgb, var(--gold) 12%, transparent); }
.empty-cabinet-copy .plugin-status b { color: var(--gold); background: color-mix(in srgb, var(--gold) 10%, transparent); }
.empty-capabilities { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 24px; }
.empty-capabilities span { display: inline-flex; align-items: center; gap: 5px; border: 1px solid var(--line); border-radius: 999px; padding: 7px 9px; color: var(--muted); background: var(--surface-inset); font-size: 9px; font-weight: 750; }

.game-selector { margin-top: 48px; }
.game-selector > header { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; margin-bottom: 15px; padding: 0 4px; }
.game-selector > header > div { display: grid; gap: 3px; }
.game-selector > header small { color: var(--gold); font-size: 9px; font-weight: 850; letter-spacing: .18em; }
.game-selector > header h2 { margin: 0; font-family: "Songti SC", "STSong", serif; font-size: 28px; }
.game-selector > header > span { color: var(--muted); font-size: 9px; font-weight: 750; }
.switch-game-strip { display: flex; gap: 13px; overflow-x: auto; margin: 0 calc(-1 * var(--layout-gutter)); padding: 15px var(--layout-gutter) 28px; scroll-padding-inline: var(--layout-gutter); scroll-snap-type: x mandatory; overscroll-behavior-inline: contain; scrollbar-width: none; }
.switch-game-strip::-webkit-scrollbar { display: none; }
.switch-game-tile { --card-tone: var(--gold); position: relative; flex: 0 0 clamp(158px, 18vw, 204px); min-width: 0; display: grid; grid-template-rows: minmax(0, 1fr) auto; gap: 10px; scroll-snap-align: center; border: 1px solid color-mix(in srgb, var(--card-tone) 23%, var(--line)); border-radius: 18px; padding: 30px 10px 12px; color: var(--text); background: var(--material-pattern), color-mix(in srgb, var(--surface-elevated) 94%, transparent); box-shadow: var(--shadow-card); text-align: left; cursor: pointer; }
.switch-game-tile.active { border-color: var(--card-tone); box-shadow: 0 0 0 3px color-mix(in srgb, var(--card-tone) 20%, transparent), 0 22px 50px color-mix(in srgb, var(--bg) 45%, transparent); transform: translateY(-6px); }
.switch-game-tile :deep(.board-game-plugin-art) { height: 142px; min-height: 0; }
.tile-plugin-index { position: absolute; top: 10px; left: 11px; color: var(--card-tone); font-family: ui-monospace, "SFMono-Regular", Consolas, monospace; font-size: 7px; font-weight: 850; letter-spacing: .1em; }
.tile-copy { min-width: 0; display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.tile-copy strong { overflow: hidden; font-family: "Songti SC", "STSong", serif; font-size: 16px; text-overflow: ellipsis; white-space: nowrap; }
.tile-copy small { flex: 0 0 auto; display: inline-flex; align-items: center; gap: 3px; color: var(--muted); font-size: 8px; font-weight: 750; }
.selector-hint { display: flex; align-items: center; justify-content: center; gap: 8px; margin: 3px 0 0; color: var(--muted); font-size: 9px; }
.selector-hint i { width: 6px; aspect-ratio: 1; border-radius: 50%; background: var(--gold); box-shadow: 0 0 0 4px color-mix(in srgb, var(--gold) 10%, transparent); }

.tone-amber { --card-tone: #d9ad62; }
.tone-coral { --card-tone: #e7897d; }
.tone-forest { --card-tone: #70c99e; }
.tone-ocean { --card-tone: #77b9df; }
.tone-violet { --card-tone: #ad91df; }

@media (hover: hover) {
  .collection-settings:hover { border-color: var(--line-strong); color: var(--gold); background: var(--surface-soft); }
  .switch-game-tile:hover { border-color: var(--card-tone); transform: translateY(-6px); }
}

@media (max-width: 860px) {
  .selected-game-panel,.empty-plugin-cabinet { grid-template-columns: minmax(310px, 1fr) minmax(0, 1fr); }
  .selected-game-copy,.empty-cabinet-copy { padding: 30px; }
  .empty-cartridge-row { padding: 22px; }
}

@container (max-width: 680px) {
  .board-game-collection { padding-right: 12px; padding-left: 12px; }
  .collection-page-header { grid-template-columns: auto minmax(0, 1fr) auto; gap: 12px; min-height: 0; padding: 20px 0 34px; }
  .collection-page-header::after { bottom: 16px; left: 0; }
  .collection-page-header small { font-size: 7px; }
  .collection-page-header h1 { margin-top: 6px; font-size: 37px; }
  .collection-page-header p { font-size: 10px; }
  .collection-settings { width: 42px; padding: 0; justify-content: center; }
  .collection-settings span { display: none; }
  .selected-game-panel,.empty-plugin-cabinet { min-height: 0; grid-template-columns: 1fr; border-radius: 18px; }
  .selected-game-art { min-height: 225px; padding: 10px; }
  .selected-game-art :deep(.board-game-plugin-art) { min-height: 205px; border-radius: 12px; }
  .selected-game-art :deep(.plugin-mark) { width: 72px; border-radius: 20px; font-size: 31px; }
  .selected-game-number { right: 20px; bottom: 17px; font-size: 9px; }
  .selected-game-copy,.empty-cabinet-copy { padding: 24px 20px 22px; }
  .selected-game-meta { margin-top: 20px; }
  .selected-game-copy h2,.empty-cabinet-copy h2 { font-size: 37px; }
  .selected-game-copy > p,.empty-cabinet-copy > p { font-size: 11px; }
  .launch-game-button { width: 100%; margin-top: 20px; }
  .empty-cartridge-row { min-height: 240px; gap: 7px; padding: 22px 12px; }
  .empty-cartridge-row > span { height: 142px; gap: 10px; border-radius: 12px; }
  .empty-cartridge-row i { width: 38px; border-radius: 12px; font-size: 22px; }
  .empty-cartridge-row small { font-size: 6px; }
  .empty-capabilities { margin-top: 18px; }
  .empty-capabilities span { font-size: 7px; }
  .game-selector { margin-top: 37px; }
  .game-selector > header { align-items: flex-start; flex-direction: column; gap: 4px; margin-bottom: 8px; }
  .game-selector > header h2 { font-size: 25px; }
  .game-selector > header > span { font-size: 7px; }
  .switch-game-strip { gap: 10px; margin-right: -12px; margin-left: -12px; padding-right: 12px; padding-left: 12px; scroll-padding-inline: 12px; }
  .switch-game-tile { flex-basis: 152px; border-radius: 15px; padding: 27px 8px 10px; }
  .switch-game-tile :deep(.board-game-plugin-art) { height: 118px; }
  .tile-copy strong { font-size: 14px; }
  .tile-copy small { font-size: 7px; }
  .selector-hint { font-size: 8px; }
}
</style>
