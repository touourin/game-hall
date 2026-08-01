<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import QrcodeVue from 'qrcode.vue'
import {
  ArrowRight,
  Bot,
  Check,
  ChevronRight,
  CircleHelp,
  Crown,
  Eye,
  History,
  Link2,
  Maximize2,
  MessageCircle,
  Minimize2,
  Move,
  QrCode,
  RotateCcw,
  Send,
  Shield,
  Sparkles,
  Swords,
  UserRound,
  UsersRound,
  X,
} from '@lucide/vue'
import MissionTrack from './components/MissionTrack.vue'
import RoleSkinPicker from './components/RoleSkinPicker.vue'
import SecretCard from './components/SecretCard.vue'
import InviteLinkPanel from '../../components/InviteLinkPanel.vue'
import HostTransferNotice from '../../components/HostTransferNotice.vue'
import RoomExitButton from '../../components/RoomExitButton.vue'
import {
  clearRoleSkinLock,
  lockRoleSkin,
  rememberRoleSkin,
  storedRoleSkin,
  storedRoleSkinLock,
  type RoleSkinId,
} from './roleSkins'
import { useRoomStore } from './store'
import type { PlayerView, RoomSnapshot } from './types'

const props = defineProps<{ snapshot: RoomSnapshot }>()
const room = useRoomStore()

const selectedTeamIds = ref<string[]>([])
const ladyTargetId = ref<string | null>(null)
const assassinTargetId = ref<string | null>(null)
const earlyAssassinTargetId = ref<string | null>(null)
const roleSeen = ref(false)
const ladySeen = ref(false)
const showQr = ref(false)
const showIdentity = ref(false)
const showRules = ref(false)
const showChat = ref(false)
const showReplay = ref(false)
const showPlayerNumbers = ref(false)
const showLadyHistory = ref(false)
const showEarlyAssassination = ref(false)
const chatHeight = ref<number | null>(null)
const chatRestoreHeight = ref<number | null>(null)
const chatMaximized = ref(false)
const chatMoving = ref(false)
const chatOffset = ref({ x: 0, y: 0 })
const chatDraft = ref('')
const chatSheet = ref<HTMLElement | null>(null)
const chatList = ref<HTMLElement | null>(null)
const selectedReplayMission = ref<number | null>(null)
const selectedRoleSkin = ref<RoleSkinId>(storedRoleSkin())
const lockedRoleSkin = ref<RoleSkinId | null>(null)
const seenChatIds = ref(
  new Set(props.snapshot.chat.messages.map((message) => message.id)),
)

const leader = computed(() =>
  props.snapshot.players.find(
    (player) => player.id === props.snapshot.game.leaderId,
  ),
)
const ladyHolder = computed(() =>
  props.snapshot.players.find(
    (player) => player.id === props.snapshot.lady.holderId,
  ),
)
const showLadyReminder = computed(
  () =>
    props.snapshot.lady.enabled &&
    Boolean(props.snapshot.lady.holderId) &&
    ['team_building', 'team_voting', 'mission_voting'].includes(
      props.snapshot.phase,
    ),
)
const ladyReminderTiming = computed(() => {
  const missionNumber = props.snapshot.game.missionNumber
  if (missionNumber === 1) {
    return '第 2 次任务结束后首次查验'
  }
  if (missionNumber <= 4) {
    return '本次任务结束后负责查验'
  }
  return '本局仙女查验已经结束'
})
const selectedPlayers = computed(() =>
  props.snapshot.players.filter((player) =>
    props.snapshot.game.selectedTeamIds.includes(player.id),
  ),
)
const latestMission = computed(
  () => props.snapshot.game.missionHistory.at(-1) ?? null,
)
const assassinPlayer = computed(() =>
  props.snapshot.players.find((player) => player.role === 'assassin'),
)
const assassinTarget = computed(() =>
  props.snapshot.players.find(
    (player) => player.id === props.snapshot.result.assassinTargetId,
  ),
)
const assassinationHit = computed(
  () => assassinTarget.value?.role === 'merlin',
)
const shareUrl = computed(() => {
  const url = new URL(window.location.href)
  url.search = ''
  url.hash = ''
  url.searchParams.set('game', 'avalon')
  url.searchParams.set('room', props.snapshot.roomCode)
  return url.toString()
})
const phaseTitle = computed(() => {
  const titles: Record<RoomSnapshot['phase'], string> = {
    lobby: '等待圆桌集结',
    role_reveal: '确认你的身份',
    team_building: '组建任务队伍',
    team_voting: '表决任务队伍',
    mission_voting: '执行秘密任务',
    round_result: '任务结算',
    lady_select: '湖中仙女',
    lady_reveal: '仙女的启示',
    assassination: '最后的刺杀',
    game_over: '本局终章',
  }
  return titles[props.snapshot.phase]
})
const unreadChatCount = computed(
  () =>
    props.snapshot.chat.messages.filter(
      (message) =>
        message.senderId !== props.snapshot.self.id &&
        !seenChatIds.value.has(message.id),
    ).length,
)
const replayMissionNumbers = computed(() => [
  ...new Set(
    props.snapshot.game.proposalHistory.map(
      (proposal) => proposal.missionNumber,
    ),
  ),
])
const replayProposals = computed(() =>
  selectedReplayMission.value === null
    ? props.snapshot.game.proposalHistory
    : props.snapshot.game.proposalHistory.filter(
        (proposal) =>
          proposal.missionNumber === selectedReplayMission.value,
      ),
)
const chatPanelStyle = computed<Record<string, string>>(() => {
  const style: Record<string, string> = {}
  if (chatHeight.value !== null) {
    style['--chat-sheet-height'] = `${chatHeight.value}px`
  }
  style['--chat-sheet-offset-x'] = `${chatOffset.value.x}px`
  style['--chat-sheet-offset-y'] = `${chatOffset.value.y}px`
  return style
})
const activeRoleSkin = computed(
  () => lockedRoleSkin.value ?? selectedRoleSkin.value,
)

let chatResizePointerId: number | null = null
let chatResizeStartY = 0
let chatResizeStartHeight = 0
let chatMovePointerId: number | null = null
let chatMoveStartX = 0
let chatMoveStartY = 0
let chatMoveStartOffsetX = 0
let chatMoveStartOffsetY = 0
let chatMoveStartLeft = 0
let chatMoveStartTop = 0
let chatMoveWidth = 0
let chatMoveHeight = 0

watch(
  () => props.snapshot.phase,
  (phase) => {
    selectedTeamIds.value = []
    ladyTargetId.value = null
    assassinTargetId.value = null
    earlyAssassinTargetId.value = null
    ladySeen.value = false
    if (phase === 'role_reveal') {
      roleSeen.value = false
    }
    if (phase === 'game_over') {
      showEarlyAssassination.value = false
    }
  },
)
watch(
  () => [props.snapshot.roomCode, props.snapshot.phase] as const,
  ([roomCode, phase]) => {
    if (phase === 'lobby') {
      clearRoleSkinLock(roomCode)
      lockedRoleSkin.value = null
      selectedRoleSkin.value = storedRoleSkin()
      return
    }

    lockedRoleSkin.value =
      storedRoleSkinLock(roomCode) ??
      lockRoleSkin(roomCode, selectedRoleSkin.value)
  },
  { immediate: true },
)
watch(
  () => props.snapshot.chat.messages.at(-1)?.id,
  async () => {
    if (!showChat.value) return
    markChatRead()
    await scrollChatToBottom()
  },
)

