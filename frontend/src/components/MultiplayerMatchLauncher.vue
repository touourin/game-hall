<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import {
  ChevronRight,
  CircleDot,
  Crown,
  DoorOpen,
  LogIn,
  Plus,
  Radio,
  Settings2,
  ShieldCheck,
  Sparkles,
  Swords,
  UsersRound,
  X,
} from '@lucide/vue'
import type { ArcadeGameKey, ArcadeLobbyRoom, GameCatalogItem } from '../types/arcade'
import { gameRuleLabels } from '../gameRules'
import AvatarImage from './AvatarImage.vue'
import GameRuleSettings from './GameRuleSettings.vue'

interface MatchIdentity {
  protocol: string
  kicker: string
  title: string
  description: string
  accent: string
  glow: string
}

const props = defineProps<{
  game: GameCatalogItem
  gameKey: ArcadeGameKey
  rooms: ArcadeLobbyRoom[]
  modelValue: Record<string, unknown>
  mode: 'create' | 'join'
  roomCode: string
  disabled?: boolean
  activeRoom?: boolean
  guest?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, unknown>]
  'update:mode': [value: 'create' | 'join']
  'update:roomCode': [value: string]
  submit: []
}>()

const joinInput = ref<HTMLInputElement | null>(null)
const showRules = ref(false)
const ruleDraft = ref<Record<string, unknown>>({})

const identities: Partial<Record<ArcadeGameKey, MatchIdentity>> = {
  avalon: {
    protocol: 'CAMELOT COUNCIL',
    kicker: '忠诚与谎言同时入席',
    title: '召集远征议会',
    description: '建立你的议会，邀请熟悉的伙伴，在身份与投票之间决定王国的命运。',
    accent: '#e1bc68',
    glow: '#a77a2d',
  },
  gomoku: {
    protocol: 'FIVE IN A ROW',
    kicker: '纵横十五路，一线定胜负',
    title: '落座连珠棋局',
    description: '选择公平开局与胜负规则，邀请对手在棋盘中央展开攻守。',
    accent: '#c5d2d7',
    glow: '#71858d',
  },
  xiangqi: {
    protocol: 'RIVER CAMPAIGN',
    kicker: '隔河列阵，攻守有序',
    title: '布下楚汉战局',
    description: '创建一场完整可复盘的中国象棋对局，让每一步进退都有回应。',
    accent: '#df887d',
    glow: '#9d433d',
  },
  go: {
    protocol: 'TERRITORY MATCH',
    kicker: '方寸落子，争地围空',
    title: '开启手谈棋局',
    description: '设定棋盘、贴目与先手，在安静的落子中争夺整片疆域。',
    accent: '#79c9ae',
    glow: '#327c68',
  },
  poker: {
    protocol: 'PRIVATE TABLE',
    kicker: '筹码、位置与对手',
    title: '开启私人牌桌',
    description: '设定筹码与盲注，邀请玩家入席，让每一轮下注都保留压力。',
    accent: '#df9d9d',
    glow: '#8f4247',
  },
  doudizhu: {
    protocol: 'LANDLORD MATCH',
    kicker: '三人入局，叫抢定势',
    title: '召集一桌牌局',
    description: '创建三人牌局，确认玩法后邀请另外两位玩家加入。',
    accent: '#83bde5',
    glow: '#3d6f99',
  },
  junqi: {
    protocol: 'HIDDEN COMMAND',
    kicker: '暗中布阵，铁路突袭',
    title: '建立前线指挥所',
    description: '选择暗棋或翻棋模式，与对手在隐蔽信息中争夺最后的军旗。',
    accent: '#b4bd75',
    glow: '#687039',
  },
}

