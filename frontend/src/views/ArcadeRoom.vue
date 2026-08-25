<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import {
  Eye,
  QrCode,
  RotateCcw,
  Settings2,
  UsersRound,
} from '@lucide/vue'
import ArcadeChatPanel from '../components/ArcadeChatPanel.vue'
import GameSkinPicker from '../components/GameSkinPicker.vue'
import InviteLinkPanel from '../components/InviteLinkPanel.vue'
import GameRuleSettings from '../components/GameRuleSettings.vue'
import HostTransferNotice from '../components/HostTransferNotice.vue'
import MatchRequestPanel from '../components/MatchRequestPanel.vue'
import RoomExitButton from '../components/RoomExitButton.vue'
import RoomDissolveButton from '../components/RoomDissolveButton.vue'
import RoomPageHeader from '../components/RoomPageHeader.vue'
import RoomRecordActions from '../components/RoomRecordActions.vue'
import RoomInviteModal from '../components/RoomInviteModal.vue'
import AvatarImage from '../components/AvatarImage.vue'
import RoomPlayerRoster from '../components/RoomPlayerRoster.vue'
import BaseModal from '../components/ui/BaseModal.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiIconButton from '../components/ui/UiIconButton.vue'
import { useArcadeStore } from '../stores/arcade'
import type { ArcadeSnapshot } from '../types/arcade'
import { gameRuleLabels, withDefaultGameRules } from '../gameRules'
import { isSoloGameKey } from '../gameCatalog'
import {
  gameSkinCssVariables,
  gameSkinKind,
  rememberGameSkin,
  storedGameSkin,
  type GameSkinId,
} from '../gameSkins'
import { gameRegistration } from '../game-platform/registry'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const emit = defineEmits<{ settings: [] }>()
const arcade = useArcadeStore()
const registration = computed(() => gameRegistration(props.snapshot.gameKey))
const roomShell = computed(() => registration.value?.presentation.roomShell ?? {})
const gameView = computed(() => registration.value?.presentation.component ?? null)
const roomLayout = computed(() => registration.value?.presentation.roomLayout ?? null)
const moduleHeaderDetails = computed(() => roomShell.value.headerDetailsComponent ?? null)
const moduleHeaderActions = computed(() => roomShell.value.headerActionsComponent ?? null)
const moduleRuleActions = computed(() => roomShell.value.ruleActionsComponent ?? null)
const moduleLobby = computed(() => roomShell.value.lobbyComponent ?? null)
const moduleWaitingMessage = computed(() => (
  roomShell.value.waitingMessage?.(props.snapshot) ?? null
))
const ruleEditor = ref<Record<string, unknown> | null>(null)
const showQr = ref(false)
const sharedChat = ref<{ openChat: () => Promise<void> } | null>(null)
const activeGameSkin = ref<GameSkinId>(storedGameSkin())
const isSpectating = computed(() => props.snapshot.viewer?.mode === 'spectator')
const perspectivePlayer = computed(() => props.snapshot.players.find(
  (player) => player.id === props.snapshot.self.id,
) ?? null)
const roomSpectators = computed(() => props.snapshot.spectators ?? [])
const viewerIsGuest = computed(() => (
  props.snapshot.viewer?.isGuest ?? props.snapshot.self.isGuest
))
const missingPlayers = computed(
  () => Math.max(0, (props.snapshot.minimumPlayers ?? props.snapshot.requiredPlayers) - props.snapshot.players.length),
)
const availableSeats = computed(
  () => Math.max(0, props.snapshot.requiredPlayers - props.snapshot.players.length),
)
const canAddAiPlayer = computed(() => (
  props.snapshot.actions.canAddAiPlayer === true
  && availableSeats.value > 0
))
const inviteUrl = computed(() => {
  const url = new URL(window.location.href)
  url.pathname = `/games/${props.snapshot.gameKey}/rooms/${props.snapshot.roomCode}`
  url.search = ''
  url.hash = ''
  return url.toString()
})
const selfRematchReady = computed(() =>
  props.snapshot.rematchReadyPlayerIds.includes(props.snapshot.self.id),
)
const isSolo = computed(() => isSoloGameKey(props.snapshot.gameKey))
const activeGameSkinKind = computed(() => gameSkinKind(props.snapshot.gameKey))
const activeGameSkinStyle = computed(() => (
  activeGameSkinKind.value ? gameSkinCssVariables(activeGameSkin.value) : undefined
))
const roomHeaderEyebrow = computed(() => {
  const suffix = roomShell.value.headerEyebrowSuffix?.(props.snapshot)
    ?? (isSolo.value ? ' · 单人挑战' : '')
  return `${props.snapshot.gameName}${suffix}`
})
const roomHeaderTitle = computed(() => {
  const moduleTitle = roomShell.value.headerTitle?.(props.snapshot)
  if (moduleTitle) return moduleTitle
  if (isSolo.value) return props.snapshot.gameName
  return props.snapshot.roomName || `房间 ${props.snapshot.roomCode}`
})
const roomStatsMode = computed(() => roomShell.value.statsMode?.(props.snapshot))

