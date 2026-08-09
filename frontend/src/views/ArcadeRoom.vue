<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  Bot,
  ChevronRight,
  CircleHelp,
  Crown,
  Eye,
  QrCode,
  RotateCcw,
  Settings2,
  UsersRound,
  X,
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
import RoomKickButton from '../components/RoomKickButton.vue'
import ModeGuide from '../components/ModeGuide.vue'
import PressRevealCard from '../components/PressRevealCard.vue'
import RoleSkinLoadoutPicker from '../components/RoleSkinLoadoutPicker.vue'
import { useArcadeStore } from '../stores/arcade'
import {
  isAvalonArcadeSnapshot,
  type ArcadeSnapshot,
} from '../types/arcade'
import type { RoleSkinLoadoutRoleOption } from '../components/uiTypes'
import { gameRuleLabels, withDefaultGameRules } from '../gameRules'
import { isSoloGameKey } from '../gameCatalog'
import { AVALON_COURT_GUIDE } from '../gameModeGuides'
import {
  ROLE_SKINS,
  ROLE_SKIN_ROLES,
  clearRoleSkinLoadoutLock,
  defaultRoleSkinLoadout,
  lockRoleSkinLoadout,
  rememberRoleSkinLoadout,
  roleArtwork,
  roleArtworkFraming,
  roleSkinName,
  roleSkinRoleCode,
  storedRoleSkinLoadout,
  storedRoleSkinLoadoutLock,
  type RoleSkinLoadout,
  type RoleSkinId,
} from '../gameRoleSkins'
import {
  emptyAvalonRoleSkinProgress,
  isAvalonRoleSkinFreeWeek,
  isRoleSkinUnlocked,
  loadAvalonRoleSkinProgress,
} from '../avalonRoleSkinProgress'
import {
  gameSkinCssVariables,
  gameSkinKind,
  rememberGameSkin,
  storedGameSkin,
  type GameSkinId,
} from '../gameSkins'
import DoudizhuTable from '../games/doudizhu/DoudizhuTable.vue'
import DepartedSuspicionTable from '../games/departed_suspicion/DepartedSuspicionTable.vue'
import GoBoard from '../games/go/GoBoard.vue'
import GomokuBoard from '../games/gomoku/GomokuBoard.vue'
import XiangqiBoard from '../games/xiangqi/XiangqiBoard.vue'
import JunqiBoard from '../games/junqi/JunqiBoard.vue'
import ReactionTest from '../games/reaction/ReactionTest.vue'
import SchulteGrid from '../games/schulte/SchulteGrid.vue'
import MinesweeperBoard from '../games/minesweeper/MinesweeperBoard.vue'
import HanoiGame from '../games/hanoi/HanoiGame.vue'
import MonopolyBoard from '../games/monopoly/MonopolyBoard.vue'
import PokerTable from '../games/poker/PokerTable.vue'
import AvalonTable from '../games/avalon/AvalonTable.vue'
import { thirdPartyGameComponent } from '../thirdPartyGameRegistry'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const emit = defineEmits<{ settings: [] }>()
const arcade = useArcadeStore()
const pluginGameComponent = computed(() => thirdPartyGameComponent(props.snapshot.gameKey))
const avalonSnapshot = computed(
  () => isAvalonArcadeSnapshot(props.snapshot) ? props.snapshot.game : null,
)
const ruleEditor = ref<Record<string, unknown> | null>(null)
const showQr = ref(false)
const showPlayerNumbers = ref(false)
const showIdentity = ref(false)
const showAvalonRules = ref(false)
const selectedAiDifficulty = ref(
  props.snapshot.ai?.defaultDifficulty ?? 'normal',
)
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
const roleSkinAccountId = computed(() => (
  props.snapshot.viewer?.accountId
  ?? props.snapshot.self.accountId
  ?? props.snapshot.viewer?.id
  ?? props.snapshot.self.id
))
const selectedRoleSkinLoadout = ref<RoleSkinLoadout>(
  viewerIsGuest.value
    ? defaultRoleSkinLoadout()
    : storedRoleSkinLoadout(roleSkinAccountId.value),
)
const lockedRoleSkinLoadout = ref<RoleSkinLoadout | null>(null)
const roleSkinProgress = ref(emptyAvalonRoleSkinProgress())
const roleSkinProgressLoading = ref(false)
const roleSkinProgressError = ref<string | null>(null)
let roleSkinProgressRequest = 0
const missingPlayers = computed(
  () => Math.max(0, (props.snapshot.minimumPlayers ?? props.snapshot.requiredPlayers) - props.snapshot.players.length),
)
const availableSeats = computed(
  () => Math.max(0, props.snapshot.requiredPlayers - props.snapshot.players.length),
)
const playerStripColumns = computed(() => {
  const playerCount = props.snapshot.players.length
  if (playerCount <= 5) return Math.max(1, playerCount)
  if (playerCount === 6) return 3
  return Math.ceil(playerCount / 2)
})
const playerStripStyle = computed(() => {
  const columns = playerStripColumns.value
  const widthPercent = Number((100 / columns).toFixed(6))
  const gapCorrection = Number((10 * (columns - 1) / columns).toFixed(3))
  return {
    '--player-card-width': `calc(${widthPercent}% - ${gapCorrection}px)`,
  }
})
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
watch(
  () => props.snapshot.ai?.defaultDifficulty,
  (difficulty) => {
    if (difficulty) selectedAiDifficulty.value = difficulty
  },
)
const activeRoleFamily = computed(() => roleSkinRoleCode(
  avalonSnapshot.value?.self.role?.code ?? '',
))
const activeRoleSkin = computed<RoleSkinId>(() => {
  const role = activeRoleFamily.value
  if (!role) return 'classic-tabletop'
  const candidate = (
    lockedRoleSkinLoadout.value ?? selectedRoleSkinLoadout.value
  )[role]
  return isRoleSkinUnlocked(roleSkinProgress.value, role, candidate)
    ? candidate
    : 'classic-tabletop'
})
const roleSkinLoadoutOptions = computed<RoleSkinLoadoutRoleOption[]>(() => (
  ROLE_SKIN_ROLES.map((role) => {
    const progressCode = role.code === 'shadow_merlin'
      ? 'merlin'
      : role.code === 'dissenting_courtier'
        ? 'loyal_servant'
        : role.code
    const progress = roleSkinProgress.value.roles[progressCode]
    const selectedSkinId = selectedRoleSkinLoadout.value[role.code]
    const selectedSkin = ROLE_SKINS.find((skin) => skin.id === selectedSkinId)
      ?? ROLE_SKINS[0]!
    return {
      code: role.code,
      name: role.name,
      group: role.alignment === 'good' ? '亚瑟阵营' : '莫德雷德阵营',
      wins: progress.wins,
      currentSkinName: selectedSkin.name,
      currentArtwork: roleArtwork(role.code, selectedSkin.id) ?? selectedSkin.preview,
      currentFraming: roleArtworkFraming(role.code, selectedSkin.id),
      legacyAllUnlocked: roleSkinProgress.value.legacyAllUnlocked,
      eventAllUnlocked: roleSkinProgress.value.eventAllUnlocked,
      upgradeWinsRequired: roleSkinProgress.value.upgradeWinsRequired,
      ultimateWinsRequired: roleSkinProgress.value.ultimateWinsRequired,
      choices: ROLE_SKINS.map((skin) => {
        const requiredWins = skin.tier === '终极'
          ? roleSkinProgress.value.ultimateWinsRequired
          : skin.tier === '升级'
            ? roleSkinProgress.value.upgradeWinsRequired
            : 0
        return {
          id: skin.id,
          name: skin.name,
          description: skin.description,
          tier: skin.tier,
          artwork: roleArtwork(role.code, skin.id) ?? skin.preview,
          framing: roleArtworkFraming(role.code, skin.id),
          unlocked: isRoleSkinUnlocked(roleSkinProgress.value, role.code, skin.id),
          remainingWins: Math.max(0, requiredWins - progress.wins),
        }
      }),
    }
  })
))
const avalonPhaseLabel = computed(() => {
  const phase = avalonSnapshot.value?.phase
  if (!phase) return ''
  return {
    lobby: '等待玩家集结',
    role_reveal: '确认身份',
    team_building: '组建任务队伍',
    team_voting: '表决任务队伍',
    mission_voting: '执行秘密任务',
    round_result: '任务结算',
    lady_select: '湖中仙女',
    lady_reveal: '仙女启示',
    assassination: '最后刺杀',
    dagger_grant: '黑誓授刃',
    final_council: '最后议事',
    exile_council_ballot: '祓影议庭锁票',
    exile_council_assassination_decision: '祓影议庭',
    exile_council_assassination_target: '暗刃刺杀',
    game_over: '本局终章',
  }[phase]
})
const roomHeaderEyebrow = computed(() => {
  const suffix = props.snapshot.gameKey === 'avalon'
    ? ` · ${avalonSnapshot.value?.settings.mode === 'court_undercurrent' ? '王庭暗流' : '标准模式'} · ${avalonPhaseLabel.value}`
    : props.snapshot.gameKey === 'departed_suspicion'
      ? ` · ${props.snapshot.options.equipmentSet === 'base' ? '基础装备局' : '扩展装备局'}`
    : props.snapshot.gameKey === 'junqi'
    ? ` · ${props.snapshot.options.mode === 'flip' ? '翻棋军旗' : '暗军旗'}`
    : props.snapshot.gameKey === 'reaction'
      ? ' · 单人测试'
      : props.snapshot.gameKey === 'schulte'
        ? ' · 单人专注'
        : props.snapshot.gameKey === 'minesweeper'
          ? ` · ${props.snapshot.game.difficultyLabel}`
          : props.snapshot.gameKey === 'hanoi'
            ? ' · 单人益智'
            : isSolo.value
              ? ' · 单人挑战'
              : ''
  return `${props.snapshot.gameName}${suffix}`
})
const roomHeaderTitle = computed(() => {
  const soloTitles: Partial<Record<ArcadeSnapshot['gameKey'], string>> = {
    reaction: '反应挑战',
    schulte: '舒尔特挑战',
    minesweeper: '扫雷挑战',
    hanoi: '汉诺塔挑战',
  }
  if (isSolo.value) return soloTitles[props.snapshot.gameKey] ?? props.snapshot.gameName
  return props.snapshot.roomName || `房间 ${props.snapshot.roomCode}`
})
const roomStatsMode = computed(() => (
  props.snapshot.gameKey === 'minesweeper'
    ? String(props.snapshot.options.difficulty ?? 'beginner')
    : undefined
))