const identity = computed(() => identities[props.gameKey] ?? {
  protocol: 'MULTIPLAYER MATCH',
  kicker: props.game.description,
  title: `创建${props.game.name}对局`,
  description: '设置规则，邀请玩家加入房间。',
  accent: '#e1bc68',
  glow: '#8a6b32',
})
const ruleLabels = computed(() => gameRuleLabels(props.gameKey, props.modelValue))
const selectedPublicRoom = computed(() => props.rooms.find(
  (room) => room.roomCode === props.roomCode.trim().toUpperCase(),
))
const totalWaitingPlayers = computed(() => props.rooms.reduce(
  (total, room) => total + room.playerCount,
  0,
))
const launcherStyle = computed(() => ({
  '--match-accent': identity.value.accent,
  '--match-glow': identity.value.glow,
}))

function changeMode(mode: 'create' | 'join') {
  emit('update:mode', mode)
  if (mode === 'join') void nextTick(() => joinInput.value?.focus())
}

function chooseRoom(room: ArcadeLobbyRoom) {
  if (props.guest && room.allowsGuests === false) return
  emit('update:mode', 'join')
  emit('update:roomCode', room.roomCode)
  void nextTick(() => joinInput.value?.focus())
}

function updateRoomCode(event: Event) {
  const value = (event.target as HTMLInputElement).value.toUpperCase()
  emit('update:roomCode', value)
}

function openRuleEditor() {
  ruleDraft.value = { ...props.modelValue }
  showRules.value = true
}

function saveRules() {
  emit('update:modelValue', { ...ruleDraft.value })
  showRules.value = false
}
</script>