watch(
  () => [props.snapshot.phase, props.snapshot.gameKey] as const,
  async ([phase], previous) => {
    if (phase !== 'lobby' || isSolo.value) showQr.value = false
    if (previous?.[0] === 'lobby' && phase !== 'lobby') {
      await nextTick()
      window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
    }
  },
)
const exitDescription = computed(() => {
  if (isSpectating.value) {
    return '退出后将结束当前观战，不会影响房间内的玩家和对局。'
  }
  if (props.snapshot.actions.canAct && isSolo.value) {
    return '退出将放弃当前进度，未完成的挑战不会记录成绩。'
  }
  if (props.snapshot.actions.canAct) {
    return roomShell.value.activeExitDescription
      ?? '暂时返回会保留座位和进度；认输并退出将放弃本局，而且无法再返回。'
  }
  if (props.snapshot.phase === 'lobby') {
    return '你会离开房间并让出座位；如果你是房主，房主将自动移交。'
  }
  if (props.snapshot.phase === 'finished') {
    return '你会退出当前房间并返回游戏大厅。'
  }
  return '退出后将返回游戏大厅。'
})
const exitMode = computed(() => {
  if (isSpectating.value) return 'spectator'
  if (!props.snapshot.actions.canAct) return 'leave'
  return isSolo.value ? 'solo-active' : 'multiplayer-active'
})

function openRuleEditor() {
  ruleEditor.value = withDefaultGameRules(
    props.snapshot.gameKey,
    props.snapshot.options,
  )
}

async function saveRules() {
  if (!ruleEditor.value) return
  if (await arcade.updateRules(ruleEditor.value)) ruleEditor.value = null
}

function selectGameSkin(skin: GameSkinId) {
  activeGameSkin.value = skin
  rememberGameSkin(skin)
}

function addAiPlayer(difficulty: string) {
  void arcade.action('add_ai', { difficulty })
}

function openSharedChat() {
  void sharedChat.value?.openChat()
}

</script>