function reconciledRoleSkinLoadout(loadout: RoleSkinLoadout): RoleSkinLoadout {
  return Object.fromEntries(
    ROLE_SKIN_ROLES.map((role) => {
      const skin = loadout[role.code]
      return [
        role.code,
        isRoleSkinUnlocked(roleSkinProgress.value, role.code, skin)
          ? skin
          : 'classic-tabletop',
      ]
    }),
  ) as RoleSkinLoadout
}

async function refreshRoleSkinProgress() {
  if (!avalonSnapshot.value) return
  const request = ++roleSkinProgressRequest
  roleSkinProgressError.value = null
  if (viewerIsGuest.value) {
    roleSkinProgress.value = emptyAvalonRoleSkinProgress(
      isAvalonRoleSkinFreeWeek(),
    )
    selectedRoleSkinLoadout.value = defaultRoleSkinLoadout()
    return
  }
  roleSkinProgressLoading.value = true
  try {
    const progress = await loadAvalonRoleSkinProgress()
    if (request !== roleSkinProgressRequest) return
    roleSkinProgress.value = progress
    const reconciled = reconciledRoleSkinLoadout(selectedRoleSkinLoadout.value)
    selectedRoleSkinLoadout.value = reconciled
    rememberRoleSkinLoadout(roleSkinAccountId.value, reconciled)
  } catch (error) {
    if (request !== roleSkinProgressRequest) return
    roleSkinProgress.value = emptyAvalonRoleSkinProgress(
      isAvalonRoleSkinFreeWeek(),
    )
    selectedRoleSkinLoadout.value = defaultRoleSkinLoadout()
    roleSkinProgressError.value = error instanceof Error
      ? error.message
      : '身份皮肤进度读取失败'
  } finally {
    if (request === roleSkinProgressRequest) roleSkinProgressLoading.value = false
  }
}