<template>
  <section
    class="multiplayer-match-launcher surface"
    :class="`multiplayer-match-launcher--${gameKey}`"
    :style="launcherStyle"
  >
    <aside class="match-story">
      <header class="match-story-header">
        <span>{{ identity.protocol }}</span>
        <b><i /> MATCHMAKING ONLINE</b>
      </header>

      <div class="match-hero">
        <div class="match-emblem" aria-hidden="true">
          <span class="match-orbit match-orbit-one" />
          <span class="match-orbit match-orbit-two" />
          <span><Swords :size="34" :stroke-width="1.55" /></span>
          <Sparkles class="match-spark" :size="14" />
        </div>
        <div class="match-hero-copy">
          <p>{{ identity.kicker }}</p>
          <h2>{{ identity.title }}</h2>
          <span>{{ identity.description }}</span>
        </div>
      </div>

      <dl class="match-live-metrics">
        <div><dt>对局人数</dt><dd>{{ game.players }}</dd></div>
        <div><dt>公开房间</dt><dd>{{ rooms.length }}</dd></div>
        <div><dt>等待玩家</dt><dd>{{ totalWaitingPlayers }}</dd></div>
      </dl>

      <section class="match-room-browser" aria-label="等待中的公开房间">
        <header>
          <span><Radio :size="15" />公开房间</span>
          <small>{{ rooms.length ? '选择一间并确认加入' : '暂时没有等待中的房间' }}</small>
        </header>
        <div v-if="rooms.length" class="match-room-list">
          <button
            v-for="room in rooms"
            :key="room.roomCode"
            type="button"
            class="match-room-item"
            :class="{ selected: selectedPublicRoom?.roomCode === room.roomCode }"
            :disabled="guest && room.allowsGuests === false"
            @click="chooseRoom(room)"
          >
            <AvatarImage class="match-room-avatar" :src="room.hostAvatarUrl" :name="room.hostName" />
            <span>
              <strong>{{ room.hostName }} 的房间</strong>
              <small>{{ room.roomCode }} · {{ room.playerCount }}/{{ room.maxPlayers }} 人{{ room.statsEligible === false ? ' · 休闲局' : '' }}</small>
            </span>
            <ChevronRight :size="17" />
          </button>
        </div>
        <div v-else class="match-room-empty">
          <UsersRound :size="22" />
          <span><strong>成为本场第一位房主</strong><small>规则确认后即可分享房间代码</small></span>
        </div>
      </section>
    </aside>

    <div class="match-console">
      <header class="match-console-header">
        <span><small>MATCH CONSOLE</small><strong>对局控制台</strong></span>
        <b><CircleDot :size="12" /> READY</b>
      </header>

      <div class="segmented-control match-mode-control">
        <button type="button" :class="{ active: mode === 'create' }" @click="changeMode('create')"><Plus :size="15" />创建房间</button>
        <button type="button" :class="{ active: mode === 'join' }" @click="changeMode('join')"><LogIn :size="15" />加入房间</button>
      </div>

      <form @submit.prevent="emit('submit')">
        <div v-if="mode === 'create'" class="match-create-panel">
          <div class="match-rule-summary">
            <header>
              <span><Settings2 :size="17" /><strong>本局规则</strong></span>
              <button type="button" @click="openRuleEditor">调整规则</button>
            </header>
            <div>
              <span v-for="label in ruleLabels" :key="label">{{ label }}</span>
            </div>
          </div>
          <div class="match-host-note">
            <Crown :size="17" />
            <span><strong>你将成为房主</strong><small>创建后可分享房间代码；等待阶段仍能修改规则和管理玩家。</small></span>
          </div>
        </div>

        <div v-else class="match-join-panel">
          <label class="field match-code-field">
            <span>房间代码</span>
            <span class="match-code-input-wrap"><DoorOpen :size="20" /><input ref="joinInput" :value="roomCode" maxlength="8" class="room-code-input" placeholder="输入 4–8 位代码" autocomplete="off" autocapitalize="characters" @input="updateRoomCode" /></span>
          </label>
          <div v-if="selectedPublicRoom" class="match-selected-room">
            <AvatarImage class="match-room-avatar" :src="selectedPublicRoom.hostAvatarUrl" :name="selectedPublicRoom.hostName" />
            <span><strong>准备加入 {{ selectedPublicRoom.hostName }} 的房间</strong><small>{{ selectedPublicRoom.playerCount }}/{{ selectedPublicRoom.maxPlayers }} 人正在等待</small></span>
          </div>
          <p v-else class="match-code-note">邀请码不区分大小写。也可以从左侧公开房间中选择。</p>
        </div>

        <p v-if="activeRoom" class="match-active-room-hint">请先返回并退出当前房间，再开始或加入其他对局。</p>

        <button type="submit" class="match-primary-action" :disabled="disabled">
          <span><Plus v-if="mode === 'create'" :size="19" /><LogIn v-else :size="19" /></span>
          <span><small>{{ mode === 'create' ? 'CREATE PRIVATE SESSION' : 'ENTER MATCH SESSION' }}</small><strong>{{ mode === 'create' ? `创建${game.name}房间` : '确认加入房间' }}</strong></span>
          <i aria-hidden="true" />
        </button>
      </form>

      <footer class="match-trust-row">
        <span><ShieldCheck :size="13" />掉线保护 10 分钟</span>
        <span><UsersRound :size="13" />熟人房间优先</span>
      </footer>
    </div>

    <Teleport to="body">
      <div
        v-if="showRules"
        class="match-rule-backdrop"
        :style="launcherStyle"
        @click.self="showRules = false"
        @keydown.esc="showRules = false"
      >
        <section class="match-rule-modal" role="dialog" aria-modal="true" aria-label="创建房间规则">
          <header>
            <span><small>ROOM CONFIGURATION</small><strong>{{ game.name }}房间规则</strong></span>
            <button type="button" aria-label="关闭规则设置" @click="showRules = false"><X :size="20" /></button>
          </header>
          <div class="match-rule-body">
            <GameRuleSettings v-model="ruleDraft" :game-key="gameKey" :guest-mode="guest" />
          </div>
          <footer>
            <span>保存后将用于新建房间</span>
            <button type="button" @click="saveRules">保存规则</button>
          </footer>
        </section>
      </div>
    </Teleport>
  </section>
</template>