function playerName(playerId: string | null): string {
  const player = props.snapshot.players.find((item) => item.id === playerId)
  return player ? playerDisplayName(player) : '未知玩家'
}

function selectRoleSkin(skin: RoleSkinId) {
  if (props.snapshot.phase !== 'lobby') return
  selectedRoleSkin.value = skin
  rememberRoleSkin(skin)
}

function playerDisplayName(player: PlayerView): string {
  return player.isBot ? `${player.name} · AI` : player.name
}

function playerNumber(playerId: string | null): number | null {
  const player = props.snapshot.players.find((item) => item.id === playerId)
  return player ? player.seat + 1 : null
}

function playerLabel(playerId: string | null): string {
  const number = playerNumber(playerId)
  const name = playerName(playerId)
  return number ? `${number}号 ${name}` : name
}

function toggleTeamPlayer(playerId: string) {
  const current = selectedTeamIds.value
  if (current.includes(playerId)) {
    selectedTeamIds.value = current.filter((id) => id !== playerId)
    return
  }
  const required = props.snapshot.game.requiredTeamSize ?? 0
  if (current.length < required) {
    selectedTeamIds.value = [...current, playerId]
  }
}

function playerClasses(player: PlayerView) {
  return {
    selected: selectedTeamIds.value.includes(player.id),
    offline: !player.connected,
    leader: player.isLeader,
  }
}

function openReplay(missionNumber: number | null = null) {
  selectedReplayMission.value = missionNumber
  showReplay.value = true
}

function missionOutcome(missionNumber: number) {
  return props.snapshot.game.missionHistory.find(
    (mission) => mission.number === missionNumber,
  )
}

function myLadyCheck(missionNumber: number, targetId: string) {
  return props.snapshot.lady.myChecks.find(
    (check) =>
      check.missionNumber === missionNumber && check.targetId === targetId,
  )
}

function revealedAlignment(playerId: string) {
  return props.snapshot.players.find((player) => player.id === playerId)
    ?.alignment
}

async function proposeTeam() {
  await room.perform('game:propose-team', {
    team_ids: selectedTeamIds.value,
  })
}

async function inspectWithLady() {
  if (!ladyTargetId.value) return
  await room.perform('game:lady-inspect', {
    target_id: ladyTargetId.value,
  })
}

async function assassinate() {
  if (!assassinTargetId.value) return
  await room.perform('game:assassinate', {
    target_id: assassinTargetId.value,
  })
}

async function earlyAssassinate() {
  if (!earlyAssassinTargetId.value) return
  const response = await room.perform('game:early-assassinate', {
    target_id: earlyAssassinTargetId.value,
  })
  if (response) showEarlyAssassination.value = false
}

function markChatRead() {
  seenChatIds.value = new Set(
    props.snapshot.chat.messages.map((message) => message.id),
  )
}

async function scrollChatToBottom() {
  await nextTick()
  if (chatList.value) {
    chatList.value.scrollTop = chatList.value.scrollHeight
  }
}

async function openChat() {
  if (chatHeight.value === null) {
    chatHeight.value = defaultChatHeight()
  }
  showChat.value = true
  markChatRead()
  await scrollChatToBottom()
}

function closeChat() {
  showChat.value = false
  markChatRead()
}

function viewportHeight(): number {
  return window.visualViewport?.height ?? window.innerHeight
}

function desktopChatEnabled(): boolean {
  return window.innerWidth >= 1000
}

function chatHeightLimits(): { min: number; max: number } {
  const edgeSpace = desktopChatEnabled() ? 48 : 12
  const max = Math.max(220, viewportHeight() - edgeSpace)
  const preferredMin = desktopChatEnabled() ? 320 : 260
  return { min: Math.min(preferredMin, max), max }
}

function clampChatHeight(height: number): number {
  const { min, max } = chatHeightLimits()
  return Math.round(Math.min(max, Math.max(min, height)))
}

function defaultChatHeight(): number {
  const preferred = desktopChatEnabled()
    ? Math.min(viewportHeight() * 0.66, 620)
    : Math.min(viewportHeight() * 0.44, 390)
  return clampChatHeight(preferred)
}

function currentChatHeight(): number {
  return chatHeight.value ?? defaultChatHeight()
}

function beginChatResize(event: PointerEvent) {
  chatResizePointerId = event.pointerId
  chatResizeStartY = event.clientY
  chatResizeStartHeight = currentChatHeight()
  chatMaximized.value = false
  ;(event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId)
}

function resizeChat(event: PointerEvent) {
  if (event.pointerId !== chatResizePointerId) return
  chatHeight.value = clampChatHeight(
    chatResizeStartHeight + chatResizeStartY - event.clientY,
  )
}

function endChatResize(event: PointerEvent) {
  if (event.pointerId !== chatResizePointerId) return
  chatResizePointerId = null
  ;(event.currentTarget as HTMLElement).releasePointerCapture?.(
    event.pointerId,
  )
  void nextTick(constrainChatOffset)
}

function resizeChatBy(pixels: number) {
  chatMaximized.value = false
  chatHeight.value = clampChatHeight(currentChatHeight() + pixels)
}

async function toggleChatSize() {
  if (chatMaximized.value) {
    chatHeight.value = clampChatHeight(
      chatRestoreHeight.value ?? defaultChatHeight(),
    )
    chatMaximized.value = false
  } else {
    chatRestoreHeight.value = currentChatHeight()
    chatHeight.value = chatHeightLimits().max
    chatMaximized.value = true
  }
  await nextTick()
  constrainChatOffset()
  await scrollChatToBottom()
}

function clampWindowPosition(
  left: number,
  top: number,
  width: number,
  height: number,
): { left: number; top: number } {
  const edge = 12
  const maxLeft = Math.max(edge, window.innerWidth - width - edge)
  const maxTop = Math.max(edge, viewportHeight() - height - edge)
  return {
    left: Math.min(maxLeft, Math.max(edge, left)),
    top: Math.min(maxTop, Math.max(edge, top)),
  }
}

function beginChatMove(event: PointerEvent) {
  if (!desktopChatEnabled() || !chatSheet.value) return
  const rect = chatSheet.value.getBoundingClientRect()
  chatMovePointerId = event.pointerId
  chatMoveStartX = event.clientX
  chatMoveStartY = event.clientY
  chatMoveStartOffsetX = chatOffset.value.x
  chatMoveStartOffsetY = chatOffset.value.y
  chatMoveStartLeft = rect.left
  chatMoveStartTop = rect.top
  chatMoveWidth = rect.width
  chatMoveHeight = rect.height
  chatMoving.value = true
  event.preventDefault()
  ;(event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId)
}

function moveChat(event: PointerEvent) {
  if (event.pointerId !== chatMovePointerId) return
  const position = clampWindowPosition(
    chatMoveStartLeft + event.clientX - chatMoveStartX,
    chatMoveStartTop + event.clientY - chatMoveStartY,
    chatMoveWidth,
    chatMoveHeight,
  )
  chatOffset.value = {
    x: chatMoveStartOffsetX + position.left - chatMoveStartLeft,
    y: chatMoveStartOffsetY + position.top - chatMoveStartTop,
  }
}

function endChatMove(event: PointerEvent) {
  if (event.pointerId !== chatMovePointerId) return
  chatMovePointerId = null
  chatMoving.value = false
  ;(event.currentTarget as HTMLElement).releasePointerCapture?.(
    event.pointerId,
  )
}