watch(
  () => [props.snapshot.phase, props.snapshot.gameKey] as const,
  ([phase]) => {
    if (phase !== 'lobby' || isSolo.value) showQr.value = false
  },
)
watch(
  () => [props.snapshot.roomCode, avalonSnapshot.value?.phase] as const,
  ([roomCode, phase]) => {
    if (!phase) return
    if (phase === 'lobby') {
      clearRoleSkinLoadoutLock(roomCode)
      lockedRoleSkinLoadout.value = null
      selectedRoleSkinLoadout.value = viewerIsGuest.value
        ? defaultRoleSkinLoadout()
        : storedRoleSkinLoadout(roleSkinAccountId.value)
      return
    }
    lockedRoleSkinLoadout.value =
      storedRoleSkinLoadoutLock(roomCode) ??
      lockRoleSkinLoadout(roomCode, selectedRoleSkinLoadout.value)
  },
  { immediate: true },
)
watch(
  () => [
    props.snapshot.gameKey,
    roleSkinAccountId.value,
    viewerIsGuest.value,
  ] as const,
  ([gameKey]) => {
    if (gameKey !== 'avalon') return
    selectedRoleSkinLoadout.value = viewerIsGuest.value
      ? defaultRoleSkinLoadout()
      : storedRoleSkinLoadout(roleSkinAccountId.value)
    void refreshRoleSkinProgress()
  },
  { immediate: true },
)
watch(
  () => avalonSnapshot.value?.phase,
  (phase, previousPhase) => {
    if (phase === 'lobby' && previousPhase && previousPhase !== 'lobby') {
      void refreshRoleSkinProgress()
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
    if (props.snapshot.gameKey === 'poker') {
      return '暂时返回会保留座位和筹码；退出并淘汰将放弃本桌，而且无法再返回。'
    }
    return '暂时返回会保留座位和进度；认输并退出将放弃本局，而且无法再返回。'
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

function selectRoleSkin(roleCode: string, skinId: string) {
  if (avalonSnapshot.value?.phase !== 'lobby') return
  const role = roleSkinRoleCode(roleCode)
  const skin = ROLE_SKINS.find((option) => option.id === skinId)?.id
  if (!role || !skin || !isRoleSkinUnlocked(roleSkinProgress.value, role, skin)) return
  const next = { ...selectedRoleSkinLoadout.value, [role]: skin }
  selectedRoleSkinLoadout.value = next
  if (!viewerIsGuest.value) {
    rememberRoleSkinLoadout(roleSkinAccountId.value, next)
  }
}

function playerNumber(playerId: string): number | null {
  const player = props.snapshot.players.find((item) => item.id === playerId)
  return player ? player.seat + 1 : null
}

function avalonPlayerLabel(playerId: string): string {
  const player = props.snapshot.players.find((item) => item.id === playerId)
  return player ? `${player.seat + 1}号 ${player.name}` : '未知玩家'
}

function aiDifficultyLabel(difficulty?: string | null): string {
  if (!difficulty) return '普通'
  return props.snapshot.ai?.difficulties.find(
    (option) => option.key === difficulty,
  )?.label ?? difficulty
}

function selfRoleArtwork(): string | null {
  const roleCode = avalonSnapshot.value?.self.role?.code
  return roleCode ? roleArtwork(roleCode, activeRoleSkin.value) : null
}

function selfRoleArtworkFraming() {
  return roleArtworkFraming(
    avalonSnapshot.value?.self.role?.code ?? '',
    activeRoleSkin.value,
  )
}

function openSharedChat() {
  void sharedChat.value?.openChat()
}

</script>

<template>
  <main
    class="arcade-room page-container adaptive-layout-root"
    :class="{
      'arcade-room--wide': ['avalon', 'departed_suspicion', 'poker', 'doudizhu', 'junqi', 'minesweeper', 'monopoly'].includes(snapshot.gameKey),
      'arcade-room--active': snapshot.phase !== 'lobby',
      'arcade-room--board-game': ['gomoku', 'xiangqi', 'go', 'junqi'].includes(snapshot.gameKey),
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
          :abandon-label="snapshot.gameKey === 'poker' ? '退出并淘汰' : undefined"
          @leave="arcade.leaveRoom"
          @detach="arcade.detachRoom"
          @abandon="arcade.abandonRoom"
        />
      </template>
      <template v-if="avalonSnapshot" #details>
        <button
          class="self-number-trigger"
          type="button"
          :aria-label="`${isSpectating ? '观战视角' : '我的号码'}是 ${playerNumber(snapshot.self.id)} 号，查看玩家号码表`"
          @click="showPlayerNumbers = true"
        >
          <span class="self-number-value">
            {{ playerNumber(snapshot.self.id) }}号
          </span>
          <span class="self-number-copy">
            <small>{{ isSpectating ? '观战视角' : '我的号码' }}</small>
            <span>查看号码表</span>
          </span>
          <ChevronRight :size="14" aria-hidden="true" />
        </button>
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
        <button
          type="button"
          class="header-action"
          aria-label="打开设置"
          @click="emit('settings')"
        >
          <Settings2 :size="20" />
        </button>
        <button
          v-if="snapshot.phase === 'lobby' && !isSolo"
          type="button"
          class="header-action"
          aria-label="显示加入二维码"
          @click="showQr = true"
        >
          <QrCode :size="21" />
        </button>
        <button
          v-if="avalonSnapshot?.self.role && avalonSnapshot.phase !== 'game_over'"
          class="header-action"
          type="button"
          aria-label="查看我的身份"
          @click="showIdentity = true"
        >
          <Eye :size="20" />
        </button>
        <button
          v-if="avalonSnapshot"
          class="header-action"
          type="button"
          aria-label="查看玩法说明"
          @click="showAvalonRules = true"
        >
          <CircleHelp :size="21" />
        </button>
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

    <section
      v-if="!isSolo"
      class="surface arcade-player-strip"
      :data-player-columns="playerStripColumns"
      :style="playerStripStyle"
      aria-label="房间玩家"
    >
      <article
        v-for="player in snapshot.players"
        :key="player.id"
        :class="{ self: player.id === snapshot.self.id, perspective: isSpectating && player.id === snapshot.self.id }"
      >
        <span class="arcade-player-avatar">
          <img
            v-if="player.avatarUrl"
            :src="player.avatarUrl"
            alt=""
            draggable="false"
          />
          <template v-else>{{ player.seat + 1 }}</template>
        </span>
        <div>
          <strong>{{ player.name }}</strong>
          <small>
            <Crown v-if="player.isHost" :size="13" />
            {{ player.isBot ? `AI · ${aiDifficultyLabel(player.botDifficulty)}` : player.isHost ? '房主' : '玩家' }}{{ player.isGuest ? ' · 游客' : '' }}
            {{ player.leftRoom
              ? '· 已退出'
              : player.connected
              ? '· 在线'
              : player.disconnectForfeited
                ? '· 掉线弃权'
                : player.disconnectForfeitAt
                  ? '· 离线，10 分钟后弃权'
                  : '· 离线' }}
            {{ isSpectating && player.id === snapshot.self.id ? ' · 当前观战视角' : '' }}
          </small>
        </div>
        <RoomKickButton
          v-if="snapshot.actions.canKickPlayers && player.id !== snapshot.self.id"
          :player-name="player.name"
          :busy="arcade.busy"
          @confirm="arcade.kickPlayer(player.id)"
        />
      </article>
    </section>

    <section v-if="!isSolo || roomSpectators.length" class="surface arcade-spectator-strip" aria-label="房间观众">
      <header><span><Eye :size="17" /><strong>观战席</strong></span><b>{{ roomSpectators.length }} 人</b></header>
      <div v-if="roomSpectators.length">
        <article v-for="spectator in roomSpectators" :key="spectator.id">
          <span class="arcade-spectator-avatar">
            <img v-if="spectator.avatarUrl" :src="spectator.avatarUrl" alt="" draggable="false" />
            <template v-else>{{ spectator.name.slice(0, 1) }}</template>
          </span>
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
        <span
          v-if="snapshot.actions.canAddAiPlayer"
          class="ai-add-controls"
        >
          <label v-if="(snapshot.ai?.difficulties.length ?? 0) > 1">
            <span class="sr-only">AI 难度</span>
            <select v-model="selectedAiDifficulty" aria-label="AI 难度">
              <option
                v-for="difficulty in snapshot.ai?.difficulties"
                :key="difficulty.key"
                :value="difficulty.key"
              >{{ difficulty.label }}</option>
            </select>
          </label>
          <button
            type="button"
            :disabled="arcade.busy"
            @click="arcade.action('add_ai', { difficulty: selectedAiDifficulty })"
          >
            <Bot :size="16" /> 添加 AI
          </button>
        </span>
        <button v-if="snapshot.actions.canEditRules" type="button" @click="openRuleEditor">{{ snapshot.phase === 'finished' ? '修改下局规则' : '修改规则' }}</button>
      </div>
    </section>

    <GameSkinPicker
      v-if="snapshot.phase === 'lobby' && activeGameSkinKind"
      :model-value="activeGameSkin"
      :kind="activeGameSkinKind"
      @update:model-value="selectGameSkin"
    />

    <RoleSkinLoadoutPicker
      v-if="avalonSnapshot?.phase === 'lobby'"
      :roles="roleSkinLoadoutOptions"
      :loading="roleSkinProgressLoading"
      :error="roleSkinProgressError"
      @select="selectRoleSkin"
      @retry="refreshRoleSkinProgress"
    />

    <section v-if="snapshot.phase === 'lobby'" class="surface arcade-waiting">
      <UsersRound :size="48" />
      <h2>等待玩家到齐</h2>
      <p
        v-if="avalonSnapshot?.settings.shadowMerlinEnabled && snapshot.players.length < 6"
      >
        暗影梅林扩展至少需要 6 名玩家，还需
        {{ 6 - snapshot.players.length }} 名
      </p>
      <p v-else-if="missingPlayers > 0">还需要 {{ missingPlayers }} 名玩家</p>
      <p v-else-if="availableSeats > 0">已可开始，还可加入 {{ availableSeats }} 名玩家</p>
      <p v-else>人员已到齐，房主可以开始</p>
      <button v-if="!isSolo" type="button" class="room-code-share" aria-label="显示加入二维码" @click="showQr = true">
        {{ snapshot.roomCode }}
      </button>
      <InviteLinkPanel
        v-if="!isSolo"
        :url="inviteUrl"
        :share-title="`加入${snapshot.gameName}“${snapshot.roomName || `房间 ${snapshot.roomCode}`}”`"
        :share-text="`点击链接加入${snapshot.roomName || `我的${snapshot.gameName}房间`}，房间码 ${snapshot.roomCode}`"
      />
      <button
        v-if="snapshot.actions.canStart"
        type="button"
        class="primary-button"
        @click="arcade.startGame"
      >
        开始{{ snapshot.gameName }}
      </button>
    </section>

    <section v-else class="arcade-game-stage">
      <div v-if="snapshot.phase === 'finished' && !isSolo && !avalonSnapshot" class="surface result-banner">
        <small>{{ snapshot.gameKey === 'poker' ? '本桌结束' : '本局结束' }}</small>
        <h2>{{ snapshot.winReason }}</h2>
        <p>
          {{ isSpectating
            ? `${perspectivePlayer?.name ?? '被观战玩家'}${snapshot.winnerPlayerIds.includes(snapshot.self.id) ? '赢了' : '未获胜'}`
            : snapshot.winnerPlayerIds.includes(snapshot.self.id) ? '你赢了' : '再接再厉' }}
          · 战绩已保存
        </p>
        <p class="rematch-progress">
          {{ snapshot.rematchReadyPlayerIds.length }} / {{ snapshot.players.length }} 人已准备
        </p>
        <button
          v-if="snapshot.actions.canRestart || selfRematchReady"
          type="button"
          class="primary-button"
          :disabled="selfRematchReady"
          @click="arcade.restartGame"
        >
          <RotateCcw :size="18" />
          {{ selfRematchReady ? '等待其他玩家' : snapshot.gameKey === 'poker' ? '准备重新开桌' : '准备再来一局' }}
        </button>
      </div>

      <GomokuBoard v-if="snapshot.gameKey === 'gomoku'" :snapshot="snapshot" />
      <DepartedSuspicionTable v-else-if="snapshot.gameKey === 'departed_suspicion'" :snapshot="snapshot" />
      <XiangqiBoard v-else-if="snapshot.gameKey === 'xiangqi'" :snapshot="snapshot" />
      <GoBoard v-else-if="snapshot.gameKey === 'go'" :snapshot="snapshot" />
      <PokerTable v-else-if="snapshot.gameKey === 'poker'" :snapshot="snapshot" />
      <DoudizhuTable v-else-if="snapshot.gameKey === 'doudizhu'" :snapshot="snapshot" />
      <JunqiBoard v-else-if="snapshot.gameKey === 'junqi'" :snapshot="snapshot" />
      <ReactionTest v-else-if="snapshot.gameKey === 'reaction'" :snapshot="snapshot" />
      <SchulteGrid v-else-if="snapshot.gameKey === 'schulte'" :snapshot="snapshot" />
      <MinesweeperBoard v-else-if="snapshot.gameKey === 'minesweeper'" :snapshot="snapshot" />
      <HanoiGame v-else-if="snapshot.gameKey === 'hanoi'" :snapshot="snapshot" />
      <MonopolyBoard v-else-if="snapshot.gameKey === 'monopoly'" :snapshot="snapshot" />
      <component v-else-if="pluginGameComponent" :is="pluginGameComponent" :snapshot="snapshot" />
      <AvalonTable
        v-else-if="avalonSnapshot"
        :snapshot="avalonSnapshot"
        :role-skin="activeRoleSkin"
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

    <div v-if="ruleEditor" class="modal-backdrop" @click.self="ruleEditor = null">
      <section class="modal-card rule-editor-modal" role="dialog" aria-modal="true">
        <button class="modal-close" type="button" aria-label="关闭规则设置" @click="ruleEditor = null">
          <X :size="20" />
        </button>
        <span class="modal-icon"><Settings2 :size="25" /></span>
        <h2>房间规则</h2>
        <p>{{ snapshot.phase === 'finished' ? '保存后所有玩家会返回等待阶段，新规则从下一局生效。' : '保存后会同步给房间中的所有玩家，开局后不可修改。' }}</p>
        <GameRuleSettings v-model="ruleEditor" :game-key="snapshot.gameKey" :guest-mode="viewerIsGuest" />
        <button type="button" class="primary-button wide-button" :disabled="arcade.busy" @click="saveRules">保存规则</button>
      </section>
    </div>

    <div v-if="showPlayerNumbers && avalonSnapshot" class="modal-backdrop" @click.self="showPlayerNumbers = false">
      <section class="modal-card player-number-modal" role="dialog" aria-modal="true" aria-label="玩家号码表">
        <button class="modal-close" type="button" aria-label="关闭玩家号码表" @click="showPlayerNumbers = false">
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
            <small v-if="player.isBot">AI · {{ aiDifficultyLabel(player.botDifficulty) }}</small>
            <small v-if="player.id === snapshot.self.id">{{ isSpectating ? '观战视角' : '你' }}</small>
          </div>
        </div>
      </section>
    </div>

    <div v-if="showIdentity && avalonSnapshot?.self.role" class="modal-backdrop" @click.self="showIdentity = false">
      <section class="modal-card identity-modal" role="dialog" aria-modal="true">
        <button class="modal-close" type="button" aria-label="关闭身份" @click="showIdentity = false">
          <X :size="20" />
        </button>
        <PressRevealCard
          :title="avalonSnapshot.self.role.label"
          :subtitle="avalonSnapshot.self.role.alignment === 'good' ? '亚瑟阵营' : '莫德雷德阵营'"
          :artwork="selfRoleArtwork()"
          :artwork-label="roleSkinName(activeRoleSkin)"
          :artwork-framing="selfRoleArtworkFraming()"
          hint="按住重新查看身份"
        >
          <p class="secret-description">{{ avalonSnapshot.self.role.description }}</p>
          <div v-if="avalonSnapshot.self.role.knowledge.length" class="knowledge-list">
            <span v-for="item in avalonSnapshot.self.role.knowledge" :key="item.playerId">
              {{ avalonPlayerLabel(item.playerId) }} · {{ item.label }}
            </span>
          </div>
          <div v-if="avalonSnapshot.lady.myChecks.length" class="knowledge-list">
            <span v-for="check in avalonSnapshot.lady.myChecks" :key="`${check.missionNumber}-${check.targetId}`">
              仙女：{{ avalonPlayerLabel(check.targetId) }} · {{ check.alignment === 'good' ? '好人阵营' : '坏人阵营' }}
            </span>
          </div>
        </PressRevealCard>
      </section>
    </div>

    <div v-if="showAvalonRules && avalonSnapshot" class="modal-backdrop" @click.self="showAvalonRules = false">
      <section class="modal-card rules-modal" role="dialog" aria-modal="true">
        <button class="modal-close" type="button" aria-label="关闭玩法说明" @click="showAvalonRules = false">
          <X :size="20" />
        </button>
        <span class="modal-icon"><CircleHelp :size="25" /></span>
        <h2>{{ avalonSnapshot.settings.mode === 'court_undercurrent' ? '王庭暗流 · 玩法说明' : '标准阿瓦隆 · 玩法说明' }}</h2>
        <p>{{ avalonSnapshot.settings.mode === 'court_undercurrent' ? '背景故事、特殊角色与终局规则集中在这里。' : '本局采用标准阿瓦隆规则。' }}</p>
        <ModeGuide
          v-if="avalonSnapshot.settings.mode === 'court_undercurrent'"
          :content="AVALON_COURT_GUIDE"
        />
        <section class="avalon-core-rules">
          <h3>阿瓦隆基础规则</h3>
          <ul>
            <li>好人只能提交任务成功，坏人可选择成功或失败。</li>
            <li>队伍表决需要过半赞成，平票视为否决。</li>
            <li>同一任务连续五次组队被否决，当前任务直接失败。</li>
            <li>部分玩家掉线超过 10 分钟，其所属阵营弃权；全员离线只进入房间清理流程。</li>
            <li v-if="snapshot.players.length >= 7">第四次任务需要两张失败票才会失败。</li>
            <li v-if="avalonSnapshot.settings.ladyEnabled">仙女只查阵营，持有者可以谎报查验结果。</li>
          </ul>
        </section>
      </section>
    </div>
  </main>
</template>

<style scoped>
.arcade-room { padding-bottom: 70px; }
.guest-match-notice { margin: 0 0 18px; padding: 12px 15px; border-color: color-mix(in srgb, var(--gold) 35%, var(--line)); background: color-mix(in srgb, var(--gold) 7%, var(--surface)); }
.guest-match-notice strong,.guest-match-notice span { display: block; }.guest-match-notice strong { color: var(--gold); font-size: 13px; }.guest-match-notice span { margin-top: 4px; color: var(--muted); font-size: 11px; line-height: 1.55; }
.spectator-mode-banner { display: flex; align-items: center; gap: 11px; margin: 0 0 18px; padding: 12px 15px; border-color: color-mix(in srgb, #68c8df 38%, var(--line)); background: color-mix(in srgb, #68c8df 7%, var(--surface)); }
.spectator-mode-banner > svg { flex: 0 0 auto; color: #83d4e7; }.spectator-mode-banner span { min-width: 0; display: grid; gap: 3px; }.spectator-mode-banner strong { color: #9dddeb; font-size: 13px; }.spectator-mode-banner small { color: var(--muted); line-height: 1.45; }
.arcade-player-strip { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 24px; padding: 14px; }
.arcade-player-strip article { display: flex; flex: 0 0 var(--player-card-width); gap: 10px; align-items: center; min-width: 0; min-height: 68px; padding: 10px; border: 1px solid color-mix(in srgb, var(--line) 72%, transparent); border-radius: 12px; background: color-mix(in srgb, var(--surface-elevated) 42%, transparent); }
.arcade-player-strip article > div { min-width: 0; flex: 1; }
.arcade-player-strip article.self { border-color: color-mix(in srgb, var(--gold) 40%, transparent); background: color-mix(in srgb, var(--gold) 7%, transparent); }
.arcade-player-strip article > span { width: 34px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 10px; color: var(--gold); background: color-mix(in srgb, var(--gold) 13%, transparent); font-weight: 900; }
.arcade-player-avatar { overflow: hidden; }
.arcade-player-avatar img { width: 100%; height: 100%; object-fit: cover; }
.arcade-player-strip strong, .arcade-player-strip small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.arcade-player-strip small { margin-top: 2px; color: var(--muted); }
.arcade-player-strip small svg { vertical-align: -2px; color: var(--gold); }
.arcade-spectator-strip { display: grid; gap: 10px; margin: -10px 0 24px; padding: 12px 14px; }
.arcade-spectator-strip > header { display: flex; align-items: center; justify-content: space-between; gap: 10px; }.arcade-spectator-strip > header span { display: inline-flex; align-items: center; gap: 7px; color: #83d4e7; }.arcade-spectator-strip > header b { color: var(--muted); font-size: 10px; }
.arcade-spectator-strip > div { display: flex; flex-wrap: wrap; gap: 8px; }.arcade-spectator-strip article { min-width: min(100%, 190px); display: flex; align-items: center; gap: 8px; border: 1px solid var(--line); border-radius: 11px; padding: 8px 10px; background: var(--surface-inset); }.arcade-spectator-strip article > span:last-child { min-width: 0; display: grid; gap: 1px; }.arcade-spectator-strip article strong,.arcade-spectator-strip article small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.arcade-spectator-strip article small { color: var(--muted); font-size: 9px; }.arcade-spectator-strip > p { margin: 0; color: var(--muted); font-size: 10px; }
.arcade-spectator-avatar { flex: 0 0 auto; width: 30px; aspect-ratio: 1; display: grid; place-items: center; overflow: hidden; border-radius: 9px; color: #83d4e7; background: color-mix(in srgb, #68c8df 12%, var(--surface-elevated)); font-size: 11px; font-weight: 900; }.arcade-spectator-avatar img { width: 100%; height: 100%; object-fit: cover; }
.room-rule-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: -12px 0 24px; padding: 11px 13px; }
.room-rule-bar > div { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; min-width: 0; }
.room-rule-bar svg { flex: 0 0 auto; color: var(--gold); }
.room-rule-bar span { border: 1px solid var(--line); border-radius: 999px; padding: 4px 8px; color: var(--muted); background: rgba(0, 0, 0, .1); font-size: 10px; }
.room-rule-actions { flex: 0 0 auto; display: flex; gap: 8px; }
.room-rule-actions button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 36px; border: 1px solid color-mix(in srgb, var(--gold) 38%, var(--line)); border-radius: 10px; padding: 0 11px; color: var(--gold); background: color-mix(in srgb, var(--gold) 7%, transparent); font-weight: 850; }
.game-skin-card + .arcade-waiting,
.role-skin-loadout + .arcade-waiting { margin-top: 18px; }
.arcade-waiting { min-height: min(390px, 48dvh); display: grid; place-items: center; align-content: center; gap: 12px; padding: 30px 18px; text-align: center; }
.arcade-waiting > svg { color: var(--gold); }
.arcade-waiting h2, .arcade-waiting p { margin: 0; }
.arcade-waiting p { color: var(--muted); }
.ai-add-controls { display: inline-flex; align-items: stretch; gap: 8px; }
.ai-add-controls label { display: flex; }
.ai-add-controls select { min-width: 78px; border: 1px solid var(--line); border-radius: 10px; padding: 0 28px 0 10px; color: var(--text); background: var(--surface-raised); font: inherit; }
.room-code-share { margin: 14px 0 0; border: 0; padding: 0; color: var(--text); background: transparent; font-size: 28px; font-weight: 800; letter-spacing: .18em; }
.arcade-waiting :deep(.invite-link-panel) { width: min(100%, 620px); }
.arcade-game-stage { display: grid; gap: 22px; }
.result-banner { padding: 18px; text-align: center; }
.result-banner small { color: var(--gold); }
.result-banner h2 { margin: 5px 0; }
.result-banner p { color: var(--muted); }
.result-banner .rematch-progress { margin-bottom: 0; font-size: 11px; }
.result-banner .primary-button { margin: 12px auto 0; }
.rule-editor-modal { width: min(94vw, 620px); max-height: min(88vh, 820px); overflow-y: auto; }
.rule-editor-modal > p { margin: -4px 0 20px; color: var(--muted); }
.rule-editor-modal > .wide-button { margin-top: 22px; }
@media (max-width: 860px) {
  .arcade-player-strip article { flex-basis: calc(33.333333% - 6.667px); }
}
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
  .arcade-player-strip article { flex-basis: calc(50% - 5px); }
  .room-rule-bar { align-items: stretch; flex-direction: column; }
  .room-rule-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); }
  .room-rule-actions button { width: 100%; }
  .arcade-waiting { min-height: 0; padding: 25px 14px; }
  .arcade-waiting > svg { width: 38px; height: 38px; }
  .arcade-waiting h2 { font-size: 20px; }
  .arcade-waiting .room-code-share { margin-top: 7px; font-size: 24px; }
}
@media (max-width: 430px) {
  .arcade-player-strip article { flex-basis: 100%; }
}
@media (orientation: landscape) and (min-width: 621px) and (max-width: 980px) and (max-height: 600px) {
  .arcade-room--active.arcade-room--board-game :deep(.room-page-header) { grid-template-columns: auto minmax(0, 1fr) auto; }
  .arcade-room--active.arcade-room--board-game :deep(.room-page-actions) { grid-column: auto; width: auto; justify-content: flex-end; }
  .arcade-room--active.arcade-room--board-game > .arcade-game-stage { order: 2; }
  .arcade-room--active.arcade-room--board-game > .guest-match-notice { order: 3; margin-top: 18px; }
}
@media (min-width: 860px) {
  .arcade-room.arcade-room--wide { width: min(100%, 1080px); }
}
</style>