<style scoped>
.multiplayer-match-launcher {
  --match-accent: var(--gold);
  --match-glow: #8a6b32;
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.03fr) minmax(400px, .97fr);
  overflow: hidden;
  border-color: color-mix(in srgb, var(--match-accent) 28%, var(--line));
  background:
    radial-gradient(circle at 8% 8%, color-mix(in srgb, var(--match-glow) 19%, transparent), transparent 35%),
    linear-gradient(128deg, color-mix(in srgb, var(--surface-elevated) 88%, transparent), var(--surface) 58%),
    var(--material-pattern);
  box-shadow: 0 34px 90px color-mix(in srgb, var(--bg) 64%, transparent);
  isolation: isolate;
}
.multiplayer-match-launcher::before { position: absolute; z-index: -1; inset: 0; background: repeating-linear-gradient(0deg, transparent 0 31px, color-mix(in srgb, var(--match-accent) 3%, transparent) 32px), linear-gradient(90deg, transparent 49.9%, color-mix(in srgb, var(--match-accent) 13%, transparent) 50%, transparent 50.1%); content: ''; pointer-events: none; }
.match-story { min-width: 0; padding: 30px 30px 26px; }
.match-story-header, .match-console-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.match-story-header > span, .match-console-header small { color: var(--match-accent); font-size: 8px; font-weight: 950; letter-spacing: .18em; }
.match-story-header b { display: inline-flex; align-items: center; gap: 6px; color: var(--muted); font-size: 7px; letter-spacing: .1em; }
.match-story-header b i { width: 5px; aspect-ratio: 1; border-radius: 50%; background: #63c995; box-shadow: 0 0 10px #63c995; }
.match-hero { display: grid; grid-template-columns: 132px minmax(0, 1fr); align-items: center; gap: 20px; margin: 30px 0 25px; }
.match-emblem { position: relative; width: 126px; aspect-ratio: 1; display: grid; place-items: center; }
.match-emblem > span:not(.match-orbit) { position: relative; z-index: 2; width: 66px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--match-accent) 54%, var(--line)); border-radius: 22px; color: var(--match-accent); background: linear-gradient(145deg, color-mix(in srgb, var(--match-accent) 14%, transparent), transparent), var(--surface-elevated); box-shadow: 0 18px 38px color-mix(in srgb, var(--match-glow) 26%, transparent); transform: rotate(45deg); }
.match-emblem > span:not(.match-orbit) svg { transform: rotate(-45deg); }
.match-orbit { position: absolute; border: 1px solid color-mix(in srgb, var(--match-accent) 26%, transparent); border-radius: 50%; }
.match-orbit-one { inset: 4px; border-style: dashed; transform: rotate(14deg); }
.match-orbit-two { inset: 20px; opacity: .65; }
.match-spark { position: absolute; top: 11px; right: 4px; color: var(--match-accent); }
.match-hero-copy p { margin: 0 0 7px; color: var(--text-soft); font-size: 10px; font-weight: 850; letter-spacing: .08em; }
.match-hero-copy h2 { margin: 0; font-family: "Songti SC", "STSong", serif; font-size: clamp(27px, 3vw, 35px); font-weight: 650; letter-spacing: -.03em; line-height: 1.18; }
.match-hero-copy > span { display: block; margin-top: 12px; color: var(--muted); font-size: 11px; line-height: 1.7; }
.match-live-metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; margin: 0 0 19px; }
.match-live-metrics > div { min-width: 0; border: 1px solid var(--line); border-radius: 11px; padding: 9px 10px; background: color-mix(in srgb, var(--surface-elevated) 33%, transparent); }
.match-live-metrics dt { overflow: hidden; color: var(--muted); font-size: 7px; font-weight: 850; text-overflow: ellipsis; white-space: nowrap; }
.match-live-metrics dd { margin: 5px 0 0; color: var(--text); font-size: 13px; font-weight: 900; }
.match-room-browser { border-top: 1px solid var(--line); padding-top: 17px; }
.match-room-browser > header { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 9px; }
.match-room-browser > header span { display: inline-flex; align-items: center; gap: 6px; color: var(--text); font-size: 11px; font-weight: 900; }
.match-room-browser > header svg { color: var(--match-accent); }
.match-room-browser > header small { color: var(--muted); font-size: 8px; }
.match-room-list { display: grid; gap: 7px; max-height: 190px; overflow-y: auto; padding-right: 2px; }
.match-room-item { min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 9px; width: 100%; min-height: 54px; border: 1px solid var(--line); border-radius: 12px; padding: 7px 9px; color: var(--text); background: color-mix(in srgb, var(--surface-inset) 72%, transparent); text-align: left; cursor: pointer; }
.match-room-item.selected { border-color: color-mix(in srgb, var(--match-accent) 55%, var(--line)); background: color-mix(in srgb, var(--match-accent) 9%, var(--surface-inset)); }
.match-room-item > span { min-width: 0; display: grid; gap: 3px; }
.match-room-item strong, .match-room-item small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.match-room-item strong { font-size: 10px; }.match-room-item small { color: var(--muted); font-size: 8px; }
.match-room-item > svg { color: var(--muted); }
.match-room-avatar { width: 34px; aspect-ratio: 1; border: 1px solid color-mix(in srgb, var(--match-accent) 28%, var(--line)); border-radius: 10px; color: var(--match-accent); background: color-mix(in srgb, var(--match-accent) 9%, var(--surface-inset)); font-size: 10px; font-weight: 900; }
.match-room-empty { min-height: 72px; display: flex; align-items: center; justify-content: center; gap: 10px; border: 1px dashed color-mix(in srgb, var(--match-accent) 24%, var(--line)); border-radius: 12px; color: var(--match-accent); background: color-mix(in srgb, var(--match-accent) 4%, transparent); }
.match-room-empty > span { display: grid; gap: 3px; }.match-room-empty strong { color: var(--text); font-size: 10px; }.match-room-empty small { color: var(--muted); font-size: 8px; }
.match-console { min-width: 0; display: flex; flex-direction: column; margin: 13px; border: 1px solid color-mix(in srgb, var(--match-accent) 18%, var(--line)); border-radius: calc(var(--radius-lg) - 7px); padding: 25px; background: linear-gradient(145deg, color-mix(in srgb, var(--match-accent) 6%, transparent), transparent 40%), color-mix(in srgb, var(--surface-inset) 86%, transparent); box-shadow: inset 0 1px 0 color-mix(in srgb, white 4%, transparent); }
.match-console-header { border-bottom: 1px solid var(--line); padding-bottom: 17px; }
.match-console-header > span { display: grid; gap: 4px; }.match-console-header strong { font-size: 15px; }
.match-console-header b { display: inline-flex; align-items: center; gap: 5px; border: 1px solid color-mix(in srgb, var(--match-accent) 30%, var(--line)); border-radius: 999px; padding: 5px 8px; color: var(--match-accent); background: color-mix(in srgb, var(--match-accent) 7%, transparent); font-size: 7px; letter-spacing: .1em; }
.match-mode-control { margin: 19px 0; }.match-mode-control button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; }
.match-console form { min-height: 0; display: flex; flex: 1; flex-direction: column; }
.match-create-panel, .match-join-panel { display: grid; gap: 12px; }
.match-rule-summary { border: 1px solid var(--line); border-radius: 14px; padding: 13px; background: color-mix(in srgb, var(--surface-elevated) 30%, transparent); }
.match-rule-summary header { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 11px; }
.match-rule-summary header span { display: inline-flex; align-items: center; gap: 7px; }.match-rule-summary header svg { color: var(--match-accent); }.match-rule-summary header strong { font-size: 11px; }
.match-rule-summary header button { border: 1px solid color-mix(in srgb, var(--match-accent) 32%, var(--line)); border-radius: 9px; padding: 7px 9px; color: var(--match-accent); background: color-mix(in srgb, var(--match-accent) 7%, transparent); font-size: 9px; font-weight: 850; }
.match-rule-summary > div { display: flex; flex-wrap: wrap; gap: 6px; }
.match-rule-summary > div span { border: 1px solid var(--line); border-radius: 999px; padding: 5px 7px; color: var(--muted); background: var(--surface-inset); font-size: 8px; }
.match-host-note, .match-selected-room { display: flex; align-items: center; gap: 10px; border: 1px solid color-mix(in srgb, var(--match-accent) 17%, var(--line)); border-radius: 12px; padding: 10px 11px; color: var(--match-accent); background: color-mix(in srgb, var(--match-accent) 5%, transparent); }
.match-host-note > span, .match-selected-room > span { min-width: 0; display: grid; gap: 2px; }.match-host-note strong, .match-selected-room strong { color: var(--text); font-size: 9px; }.match-host-note small, .match-selected-room small { color: var(--muted); font-size: 8px; line-height: 1.45; }
.match-code-field { display: grid; gap: 8px; }.match-code-field > span:first-child { color: var(--text-soft); font-size: 10px; font-weight: 850; }
.match-code-input-wrap { display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: center; gap: 10px; min-height: 68px; border: 1px solid color-mix(in srgb, var(--match-accent) 32%, var(--line)); border-radius: 14px; padding: 0 15px; color: var(--match-accent); background: color-mix(in srgb, var(--surface-elevated) 34%, transparent); }
.match-code-input-wrap input { min-width: 0; width: 100%; border: 0; outline: 0; padding: 0; color: var(--text); background: transparent; font-size: 17px; font-weight: 900; letter-spacing: .13em; text-transform: uppercase; }
.match-code-input-wrap input::placeholder { color: var(--muted); font-size: 11px; letter-spacing: .03em; }
.match-code-note { margin: 0; color: var(--muted); font-size: 9px; line-height: 1.55; }
.match-active-room-hint { margin: 12px 0 0; color: var(--muted); font-size: 9px; text-align: center; }
.match-primary-action { position: relative; width: 100%; min-height: 66px; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 11px; overflow: hidden; margin-top: auto; border: 1px solid color-mix(in srgb, var(--match-accent) 74%, white 12%); border-radius: 14px; padding: 0 16px; color: var(--accent-contrast); background: linear-gradient(125deg, color-mix(in srgb, var(--match-accent) 72%, white), var(--match-accent)); box-shadow: 0 15px 32px color-mix(in srgb, var(--match-glow) 24%, transparent); text-align: left; cursor: pointer; }
.match-primary-action > span:first-child { width: 35px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 10px; background: color-mix(in srgb, var(--accent-contrast) 12%, transparent); }
.match-primary-action > span:nth-child(2) { display: grid; gap: 2px; }.match-primary-action small { font-size: 6px; font-weight: 950; letter-spacing: .16em; opacity: .66; }.match-primary-action strong { font-size: 13px; }.match-primary-action > i { width: 25px; height: 1px; background: currentColor; opacity: .42; }
.match-primary-action:disabled { box-shadow: none; }
.match-trust-row { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px 15px; margin-top: 13px; color: var(--muted); font-size: 8px; }.match-trust-row span { display: inline-flex; align-items: center; gap: 5px; }.match-trust-row svg { color: var(--match-accent); }
.match-rule-backdrop { position: fixed; z-index: 90; inset: 0; display: grid; place-items: center; overflow-y: auto; overscroll-behavior: contain; padding: 16px; background: color-mix(in srgb, var(--bg) 82%, transparent); backdrop-filter: blur(10px); }
.match-rule-modal { width: min(620px, 100%); height: min(88dvh, 820px); min-height: 0; display: grid; grid-template-rows: auto minmax(0, 1fr) auto; overflow: hidden; border: 1px solid color-mix(in srgb, var(--match-accent) 30%, var(--line)); border-radius: 22px; color: var(--text); background: var(--material-pattern), var(--modal-surface); box-shadow: 0 28px 90px rgba(0,0,0,.48); }
.match-rule-modal > header, .match-rule-modal > footer { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 16px 18px; background: color-mix(in srgb, var(--surface-elevated) 84%, transparent); }
.match-rule-modal > header { border-bottom: 1px solid var(--line); }.match-rule-modal > header > span { display: grid; gap: 3px; }.match-rule-modal > header small { color: var(--match-accent); font-size: 7px; font-weight: 950; letter-spacing: .16em; }.match-rule-modal > header strong { font-family: "Songti SC", "STSong", serif; font-size: 18px; }
.match-rule-modal > header button { display: grid; place-items: center; width: 38px; height: 38px; border: 1px solid var(--line); border-radius: 50%; color: var(--text); background: var(--surface-inset); }
.match-rule-body { min-height: 0; overflow-y: auto; overscroll-behavior: contain; scrollbar-gutter: stable; padding: 18px; }
.match-rule-modal > footer { border-top: 1px solid var(--line); }.match-rule-modal > footer > span { color: var(--muted); font-size: 9px; }.match-rule-modal > footer button { min-width: 124px; min-height: 40px; border: 0; border-radius: 11px; color: var(--accent-contrast); background: var(--match-accent); font-weight: 900; }
@media (hover: hover) { .match-room-item:hover:not(:disabled) { border-color: color-mix(in srgb, var(--match-accent) 42%, var(--line)); transform: translateY(-1px); }.match-primary-action:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 19px 39px color-mix(in srgb, var(--match-glow) 31%, transparent); } }
@media (max-width: 900px) { .multiplayer-match-launcher { grid-template-columns: 1fr; }.match-story { padding-bottom: 22px; }.match-console { margin-top: 0; }.match-hero { grid-template-columns: 110px minmax(0, 1fr); }.match-emblem { width: 104px; }.match-room-list { max-height: 220px; } }
@media (max-width: 600px) { .match-story { padding: 21px 16px 18px; }.match-story-header b { display: none; }.match-hero { grid-template-columns: 76px minmax(0, 1fr); gap: 13px; margin: 22px 0 18px; }.match-emblem { width: 72px; }.match-emblem > span:not(.match-orbit) { width: 44px; border-radius: 15px; }.match-emblem > span:not(.match-orbit) svg { width: 23px; }.match-orbit-two { inset: 12px; }.match-spark { display: none; }.match-hero-copy p { font-size: 8px; }.match-hero-copy h2 { font-size: 25px; }.match-hero-copy > span { margin-top: 7px; font-size: 10px; line-height: 1.55; }.match-live-metrics { margin-bottom: 15px; }.match-live-metrics > div { padding: 8px; }.match-room-browser > header { align-items: flex-start; flex-direction: column; gap: 3px; }.match-room-list { max-height: 174px; }.match-console { margin: 0 6px 6px; padding: 19px 13px 16px; border-radius: 17px; }.match-mode-control { margin: 15px 0; }.match-primary-action { min-height: 64px; margin-top: 18px; padding: 0 12px; }.match-primary-action > i { display: none; }.match-rule-backdrop { align-items: end; padding: 8px 8px 0; }.match-rule-modal { width: 100%; height: calc(100dvh - 8px); border-radius: 21px 21px 0 0; }.match-rule-body { padding: 14px; }.match-rule-modal > footer { padding-bottom: calc(14px + env(safe-area-inset-bottom)); }.match-rule-modal > footer > span { display: none; }.match-rule-modal > footer button { width: 100%; }.match-trust-row { padding-bottom: env(safe-area-inset-bottom); } }
</style>