function moveChatBy(horizontal: number, vertical: number) {
  if (!desktopChatEnabled() || !chatSheet.value) return
  const rect = chatSheet.value.getBoundingClientRect()
  const position = clampWindowPosition(
    rect.left + horizontal,
    rect.top + vertical,
    rect.width,
    rect.height,
  )
  chatOffset.value = {
    x: chatOffset.value.x + position.left - rect.left,
    y: chatOffset.value.y + position.top - rect.top,
  }
}

function constrainChatOffset() {
  if (!desktopChatEnabled() || !chatSheet.value) return
  const rect = chatSheet.value.getBoundingClientRect()
  const position = clampWindowPosition(
    rect.left,
    rect.top,
    rect.width,
    rect.height,
  )
  chatOffset.value = {
    x: chatOffset.value.x + position.left - rect.left,
    y: chatOffset.value.y + position.top - rect.top,
  }
}

function formatMessageTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}

async function sendChat() {
  const content = chatDraft.value.trim()
  if (!content) return
  const response = await room.perform('chat:send', { content })
  if (response) {
    chatDraft.value = ''
    await scrollChatToBottom()
  }
}

</script>

<template>
  <main
    class="game-page page-container"
    :class="{ 'chat-open': showChat }"
    :style="chatPanelStyle"
  >
    <header class="room-header">
      <div class="room-brand">
        <Crown :size="20" />
        <div>
          <span>{{ phaseTitle }}</span>
          <strong>
            房间 {{ snapshot.roomCode }}
            <button
              class="self-number-trigger"
              type="button"
              :aria-label="`我的号码是 ${playerNumber(snapshot.self.id)} 号，查看玩家号码表`"
              @click="showPlayerNumbers = true"
            >
              <span class="self-number-value">
                {{ playerNumber(snapshot.self.id) }}号
              </span>
              <span class="self-number-copy">
                <small>我的号码</small>
                <span>查看号码表</span>
              </span>
              <ChevronRight :size="14" aria-hidden="true" />
            </button>
          </strong>
        </div>
      </div>
      <div class="header-actions">
        <button
          v-if="snapshot.phase === 'lobby'"
          class="header-action"
          type="button"
          aria-label="显示加入二维码"
          @click="showQr = true"
        >
          <QrCode :size="21" />
        </button>
        <template v-else>
          <button
            v-if="snapshot.self.role && snapshot.phase !== 'game_over'"
            class="header-action"
            type="button"
            aria-label="查看我的身份"
            @click="showIdentity = true"
          >
            <Eye :size="20" />
          </button>
          <button
            class="header-action"
            type="button"
            aria-label="查看规则提示"
            @click="showRules = true"
          >
            <CircleHelp :size="21" />
          </button>
        </template>
        <RoomExitButton
          :busy="room.busy"
          :description="
            snapshot.phase === 'lobby'
              ? '你会离开圆桌并让出号码；如果你是房主，房主将自动移交。'
              : '你的座位、号码和身份都会保留，可以从首页随时返回本局。'
          "
          @confirm="room.leaveRoom"
        />
      </div>
    </header>

    <HostTransferNotice :transfer-at="snapshot.hostTransferAt" />

    <MissionTrack
      v-if="snapshot.phase !== 'lobby' && snapshot.phase !== 'role_reveal'"
      :current-mission="snapshot.game.missionNumber"
      :history="snapshot.game.missionHistory"
      :player-count="snapshot.players.length"
      :replayable-missions="replayMissionNumbers"
      @select-mission="openReplay"
    />
    <p
      v-if="snapshot.game.proposalHistory.length"
      class="mission-replay-hint"
    >
      <History :size="14" />
      点击有记录的任务圈查看该轮复盘
    </p>
    <div
      v-if="
        snapshot.lady.history.length ||
        snapshot.actions.canEarlyAssassinate
      "
      class="game-toolbar"
    >
      <button
        v-if="snapshot.actions.canEarlyAssassinate"
        class="danger-tool"
        type="button"
        @click="showEarlyAssassination = true"
      >
        <Swords :size="17" />
        提前刺杀
      </button>
      <button
        v-if="snapshot.lady.history.length"
        type="button"
        @click="showLadyHistory = true"
      >
        <Sparkles :size="17" />
        仙女记录
        <span>{{ snapshot.lady.history.length }}</span>
      </button>
    </div>

    <div
      v-if="showLadyReminder"
      class="surface mission-lady-reminder"
      aria-label="湖中仙女当前持有者"
    >
      <span class="mission-lady-icon"><Sparkles :size="20" /></span>
      <div>
        <small>湖中仙女当前持有者</small>
        <strong>{{ playerLabel(ladyHolder?.id ?? null) }}</strong>
      </div>
      <em>{{ ladyReminderTiming }}</em>
    </div>

    <section v-if="snapshot.phase === 'lobby'" class="phase-stack">
      <div class="surface lobby-code-card">
        <span class="eyebrow">ROOM CODE</span>
        <button type="button" @click="showQr = true">
          {{ snapshot.roomCode }}
        </button>
        <p>让朋友连接同一 Wi‑Fi，输入代码或扫描二维码加入</p>
        <InviteLinkPanel
          :url="shareUrl"
          :share-title="`加入阿瓦隆房间 ${snapshot.roomCode}`"
          :share-text="`点击链接加入我的阿瓦隆房间 ${snapshot.roomCode}`"
        />
      </div>

      <div class="section-heading">
        <div>
          <span>圆桌成员</span>
          <strong>{{ snapshot.players.length }} / 10</strong>
        </div>
        <div class="lobby-heading-actions">
          <button
            v-if="snapshot.actions.canAddAiPlayer"
            class="text-button add-ai-button"
            type="button"
            :disabled="room.busy"
            @click="room.perform('room:add-ai-player')"
          >
            <Bot :size="16" /> 添加 AI
          </button>
        </div>
      </div>

      <div class="player-list">
        <div
          v-for="player in snapshot.players"
          :key="player.id"
          class="player-row"
          :class="{ offline: !player.connected }"
        >
          <span class="avatar number-avatar">{{ player.seat + 1 }}</span>
          <div>
            <strong>
              {{ player.name }}
              <span v-if="player.isBot" class="ai-player-badge">AI</span>
            </strong>
            <small>
              {{ player.seat + 1 }} 号玩家
              <template v-if="player.id === snapshot.self.id"> · 你</template>
            </small>
          </div>
          <div class="player-row-actions">
            <span v-if="player.isHost" class="status-badge gold">房主</span>
            <span v-if="!player.connected" class="status-badge">离线</span>
            <button
              v-if="snapshot.self.isHost && !player.isHost"
              class="kick-button"
              type="button"
              :aria-label="`移除 ${player.name}`"
              @click="room.perform('room:kick', { target_id: player.id })"
            >
              <X :size="15" /> 移除
            </button>
          </div>
        </div>
      </div>

      <div class="surface settings-card">
        <div class="setting-row">
          <div class="setting-icon"><Link2 :size="20" /></div>
          <div class="setting-copy">
            <strong>在大厅公开</strong>
            <span>其他人可以从首页看到并选择这个房间</span>
          </div>
          <label class="switch">
            <input
              type="checkbox"
              :checked="snapshot.settings.listed"
              :disabled="!snapshot.actions.canUpdateSettings"
              @change="
                room.perform('room:set-listed', {
                  listed: ($event.target as HTMLInputElement).checked,
                })
              "
            />
            <span />
          </label>
        </div>

        <div class="setting-row">
          <div class="setting-icon"><Sparkles :size="20" /></div>
          <div class="setting-copy">
            <strong>湖中仙女</strong>
            <span>
              第 2、3、4 次任务后秘密查验阵营
              <template v-if="!snapshot.settings.ladyRecommended"> · 建议 7 人以上</template>
            </span>
          </div>
          <label class="switch">
            <input
              type="checkbox"
              :checked="snapshot.settings.ladyEnabled"
              :disabled="!snapshot.actions.canUpdateSettings"
              @change="
                room.perform('room:set-lady', {
                  enabled: ($event.target as HTMLInputElement).checked,
                })
              "
            />
            <span />
          </label>
        </div>

        <div
          v-if="'earlyAssassinationEnabled' in snapshot.settings"
          class="setting-row"
        >
          <div class="setting-icon danger-setting-icon">
            <Swords :size="20" />
          </div>
          <div class="setting-copy">
            <strong>允许提前刺杀</strong>
            <span>刺客可在讨论阶段豪赌梅林；刺错则好人立即获胜</span>
          </div>
          <label class="switch danger-switch">
            <input
              type="checkbox"
              :checked="snapshot.settings.earlyAssassinationEnabled"
              :disabled="!snapshot.actions.canUpdateSettings"
              @change="
                room.perform('room:set-early-assassination', {
                  enabled: ($event.target as HTMLInputElement).checked,
                })
              "
            />
            <span />
          </label>
        </div>

        <div v-if="snapshot.settings.rolePreset.length" class="role-preset">
          <span>当前人数角色预设</span>
          <div>
            <span
              v-for="(role, index) in snapshot.settings.rolePreset"
              :key="`${role.code}-${index}`"
              class="role-chip"
            >
              {{ role.label }}
            </span>
          </div>
        </div>
      </div>

      <RoleSkinPicker
        :model-value="selectedRoleSkin"
        @update:model-value="selectRoleSkin"
      />

      <button
        v-if="snapshot.self.isHost"
        class="primary-button wide-button"
        type="button"
        :disabled="!snapshot.actions.canStart"
        @click="room.perform('game:start')"
      >
        <Swords :size="19" />
        {{ snapshot.players.length < 5 ? `还需 ${5 - snapshot.players.length} 人` : '开始游戏' }}
      </button>
      <div v-else class="waiting-card">
        <span class="pulse-dot" />
        等待房主开始游戏
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'role_reveal'" class="phase-stack">
      <div class="phase-intro">
        <span class="phase-icon"><Eye :size="22" /></span>
        <div>
          <h2>只让自己看到</h2>
          <p>确认周围没人偷看，再按住下方卡片。</p>
        </div>
      </div>

      <div
        v-if="snapshot.game.leaderId"
        class="surface first-leader-card"
        role="status"
      >
        <span class="first-leader-icon"><Crown :size="24" /></span>
        <div>
          <small>本局首任队长</small>
          <strong>{{ playerLabel(snapshot.game.leaderId) }}</strong>
          <p>身份确认结束后，由这位玩家首先组建任务队伍</p>
        </div>
        <em>首先带队</em>
      </div>

      <div
        v-if="snapshot.settings.ladyEnabled && snapshot.lady.holderId"
        class="surface initial-lady-card"
        role="status"
      >
        <span class="initial-lady-icon"><Sparkles :size="24" /></span>
        <div>
          <small>湖中仙女初始持有者</small>
          <strong>{{ playerLabel(snapshot.lady.holderId) }}</strong>
          <p>第 2 次任务结束后，由这位玩家首先秘密查验阵营</p>
        </div>
        <em>持有仙女</em>
      </div>

      <div class="surface player-number-roster">
        <header>
          <UsersRound :size="19" />
          <div>
            <strong>玩家号码表</strong>
            <small>本局所有讨论和投票都使用以下号码</small>
          </div>
        </header>
        <div>
          <span
            v-for="player in snapshot.players"
            :key="player.id"
            :class="{
              self: player.id === snapshot.self.id,
              leader: player.id === snapshot.game.leaderId,
            }"
          >
            <b>{{ player.seat + 1 }}号</b>
            <strong>{{ playerDisplayName(player) }}</strong>
            <span class="player-number-badges">
              <em v-if="player.id === snapshot.self.id">你</em>
              <em
                v-if="player.id === snapshot.game.leaderId"
                class="leader-badge"
              >
                <Crown :size="10" /> 队长
              </em>
              <em
                v-if="
                  snapshot.settings.ladyEnabled &&
                  player.id === snapshot.lady.holderId
                "
                class="lady-holder-badge"
              >
                <Sparkles :size="10" /> 仙女
              </em>
            </span>
          </span>
        </div>
      </div>

      <SecretCard
        v-if="snapshot.self.role"
        :title="snapshot.self.role.label"
        :subtitle="snapshot.self.role.alignment === 'good' ? '亚瑟阵营' : '莫德雷德阵营'"
        :role-code="snapshot.self.role.code"
        :role-skin="activeRoleSkin"
        @seen="roleSeen = true"
      >
        <p class="secret-description">{{ snapshot.self.role.description }}</p>
        <div v-if="snapshot.self.role.knowledge.length" class="knowledge-list">
          <span
            v-for="item in snapshot.self.role.knowledge"
            :key="item.playerId"
          >
            {{ playerLabel(item.playerId) }} · {{ item.label }}
          </span>
        </div>
        <p v-else class="muted-secret">你没有额外可见信息</p>
      </SecretCard>

      <button
        v-if="snapshot.actions.canConfirmRole"
        class="primary-button wide-button"
        type="button"
        :disabled="!roleSeen"
        @click="room.perform('game:confirm-role')"
      >
        <Check :size="19" /> 我已记住身份
      </button>
      <div v-else class="waiting-card">
        <span class="pulse-dot" />
        已确认，等待其他玩家
      </div>
      <p class="center-note">
        已确认 {{ snapshot.game.roleConfirmedCount }} / {{ snapshot.players.length }}
      </p>
    </section>

    <section v-else-if="snapshot.phase === 'team_building'" class="phase-stack">
      <div class="phase-intro">
        <span class="phase-icon"><UsersRound :size="22" /></span>
        <div>
          <h2>第 {{ snapshot.game.missionNumber }} 次任务</h2>
          <p>
            队长 {{ playerLabel(leader?.id ?? null) }} 需要选择
            {{ snapshot.game.requiredTeamSize }} 名成员
          </p>
        </div>
        <span class="attempt-badge">第 {{ snapshot.game.proposalAttempt }} 次组队</span>
      </div>

      <div
        v-if="snapshot.game.lastTeamVotes.length"
        class="surface previous-votes"
      >
        <span>上一轮表决</span>
        <div>
          <span
            v-for="vote in snapshot.game.lastTeamVotes"
            :key="vote.playerId"
            :class="vote.approve ? 'vote-yes' : 'vote-no'"
          >
            {{ playerLabel(vote.playerId) }} {{ vote.approve ? '赞成' : '反对' }}
          </span>
        </div>
      </div>

      <template v-if="snapshot.actions.canProposeTeam">
        <div class="selection-counter">
          <span>选择任务成员</span>
          <strong>{{ selectedTeamIds.length }} / {{ snapshot.game.requiredTeamSize }}</strong>
        </div>
        <div class="player-grid">
          <button
            v-for="player in snapshot.players"
            :key="player.id"
            type="button"
            class="player-tile"
            :class="playerClasses(player)"
            @click="toggleTeamPlayer(player.id)"
          >
            <span class="avatar number-avatar">{{ player.seat + 1 }}</span>
            <strong>{{ playerDisplayName(player) }}</strong>
            <span
              v-if="player.isLeader || player.id === snapshot.lady.holderId"
              class="player-tile-badges"
            >
              <small v-if="player.isLeader" class="leader-chip">
                <Crown :size="10" /> 队长
              </small>
              <small
                v-if="player.id === snapshot.lady.holderId"
                class="lady-chip"
              >
                <Sparkles :size="10" /> 仙女
              </small>
            </span>
            <Check v-if="selectedTeamIds.includes(player.id)" :size="18" />
          </button>
        </div>
        <button
          class="primary-button wide-button"
          type="button"
          :disabled="selectedTeamIds.length !== snapshot.game.requiredTeamSize"
          @click="proposeTeam"
        >
          提交任务队伍 <ChevronRight :size="19" />
        </button>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot" />
        <strong>{{ playerLabel(leader?.id ?? null) }} 正在选择队伍</strong>
        <small>可以面对面讨论并给队长建议</small>
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'team_voting'" class="phase-stack">
      <div class="phase-intro">
        <span class="phase-icon"><Shield :size="22" /></span>
        <div>
          <h2>这支队伍可信吗？</h2>
          <p>过半赞成才会进入任务，平票视为否决。</p>
        </div>
      </div>

      <div class="surface selected-team-card">
        <span>任务成员</span>
        <div class="selected-team">
          <div v-for="player in selectedPlayers" :key="player.id">
            <span class="avatar number-avatar">{{ player.seat + 1 }}</span>
            <strong>{{ playerDisplayName(player) }}</strong>
          </div>
        </div>
      </div>

      <div v-if="snapshot.actions.canVoteTeam" class="vote-actions">
        <button
          class="decision-button reject"
          type="button"
          @click="room.perform('game:vote-team', { approve: false })"
        >
          <X :size="25" />
          <strong>反对</strong>
          <span>重新组队</span>
        </button>
        <button
          class="decision-button approve"
          type="button"
          @click="room.perform('game:vote-team', { approve: true })"
        >
          <Check :size="25" />
          <strong>赞成</strong>
          <span>执行任务</span>
        </button>
      </div>
      <div v-else class="waiting-card">
        <span class="pulse-dot" />
        投票已锁定，等待其他玩家
      </div>
      <p class="center-note">
        已提交 {{ snapshot.game.teamVotesSubmitted }} / {{ snapshot.players.length }}
      </p>
    </section>

    <section v-else-if="snapshot.phase === 'mission_voting'" class="phase-stack">
      <div class="phase-intro">
        <span class="phase-icon"><Swords :size="22" /></span>
        <div>
          <h2>任务已经出发</h2>
          <p>
            <template v-if="snapshot.game.failThreshold === 2">本轮至少两张失败票才会失败。</template>
            <template v-else>只要出现一张失败票，任务就会失败。</template>
          </p>
        </div>
      </div>

      <div class="surface selected-team-card">
        <span>执行任务</span>
        <div class="selected-team">
          <div v-for="player in selectedPlayers" :key="player.id">
            <span class="avatar number-avatar">{{ player.seat + 1 }}</span>
            <strong>{{ playerDisplayName(player) }}</strong>
          </div>
        </div>
      </div>

      <template v-if="snapshot.actions.canVoteMission">
        <p class="private-warning"><Eye :size="16" /> 任务选择不会公开你的名字</p>
        <div class="mission-actions">
          <button
            class="mission-card success-card"
            type="button"
            @click="room.perform('game:vote-mission', { success: true })"
          >
            <Check :size="28" />
            <strong>任务成功</strong>
            <span>守护亚瑟的荣光</span>
          </button>
          <button
            v-if="snapshot.actions.canMissionFail"
            class="mission-card fail-card"
            type="button"
            @click="room.perform('game:vote-mission', { success: false })"
          >
            <X :size="28" />
            <strong>任务失败</strong>
            <span>暗中破坏这次行动</span>
          </button>
        </div>
        <p v-if="!snapshot.actions.canMissionFail" class="center-note">
          好人阵营只能提交任务成功
        </p>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot" />
        <strong>
          {{ snapshot.game.myMissionVoteSubmitted ? '任务票已提交' : '等待任务成员秘密选择' }}
        </strong>
        <small>面对面保持讨论，但不要让别人看到你的屏幕</small>
      </div>
      <p class="center-note">
        已提交 {{ snapshot.game.missionVotesSubmitted }} /
        {{ snapshot.game.selectedTeamIds.length }}
      </p>
    </section>

    <section v-else-if="snapshot.phase === 'round_result'" class="phase-stack">
      <div
        v-if="latestMission"
        class="result-hero"
        :class="latestMission.success ? 'success' : 'failed'"
      >
        <span>
          <Check v-if="latestMission.success" :size="34" />
          <X v-else :size="34" />
        </span>
        <p>第 {{ latestMission.number }} 次任务</p>
        <h2>{{ latestMission.success ? '任务成功' : '任务失败' }}</h2>
        <strong>出现 {{ latestMission.failCount }} 张失败票</strong>
      </div>

      <div class="score-summary">
        <div>
          <span>亚瑟阵营</span>
          <strong>{{ snapshot.game.successCount }}</strong>
          <small>次成功</small>
        </div>
        <div>
          <span>莫德雷德阵营</span>
          <strong>{{ snapshot.game.failCount }}</strong>
          <small>次失败</small>
        </div>
      </div>

      <button
        v-if="snapshot.actions.canContinueRound"
        class="primary-button wide-button"
        type="button"
        @click="room.perform('game:continue')"
      >
        继续结算 <ArrowRight :size="19" />
      </button>
      <div v-else class="waiting-card">
        <span class="pulse-dot" />
        等待房主继续
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'lady_select'" class="phase-stack">
      <div class="phase-intro lady-intro">
        <span class="phase-icon"><Sparkles :size="22" /></span>
        <div>
          <h2>湖中仙女苏醒</h2>
          <p>
            当前持有者是 {{ playerLabel(snapshot.lady.holderId) }}，查验结果只对持有者可见。
          </p>
        </div>
      </div>

      <template v-if="snapshot.actions.canUseLady">
        <div class="selection-counter">
          <span>选择一名玩家查验阵营</span>
          <strong>{{ ladyTargetId ? '已选择' : '未选择' }}</strong>
        </div>
        <div class="player-grid">
          <button
            v-for="player in snapshot.players.filter((item) =>
              snapshot.lady.eligibleTargetIds.includes(item.id),
            )"
            :key="player.id"
            type="button"
            class="player-tile"
            :class="{ selected: ladyTargetId === player.id }"
            @click="ladyTargetId = player.id"
          >
            <span class="avatar number-avatar">{{ player.seat + 1 }}</span>
            <strong>{{ playerDisplayName(player) }}</strong>
            <Sparkles v-if="ladyTargetId === player.id" :size="18" />
          </button>
        </div>
        <button
          class="primary-button wide-button"
          type="button"
          :disabled="!ladyTargetId"
          @click="inspectWithLady"
        >
          秘密查验 <ChevronRight :size="19" />
        </button>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot" />
        <strong>{{ playerLabel(snapshot.lady.holderId) }} 正在选择查验对象</strong>
        <small>持有者可以隐瞒或谎报最终看到的阵营</small>
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'lady_reveal'" class="phase-stack">
      <div class="phase-intro lady-intro">
        <span class="phase-icon"><Sparkles :size="22" /></span>
        <div>
          <h2>仙女的启示</h2>
          <p>
            {{ playerLabel(snapshot.lady.pendingInspectorId) }} 查验了
            {{ playerLabel(snapshot.lady.pendingTargetId) }}
          </p>
        </div>
      </div>

      <template v-if="snapshot.actions.canAcknowledgeLady && snapshot.lady.currentResult">
        <SecretCard
          :title="playerLabel(snapshot.lady.currentResult.targetId)"
          :subtitle="
            snapshot.lady.currentResult.alignment === 'good'
              ? '属于好人阵营'
              : '属于坏人阵营'
          "
          hint="按住查看查验结果"
          @seen="ladySeen = true"
        />
        <p class="center-note">你可以向大家说出真相，也可以撒谎。</p>
        <button
          class="primary-button wide-button"
          type="button"
          :disabled="!ladySeen"
          @click="room.perform('game:lady-acknowledge')"
        >
          我已记住结果 <Check :size="19" />
        </button>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot" />
        <strong>等待查验者确认秘密结果</strong>
        <small>
          湖中仙女将传给 {{ playerLabel(snapshot.lady.pendingTargetId) }}
        </small>
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'assassination'" class="phase-stack">
      <div class="assassination-hero">
        <span><Swords :size="29" /></span>
        <p>好人已完成三次任务</p>
        <h2>刺客的最后机会</h2>
        <strong>找出梅林，邪恶阵营仍可翻盘</strong>
      </div>

      <div class="surface assassination-alignments">
        <header>
          <Eye :size="19" />
          <div>
            <strong>最终阵营公开</strong>
            <small>奥伯伦已与坏人会合；具体角色在刺杀后揭晓</small>
          </div>
        </header>
        <div>
          <span
            v-for="player in snapshot.players"
            :key="player.id"
            :class="player.alignment"
          >
            <b>{{ player.seat + 1 }}号</b>
            <strong>{{ playerDisplayName(player) }}</strong>
            <em>{{ player.alignment === 'evil' ? '坏人' : '好人' }}</em>
          </span>
        </div>
      </div>

      <template v-if="snapshot.actions.canAssassinate">
        <div class="selection-counter">
          <span>选择你认为的梅林</span>
          <strong>{{ assassinTargetId ? '目标锁定' : '谨慎选择' }}</strong>
        </div>
        <div class="player-grid">
          <button
            v-for="player in snapshot.players.filter(
              (item) => item.alignment === 'good',
            )"
            :key="player.id"
            type="button"
            class="player-tile"
            :class="{ selected: assassinTargetId === player.id }"
            @click="assassinTargetId = player.id"
          >
            <span class="avatar number-avatar">{{ player.seat + 1 }}</span>
            <strong>{{ playerDisplayName(player) }}</strong>
            <Swords v-if="assassinTargetId === player.id" :size="18" />
          </button>
        </div>
        <button
          class="danger-button wide-button"
          type="button"
          :disabled="!assassinTargetId"
          @click="assassinate"
        >
          确认刺杀 {{ playerLabel(assassinTargetId) }}
        </button>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot danger-dot" />
        <strong>邪恶势力正在做最后判断</strong>
        <small>刺客确认前，所有玩家仍需隐藏身份</small>
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'game_over'" class="phase-stack">
      <div
        class="final-hero"
        :class="snapshot.result.winner === 'good' ? 'good' : 'evil'"
      >
        <span>
          <Shield v-if="snapshot.result.winner === 'good'" :size="31" />
          <Swords v-else :size="31" />
        </span>
        <p>{{ snapshot.result.winner === 'good' ? '亚瑟的荣光延续' : '阴影笼罩阿瓦隆' }}</p>
        <h2>{{ snapshot.result.winner === 'good' ? '好人阵营获胜' : '坏人阵营获胜' }}</h2>
        <strong>{{ snapshot.result.reason }}</strong>
      </div>

      <div
        v-if="assassinTarget"
        class="surface assassination-record"
        :class="assassinationHit ? 'hit' : 'missed'"
      >
        <header>
          <span><Swords :size="21" /></span>
          <div>
            <strong>刺杀记录</strong>
            <small>
              {{
                snapshot.result.assassinationWasEarly
                  ? '刺客在任务结束前发动了提前刺杀'
                  : '好人完成三次任务后的最终选择'
              }}
            </small>
          </div>
          <span class="assassination-status">
            {{ assassinationHit ? '命中梅林' : '刺杀失败' }}
          </span>
        </header>

        <div class="assassination-chain">
          <div v-if="assassinPlayer">
            <span class="avatar number-avatar">
              {{ assassinPlayer.seat + 1 }}
            </span>
            <strong>{{ playerDisplayName(assassinPlayer) }}</strong>
            <small>刺客</small>
          </div>
          <ArrowRight :size="20" />
          <div>
            <span class="avatar number-avatar">
              {{ assassinTarget.seat + 1 }}
            </span>
            <strong>{{ playerDisplayName(assassinTarget) }}</strong>
            <small>{{ assassinTarget.roleLabel }}</small>
          </div>
        </div>

        <p>
          {{ playerLabel(assassinPlayer?.id ?? null) }} 选择刺杀
          {{ playerLabel(assassinTarget.id) }}，其真实身份为
          <strong>{{ assassinTarget.roleLabel }}</strong>。
        </p>
      </div>

      <div class="surface role-reveal-list">
        <span>身份揭晓</span>
        <div
          v-for="player in snapshot.players"
          :key="player.id"
          class="reveal-row"
        >
          <span class="avatar number-avatar">{{ player.seat + 1 }}</span>
          <strong>{{ playerDisplayName(player) }}</strong>
          <span :class="['alignment-label', player.alignment]">
            {{ player.roleLabel }}
          </span>
        </div>
      </div>

      <button
        v-if="snapshot.actions.canRestart"
        class="primary-button wide-button"
        type="button"
        @click="room.perform('game:restart')"
      >
        <RotateCcw :size="18" /> 返回大厅再来一局
      </button>
      <div v-else class="waiting-card">
        <span class="pulse-dot" />
        等待房主决定是否再来一局
      </div>
    </section>

    <div
      v-if="showEarlyAssassination && snapshot.actions.canEarlyAssassinate"
      class="modal-backdrop"
      @click.self="showEarlyAssassination = false"
    >
      <section
        class="modal-card early-assassination-modal"
        role="dialog"
        aria-modal="true"
        aria-label="提前刺杀"
      >
        <button
          class="modal-close"
          type="button"
          aria-label="关闭提前刺杀"
          @click="showEarlyAssassination = false"
        >
          <X :size="20" />
        </button>
        <span class="modal-icon danger-modal-icon">
          <Swords :size="25" />
        </span>
        <h2>发动提前刺杀</h2>
        <p>刺中梅林，坏人立即获胜；刺错，好人立即获胜。确认后无法撤销。</p>

        <div class="player-grid early-assassination-targets">
          <button
            v-for="player in snapshot.players.filter(
              (item) => item.id !== snapshot.self.id,
            )"
            :key="player.id"
            type="button"
            class="player-tile"
            :class="{ selected: earlyAssassinTargetId === player.id }"
            @click="earlyAssassinTargetId = player.id"
          >
            <span class="avatar number-avatar">{{ player.seat + 1 }}</span>
            <strong>{{ playerDisplayName(player) }}</strong>
            <Swords v-if="earlyAssassinTargetId === player.id" :size="18" />
          </button>
        </div>

        <button
          class="danger-button wide-button"
          type="button"
          :disabled="!earlyAssassinTargetId"
          @click="earlyAssassinate"
        >
          确认刺杀 {{ playerLabel(earlyAssassinTargetId) }}
        </button>
      </section>
    </div>

    <div
      v-if="showLadyHistory"
      class="modal-backdrop"
      @click.self="showLadyHistory = false"
    >
      <section
        class="modal-card lady-history-modal"
        role="dialog"
        aria-modal="true"
        aria-label="湖中仙女查验历史"
      >
        <button
          class="modal-close"
          type="button"
          aria-label="关闭仙女记录"
          @click="showLadyHistory = false"
        >
          <X :size="20" />
        </button>
        <span class="modal-icon"><Sparkles :size="25" /></span>
        <h2>仙女记录</h2>
        <p>查验关系公开，查验结果在游戏中保持私密</p>

        <div class="lady-history-list">
          <article
            v-for="check in snapshot.lady.history"
            :key="`${check.missionNumber}-${check.inspectorId}-${check.targetId}`"
            class="lady-history-item"
          >
            <header>
              第 {{ check.missionNumber }} 次任务后
            </header>
            <div class="lady-history-chain">
              <div>
                <span class="avatar number-avatar">
                  {{ playerNumber(check.inspectorId) ?? check.inspectorName.slice(0, 1) }}
                </span>
                <strong>{{ playerLabel(check.inspectorId) }}</strong>
                <small>查验者</small>
              </div>
              <ArrowRight :size="19" />
              <div>
                <span class="avatar number-avatar">
                  {{ playerNumber(check.targetId) ?? check.targetName.slice(0, 1) }}
                </span>
                <strong>{{ playerLabel(check.targetId) }}</strong>
                <small>被查验并接过仙女</small>
              </div>
            </div>

            <div
              v-if="myLadyCheck(check.missionNumber, check.targetId)"
              class="lady-history-result private"
              :class="
                myLadyCheck(check.missionNumber, check.targetId)?.alignment
              "
            >
              <Eye :size="15" />
              你看到：
              {{
                myLadyCheck(check.missionNumber, check.targetId)?.alignment ===
                'good'
                  ? '好人阵营'
                  : '坏人阵营'
              }}
            </div>
            <div
              v-else-if="
                snapshot.phase === 'game_over' &&
                revealedAlignment(check.targetId)
              "
              class="lady-history-result revealed"
              :class="revealedAlignment(check.targetId)"
            >
              真实阵营：
              {{
                revealedAlignment(check.targetId) === 'good'
                  ? '好人阵营'
                  : '坏人阵营'
              }}
            </div>
            <div v-else class="lady-history-result hidden">
              结果仅 {{ playerLabel(check.inspectorId) }} 可见
            </div>
          </article>
        </div>

        <div class="lady-current-holder">
          <Sparkles :size="16" />
          {{ snapshot.phase === 'game_over' ? '最终' : '当前' }}持有者：
          <strong>{{ playerLabel(snapshot.lady.holderId) }}</strong>
        </div>
      </section>
    </div>

    <div
      v-if="showReplay"
      class="modal-backdrop"
      @click.self="showReplay = false"
    >
      <section
        class="modal-card replay-modal"
        role="dialog"
        aria-modal="true"
        aria-label="组队投票复盘"
      >
        <button
          class="modal-close"
          type="button"
          aria-label="关闭投票复盘"
          @click="showReplay = false"
        >
          <X :size="20" />
        </button>
        <span class="modal-icon"><History :size="25" /></span>
        <h2>
          {{ selectedReplayMission === null ? '投票复盘' : `第 ${selectedReplayMission} 轮复盘` }}
        </h2>
        <p>
          {{ selectedReplayMission === null ? '按时间记录每次组队和公开表决' : '本轮全部组队和公开表决' }}
        </p>

        <div class="replay-list">
          <article
            v-for="(proposal, index) in replayProposals"
            :key="`${proposal.missionNumber}-${proposal.attempt}-${index}`"
            class="replay-round"
          >
            <header>
              <div>
                <strong>
                  第 {{ proposal.missionNumber }} 次任务
                </strong>
                <small>第 {{ proposal.attempt }} 次组队</small>
                <span class="replay-leader">
                  <Crown :size="12" />
                  队长 {{ playerLabel(proposal.leaderId) }}
                </span>
              </div>
              <span :class="proposal.accepted ? 'accepted' : 'rejected'">
                {{ proposal.accepted ? '通过' : '否决' }}
              </span>
            </header>

            <div class="replay-team">
              <span>任务队伍</span>
              <div>
                <strong
                  v-for="playerId in proposal.teamIds"
                  :key="playerId"
                  :class="{ leader: playerId === proposal.leaderId }"
                >
                  {{ playerLabel(playerId) }}
                  <small v-if="playerId === proposal.leaderId">队长</small>
                </strong>
              </div>
            </div>

            <div class="replay-votes">
              <span
                v-for="vote in proposal.votes"
                :key="vote.playerId"
                :class="vote.approve ? 'vote-yes' : 'vote-no'"
              >
                {{ playerLabel(vote.playerId) }}
                {{ vote.approve ? '赞成' : '反对' }}
              </span>
            </div>

            <div
              v-if="proposal.accepted && missionOutcome(proposal.missionNumber)"
              class="replay-mission-result"
              :class="
                missionOutcome(proposal.missionNumber)?.success
                  ? 'success'
                  : 'failed'
              "
            >
              <span>
                {{
                  missionOutcome(proposal.missionNumber)?.success
                    ? '任务成功'
                    : '任务失败'
                }}
              </span>
              <strong>
                {{ missionOutcome(proposal.missionNumber)?.failCount }} 张失败票
              </strong>
            </div>
          </article>
        </div>
        <small class="replay-privacy">
          任务票保持匿名，仅展示失败票总数
        </small>
      </section>
    </div>

    <button
      v-if="!showChat"
      class="chat-dock"
      type="button"
      aria-label="打开文字聊天"
      @click="openChat"
    >
      <MessageCircle :size="20" />
      <strong>聊天</strong>
      <span v-if="unreadChatCount" class="unread-badge">
        {{ unreadChatCount > 9 ? '9+' : unreadChatCount }}
      </span>
    </button>

    <section
      v-if="showChat"
      ref="chatSheet"
      class="chat-sheet chat-sheet--docked"
      :class="{ 'is-moving': chatMoving }"
      role="region"
      aria-label="房间文字聊天"
    >
        <div
          class="chat-resize-handle"
          role="separator"
          aria-label="拖动调整聊天框高度"
          aria-orientation="horizontal"
          :aria-valuemin="chatHeightLimits().min"
          :aria-valuemax="chatHeightLimits().max"
          :aria-valuenow="currentChatHeight()"
          tabindex="0"
          @pointerdown.prevent="beginChatResize"
          @pointermove.prevent="resizeChat"
          @pointerup="endChatResize"
          @pointercancel="endChatResize"
          @keydown.up.prevent="resizeChatBy(60)"
          @keydown.down.prevent="resizeChatBy(-60)"
          @keydown.home.prevent="chatHeight = chatHeightLimits().min"
          @keydown.end.prevent="chatHeight = chatHeightLimits().max"
        >
          <span />
        </div>
        <header class="chat-sheet-header">
          <div
            class="chat-move-handle"
            role="button"
            tabindex="0"
            aria-label="拖动聊天窗口，方向键也可移动"
            @pointerdown="beginChatMove"
            @pointermove="moveChat"
            @pointerup="endChatMove"
            @pointercancel="endChatMove"
            @keydown.left.prevent="moveChatBy(-30, 0)"
            @keydown.right.prevent="moveChatBy(30, 0)"
            @keydown.up.prevent="moveChatBy(0, -30)"
            @keydown.down.prevent="moveChatBy(0, 30)"
          >
            <Move class="chat-move-icon" :size="17" aria-hidden="true" />
            <span class="chat-online-dot" />
            <div>
              <strong>圆桌密谈</strong>
              <small>{{ snapshot.players.filter((player) => player.connected).length }} 人在线</small>
            </div>
          </div>
          <div class="chat-header-actions">
            <button
              class="chat-size-button"
              type="button"
              :aria-label="chatMaximized ? '还原聊天框' : '放大聊天框'"
              @click="toggleChatSize"
            >
              <Minimize2 v-if="chatMaximized" :size="19" />
              <Maximize2 v-else :size="19" />
            </button>
            <button class="modal-close" type="button" aria-label="关闭聊天" @click="closeChat">
              <X :size="20" />
            </button>
          </div>
        </header>

        <div ref="chatList" class="chat-list" aria-live="polite">
          <div v-if="!snapshot.chat.messages.length" class="chat-empty">
            <MessageCircle :size="28" />
            <strong>这里还很安静</strong>
            <span>发一条消息开始圆桌讨论</span>
          </div>
          <article
            v-for="message in snapshot.chat.messages"
            :key="message.id"
            class="chat-message"
            :class="{ mine: message.senderId === snapshot.self.id }"
          >
            <span class="chat-avatar">
              {{ playerNumber(message.senderId) ?? message.senderName.slice(0, 1) }}
            </span>
            <div>
              <header>
                <strong>
                  <template v-if="playerNumber(message.senderId)">
                    {{ playerNumber(message.senderId) }}号 ·
                  </template>
                  {{ message.senderName }}
                </strong>
                <time :datetime="message.createdAt">
                  {{ formatMessageTime(message.createdAt) }}
                </time>
              </header>
              <p>{{ message.content }}</p>
            </div>
          </article>
        </div>

        <form class="chat-composer" @submit.prevent="sendChat">
          <textarea
            v-model="chatDraft"
            rows="1"
            :maxlength="snapshot.chat.maxLength"
            placeholder="输入消息…"
            aria-label="聊天消息"
            @keydown.enter.exact.prevent="sendChat"
          />
          <button
            type="submit"
            aria-label="发送消息"
            :disabled="!chatDraft.trim() || room.busy"
          >
            <Send :size="19" />
          </button>
          <small>房间内所有玩家可见 · {{ chatDraft.length }}/{{ snapshot.chat.maxLength }}</small>
        </form>
    </section>

    <div v-if="showQr" class="modal-backdrop" @click.self="showQr = false">
      <section class="modal-card qr-modal" role="dialog" aria-modal="true">
        <button class="modal-close" aria-label="关闭" @click="showQr = false">
          <X :size="20" />
        </button>
        <span class="modal-icon"><QrCode :size="25" /></span>
        <h2>扫描加入圆桌</h2>
        <p>请先连接与服务器相同的 Wi‑Fi</p>
        <div class="qr-frame">
          <QrcodeVue :value="shareUrl" :size="196" level="M" />
        </div>
        <strong class="modal-room-code">{{ snapshot.roomCode }}</strong>
        <small>{{ shareUrl }}</small>
      </section>
    </div>

    <div
      v-if="showPlayerNumbers"
      class="modal-backdrop"
      @click.self="showPlayerNumbers = false"
    >
      <section
        class="modal-card player-number-modal"
        role="dialog"
        aria-modal="true"
        aria-label="玩家号码表"
      >
        <button
          class="modal-close"
          type="button"
          aria-label="关闭玩家号码表"
          @click="showPlayerNumbers = false"
        >
          <X :size="20" />
        </button>
        <span class="modal-icon"><UsersRound :size="25" /></span>
        <h2>玩家号码表</h2>
        <p>本局号码保持不变</p>

        <div class="player-number-list">
          <div
            v-for="player in snapshot.players"
            :key="player.id"
            :class="{ self: player.id === snapshot.self.id }"
          >
            <span>{{ player.seat + 1 }}</span>
            <strong>{{ player.name }}</strong>
            <small v-if="player.isBot">AI</small>
            <small v-if="player.id === snapshot.self.id">你</small>
          </div>
        </div>
      </section>
    </div>

    <div
      v-if="showIdentity && snapshot.self.role"
      class="modal-backdrop"
      @click.self="showIdentity = false"
    >
      <section class="modal-card identity-modal" role="dialog" aria-modal="true">
        <button
          class="modal-close"
          aria-label="关闭"
          @click="showIdentity = false"
        >
          <X :size="20" />
        </button>
        <SecretCard
          :title="snapshot.self.role.label"
          :subtitle="snapshot.self.role.alignment === 'good' ? '亚瑟阵营' : '莫德雷德阵营'"
          :role-code="snapshot.self.role.code"
          :role-skin="activeRoleSkin"
          hint="按住重新查看身份"
        >
          <p class="secret-description">{{ snapshot.self.role.description }}</p>
          <div v-if="snapshot.self.role.knowledge.length" class="knowledge-list">
            <span
              v-for="item in snapshot.self.role.knowledge"
              :key="item.playerId"
            >
              {{ playerLabel(item.playerId) }} · {{ item.label }}
            </span>
          </div>
          <div v-if="snapshot.lady.myChecks.length" class="knowledge-list">
            <span
              v-for="check in snapshot.lady.myChecks"
              :key="`${check.missionNumber}-${check.targetId}`"
            >
              仙女：{{ playerLabel(check.targetId) }} ·
              {{ check.alignment === 'good' ? '好人阵营' : '坏人阵营' }}
            </span>
          </div>
        </SecretCard>
      </section>
    </div>

    <div v-if="showRules" class="modal-backdrop" @click.self="showRules = false">
      <section class="modal-card rules-modal" role="dialog" aria-modal="true">
        <button class="modal-close" aria-label="关闭" @click="showRules = false">
          <X :size="20" />
        </button>
        <span class="modal-icon"><CircleHelp :size="25" /></span>
        <h2>本局提示</h2>
        <ul>
          <li>好人只能提交任务成功，坏人可选择成功或失败。</li>
          <li>队伍表决需要过半赞成，平票视为否决。</li>
          <li>连续五次组队被否决，坏人直接获胜。</li>
          <li v-if="snapshot.players.length >= 7">第四次任务需要两张失败票才会失败。</li>
          <li v-if="snapshot.settings.ladyEnabled">仙女只查阵营，持有者可以谎报查验结果。</li>
        </ul>
      </section>
    </div>
  </main>
</template>