<template>
  <main
    class="arcade-room page-container adaptive-layout-root"
    :class="{
      'arcade-room--wide': roomLayout === 'wide',
      'arcade-room--immersive': roomLayout === 'immersive',
      'arcade-room--active': snapshot.phase !== 'lobby',
      'arcade-room--board-game': registration?.presentation.skinKind === 'board',
      'arcade-room--spectating': isSpectating,
    }"
    :data-game-skin="activeGameSkinKind ? activeGameSkin : undefined"
    :style="activeGameSkinStyle"
  >
    <RoomPageHeader
      :eyebrow="roomHeaderEyebrow"
      :title="roomHeaderTitle"
    >
      <template #navigation>
        <RoomExitButton
          :busy="arcade.busy"
          :description="exitDescription"
          :mode="exitMode"
          :abandon-label="roomShell.abandonLabel"
          @leave="arcade.leaveRoom"
          @detach="arcade.detachRoom"
          @abandon="arcade.abandonRoom"
        />
      </template>
      <template v-if="moduleHeaderDetails" #details>
        <component :is="moduleHeaderDetails" :snapshot="snapshot" />
      </template>
      <template #actions>
        <RoomRecordActions
          v-if="!isSpectating"
          :account-id="snapshot.self.accountId"
          :game-key="snapshot.gameKey"
          :game-name="snapshot.gameName"
          :game-mode="roomStatsMode"
          :guest="viewerIsGuest"
        />
        <UiIconButton
          aria-label="打开设置"
          @click="emit('settings')"
        >
          <Settings2 :size="20" />
        </UiIconButton>
        <UiIconButton
          v-if="snapshot.phase === 'lobby' && !isSolo"
          aria-label="显示加入二维码"
          @click="showQr = true"
        >
          <QrCode :size="21" />
        </UiIconButton>
        <component
          v-if="moduleHeaderActions"
          :is="moduleHeaderActions"
          :snapshot="snapshot"
        />
        <RoomDissolveButton
          v-if="snapshot.actions.canDissolve"
          :busy="arcade.busy"
          @confirm="arcade.dissolveRoom"
        />
      </template>
    </RoomPageHeader>

    <HostTransferNotice :transfer-at="snapshot.hostTransferAt" />

    <section v-if="isSpectating" class="surface spectator-mode-banner" role="status">
      <Eye :size="20" />
      <span><strong>正在以 {{ perspectivePlayer?.name ?? '目标玩家' }} 的第一人称视角观战</strong><small>本局视角已固定；你只能查看，不能出牌、投票、聊天或参与房间操作。</small></span>
    </section>

    <section
      v-if="snapshot.statsEligible === false || (snapshot.phase === 'lobby' && snapshot.options.allowGuests)"
      class="surface guest-match-notice"
      role="status"
    >
      <strong>{{ snapshot.statsEligible !== false ? '本房间允许游客加入' : '休闲局 · 本局不计战绩' }}</strong>
      <span>{{ snapshot.statsEligible !== false ? '目前尚无游客；若游客加入并参与开局，整局不会计入任何玩家战绩。' : '本局阵容包含游客，所有玩家的场次、胜负、历史和排行榜成绩均不会记录。' }}</span>
    </section>

    <RoomPlayerRoster
      v-if="!isSolo"
      :players="snapshot.players"
      :self-id="snapshot.self.id"
      :perspective-player-id="isSpectating ? snapshot.self.id : null"
      :can-kick-players="snapshot.actions.canKickPlayers"
      :can-add-ai-player="canAddAiPlayer"
      :available-seats="availableSeats"
      :ai="snapshot.ai"
      :busy="arcade.busy"
      @kick="arcade.kickPlayer"
      @add-ai="addAiPlayer"
    />

    <section v-if="!isSolo || roomSpectators.length" class="surface arcade-spectator-strip" aria-label="房间观众">
      <header><span><Eye :size="17" /><strong>观战席</strong></span><b>{{ roomSpectators.length }} 人</b></header>
      <div v-if="roomSpectators.length">
        <article v-for="spectator in roomSpectators" :key="spectator.id">
          <AvatarImage
            class="arcade-spectator-avatar"
            :src="spectator.avatarUrl"
            :name="spectator.name"
          />
          <span><strong>{{ spectator.name }}{{ spectator.id === snapshot.viewer?.id ? '（你）' : '' }}</strong><small>正在观看 {{ spectator.targetPlayerName }}</small></span>
        </article>
      </div>
      <p v-else>暂无观众</p>
    </section>

    <section v-if="!isSolo" class="surface room-rule-bar" aria-label="房间规则">
      <div>
        <Settings2 :size="18" />
        <span v-for="label in gameRuleLabels(snapshot.gameKey, snapshot.options)" :key="label">{{ label }}</span>
        <span>{{ snapshot.options.allowSpectators === false ? '关闭观战' : '允许第一人称观战' }}</span>
        <span>掉线保护 10 分钟</span>
      </div>
      <div class="room-rule-actions">
        <component
          v-if="moduleRuleActions"
          :is="moduleRuleActions"
          :snapshot="snapshot"
          placement="rule"
        />
        <button v-if="snapshot.actions.canEditRules" type="button" data-ui-interaction="choice" @click="openRuleEditor">{{ snapshot.phase === 'finished' ? '修改下局规则' : '修改规则' }}</button>
      </div>
    </section>

    <GameSkinPicker
      v-if="snapshot.phase === 'lobby' && activeGameSkinKind"
      :model-value="activeGameSkin"
      :kind="activeGameSkinKind"
      @update:model-value="selectGameSkin"
    />

    <component
      v-if="snapshot.phase === 'lobby' && moduleLobby"
      :is="moduleLobby"
      :snapshot="snapshot"
    />

    <section v-if="snapshot.phase === 'lobby'" class="surface arcade-waiting">
      <UsersRound :size="48" />
      <h2>等待玩家到齐</h2>
      <p v-if="moduleWaitingMessage">{{ moduleWaitingMessage }}</p>
      <p v-else-if="missingPlayers > 0">还需要 {{ missingPlayers }} 名玩家</p>
      <p v-else-if="availableSeats > 0">已可开始，还可加入 {{ availableSeats }} 名玩家</p>
      <p v-else>人员已到齐，房主可以开始</p>
      <button v-if="!isSolo" type="button" class="room-code-share" data-ui-interaction="lift" aria-label="显示加入二维码" @click="showQr = true">
        {{ snapshot.roomCode }}
      </button>
      <InviteLinkPanel
        v-if="!isSolo"
        :url="inviteUrl"
        :share-title="`加入${snapshot.gameName}“${snapshot.roomName || `房间 ${snapshot.roomCode}`}”`"
        :share-text="`点击链接加入${snapshot.roomName || `我的${snapshot.gameName}房间`}，房间码 ${snapshot.roomCode}`"
      />
      <UiButton
        v-if="snapshot.actions.canStart"
        variant="primary"
        @click="arcade.startGame"
      >
        开始{{ snapshot.gameName }}
      </UiButton>
    </section>

    <section v-else class="arcade-game-stage">
      <div v-if="snapshot.phase === 'finished' && !isSolo && !roomShell.handlesResult" class="surface result-banner">
        <small>{{ roomShell.finishedLabel ?? '本局结束' }}</small>
        <h2>{{ snapshot.winReason }}</h2>
        <p>
          {{ isSpectating
            ? `${perspectivePlayer?.name ?? '被观战玩家'}${snapshot.winnerPlayerIds.includes(snapshot.self.id) ? '赢了' : '未获胜'}`
            : snapshot.winnerPlayerIds.includes(snapshot.self.id) ? '你赢了' : '再接再厉' }}
          · {{ snapshot.statsEligible === false ? '休闲局不计战绩' : '战绩已保存' }}
        </p>
        <p class="rematch-progress">
          {{ snapshot.rematchReadyPlayerIds.length }} / {{ snapshot.players.length }} 人已准备
        </p>
        <UiButton
          v-if="snapshot.actions.canRestart || selfRematchReady"
          variant="primary"
          :disabled="selfRematchReady"
          @click="arcade.restartGame"
        >
          <RotateCcw :size="18" />
          {{ selfRematchReady ? '等待其他玩家' : roomShell.rematchLabel ?? '准备再来一局' }}
        </UiButton>
      </div>

      <component
        v-if="gameView"
        :is="gameView"
        :snapshot="snapshot"
        @open-chat="openSharedChat"
      />

      <MatchRequestPanel
        v-if="!isSpectating && (snapshot.actions.canRequestUndo || snapshot.actions.canRequestDraw || snapshot.actions.canRequestEndTable || snapshot.request)"
        :request="snapshot.request"
        :can-request-undo="snapshot.actions.canRequestUndo"
        :can-request-draw="snapshot.actions.canRequestDraw"
        :can-request-end-table="snapshot.actions.canRequestEndTable"
        :busy="arcade.busy"
        @request="arcade.requestGameAction"
        @resolve="arcade.resolveGameRequest"
      />
    </section>

    <ArcadeChatPanel
      v-if="!isSolo"
      ref="sharedChat"
      :messages="snapshot.chat.messages"
      :max-length="snapshot.chat.maxLength"
      :self-id="snapshot.viewer?.id ?? snapshot.self.id"
      :busy="arcade.busy"
      :read-only="isSpectating"
      :send="arcade.sendChat"
    />

    <RoomInviteModal
      v-if="showQr && snapshot.phase === 'lobby' && !isSolo"
      :url="inviteUrl"
      :room-code="snapshot.roomCode"
      :title="`扫描加入${snapshot.gameName}房间`"
      @close="showQr = false"
    />

    <BaseModal
      v-if="ruleEditor"
      aria-label="房间规则"
      panel-class="rule-editor-modal"
      close-label="关闭规则设置"
      mobile-sheet
      inline
      @close="ruleEditor = null"
    >
        <span class="modal-icon"><Settings2 :size="25" /></span>
        <h2>房间规则</h2>
        <p>{{ snapshot.phase === 'finished' ? '保存后所有玩家会返回等待阶段，新规则从下一局生效。' : '保存后会同步给房间中的所有玩家，开局后不可修改。' }}</p>
        <GameRuleSettings v-model="ruleEditor" :game-key="snapshot.gameKey" :guest-mode="viewerIsGuest" />
        <UiButton variant="primary" block :disabled="arcade.busy" @click="saveRules">保存规则</UiButton>
    </BaseModal>

  </main>
</template>

<style scoped>
.arcade-room { padding-bottom: 70px; }
.guest-match-notice { margin: 0 0 18px; padding: 12px 15px; border-color: color-mix(in srgb, var(--accent) 35%, var(--line)); background: color-mix(in srgb, var(--accent) 7%, var(--surface)); }
.guest-match-notice strong,.guest-match-notice span { display: block; }.guest-match-notice strong { color: var(--accent); font-size: 13px; }.guest-match-notice span { margin-top: 4px; color: var(--muted); font-size: 11px; line-height: 1.55; }
.spectator-mode-banner { display: flex; align-items: center; gap: 11px; margin: 0 0 18px; padding: 12px 15px; border-color: color-mix(in srgb, #68c8df 38%, var(--line)); background: color-mix(in srgb, #68c8df 7%, var(--surface)); }
.spectator-mode-banner > svg { flex: 0 0 auto; color: #83d4e7; }.spectator-mode-banner span { min-width: 0; display: grid; gap: 3px; }.spectator-mode-banner strong { color: #9dddeb; font-size: 13px; }.spectator-mode-banner small { color: var(--muted); line-height: 1.45; }
.arcade-spectator-strip { display: grid; gap: 10px; margin: -10px 0 24px; padding: 12px 14px; border-style: dashed; }
.arcade-spectator-strip > header { display: flex; align-items: center; justify-content: space-between; gap: 10px; }.arcade-spectator-strip > header span { display: inline-flex; align-items: center; gap: 7px; color: #83d4e7; }.arcade-spectator-strip > header b { color: var(--muted); font-size: 10px; }
.arcade-spectator-strip > div { display: flex; flex-wrap: wrap; gap: 8px; }.arcade-spectator-strip article { min-width: min(100%, 190px); display: flex; align-items: center; gap: 8px; border: 1px solid var(--line); border-radius: var(--radius-control); padding: 8px 10px; background: var(--control-surface), var(--surface-inset); box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 28%, transparent); }.arcade-spectator-strip article > span:last-child { min-width: 0; display: grid; gap: 1px; }.arcade-spectator-strip article strong,.arcade-spectator-strip article small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.arcade-spectator-strip article small { color: var(--muted); font-size: 9px; }.arcade-spectator-strip > p { margin: 0; color: var(--muted); font-size: 10px; }
.arcade-spectator-avatar { flex: 0 0 auto; width: 30px; aspect-ratio: 1; display: grid; place-items: center; overflow: hidden; border-radius: 4px; color: #83d4e7; background: color-mix(in srgb, #68c8df 12%, var(--surface-elevated)); font-size: 11px; font-weight: 900; }.arcade-spectator-avatar img { width: 100%; height: 100%; object-fit: cover; }
.room-rule-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: -12px 0 24px; padding: 11px 13px; }
.room-rule-bar > div { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; min-width: 0; }
.room-rule-bar svg { flex: 0 0 auto; color: var(--accent); }
.room-rule-bar span { border: 1px solid var(--line); border-radius: 999px; padding: 5px 9px; color: var(--muted); background: var(--control-surface), var(--surface-inset); box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 24%, transparent); font-size: 9px; }
.room-rule-actions { flex: 0 0 auto; display: flex; gap: 8px; }
.room-rule-actions button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 36px; border: 1px solid color-mix(in srgb, var(--accent) 38%, var(--line)); border-radius: 10px; padding: 0 11px; color: var(--accent); background: color-mix(in srgb, var(--accent) 7%, transparent); font-weight: 850; }
.game-skin-card + .arcade-waiting,
.role-skin-loadout + .arcade-waiting { margin-top: 18px; }
.arcade-waiting { position:relative; min-height: min(390px, 48dvh); display: grid; place-items: center; align-content: center; gap: 12px; overflow:hidden; padding: 30px 18px; border-color:color-mix(in srgb,var(--accent) 26%,var(--line)); text-align: center; }
.arcade-waiting::before,.arcade-waiting::after { position:absolute; width:230px; aspect-ratio:1; border:1px solid var(--instrument-line); border-radius:50%; content:''; }.arcade-waiting::after { width:150px; border-color:var(--instrument-bright); border-style:dashed; }
.arcade-waiting > * { position:relative; z-index:1; }
.arcade-waiting > svg { color: var(--accent); filter:drop-shadow(0 0 12px color-mix(in srgb,var(--accent) 38%,transparent)); }
.arcade-waiting h2, .arcade-waiting p { margin: 0; }
.arcade-waiting p { color: var(--muted); }
.room-code-share { margin: 14px 0 0; border: 1px solid var(--line-strong); border-radius:var(--radius-control); padding:10px 16px; color: var(--accent); background: var(--control-surface), var(--surface-inset); box-shadow:var(--shadow-contact), inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 52%, transparent); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size: 23px; font-weight: 800; letter-spacing: .18em; }
.arcade-waiting :deep(.invite-link-panel) { width: min(100%, 620px); }
.arcade-game-stage { display: grid; gap: 22px; }
.arcade-room--active.arcade-room--immersive { display: flex; flex-direction: column; }
.arcade-room--active.arcade-room--immersive :deep(.room-page-header) { order: 1; min-height: 60px; margin: 8px 0 10px; padding: 8px 11px; }
.arcade-room--active.arcade-room--immersive :deep(.room-page-copy > small) { font-size: 8px; }
.arcade-room--active.arcade-room--immersive :deep(.room-page-title-row) { margin-top: 2px; }
.arcade-room--active.arcade-room--immersive :deep(.room-page-title-row h1) { font-size: clamp(20px, 2.5vw, 27px); }
.arcade-room--active.arcade-room--immersive > .arcade-game-stage { order: 2; gap: 14px; }
.arcade-room--active.arcade-room--immersive :deep(.host-transfer-notice),
.arcade-room--active.arcade-room--immersive > .guest-match-notice,
.arcade-room--active.arcade-room--immersive > .spectator-mode-banner { order: 3; margin-top: 18px; }
.arcade-room--active.arcade-room--immersive > .arcade-player-strip { order: 4; }
.arcade-room--active.arcade-room--immersive > .arcade-spectator-strip { order: 5; }
.arcade-room--active.arcade-room--immersive > .room-rule-bar { order: 6; }
.arcade-room--active.arcade-room--immersive > :deep(.arcade-chat-dock),
.arcade-room--active.arcade-room--immersive > :deep(.arcade-chat-panel) { order: 7; }
.result-banner { padding: 18px; text-align: center; }
.result-banner small { color: var(--accent); }
.result-banner h2 { margin: 5px 0; }
.result-banner p { color: var(--muted); }
.result-banner .rematch-progress { margin-bottom: 0; font-size: 11px; }
.result-banner .ui-button--primary { margin: 12px auto 0; }
:global(.modal-card.rule-editor-modal) { width: min(94vw, 620px); max-height: min(88vh, 820px); overflow-y: auto; }
:global(.modal-card.rule-editor-modal) > p { margin: -4px 0 20px; color: var(--muted); }
:global(.modal-card.rule-editor-modal) > .ui-button--block { margin-top: 22px; }
@media (max-width: 620px), (orientation: landscape) and (max-height: 600px) and (max-width: 980px) {
  .arcade-room--active { display: flex; flex-direction: column; }
  .arcade-room--active :deep(.room-page-header) { order: 1; }
  .arcade-room--active :deep(.host-transfer-notice),
  .arcade-room--active > .guest-match-notice,
  .arcade-room--active > .spectator-mode-banner { order: 2; }
  .arcade-room--active > .arcade-game-stage { order: 3; }
  .arcade-room--active > .arcade-player-strip { order: 4; margin-top: 18px; }
  .arcade-room--active > .arcade-spectator-strip { order: 5; margin-top: -8px; }
  .arcade-room--active > .room-rule-bar { order: 6; }
  .arcade-room--active > :deep(.arcade-chat-dock),
  .arcade-room--active > :deep(.arcade-chat-panel) { order: 7; }
  .arcade-room--active.arcade-room--board-game :deep(.room-page-header) { margin-bottom: 12px; }
  .arcade-room--active.arcade-room--board-game :deep(.room-page-copy > small) { font-size: 9px; letter-spacing: .08em; }
  .arcade-room--active.arcade-room--board-game :deep(.room-page-title-row h1) { font-size: 23px; }
  .arcade-room--active.arcade-room--board-game :deep(.room-page-actions) { overflow-x: auto; flex-wrap: nowrap; padding-bottom: 2px; }
  .room-rule-bar { align-items: stretch; flex-direction: column; }
  .room-rule-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); }
  .room-rule-actions button { width: 100%; }
  .arcade-waiting { min-height: 0; padding: 25px 14px; }
  .arcade-waiting > svg { width: 38px; height: 38px; }
  .arcade-waiting h2 { font-size: 20px; }
  .arcade-waiting .room-code-share { margin-top: 7px; font-size: 24px; }
}
@media (orientation: landscape) and (min-width: 621px) and (max-width: 980px) and (max-height: 600px) {
  .arcade-room--active.arcade-room--board-game :deep(.room-page-header) { grid-template-columns: auto minmax(0, 1fr) auto; }
  .arcade-room--active.arcade-room--board-game :deep(.room-page-actions) { grid-column: auto; width: auto; justify-content: flex-end; }
  .arcade-room--active.arcade-room--board-game > .arcade-game-stage { order: 2; }
  .arcade-room--active.arcade-room--board-game > .guest-match-notice { order: 3; margin-top: 18px; }
}
@media (min-width: 860px) {
  .arcade-room.arcade-room--wide { width: min(100%, 1080px); }
  .arcade-room.arcade-room--immersive { width: min(100%, 1680px); }
}
</style>
